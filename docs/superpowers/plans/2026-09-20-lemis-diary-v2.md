# Lemi's Diary v2 实现计划(大富翁玩法 + 双模式)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Lemi's Diary 从静态信息清单重做为"大富翁玩法 + 集卡体系"的交互游戏,并保留一个只读的 storymap 式图鉴模式。

**Architecture:** 复用 v1 的 Python 构建管线与三层数据模型,新增棋盘/卡牌/引语/街头卡四类数据与 `verified` 构建时过滤;前端推倒重做,按职责拆成 core/game/codex 三组小模块,纯静态 CDN 引入,无构建工具。

**Tech Stack:** Python 3.11(标准库 + requests)、原生 JS、MapLibre GL(CDN)、Scrollama.js(CDN)、pytest

**Spec:** `docs/superpowers/specs/2026-09-20-lemis-diary-v2-board-game.md`

## Global Constraints

- 纯静态站:无后端、无账号、无构建工具;所有第三方库经 CDN 引入
- 坐标约定:全局以 `[lat, lng]` 存储,**仅在传给 MapLibre 时**转为 `[lng, lat]`
- 双语:数据层双语存储(`_zh`/`_en`),展示层单语切换,缺译文回退另一语言
- `MapLibre flyTo` 调用**必须带 `essential: true`**,否则 reduced-motion 下降级为 jumpTo
- Scrollama:CSS **禁用 vh 单位**(滚动触发 resize);移动端 offset 用 px 不用 %;**不得置于 iframe**
- 动效时长(spec 第 5.2 节,精确值):骰子按下 100ms + 翻滚 400ms;步行 ≤1000ms;掉卡 = 出片 150ms + 显影 350ms + 定影 100ms;其他格子统一 3000ms
- `prefers-reduced-motion` 时所有动效退化为 200ms 淡入淡出
- 触控目标 ≥ 44px
- **不做任何音效**
- 卡册计数分母为 10(7 R + 3 SR),SSR 不计入
- 图鉴模式**不读写 localStorage**(`lemi_lang` 除外),不显示任何进度
- commit message 遵循 Conventional Commits

## Review Focus

以下五类输入 spec 未明写但真实用户会遇到,每条已在对应任务补了测试:

1. **localStorage 不可用**(隐私模式/写满):游戏应仍可玩,降级为不保存 → Task 5
2. **状态版本迁移**:结构变更时不得清空用户已收集卡册 → Task 5
3. **骰子点数超过剩余格数**:应走到终点为止,不得越界索引 → Task 8
4. **重复游玩已收集的卡**:不得重复计入卡册计数 → Task 5
5. **卡面图片加载失败**:卡片仍须可读,不得出现空白卡 → Task 9

---

## 文件结构

**前端(推倒重做)**

```
web/
  templates/
    board.html        游戏模式主页面
    codex.html        图鉴模式主页面
  assets/
    core/
      i18n.js         pickLang + 语言切换(复用 v1 逻辑)
      storage.js      localStorage 读写 + 版本迁移 + 不可用降级
      mapkit.js       MapLibre 初始化 + flyTo/panTo 封装
    game/
      dice.js         骰子点数生成 + 动效
      pawn.js         Lemi 棋子移动
      card.js         卡片显影 + 翻面
      tiles.js        五类格子触发逻辑
      collection.js   卡册(剪影占位)
      game.js         主循环编排
    codex/
      codex.js        Scrollama 滚动叙事(只读)
    styles/
      base.css        设计 token
      game.css        游戏模式
      codex.css       图鉴模式
```

**后端(增量修改)**

```
pipeline/
  models.py       + BoardTile / Quote / Card / StreetCard
  schema.py       + load_card / load_street_card / load_board
  verify.py       (新) verified gate
  board_gen.py    (新) 棋盘生成:保底1格 + 余量按距离分配
  build_site.py   payload 增加 board / cards / street_cards
  run_paris.py    编排
```

**内容**

```
content/
  boards/emily-in-paris.json
  cards/paris-*.json          7 R + 3 SR
  street/paris-*.json         5 条(经交叉验证)
  chance/paris-*.json         3 条
```

---

## Task 1: 数据模型扩展

**Files:**
- Modify: `pipeline/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: 现有 `ImageRef`、`meets_threshold`
- Produces: `BoardTile`、`Quote`、`Card`、`StreetCard` 四个 dataclass,供 Task 2/3/4 使用

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_models.py`:

```python
from pipeline.models import BoardTile, Card, Quote, StreetCard


def test_board_tile_defaults():
    t = BoardTile(index=0, type="poi", lat=48.8, lng=2.3)
    assert t.poi_id == ""
    assert t.content_id == ""


def test_quote_requires_source_fields():
    q = Quote(text_zh="你好", text_original="Bonjour",
              source="S1E1", source_url="https://example.com", verified=True)
    assert q.verified is True


def test_card_quote_optional():
    c = Card(id="paris-flore-r", rarity="R", storyline_id="emily-in-paris")
    assert c.quote is None
    assert c.image is None


def test_street_card_sources_list():
    s = StreetCard(id="paris-bonjour", category="etiquette",
                   text_zh="进店先说 Bonjour", text_en="Say Bonjour",
                   near_poi_id="cafe-de-flore",
                   sources=["https://a.example", "https://b.example"],
                   verified=True)
    assert len(s.sources) == 2
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_models.py -v -k "board_tile or quote or card or street"`
Expected: FAIL — `ImportError: cannot import name 'BoardTile'`

- [ ] **Step 3: 实现**

追加到 `pipeline/models.py` 末尾:

```python
TILE_TYPES = ("poi", "chance", "photo", "street", "easter")
RARITIES = ("R", "SR", "SSR")
STREET_CATEGORIES = ("rule", "transit", "etiquette", "trivia")


@dataclass
class BoardTile:
    """One square on the board; POI squares point at a shared POI."""

    index: int
    type: str
    lat: float
    lng: float
    poi_id: str = ""
    content_id: str = ""


@dataclass
class Quote:
    """A handwritten-font quote on a card. Every field is required."""

    text_zh: str
    text_original: str
    source: str
    source_url: str
    verified: bool


@dataclass
class Card:
    """A collectible card dropped when landing on a POI or easter-egg tile."""

    id: str
    rarity: str
    storyline_id: str
    poi_id: str = ""
    image: Optional[ImageRef] = None
    title_zh: str = ""
    title_en: str = ""
    body_zh: str = ""
    body_en: str = ""
    quote: Optional[Quote] = None


@dataclass
class StreetCard:
    """A Paris street-knowledge card shown on street tiles."""

    id: str
    category: str
    text_zh: str
    text_en: str
    near_poi_id: str
    sources: List[str] = field(default_factory=list)
    verified: bool = False
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS(含 v1 原有用例)

- [ ] **Step 5: 提交**

```bash
git add pipeline/models.py tests/test_models.py
git commit -m "feat(models): add BoardTile, Quote, Card, StreetCard for v2 board game"
```

---

## Task 2: verified 构建时 gate

**Files:**
- Create: `pipeline/verify.py`
- Test: `tests/test_verify.py`

**Interfaces:**
- Consumes: Task 1 的 `Quote`、`StreetCard`
- Produces: `quote_passes(quote) -> bool`、`street_card_passes(card) -> bool`、`filter_street_cards(cards) -> List[StreetCard]`,供 Task 4 的 build_site 使用

- [ ] **Step 1: 写失败测试**

Create `tests/test_verify.py`:

```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_verify.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.verify'`

- [ ] **Step 3: 实现**

Create `pipeline/verify.py`:

```python
"""Build-time gate for content whose accuracy must be checked, not self-rated.

Quotes and street cards are rejected unless they carry real sources and have
been marked verified by the cross-check / adversarial-review pass. LLM
self-rated confidence is deliberately not accepted here.
"""
from __future__ import annotations

from typing import List, Optional

from pipeline.models import Quote, StreetCard

MIN_STREET_SOURCES = 2


def quote_passes(quote: Optional[Quote]) -> bool:
    """Return True if the quote is verified and carries a real source."""
    if quote is None:
        return False
    if not quote.verified:
        return False
    return bool(quote.source.strip()) and bool(quote.source_url.strip())


def street_card_passes(card: Optional[StreetCard]) -> bool:
    """Return True if the street card is verified and cross-checked."""
    if card is None:
        return False
    if not card.verified:
        return False
    return len([s for s in card.sources if s.strip()]) >= MIN_STREET_SOURCES


def filter_street_cards(cards: List[StreetCard]) -> List[StreetCard]:
    """Drop every street card that fails the gate."""
    return [c for c in cards if street_card_passes(c)]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_verify.py -v`
Expected: PASS(9 个用例)

- [ ] **Step 5: 提交**

```bash
git add pipeline/verify.py tests/test_verify.py
git commit -m "feat(verify): reject unsourced quotes and under-cited street cards at build time"
```

---

## Task 3: 棋盘生成器

**Files:**
- Create: `pipeline/board_gen.py`
- Test: `tests/test_board_gen.py`

**Interfaces:**
- Consumes: Task 1 的 `BoardTile`;现有 `POI`、`StoryLine`、`stops_for_storyline`
- Produces: `haversine_km(a, b) -> float`、`allocate_filler(gaps, total) -> List[int]`、`interpolate(a, b, frac) -> Tuple[float, float]`、`build_board(storyline, pois, filler_plan) -> List[BoardTile]`,供 Task 4 使用

**背景(已实测):** 相邻 POI 间距极不均衡——公寓→先贤祠仅 0.21 km,歌剧院→桥 1.61 km,桥→铁塔 1.94 km。纯按距离加权会让 0.21 km 区间分到 **0 格**,导致两个 POI 格紧邻、摇到 2 就连吃两个 POI。因此采用**保底 1 格 + 余量按距离分配**,实测得 `[1,2,2,2,3,3]`,合计 13 个路途格 + 7 个 POI 格 = 20 格。

- [ ] **Step 1: 写失败测试**

Create `tests/test_board_gen.py`:

```python
from pipeline.board_gen import allocate_filler, haversine_km, interpolate


def test_haversine_known_distance():
    # Emily 的公寓 → 先贤祠,实测约 0.21 km
    d = haversine_km((48.8443, 2.3487), (48.8462, 2.3464))
    assert 0.15 < d < 0.30


def test_allocate_filler_gives_every_gap_at_least_one():
    gaps = [0.21, 1.14, 1.25, 0.84, 1.61, 1.94]
    out = allocate_filler(gaps, 13)
    assert sum(out) == 13
    assert min(out) >= 1


def test_allocate_filler_longer_gap_gets_more():
    gaps = [0.21, 1.14, 1.25, 0.84, 1.61, 1.94]
    out = allocate_filler(gaps, 13)
    assert out[5] > out[0]  # 1.94km 段应多于 0.21km 段


def test_allocate_filler_handles_total_equal_to_gap_count():
    assert allocate_filler([1.0, 2.0, 3.0], 3) == [1, 1, 1]


def test_allocate_filler_raises_when_total_too_small():
    try:
        allocate_filler([1.0, 2.0, 3.0], 2)
    except ValueError:
        return
    raise AssertionError("expected ValueError when total < number of gaps")


def test_interpolate_midpoint():
    lat, lng = interpolate((0.0, 0.0), (2.0, 4.0), 0.5)
    assert abs(lat - 1.0) < 1e-9
    assert abs(lng - 2.0) < 1e-9
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_board_gen.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.board_gen'`

- [ ] **Step 3: 实现**

Create `pipeline/board_gen.py`:

```python
"""Generate the board: POI squares in storyline order, filler squares between.

POI spacing on a real storyline is very uneven (0.21 km between Emily's flat
and the Panthéon, 1.94 km from the bridge to the tower). Allocating filler
purely by distance would give the shortest gap zero squares, putting two POI
squares back to back. Every gap therefore gets at least one filler square,
and the remainder is distributed by distance.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

from pipeline.models import BoardTile, POI, StoryLine
from pipeline.schema import stops_for_storyline

EARTH_RADIUS_KM = 6371.0


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Great-circle distance in km between two (lat, lng) points."""
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat = lat2 - lat1
    dlng = math.radians(b[1] - a[1])
    h = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def allocate_filler(gaps: List[float], total: int) -> List[int]:
    """Split `total` filler squares across gaps: one each, rest by distance.

    Uses the largest-remainder method for the distance-weighted part so the
    counts sum exactly to `total`.
    """
    if total < len(gaps):
        raise ValueError(
            f"need at least one filler per gap: total={total} gaps={len(gaps)}")
    counts = [1] * len(gaps)
    remaining = total - len(gaps)
    if remaining == 0:
        return counts
    span = sum(gaps)
    raw = [g / span * remaining for g in gaps]
    extra = [int(r) for r in raw]
    short = remaining - sum(extra)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - extra[i], reverse=True)
    for i in order[:short]:
        extra[i] += 1
    return [c + e for c, e in zip(counts, extra)]


def interpolate(a: Tuple[float, float], b: Tuple[float, float],
                frac: float) -> Tuple[float, float]:
    """Linearly interpolate between two (lat, lng) points."""
    return (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac)


def build_board(storyline: StoryLine, pois: Dict[str, POI],
                filler_plan: List[str], total_filler: int = 13) -> List[BoardTile]:
    """Build the ordered board for a storyline.

    filler_plan is the ordered list of filler tile types to consume, e.g.
    ["street", "chance", "photo", "easter", ...]. It must contain at least
    total_filler entries; extras are ignored.
    """
    stops = stops_for_storyline(storyline)
    coords = [(pois[s.poi_id].lat, pois[s.poi_id].lng) for s in stops]
    gaps = [haversine_km(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]
    counts = allocate_filler(gaps, total_filler)

    tiles: List[BoardTile] = []
    cursor = 0
    for i, stop in enumerate(stops):
        lat, lng = coords[i]
        tiles.append(BoardTile(index=len(tiles), type="poi",
                               lat=lat, lng=lng, poi_id=stop.poi_id))
        if i >= len(counts):
            continue
        n = counts[i]
        for k in range(n):
            frac = (k + 1) / (n + 1)
            flat, flng = interpolate(coords[i], coords[i + 1], frac)
            ttype = filler_plan[cursor % len(filler_plan)]
            cursor += 1
            tiles.append(BoardTile(index=len(tiles), type=ttype,
                                   lat=flat, lng=flng))
    return tiles
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_board_gen.py -v`
Expected: PASS(6 个用例)

