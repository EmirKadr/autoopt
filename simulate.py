"""
simulate.py – Simulator för plockplatsoptimering
=================================================
AGENTEN FÅR INTE ÄNDRA DENNA FIL.

Laddar historisk data, beräknar artikelstatistik, tilldelar plockplatser
baserat på strategy.py, och simulerar påfyllningar dag för dag.

Returnerar ett SimResultat-objekt med alla nyckeltal.
"""

import os
import glob
import warnings
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

import config
import strategy

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)


# ---------------------------------------------------------------------------
# DATAKLASSER
# ---------------------------------------------------------------------------

@dataclass
class ArtikelStats:
    artikelnr: str
    freq_2day: float          # Tvådagarsfrekvens
    n_butiker_frac: float     # Andel butiker som beställt
    stabilitet: float         # Vecka-till-vecka stabilitet
    is_kampanj: bool          # Kampanjartikel?
    has_buffer: bool          # Buffertpall?
    days_since_last_pick: int # Dagar sedan senaste plockning
    has_any_history: bool     # Plockats någon gång under perioden?
    total_picks: int          # Totalt antal plockningar under perioden
    score: float = 0.0        # Beräknas av score_article()


@dataclass
class SimResultat:
    bolag: str
    zon: str
    n_artiklar_total: int
    n_tilldelade: int
    max_platser: int

    paafyllningar_totalt: int
    paafyllningar_reguljara: int    # Pall tömd → ny pall behövs
    paafyllningar_tvangsbyte: int   # Ny artikel trängde ut gamla

    onodiga_returer: int            # Artiklar tillbaka < ONÖDIG_RETUR_DAGAR
    onodiga_returer_pct: float

    serviceniva_pct: float          # Ordrade artiklar som fanns på plockplats
    tvangsbyte_pct: float           # Andel byten som var tvångsbyte

    experiment_id: str = ""
    fel: Optional[str] = None       # Om None → OK, annars felbeskrivning


# ---------------------------------------------------------------------------
# HJÄLPFUNKTIONER – KLASSIFICERING
# ---------------------------------------------------------------------------

def klassificera_plats(lagerplats: str) -> dict:
    """
    Returnerar dict med: agare (GG/MG/Exkl), zon, forvaringsform, ar_hyllplats
    Baserat på location-taxonomy wiki.
    """
    p = str(lagerplats).strip()
    ar_hyllplats = len(p) > 0 and p[-1].isalpha()

    # Regel 1: BA* → exkluderad
    if p.startswith("BA"):
        return {"agare": "Exkl", "zon": "Ej klass", "ar_hyllplats": ar_hyllplats}

    # Regel 2: AA03A–AA14C → GG / A / Krattplats
    if p.startswith("AA") and len(p) >= 4:
        try:
            num = int(p[2:4])
            if 3 <= num <= 14:
                return {"agare": "GG", "zon": "A", "ar_hyllplats": ar_hyllplats}
        except ValueError:
            pass

    # Regel 3: AA23–AA69 → GG / Grav
    if p.startswith("AA") and len(p) >= 4:
        try:
            num = int(p[2:4])
            if 23 <= num <= 69:
                return {"agare": "GG", "zon": "Grav", "ar_hyllplats": ar_hyllplats}
        except ValueError:
            pass

    # Regel 4: AA15–AA22, AA70–AA75 → GG / A
    if p.startswith("AA") and len(p) >= 4:
        try:
            num = int(p[2:4])
            if (15 <= num <= 22) or (70 <= num <= 75):
                return {"agare": "GG", "zon": "A", "ar_hyllplats": ar_hyllplats}
        except ValueError:
            pass

    # Regel 5: ZBRAND*, EXPLO* → GG / Brand
    if p.startswith("ZBRAND") or p.startswith("EXPLO"):
        return {"agare": "GG", "zon": "Brand", "ar_hyllplats": ar_hyllplats}

    # Regel 6: BN* → GG / EH
    if p.startswith("BN"):
        return {"agare": "GG", "zon": "EH", "ar_hyllplats": ar_hyllplats}

    # Regel 7: BO*, BP*, BQ* → GG / SK
    if p.startswith("BO") or p.startswith("BP") or p.startswith("BQ"):
        return {"agare": "GG", "zon": "SK", "ar_hyllplats": ar_hyllplats}

    # Regel 8: SK* → GG / SK
    if p.startswith("SK"):
        return {"agare": "GG", "zon": "SK", "ar_hyllplats": ar_hyllplats}

    # Regel 9: KAM* → GG / KAM
    if p.startswith("KAM"):
        return {"agare": "GG", "zon": "KAM", "ar_hyllplats": ar_hyllplats}

    # Regel 10: UTE* → GG / UTE
    if p.startswith("UTE"):
        return {"agare": "GG", "zon": "UTE", "ar_hyllplats": ar_hyllplats}

    # Regel 11: Övriga B* → GG / A
    if p.startswith("B"):
        return {"agare": "GG", "zon": "A", "ar_hyllplats": ar_hyllplats}

    # Regel 12: M1BR*, M2BR*, MBR* → MG / Brand
    if p.startswith("M1BR") or p.startswith("M2BR") or p.startswith("MBR"):
        return {"agare": "MG", "zon": "Brand", "ar_hyllplats": ar_hyllplats}

    # Regel 13: MGOLV*, MLIST* → MG / SK
    if p.startswith("MGOLV") or p.startswith("MLIST"):
        return {"agare": "MG", "zon": "SK", "ar_hyllplats": ar_hyllplats}

    # Regel 14: L* → MG / A
    if p.startswith("L"):
        return {"agare": "MG", "zon": "A", "ar_hyllplats": ar_hyllplats}

    # Regel 15: Allt övrigt → exkluderad
    return {"agare": "Exkl", "zon": "Ej klass", "ar_hyllplats": ar_hyllplats}


