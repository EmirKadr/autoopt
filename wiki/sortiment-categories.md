# Sortimentskategorier

## De fem kategorierna

| Kategori | Kriterium | Ca antal (GG A-zon) | Handling |
|----------|-----------|---------------------|----------|
| **Stanna alltid** | ≥60% tvådagarsfrekvens | ~377 | Behåll på plockplats |
| **Mellanzon** | 30–60% | ~466 | Bevakas – kan stanna eller lämna |
| **Kan lämna** | <30% OCH har buffert | ~297 | Kandidat för utflytt |
| **Kritisk** | <30% OCH saknar buffert | ~217 | Får ej lämna utan att buffert ordnas |
| **Aldrig plockad** | 0 plockningar på 29 dagar | ~52 | Prioritet för utflytt |

**Standardtrösklar:** `THRESHOLD_STANNA = 60%`, `THRESHOLD_LAMNA = 30%` (justerbara i appen).

## Tvådagarsfrekvens – definition
Andelen dagar (av totalt analyserade orderdagar) då en artikel är **med i sortimentet för ett tvådagarsfönster**. En artikel räknas som "i fönstret" om den är med i antingen dagens avgång eller morgondagens förtidig plockning.

Beräkningsgrund: join av `pick_log_full` mot `order_log` via `Ordernr` för att fastställa orderdagar.

## Buffert-kriteriets roll
En artikel i kategorin "Kan lämna" **har buffert** → kan lämna plockplats utan risk för servicefall.
En artikel i kategorin "Kritisk" **saknar buffert** → att flytta ut den skapar direkt plockrisk.

Buffertdata hämtas från `article_buffertpallet-*`.

## Kampanjartiklar – nedviktning
Kampanjartiklar ska **inte** räknas som "Stanna alltid" trots tillfälligt hög volym. Känns igen på:
- Hög toppighet (plockvolymen koncentrerad till få dagar)
- Kort aktiv period (2–10 dagar, inte månader)
- Bred synkad distribution (många butiker tar emot samma artikel samtidigt)

Exempel: PLASTKRUKA STRIPES, MONSTER DOG BONE BROTH, BLUNDSTONE 400.

Hantering: nedvikta kampanjprofilen i tvådagarsfrekvens-beräkningen (ej fullt implementerat ännu).

## Framtida modeldimensioner
Enbart plockfrekvens är otillräckligt. En bättre modell bör väga fyra dimensioner:

| Dimension | Beskrivning |
|-----------|-------------|
| **Närvarofrekvens** | Tvådagarsfrekvens (nuvarande metod) |
| **Butiksbredd** | Hur många unika butiker beställer artikeln |
| **Stabilitet** | Vecka-till-vecka konsistens (inte bara totalt) |
| **Kampanjprofil** | Toppighet – identifierar kampanjartiklar för nedviktning |

## Effekt av aktiv sortimentsstyrning
Med aktiv styrning baserad på kategorierna kan ~349 artiklar frigöras till buffert, vilket skapar ~59 extra pallplatser och en **planeringshorisont** istället för reaktiva beslut.

## Se även
- [Problemdefinition](problem-definition.md) – varför sortimentsstyrning behövs
- [Kapacitetsanalys](capacity-analysis.md) – var de frigjorda platserna finns
- [Datakällor](data-sources.md) – pick_log och order_log för frekvensberäkning
