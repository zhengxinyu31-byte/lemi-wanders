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

*(后续任务 4-16 见下一节,将在本文件中续写)*