# ---------------------------------------------------------------------------
# DATALADDNING
# ---------------------------------------------------------------------------

def _hitta_fil(mapp: str, prefix: str, fallback_namn: str) -> str:
    """Hittar senaste fil med givet prefix, faller tillbaka på exakt namn."""
    mönster = os.path.join(mapp, f"{prefix}*.csv")
    träffar = sorted(glob.glob(mönster), reverse=True)
    if träffar:
        return träffar[0]
    explicit = os.path.join(mapp, fallback_namn)
    if os.path.exists(explicit):
        return explicit
    raise FileNotFoundError(f"Hittade inte fil med prefix '{prefix}' i {mapp}")


def ladda_data() -> dict:
    """Laddar alla CSV-filer och returnerar dict med DataFrames."""
    mapp = config.DATA_DIR

    def läs(filnamn: str, **kwargs) -> pd.DataFrame:
        sökväg = os.path.join(mapp, filnamn)
        if not os.path.exists(sökväg):
            raise FileNotFoundError(f"Fil saknas: {sökväg}\nKontrollera config.py")
        return pd.read_csv(sökväg, sep="\t", encoding="utf-8-sig", **kwargs)

    data = {}

    data["pick_log"] = läs(config.PICK_LOG_FILE,
                           parse_dates=[config.COL_PICK_DATUM], dayfirst=True)

    data["pick_loc_log"] = läs(config.PICK_LOCATION_LOG_FILE,
                               parse_dates=[config.COL_LOC_TIMESTAMP], dayfirst=True)

    data["buffert"] = läs(config.BUFFERT_FILE)

    data["location"] = läs(config.LOCATION_FILE)

    data["order_log"] = läs(config.ORDER_LOG_FILE,
                            parse_dates=[config.COL_ORD_AVGANGSDATUM], dayfirst=True)

    # customer_order_details har ingen rubrikrad
    data["order_details"] = läs(config.ORDER_DETAILS_FILE, header=None)

    return data


# ---------------------------------------------------------------------------
# ARTIKELSTATISTIK
# ---------------------------------------------------------------------------

