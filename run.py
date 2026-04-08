"""
run.py – Kör ett experiment och loggar resultatet
==================================================
Användning:
    python run.py
    python run.py --id "test-tröskelvärden"

Skriver resultat till results/YYYYMMDD_HHMMSS.json och uppdaterar
program.md med senaste körningens nyckeltal.
"""

import os
import sys
import json
import argparse
import shutil
from datetime import datetime

import simulate
import strategy
import config


# ---------------------------------------------------------------------------
# HJÄLPFUNKTIONER
# ---------------------------------------------------------------------------

def bästa_resultat() -> int:
    """Läser bästa total_paafyllningar från results/-mappen."""
    bäst = None
    if not os.path.exists(config.RESULTS_DIR):
        return None
    for f in os.listdir(config.RESULTS_DIR):
        if not f.endswith(".json"):
            continue
        with open(os.path.join(config.RESULTS_DIR, f)) as fh:
            try:
                d = json.load(fh)
                v = d.get("paafyllningar_totalt")
                if v is not None and (bäst is None or v < bäst):
                    bäst = v
            except Exception:
                pass
    return bäst


def spara_resultat(res: simulate.SimResultat, tidsstämpel: str) -> str:
    """Sparar resultatet som JSON i results/."""
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    filnamn = os.path.join(config.RESULTS_DIR, f"{tidsstämpel}.json")
    data = {
        "experiment_id":              res.experiment_id,
        "tidsstämpel":                tidsstämpel,
        "bolag":                      res.bolag,
        "zon":                        res.zon,
        "n_artiklar_total":           res.n_artiklar_total,
        "n_tilldelade":               res.n_tilldelade,
        "max_platser":                res.max_platser,
        "paafyllningar_totalt":       res.paafyllningar_totalt,
        "paafyllningar_reguljara":    res.paafyllningar_reguljara,
        "paafyllningar_tvangsbyte":   res.paafyllningar_tvangsbyte,
        "onodiga_returer":            res.onodiga_returer,
        "onodiga_returer_pct":        round(res.onodiga_returer_pct, 1),
        "serviceniva_pct":            round(res.serviceniva_pct, 1),
        "tvangsbyte_pct":             round(res.tvangsbyte_pct, 1),
        # Parametrar från strategy.py (för reproducerbarhet)
        "strategy_params": {
            "THRESHOLD_STANNA":            strategy.THRESHOLD_STANNA,
            "THRESHOLD_LAMNA":             strategy.THRESHOLD_LAMNA,
            "WEIGHT_FREQUENCY":            strategy.WEIGHT_FREQUENCY,
            "WEIGHT_BUTIK_BREDD":          strategy.WEIGHT_BUTIK_BREDD,
            "WEIGHT_STABILITET":           strategy.WEIGHT_STABILITET,
            "KAMPANJ_TOPPIGHET_THRESHOLD": strategy.KAMPANJ_TOPPIGHET_THRESHOLD,
            "KAMPANJ_PENALTY":             strategy.KAMPANJ_PENALTY,
        },
    }
    with open(filnamn, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return filnamn


def spara_bästa_strategi(tidsstämpel: str):
    """Kopierar nuvarande strategy.py till best/-mappen."""
    os.makedirs(config.BEST_DIR, exist_ok=True)
    källa = os.path.join(os.path.dirname(__file__), "strategy.py")
    mål   = os.path.join(config.BEST_DIR, f"strategy_{tidsstämpel}.py")
    shutil.copy2(källa, mål)
    return mål


def uppdatera_program_md(res: simulate.SimResultat, tidsstämpel: str, är_bäst: bool):
    """Uppdaterar nulägesblocket i program.md med senaste körningens nyckeltal."""
    pm_sökväg = os.path.join(os.path.dirname(__file__), "program.md")
    if not os.path.exists(pm_sökväg):
        return

    with open(pm_sökväg, encoding="utf-8") as fh:
        innehåll = fh.read()

    nytt_block = (
        f"```\n"
        f"Senaste körning  : {tidsstämpel}\n"
        f"total_paafyllningar : {res.paafyllningar_totalt}\n"
        f"serviceniva_pct     : {res.serviceniva_pct:.1f}%\n"
        f"tvangsbyte_pct      : {res.tvangsbyte_pct:.1f}%\n"
        f"onodiga_returer_pct : {res.onodiga_returer_pct:.1f}%\n"
        f"```"
    )

    # Ersätt blocket mellan "## Nulägesbaseline" och nästa "---"
    import re
    nytt = re.sub(
        r"```\nSenaste körning.*?```",
        nytt_block,
        innehåll,
        flags=re.DOTALL
    )

    if nytt != innehåll:
        with open(pm_sökväg, "w", encoding="utf-8") as fh:
            fh.write(nytt)


def skriv_utskrift(res: simulate.SimResultat, bäst_tidigare: int, tidsstämpel: str):
    """Skriver formaterat resultat till stdout."""
    print()
    print("=" * 45)
    print("  EXPERIMENT RESULTAT")
    print("=" * 45)
    print(f"  Körning        : {tidsstämpel}")
    if res.experiment_id:
        print(f"  ID             : {res.experiment_id}")
    print(f"  Bolag/Zon      : {res.bolag} / {res.zon}")
    print(f"  Artiklar total : {res.n_artiklar_total:,}")
    print(f"  Tilldelade     : {res.n_tilldelade:,} / {res.max_platser:,} platser "
          f"({res.n_tilldelade/max(res.max_platser,1)*100:.1f}%)")
    print()
    print(f"  Påfyllningar totalt    : {res.paafyllningar_totalt:,}  ← MINIMERA DETTA")
    print(f"    varav reguljära      : {res.paafyllningar_reguljara:,}")
    print(f"    varav tvångsbyte     : {res.paafyllningar_tvangsbyte:,}")
    print(f"  Onödiga returer (<3d)  : {res.onodiga_returer:,}  ({res.onodiga_returer_pct:.1f}%)")
    print(f"  Servicenivå            : {res.serviceniva_pct:.1f}%")
    print(f"  Tvångsbyte-%           : {res.tvangsbyte_pct:.1f}%")
    print()

    if bäst_tidigare is None:
        print(f"  Bästa hittills         : {res.paafyllningar_totalt:,}  (FÖRSTA KÖRNING)")
    else:
        delta = res.paafyllningar_totalt - bäst_tidigare
        tecken = "+" if delta > 0 else ("−" if delta < 0 else "=")
        förbättring = "✓ NY BÄSTA!" if delta < 0 else ("✗ Sämre" if delta > 0 else "= Oförändrad")
        print(f"  Bästa hittills         : {bäst_tidigare:,}")
        print(f"  Delta från bästa       : {tecken}{abs(delta):,}  {förbättring}")

    # Varning om servicenivå är för låg
    if res.serviceniva_pct < 85.0:
        print()
        print("  ⚠ VARNING: Servicenivå under 85% – behåll inte denna strategi!")

    print("=" * 45)
    print()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Kör ett autoresearch-experiment")
    parser.add_argument("--id", default="", help="Valfritt experiment-ID")
    args = parser.parse_args()

    tidsstämpel = datetime.now().strftime("%Y%m%d_%H%M%S")
    bäst_innan  = bästa_resultat()

    print(f"\nKör simulation... (bolag={strategy.BOLAG}, zon={strategy.ZON})")

    res = simulate.kör_simulation(experiment_id=args.id or tidsstämpel)

    if res.fel:
        print(f"\n❌ FEL: {res.fel}")
        print("Kontrollera att datafiler finns i data/ och att config.py pekar rätt.")
        sys.exit(1)

    # Skriv utskrift
    skriv_utskrift(res, bäst_innan, tidsstämpel)

    # Spara resultat
    sparad_fil = spara_resultat(res, tidsstämpel)
    print(f"  Sparat: results/{tidsstämpel}.json")

    # Om bättre: spara strategi
    är_bäst = bäst_innan is None or res.paafyllningar_totalt < bäst_innan
    if är_bäst:
        bäst_fil = spara_bästa_strategi(tidsstämpel)
        print(f"  Ny bästa sparad: best/strategy_{tidsstämpel}.py")

    # Uppdatera program.md
    uppdatera_program_md(res, tidsstämpel, är_bäst)
    print(f"  program.md uppdaterad med senaste nyckeltal\n")


if __name__ == "__main__":
    main()
