# Problemdefinition – Platsanalys

## Rotproblemet
Fel artiklar upptar plockplatserna. Det finns ingen aktiv beslutsprocess för vilka artiklar som ska ha fast plockplats — det styrs av tröghet och slump. Resultatet är reaktiv brandkårsutryckning istället för aktiv sortimentsstyrning.

## Konsekvenser (mätta för GG A-zon)
- **82%** av alla artikelbyten är kapacitetstvångsbyte — ny artikel tvingade ut den förra
- **28%** av utbytta artiklar behövs tillbaka på plockplats inom 3 dagar (onödigt dubbelarbete)
- **~54 platsrörelser per dag**, varav en stor del är onödiga
- Lågfrekvensartiklar blockerar platser som högfrekvensartiklar behöver

Det är **inte** ett kapacitetsproblem — det är ett **sortimentsstyrningsproblem**.

## 30/70-regeln och tvådagarsperspektivet
~30% av ordrar plockas dagen **före** avgång (förtidsplock). ~70% plockas **samma dag**. Det innebär att kapacitetsbehovet alltid måste räknas i ett tvådagars-fönster: dagens avgång + morgondagens förtidig plockning. En artikel som "lämnar" sortimentet idag kan fortfarande behövas imorgon.

→ Konsekvens: en article räknas som "i sortimentet" om den är med i minst en av de två dagarna i fönstret.

## Kapacitetsläge GG A-zon
- 1 364 plockplatser totalt
- 1 323 uppfyllda → **41 lediga** (96% beläggning)
- Av de 41 lediga är bara **23 vanliga pallplatser** (hyllplatser kan inte ta emot ny pall)
- Aktiv sortimentsstyrning kan frigöra ~349 artiklar till buffert → ~59 extra pallplatser → planeringshorisont istället för reaktiva beslut

## Tvångsbyte-definition
| Typ | Kriterium |
|-----|-----------|
| **Kapacitetstvång** | Ny artikel placerades på platsen inom **24 timmar** efter att förra åkte ut |
| **Aktivt val** | Platsen stod tom **>24 timmar** innan ny artikel placerades |

Källa: `v_ask_pick_location_log` (placeringshistorik, inte plockaktivitet).

## Tvångsbyte per zon
| Zon | Tvångsbyte% |
|-----|------------|
| GG A | 82,5% |
| GG SK | 89,6% |
| GG Brand | – |
| MG A | 71% |
| MG Brand | **98,3%** |

MG A är inte ett akut problem (2 185 lediga platser). MG:s kritiska zon är Brand.

## Orderrytm
- ~41,5 butiker/dag i genomsnitt, 47,5 på fredagar
- 104 butiker, 2 499 orderhuvuden, 30 orderdagar analyserade (feb–mar 2026)
- Samma butik har mycket låg likhet till nästa leverans (Jaccard ~0,038) — behovsstyrd, inte standardiserad
- Kedjan totalt är dock stabil: **91,5% av artiklarna återkommer månad till månad**

## Öppna frågor
- Hur valideras 60%/30%-trösklarna mot verksamhetens erfarenhet?
- Säsongsartiklar: hur skiljer vi "aldrig plockad pga fel säsong" från "utgånget sortiment"?
- Hantering av ~6 000 artiklar från platser utan matchande namnregel ("Övrigt"-kategorin)

## Se även
- [Sortimentskategorier](sortiment-categories.md) – hur artiklar klassificeras
- [Kapacitetsanalys](capacity-analysis.md) – detaljerat kapacitetsläge
- [Datakällor](data-sources.md) – pick_log vs pick_location_log