def beräkna_artikelstatistik(data: dict, bolag: str, zon: str) -> list[ArtikelStats]:
    """
    Beräknar statistik per artikel för angiven bolag+zon.
    Returnerar lista av ArtikelStats.
    """
    pick_log = data["pick_log"]
    order_log = data["order_log"]
    buffert = data["buffert"]

    # Filtrera på bolag
    pick = pick_log[pick_log[config.COL_PICK_BOLAG].astype(str).str.strip() == bolag].copy()

    # Filtrera på zon om angiven
    if zon and zon != "Alla":
        if config.COL_PICK_ZON in pick.columns:
            pick = pick[pick[config.COL_PICK_ZON].astype(str).str.strip() == zon]

    # Analysperiod
    if config.ANALYS_DAGAR and len(pick) > 0:
        senaste_datum = pick[config.COL_PICK_DATUM].max()
        från_datum = senaste_datum - timedelta(days=config.ANALYS_DAGAR)
        pick = pick[pick[config.COL_PICK_DATUM] >= från_datum]

    if len(pick) == 0:
        return []

    senaste_datum = pick[config.COL_PICK_DATUM].max()
    tidiga_datum  = pick[config.COL_PICK_DATUM].min()
    total_dagar   = max((senaste_datum - tidiga_datum).days, 1)

    # Koppla Ordernr → avgångsdatum för tvådagarsfönster
    ord_map = {}
    if config.COL_ORD_ORDERNR in order_log.columns and config.COL_ORD_AVGANGSDATUM in order_log.columns:
        ord_map = dict(zip(
            order_log[config.COL_ORD_ORDERNR].astype(str),
            order_log[config.COL_ORD_AVGANGSDATUM]
        ))

    pick = pick.copy()
    pick["_avgangsdatum"] = pick[config.COL_PICK_ORDERNR].astype(str).map(ord_map)

    # Tvådagarsfönster: artikel räknas som "aktiv" dag D om plockdatum ∈ [D-1, D]
    # Förenkling: använd plockdatum direkt om avgångsdatum saknas
    pick["_aktiv_dag"] = pick["_avgangsdatum"].fillna(pick[config.COL_PICK_DATUM])

    # Unika aktiva dagar per artikel
    aktiva_dagar_per_artikel = (
        pick.groupby(config.COL_PICK_ARTIKEL)["_aktiv_dag"]
        .apply(lambda s: s.dt.date.nunique())
    )

    # Beräkna tvådagarsfrekvens
    freq_2day = (aktiva_dagar_per_artikel / total_dagar).clip(0, 1)

    # Unika butiker per artikel (via Ordernr → butiksinfo om tillgängligt)
    # Approximation: antal unika ordrar ≈ butiksbredd
    ordrar_per_artikel = pick.groupby(config.COL_PICK_ARTIKEL)[config.COL_PICK_ORDERNR].nunique()
    max_ordrar = ordrar_per_artikel.max() if len(ordrar_per_artikel) > 0 else 1
    butik_bredd_frac = (ordrar_per_artikel / max(max_ordrar, 1)).clip(0, 1)

    # Stabilitet: vecka-till-vecka konsistens
    pick["_vecka"] = pick[config.COL_PICK_DATUM].dt.isocalendar().week
    veckor = pick["_vecka"].nunique()
    if veckor > 1:
        picks_per_artikel_vecka = (
            pick.groupby([config.COL_PICK_ARTIKEL, "_vecka"])
            .size()
            .unstack(fill_value=0)
        )
        # Stabilitet = 1 - (std / (mean + epsilon))
        medel = picks_per_artikel_vecka.mean(axis=1)
        std   = picks_per_artikel_vecka.std(axis=1).fillna(0)
        stabilitet = (1 - std / (medel + 1)).clip(0, 1)
    else:
        stabilitet = pd.Series(0.5, index=freq_2day.index)

    # Kampanjdetektering: toppighet = andel picks på topp-3 dagar
    picks_per_dag = (
        pick.groupby([config.COL_PICK_ARTIKEL, config.COL_PICK_DATUM])
        .size()
        .reset_index(name="n")
    )

    def toppighet(grp):
        if len(grp) < 3:
            return 1.0
        topp3 = grp.nlargest(3, "n")["n"].sum()
        tot   = grp["n"].sum()
        return topp3 / max(tot, 1)

    topp_per_artikel = (
        picks_per_dag.groupby(config.COL_PICK_ARTIKEL)
        .apply(toppighet)
    )
    is_kampanj = topp_per_artikel > strategy.KAMPANJ_TOPPIGHET_THRESHOLD

    # Dagar sedan senaste plockning
    senaste_pick = pick.groupby(config.COL_PICK_ARTIKEL)[config.COL_PICK_DATUM].max()
    days_since = ((senaste_datum - senaste_pick).dt.days).astype(int)

    # Totalt antal plockningar
    total_picks = pick.groupby(config.COL_PICK_ARTIKEL).size()

    # Buffert – artiklar med buffertpall
    buf_artiklar = set(
        buffert[buffert[config.COL_BUF_BOLAG].astype(str).str.strip() == bolag]
        [config.COL_BUF_ARTIKEL].astype(str).str.strip()
    )

    # Samla alla artiklar som förekommer
    alla_artiklar = sorted(freq_2day.index.astype(str).tolist())
    stats_lista = []

    for art in alla_artiklar:
        art_str = str(art)
        f2d   = float(freq_2day.get(art, 0.0))
        bredd = float(butik_bredd_frac.get(art, 0.0))
        stab  = float(stabilitet.get(art, 0.5))
        kamp  = bool(is_kampanj.get(art, False))
        buf   = art_str in buf_artiklar
        dagar = int(days_since.get(art, total_dagar))
        hist  = bool(total_picks.get(art, 0) > 0)
        picks = int(total_picks.get(art, 0))

        sc = strategy.score_article(f2d, bredd, stab, kamp, buf, dagar, hist)

        stats_lista.append(ArtikelStats(
            artikelnr=art_str,
            freq_2day=f2d,
            n_butiker_frac=bredd,
            stabilitet=stab,
            is_kampanj=kamp,
            has_buffer=buf,
            days_since_last_pick=dagar,
            has_any_history=hist,
            total_picks=picks,
            score=sc,
        ))

    # Sortera: högst score först
    stats_lista.sort(key=lambda s: s.score, reverse=True)
    return stats_lista