- [ ] **Step 5: 加棋盘整体结构的测试**

追加到 `tests/test_board_gen.py`:

```python
import glob
import json
import os

from pipeline.board_gen import build_board
from pipeline.schema import load_poi, load_storyline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILLER_PLAN = ["street", "chance", "photo", "street", "easter", "street",
               "chance", "photo", "street", "easter", "chance", "street",
               "easter"]


def _load_real():
    pois = {}
    for p in glob.glob(os.path.join(ROOT, "content", "pois", "*.json")):
        poi = load_poi(p)
        pois[poi.id] = poi
    sl = load_storyline(os.path.join(ROOT, "content", "storylines",
                                     "emily-in-paris.json"))
    return sl, pois


def test_real_board_has_twenty_tiles():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    assert len(tiles) == 20


def test_real_board_starts_and_ends_on_poi():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    assert tiles[0].type == "poi"
    assert tiles[0].poi_id == "place-estrapade"
    assert tiles[-1].type == "poi"
    assert tiles[-1].poi_id == "tour-eiffel"


def test_no_two_poi_tiles_adjacent():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    for a, b in zip(tiles, tiles[1:]):
        assert not (a.type == "poi" and b.type == "poi")


def test_indices_are_sequential():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    assert [t.index for t in tiles] == list(range(20))
```

- [ ] **Step 6: 运行确认通过**

Run: `python -m pytest tests/test_board_gen.py -v`
Expected: PASS(10 个用例)

- [ ] **Step 7: 提交**

```bash
git add pipeline/board_gen.py tests/test_board_gen.py
git commit -m "feat(board): generate 20-tile board with min-one-filler allocation"
```

---

## Task 4: 内容加载器

**Files:**
- Modify: `pipeline/schema.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Consumes: Task 1 的四个 dataclass;现有 `_read`、`_image_from_dict`
- Produces: `load_card(path) -> Card`、`load_street_card(path) -> StreetCard`、`load_chance(path) -> dict`,供 Task 6 的 build_site 使用

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_schema.py`:

```python
import json
import os
import tempfile

from pipeline.schema import load_card, load_chance, load_street_card


def _write(tmpdir, name, obj):
    p = os.path.join(tmpdir, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def test_load_card_with_quote():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "c.json", {
            "id": "paris-tour-eiffel-r", "rarity": "R",
            "storyline_id": "emily-in-paris", "poi_id": "tour-eiffel",
            "title_zh": "埃菲尔铁塔", "title_en": "Eiffel Tower",
            "body_zh": "正文", "body_en": "body",
            "quote": {"text_zh": "译文", "text_original": "orig",
                      "source": "La Vie errante, 1890",
                      "source_url": "https://fr.wikisource.org/x",
                      "verified": True},
        })
        card = load_card(p)
        assert card.rarity == "R"
        assert card.quote is not None
        assert card.quote.verified is True


def test_load_card_without_quote():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "c.json", {
            "id": "paris-cafe-de-flore-r", "rarity": "R",
            "storyline_id": "emily-in-paris", "poi_id": "cafe-de-flore",
            "title_zh": "花神咖啡馆", "title_en": "Cafe de Flore",
            "body_zh": "正文", "body_en": "body",
        })
        assert load_card(p).quote is None


def test_load_street_card():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "s.json", {
            "id": "paris-bonjour", "category": "etiquette",
            "text_zh": "进店先说 Bonjour", "text_en": "Say Bonjour first",
            "near_poi_id": "place-estrapade",
            "sources": ["https://a.example", "https://b.example"],
            "verified": True,
        })
        s = load_street_card(p)
        assert s.category == "etiquette"
        assert len(s.sources) == 2


def test_load_chance_question():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "q.json", {
            "id": "paris-eiffel-petition",
            "question_zh": "铁塔当年被多少艺术家联名反对?",
            "question_en": "How many artists signed the protest?",
            "options_zh": ["7 位", "47 位", "300 位"],
            "options_en": ["7", "47", "300"],
            "answer_index": 1,
            "explain_zh": "1887 年《反对埃菲尔铁塔抗议书》有 47 人签署。",
            "explain_en": "The 1887 protest carried 47 signatures.",
        })
        q = load_chance(p)
        assert q["answer_index"] == 1
        assert len(q["options_zh"]) == 3
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_schema.py -v -k "load_card or load_street or load_chance"`
Expected: FAIL — `ImportError: cannot import name 'load_card'`

- [ ] **Step 3: 实现**

在 `pipeline/schema.py` 的 import 行追加 `Card, Quote, StreetCard`,并在 `load_storyline` 之后插入:

```python
def _quote_from_dict(d: Optional[dict]) -> Optional[Quote]:
    if not d:
        return None
    return Quote(
        text_zh=d.get("text_zh", ""), text_original=d.get("text_original", ""),
        source=d.get("source", ""), source_url=d.get("source_url", ""),
        verified=bool(d.get("verified", False)),
    )


def load_card(path: str) -> Card:
    """Load a collectible card from a JSON file."""
    d = json.loads(_read(path))
    return Card(
        id=d["id"], rarity=d["rarity"], storyline_id=d["storyline_id"],
        poi_id=d.get("poi_id", ""),
        image=_image_from_dict(d.get("image")),
        title_zh=d.get("title_zh", ""), title_en=d.get("title_en", ""),
        body_zh=d.get("body_zh", ""), body_en=d.get("body_en", ""),
        quote=_quote_from_dict(d.get("quote")),
    )


def load_street_card(path: str) -> StreetCard:
    """Load a street-knowledge card from a JSON file."""
    d = json.loads(_read(path))
    return StreetCard(
        id=d["id"], category=d["category"],
        text_zh=d.get("text_zh", ""), text_en=d.get("text_en", ""),
        near_poi_id=d.get("near_poi_id", ""),
        sources=list(d.get("sources", [])),
        verified=bool(d.get("verified", False)),
    )


def load_chance(path: str) -> dict:
    """Load a chance-tile quiz question. Returned as a plain dict."""
    return json.loads(_read(path))
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_schema.py -v`
Expected: PASS(含 v1 原有用例)

- [ ] **Step 5: 提交**

```bash
git add pipeline/schema.py tests/test_schema.py
git commit -m "feat(schema): load cards, street cards and chance questions"
```

---

## Task 5: 内容文件填充

**Files:**
- Create: `content/cards/paris-*.json`(10 个:7 R + 3 SR)
- Create: `content/street/paris-*.json`(5 个)
- Create: `content/chance/paris-*.json`(3 个)
- Create: `content/boards/emily-in-paris.json`
- Test: `tests/test_content_files.py`

**Interfaces:**
- Consumes: Task 4 的 `load_card`/`load_street_card`/`load_chance`;Task 2 的 gate 函数
- Produces: 内容文件本身,供 Task 6 构建 payload

**内容来源:** 全部取自 `content/VERIFIED_CONTENT.md`(已完成交叉验证 + 对抗性审查)。**不得自行编写新的引语或街头卡**;该文件未收录的 POI 一律不设 quote 字段。

- [ ] **Step 1: 写失败测试**

Create `tests/test_content_files.py`:

```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_content_files.py -v`
Expected: FAIL — 目录不存在,`len(cards) == 10` 断言失败(实际 0)

- [ ] **Step 3: 建目录并写 7 张 R 卡**

`content/cards/paris-place-estrapade-r.json`(无 quote,VERIFIED_CONTENT 未收录):

```json
{
  "id": "paris-place-estrapade-r",
  "rarity": "R",
  "storyline_id": "emily-in-paris",
  "poi_id": "place-estrapade",
  "title_zh": "埃斯特拉帕德广场",
  "title_en": "Place de l'Estrapade",
  "body_zh": "Emily 在巴黎的家,剧中那扇绿色大门 No.1 是全球剧迷的打卡起点。剧集播出后,现实中这栋楼的居民不堪其扰——每天大量游客来门口拍照。安静的拉丁区小广场因此变成了'网红'地标。",
  "body_en": "Emily's home in Paris; the green door at No.1 is where fans start their pilgrimage. After the show aired, residents were overwhelmed by daily crowds photographing the door. A quiet Latin Quarter square turned into a viral landmark."
}
```

`content/cards/paris-pantheon-r.json`(带 quote):

```json
{
  "id": "paris-pantheon-r",
  "rarity": "R",
  "storyline_id": "emily-in-paris",
  "poi_id": "pantheon",
  "title_zh": "先贤祠",
  "title_en": "Panthéon",
  "body_zh": "先贤祠安葬着伏尔泰、卢梭、雨果、左拉、居里夫人等法国伟人。原为路易十五还愿建造的圣女热纳维耶芙教堂,法国大革命后改为安葬伟人的世俗先贤祠。傅科摆最早在此进行地球自转实验。",
  "body_en": "The Panthéon holds the tombs of Voltaire, Rousseau, Hugo, Zola and Marie Curie. Built as the church of Sainte-Geneviève on a vow of Louis XV, it became a secular mausoleum after the Revolution. Foucault first demonstrated the Earth's rotation with his pendulum here.",
  "quote": {
    "text_zh": "祖国感念伟人",
    "text_original": "Aux grands hommes la patrie reconnaissante",
    "source": "先贤祠正立面山花楣铭文,源自 1791 年制宪议会法令",
    "source_url": "https://fr.wikipedia.org/wiki/Panth%C3%A9on_(Paris)",
    "verified": true
  }
}
```

`content/cards/paris-cafe-de-flore-r.json`(**无 quote** — 萨特名句查不到一手出处):

```json
{
  "id": "paris-cafe-de-flore-r",
  "rarity": "R",
  "storyline_id": "emily-in-paris",
  "poi_id": "cafe-de-flore",
  "title_zh": "花神咖啡馆",
  "title_en": "Café de Flore",
  "body_zh": "萨特与波伏娃在此写作、辩论,是存在主义哲学的诞生地之一;加缪、毕加索也是常客。创立于 1887 年,'花神'得名于对面的一尊花神芙罗拉雕像。二战后成为法国知识分子的据点。",
  "body_en": "Sartre and Beauvoir wrote and debated here, making it a birthplace of existentialism; Camus and Picasso were regulars. Founded in 1887, the 'Flore' is named after a statue of the goddess Flora that once stood opposite. After WWII it became a hub for French intellectuals."
}
```

`content/cards/paris-jardin-palais-royal-r.json`(带 quote,取前半句):

```json
{
  "id": "paris-jardin-palais-royal-r",
  "rarity": "R",
  "storyline_id": "emily-in-paris",
  "poi_id": "jardin-palais-royal",
  "title_zh": "皇家宫殿花园",
  "title_en": "Jardin du Palais-Royal",
  "body_zh": "花园里的布伦黑白条纹柱阵(Les Deux Plateaux)是巴黎最著名的当代艺术打卡点之一。作家科莱特长住于此;这里也是《午夜巴黎》《天使爱美丽》等多部电影钟爱的取景地。建于 17 世纪,曾是法国大革命的舆论策源地之一。",
  "body_en": "Buren's black-and-white striped columns (Les Deux Plateaux) are one of Paris's most famous contemporary-art photo spots. The writer Colette lived here for years; it is also a beloved location for Midnight in Paris and Amélie. Built in the 17th century, it was a seedbed of Revolutionary opinion.",
  "quote": {
    "text_zh": "我们从未看得够,永远看得不够。",
    "text_original": "Nous ne regardons, nous ne regarderons jamais assez.",
    "source": "科莱特《我窗前的巴黎》(Paris de ma fenêtre),写于 1940-1944 年皇家宫殿寓所",
    "source_url": "https://www.amisdecolette.fr/ressources/citations/",
    "verified": true
  }
}
```

`content/cards/paris-palais-garnier-r.json`(带 quote):

```json
{
  "id": "paris-palais-garnier-r",
  "rarity": "R",
  "storyline_id": "emily-in-paris",
  "poi_id": "palais-garnier",
  "title_zh": "加尼叶歌剧院",
  "title_en": "Palais Garnier",
  "body_zh": "加斯东·勒鲁的小说《歌剧魅影》即以此歌剧院为背景,地下湖、包厢 No.5 都是小说元素;夏加尔为其绘制了穹顶壁画。1875 年落成,建筑师夏尔·加尼叶设计,是拿破仑三世第二帝国建筑风格的代表。",
  "body_en": "Gaston Leroux's The Phantom of the Opera is set in this very house — the underground lake and Box No.5 are drawn from it; Chagall painted the ceiling fresco. Completed in 1875 to a design by Charles Garnier, it exemplifies the Second Empire style.",
  "quote": {
    "text_zh": "歌剧院的幽灵确曾存在。",
    "text_original": "Le fantôme de l'Opéra a existé.",
    "source": "加斯东·勒鲁《歌剧魅影》序言开篇第一句,Pierre Lafitte,1910",
    "source_url": "https://www.livredepoche.com/livre/le-fantome-de-lopera-9782253009504/",
    "verified": true
  }
}
```

`content/cards/paris-pont-alexandre-iii-r.json`(无 quote):

```json
{
  "id": "paris-pont-alexandre-iii-r",
  "rarity": "R",
  "storyline_id": "emily-in-paris",
  "poi_id": "pont-alexandre-iii",
  "title_zh": "亚历山大三世桥",
  "title_en": "Pont Alexandre III",
  "body_zh": "被公认为巴黎最华丽的桥,金色飞马、天使雕像出自多位法国雕塑家之手,是美好年代建筑艺术的巅峰之作。建于 1896-1900 年,为 1900 年巴黎世博会而建,以俄国沙皇亚历山大三世命名,象征法俄同盟。日落时分金色雕塑最美。",
  "body_en": "Widely regarded as the most ornate bridge in Paris, its gilded winged horses and angels are the work of several French sculptors — a pinnacle of Belle Époque architecture. Built 1896-1900 for the World's Fair, named after Tsar Alexander III to mark the Franco-Russian alliance. The gilding is at its best at sunset."
}
```

