import glob
import os

from pipeline.schema import load_card, load_chance, load_street_card
from pipeline.verify import quote_passes, street_card_passes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "content", "cards")
STREET = os.path.join(ROOT, "content", "street")
CHANCE = os.path.join(ROOT, "content", "chance")

# 有合格引语的 POI,见 content/VERIFIED_CONTENT.md
POIS_WITH_QUOTE = {"tour-eiffel", "pantheon", "jardin-palais-royal",
                   "palais-garnier"}


def _cards():
    return [load_card(p) for p in sorted(glob.glob(os.path.join(CARDS, "*.json")))]


def test_ten_cards_seven_r_three_sr():
    cards = _cards()
    assert len(cards) == 10
    assert len([c for c in cards if c.rarity == "R"]) == 7
    assert len([c for c in cards if c.rarity == "SR"]) == 3


def test_card_ids_unique():
    ids = [c.id for c in _cards()]
    assert len(ids) == len(set(ids))


def test_every_quote_present_passes_the_gate():
    for c in _cards():
        if c.quote is not None:
            assert quote_passes(c.quote), f"{c.id} has an unverified quote"


def test_only_verified_pois_carry_quotes():
    for c in _cards():
        if c.quote is not None:
            assert c.poi_id in POIS_WITH_QUOTE, (
                f"{c.id} carries a quote for a POI with no verified source")


def test_five_street_cards_all_pass_gate():
    cards = [load_street_card(p)
             for p in sorted(glob.glob(os.path.join(STREET, "*.json")))]
    assert len(cards) == 5
    for c in cards:
        assert street_card_passes(c), f"{c.id} fails the street-card gate"


def test_street_cards_cover_four_categories():
    cats = {load_street_card(p).category
            for p in glob.glob(os.path.join(STREET, "*.json"))}
    assert cats == {"rule", "transit", "etiquette", "trivia"}


def test_three_chance_questions_answer_in_range():
    qs = [load_chance(p) for p in sorted(glob.glob(os.path.join(CHANCE, "*.json")))]
    assert len(qs) == 3
    for q in qs:
        assert 0 <= q["answer_index"] < len(q["options_zh"])
        assert len(q["options_zh"]) == len(q["options_en"])