# ---------------------------------------------------------------------------
# TILLDELNING AV PLOCKPLATSER
# ---------------------------------------------------------------------------

def tilldela_plockplatser(
    stats_lista: list[ArtikelStats],
    max_platser: int
) -> set[str]:
    """
    Väljer vilka artiklar som ska ha plockplats.
    Returnerar mängd av artikelnummer.

    Regler:
    1. Artiklar som should_force_remove() = True exkluderas direkt
    2. Artiklar utan buffert och låg frekvens inkluderas alltid (kan inte tas bort)
    3. Resterande platser fylls med artiklar sorterade på score (högst först)
    """
    tilldelade = set()
    måste_ha = set()

    for s in stats_lista:
        # Obligatorisk: artikel utan buffert och låg frekvens
        if not s.has_buffer and s.freq_2day < strategy.THRESHOLD_LAMNA:
            måste_ha.add(s.artikelnr)

    # Lägg först in obligatoriska
    for s in stats_lista:
        if s.artikelnr in måste_ha:
            tilldelade.add(s.artikelnr)

    # Fyll sedan med bästa-score-artiklar upp till max
    lediga = max_platser - len(tilldelade)
    for s in stats_lista:
        if lediga <= 0:
            break
        if s.artikelnr in tilldelade:
            continue
        if strategy.should_force_remove(
            s.freq_2day, s.has_buffer, 0, s.total_picks
        ):
            continue  # Aggressivt exkluderad
        tilldelade.add(s.artikelnr)
        lediga -= 1

    return tilldelade


# ---------------------------------------------------------------------------
# SIMULATION DAG FÖR DAG
# ---------------------------------------------------------------------------