`content/cards/paris-tour-eiffel-r.json`(带 quote — **用莫泊桑真实原句,不用杜撰的餐厅段子**):

```json
{
  "id": "paris-tour-eiffel-r",
  "rarity": "R",
  "storyline_id": "emily-in-paris",
  "poi_id": "tour-eiffel",
  "title_zh": "埃菲尔铁塔",
  "title_en": "Eiffel Tower",
  "body_zh": "为 1889 年巴黎世博会而建,设计师古斯塔夫·埃菲尔。落成时曾遭巴黎文艺界联名反对——1887 年的抗议书有 47 位艺术家签名,莫泊桑是其中之一。如今它是法国最标志性的建筑。夜间整点有 5 分钟闪灯秀。",
  "body_en": "Built for the 1889 World's Fair by Gustave Eiffel, it drew a petition of protest from the Paris art world — the 1887 letter carried 47 signatures, Maupassant's among them. Today it is France's most iconic structure. On the hour after dark it sparkles for five minutes.",
  "quote": {
    "text_zh": "我离开了巴黎,甚至离开了法国,只因为埃菲尔铁塔终究让我厌烦透顶。",
    "text_original": "J'ai quitté Paris et même la France, parce que la tour Eiffel finissait par m'ennuyer trop.",
    "source": "莫泊桑《漂泊的一生》首篇《Lassitude》开篇第一句,Ollendorff,1890",
    "source_url": "https://fr.wikisource.org/wiki/La_Vie_errante_(Ollendorff,_1890)/Lassitude",
    "verified": true
  }
}
```

- [ ] **Step 4: 写 3 张 SR 卡**

SR 卡对应彩蛋格,不绑 POI(`poi_id` 留空),内容为跨 POI 的隐藏主题。

`content/cards/paris-sr-petition.json`:

```json
{
  "id": "paris-sr-petition",
  "rarity": "SR",
  "storyline_id": "emily-in-paris",
  "title_zh": "反对铁塔的 47 人",
  "title_en": "The 47 Who Opposed the Tower",
  "body_zh": "1887 年,47 位艺术家与作家联名在《时报》发表抗议书,反对建造埃菲尔铁塔,称它是'骇人的铁柱'。签名者包括莫泊桑、小仲马、加尼叶——对,就是加尼叶歌剧院那位建筑师。今天这些反对者的名字,大多要靠铁塔才被记起。",
  "body_en": "In 1887, forty-seven artists and writers signed a protest in Le Temps against the Eiffel Tower, calling it a 'hateful column of bolted sheet metal.' Signatories included Maupassant, Dumas fils, and Garnier — yes, the architect of the Palais Garnier. Today most of those names are remembered because of the tower."
}
```

`content/cards/paris-sr-existentialism.json`:

```json
{
  "id": "paris-sr-existentialism",
  "rarity": "SR",
  "storyline_id": "emily-in-paris",
  "title_zh": "左岸的哲学工位",
  "title_en": "The Left Bank Office",
  "body_zh": "二战期间燃料短缺,巴黎的公寓冷得没法待。萨特和波伏娃干脆把咖啡馆当办公室——那里有暖气。存在主义很大一部分就是在这种'为了取暖'的现实里写出来的。",
  "body_en": "Fuel was scarce during the war and Paris flats were too cold to work in. Sartre and Beauvoir simply treated the cafés as their office — the cafés had heating. A good deal of existentialism was written in pursuit of warmth."
}
```

`content/cards/paris-sr-tourist-gaze.json`:

```json
{
  "id": "paris-sr-tourist-gaze",
  "rarity": "SR",
  "storyline_id": "emily-in-paris",
  "title_zh": "法国人怎么看这部剧",
  "title_en": "What the French Made of the Show",
  "body_zh": "《艾米莉在巴黎》在法国引发了不小的争议:本地观众吐槽它把巴黎拍成了'明信片滤镜',剧中巴黎人个个傲慢、下午三点才上班。有意思的是,这没妨碍取景地变成真正的打卡点——批评归批评,游客照来。",
  "body_en": "Emily in Paris stirred real irritation in France: local viewers said it shot the city as a postcard filter, with Parisians written as arrogant and strolling in at three in the afternoon. The criticism did nothing to stop the locations becoming genuine pilgrimage sites."
}
```

- [ ] **Step 5: 写 5 条街头卡**

逐条照抄 `content/VERIFIED_CONTENT.md` 的「街头卡 5 条」,文件名与 id 一致:
`paris-cafe-pricing.json`、`paris-metro-doors.json`、`paris-bonjour.json`、
`paris-haussmann.json`、`paris-wallace-fountain.json`。

每个文件形如:

```json
{
  "id": "paris-bonjour",
  "category": "etiquette",
  "text_zh": "<照抄 VERIFIED_CONTENT.md 对应 text_zh>",
  "text_en": "<照抄对应 text_en>",
  "near_poi_id": "place-estrapade",
  "sources": ["<照抄 sources 两条>"],
  "verified": true
}
```

**不得改写文案** —— 其中的「部分」「通常」「多数」等限定词是对抗审查的产物,删掉就会把话说绝。

- [ ] **Step 6: 写 3 条机会题**

`content/chance/paris-eiffel-petition.json`:

```json
{
  "id": "paris-eiffel-petition",
  "question_zh": "1887 年反对建造埃菲尔铁塔的联名抗议书,有多少位艺术家签名?",
  "question_en": "How many artists signed the 1887 protest against the Eiffel Tower?",
  "options_zh": ["7 位", "47 位", "300 位"],
  "options_en": ["7", "47", "300"],
  "answer_index": 1,
  "explain_zh": "47 位。签名者包括莫泊桑、小仲马,还有加尼叶歌剧院的建筑师夏尔·加尼叶。",
  "explain_en": "Forty-seven — among them Maupassant, Dumas fils, and Charles Garnier, architect of the opera house."
}
```

`content/chance/paris-pantheon-pendulum.json`:

```json
{
  "id": "paris-pantheon-pendulum",
  "question_zh": "傅科在先贤祠用一个巨大的摆证明了什么?",
  "question_en": "What did Foucault prove with a giant pendulum in the Panthéon?",
  "options_zh": ["地球在自转", "月球引力存在", "空气有重量"],
  "options_en": ["The Earth rotates", "Lunar gravity exists", "Air has weight"],
  "answer_index": 0,
  "explain_zh": "1851 年,傅科在此用摆的偏转首次直观证明了地球自转。",
  "explain_en": "In 1851 Foucault used the pendulum's drift to demonstrate the Earth's rotation for the first time."
}
```

`content/chance/paris-garnier-phantom.json`:

```json
{
  "id": "paris-garnier-phantom",
  "question_zh": "《歌剧魅影》里那个地下湖,在加尼叶歌剧院真的存在吗?",
  "question_en": "Does the underground lake from The Phantom of the Opera really exist?",
  "options_zh": ["纯属虚构", "确有一个地下蓄水池", "是排练厅的误传"],
  "options_en": ["Pure fiction", "There is a real water tank below", "A rehearsal-hall mix-up"],
  "answer_index": 1,
  "explain_zh": "歌剧院地下确有一个蓄水池,建造时为处理地下水而设,至今仍在,消防队会在此训练。",
  "explain_en": "There is a real cistern beneath the opera house, built to manage groundwater. It is still there, and the fire brigade trains in it."
}
```

- [ ] **Step 7: 写棋盘定义**

`content/boards/emily-in-paris.json` 记录填充计划与格子内容映射,坐标由 `board_gen.build_board` 在构建时算出:

```json
{
  "storyline_id": "emily-in-paris",
  "total_filler": 13,
  "night_from_index": 13,
  "filler_plan": ["street", "chance", "photo", "street", "easter", "street",
                  "chance", "photo", "street", "easter", "chance", "street",
                  "easter"],
  "content_map": {
    "street": ["paris-bonjour", "paris-metro-doors", "paris-cafe-pricing",
               "paris-haussmann", "paris-wallace-fountain"],
    "chance": ["paris-eiffel-petition", "paris-pantheon-pendulum",
               "paris-garnier-phantom"],
    "easter": ["paris-sr-petition", "paris-sr-existentialism",
               "paris-sr-tourist-gaze"]
  }
}
```

- [ ] **Step 8: 运行确认通过**

Run: `python -m pytest tests/test_content_files.py -v`
Expected: PASS(7 个用例)

- [ ] **Step 9: 提交**

```bash
git add content/cards content/street content/chance content/boards tests/test_content_files.py
git commit -m "feat(content): add 10 cards, 5 verified street cards, 3 quiz questions, board定义"
```

---

## Task 6: 构建产出扩展

**Files:**
- Modify: `pipeline/build_site.py`
- Modify: `pipeline/run_paris.py`
- Test: `tests/test_build_site.py`

**Interfaces:**
- Consumes: Task 2 `filter_street_cards`/`quote_passes`;Task 3 `build_board`;Task 4 三个 loader
- Produces: payload 新增 `board`(格子数组)、`cards`(id → 卡面)、`street_cards`、`chance`、`night_from_index` 五个键,供前端 Task 8-14 消费

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_build_site.py`:

```python
from pipeline.build_site import build_game_payload
from pipeline.models import BoardTile, Card, Quote, StreetCard


def _card(cid, rarity="R", quote=None):
    return Card(id=cid, rarity=rarity, storyline_id="sl", poi_id="p",
                title_zh="标题", title_en="Title",
                body_zh="正文", body_en="Body", quote=quote)


def test_game_payload_includes_board_and_cards():
    tiles = [BoardTile(index=0, type="poi", lat=1.0, lng=2.0, poi_id="p")]
    out = build_game_payload(tiles, [_card("c1")], [], [], night_from_index=13)
    assert out["board"][0]["type"] == "poi"
    assert out["cards"]["c1"]["rarity"] == "R"
    assert out["night_from_index"] == 13


def test_unverified_quote_is_stripped_from_card():
    bad = Quote(text_zh="x", text_original="x", source="",
                source_url="", verified=False)
    out = build_game_payload([], [_card("c1", quote=bad)], [], [], 13)
    assert "quote" not in out["cards"]["c1"]


def test_verified_quote_is_kept():
    good = Quote(text_zh="译文", text_original="orig", source="书, 1890",
                 source_url="https://a.example", verified=True)
    out = build_game_payload([], [_card("c1", quote=good)], [], [], 13)
    assert out["cards"]["c1"]["quote"]["text_original"] == "orig"


def test_unverified_street_card_is_dropped():
    ok = StreetCard(id="s1", category="rule", text_zh="a", text_en="a",
                    near_poi_id="p",
                    sources=["https://a.example", "https://b.example"],
                    verified=True)
    bad = StreetCard(id="s2", category="rule", text_zh="b", text_en="b",
                     near_poi_id="p", sources=["https://a.example"],
                     verified=True)
    out = build_game_payload([], [], [ok, bad], [], 13)
    assert list(out["street_cards"].keys()) == ["s1"]


def test_street_card_sources_not_leaked_to_frontend():
    ok = StreetCard(id="s1", category="rule", text_zh="a", text_en="a",
                    near_poi_id="p",
                    sources=["https://a.example", "https://b.example"],
                    verified=True)
    out = build_game_payload([], [], [ok], [], 13)
    assert "sources" not in out["street_cards"]["s1"]
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_build_site.py -v -k game_payload`
Expected: FAIL — `ImportError: cannot import name 'build_game_payload'`

- [ ] **Step 3: 实现**

在 `pipeline/build_site.py` 追加:

```python
from pipeline.models import BoardTile, Card, StreetCard
from pipeline.verify import filter_street_cards, quote_passes


def _tile_dict(t: BoardTile) -> dict:
    d = {"index": t.index, "type": t.type, "lat": t.lat, "lng": t.lng}
    if t.poi_id:
        d["poi_id"] = t.poi_id
    if t.content_id:
        d["content_id"] = t.content_id
    return d


def _card_dict(c: Card) -> dict:
    d = {"id": c.id, "rarity": c.rarity, "storyline_id": c.storyline_id,
         "poi_id": c.poi_id, "title_zh": c.title_zh, "title_en": c.title_en,
         "body_zh": c.body_zh, "body_en": c.body_en}
    if c.image:
        d["image"] = _image_dict(c.image)
    if quote_passes(c.quote):
        d["quote"] = {"text_zh": c.quote.text_zh,
                      "text_original": c.quote.text_original,
                      "source": c.quote.source,
                      "source_url": c.quote.source_url}
    return d


def _street_dict(s: StreetCard) -> dict:
    # sources 只用于构建时校验,不输出到前端
    return {"id": s.id, "category": s.category,
            "text_zh": s.text_zh, "text_en": s.text_en,
            "near_poi_id": s.near_poi_id}


def build_game_payload(tiles, cards, street_cards, chance,
                       night_from_index: int) -> dict:
    """Build the game-mode payload: board, cards, street cards, quiz."""
    return {
        "board": [_tile_dict(t) for t in tiles],
        "cards": {c.id: _card_dict(c) for c in cards},
        "street_cards": {s.id: _street_dict(s)
                         for s in filter_street_cards(street_cards)},
        "chance": {q["id"]: q for q in chance},
        "night_from_index": night_from_index,
    }
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_build_site.py -v`
Expected: PASS

- [ ] **Step 5: 接入 run_paris**

修改 `pipeline/run_paris.py` 的 `main`,在 `build_city_payload` 之后合并游戏 payload:

```python
    board_cfg = json.loads(open(
        os.path.join(ROOT, "content", "boards", "emily-in-paris.json"),
        encoding="utf-8").read())
    sl = next(s for s in storylines if s.id == board_cfg["storyline_id"])
    tiles = build_board(sl, pois, board_cfg["filler_plan"],
                        board_cfg["total_filler"])
    _attach_content(tiles, board_cfg["content_map"])

    cards = [load_card(p) for p in
             sorted(glob.glob(os.path.join(ROOT, "content", "cards", "*.json")))]
    street = [load_street_card(p) for p in
              sorted(glob.glob(os.path.join(ROOT, "content", "street", "*.json")))]
    chance = [load_chance(p) for p in
              sorted(glob.glob(os.path.join(ROOT, "content", "chance", "*.json")))]

    payload = build_city_payload(city, pois, storylines)
    payload.update(build_game_payload(tiles, cards, street, chance,
                                      board_cfg["night_from_index"]))
