# autoopt – Automatiserad plockplatsoptimering

## Syfte
Hitta den optimala strategin för att välja vilka artiklar som ska ha plockplatser,
med målet att **minimera totalt antal påfyllningar** (pallrörelser).

Projektet använder en autoresearch-loop: en LLM-agent modifierar `strategy.py`,
kör `run.py`, utvärderar resultatet, och upprepar tills ingen förbättring hittas.

## Filstruktur och ansvar

| Fil | Vad den gör | Vem äger den |
|-----|-------------|--------------|
| `program.md` | Agentinstruktioner – vad som ska optimeras, regler, idéer | Människa (du) |
| `strategy.py` | Parametrar och poängsättningsfunktion | **Agenten modifierar** |
| `simulate.py` | Laddar data, simulerar, räknar påfyllningar | Agenten rör EJ |
| `run.py` | Kör ett experiment, skriver till `results/` | Agenten kör |
| `config.py` | Sökvägar till datafiler | Människa justerar |
| `results/` | Logg över alla experiment (append-only) | Agenten skriver |
| `best/` | Kopia av bästa strategy.py hittills | Agenten sparar hit |
| `wiki/` | Domänkunskap portad från Platsanalys | Referens |
| `data/` | CSV-datafiler (pekas ut i config.py) | Källdata, rör ej |

## Kritiska domänregler (FÅR EJ BRYTAS)

- **Separera alltid GG och MG** – använd `Bolag`-kolumnen, aldrig platsnamnsmönster
- **Hyllplats ≠ pallplats** – platskod slutar på bokstav = hyllplats. Ny pall kan INTE
  placeras på hyllplats. Räkna bara vanliga pallplatser i kapacitetsberäkningar.
- **pick_log ≠ pick_location_log**
  - `pick_log_full` = plockaktivitet (vad plockades och när)
  - `pick_location_log` = platstilldelning (IN/OUT-händelser för artiklar på platser)
- **Tvångsbyte-definition**: ny artikel på samma plats inom 24h efter att förra lämnade
  = kapacitetstryck, inte aktivt val
- **Tvådagarsfönster**: en artikel är "i sortimentet" dag D om den är med i avgången D
  ELLER förtidsplockning för avgång D+1. Beräkna alltid frekvens mot detta fönster.
- **Buffer-krav**: en artikel med `<30%` frekvens som SAKNAR buffertpall FÅR EJ
  tas bort från plockplats – det skapar omedelbar plockrisk.
- **Kampanjartiklar**: hög kortsiktig volym = inte "stanna"-kandidat. Känns igen på
  toppighet (>70% av picks på topp-3 dagar) och kort aktiv period (<14 dagar).

## Kapacitetsläge GG A-zon (referensvärden)
- 1 364 plockplatser totalt
- ~23 lediga vanliga pallplatser (hyllplatser substituerar inte)
- 82,5% av artikelbyten är tvångsbyte idag
- 28% av utbytta artiklar behövs tillbaka inom 3 dagar

## Datafiler (se config.py för sökvägar)
Alla CSV-filer är tabbseparerade (`\t`), UTF-8-sig, namngivna med timestamp.

| Fil | Innehåll |
|-----|----------|
| `pick_log_full-*.csv` | Plockaktivitet – artikel, datum, ordernr, bolag, zon |
| `pick_location_log-*.csv` | IN/OUT på platser – artikel, plats, timestamp, bolag |
| `v_ask_article_buffertpallet-*.csv` | Vilka artiklar har buffertpall och var |
| `location-*.csv` | Platsmasterlista – Lagerplats, Typ (P=plock), klassificering |
| `v_ask_order_log-*.csv` | Orderhuvuden – datum, avgångsdatum |
| `v_ask_customer_order_details_all-*.csv` | Orderrader (ingen rubrikrad, col 5=ArtNr, col 24=Bolag) |

## Ingest av ny data
1. Lägg nya CSV-filer i `data/`
2. Uppdatera `config.py` med nya filnamn (timestamp-baserade)
3. Kör `python run.py` för att verifiera att data läses in korrekt

## Se även
- `wiki/problem-definition.md` – rotproblemet och varför det är svårt
- `wiki/sortiment-categories.md` – de fem kategorierna och tröskelvärdena
- `wiki/data-sources.md` – exakt vad varje CSV-fil innehåller