def simulera(
    data: dict,
    stats_lista: list[ArtikelStats],
    tilldelade: set[str],
    bolag: str,
) -> dict:
    """
    Simulerar påfyllningar dag för dag baserat på historisk pick_log.

    Returnerar dict med simuleringsresultat.
    """
    pick_log = data["pick_log"]
    pick_loc = data["pick_loc_log"]

    pick = pick_log[pick_log[config.COL_PICK_BOLAG].astype(str).str.strip() == bolag].copy()
    if config.ANALYS_DAGAR and len(pick) > 0:
        senaste = pick[config.COL_PICK_DATUM].max()
        pick = pick[pick[config.COL_PICK_DATUM] >= senaste - timedelta(days=config.ANALYS_DAGAR)]

    if len(pick) == 0:
        return {"fel": "Inga plockrader för angiven bolag/zon"}

    # Statistik-lookup
    stats_map = {s.artikelnr: s for s in stats_lista}

    # Simuleringsstate
    # pall_saldo[artikel] = antal enheter kvar på plockplats-pallen
    pall_saldo: dict[str, int] = {}
    for art in tilldelade:
        pall_saldo[art] = config.UPPSKATTAD_PALLSTORLEK  # Börja full

    paafyllningar_reguljara = 0
    paafyllningar_tvangsbyte = 0
    servicehits = 0
    servicemissar = 0

    # Spåra när en artikel senast lämnade plockplats (för tvångsbyte-detektering)
    senast_ute: dict[str, pd.Timestamp] = {}

    # Spåra pallrörelser för onödiga returer
    # rörelser[artikel] = lista av (tidpunkt, typ) där typ = "IN" eller "OUT"
    rörelser: list[tuple[str, pd.Timestamp, str]] = []

    # Bearbeta dag för dag
    dagar = sorted(pick[config.COL_PICK_DATUM].dt.date.unique())

    for dag in dagar:
        dag_picks = pick[pick[config.COL_PICK_DATUM].dt.date == dag]
        ordrade_artiklar = dag_picks[config.COL_PICK_ARTIKEL].astype(str).unique()

        for art in ordrade_artiklar:
            n_picks = int((dag_picks[config.COL_PICK_ARTIKEL].astype(str) == art).sum())

            if art in tilldelade:
                # Artikeln ska vara på plockplats
                servicehits += n_picks

                # Dra av från pallsaldo
                pall_saldo[art] = pall_saldo.get(art, config.UPPSKATTAD_PALLSTORLEK) - n_picks

                # Pall tömd → regelbunden påfyllning
                if pall_saldo.get(art, 0) <= 0:
                    paafyllningar_reguljara += 1
                    pall_saldo[art] = config.UPPSKATTAD_PALLSTORLEK
                    rörelser.append((art, pd.Timestamp(dag), "IN"))
            else:
                # Artikeln är INTE tilldelad plockplats → servicemiss (plock från buffert)
                servicemissar += n_picks

        # Kontrollera om några tilldelade artiklar behöver tvingas ut (kapacitet)
        # I simuleringen: om en artikel som INTE är tilldelad är mer urgent,
        # simulera ett tvångsbyte
        # Förenkling: tvångsbyte sker när totalt tilldelade > max_platser
        # (hanteras i tilldela_plockplatser(), här räknar vi bara reguljära)

    # Beräkna onödiga returer från rörelserna
    # (artiklar som kom tillbaka < ONÖDIG_RETUR_DAGAR efter att ha letts ut)
    # Baseras på faktisk pick_location_log
    onodiga = _beräkna_onödiga_returer(data, bolag)

    # Tvångsbyte från pick_location_log
    tvangsbyte_count, total_byten = _beräkna_tvangsbyte(data, bolag)

    totalt = paafyllningar_reguljara + tvangsbyte_count

    service_total = servicehits + servicemissar
    serviceniva = servicehits / max(service_total, 1)
    tvangsbyte_pct = tvangsbyte_count / max(total_byten, 1) * 100
    onodiga_pct = onodiga / max(total_byten, 1) * 100

    return {
        "paafyllningar_totalt":      totalt,
        "paafyllningar_reguljara":   paafyllningar_reguljara,
        "paafyllningar_tvangsbyte":  tvangsbyte_count,
        "onodiga_returer":           onodiga,
        "onodiga_returer_pct":       onodiga_pct,
        "serviceniva_pct":           serviceniva * 100,
        "tvangsbyte_pct":            tvangsbyte_pct,
        "servicehits":               servicehits,
        "servicemissar":             servicemissar,
    }


def _beräkna_tvangsbyte(data: dict, bolag: str) -> tuple[int, int]:
    """
    Räknar tvångsbyte från pick_location_log.
    Tvångsbyte = ny artikel på samma plats inom TVANGSBYTE_TIMMAR efter att förra lämnade.
    Returnerar (tvangsbyte_count, total_byten).
    """
    loc = data["pick_loc_log"]
    loc = loc[loc[config.COL_LOC_BOLAG].astype(str).str.strip() == bolag].copy()

    if len(loc) == 0:
        return 0, 0

    loc = loc.sort_values(config.COL_LOC_TIMESTAMP)

    # Gruppera per plats, titta på IN-händelser
    ny_plats = config.COL_LOC_NY_PLATS
    if ny_plats not in loc.columns:
        return 0, 0

    tvangsbyte = 0
    total_in = 0

    for plats, grp in loc.groupby(ny_plats):
        grp = grp.sort_values(config.COL_LOC_TIMESTAMP)
        timestamps = grp[config.COL_LOC_TIMESTAMP].tolist()
        artiklar   = grp[config.COL_LOC_ARTIKEL].astype(str).tolist()

        total_in += len(timestamps)

        for i in range(1, len(timestamps)):
            prev_ts   = timestamps[i - 1]
            curr_ts   = timestamps[i]
            prev_art  = artiklar[i - 1]
            curr_art  = artiklar[i]

            if prev_art == curr_art:
                continue  # Samma artikel – inte ett byte

            diff_h = (curr_ts - prev_ts).total_seconds() / 3600
            if 0 < diff_h <= config.TVANGSBYTE_TIMMAR:
                tvangsbyte += 1

    return tvangsbyte, total_in