```

并在模块内加 `_attach_content`,按类型轮转把 content_map 里的 id 挂到格子上:

```python
def _attach_content(tiles, content_map):
    """Assign content ids to filler tiles, cycling within each type."""
    cursor = {k: 0 for k in content_map}
    for t in tiles:
        pool = content_map.get(t.type)
        if not pool:
            continue
        t.content_id = pool[cursor[t.type] % len(pool)]
        cursor[t.type] += 1
```

- [ ] **Step 6: 跑端到端构建**

Run: `LEMI_OFFLINE=1 python -m pipeline.run_paris && python -c "import json;d=json.load(open('dist/data/paris.json'));print('board',len(d['board']),'cards',len(d['cards']),'street',len(d['street_cards']),'night',d['night_from_index'])"`
Expected: `board 20 cards 10 street 5 night 13`

- [ ] **Step 7: 提交**

```bash
git add pipeline/build_site.py pipeline/run_paris.py tests/test_build_site.py
git commit -m "feat(build): emit board, cards, street cards and quiz into payload"
```

---

## 前端测试约定(Task 7 起适用)

v1 的 `tests/test_frontend.py` 只做静态文本断言(检查文件里有没有某个字符串),无法验证逻辑正确性。Review Focus 的五条全是逻辑问题,因此纯逻辑模块改用 **Node 内置测试运行器**真跑:

- 运行器:`node --test`(Node v24 内置,零依赖,已验证可用)
- **并发限制:所有 node --test 命令必须带 `--test-concurrency=2`**,否则会按 CPU 核数起 worker 撞 cgroup 配额
- 测试文件放 `tests/js/*.test.js`
- 被测模块用 UMD 式双导出,浏览器挂 `window`、Node 走 `module.exports`:

```javascript
if (typeof module !== "undefined" && module.exports) {
  module.exports = { fn };
} else if (typeof window !== "undefined") {
  window.LemiXxx = { fn };
}
```

- 涉及 DOM/MapLibre/动效的部分不写单测(无 jsdom 依赖),靠 Task 16 的手动验收清单覆盖

---

## Task 7: 状态持久化

**Files:**
- Create: `web/assets/core/storage.js`
- Test: `tests/js/storage.test.js`

**Interfaces:**
- Consumes: 无
- Produces: `createStorage(backend)` 返回对象,含 `load()`、`save(state)`、`addCard(id)`、`hasCard(id)`、`cardCount()`、`setTile(slId, n)`、`migrate(raw)`。Task 11(卡册)、Task 13(主循环)消费此接口。

**Review Focus 覆盖:** 本任务的测试覆盖 #1 localStorage 不可用、#2 版本迁移、#4 重复收卡不重复计数。

- [ ] **Step 1: 写失败测试**

Create `tests/js/storage.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { createStorage, CURRENT_VERSION } = require("../../web/assets/core/storage.js");

function memoryBackend(initial) {
  let store = initial === undefined ? {} : initial;
  return {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    _dump: () => store,
  };
}

function brokenBackend() {
  return {
    getItem: () => { throw new Error("SecurityError"); },
    setItem: () => { throw new Error("QuotaExceededError"); },
  };
}

test("fresh state has empty cards and current version", () => {
  const s = createStorage(memoryBackend());
  const st = s.load();
  assert.strictEqual(st.v, CURRENT_VERSION);
  assert.deepStrictEqual(st.cards, []);
});

test("addCard persists across reload", () => {
  const backend = memoryBackend();
  const a = createStorage(backend);
  a.addCard("paris-tour-eiffel-r");
  const b = createStorage(backend);
  assert.ok(b.hasCard("paris-tour-eiffel-r"));
  assert.strictEqual(b.cardCount(), 1);
});

test("addCard is idempotent - replaying a card does not double count", () => {
  const s = createStorage(memoryBackend());
  s.addCard("c1");
  s.addCard("c1");
  s.addCard("c1");
  assert.strictEqual(s.cardCount(), 1);
});

test("addCard reports whether the card was new", () => {
  const s = createStorage(memoryBackend());
  assert.strictEqual(s.addCard("c1"), true);
  assert.strictEqual(s.addCard("c1"), false);
});

test("game still works when localStorage throws", () => {
  const s = createStorage(brokenBackend());
  assert.doesNotThrow(() => s.addCard("c1"));
  assert.strictEqual(s.hasCard("c1"), true);   // 内存里仍然生效
  assert.strictEqual(s.cardCount(), 1);
});

test("corrupt JSON falls back to a fresh state instead of crashing", () => {
  const s = createStorage(memoryBackend({ lemi_state: "{not json" }));
  assert.deepStrictEqual(s.load().cards, []);
});

test("migrate keeps collected cards when version is older", () => {
  const old = JSON.stringify({ v: 0, cards: ["c1", "c2"] });
  const s = createStorage(memoryBackend({ lemi_state: old }));
  const st = s.load();
  assert.strictEqual(st.v, CURRENT_VERSION);
  assert.deepStrictEqual(st.cards, ["c1", "c2"]);  // 绝不能清空
});

test("migrate fills in missing fields from an older shape", () => {
  const old = JSON.stringify({ v: 0, cards: ["c1"] });
  const s = createStorage(memoryBackend({ lemi_state: old }));
  const st = s.load();
  assert.deepStrictEqual(st.storylines, {});
  assert.deepStrictEqual(st.ssr_shards, {});
});

test("setTile records progress per storyline", () => {
  const s = createStorage(memoryBackend());
  s.setTile("emily-in-paris", 7);
  assert.strictEqual(s.load().storylines["emily-in-paris"].tile, 7);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/storage.test.js`
Expected: FAIL — `Cannot find module '../../web/assets/core/storage.js'`

- [ ] **Step 3: 实现**

Create `web/assets/core/storage.js`:

```javascript
// Player state persistence. Game mode only — codex mode never touches this.
// Every write is best-effort: if localStorage is unavailable (private mode,
// quota exceeded) the game keeps running against the in-memory copy.

var STORAGE_KEY = "lemi_state";
var CURRENT_VERSION = 1;

function freshState() {
  return { v: CURRENT_VERSION, cards: [], storylines: {}, ssr_shards: {} };
}

function migrate(raw) {
  // Older shapes must never lose collected cards.
  if (!raw || typeof raw !== "object") return freshState();
  return {
    v: CURRENT_VERSION,
    cards: Array.isArray(raw.cards) ? raw.cards.slice() : [],
    storylines: raw.storylines && typeof raw.storylines === "object"
      ? raw.storylines : {},
    ssr_shards: raw.ssr_shards && typeof raw.ssr_shards === "object"
      ? raw.ssr_shards : {},
  };
}

function createStorage(backend) {
  var state = freshState();
  try {
    var text = backend.getItem(STORAGE_KEY);
    if (text) state = migrate(JSON.parse(text));
  } catch (e) {
    state = freshState();   // unreadable or corrupt: start clean, do not crash
  }

  function persist() {
    try {
      backend.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      // Quota or security error: in-memory state stays authoritative.
    }
  }

  return {
    load: function () { return state; },
    save: function (next) { state = next; persist(); },
    addCard: function (id) {
      if (state.cards.indexOf(id) !== -1) return false;
      state.cards.push(id);
      persist();
      return true;
    },
    hasCard: function (id) { return state.cards.indexOf(id) !== -1; },
    cardCount: function () { return state.cards.length; },
    setTile: function (slId, n) {
      if (!state.storylines[slId]) state.storylines[slId] = { tile: 0, done: false };
      state.storylines[slId].tile = n;
      persist();
    },
    migrate: migrate,
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createStorage: createStorage, migrate: migrate,
                     CURRENT_VERSION: CURRENT_VERSION };
} else if (typeof window !== "undefined") {
  window.LemiStorage = { createStorage: createStorage,
                         CURRENT_VERSION: CURRENT_VERSION };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/storage.test.js`
Expected: PASS(9 个用例)

- [ ] **Step 5: 提交**

```bash
git add web/assets/core/storage.js tests/js/storage.test.js
git commit -m "feat(storage): player state with migration and unavailable-backend fallback"
```

---

## Task 8: 骰子与移动规则

**Files:**
- Create: `web/assets/game/dice.js`
- Test: `tests/js/dice.test.js`

**Interfaces:**
- Consumes: 无
- Produces: `rollDice(rng)` 返回 1-6;`resolveMove(from, roll, boardLength)` 返回 `{to, path, finished}`。Task 13 主循环消费。

**Review Focus 覆盖:** 本任务的测试覆盖 #3 骰子点数超过剩余格数不得越界。

**规则(spec 3.1):** 骰子控制走多远,不控制跳过谁。`path` 必须包含**途经的每一格**,主循环据此逐格触发,不得跳过 POI。

- [ ] **Step 1: 写失败测试**

Create `tests/js/dice.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { rollDice, resolveMove } = require("../../web/assets/game/dice.js");

test("rollDice stays within 1..6", () => {
  for (let i = 0; i < 200; i++) {
    const n = rollDice();
    assert.ok(n >= 1 && n <= 6, "got " + n);
    assert.strictEqual(n, Math.floor(n));
  }
});

test("rollDice uses the injected rng", () => {
  assert.strictEqual(rollDice(() => 0), 1);
  assert.strictEqual(rollDice(() => 0.999), 6);
});

test("path lists every tile passed, never skipping one", () => {
  const { to, path } = resolveMove(0, 3, 20);
  assert.strictEqual(to, 3);
  assert.deepStrictEqual(path, [1, 2, 3]);
});

test("move stops at the last tile when the roll overshoots", () => {
  const { to, path, finished } = resolveMove(18, 6, 20);
  assert.strictEqual(to, 19);              // 不得越界到 24
  assert.deepStrictEqual(path, [19]);
  assert.strictEqual(finished, true);
});

test("landing exactly on the last tile finishes the run", () => {
  const { to, finished } = resolveMove(17, 2, 20);
  assert.strictEqual(to, 19);
  assert.strictEqual(finished, true);
});

test("a move that does not reach the end is not finished", () => {
  assert.strictEqual(resolveMove(0, 5, 20).finished, false);
});

test("rolling from the final tile yields an empty path", () => {
  const { to, path, finished } = resolveMove(19, 4, 20);
  assert.strictEqual(to, 19);
  assert.deepStrictEqual(path, []);
  assert.strictEqual(finished, true);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/dice.test.js`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现**

Create `web/assets/game/dice.js`:

```javascript
// Dice and movement rules.
//
// The die decides HOW FAR Lemi walks, never WHICH tiles she skips: the
// returned path lists every tile passed so the caller can trigger each one.
// A roll past the final tile stops at the end rather than overshooting.

function rollDice(rng) {
  var r = (rng || Math.random)();
  return Math.floor(r * 6) + 1;
}

function resolveMove(from, roll, boardLength) {
  var last = boardLength - 1;
  var to = Math.min(from + roll, last);
  var path = [];
  for (var i = from + 1; i <= to; i++) path.push(i);
  return { to: to, path: path, finished: to >= last };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { rollDice: rollDice, resolveMove: resolveMove };
} else if (typeof window !== "undefined") {
  window.LemiDice = { rollDice: rollDice, resolveMove: resolveMove };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/dice.test.js`
Expected: PASS(7 个用例)

- [ ] **Step 5: 提交**

```bash
git add web/assets/game/dice.js tests/js/dice.test.js
git commit -m "feat(dice): roll and movement that never skips a tile or overshoots"
```

---

## Task 9: 卡片数据整形

**Files:**
- Create: `web/assets/game/card.js`
- Test: `tests/js/card.test.js`

**Interfaces:**
- Consumes: Task 6 产出的 payload `cards` 字典
- Produces: `shapeCard(raw, lang)` 返回 `{id, rarity, title, body, quote, image, hasImage}`;`rarityClass(rarity)` 返回 CSS 类名。Task 13 主循环、Task 11 卡册消费。

**Review Focus 覆盖:** 本任务的测试覆盖 #5 图片加载失败时卡片仍可读。

- [ ] **Step 1: 写失败测试**

Create `tests/js/card.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { shapeCard, rarityClass } = require("../../web/assets/game/card.js");

const RAW = {
  id: "paris-tour-eiffel-r", rarity: "R", poi_id: "tour-eiffel",
  title_zh: "埃菲尔铁塔", title_en: "Eiffel Tower",
  body_zh: "中文正文", body_en: "English body",
  image: { url: "https://x/a.jpg", thumb: "https://x/t.jpg" },
  quote: { text_zh: "译文", text_original: "orig",
           source: "书, 1890", source_url: "https://a.example" },
};

test("shapeCard picks the requested language", () => {
  assert.strictEqual(shapeCard(RAW, "zh").title, "埃菲尔铁塔");
  assert.strictEqual(shapeCard(RAW, "en").title, "Eiffel Tower");
});

test("shapeCard falls back when a translation is missing", () => {
  const partial = Object.assign({}, RAW, { title_en: "" });
  assert.strictEqual(shapeCard(partial, "en").title, "埃菲尔铁塔");
});

test("card without an image is still readable", () => {
  const noImg = Object.assign({}, RAW, { image: null });
  const c = shapeCard(noImg, "zh");
  assert.strictEqual(c.hasImage, false);
  assert.strictEqual(c.body, "中文正文");   // 正文仍在,不是空白卡
  assert.strictEqual(c.title, "埃菲尔铁塔");
});

test("card with a blank image url counts as having no image", () => {
  const blank = Object.assign({}, RAW, { image: { url: "", thumb: "" } });
  assert.strictEqual(shapeCard(blank, "zh").hasImage, false);
});

test("quote is shaped with its source for attribution", () => {
  const q = shapeCard(RAW, "zh").quote;
  assert.strictEqual(q.text, "译文");
  assert.strictEqual(q.original, "orig");
  assert.strictEqual(q.source, "书, 1890");
});

test("card without a quote yields null, not an empty object", () => {
  const noQuote = Object.assign({}, RAW, { quote: undefined });
  assert.strictEqual(shapeCard(noQuote, "zh").quote, null);
});

test("rarityClass maps each rarity to its own class", () => {
  assert.strictEqual(rarityClass("R"), "card-r");
  assert.strictEqual(rarityClass("SR"), "card-sr");
  assert.strictEqual(rarityClass("SSR"), "card-ssr");
});

test("unknown rarity degrades to the common class", () => {
  assert.strictEqual(rarityClass("bogus"), "card-r");
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/card.test.js`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现**

Create `web/assets/game/card.js`:

```javascript
// Card shaping. A card must stay readable when its image is missing or
// fails to load, so hasImage is reported separately from the text.

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function shapeCard(raw, lang) {
  var img = raw.image || null;
  var hasImage = !!(img && img.url);
  var quote = null;
  if (raw.quote) {
    quote = {
      text: raw.quote.text_zh || "",
      original: raw.quote.text_original || "",
      source: raw.quote.source || "",
      sourceUrl: raw.quote.source_url || "",
    };
  }
  return {
    id: raw.id,
    rarity: raw.rarity,
    poiId: raw.poi_id || "",
    title: pick(raw.title_zh, raw.title_en, lang),
    body: pick(raw.body_zh, raw.body_en, lang),
    image: img,
    hasImage: hasImage,
    quote: quote,
  };
}

function rarityClass(rarity) {
  if (rarity === "SSR") return "card-ssr";
  if (rarity === "SR") return "card-sr";
  return "card-r";
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { shapeCard: shapeCard, rarityClass: rarityClass };
} else if (typeof window !== "undefined") {
  window.LemiCard = { shapeCard: shapeCard, rarityClass: rarityClass };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/card.test.js`
Expected: PASS(8 个用例)

- [ ] **Step 5: 提交**

```bash
git add web/assets/game/card.js tests/js/card.test.js
git commit -m "feat(card): shape card data with language fallback and image-absent handling"
```

---

## Task 10: 格子触发规则

**Files:**
- Create: `web/assets/game/tiles.js`
- Test: `tests/js/tiles.test.js`

**Interfaces:**
- Consumes: Task 6 payload 的 `board`/`cards`/`street_cards`/`chance`;Task 7 storage 的 `hasCard`
- Produces: `resolveTile(tile, payload, lang)` 返回 `{kind, durationMs, content}`;`isNight(index, nightFrom)` 返回布尔。Task 13 主循环消费。

**时长(spec 5.2/5.5,精确值):** POI 格与彩蛋格掉卡 600ms;机会/机位/街头格统一 3000ms。

- [ ] **Step 1: 写失败测试**

Create `tests/js/tiles.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { resolveTile, isNight, DURATIONS } = require("../../web/assets/game/tiles.js");

const PAYLOAD = {
  pois: { "tour-eiffel": { id: "tour-eiffel", name_zh: "埃菲尔铁塔",
                           name_en: "Eiffel Tower" } },
  cards: { "paris-tour-eiffel-r": { id: "paris-tour-eiffel-r", rarity: "R",
                                    poi_id: "tour-eiffel", title_zh: "铁塔",
                                    title_en: "Tower", body_zh: "正文",
                                    body_en: "body" },
           "paris-sr-petition": { id: "paris-sr-petition", rarity: "SR",
                                  title_zh: "47 人", title_en: "The 47",
                                  body_zh: "正文", body_en: "body" } },
  street_cards: { "paris-bonjour": { id: "paris-bonjour", category: "etiquette",
                                     text_zh: "先说 Bonjour",
                                     text_en: "Say Bonjour" } },
  chance: { "paris-eiffel-petition": { id: "paris-eiffel-petition",
                                       question_zh: "多少人签名?",
                                       question_en: "How many signed?",
                                       options_zh: ["7", "47", "300"],
                                       options_en: ["7", "47", "300"],
                                       answer_index: 1,
                                       explain_zh: "47 位。",
                                       explain_en: "Forty-seven." } },
};

test("poi tile drops the matching R card", () => {
  const t = { index: 0, type: "poi", poi_id: "tour-eiffel" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "card");
  assert.strictEqual(r.content.id, "paris-tour-eiffel-r");
  assert.strictEqual(r.durationMs, DURATIONS.card);
});

test("easter tile drops an SR card", () => {
  const t = { index: 4, type: "easter", content_id: "paris-sr-petition" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "card");
  assert.strictEqual(r.content.rarity, "SR");
});

test("street tile returns text at the shared 3s duration", () => {
  const t = { index: 1, type: "street", content_id: "paris-bonjour" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "street");
  assert.strictEqual(r.content.text, "先说 Bonjour");
  assert.strictEqual(r.durationMs, 3000);
});

test("chance tile carries options and the answer index", () => {
  const t = { index: 2, type: "chance", content_id: "paris-eiffel-petition" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "chance");
  assert.strictEqual(r.content.answerIndex, 1);
  assert.deepStrictEqual(r.content.options, ["7", "47", "300"]);
  assert.strictEqual(r.durationMs, 3000);
});

test("chance tile shapes English options when asked", () => {
  const t = { index: 2, type: "chance", content_id: "paris-eiffel-petition" };
  assert.strictEqual(resolveTile(t, PAYLOAD, "en").content.question,
                     "How many signed?");
});

test("a tile whose content is missing degrades to a skip, not a crash", () => {
  const t = { index: 3, type: "street", content_id: "does-not-exist" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "skip");
  assert.strictEqual(r.durationMs, 0);
});

test("poi tile with no matching card degrades to a skip", () => {
  const t = { index: 0, type: "poi", poi_id: "unknown-poi" };
  assert.strictEqual(resolveTile(t, PAYLOAD, "zh").kind, "skip");
});

test("isNight flips at the configured index and stays night after", () => {
  assert.strictEqual(isNight(12, 13), false);
  assert.strictEqual(isNight(13, 13), true);
  assert.strictEqual(isNight(19, 13), true);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/tiles.test.js`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现**

Create `web/assets/game/tiles.js`:

```javascript
// Tile resolution: given a board tile, work out what to show and for how
// long. Missing content degrades to a skip so a content gap never stalls
// the game loop.

var DURATIONS = { card: 600, info: 3000 };

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function _card(raw, lang) {
  var shape = (typeof require !== "undefined")
    ? require("./card.js").shapeCard
    : window.LemiCard.shapeCard;
  return { kind: "card", durationMs: DURATIONS.card, content: shape(raw, lang) };
}

function _skip() {
  return { kind: "skip", durationMs: 0, content: null };
}

function resolveTile(tile, payload, lang) {
  if (tile.type === "poi") {
    var cards = payload.cards || {};
    for (var id in cards) {
      if (cards[id].poi_id === tile.poi_id) return _card(cards[id], lang);
    }
    return _skip();
  }
  if (tile.type === "easter") {
    var c = (payload.cards || {})[tile.content_id];
    return c ? _card(c, lang) : _skip();
  }
  if (tile.type === "street") {
    var s = (payload.street_cards || {})[tile.content_id];
    if (!s) return _skip();
    return { kind: "street", durationMs: DURATIONS.info,
             content: { id: s.id, category: s.category,
                        text: pick(s.text_zh, s.text_en, lang) } };
  }
  if (tile.type === "chance") {
    var q = (payload.chance || {})[tile.content_id];
    if (!q) return _skip();
    return { kind: "chance", durationMs: DURATIONS.info,
             content: { id: q.id,
                        question: pick(q.question_zh, q.question_en, lang),
                        options: lang === "en" ? q.options_en : q.options_zh,
                        answerIndex: q.answer_index,
                        explain: pick(q.explain_zh, q.explain_en, lang) } };
  }
  if (tile.type === "photo") {
    var poi = (payload.pois || {})[tile.poi_id] || null;
    if (!poi) return _skip();
    return { kind: "photo", durationMs: DURATIONS.info,
             content: { poiId: poi.id,
                        name: pick(poi.name_zh, poi.name_en, lang),
                        image: (poi.base_images || [])[0] || null } };
  }
  return _skip();
}

function isNight(index, nightFrom) {
  return index >= nightFrom;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { resolveTile: resolveTile, isNight: isNight,
                     DURATIONS: DURATIONS };
} else if (typeof window !== "undefined") {
  window.LemiTiles = { resolveTile: resolveTile, isNight: isNight,
                       DURATIONS: DURATIONS };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/tiles.test.js`
Expected: PASS(8 个用例)

- [ ] **Step 5: 提交**

```bash
git add web/assets/game/tiles.js tests/js/tiles.test.js
git commit -m "feat(tiles): resolve tile content per type with skip-on-missing degradation"
```

---

## Task 11: 卡册

**Files:**
- Create: `web/assets/game/collection.js`
- Test: `tests/js/collection.test.js`

**Interfaces:**
- Consumes: Task 7 storage;Task 6 payload `cards`
- Produces: `buildCollection(payload, storage, lang)` 返回 `{slots, owned, total, ssr}`。Task 13 渲染卡册页面时消费。

**规则(spec 第 4、8 节):** 分母为 10(7 R + 3 SR),SSR 不计入。未获得的卡必须以剪影占位出现在 slots 中,不能从列表里消失。

- [ ] **Step 1: 写失败测试**

Create `tests/js/collection.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { buildCollection } = require("../../web/assets/game/collection.js");
const { createStorage } = require("../../web/assets/core/storage.js");

function mem() {
  let s = {};
  return { getItem: (k) => (k in s ? s[k] : null),
           setItem: (k, v) => { s[k] = String(v); } };
}

function payloadWith(n) {
  const cards = {};
  for (let i = 0; i < n; i++) {
    cards["c" + i] = { id: "c" + i, rarity: i < 7 ? "R" : "SR",
                       title_zh: "卡" + i, title_en: "Card " + i,
                       body_zh: "正文", body_en: "body" };
  }
  return { cards: cards, ssr_shards_required: 3 };
}

test("every card has a slot even when nothing is collected", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.strictEqual(c.slots.length, 10);
  assert.strictEqual(c.owned, 0);
  assert.strictEqual(c.total, 10);
});

test("uncollected slots are silhouettes carrying no title", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.strictEqual(c.slots[0].owned, false);
  assert.strictEqual(c.slots[0].title, "");     // 剪影不剧透内容
  assert.strictEqual(c.slots[0].rarity, "R");   // 但稀有度可见
});

test("collected slots reveal their title", () => {
  const st = createStorage(mem());
  st.addCard("c0");
  const c = buildCollection(payloadWith(10), st, "zh");
  assert.strictEqual(c.slots[0].owned, true);
  assert.strictEqual(c.slots[0].title, "卡0");
  assert.strictEqual(c.owned, 1);
});

test("slots are ordered R first then SR", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.deepStrictEqual(c.slots.slice(0, 7).map((s) => s.rarity),
                         ["R", "R", "R", "R", "R", "R", "R"]);
  assert.deepStrictEqual(c.slots.slice(7).map((s) => s.rarity),
                         ["SR", "SR", "SR"]);
});

test("ssr is locked and excluded from the denominator", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.strictEqual(c.total, 10);          // 不是 11
  assert.strictEqual(c.ssr.locked, true);
  assert.strictEqual(c.ssr.shards, 0);
  assert.strictEqual(c.ssr.required, 3);
});

test("collecting every card does not unlock ssr on its own", () => {
  const st = createStorage(mem());
  for (let i = 0; i < 10; i++) st.addCard("c" + i);
  const c = buildCollection(payloadWith(10), st, "zh");
  assert.strictEqual(c.owned, 10);
  assert.strictEqual(c.ssr.locked, true);   // 需 3 条故事线,非集满本线
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/collection.test.js`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现**

Create `web/assets/game/collection.js`:

```javascript
// The card album. Uncollected cards keep a silhouette slot so the player
// can see what is still missing — that visible gap is what drives
// collection. SSR is a city-level reward and never counts toward the
// per-storyline denominator.

var RARITY_ORDER = { R: 0, SR: 1 };

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function buildCollection(payload, storage, lang) {
  var cards = payload.cards || {};
  var ids = Object.keys(cards).filter(function (id) {
    return cards[id].rarity === "R" || cards[id].rarity === "SR";
  });
  ids.sort(function (a, b) {
    var d = RARITY_ORDER[cards[a].rarity] - RARITY_ORDER[cards[b].rarity];
    return d !== 0 ? d : (a < b ? -1 : 1);
  });

  var owned = 0;
  var slots = ids.map(function (id) {
    var has = storage.hasCard(id);
    if (has) owned += 1;
    return {
      id: id,
      rarity: cards[id].rarity,
      owned: has,
      title: has ? pick(cards[id].title_zh, cards[id].title_en, lang) : "",
    };
  });

  var shards = (storage.load().ssr_shards || {}).paris || 0;
  var required = payload.ssr_shards_required || 3;
  return {
    slots: slots,
    owned: owned,
    total: slots.length,
    ssr: { locked: shards < required, shards: shards, required: required },
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { buildCollection: buildCollection };
} else if (typeof window !== "undefined") {
  window.LemiCollection = { buildCollection: buildCollection };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/collection.test.js`
Expected: PASS(6 个用例)

- [ ] **Step 5: 提交**

```bash
git add web/assets/game/collection.js tests/js/collection.test.js
git commit -m "feat(collection): album with silhouette slots and city-level SSR lock"
```

---

## Task 12: 地图封装

**Files:**
- Create: `web/assets/core/mapkit.js`
- Test: `tests/js/mapkit.test.js`

**Interfaces:**
- Consumes: 无(MapLibre 实例由调用方注入)
- Produces: `toLngLat([lat, lng])`、`needsPan(tileXY, viewport, marginRatio)`、`flyOptions(tile, reduced)`、`createCamera(map, opts)`(含 `moveTo(tile, isPoi)`)。Task 13 主循环、Task 15 图鉴消费。

**镜头策略(spec 5.3):** 步行时镜头不动,仅当棋子进入视野边缘 15% 才 `panTo` 一次;**仅落 POI 格才 `flyTo` 俯冲**(pitch 50°)。`flyTo` 必须带 `essential: true`。

- [ ] **Step 1: 写失败测试**

Create `tests/js/mapkit.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { toLngLat, needsPan, flyOptions } = require("../../web/assets/core/mapkit.js");

test("toLngLat swaps stored lat,lng into MapLibre order", () => {
  assert.deepStrictEqual(toLngLat([48.8584, 2.2945]), [2.2945, 48.8584]);
});

test("a point in the middle of the view needs no pan", () => {
  const vp = { width: 1000, height: 800 };
  assert.strictEqual(needsPan({ x: 500, y: 400 }, vp, 0.15), false);
});

test("a point inside the edge margin needs a pan", () => {
  const vp = { width: 1000, height: 800 };
  assert.strictEqual(needsPan({ x: 100, y: 400 }, vp, 0.15), true);  // 左边缘内
  assert.strictEqual(needsPan({ x: 500, y: 60 }, vp, 0.15), true);   // 上边缘内
});

test("a point outside the viewport needs a pan", () => {
  const vp = { width: 1000, height: 800 };
  assert.strictEqual(needsPan({ x: -20, y: 400 }, vp, 0.15), true);
});

test("poi flight is a pitched cinematic move", () => {
  const o = flyOptions({ lat: 48.86, lng: 2.29 }, false);
  assert.deepStrictEqual(o.center, [2.29, 48.86]);
  assert.strictEqual(o.pitch, 50);
  assert.strictEqual(o.essential, true);   // 缺了它 reduced-motion 会跳过动画
});

test("reduced motion keeps essential but drops the pitch and duration", () => {
  const o = flyOptions({ lat: 48.86, lng: 2.29 }, true);
  assert.strictEqual(o.essential, true);
  assert.strictEqual(o.pitch, 0);
  assert.strictEqual(o.duration, 200);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/mapkit.test.js`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现**

Create `web/assets/core/mapkit.js`:

```javascript
// MapLibre helpers.
//
// Camera policy, borrowed from storymap: during a walk the camera stays
// put and only pans once the pawn reaches the edge of the view. Constant
// camera motion is what makes map playback nauseating. A pitched flyTo is
// reserved for arriving at a POI, where the move is the point.
//
// Coordinates are stored as [lat, lng] project-wide and only swapped here.

var PITCH_ON_ARRIVAL = 50;
var EDGE_MARGIN = 0.15;

function toLngLat(latLng) {
  return [latLng[1], latLng[0]];
}

function needsPan(point, viewport, marginRatio) {
  var m = marginRatio === undefined ? EDGE_MARGIN : marginRatio;
  var mx = viewport.width * m;
  var my = viewport.height * m;
  return point.x < mx || point.x > viewport.width - mx
      || point.y < my || point.y > viewport.height - my;
}

function flyOptions(tile, reduced) {
  // essential:true is required, or the OS "reduce motion" setting turns
  // this into a jumpTo and the arrival moment disappears.
  if (reduced) {
    return { center: [tile.lng, tile.lat], zoom: 15, pitch: 0,
             duration: 200, essential: true };
  }
  return { center: [tile.lng, tile.lat], zoom: 16,
           pitch: PITCH_ON_ARRIVAL, bearing: -20,
           speed: 0.8, curve: 1.2, essential: true };
}

function prefersReducedMotion() {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function createCamera(map, opts) {
  var reduced = (opts && opts.reduced !== undefined)
    ? opts.reduced : prefersReducedMotion();
  return {
    moveTo: function (tile, isPoi) {
      if (isPoi) {
        map.flyTo(flyOptions(tile, reduced));
        return;
      }
      var p = map.project([tile.lng, tile.lat]);
      var c = map.getContainer();
      if (needsPan(p, { width: c.clientWidth, height: c.clientHeight })) {
        map.panTo([tile.lng, tile.lat], { duration: reduced ? 200 : 600 });
      }
    },
    reduced: reduced,
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { toLngLat: toLngLat, needsPan: needsPan,
                     flyOptions: flyOptions, createCamera: createCamera };
} else if (typeof window !== "undefined") {
  window.LemiMap = { toLngLat: toLngLat, needsPan: needsPan,
                     flyOptions: flyOptions, createCamera: createCamera };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/mapkit.test.js`
Expected: PASS(6 个用例)

- [ ] **Step 5: 提交**

```bash
git add web/assets/core/mapkit.js tests/js/mapkit.test.js
git commit -m "feat(mapkit): restrained camera - pan at edges, pitched flyTo only on arrival"
```

---

## Task 13: 游戏主循环

**Files:**
- Create: `web/assets/game/game.js`
- Test: `tests/js/game.test.js`

**Interfaces:**
- Consumes: Task 7 storage、Task 8 dice、Task 9 card、Task 10 tiles、Task 12 mapkit
- Produces: `createGame(payload, storage, deps)`,含 `roll()`(async,返回本回合事件序列)、`state()`、`reset()`。Task 14 的页面脚本调用。

**规则:** `roll()` 必须按 `path` 顺序逐格产出事件,POI 不得跳过;掉卡时经 storage 去重;走到末格标记 `finished`。

- [ ] **Step 1: 写失败测试**

Create `tests/js/game.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { createGame } = require("../../web/assets/game/game.js");
const { createStorage } = require("../../web/assets/core/storage.js");

function mem() {
  let s = {};
  return { getItem: (k) => (k in s ? s[k] : null),
           setItem: (k, v) => { s[k] = String(v); } };
}

const PAYLOAD = {
  night_from_index: 3,
  board: [
    { index: 0, type: "poi", lat: 48.84, lng: 2.34, poi_id: "a" },
    { index: 1, type: "street", lat: 48.845, lng: 2.345, content_id: "s1" },
    { index: 2, type: "poi", lat: 48.85, lng: 2.35, poi_id: "b" },
    { index: 3, type: "easter", lat: 48.855, lng: 2.355, content_id: "e1" },
    { index: 4, type: "poi", lat: 48.86, lng: 2.36, poi_id: "c" },
  ],
  pois: { a: { id: "a" }, b: { id: "b" }, c: { id: "c" } },
  cards: {
    ca: { id: "ca", rarity: "R", poi_id: "a", title_zh: "A", title_en: "A",
          body_zh: "x", body_en: "x" },
    cb: { id: "cb", rarity: "R", poi_id: "b", title_zh: "B", title_en: "B",
          body_zh: "x", body_en: "x" },
    cc: { id: "cc", rarity: "R", poi_id: "c", title_zh: "C", title_en: "C",
          body_zh: "x", body_en: "x" },
    e1: { id: "e1", rarity: "SR", title_zh: "E", title_en: "E",
          body_zh: "x", body_en: "x" },
  },
  street_cards: { s1: { id: "s1", category: "rule", text_zh: "街",
                        text_en: "street" } },
  chance: {},
};

function fakeDeps(rollValue) {
  const moves = [];
  return {
    rng: () => (rollValue - 1) / 6 + 0.01,
    camera: { moveTo: (tile, isPoi) => moves.push([tile.index, isPoi]) },
    lang: "zh",
    _moves: moves,
  };
}

test("a roll of 2 from the start passes tile 1 and lands on tile 2", async () => {
  const deps = fakeDeps(2);
  const g = createGame(PAYLOAD, createStorage(mem()), deps);
  const events = await g.roll();
  assert.deepStrictEqual(events.map((e) => e.tileIndex), [1, 2]);
});

test("a POI passed mid-path still fires - the die never skips content", async () => {
  const deps = fakeDeps(4);           // 0 -> 4,途经 1,2,3
  const g = createGame(PAYLOAD, createStorage(mem()), deps);
  const events = await g.roll();
  const poiEvents = events.filter((e) => e.kind === "card" && e.content.rarity === "R");
  assert.ok(poiEvents.some((e) => e.tileIndex === 2), "tile 2 POI must fire");
  assert.strictEqual(events.length, 4);
});

test("landing on a POI marks the card as newly collected", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(2));
  const events = await g.roll();
  const card = events.find((e) => e.kind === "card");
  assert.strictEqual(card.isNew, true);
});

test("replaying an owned card reports isNew false and count stays put", async () => {
  const storage = createStorage(mem());
  storage.addCard("cb");
  const g = createGame(PAYLOAD, storage, fakeDeps(2));
  const events = await g.roll();
  const card = events.find((e) => e.kind === "card");
  assert.strictEqual(card.isNew, false);
  assert.strictEqual(storage.cardCount(), 1);
});

test("camera pitches only on POI tiles", async () => {
  const deps = fakeDeps(2);
  const g = createGame(PAYLOAD, createStorage(mem()), deps);
  await g.roll();
  assert.deepStrictEqual(deps._moves, [[1, false], [2, true]]);
});

test("crossing the night index flags the event", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(4));
  const events = await g.roll();
  assert.strictEqual(events.find((e) => e.tileIndex === 2).night, false);
  assert.strictEqual(events.find((e) => e.tileIndex === 3).night, true);
});

test("reaching the last tile finishes the run", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(6));
  const events = await g.roll();
  assert.strictEqual(events[events.length - 1].finished, true);
  assert.strictEqual(g.state().position, 4);
});

test("rolling after the run finished yields no events", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(6));
  await g.roll();
  assert.deepStrictEqual(await g.roll(), []);
});

test("position survives a reload through storage", async () => {
  const backend = mem();
  const g = createGame(PAYLOAD, createStorage(backend), fakeDeps(2));
  await g.roll();
  const g2 = createGame(PAYLOAD, createStorage(backend), fakeDeps(1));
  assert.strictEqual(g2.state().position, 2);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/game.test.js`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现**

Create `web/assets/game/game.js`:

```javascript
// Game loop. One roll produces an ordered list of events, one per tile
// walked. Every tile on the path fires, including POIs passed in the
// middle of a move — the die sets the pace, never the content.

var STORYLINE_ID = "emily-in-paris";

function _req(path, globalName, key) {
  if (typeof require !== "undefined") return require(path)[key];
  return window[globalName][key];
}

function createGame(payload, storage, deps) {
  var rollDice = _req("./dice.js", "LemiDice", "rollDice");
  var resolveMove = _req("./dice.js", "LemiDice", "resolveMove");
  var resolveTile = _req("./tiles.js", "LemiTiles", "resolveTile");
  var isNight = _req("./tiles.js", "LemiTiles", "isNight");

  var board = payload.board || [];
  var nightFrom = payload.night_from_index;
  var lang = (deps && deps.lang) || "zh";
  var camera = deps && deps.camera;
  var rng = deps && deps.rng;

  var saved = storage.load().storylines[STORYLINE_ID];
  var position = saved ? saved.tile : 0;

  function roll() {
    var move = resolveMove(position, rollDice(rng), board.length);
    var events = [];
    move.path.forEach(function (idx) {
      var tile = board[idx];
      var resolved = resolveTile(tile, payload, lang);
      if (camera) camera.moveTo(tile, tile.type === "poi");

      var isNew = false;
      if (resolved.kind === "card") {
        isNew = storage.addCard(resolved.content.id);
      }
      events.push({
        tileIndex: idx,
        kind: resolved.kind,
        durationMs: resolved.durationMs,
        content: resolved.content,
        isNew: isNew,
        night: isNight(idx, nightFrom),
        finished: idx === board.length - 1,
      });
    });
    position = move.to;
    storage.setTile(STORYLINE_ID, position);
    return Promise.resolve(events);
  }

  return {
    roll: roll,
    state: function () {
      return { position: position, finished: position >= board.length - 1,
               night: isNight(position, nightFrom) };
    },
    reset: function () {
      position = 0;
      storage.setTile(STORYLINE_ID, 0);
    },
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createGame: createGame };
} else if (typeof window !== "undefined") {
  window.LemiGame = { createGame: createGame };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/game.test.js`
Expected: PASS(9 个用例)

- [ ] **Step 5: 全量 JS 测试**

Run: `node --test --test-concurrency=2 tests/js/`
Expected: PASS(6 个测试文件全绿)

- [ ] **Step 6: 提交**

```bash
git add web/assets/game/game.js tests/js/game.test.js
git commit -m "feat(game): roll loop that fires every tile on the path"
```

---

## Task 14: 游戏页面与样式

**Files:**
- Create: `web/templates/board.html`
- Create: `web/assets/styles/base.css`
- Create: `web/assets/styles/game.css`
- Create: `web/assets/game/ui.js`
- Modify: `pipeline/build_site.py`(渲染 board.html)
- Test: `tests/test_frontend.py`

**Interfaces:**
- Consumes: Task 13 `createGame`;Task 11 `buildCollection`;Task 12 `createCamera`
- Produces: 可运行的游戏页面。Task 16 验收。

**动效时长(Global Constraints,必须精确):** 骰子按下 100ms + 翻滚 400ms;步行 ≤1000ms;掉卡 150/350/100ms;其他格 3000ms;reduced-motion 全部 200ms。

**移动端(spec 第 11 节):** 竖屏地图 55%,骰子置右下拇指热区,卡片走底部抽屉上滑占满屏,触控目标 ≥44px。

- [ ] **Step 1: 写失败测试**

v1 的 `test_city_html_references_maplibre_and_app` 与 `test_app_js_defines_picklang_and_visible` 指向已被取代的 `city.html`/`app.js`,**先删除这两个用例**,再追加到 `tests/test_frontend.py`:
    html = open(os.path.join(WEB, "templates", "board.html"), encoding="utf-8").read()
    for mod in ("core/storage.js", "core/mapkit.js", "game/dice.js",
                "game/card.js", "game/tiles.js", "game/collection.js",
                "game/game.js", "game/ui.js"):
        assert mod in html, f"board.html must load {mod}"
    assert "maplibre-gl" in html
    assert "{{CITY_ID}}" in html


def test_game_css_has_mobile_layout_and_touch_targets():
    css = open(os.path.join(WEB, "assets", "styles", "game.css"),
               encoding="utf-8").read()
    assert "@media" in css, "mobile-first is a hard requirement"
    assert "44px" in css, "touch targets must be at least 44px"


def test_game_css_honours_reduced_motion():
    css = open(os.path.join(WEB, "assets", "styles", "game.css"),
               encoding="utf-8").read()
    assert "prefers-reduced-motion" in css


def test_animation_durations_match_the_spec():
    css = open(os.path.join(WEB, "assets", "styles", "game.css"),
               encoding="utf-8").read()
    for ms in ("100ms", "400ms", "150ms", "350ms"):
        assert ms in css, f"spec timing {ms} missing from game.css"
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_frontend.py -v -k "board_html or game_css or animation_durations"`
Expected: FAIL — `FileNotFoundError: web/templates/board.html`

- [ ] **Step 3: 写 base.css**

Create `web/assets/styles/base.css`:

```css
/* Design tokens shared by both modes. */
:root {
  --paper: #faf7f2;
  --ink: #2b2723;
  --accent: #c0392b;
  --gold: #c9a227;
  --line: #e8e0d6;
  --night: #14203a;
  --radius: 10px;
  --touch: 44px;                 /* minimum touch target */
  --t-press: 100ms;
  --t-dice: 400ms;
  --t-walk: 1000ms;
  --t-card-out: 150ms;
  --t-card-develop: 350ms;
  --t-card-set: 100ms;
  --t-info: 3000ms;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Noto Sans SC", "PingFang SC", system-ui, sans-serif;
  color: var(--ink);
  background: var(--paper);
}

