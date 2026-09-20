from pipeline.models import Quote, StreetCard
from pipeline.verify import quote_passes, street_card_passes, filter_street_cards


def _q(**kw):
    base = dict(text_zh="x", text_original="x", source="S1E1",
                source_url="https://a.example", verified=True)
    base.update(kw)
    return Quote(**base)


def test_quote_passes_when_complete():
    assert quote_passes(_q()) is True


def test_quote_rejected_when_unverified():
    assert quote_passes(_q(verified=False)) is False


def test_quote_rejected_when_source_blank():
    assert quote_passes(_q(source="")) is False
    assert quote_passes(_q(source_url="")) is False


def test_quote_rejected_when_none():
    assert quote_passes(None) is False


def _s(**kw):
    base = dict(id="a", category="rule", text_zh="x", text_en="x",
                near_poi_id="p", sources=["https://a.example", "https://b.example"],
                verified=True)
    base.update(kw)
    return StreetCard(**base)


def test_street_card_passes_with_two_sources():
    assert street_card_passes(_s()) is True


def test_street_card_rejected_with_one_source():
    assert street_card_passes(_s(sources=["https://a.example"])) is False


def test_street_card_rejected_when_unverified():
    assert street_card_passes(_s(verified=False)) is False


def test_filter_street_cards_drops_failures():
    good, bad = _s(id="good"), _s(id="bad", verified=False)
    assert [c.id for c in filter_street_cards([good, bad])] == ["good"]
