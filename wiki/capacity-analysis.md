# Kapacitetsanalys

## GG A-zon – nuläge
| Mätvärde | Antal |
|----------|-------|
| Totalt antal plockplatser | 1 364 |
| Uppfyllda | 1 323 |
| **Lediga** | **41** |
| Beläggningsgrad | **96,9%** |

### Uppdelning av lediga platser
| Typ | Lediga |
|-----|--------|
| Vanliga (pallplatser) | **23** |
| Hyllplatser | 23 |

**Vanliga pallplatser är den kritiska resursen.** Ny pall kan inte placeras på hyllplats → hyllplatser substituerar inte.

## Tvångsbyte per zon
| Bolag | Zon | Tvångsbyte% | Kommentar |
|-------|-----|------------|-----------|
| GG | A | 82,5% | Kritisk – primär fokus |
| GG | SK | 89,6% | Hög men lägre prioritet |
| MG | A | 71% | Inte akut (2 185 lediga platser) |
| MG | Brand | **98,3%** | MG:s kritiska zon |

## Frigjord kapacitet vid aktiv sortimentsstyrning
Med kategoribaserad styrning kan ~349 artiklar flytta till buffert:
- **~59 extra pallplatser** frigörs
- Ger en **planeringshorisont** – kan planera om sortiment i förväg istället för att reagera

## Återkomst efter tvångsbyte
- **26–30%** av utbytta artiklar återkommer till plockplats inom 3 dagar
- Det innebär att flytten var onödig – artikeln borde aldrig ha lämnat

## Väntetid (tid mellan OUT och nästa IN på samma plats)
Mäts i `efficiency.py` via `WaitTimeDistribution`. Låg väntetid = tecken på kapacitetstryck (plats fylls omedelbart).

## Beläggningsdefinitioner

### Plockplats
- **Ledig** = ingen artikel tilldelad (`Plocksaldo = 0` och inte i pick_location_log som aktiv)
- **0-saldo** = artikel tilldelad men `Plocksaldo = 0` (tom pall eller tömd hylla)
- **Uppfylld** = artikel tilldelad med `Plocksaldo > 0`

### Matriser i appen
Båda matriserna (`zon × ägare`, `förvaringsform × ägare`) visar triplet:
```
ledig / ledig+0-saldo / total
```

## Se även
- [Problemdefinition](problem-definition.md) – rotproblemet och dess konsekvenser
- [Sortimentskategorier](sortiment-categories.md) – vilka artiklar som kan frigöra platser
- [Lagerplatstaxonomi](location-taxonomy.md) – hur platser klassificeras