.serif { font-family: "Noto Serif SC", "Songti SC", serif; }
/* Handwriting is reserved for sourced quotes only. */
.handwriting { font-family: "Ma Shan Zheng", "Kaiti SC", cursive; }

button {
  min-height: var(--touch);
  min-width: var(--touch);
  border: 0;
  border-radius: var(--radius);
  font: inherit;
  cursor: pointer;
}
```

- [ ] **Step 4: 写 game.css**

Create `web/assets/styles/game.css`:

```css
/* Game mode. Mobile-first: the phone layout is the default, the desktop
   split is the override. Two of the three target scenarios are phones. */

#game {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

#map { flex: 0 0 55%; }

#controls {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  gap: 12px;
}

#daypart {
  font-size: 14px;
  letter-spacing: .05em;
}

#dice {
  width: 72px; height: 72px;          /* well past the 44px minimum */
  margin-left: auto;                   /* right-hand thumb zone */
  background: var(--accent);
  color: #fff;
  font-size: 28px; font-weight: 700;
}
#dice:active { transform: translateY(2px); transition: transform var(--t-press); }
#dice.rolling { animation: dice-roll var(--t-dice) cubic-bezier(.34,1.56,.64,1); }

@keyframes dice-roll {
  0%   { transform: rotateX(0) rotateY(0); }
  70%  { transform: rotateX(540deg) rotateY(360deg); }
  100% { transform: rotateX(720deg) rotateY(360deg); }
}

