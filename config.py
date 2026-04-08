"""
config.py – Sökvägar och konfiguration
=======================================
Justera DATA_DIR och filnamnen nedan när du lägger till ny data.
Filnamnen är timestamp-baserade (YYYYMMDDHHMMSS).
"""

import os

# ---------------------------------------------------------------------------
# SÖKVÄGAR
# ---------------------------------------------------------------------------

# Mapp där CSV-filerna ligger
# Ändra till den faktiska sökvägen på din dator, t.ex.:
#   DATA_DIR = r"C:\Users\emikad\projects\Platsanalys\data"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Mapp för experimentresultat
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# Mapp för bästa strategier
BEST_DIR = os.path.join(os.path.dirname(__file__), "best")

# ---------------------------------------------------------------------------
# DATAFILER – uppdatera timestamps när du lägger till ny data
# ---------------------------------------------------------------------------

# Plockaktivitet – vad som plockades och när
PICK_LOG_FILE = "v_ask_pick_log_full-20260327111807.csv"

# Plockplatstilldelning – IN/OUT-händelser
PICK_LOCATION_LOG_FILE = "v_ask_pick_location_log-20260327111817.csv"

# Buffertpallar – vilka artiklar har buffert och var
BUFFERT_FILE = "v_ask_article_buffertpallet-20260327111741.csv"

# Platsmasterlista – alla lagerplatser med typ och klassificering
LOCATION_FILE = "location-20260327111812.csv"

# Orderhuvuden – koppling Ordernr → avgångsdatum
ORDER_LOG_FILE = "v_ask_order_log-20260327111749.csv"

# Orderrader – vilka artiklar per order (ingen rubrikrad)
ORDER_DETAILS_FILE = "v_ask_customer_order_details_all-20260327111808.csv"

# ---------------------------------------------------------------------------
# KAPACITET OCH SIMULERINGSPARAMETRAR
# ---------------------------------------------------------------------------

# Max antal plockplatser i GG A-zon (vanliga pallplatser)
MAX_PICKPLATSER_GG_A = 1364

# Uppskattad kapacitet per plockplats (enheter per pall)
# Används för att beräkna hur ofta en plats behöver fyllas på
# Justera baserat på verklig pallstorlek om du har den datan
UPPSKATTAD_PALLSTORLEK = 200

# Analysperiod – hur många dagar bakåt att analysera
# Sätts till None för att använda hela datatillgängliga perioden
ANALYS_DAGAR = 30

# Tvångsbyte-fönster – max timmar mellan ut och in för att räknas som tvångsbyte
TVANGSBYTE_TIMMAR = 24

# Retur-fönster – max dagar för att räknas som "onödig retur"
ONÖDIG_RETUR_DAGAR = 3

# ---------------------------------------------------------------------------
# KOLUMNNAMN (ändra om CSV-strukturen skiljer sig)
# ---------------------------------------------------------------------------

# pick_log_full kolumner
COL_PICK_DATUM      = "Datum"
COL_PICK_ARTIKEL    = "Artikelnr"
COL_PICK_ORDERNR    = "Ordernr"
COL_PICK_BOLAG      = "Bolag"
COL_PICK_ZON        = "Zon"
COL_PICK_LOKATION   = "Lokation"

# pick_location_log kolumner
COL_LOC_ARTIKEL     = "Artikel"
COL_LOC_NY_PLATS    = "Ny plats"
COL_LOC_TIDIG_PLATS = "Tidigare plats"
COL_LOC_BOLAG       = "Bolag"
COL_LOC_TIMESTAMP   = "Timestamp"

# article_buffertpallet kolumner
COL_BUF_ARTIKEL     = "Artikel"
COL_BUF_BOLAG       = "Bolag"
COL_BUF_LAGERPLATS  = "Lagerplats"

# location kolumner
COL_LOC_LAGERPLATS  = "Lagerplats"
COL_LOC_TYP         = "Typ"  # P = plockplats

# order_log kolumner
COL_ORD_ORDERNR     = "Ordernr"
COL_ORD_AVGANGSDATUM = "Avgångsdatum"

# customer_order_details (ingen rubrikrad – använd kolumnindex)
COL_DET_ARTIKEL_IDX = 5    # Col 5 = Artikelnummer
COL_DET_ARTIKEL_NAMN_IDX = 6  # Col 6 = Artikelnamn
COL_DET_ORDERNR_IDX = 17   # Col 17 = Ordernummer
COL_DET_BOLAG_IDX   = 24   # Col 24 = Bolag
COL_DET_ROBOT_IDX   = 27   # Col 27 = RobotArtikel
