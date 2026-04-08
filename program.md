# program.md – Agentinstruktioner

Du är en optimeringsagent. Ditt mål är att minimera **totalt antal påfyllningar**
(pallrörelser i lagret) genom att hitta den bästa strategin för vilka artiklar
som ska ha plockplatser.

---

## Din arbetsloop

1. Läs senaste resultatet i `results/` (om det finns)
2. Läs nuvarande `strategy.py`
3. Gör EN förändring i `strategy.py` (se nedan vad du får ändra)
4. Kör: `python run.py`
5. Läs output – jämför `total_paafyllningar` mot tidigare bästa
6. Om bättre: kopiera `strategy.py` till `best/strategy_YYYYMMDD_HHMMSS.py`
7. Upprepa från steg 1

Ändra **en sak i taget**. Gör inte flera förändringar samtidigt – du kan inte
veta vilken förändring som hjälpte.

---

## Vad du FÅR ändra

Allt i `strategy.py` är tillåtet att modifiera:
- Tröskelvärdena (`THRESHOLD_STANNA`, `THRESHOLD_LAMNA`)
- Vikterna (`WEIGHT_*`)
- Kampanj-logiken och tröskeln
- `score_article()`-funktionen – du får lägga till nya faktorer
- `should_force_remove()`-funktionen – regler för när artikel tvingat ska lämna

Du FÅR INTE:
- Ändra `simulate.py`
- Ändra `run.py`
- Ändra `config.py`
- Ändra datafiler i `data/`

---

## Vad du optimerar

**Primärt mål**: minimera `total_paafyllningar` i resultatet från `run.py`

**Sekundära mål** (lägre vikt, men håll ett öga på dem):
- Håll `serviceniva_pct` ≥ 85% (artiklar som behövdes och fanns på plockplats)
- Håll `tvangsbyte_pct` så lågt som möjligt
- Håll `onodiga_returer_pct` (artiklar som kom tillbaka inom 3 dagar) < 15%

Om en förändring minskar påfyllningar men bryter servicenivå under 85%, ska du
INTE behålla förändringen.

---

## Domänbegränsningar (KRITISKA – bryt dem aldrig)

- GG och MG behandlas ALLTID separat
- Artiklar med `has_buffer = False` och `freq_2day < 0.30` FÅR INTE tas bort
  från plockplats (plockrisk om ingen buffert finns)
- Ny pall kan INTE placeras på hyllplats (platskod slutar på bokstav)
- Max antal plockplatser = värdet i `config.py` (`MAX_PICKPLATSER`)
- En artikel är "i sortimentet" om den är med i tvådagarsfönstret (se CLAUDE.md)

---

## Nulägesbaseline
*Uppdateras automatiskt av run.py efter varje körning*

```
Senaste körning  : [ej kört ännu]
total_paafyllningar : -
serviceniva_pct     : -
tvangsbyte_pct      : -
onodiga_returer_pct : -
```

---

## Idéer att testa (prioriterade)

1. **Fyradimensionell scoring** – lägg till butiksbredd och vecka-till-vecka stabilitet
   som egna faktorer i `score_article()`, inte bara frekvens
2. **Dynamisk buffer-vikt** – artiklar med buffer kan lämna mer aggressivt,
   artiklar utan buffer ska ha extra hög score för att stanna
3. **Säsongsjustering** – artiklar aldrig plockade senaste 14 dagarna trots att
   de HAR plockats tidigare kan vara säsongsartiklar, inte döda artiklar
4. **Tröskelvärdes-sökning** – testa `THRESHOLD_STANNA` i steg om 5% (0.40–0.80)
   och `THRESHOLD_LAMNA` i steg om 5% (0.10–0.40)
5. **Kampanj-detektering** – finslipa toppighets-tröskeln; testa 0.50–0.85
6. **Forced removal-logik** – när plats måste frigöras, välj artikeln med lägst
   `score / days_on_location` (dvs. lägst avkastning på platsen den ockuperat)

---

## Resultatformat (från run.py)
```
=== EXPERIMENT RESULTAT ===
Körning        : 2026-04-08 14:32:11
Bolag/Zon      : GG / A
Artiklar total : 1 842
Tilldelade     : 1 341 / 1 364 platser (98.3%)

Påfyllningar totalt    : 4 821  ← MINIMERA DETTA
  varav regelbundna    : 3 102
  varav tvångsbyte     : 1 719
Onödiga returer (<3d)  : 312   (18.2%)
Servicenivå            : 87.4%
Tvångsbyte-%           : 71.3%

Bästa hittills         : 4 821
Delta från bästa       : 0 (=)
===========================
```
