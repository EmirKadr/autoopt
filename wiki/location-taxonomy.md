# Lagerplatstaxonomi – Klassificeringsregler

## Tre dimensioner
Varje plockplats klassificeras längs tre dimensioner:

| Dimension | Möjliga värden |
|-----------|---------------|
| **Ägare** | Granngården, Mestergruppen, Exkluderad |
| **Zon** | A, SK, Brand, Grav, KAM, UTE, EH, Ej klassad |
| **Förvaringsform** | Vanlig (pallplats), Hyllplats, Krattplats, Ej tillämpligt |

Klassificeringen baseras enbart på **platskoden** (`Lagerplats`-kolumnen i `location-*.csv`).

## Hyllplats vs Vanlig (pallplats)
**Kritisk distinktion.** Ny pall kan **inte** placeras på hyllplats.

- Platskod slutar på **bokstav** → Hyllplats (ex. `BK09012A`)
- Platskod slutar på **siffra** → Vanlig/pallplats (ex. `BK09012`)

## Regelmatris (15 regler, prioritetsordning)

| # | Mönster | Ägare | Zon | Förvaringsform | Kommentar |
|---|---------|-------|-----|----------------|-----------|
| 1 | `BA*` | Exkluderad | Ej klassad | Ej tillämpligt | BA ska inte räknas in |
| 2 | `AA03A–AA14C` | Granngården | A | Krattplats | Vanlig zon med egen lagringsform |
| 3 | `AA23–AA69` | Granngården | Grav | Ej tillämpligt | Automatisk påfyllning (gravitation) |
| 4 | `AA15–AA22`, `AA70–AA75` | Granngården | A | Ej tillämpligt | Övriga AA-platser |
| 5 | `ZBRAND*`, `EXPLO*` | Granngården | Brand | Ej tillämpligt | Brandplatser |
| 6 | `BN*` | Granngården | EH | Bokstav sist → Hyllplats, annars Vanlig | E-handelsgång |
| 7 | `BO*`, `BP*`, `BQ*` | Granngården | SK | Bokstav sist → Hyllplats, annars Vanlig | Skrymmande B-zoner |
| 8 | `SK*` | Granngården | SK | Ej tillämpligt | Skrymmande specialplatser |
| 9 | `KAM*` | Granngården | KAM | Ej tillämpligt | Kampanjplatser |
| 10 | `UTE*` | Granngården | UTE | Ej tillämpligt | Palltak |
| 11 | Övriga `B*` | Granngården | A | Bokstav sist → Hyllplats, annars Vanlig | B-prefix ej matchat tidigare |
| 12 | `M1BR*`, `M2BR*`, `MBR*` | Mestergruppen | Brand | Bokstav sist → Hyllplats, annars Vanlig | Brandplockplatser |
| 13 | `MGOLV*`, `MLIST*` | Mestergruppen | SK | Bokstav sist → Hyllplats, annars Vanlig | Skrymmande plockplatser |
| 14 | `L*` | Mestergruppen | A | Bokstav sist → Hyllplats, annars Vanlig | Ordinarie plockplatser |
| 15 | Allt övrigt | Exkluderad | Ej klassad | Ej tillämpligt | Ingen matchande regel i v1 |

Reglerna tillämpas i nummerordning – första träff gäller.

## Exempelplatser per regel

| Platskod | Regel | Klassificering |
|----------|-------|---------------|
| `AA03A`, `AA14C` | 2 | GG / A / Krattplats |
| `AA23`, `AA69` | 3 | GG / Grav / Ej tillämpligt |
| `AA15`, `AA75` | 4 | GG / A / Ej tillämpligt |
| `ZBRAND01011`, `EXPLO01` | 5 | GG / Brand / Ej tillämpligt |
| `BN01012A` | 6 | GG / EH / Hyllplats |
| `BN01013` | 6 | GG / EH / Vanlig |
| `BO01012A`, `BP11021` | 7 | GG / SK / Hyllplats/Vanlig |
| `KAM01` | 9 | GG / KAM / Ej tillämpligt |
| `UTE11` | 10 | GG / UTE / Ej tillämpligt |
| `M1BR01011` | 12 | MG / Brand / Vanlig |
| `M2BR07012A` | 12 | MG / Brand / Hyllplats |
| `MGOLV10` | 13 | MG / SK / Vanlig |
| `LA03011` | 14 | MG / A / Vanlig |
| `LA03012A` | 14 | MG / A / Hyllplats |
| `BA01011` | 1 | Exkluderad |
| `SPECIAL 1`, `24PORT` | 15 | Exkluderad |

## Exkluderingar
- `BA*` exkluderas alltid.
- Koder utan matchande regel → Exkluderad med orsak "Ingen matchande regel".
- Exkluderade rader visas i GUI och export men räknas inte in under GG eller MG.
- `Krattplats` är en förvaringsform, inte en zon.

## Datakälla och filformat
- Fil: senaste `location-*.csv` i `data/`
- Appen använder **endast** rader där `Typ = P` (plockplatser)
- Format: tabbseparerad CSV

## Se även
- [Datakällor](data-sources.md) – om location-filen och andra CSV-filer
- [Kapacitetsanalys](capacity-analysis.md) – hur klassificeringen används i kapacitetsberäkningar
