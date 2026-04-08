"""
strategy.py – Strategi för plockplatstilldelning
=================================================
DETTA ÄR FILEN SOM AGENTEN MODIFIERAR.

Innehåller:
  - Parametrar (tröskelvärden, vikter)
  - score_article()       – poängsätter en artikel; högre = mer prioriterad för plockplats
  - should_force_remove() – bestämmer om en artikel MÅSTE lämna plockplats

simulate.py anropar dessa funktioner. Ändra inte signaturer.
"""

# ---------------------------------------------------------------------------
# PARAMETRAR
# ---------------------------------------------------------------------------

# Bolag och zon att optimera
BOLAG = "GG"
ZON   = "A"

# Frekvenstörskel – tvådagarsfrekvens (0.0 – 1.0)
# Artiklar ≥ THRESHOLD_STANNA: stark kandidat att behålla
# Artiklar < THRESHOLD_LAMNA:  kandidat att ta bort (om de har buffert)
THRESHOLD_STANNA = 0.60
THRESHOLD_LAMNA  = 0.30

# Vikter i score_article()
WEIGHT_FREQUENCY   = 1.0   # Tvådagarsfrekvens – starkaste signalen
WEIGHT_BUTIK_BREDD = 0.3   # Andel unika butiker som beställt artikeln
WEIGHT_STABILITET  = 0.2   # Vecka-till-vecka konsistens (0 = kaotisk, 1 = jämn)

# Kampanjartiklar
# Toppighet = andel av picks koncentrerade till topp-3 dagar av aktiv period
# Om toppighet > KAMPANJ_TOPPIGHET_THRESHOLD → markeras som kampanjartikel
KAMPANJ_TOPPIGHET_THRESHOLD = 0.70
KAMPANJ_PENALTY             = 0.50  # Multiplicera score med detta för kampanjartiklar

# Säsongsartiklar
# Om artikel inte plockats senaste SASONG_INAKTIV_DAGAR men har historik = möjlig säsongsartikel
# Ge dessa en liten extra bonus (de är inte döda, bara vilande)
SASONG_INAKTIV_DAGAR = 14
SASONG_BONUS         = 0.10

# Buffer-bonus: artiklar MED buffert är säkrare att hålla kvar (de kan snabbt fyllas på)
# Artiklar UTAN buffert och låg frekvens är de svåraste – de FÅR EJ tas bort
BUFFER_BONUS = 0.05

# ---------------------------------------------------------------------------
# SCORE_ARTICLE – poängsätter en artikel
# ---------------------------------------------------------------------------

def score_article(
    freq_2day: float,       # Tvådagarsfrekvens (0.0–1.0)
    n_butiker_frac: float,  # Andel av totala butiker som beställt (0.0–1.0)
    stabilitet: float,      # Vecka-till-vecka stabilitet (0.0–1.0)
    is_kampanj: bool,       # Är artikeln en kampanjartikel?
    has_buffer: bool,       # Har artikeln en buffertpall?
    days_since_last_pick: int,  # Dagar sedan senaste plockning
    has_any_history: bool,  # Har artikeln plockats någon gång under perioden?
) -> float:
    """
    Returnerar en prioritetsscore. Högre = artikel bör prioriteras för plockplats.

    Rangordning av faktorer:
    1. Frekvens är den viktigaste signalen
    2. Butiksbredd (bred efterfrågan = stabilare behov)
    3. Stabilitet (konsekvent = mer förutsägbar)
    4. Buffer-status (påverkar risk vid borttagning)
    5. Kampanjprofil (nedviktar artificiellt höga frekvenser)
    """
    score = 0.0

    # Grundpoäng baserat på frekvens
    score += freq_2day * WEIGHT_FREQUENCY

    # Butiksbredd – ju fler butiker som beställer, desto mer stabil efterfrågan
    score += n_butiker_frac * WEIGHT_BUTIK_BREDD

    # Stabilitet – jämn efterfrågan är bättre än ojämn
    score += stabilitet * WEIGHT_STABILITET

    # Buffer-bonus – artiklar med buffert är lättare att hantera
    if has_buffer:
        score += BUFFER_BONUS

    # Säsongsbonus – artikel som vilat men HAR historik (inte en dödvariant)
    if days_since_last_pick >= SASONG_INAKTIV_DAGAR and has_any_history:
        score += SASONG_BONUS

    # Kampanjstraff – nedvikta tillfälliga toppar
    if is_kampanj:
        score *= (1.0 - KAMPANJ_PENALTY)

    return score


# ---------------------------------------------------------------------------
# SHOULD_FORCE_REMOVE – artikel MÅSTE lämna plockplats
# ---------------------------------------------------------------------------

def should_force_remove(
    freq_2day: float,
    has_buffer: bool,
    days_on_location: int,
    total_picks_on_location: int,
) -> bool:
    """
    Returnerar True om artikeln AKTIVT ska frigöras från plockplats.

    Används för proaktiv sortering – inte tvångsbyte (som sker av kapacitetsbrist).
    En artikel som returnerar True är en frivillig kandidat för utflytt till buffert.

    KRITISK REGEL: Om has_buffer = False och freq_2day < THRESHOLD_LAMNA,
    returnera ALLTID False (kan inte ta bort utan buffert).
    """
    # Säkerhetsregel: aldrig ta bort artikel utan buffert och låg frekvens
    if not has_buffer and freq_2day < THRESHOLD_LAMNA:
        return False

    # Aldrig plockad på platsen → klart kandidat
    if total_picks_on_location == 0 and days_on_location > 7:
        return True

    # Mycket låg frekvens OCH har buffert → kan frigöras
    if freq_2day < THRESHOLD_LAMNA and has_buffer:
        return True

    return False