/* Pawn: Lemi walking with her backpack. */
#pawn { width: 36px; height: 36px; transition: transform var(--t-walk) linear; }

/* Card: a Polaroid developing. The blur-to-sharp reveal IS the suspense. */
.card {
  position: fixed; left: 0; right: 0; bottom: 0;
  max-height: 88dvh; overflow-y: auto;
  background: #fff;
  border-radius: 16px 16px 0 0;
  padding: 18px;
  animation: card-out var(--t-card-out) ease-out;
}
.card img { width: 100%; border-radius: 8px; animation: develop var(--t-card-develop) ease-out; }
.card.set { animation: card-set var(--t-card-set) ease-out; }

@keyframes card-out { from { transform: translateY(100%); } to { transform: none; } }
@keyframes develop {
  from { filter: blur(8px) saturate(0) brightness(1.4); }
  to   { filter: none; }
}
@keyframes card-set { 50% { transform: scale(1.02); } }

.card-r   { border: 2px solid var(--line); }
.card-sr  { border: 2px solid var(--gold); box-shadow: 0 0 18px rgba(201,162,39,.45); }
.card-ssr { border: 2px solid transparent;
            background-image: linear-gradient(#fff,#fff),
                              linear-gradient(90deg,#f0a,#0af,#af0,#f0a);
            background-origin: border-box; background-clip: padding-box, border-box; }

.card .quote { margin-top: 14px; font-size: 18px; }
.card .source { font-size: 12px; color: #888; }

/* Album: unowned cards stay visible as silhouettes so the gap is legible. */
#album { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.slot { aspect-ratio: 3/4; border-radius: var(--radius); }
.slot.locked { background: #ddd6cc; color: #a89e92;
               display: flex; align-items: center; justify-content: center; }
.slot.locked::after { content: "?"; font-size: 32px; }

#toast {
  position: fixed; left: 50%; bottom: 96px; transform: translateX(-50%);
  background: rgba(0,0,0,.82); color: #fff;
  padding: 10px 18px; border-radius: 20px;
  opacity: 0; transition: opacity 200ms;
}
#toast.show { opacity: 1; }

/* Night: one switch, not a gradient. "It got dark" is itself the event. */
body.night { background: var(--night); color: #e8eef8; }

@media (min-width: 860px) {
  #game { flex-direction: row; }
  #map { flex: 1; height: 100dvh; }
  #controls { flex: 0 0 380px; flex-direction: column; align-items: stretch; }
  .card { position: static; max-height: none; border-radius: var(--radius); }
}

@media (prefers-reduced-motion: reduce) {
  #dice.rolling, .card, .card img, .card.set { animation: none; }
  #pawn { transition: none; }
  .card { animation: fade 200ms ease-out; }
  @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
}
```

- [ ] **Step 5: 写 board.html**

Create `web/templates/board.html`:

```html
<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>Lemi's Diary</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
<link href="./assets/styles/base.css" rel="stylesheet" />
<link href="./assets/styles/game.css" rel="stylesheet" />
</head>
<body>
<div id="game">
  <div id="map"></div>
  <div id="controls">
    <span id="daypart">☀️ 白天</span>
    <button id="album-btn" type="button">🗂️ <span id="album-count">0/10</span></button>
    <button id="dice" type="button" aria-label="摇骰子">🎲</button>
  </div>
</div>
<div id="card-host" aria-live="polite"></div>
<div id="toast" role="status"></div>

<script>window.__CITY_ID__ = "{{CITY_ID}}";</script>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="./assets/core/storage.js"></script>
<script src="./assets/core/mapkit.js"></script>
<script src="./assets/game/dice.js"></script>
<script src="./assets/game/card.js"></script>
<script src="./assets/game/tiles.js"></script>
<script src="./assets/game/collection.js"></script>
<script src="./assets/game/game.js"></script>
<script src="./assets/game/ui.js"></script>
</body>
</html>
```

- [ ] **Step 6: 写 ui.js**

Create `web/assets/game/ui.js`(编排 DOM;纯逻辑已在前面任务测过):

```javascript
// Page wiring for game mode: boot the map, bind the die, render cards.
// All decision logic lives in the tested modules; this file only moves DOM.

(function () {
  if (typeof window === "undefined" || !document.getElementById) return;

  var T = { press: 100, dice: 400, walk: 1000, cardOut: 150,
            develop: 350, set: 100, info: 3000 };

  function reduced() {
    return window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function toast(msg) {
    var el = document.getElementById("toast");
    el.textContent = msg;
    el.classList.add("show");
    setTimeout(function () { el.classList.remove("show"); }, 1600);
  }

  function renderCard(card, host, onClose) {
    var box = document.createElement("div");
    box.className = "card " + window.LemiCard.rarityClass(card.rarity);
    var html = "";
    if (card.hasImage) {
      html += '<img src="' + card.image.thumb + '" alt="" '
            + 'onerror="this.style.display=\'none\'" />';
    }
    html += "<h3>" + card.title + "</h3>";
    html += '<p class="serif">' + card.body + "</p>";
    if (card.quote) {
      html += '<p class="quote handwriting">「' + card.quote.text + "」</p>";
      html += '<p class="source">' + card.quote.source + "</p>";
    }
    box.innerHTML = html;
    // Any click anywhere collects the card — no extra button to aim at.
    box.addEventListener("click", function () { box.remove(); onClose(); });
    host.appendChild(box);
    if (!reduced()) {
      setTimeout(function () { box.classList.add("set"); }, T.develop);
    }
  }

  function renderInfo(title, text, host) {
    var box = document.createElement("div");
    box.className = "card card-r";
    box.innerHTML = "<h3>" + title + '</h3><p class="serif">' + text + "</p>";
    host.appendChild(box);
    setTimeout(function () { box.remove(); }, reduced() ? 200 : T.info);
  }

  async function boot() {
    var cityId = window.__CITY_ID__ || "paris";
    var lang = localStorage.getItem("lemi_lang") || "zh";
    var payload = await fetch("./data/" + cityId + ".json").then(function (r) {
      return r.json();
    });

    var map = new maplibregl.Map({
      container: "map",
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [payload.city.center_lng, payload.city.center_lat],
      zoom: 13,
    });

    var storage = window.LemiStorage.createStorage(window.localStorage);
    var camera = window.LemiMap.createCamera(map);
    var game = window.LemiGame.createGame(payload, storage,
                                          { camera: camera, lang: lang });
    var host = document.getElementById("card-host");

    function refreshAlbum() {
      var c = window.LemiCollection.buildCollection(payload, storage, lang);
      document.getElementById("album-count").textContent =
        c.owned + "/" + c.total;
    }

    function setDaypart(night) {
      document.body.classList.toggle("night", night);
      document.getElementById("daypart").textContent = night ? "🌃 夜晚" : "☀️ 白天";
    }

    async function playEvents(events) {
      for (var i = 0; i < events.length; i++) {
        var e = events[i];
        setDaypart(e.night);
        if (e.kind === "card") {
          await new Promise(function (done) {
            renderCard(e.content, host, function () {
              if (e.isNew) { refreshAlbum(); toast("已收入卡册"); }
              done();
            });
          });
        } else if (e.kind === "street") {
          renderInfo("🗺️", e.content.text, host);
          await new Promise(function (r) { setTimeout(r, reduced() ? 200 : T.info); });
        } else if (e.kind === "chance") {
          renderInfo("🎴", e.content.question + "<br><b>"
                     + e.content.options[e.content.answerIndex] + "</b><br>"
                     + e.content.explain, host);
          await new Promise(function (r) { setTimeout(r, reduced() ? 200 : T.info); });
        } else if (e.kind === "photo") {
          renderInfo("📸", e.content.name, host);
          await new Promise(function (r) { setTimeout(r, reduced() ? 200 : T.info); });
        }
      }
    }

    var dice = document.getElementById("dice");
    dice.addEventListener("click", async function () {
      if (dice.disabled) return;
      dice.disabled = true;
      dice.classList.add("rolling");
      await new Promise(function (r) { setTimeout(r, reduced() ? 0 : T.dice); });
      dice.classList.remove("rolling");
      await playEvents(await game.roll());
      dice.disabled = false;
    });

    map.on("load", function () {
      refreshAlbum();
      setDaypart(game.state().night);
    });
  }

  window.addEventListener("DOMContentLoaded", boot);
})();
```

- [ ] **Step 7: 让 build_site 渲染 board.html**

修改 `pipeline/build_site.py` 的 `write_site`,把模板文件名改为 `board.html`,并复制 `assets` 下的子目录(`shutil.copytree` 的 `dirs_exist_ok=True` 已递归,无需改动):

```python
    tpl_path = os.path.join(web_dir, "templates", "board.html")
```

- [ ] **Step 8: 运行确认通过**

Run: `python -m pytest tests/test_frontend.py -v`
Expected: PASS

- [ ] **Step 9: 构建并人工确认**

Run: `LEMI_OFFLINE=1 python -m pipeline.run_paris && ls dist/assets/core dist/assets/game`
Expected: 两个目录下各有对应 .js 文件

- [ ] **Step 10: 删除被取代的 v1 前端**

`web/templates/city.html` 与 `web/assets/app.js` 已被 board.html + 模块化脚本取代,留着会被复制进 dist 成为死代码:

```bash
git rm web/templates/city.html web/assets/app.js
```

Run: `python -m pytest tests/ -q`
Expected: PASS(确认没有别处还引用它们)

- [ ] **Step 11: 提交**

```bash
git add web/templates/board.html web/assets/styles web/assets/game/ui.js \
        pipeline/build_site.py tests/test_frontend.py
git commit -m "feat(ui): game page with mobile-first layout and spec-exact timings"
```

---

## Task 15: 图鉴模式

**Files:**
- Create: `web/templates/codex.html`
- Create: `web/assets/codex/codex.js`
- Create: `web/assets/styles/codex.css`
- Modify: `pipeline/build_site.py`(额外渲染 codex.html)
- Test: `tests/js/codex.test.js`、`tests/test_frontend.py`

**Interfaces:**
- Consumes: payload 的 `storylines`/`pois`;Task 12 `flyOptions`
- Produces: `buildChapters(payload, lang)`、`hashForStop(n)`、`stopFromHash(hash)`

**约束(spec 第 9 节 + Global Constraints):** 本模式**不读写 localStorage**(`lemi_lang` 除外),不显示任何进度或集卡角标;CSS **禁用 vh**;移动端地图顶部 40% sticky。

- [ ] **Step 1: 写失败测试**

Create `tests/js/codex.test.js`:

```javascript
const { test } = require("node:test");
const assert = require("node:assert");
const { buildChapters, hashForStop, stopFromHash } =
  require("../../web/assets/codex/codex.js");

const PAYLOAD = {
  night_from_index: 13,
  pois: {
    a: { id: "a", name_zh: "甲", name_en: "A", lat: 1, lng: 2, base_images: [] },
    b: { id: "b", name_zh: "乙", name_en: "B", lat: 3, lng: 4, base_images: [] },
  },
  storylines: [{
    id: "sl", title_zh: "线", title_en: "Line",
    stops: [
      { poi_id: "a", order: 1, narrative: [
        { type: "scene", text_zh: "场景", text_en: "scene" }] },
      { poi_id: "b", order: 2, narrative: [
        { type: "history", text_zh: "历史", text_en: "history" }] },
    ],
  }],
};

test("chapters follow stop order", () => {
  const ch = buildChapters(PAYLOAD, "zh");
  assert.deepStrictEqual(ch.map((c) => c.title), ["甲", "乙"]);
});

test("chapters carry coordinates for the camera", () => {
  assert.deepStrictEqual(buildChapters(PAYLOAD, "zh")[0].center, [2, 1]);
});

test("chapters switch language", () => {
  assert.strictEqual(buildChapters(PAYLOAD, "en")[0].title, "A");
  assert.strictEqual(buildChapters(PAYLOAD, "en")[0].blocks[0].text, "scene");
});

test("hash round-trips a stop number", () => {
  assert.strictEqual(hashForStop(3), "#stop=3");
  assert.strictEqual(stopFromHash("#stop=3"), 3);
});

test("a malformed hash yields the first stop", () => {
  assert.strictEqual(stopFromHash("#nonsense"), 1);
  assert.strictEqual(stopFromHash(""), 1);
  assert.strictEqual(stopFromHash("#stop=abc"), 1);
});

test("codex never reads player state", () => {
  const src = require("fs").readFileSync(
    require("path").join(__dirname, "../../web/assets/codex/codex.js"), "utf8");
  assert.ok(!/lemi_state/.test(src), "codex must not touch player state");
  assert.ok(!/hasCard|cardCount|addCard/.test(src),
            "codex must not read the album");
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test --test-concurrency=2 tests/js/codex.test.js`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现 codex.js**

Create `web/assets/codex/codex.js`:

```javascript
// Codex mode: a read-only scrollytelling view of a storyline.
//
// This mode deliberately knows nothing about the player: no cards, no
// progress, no localStorage beyond the shared language preference. It
// serves the reader who just wants the material.

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function buildChapters(payload, lang) {
  var sl = (payload.storylines || [])[0];
  if (!sl) return [];
  var stops = (sl.stops || []).slice().sort(function (a, b) {
    return a.order - b.order;
  });
  return stops.map(function (st) {
    var poi = (payload.pois || {})[st.poi_id] || {};
    return {
      order: st.order,
      poiId: st.poi_id,
      title: pick(poi.name_zh, poi.name_en, lang),
      center: [poi.lng, poi.lat],
      image: (poi.base_images || [])[0] || null,
      night: st.order - 1 >= (payload.night_from_index || 99),
      blocks: (st.narrative || []).map(function (n) {
        return { type: n.type, text: pick(n.text_zh, n.text_en, lang) };
      }),
    };
  });
}

function hashForStop(n) { return "#stop=" + n; }

function stopFromHash(hash) {
  var m = /^#stop=(\d+)$/.exec(hash || "");
  return m ? parseInt(m[1], 10) : 1;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { buildChapters: buildChapters, hashForStop: hashForStop,
                     stopFromHash: stopFromHash };
} else if (typeof window !== "undefined") {
  window.LemiCodex = { buildChapters: buildChapters, hashForStop: hashForStop,
                       stopFromHash: stopFromHash };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `node --test --test-concurrency=2 tests/js/codex.test.js`
Expected: PASS(6 个用例)

- [ ] **Step 5: 写 codex.css**

Create `web/assets/styles/codex.css`:

```css
/* Codex mode. Scrollama drives the camera from scroll position.
   Note: no vh units anywhere — scrolling changes vh on mobile and would
   retrigger resize handlers. dvh/percentages only. */

#codex { display: flex; flex-direction: column; }

#codex-map {
  position: sticky; top: 0;
  height: 40dvh;
  z-index: 1;
}

#chapters { padding: 24px 18px 60dvh; }

.chapter {
  min-height: 70dvh;
  padding: 24px 0;
  opacity: .35;
  transition: opacity 300ms;
}
.chapter.active { opacity: 1; }
.chapter img { width: 100%; border-radius: 10px; }
.chapter h2 { font-size: 22px; }
.chapter p { line-height: 1.75; }

@media (min-width: 860px) {
  #codex { flex-direction: row-reverse; }
  #codex-map { flex: 1; height: 100dvh; }
  #chapters { flex: 0 0 420px; padding: 40px 28px 60dvh; }
}

@media (prefers-reduced-motion: reduce) {
  .chapter { transition: none; }
}
```

- [ ] **Step 6: 写 codex.html**

Create `web/templates/codex.html`:

```html
<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>Lemi's Diary · 图鉴</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
<link href="./assets/styles/base.css" rel="stylesheet" />
<link href="./assets/styles/codex.css" rel="stylesheet" />
</head>
<body>
<div id="codex">
  <div id="codex-map"></div>
  <div id="chapters"></div>
</div>
<a id="to-game" href="./index.html">🎲 玩游戏</a>

<script>window.__CITY_ID__ = "{{CITY_ID}}";</script>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/scrollama"></script>
<script src="./assets/core/mapkit.js"></script>
<script src="./assets/codex/codex.js"></script>
<script>
(function () {
  async function boot() {
    var cityId = window.__CITY_ID__ || "paris";
    var lang = localStorage.getItem("lemi_lang") || "zh";
    var payload = await fetch("./data/" + cityId + ".json")
      .then(function (r) { return r.json(); });

    var chapters = window.LemiCodex.buildChapters(payload, lang);
    var host = document.getElementById("chapters");
    chapters.forEach(function (c) {
      var sec = document.createElement("section");
      sec.className = "chapter";
      sec.dataset.stop = c.order;
      var html = "<h2>" + c.order + ". " + c.title + "</h2>";
      if (c.image) html += '<img src="' + c.image.thumb + '" alt="" />';
      c.blocks.forEach(function (b) { html += '<p class="serif">' + b.text + "</p>"; });
      sec.innerHTML = html;
      host.appendChild(sec);
    });

    var map = new maplibregl.Map({
      container: "codex-map",
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: chapters.length ? chapters[0].center
                              : [payload.city.center_lng, payload.city.center_lat],
      zoom: 14,
    });

    var reduced = window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    scrollama().setup({ step: ".chapter", offset: "300px" })
      .onStepEnter(function (res) {
        document.querySelectorAll(".chapter").forEach(function (el) {
          el.classList.remove("active");
        });
        res.element.classList.add("active");
        var c = chapters[res.index];
        map.flyTo({ center: c.center, zoom: 16, pitch: reduced ? 0 : 45,
                    duration: reduced ? 200 : 1200, essential: true });
        history.replaceState(null, "", window.LemiCodex.hashForStop(c.order));
      });

    var target = window.LemiCodex.stopFromHash(location.hash);
    var el = document.querySelector('.chapter[data-stop="' + target + '"]');
    if (el) el.scrollIntoView();
  }
  window.addEventListener("DOMContentLoaded", boot);
})();
</script>
</body>
</html>
```

- [ ] **Step 7: 让 build_site 同时输出 codex.html**

在 `write_site` 末尾追加:

```python
    codex_tpl = os.path.join(web_dir, "templates", "codex.html")
    if os.path.isfile(codex_tpl):
        with open(codex_tpl, "r", encoding="utf-8") as f:
            codex_html = f.read().replace("{{CITY_ID}}", city_id)
        with open(os.path.join(dist_dir, "codex.html"), "w", encoding="utf-8") as f:
            f.write(codex_html)
```

并在 `board.html` 的 controls 里加一个入口:

```html
    <a id="to-codex" href="./codex.html">📖 图鉴</a>
```

- [ ] **Step 8: 加前端测试**

追加到 `tests/test_frontend.py`:

```python
def test_codex_css_avoids_vh_units():
    css = open(os.path.join(WEB, "assets", "styles", "codex.css"),
               encoding="utf-8").read()
    import re
    # dvh is fine; bare vh retriggers resize while scrolling on mobile
    assert not re.search(r"\d+vh\b", css), "codex.css must not use vh units"


def test_codex_html_loads_scrollama():
    html = open(os.path.join(WEB, "templates", "codex.html"),
                encoding="utf-8").read()
    assert "scrollama" in html
    assert "essential" in html, "flyTo must pass essential:true"
```

- [ ] **Step 9: 运行全部测试**

Run: `python -m pytest tests/ -q && node --test --test-concurrency=2 tests/js/`
Expected: 两者均 PASS

- [ ] **Step 10: 提交**

```bash
git add web/templates/codex.html web/assets/codex web/assets/styles/codex.css \
        pipeline/build_site.py tests/js/codex.test.js tests/test_frontend.py
git commit -m "feat(codex): read-only scrollytelling mode decoupled from player state"
```

---

## Task 16: 端到端验收与文档

**Files:**
- Modify: `README.md`
- Modify: `tests/test_e2e_paris.py`

**Interfaces:**
- Consumes: 全部前序任务
- Produces: 可部署的 dist/ 与更新后的文档

- [ ] **Step 1: 写端到端测试**

追加到 `tests/test_e2e_paris.py`:

```python
def test_built_payload_has_playable_board(tmp_path):
    import json
    import os
    import subprocess
    env = dict(os.environ, LEMI_OFFLINE="1")
    subprocess.run(["python", "-m", "pipeline.run_paris"], check=True, env=env)
    d = json.load(open("dist/data/paris.json", encoding="utf-8"))

    assert len(d["board"]) == 20
    assert d["board"][0]["type"] == "poi"
    assert d["board"][-1]["type"] == "poi"
    assert d["night_from_index"] == 13

    # 每个非 POI 格都必须挂到真实内容上,否则玩家会走到空格子
    pools = {"street": d["street_cards"], "chance": d["chance"],
             "easter": d["cards"]}
    for tile in d["board"]:
        if tile["type"] in pools:
            assert tile.get("content_id") in pools[tile["type"]], (
                f"tile {tile['index']} ({tile['type']}) points at missing content")

    assert len(d["cards"]) == 10
    assert len([c for c in d["cards"].values() if c["rarity"] == "R"]) == 7
    assert len(d["street_cards"]) == 5


def test_dist_has_both_mode_pages():
    import os
    assert os.path.isfile("dist/index.html")
    assert os.path.isfile("dist/codex.html")
    for mod in ("core/storage.js", "core/mapkit.js", "game/game.js",
                "codex/codex.js"):
        assert os.path.isfile(os.path.join("dist", "assets", mod)), mod
```

- [ ] **Step 2: 运行确认**

Run: `python -m pytest tests/test_e2e_paris.py -v`
Expected: PASS

- [ ] **Step 3: 全量测试**

Run: `python -m pytest tests/ -q && node --test --test-concurrency=2 tests/js/`
Expected: 全绿

- [ ] **Step 4: 手动验收清单**

起本地服务 `cd dist && python3 -m http.server 8090 --bind 0.0.0.0`,逐项确认:

- [ ] 摇骰子:按下有下沉反馈,翻滚约 0.4 秒后出点数
- [ ] Lemi 背包步行,1 秒内走完;走路时镜头不跟
- [ ] 落 POI 格:镜头俯冲(可见倾斜),拍立得从底部吐出并由模糊显影为清晰
- [ ] 点卡片任意位置 → 卡片消失 + toast「已收入卡册」
- [ ] 卡册计数递增;打开卡册可见未获得卡的剪影 `?` 占位
- [ ] 同一张卡再次掉落时计数不变
- [ ] 走过第 13 格后切夜景,铁塔格可见
- [ ] 手机尺寸(375×812)下:地图占上方 55%,骰子在右下拇指区,卡片上滑占满屏
- [ ] 开启系统「减弱动态效果」后重载:动效消失但流程可走完
- [ ] 图鉴模式:滚动驱动地图飞行;URL 出现 `#stop=N`;刷新后回到该站
- [ ] 图鉴模式不显示任何集卡进度

- [ ] **Step 5: 更新 README**

在 `README.md` 增补 v2 章节:玩法说明、两种模式入口、`content/` 各目录职责、`VERIFIED_CONTENT.md` 的作用与新增内容时的验证要求(交叉验证 ≥2 源 + 对抗审查 + 措辞不说绝)、本地预览与部署命令。

- [ ] **Step 6: 提交**

```bash
git add README.md tests/test_e2e_paris.py
git commit -m "test(e2e): assert a playable board and both mode pages ship"
```

---

## 自审记录

**Spec 覆盖检查**

| Spec 章节 | 对应任务 |
|---|---|
| 3.1 骰子不跳过 POI | Task 8(`resolveMove` 返回完整 path)、Task 13(逐格触发测试) |
| 3.2 棋盘 20 格构成 | Task 3(生成器)、Task 5(filler_plan)、Task 16(e2e 断言) |
| 3.3 白天/夜晚第 13 格切换 | Task 10 `isNight`、Task 13 事件 `night`、Task 14 `body.night` |
| 4 卡池 R/SR/SSR | Task 5(内容)、Task 11(卡册分母 10、SSR 锁定) |
| 5.2 动效时长 | Task 14(CSS 变量 + 测试断言精确毫秒值) |
| 5.3 镜头策略 | Task 12(`needsPan`/`flyOptions`)、Task 13(仅 POI 传 isPoi=true) |
| 5.4 卡面与收卡 | Task 9(整形)、Task 14(点任意处收卡 + toast) |
| 5.5 其他格 3 秒 | Task 10(`DURATIONS.info=3000`) |
| 6 内容真实性 gate | Task 2(verify.py)、Task 5(内容取自 VERIFIED_CONTENT.md) |
| 7 数据模型 | Task 1 |
| 8 卡册剪影占位 | Task 11 |
| 9 图鉴模式 | Task 15 |
| 10 localStorage | Task 7 |
| 11 移动端 | Task 14(mobile-first CSS + 测试) |
| 12 无障碍降级 | Task 12(essential)、Task 14(reduced-motion CSS) |

**Review Focus 落点**

| 风险 | 测试所在 |
|---|---|
| localStorage 不可用 | Task 7「game still works when localStorage throws」 |
| 版本迁移不丢卡 | Task 7「migrate keeps collected cards」 |
| 骰子越界 | Task 8「move stops at the last tile when the roll overshoots」 |
| 重复收卡不重复计数 | Task 7「addCard is idempotent」、Task 13「replaying an owned card」 |
| 图片缺失仍可读 | Task 9「card without an image is still readable」 |

**类型一致性**:`createStorage`/`resolveMove`/`resolveTile`/`shapeCard`/`buildCollection`/`createCamera`/`createGame` 在定义任务与消费任务中签名一致,已逐一核对。
