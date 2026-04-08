# Datakällor – CSV-filer och tolkningsram

## Logistikflödet som helhet
Se datan som ett sammanhängande flöde:

```
inleverans → ej inlagrat → buffert/lager → order & plock → interna rörelser → korrigeringar → dispatch/utleverans → prognos framåt
```

Varje filtyp representerar ett specifikt steg eller en specifik vy i det flödet.

---

## Filtyper och tolkningsram

### Nulägesbilder (snapshot)
Beskriver aktuellt tillstånd vid exporttillfället. Förändras nästa gång data hämtas.

| Filnamn (prefix) | Innehåll | Nyckelkolumner |
|-----------------|----------|---------------|
| `location-*` | Masterlista för alla lagerplatser (typ P=plock, B=buffert) | Lagerplats, Typ, Detalj |
| `item_summary_stock_automation-*` | Saldo per artikel: plock, automation, autoplock | Artikel, Plockplats, Bolag, Plocksaldo, Buffertsaldo, Klassificering |
| `article_buffertpallet-*` | Aktuella buffertpallar – var de står, vilken artikel, antal på pall | Lagerplats, Artikel, Antal, Bolag |
| `booking_putaway-*` | Mottaget gods som ännu inte lagts in (ej inlagrat) | – |
| `order_overview-*` | Orderhuvuden på övergripande nivå: avgång, transportör, status, vikt, antal rader | – |
| `customer_order_details_all-*` | Orderrader på detaljnivå – vilka artiklar som ska plockas till varje order | Col 24=Bolag, Col 5=ArtNr, Col 6=ArtNamn, Col 17=OrdNr, Col 27=RobotArtikeln |
| `item_option-*` | Artikelmasterdata och artikelregler: plockzon, robotplock, ej staplingsbar | – |

### Händelseloggar (historik)
Append-only historik. Varje rad är en händelse med tidsstämpel.

| Filnamn (prefix) | Innehåll | Nyckelkolumner |
|-----------------|----------|---------------|
| `pick_log_full-*` | **Plockaktivitet** – vad som plockades, när och var | Datum, Lokation, Artikelnr, Ordernr, Bolag, Zon |
| `pick_location_log-*` | **Plockplatstilldelning** – IN/OUT-händelser för artiklar på platser | Artikel, Tidigare plats, Ny plats, Bolag, Timestamp |
| `receive_log-*` | Mottagningshistorik för inkommande gods | – |
| `trans_log-*` | Historik över interna lagerförflyttningar | – |
| `correct_log-*` | Saldojusteringar, inventeringsavvikelser och korrigeringar | – |
| `assignment_move-*` | Palluppdrag/arbetsuppdrag för pallhantering och flytt | – |
| `dispatch_pallet-*` | Utgående pallar kopplade till leveranser/utlastning | – |

### Planeringsdata
Framåtblickande. Används för att förutse behov.

| Filnamn (prefix) | Innehåll |
|-----------------|----------|
| prognosfiler | Framtida behov per artikel eller kampanjvolymer per vecka |

---

## Kritiska distinktioner

### pick_log_full vs pick_location_log
**Får inte blandas ihop.**

| | pick_log_full | pick_location_log |
|-|--------------|------------------|
| **Vad** | Plockaktivitet (vad som plockades) | Platstilldelning (vad som finns var) |
| **Användning** | Mäter efterfrågan, frekvens, orderdagar | Källa för tvångsbyte-analys |
| **Händelse** | En rad = ett plockuttag | En rad = en IN- eller OUT-händelse på en plats |

### Orderdag-beräkning
`Datum` i pick_log = när det plockades. `Order datum` i order_overview = när ordern skickades. Orderdag beräknas genom att koppla `pick_log.Ordernr → order_log.Ordernr`. Ca 30% plockas dagen före avgång (förtidsplock), 70% samma dag.

### Bolag-identifiering
Använd alltid kolumnen `Bolag` för att separera GG och MG. **Använd inte** platsnamnsmönster – de överlappar ibland.

### customer_order_details_all – kolumnindex
Filen saknar rubrikrad. Viktiga positioner:
- Col 5 = Artikelnummer
- Col 6 = Artikelnamn
- Col 17 = Ordernummer
- Col 24 = Bolag
- Col 27 = RobotArtikel (flagga för automation)

---

## Filformat
Alla CSV-filer är:
- **Tabbseparerade** (`\t`)
- **UTF-8-sig** enkodade
- Namngivna med **timestamp** (`filnamn-YYYYMMDDHHMMSS.csv`)
- Hanterade av **Git LFS** (stora filer lagras inte direkt i repo)

Hämta alltid senaste versionen via tidsstämpeln i filnamnet.

---

## Se även
- [Problemdefinition](problem-definition.md) – varför pick_location_log är kritisk för tvångsbyte
- [Lagerplatstaxonomi](location-taxonomy.md) – hur location-*.csv klassificeras