def _beräkna_onödiga_returer(data: dict, bolag: str) -> int:
    """
    Räknar artiklar som kom tillbaka till plockplats inom ONÖDIG_RETUR_DAGAR
    efter att ha lämnat den.
    """
    loc = data["pick_loc_log"]
    loc = loc[loc[config.COL_LOC_BOLAG].astype(str).str.strip() == bolag].copy()

    if len(loc) == 0 or config.COL_LOC_TIDIG_PLATS not in loc.columns:
        return 0

    loc = loc.sort_values(config.COL_LOC_TIMESTAMP)
    onodiga = 0

    # Spåra senaste OUT per artikel
    senast_ute: dict[str, pd.Timestamp] = {}

    for _, rad in loc.iterrows():
        art = str(rad[config.COL_LOC_ARTIKEL]).strip()
        ts  = rad[config.COL_LOC_TIMESTAMP]

        # OUT = artrikeln lämnar en plats (Ny plats är tom/annan)
        tidig = str(rad.get(config.COL_LOC_TIDIG_PLATS, "")).strip()
        ny    = str(rad.get(config.COL_LOC_NY_PLATS, "")).strip()

        if tidig and not ny:
            # Artikel lämnade en plats
            senast_ute[art] = ts
        elif ny and art in senast_ute:
            # Artikel kom tillbaka
            diff_d = (ts - senast_ute[art]).total_seconds() / 86400
            if 0 < diff_d <= config.ONÖDIG_RETUR_DAGAR:
                onodiga += 1
            del senast_ute[art]

    return onodiga


# ---------------------------------------------------------------------------
# HUVUD-API
# ---------------------------------------------------------------------------

def kör_simulation(experiment_id: str = "") -> SimResultat:
    """
    Kör en fullständig simulation med nuvarande strategy.py.
    Returnerar SimResultat.
    """
    bolag = strategy.BOLAG
    zon   = strategy.ZON

    try:
        data = ladda_data()
    except FileNotFoundError as e:
        return SimResultat(
            bolag=bolag, zon=zon,
            n_artiklar_total=0, n_tilldelade=0, max_platser=0,
            paafyllningar_totalt=0, paafyllningar_reguljara=0,
            paafyllningar_tvangsbyte=0,
            onodiga_returer=0, onodiga_returer_pct=0,
            serviceniva_pct=0, tvangsbyte_pct=0,
            experiment_id=experiment_id,
            fel=str(e)
        )

    max_platser = config.MAX_PICKPLATSER_GG_A

    stats_lista = beräkna_artikelstatistik(data, bolag, zon)
    tilldelade  = tilldela_plockplatser(stats_lista, max_platser)
    sim         = simulera(data, stats_lista, tilldelade, bolag)

    if "fel" in sim:
        return SimResultat(
            bolag=bolag, zon=zon,
            n_artiklar_total=len(stats_lista), n_tilldelade=len(tilldelade),
            max_platser=max_platser,
            paafyllningar_totalt=0, paafyllningar_reguljara=0,
            paafyllningar_tvangsbyte=0,
            onodiga_returer=0, onodiga_returer_pct=0,
            serviceniva_pct=0, tvangsbyte_pct=0,
            experiment_id=experiment_id,
            fel=sim["fel"]
        )

    return SimResultat(
        bolag=bolag,
        zon=zon,
        n_artiklar_total=len(stats_lista),
        n_tilldelade=len(tilldelade),
        max_platser=max_platser,
        paafyllningar_totalt=sim["paafyllningar_totalt"],
        paafyllningar_reguljara=sim["paafyllningar_reguljara"],
        paafyllningar_tvangsbyte=sim["paafyllningar_tvangsbyte"],
        onodiga_returer=sim["onodiga_returer"],
        onodiga_returer_pct=sim["onodiga_returer_pct"],
        serviceniva_pct=sim["serviceniva_pct"],
        tvangsbyte_pct=sim["tvangsbyte_pct"],
        experiment_id=experiment_id,
        fel=None,
    )
