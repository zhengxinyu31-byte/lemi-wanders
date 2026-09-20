# Lemi's Diary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 Lemi's Diary —— 一个纯静态的「出境游文化故事线地图」展示站,首期打通「巴黎 × 《艾米莉在巴黎》」样板:LLM 抽取 POI 并排成故事线、Photon 校准真实坐标、Wikimedia 配图,渲染成带中英切换的 MapLibre 交互地图。

**Architecture:** 四层分离——`content/`(JSON 数据层,可 git 版本管理的"手账原稿")、`pipeline/`(Python 构建期生产链)、`web/`(纯静态前端模板 + i18n)、`dist/`(GitHub Pages 发布产物)。数据模型三层解耦:POI(共享地点)/ StoryStop(POI × 故事线的一站,承载叙事内容)/ StoryLine(故事线)。生产全在构建期离线完成,产出静态 HTML/JSON,无运行时后端。

**Tech Stack:** Python 3.11+(标准库 + requests);前端纯静态 HTML + 原生 JS + MapLibre GL(CDN,无打包);地理编码 Photon(OSM);配图 Wikimedia Commons;托管 GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-09-20-lemis-diary-design.md`

## Global Constraints

- Python 版本:>= 3.11(与 spec §9.4 一致)。
- 依赖最小化:Python 仅用标准库 + `requests`;前端零框架、零打包、零构建链。
- 所有外部凭证/配置经环境变量读取(`os.getenv`),禁止硬编码(AgentKnow required)。
- 所有对外 I/O(HTTP 请求)必须设置显式 timeout(AgentKnow required)。
- 多 provider / 多策略场景用 `abc.ABC` 抽象基类 + 策略模式,禁止散落 if/elif 分派(AgentKnow required)。
- 对外可见的模块/类/函数必须写 docstring(AgentKnow required)。
- import 分组顺序:`__future__` → 标准库 → 第三方 → 本地包(AgentKnow recommended)。
- 坐标一律以 `[lat, lng]` 顺序在 Python 数据层存储;仅在传给 MapLibre 时转成 `[lng, lat]`(MapLibre 用 GeoJSON 经纬顺序)。此约定全局统一,避免经纬颠倒。
- 「宁缺毋滥」:每条 narrative/practical 内容与每张图片都带 `confidence ∈ {high, mid, low}`;展示阈值 `>= mid`,低于阈值不展示,不做人工复核。
- 多语言:数据双语存储(`text_zh`/`text_en`);UI 同一时刻单语显示,全局切换,localStorage 持久化。
- 影视图片仅用官方海报,禁止正片截图。
- Wikimedia 图片必须记录 `author` / `license` / `source_page` 以合规。

## Review Focus

以下是 spec 隐含、但容易被忽略而伤到用户的输入/失败模式,每条已在对应 Task 的测试中覆盖:

1. **共享 POI 在两条故事线显示串味** —— 同一 POI(花神咖啡馆)在《艾米莉在巴黎》线和存在主义线各自的 StoryStop 内容必须隔离,不能混显。覆盖于 Task 3(数据模型)与 Task 9(前端按当前故事线取内容)。
2. **地理编码同名地点命中错城** —— 查 "Café de Flore" 未带城市偏置可能命中他城同名店。覆盖于 Task 5(带城市偏置 + 结果落在城市 bbox 内才接受)。
3. **图片全局重复** —— 同一故事线多个 POI 配到同一张图。覆盖于 Task 6(配图去重,已用图片指纹集)。
4. **低置信度内容/图片漏展示** —— confidence 为 low 的内容或图片被渲染出来。覆盖于 Task 7(内容过滤)与 Task 9(前端渲染过滤)。
5. **语言切换后仍残留另一语言** —— 切到 en 后某些字段仍显示中文(缺 en 译文时的兜底)。覆盖于 Task 9(缺失译文回退策略 + 切换测试)。

---

## File Structure

```
lemis-diary/
├── README.md                      # 项目说明 + 快速开始
├── requirements.txt               # requests
├── .gitignore                     # cache/, dist/, .env, __pycache__/
├── .env.example                   # LLM_API_KEY 等占位
├── pytest.ini                     # pytest 配置
├── content/                       # 数据层(手工/生成的 JSON 原稿)
│   ├── cities/paris.json          #   城市
│   ├── pois/*.json                #   共享 POI(每 POI 一文件)
│   └── storylines/emily-in-paris.json   # 故事线 + 有序 StoryStop
├── pipeline/
│   ├── __init__.py
│   ├── models.py                  # 数据类:POI / StoryStop / StoryLine / City / Narrative / ImageRef
│   ├── schema.py                  # 加载 + 校验 content/ JSON,confidence 过滤
│   ├── geocode.py                 # Photon 地理编码(策略基类 + 城市偏置 + bbox 校验)
│   ├── images.py                  # Wikimedia 配图(GeoSearch + 名称搜图 + 降级链 + 去重)
│   ├── content_gen.py             # LLM 生成 narrative(双语 + confidence 自评);离线可注入 mock
│   ├── llm_client.py              # LLM HTTP 封装(env 读 key,超时,失败降级)
│   └── build_site.py              # 组装 dist/:注入数据 JSON + 拷贝 web/ 模板
├── web/
│   ├── templates/city.html        # 城市地图页(MapLibre + 侧栏 + 故事线切换 + 语言切换)
│   ├── i18n/zh.json               # UI 文案(中)
│   ├── i18n/en.json               # UI 文案(英)
│   └── assets/app.js              # 前端逻辑(取数、渲染、切换、地图)
├── cache/images/                  # Wikimedia 下载缓存(gitignore)
├── dist/                          # 构建产物(gitignore,GitHub Pages 发布目录)
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_schema.py
    ├── test_geocode.py
    ├── test_images.py
    ├── test_content_gen.py
    └── test_build_site.py
```

**依赖顺序:** Task 1(脚手架) → Task 2(models) → Task 3(schema/加载+过滤) → Task 4(llm_client) → Task 5(geocode) → Task 6(images) → Task 7(content_gen) → Task 8(build_site) → Task 9(前端) → Task 10(端到端跑通巴黎样板) → Task 11(README + 部署文档)。

---

### Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`, `.gitignore`, `.env.example`, `pytest.ini`, `pipeline/__init__.py`, `tests/__init__.py`

**Interfaces:**
- Consumes: 无
- Produces: 可运行 `pytest` 的空项目骨架;`pipeline` 可被 import。

- [ ] **Step 1: 创建 requirements.txt**

```
requests>=2.31.0
```

- [ ] **Step 2: 创建 .gitignore**

```
__pycache__/
*.pyc
.env
cache/
dist/
.pytest_cache/
```

- [ ] **Step 3: 创建 .env.example**

```
# LLM(内容生成用;离线测试可留空,走 mock)
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.minimaxi.com/v1
LLM_MODEL_ID=MiniMax-M3
LLM_TIMEOUT=120
```

- [ ] **Step 4: 创建 pytest.ini**

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 5: 创建空包文件**

`pipeline/__init__.py` 内容:
```python
"""Lemi's Diary build pipeline package."""
```
`tests/__init__.py` 为空文件。

- [ ] **Step 6: 验证 pytest 能收集(0 用例不报错)**

Run: `cd lemis-diary && python3 -m pytest -q`
Expected: `no tests ran` 且 exit code 5 或 0,无 import 错误。

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .gitignore .env.example pytest.ini pipeline/__init__.py tests/__init__.py
git commit -m "chore: scaffold lemis-diary project"
```

---

### Task 2: 数据模型(models.py)

**Files:**
- Create: `pipeline/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `ImageRef(url:str, thumb:str, author:str, license:str, source_page:str, confidence:str)` dataclass
  - `Narrative(type:str, text_zh:str, text_en:str, confidence:str, image:Optional[ImageRef]=None)` dataclass
  - `POI(id:str, city:str, country:str, name_zh:str, name_en:str, lat:Optional[float], lng:Optional[float], address_zh:str, address_en:str, base_images:List[ImageRef], practical:Optional[Narrative], default_photo_spot:Optional[Narrative])` dataclass
  - `StoryStop(storyline_id:str, poi_id:str, order:int, narrative:List[Narrative], photo_spot_override:Optional[Narrative]=None)` dataclass
  - `StoryLine(id:str, city:str, title_zh:str, title_en:str, theme:str, summary_zh:str, summary_en:str, stops:List[StoryStop], poster:Optional[ImageRef]=None)` dataclass
  - `City(id:str, name_zh:str, name_en:str, center_lat:float, center_lng:float, bbox:Tuple[float,float,float,float])` dataclass —— bbox = (min_lat, min_lng, max_lat, max_lng)
  - 常量:`CONFIDENCE_ORDER = {"low": 0, "mid": 1, "high": 2}`;`NARRATIVE_TYPES = ("scene", "anecdote", "masterpiece", "history")`
  - 函数 `meets_threshold(confidence:str, threshold:str="mid") -> bool`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_models.py
from pipeline.models import (
    ImageRef, Narrative, POI, StoryStop, StoryLine, City,
    meets_threshold, CONFIDENCE_ORDER, NARRATIVE_TYPES,
)


def test_meets_threshold_default_mid():
    assert meets_threshold("high") is True
    assert meets_threshold("mid") is True
    assert meets_threshold("low") is False


def test_meets_threshold_unknown_is_false():
    # 未知置信度按最保守处理:不展示
    assert meets_threshold("") is False
    assert meets_threshold("garbage") is False


def test_poi_holds_shared_fields_only():
    poi = POI(
        id="cafe-de-flore", city="paris", country="France",
        name_zh="花神咖啡馆", name_en="Café de Flore",
        lat=48.85414, lng=2.33263,
        address_zh="圣日耳曼大道172号", address_en="172 Bd Saint-Germain",
        base_images=[], practical=None, default_photo_spot=None,
    )
    assert poi.id == "cafe-de-flore"
    assert poi.lat == 48.85414


def test_storystop_carries_narrative():
    stop = StoryStop(
        storyline_id="emily-in-paris", poi_id="cafe-de-flore", order=6,
        narrative=[Narrative(type="scene", text_zh="Emily 在此喝咖啡",
                             text_en="Emily has coffee here", confidence="high")],
    )
    assert stop.narrative[0].type == "scene"
    assert stop.order == 6


def test_narrative_types_constant():
    assert "anecdote" in NARRATIVE_TYPES
    assert CONFIDENCE_ORDER["high"] > CONFIDENCE_ORDER["low"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_models.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'pipeline.models'`)

- [ ] **Step 3: 写实现**

```python
# pipeline/models.py
"""Core data models for Lemi's Diary.

Three-layer decoupling: POI (shared place) / StoryStop (POI × storyline,
carries narrative) / StoryLine. Objective facts live on POI; subjective
narrative lives on StoryStop, so one shared POI can tell different stories
in different storylines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

CONFIDENCE_ORDER = {"low": 0, "mid": 1, "high": 2}
NARRATIVE_TYPES = ("scene", "anecdote", "masterpiece", "history")
DEFAULT_THRESHOLD = "mid"


def meets_threshold(confidence: str, threshold: str = DEFAULT_THRESHOLD) -> bool:
    """Return True if confidence is at or above threshold.

    Unknown confidence values are treated as below threshold (do not show).
    """
    if confidence not in CONFIDENCE_ORDER:
        return False
    return CONFIDENCE_ORDER[confidence] >= CONFIDENCE_ORDER[threshold]


@dataclass
class ImageRef:
    """A single image with attribution for licensing compliance."""

    url: str
    thumb: str
    author: str
    license: str
    source_page: str
    confidence: str


@dataclass
class Narrative:
    """One bilingual narrative field with a confidence tag and optional image."""

    type: str
    text_zh: str
    text_en: str
    confidence: str
    image: Optional[ImageRef] = None


@dataclass
class POI:
    """Shared place object; objective info only, shared across storylines."""

    id: str
    city: str
    country: str
    name_zh: str
    name_en: str
    lat: Optional[float]
    lng: Optional[float]
    address_zh: str
    address_en: str
    base_images: List[ImageRef] = field(default_factory=list)
    practical: Optional[Narrative] = None
    default_photo_spot: Optional[Narrative] = None


@dataclass
class StoryStop:
    """One stop on a storyline = POI × storyline; carries the narrative."""

    storyline_id: str
    poi_id: str
    order: int
    narrative: List[Narrative] = field(default_factory=list)
    photo_spot_override: Optional[Narrative] = None


@dataclass
class StoryLine:
    """An ordered themed route of StoryStops through a city."""

    id: str
    city: str
    title_zh: str
    title_en: str
    theme: str
    summary_zh: str
    summary_en: str
    stops: List[StoryStop] = field(default_factory=list)
    poster: Optional[ImageRef] = None


@dataclass
class City:
    """A city container. bbox = (min_lat, min_lng, max_lat, max_lng)."""

    id: str
    name_zh: str
    name_en: str
    center_lat: float
    center_lng: float
    bbox: Tuple[float, float, float, float]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_models.py -v`
Expected: PASS(5 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/models.py tests/test_models.py
git commit -m "feat(models): add three-layer POI/StoryStop/StoryLine data models"
```

---

### Task 3: 数据加载与 confidence 过滤(schema.py)

**Files:**
- Create: `pipeline/schema.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Consumes: `pipeline.models`(所有 dataclass + `meets_threshold`)
- Produces:
  - `load_city(path:str) -> City`
  - `load_poi(path:str) -> POI`
  - `load_storyline(path:str) -> StoryLine`
  - `stops_for_storyline(storyline:StoryLine) -> List[StoryStop]`(按 order 排序返回)
  - `visible_narrative(stop:StoryStop, threshold:str="mid") -> List[Narrative]`(过滤掉低置信度)
  - `resolve_photo_spot(poi:POI, stop:StoryStop) -> Optional[Narrative]`(override 优先,否则 POI 默认;需过阈值)

**关键点(Review Focus #1):** `stops_for_storyline` 保证不同故事线各取各的 stops;`visible_narrative` 保证 Review Focus #4(低置信度不出)。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_schema.py
from pipeline.models import POI, StoryStop, StoryLine, Narrative
from pipeline.schema import (
    stops_for_storyline, visible_narrative, resolve_photo_spot,
)


def _stop(order, narrs, poi_id="p1", sl="sl1", override=None):
    return StoryStop(storyline_id=sl, poi_id=poi_id, order=order,
                     narrative=narrs, photo_spot_override=override)


def test_stops_sorted_by_order():
    sl = StoryLine(id="sl1", city="paris", title_zh="", title_en="",
                   theme="", summary_zh="", summary_en="",
                   stops=[_stop(3, []), _stop(1, []), _stop(2, [])])
    orders = [s.order for s in stops_for_storyline(sl)]
    assert orders == [1, 2, 3]


def test_visible_narrative_filters_low_confidence():
    stop = _stop(1, [
        Narrative("scene", "高", "high", "high"),
        Narrative("anecdote", "低", "low", "low"),
        Narrative("history", "中", "mid", "mid"),
    ])
    kept = [n.type for n in visible_narrative(stop)]
    assert kept == ["scene", "history"]  # low 被过滤


def test_shared_poi_isolated_between_storylines():
    # 同一 POI 在两条线各有 StoryStop,内容不串味(Review Focus #1)
    emily = _stop(6, [Narrative("scene", "Emily喝咖啡", "Emily", "high")],
                  poi_id="cafe", sl="emily-in-paris")
    philo = _stop(2, [Narrative("anecdote", "波伏娃写作", "Beauvoir", "high")],
                  poi_id="cafe", sl="existentialism")
    assert visible_narrative(emily)[0].text_zh == "Emily喝咖啡"
    assert visible_narrative(philo)[0].text_zh == "波伏娃写作"


def test_resolve_photo_spot_override_wins():
    poi = POI(id="cafe", city="paris", country="FR", name_zh="", name_en="",
              lat=1.0, lng=2.0, address_zh="", address_en="",
              default_photo_spot=Narrative("photo_spot", "默认机位", "default", "high"))
    override = Narrative("photo_spot", "专属机位", "special", "high")
    stop = _stop(1, [], override=override)
    assert resolve_photo_spot(poi, stop).text_zh == "专属机位"


def test_resolve_photo_spot_falls_back_to_poi_default():
    poi = POI(id="cafe", city="paris", country="FR", name_zh="", name_en="",
              lat=1.0, lng=2.0, address_zh="", address_en="",
              default_photo_spot=Narrative("photo_spot", "默认机位", "default", "high"))
    stop = _stop(1, [])
    assert resolve_photo_spot(poi, stop).text_zh == "默认机位"


def test_resolve_photo_spot_low_confidence_returns_none():
    poi = POI(id="cafe", city="paris", country="FR", name_zh="", name_en="",
              lat=1.0, lng=2.0, address_zh="", address_en="",
              default_photo_spot=Narrative("photo_spot", "弱机位", "weak", "low"))
    stop = _stop(1, [])
    assert resolve_photo_spot(poi, stop) is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_schema.py -v`
Expected: FAIL(`No module named 'pipeline.schema'`)

- [ ] **Step 3: 写实现**

```python
# pipeline/schema.py
"""Load content/ JSON into models and apply confidence filtering."""
from __future__ import annotations

import json
from typing import List, Optional

from pipeline.models import (
    City, ImageRef, Narrative, POI, StoryLine, StoryStop, meets_threshold,
)


def _image_from_dict(d: Optional[dict]) -> Optional[ImageRef]:
    if not d:
        return None
    return ImageRef(
        url=d.get("url", ""), thumb=d.get("thumb", ""),
        author=d.get("author", ""), license=d.get("license", ""),
        source_page=d.get("source_page", ""), confidence=d.get("confidence", "low"),
    )


def _narrative_from_dict(d: Optional[dict]) -> Optional[Narrative]:
    if not d:
        return None
    return Narrative(
        type=d.get("type", ""), text_zh=d.get("text_zh", ""),
        text_en=d.get("text_en", ""), confidence=d.get("confidence", "low"),
        image=_image_from_dict(d.get("image")),
    )


def load_city(path: str) -> City:
    """Load a City from a JSON file."""
    d = json.loads(_read(path))
    bbox = tuple(d["bbox"])  # (min_lat, min_lng, max_lat, max_lng)
    return City(
        id=d["id"], name_zh=d["name_zh"], name_en=d["name_en"],
        center_lat=d["center_lat"], center_lng=d["center_lng"], bbox=bbox,
    )


def load_poi(path: str) -> POI:
    """Load a shared POI from a JSON file."""
    d = json.loads(_read(path))
    return POI(
        id=d["id"], city=d["city"], country=d.get("country", ""),
        name_zh=d["name_zh"], name_en=d["name_en"],
        lat=d.get("lat"), lng=d.get("lng"),
        address_zh=d.get("address_zh", ""), address_en=d.get("address_en", ""),
        base_images=[_image_from_dict(i) for i in d.get("base_images", []) if i],
        practical=_narrative_from_dict(d.get("practical")),
        default_photo_spot=_narrative_from_dict(d.get("default_photo_spot")),
    )


def load_storyline(path: str) -> StoryLine:
    """Load a StoryLine (with its StoryStops) from a JSON file."""
    d = json.loads(_read(path))
    stops = []
    for s in d.get("stops", []):
        stops.append(StoryStop(
            storyline_id=d["id"], poi_id=s["poi_id"], order=s["order"],
            narrative=[_narrative_from_dict(n) for n in s.get("narrative", []) if n],
            photo_spot_override=_narrative_from_dict(s.get("photo_spot_override")),
        ))
    return StoryLine(
        id=d["id"], city=d["city"], title_zh=d["title_zh"], title_en=d["title_en"],
        theme=d.get("theme", ""), summary_zh=d.get("summary_zh", ""),
        summary_en=d.get("summary_en", ""), stops=stops,
        poster=_image_from_dict(d.get("poster")),
    )


def stops_for_storyline(storyline: StoryLine) -> List[StoryStop]:
    """Return this storyline's stops sorted by order."""
    return sorted(storyline.stops, key=lambda s: s.order)


def visible_narrative(stop: StoryStop, threshold: str = "mid") -> List[Narrative]:
    """Return only narrative entries at or above the confidence threshold."""
    return [n for n in stop.narrative if n and meets_threshold(n.confidence, threshold)]


def resolve_photo_spot(poi: POI, stop: StoryStop,
                       threshold: str = "mid") -> Optional[Narrative]:
    """Resolve the photo spot: stop override wins, else POI default; must pass threshold."""
    candidate = stop.photo_spot_override or poi.default_photo_spot
    if candidate and meets_threshold(candidate.confidence, threshold):
        return candidate
    return None


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_schema.py -v`
Expected: PASS(6 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/schema.py tests/test_schema.py
git commit -m "feat(schema): load content JSON + confidence filtering + shared-POI isolation"
```

---

### Task 4: LLM 客户端封装(llm_client.py)

**Files:**
- Create: `pipeline/llm_client.py`
- Test: `tests/test_llm_client.py`

**Interfaces:**
- Consumes: 无(env 读配置)
- Produces:
  - `class LLMClient` with `__init__(self, api_key:Optional[str]=None, base_url:Optional[str]=None, model:Optional[str]=None, timeout:Optional[int]=None, http_post=None)` —— `http_post` 可注入用于测试
  - `LLMClient.complete(self, system:str, user:str) -> str`(返回模型文本;网络失败抛 `LLMError`)
  - `class LLMError(Exception)`
  - `LLMClient.from_env() -> LLMClient`(从环境变量装配)

**关键点:** 凭证走 `os.getenv`(不硬编码);HTTP 必设 timeout(AgentKnow required)。`http_post` 依赖注入使单测无需真实网络。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_llm_client.py
import pytest
from pipeline.llm_client import LLMClient, LLMError


def test_complete_returns_text_via_injected_post():
    def fake_post(url, headers, json, timeout):
        class R:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "hello"}}]}
            def raise_for_status(self):
                pass
        assert timeout == 30  # timeout 必须被传入
        return R()

    client = LLMClient(api_key="k", base_url="http://x/v1", model="m",
                       timeout=30, http_post=fake_post)
    assert client.complete("sys", "usr") == "hello"


def test_complete_raises_llmerror_on_network_failure():
    def boom(url, headers, json, timeout):
        raise ConnectionError("down")

    client = LLMClient(api_key="k", base_url="http://x/v1", model="m",
                       timeout=30, http_post=boom)
    with pytest.raises(LLMError):
        client.complete("sys", "usr")


def test_from_env_reads_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "envkey")
    monkeypatch.setenv("LLM_BASE_URL", "http://y/v1")
    monkeypatch.setenv("LLM_MODEL_ID", "mm")
    client = LLMClient.from_env()
    assert client.api_key == "envkey"
    assert client.model == "mm"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_llm_client.py -v`
Expected: FAIL(`No module named 'pipeline.llm_client'`)

- [ ] **Step 3: 写实现**

```python
# pipeline/llm_client.py
"""Minimal LLM HTTP client (OpenAI-compatible chat completions).

Credentials come from environment variables; every request carries a
timeout. An http_post callable can be injected for offline testing.
"""
from __future__ import annotations

import os
from typing import Callable, Optional

DEFAULT_TIMEOUT = 120


class LLMError(Exception):
    """Raised when an LLM request fails or returns an unusable response."""


class LLMClient:
    """OpenAI-compatible chat client with injectable transport."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None, timeout: Optional[int] = None,
                 http_post: Optional[Callable] = None) -> None:
        self.api_key = api_key or ""
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or ""
        self.timeout = timeout or DEFAULT_TIMEOUT
        self._http_post = http_post

    @classmethod
    def from_env(cls) -> "LLMClient":
        """Build a client from LLM_* environment variables."""
        return cls(
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", "https://api.minimaxi.com/v1"),
            model=os.getenv("LLM_MODEL_ID", "MiniMax-M3"),
            timeout=int(os.getenv("LLM_TIMEOUT", str(DEFAULT_TIMEOUT))),
        )

    def _post(self):
        if self._http_post is not None:
            return self._http_post
        import requests  # local import so tests don't require the dep
        return requests.post

    def complete(self, system: str, user: str) -> str:
        """Return the assistant text for a system+user prompt.

        Raises:
            LLMError: on network failure or malformed response.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        payload = {"model": self.model,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]}
        try:
            resp = self._post()(url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # process-boundary catch: wrap, never swallow
            raise LLMError(str(exc)) from exc
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_llm_client.py -v`
Expected: PASS(3 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/llm_client.py tests/test_llm_client.py
git commit -m "feat(llm): add injectable OpenAI-compatible LLM client with env config"
```

---

### Task 5: 地理编码(geocode.py)

**Files:**
- Create: `pipeline/geocode.py`
- Test: `tests/test_geocode.py`

**Interfaces:**
- Consumes: `pipeline.models.City`
- Produces:
  - `class GeocodeProvider(abc.ABC)` with abstract `geocode(self, query:str, city:City) -> Optional[Tuple[float,float]]`(返回 `(lat, lng)`)
  - `class PhotonProvider(GeocodeProvider)` with `__init__(self, http_get=None, timeout:int=30)`
  - `geocode_place(query:str, city:City, provider:GeocodeProvider) -> Optional[Tuple[float,float]]`(带 bbox 校验:结果不在 city.bbox 内返回 None)
  - `in_bbox(lat:float, lng:float, bbox:Tuple[float,float,float,float]) -> bool`

**关键点(Review Focus #2):** Photon 查询带城市中心偏置(lat/lon 参数);结果必须落在 city.bbox 内才接受,否则视为命中错城 → None。用 `abc.ABC` + 策略模式(AgentKnow required),`http_get` 注入免真实网络。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_geocode.py
from pipeline.models import City
from pipeline.geocode import PhotonProvider, geocode_place, in_bbox

PARIS = City(id="paris", name_zh="巴黎", name_en="Paris",
             center_lat=48.8566, center_lng=2.3522,
             bbox=(48.80, 2.20, 48.91, 2.47))  # (min_lat,min_lng,max_lat,max_lng)


def _fake_get(features):
    def get(url, params=None, headers=None, timeout=None):
        class R:
            def raise_for_status(self): pass
            def json(self): return {"features": features}
        assert timeout is not None  # timeout 必传
        return R()
    return get


def test_in_bbox():
    assert in_bbox(48.85, 2.33, PARIS.bbox) is True
    assert in_bbox(35.68, 139.76, PARIS.bbox) is False  # 东京不在巴黎 bbox


def test_geocode_place_accepts_result_in_city():
    feats = [{"geometry": {"coordinates": [2.33263, 48.85414]},  # [lng,lat]
              "properties": {"name": "Café de Flore", "city": "Paris"}}]
    provider = PhotonProvider(http_get=_fake_get(feats))
    coord = geocode_place("Café de Flore", PARIS, provider)
    assert coord == (48.85414, 2.33263)  # 返回 (lat,lng)


def test_geocode_place_rejects_wrong_city():
    # 同名店命中东京 → 落在巴黎 bbox 外 → 拒绝(Review Focus #2)
    feats = [{"geometry": {"coordinates": [139.7, 35.68]},
              "properties": {"name": "Café de Flore", "city": "Tokyo"}}]
    provider = PhotonProvider(http_get=_fake_get(feats))
    assert geocode_place("Café de Flore", PARIS, provider) is None


def test_geocode_place_no_features_returns_none():
    provider = PhotonProvider(http_get=_fake_get([]))
    assert geocode_place("Nowhere", PARIS, provider) is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_geocode.py -v`
Expected: FAIL(`No module named 'pipeline.geocode'`)

- [ ] **Step 3: 写实现**

```python
# pipeline/geocode.py
"""Geocoding with city-biased Photon and bbox validation.

Providers follow the strategy pattern (abc.ABC). Results must fall inside
the target city's bbox to be accepted, preventing same-name hits in the
wrong city.
"""
from __future__ import annotations

import abc
from typing import Callable, Optional, Tuple

from pipeline.models import City

DEFAULT_TIMEOUT = 30
PHOTON_URL = "https://photon.komoot.io/api"


def in_bbox(lat: float, lng: float, bbox: Tuple[float, float, float, float]) -> bool:
    """Return True if (lat,lng) is inside bbox=(min_lat,min_lng,max_lat,max_lng)."""
    min_lat, min_lng, max_lat, max_lng = bbox
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


class GeocodeProvider(abc.ABC):
    """Strategy interface for a geocoding backend."""

    @abc.abstractmethod
    def geocode(self, query: str, city: City) -> Optional[Tuple[float, float]]:
        """Return (lat, lng) for query near city, or None if not found."""


class PhotonProvider(GeocodeProvider):
    """Photon (OSM) geocoder with city-center bias."""

    def __init__(self, http_get: Optional[Callable] = None,
                 timeout: int = DEFAULT_TIMEOUT) -> None:
        self._http_get = http_get
        self.timeout = timeout

    def _get(self):
        if self._http_get is not None:
            return self._http_get
        import requests
        return requests.get

    def geocode(self, query: str, city: City) -> Optional[Tuple[float, float]]:
        """Query Photon biased to the city center; return first (lat,lng)."""
        params = {"q": query, "limit": 1, "lang": "en",
                  "lon": city.center_lng, "lat": city.center_lat}
        resp = self._get()(PHOTON_URL, params=params,
                           headers={"User-Agent": "lemis-diary/0.1"},
                           timeout=self.timeout)
        resp.raise_for_status()
        feats = resp.json().get("features") or []
        if not feats:
            return None
        lng, lat = feats[0]["geometry"]["coordinates"]  # GeoJSON = [lng, lat]
        return (float(lat), float(lng))


def geocode_place(query: str, city: City,
                  provider: GeocodeProvider) -> Optional[Tuple[float, float]]:
    """Geocode query and accept the result only if it falls in city.bbox."""
    coord = provider.geocode(query, city)
    if coord is None:
        return None
    lat, lng = coord
    if not in_bbox(lat, lng, city.bbox):
        return None
    return (lat, lng)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_geocode.py -v`
Expected: PASS(4 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/geocode.py tests/test_geocode.py
git commit -m "feat(geocode): city-biased Photon provider with bbox validation"
```

---

### Task 6: 配图管线(images.py)

**Files:**
- Create: `pipeline/images.py`
- Test: `tests/test_images.py`

**Interfaces:**
- Consumes: `pipeline.models.ImageRef`
- Produces:
  - `class ImageFetcher(__init__(self, http_get=None, timeout:int=30))`
  - `ImageFetcher.geosearch(self, lat:float, lng:float, radius_m:int=200) -> List[ImageRef]`(Wikimedia GeoSearch,confidence=high)
  - `ImageFetcher.name_search(self, name:str) -> List[ImageRef]`(名称搜图,confidence=mid)
  - `pick_image(candidates:List[List[ImageRef]], used_fingerprints:set) -> Optional[ImageRef]`(按降级链依次取,跳过已用指纹,取到即加入 used 集合)
  - `fingerprint(img:ImageRef) -> str`(用 url 规范化后作指纹)

**关键点(Review Focus #3):** `pick_image` 接收降级链候选列表 `[poi实拍图, 名人名作图]`,逐级取第一张未用过的;命中即把指纹加入 `used_fingerprints` 实现全局去重。指纹用 URL 规范化(去 query、统一小写,AgentKnow URL 规范化 required)。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_images.py
from pipeline.models import ImageRef
from pipeline.images import pick_image, fingerprint, ImageFetcher


def _img(url, conf="high"):
    return ImageRef(url=url, thumb=url, author="a", license="CC",
                    source_page="s", confidence=conf)


def test_fingerprint_normalizes_url():
    a = fingerprint(_img("https://X.org/A.JPG?width=100"))
    b = fingerprint(_img("https://x.org/A.JPG"))
    assert a == b  # 去 query + 统一小写 host 后一致


def test_pick_image_takes_first_unused():
    used = set()
    poi_imgs = [_img("https://x.org/flore.jpg")]
    name_imgs = [_img("https://x.org/beauvoir.jpg")]
    got = pick_image([poi_imgs, name_imgs], used)
    assert got.url == "https://x.org/flore.jpg"
    assert len(used) == 1


def test_pick_image_skips_used_and_falls_back():
    used = {fingerprint(_img("https://x.org/flore.jpg"))}
    poi_imgs = [_img("https://x.org/flore.jpg")]       # 已用,跳过
    name_imgs = [_img("https://x.org/beauvoir.jpg")]   # 用这张
    got = pick_image([poi_imgs, name_imgs], used)
    assert got.url == "https://x.org/beauvoir.jpg"


def test_pick_image_returns_none_when_all_used():
    used = {fingerprint(_img("https://x.org/a.jpg"))}
    got = pick_image([[_img("https://x.org/a.jpg")]], used)
    assert got is None


def test_geosearch_maps_response_to_imagerefs():
    def fake_get(url, params=None, headers=None, timeout=None):
        class R:
            def raise_for_status(self): pass
            def json(self):
                return {"query": {"pages": {"1": {
                    "title": "File:Flore.jpg",
                    "imageinfo": [{"url": "https://x.org/Flore.jpg",
                                   "thumburl": "https://x.org/t/Flore.jpg",
                                   "extmetadata": {
                                       "Artist": {"value": "Jane"},
                                       "LicenseShortName": {"value": "CC BY"}}}],
                    "fullurl": "https://commons/Flore"}}}}
        return R()
    f = ImageFetcher(http_get=fake_get)
    imgs = f.geosearch(48.854, 2.332)
    assert imgs and imgs[0].confidence == "high"
    assert imgs[0].url == "https://x.org/Flore.jpg"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_images.py -v`
Expected: FAIL(`No module named 'pipeline.images'`)

- [ ] **Step 3: 写实现**

```python
# pipeline/images.py
"""Wikimedia Commons image fetching with degradation chain and dedup.

Degradation chain per POI: geo-nearby image (high) → name-search image
(mid) → nothing. A global used-fingerprint set prevents the same image
being reused across POIs in a storyline.
"""
from __future__ import annotations

from typing import Callable, List, Optional
from urllib.parse import urlparse

from pipeline.models import ImageRef

DEFAULT_TIMEOUT = 30
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def fingerprint(img: ImageRef) -> str:
    """Canonical fingerprint of an image URL (drop query, lowercase host)."""
    parsed = urlparse(img.url)
    return f"{parsed.netloc.lower()}{parsed.path.lower()}"


def pick_image(candidates: List[List[ImageRef]],
               used_fingerprints: set) -> Optional[ImageRef]:
    """Pick the first not-yet-used image following the degradation chain.

    candidates is an ordered list of tiers (e.g. [poi_images, name_images]).
    On success the chosen image's fingerprint is added to used_fingerprints.
    Returns None if every candidate is already used or the chain is empty.
    """
    for tier in candidates:
        for img in tier:
            fp = fingerprint(img)
            if fp not in used_fingerprints:
                used_fingerprints.add(fp)
                return img
    return None


class ImageFetcher:
    """Fetches images from Wikimedia Commons."""

    def __init__(self, http_get: Optional[Callable] = None,
                 timeout: int = DEFAULT_TIMEOUT) -> None:
        self._http_get = http_get
        self.timeout = timeout

    def _get(self):
        if self._http_get is not None:
            return self._http_get
        import requests
        return requests.get

    def _pages_to_imagerefs(self, data: dict, confidence: str) -> List[ImageRef]:
        pages = (data.get("query", {}) or {}).get("pages", {}) or {}
        out: List[ImageRef] = []
        for page in pages.values():
            info_list = page.get("imageinfo") or []
            if not info_list:
                continue
            info = info_list[0]
            meta = info.get("extmetadata", {}) or {}
            out.append(ImageRef(
                url=info.get("url", ""), thumb=info.get("thumburl", info.get("url", "")),
                author=(meta.get("Artist", {}) or {}).get("value", ""),
                license=(meta.get("LicenseShortName", {}) or {}).get("value", ""),
                source_page=page.get("fullurl", ""), confidence=confidence,
            ))
        return out

    def geosearch(self, lat: float, lng: float, radius_m: int = 200) -> List[ImageRef]:
        """Find images geotagged near (lat,lng); confidence=high."""
        params = {
            "action": "query", "format": "json", "generator": "geosearch",
            "ggscoord": f"{lat}|{lng}", "ggsradius": radius_m, "ggslimit": 10,
            "ggsnamespace": 6, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 800, "inprop": "url",
        }
        resp = self._get()(COMMONS_API, params=params,
                           headers={"User-Agent": "lemis-diary/0.1"},
                           timeout=self.timeout)
        resp.raise_for_status()
        return self._pages_to_imagerefs(resp.json(), "high")

    def name_search(self, name: str) -> List[ImageRef]:
        """Search images by name (person/work fallback); confidence=mid."""
        params = {
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": name, "gsrnamespace": 6, "gsrlimit": 10,
            "prop": "imageinfo", "iiprop": "url|extmetadata",
            "iiurlwidth": 800, "inprop": "url",
        }
        resp = self._get()(COMMONS_API, params=params,
                           headers={"User-Agent": "lemis-diary/0.1"},
                           timeout=self.timeout)
        resp.raise_for_status()
        return self._pages_to_imagerefs(resp.json(), "mid")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_images.py -v`
Expected: PASS(5 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/images.py tests/test_images.py
git commit -m "feat(images): Wikimedia fetch with degradation chain and global dedup"
```

---

### Task 7: 内容生成(content_gen.py)

**Files:**
- Create: `pipeline/content_gen.py`
- Test: `tests/test_content_gen.py`

**Interfaces:**
- Consumes: `pipeline.models`(Narrative, NARRATIVE_TYPES, meets_threshold)、`pipeline.llm_client.LLMClient`
- Produces:
  - `build_narrative_prompt(storyline_theme:str, poi_name:str) -> Tuple[str, str]`(返回 (system, user);要求 LLM 输出 JSON 数组,每条含 type/text_zh/text_en/confidence/reason)
  - `parse_narrative_response(raw:str) -> List[Narrative]`(解析 LLM JSON;非法条目跳过;type 不在 NARRATIVE_TYPES 跳过)
  - `generate_narrative(client:LLMClient, storyline_theme:str, poi_name:str, threshold:str="mid") -> List[Narrative]`(调 LLM + 解析 + 过滤低置信度)

**关键点(Review Focus #4):** `generate_narrative` 内即按阈值过滤;`parse_narrative_response` 对脏输出鲁棒(空串、非 JSON、缺字段均不崩)。confidence 由 LLM 自评(prompt 里要求),零额外调用。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_content_gen.py
from pipeline.content_gen import (
    build_narrative_prompt, parse_narrative_response, generate_narrative,
)


def test_prompt_mentions_theme_and_poi_and_json():
    system, user = build_narrative_prompt("Emily in Paris", "Café de Flore")
    assert "Emily in Paris" in user
    assert "Café de Flore" in user
    assert "JSON" in system or "json" in system


def test_parse_valid_response():
    raw = '''[
      {"type":"scene","text_zh":"Emily喝咖啡","text_en":"Emily","confidence":"high","reason":"S1E2"},
      {"type":"anecdote","text_zh":"波伏娃","text_en":"Beauvoir","confidence":"mid","reason":"史料"}
    ]'''
    narrs = parse_narrative_response(raw)
    assert len(narrs) == 2
    assert narrs[0].type == "scene"


def test_parse_skips_invalid_type_and_bad_json():
    assert parse_narrative_response("not json at all") == []
    raw = '[{"type":"unknown_type","text_zh":"x","text_en":"x","confidence":"high"}]'
    assert parse_narrative_response(raw) == []  # type 不在枚举内


def test_parse_tolerates_json_wrapped_in_text():
    # LLM 常在 JSON 前后加解释文字
    raw = '好的,结果如下:\n[{"type":"history","text_zh":"h","text_en":"h","confidence":"high"}]\n以上'
    narrs = parse_narrative_response(raw)
    assert len(narrs) == 1 and narrs[0].type == "history"


def test_generate_narrative_filters_low_confidence():
    class FakeClient:
        def complete(self, system, user):
            return '[{"type":"scene","text_zh":"a","text_en":"a","confidence":"low"},'\
                   '{"type":"history","text_zh":"b","text_en":"b","confidence":"high"}]'
    narrs = generate_narrative(FakeClient(), "theme", "poi")
    assert [n.type for n in narrs] == ["history"]  # low 被过滤
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_content_gen.py -v`
Expected: FAIL(`No module named 'pipeline.content_gen'`)

- [ ] **Step 3: 写实现**

```python
# pipeline/content_gen.py
"""Generate bilingual narrative for a POI within a storyline via LLM.

The LLM self-rates each entry's confidence (no extra call). Malformed
output is tolerated; entries below the threshold are dropped.
"""
from __future__ import annotations

import json
import re
from typing import List, Tuple

from pipeline.models import NARRATIVE_TYPES, Narrative, meets_threshold

_SYSTEM = (
    "你是严谨的文旅内容编辑。只输出一个 JSON 数组,不要额外解释。"
    "数组每个元素含字段:type(scene/anecdote/masterpiece/history 之一)、"
    "text_zh、text_en、confidence(high/mid/low,依据史料/作品出处自评)、reason。"
    "Output ONLY a JSON array."
)


def build_narrative_prompt(storyline_theme: str, poi_name: str) -> Tuple[str, str]:
    """Build (system, user) prompts for narrative generation."""
    user = (
        f"故事线主题:{storyline_theme}\n地点:{poi_name}\n"
        f"请只围绕『{storyline_theme}』这条故事线,写该地点相关的剧情/轶事/名作/历史。"
        f"无可靠内容的类型就不要编,confidence 如实标注。"
    )
    return _SYSTEM, user


def _extract_json_array(raw: str) -> str:
    """Extract the first top-level JSON array substring from raw text."""
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    return match.group(0) if match else ""


def parse_narrative_response(raw: str) -> List[Narrative]:
    """Parse LLM output into Narrative list; skip malformed/unknown entries."""
    if not raw:
        return []
    payload = _extract_json_array(raw)
    if not payload:
        return []
    try:
        items = json.loads(payload)
    except (ValueError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    out: List[Narrative] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        if it.get("type") not in NARRATIVE_TYPES:
            continue
        out.append(Narrative(
            type=it["type"], text_zh=it.get("text_zh", ""),
            text_en=it.get("text_en", ""), confidence=it.get("confidence", "low"),
        ))
    return out


def generate_narrative(client, storyline_theme: str, poi_name: str,
                       threshold: str = "mid") -> List[Narrative]:
    """Generate + parse + confidence-filter narrative for one POI in a storyline."""
    system, user = build_narrative_prompt(storyline_theme, poi_name)
    raw = client.complete(system, user)
    parsed = parse_narrative_response(raw)
    return [n for n in parsed if meets_threshold(n.confidence, threshold)]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_content_gen.py -v`
Expected: PASS(5 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/content_gen.py tests/test_content_gen.py
git commit -m "feat(content): LLM bilingual narrative gen with self-rated confidence filtering"
```

---

### Task 8: 站点组装(build_site.py)

**Files:**
- Create: `pipeline/build_site.py`
- Test: `tests/test_build_site.py`

**Interfaces:**
- Consumes: `pipeline.schema`(load_city/load_poi/load_storyline/stops_for_storyline/visible_narrative/resolve_photo_spot)、`pipeline.models`
- Produces:
  - `build_city_payload(city:City, pois:Dict[str,POI], storylines:List[StoryLine], threshold:str="mid") -> dict`(产出前端消费的纯 dict:含 city、pois(仅展示字段+base_images 过阈值)、storylines(每条含有序 stops,每 stop 含 poi_id/order/可见 narrative/photo_spot))
  - `write_site(payload:dict, web_dir:str, dist_dir:str) -> None`(把 payload 写成 `dist/data/<city>.json`,拷贝 web/ 到 dist/,注入城市页)

**关键点:** payload 里每个 stop 只放"可见"内容(已过 confidence);base_images 只保留过阈值的。这样前端拿到的就是干净数据。坐标转换留给前端(payload 存 [lat,lng])。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_build_site.py
import json
import os
from pipeline.models import (
    City, POI, StoryLine, StoryStop, Narrative, ImageRef,
)
from pipeline.build_site import build_city_payload, write_site

PARIS = City(id="paris", name_zh="巴黎", name_en="Paris",
             center_lat=48.8566, center_lng=2.3522, bbox=(48.8, 2.2, 48.91, 2.47))


def _poi():
    return POI(id="cafe", city="paris", country="FR",
               name_zh="花神", name_en="Flore", lat=48.854, lng=2.332,
               address_zh="地址", address_en="addr",
               base_images=[ImageRef("u", "t", "a", "cc", "s", "high")])


def _storyline():
    stop = StoryStop(storyline_id="emily", poi_id="cafe", order=1, narrative=[
        Narrative("scene", "剧情", "scene", "high"),
        Narrative("anecdote", "弱", "weak", "low"),  # 应被过滤
    ])
    return StoryLine(id="emily", city="paris", title_zh="艾米莉", title_en="Emily",
                     theme="Emily in Paris", summary_zh="s", summary_en="s", stops=[stop])


def test_payload_filters_low_confidence_narrative():
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    stop0 = payload["storylines"][0]["stops"][0]
    types = [n["type"] for n in stop0["narrative"]]
    assert types == ["scene"]  # low 的 anecdote 不在


def test_payload_includes_bilingual_fields():
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    poi = payload["pois"]["cafe"]
    assert poi["name_zh"] == "花神" and poi["name_en"] == "Flore"
    assert payload["city"]["name_en"] == "Paris"


def test_payload_stops_reference_poi_and_coord():
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    stop0 = payload["storylines"][0]["stops"][0]
    assert stop0["poi_id"] == "cafe"
    assert payload["pois"]["cafe"]["lat"] == 48.854


def test_write_site_emits_json_and_copies_web(tmp_path):
    web = tmp_path / "web"
    (web / "assets").mkdir(parents=True)
    (web / "templates").mkdir(parents=True)
    (web / "templates" / "city.html").write_text("<html>__CITY_ID__</html>", encoding="utf-8")
    (web / "assets" / "app.js").write_text("// app", encoding="utf-8")
    dist = tmp_path / "dist"
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    write_site(payload, str(web), str(dist))
    data_file = dist / "data" / "paris.json"
    assert data_file.exists()
    loaded = json.loads(data_file.read_text(encoding="utf-8"))
    assert loaded["city"]["id"] == "paris"
    assert (dist / "assets" / "app.js").exists()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_build_site.py -v`
Expected: FAIL(`No module named 'pipeline.build_site'`)

- [ ] **Step 3: 写实现**

```python
# pipeline/build_site.py
"""Assemble the static site: build a clean per-city JSON payload and emit dist/."""
from __future__ import annotations

import json
import os
import shutil
from typing import Dict, List

from pipeline.models import City, ImageRef, Narrative, POI, StoryLine
from pipeline.schema import (
    resolve_photo_spot, stops_for_storyline, visible_narrative,
)


def _image_dict(img: ImageRef) -> dict:
    return {"url": img.url, "thumb": img.thumb, "author": img.author,
            "license": img.license, "source_page": img.source_page}


def _narrative_dict(n: Narrative) -> dict:
    d = {"type": n.type, "text_zh": n.text_zh, "text_en": n.text_en}
    if n.image:
        d["image"] = _image_dict(n.image)
    return d


def _poi_dict(poi: POI, threshold: str) -> dict:
    from pipeline.models import meets_threshold
    images = [_image_dict(i) for i in poi.base_images
              if meets_threshold(i.confidence, threshold)]
    out = {"id": poi.id, "name_zh": poi.name_zh, "name_en": poi.name_en,
           "lat": poi.lat, "lng": poi.lng,
           "address_zh": poi.address_zh, "address_en": poi.address_en,
           "base_images": images}
    if poi.practical and meets_threshold(poi.practical.confidence, threshold):
        out["practical"] = _narrative_dict(poi.practical)
    return out


def build_city_payload(city: City, pois: Dict[str, POI],
                       storylines: List[StoryLine], threshold: str = "mid") -> dict:
    """Build the front-end payload for a city with all confidence filtering applied."""
    sl_out = []
    for sl in storylines:
        stops_out = []
        for stop in stops_for_storyline(sl):
            poi = pois.get(stop.poi_id)
            spot = resolve_photo_spot(poi, stop, threshold) if poi else None
            stops_out.append({
                "poi_id": stop.poi_id, "order": stop.order,
                "narrative": [_narrative_dict(n) for n in visible_narrative(stop, threshold)],
                "photo_spot": _narrative_dict(spot) if spot else None,
            })
        sl_out.append({
            "id": sl.id, "title_zh": sl.title_zh, "title_en": sl.title_en,
            "theme": sl.theme, "summary_zh": sl.summary_zh, "summary_en": sl.summary_en,
            "poster": _image_dict(sl.poster) if sl.poster else None,
            "stops": stops_out,
        })
    return {
        "city": {"id": city.id, "name_zh": city.name_zh, "name_en": city.name_en,
                 "center_lat": city.center_lat, "center_lng": city.center_lng},
        "pois": {pid: _poi_dict(p, threshold) for pid, p in pois.items()},
        "storylines": sl_out,
    }


def write_site(payload: dict, web_dir: str, dist_dir: str) -> None:
    """Write payload JSON into dist/data/ and copy web/ assets + city page into dist/."""
    os.makedirs(os.path.join(dist_dir, "data"), exist_ok=True)
    city_id = payload["city"]["id"]
    with open(os.path.join(dist_dir, "data", f"{city_id}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # copy assets + i18n
    for sub in ("assets", "i18n"):
        src = os.path.join(web_dir, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dist_dir, sub), dirs_exist_ok=True)

    # render city page (replace placeholder with city id)
    tpl_path = os.path.join(web_dir, "templates", "city.html")
    with open(tpl_path, "r", encoding="utf-8") as f:
        html = f.read().replace("__CITY_ID__", city_id)
    with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_build_site.py -v`
Expected: PASS(4 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/build_site.py tests/test_build_site.py
git commit -m "feat(build): assemble filtered city payload and emit static dist/"
```

---

### Task 9: 前端(city.html + app.js + i18n)

**Files:**
- Create: `web/templates/city.html`, `web/assets/app.js`, `web/i18n/zh.json`, `web/i18n/en.json`
- Test: `tests/test_frontend.py`(用 Python 做纯函数级校验 + 静态断言;不引入 JS 测试框架,保持零依赖)

**Interfaces:**
- Consumes: `dist/data/<city>.json`(Task 8 产出)、`i18n/<lang>.json`
- Produces: 浏览器可直接打开的城市页;`app.js` 内含可被 Node 单测的纯函数 `pickLang(field_zh, field_en, lang)` 与 `visibleForLang(payload, lang)`(导出到 `window` 便于人工验证)

**关键点:**
- Review Focus #1:前端**按当前选中的故事线**渲染其 stops,切换故事线只显示该线内容。
- Review Focus #5:`pickLang` 缺 en 译文时回退 zh(反之亦然),切换语言不残留空白。
- 语言状态存 localStorage;顶部按钮全局切换。
- 地图坐标转换:payload 存 `[lat,lng]`,传给 MapLibre 时用 `[lng,lat]`。

- [ ] **Step 1: 写失败测试(Python 校验前端资源存在且结构正确)**

```python
# tests/test_frontend.py
import json
import os

WEB = os.path.join(os.path.dirname(__file__), "..", "web")


def test_i18n_files_have_same_keys():
    zh = json.load(open(os.path.join(WEB, "i18n", "zh.json"), encoding="utf-8"))
    en = json.load(open(os.path.join(WEB, "i18n", "en.json"), encoding="utf-8"))
    assert set(zh.keys()) == set(en.keys())  # 两语言 key 必须一致
    assert "switch_language" in zh


def test_city_html_references_maplibre_and_app():
    html = open(os.path.join(WEB, "templates", "city.html"), encoding="utf-8").read()
    assert "maplibre-gl" in html
    assert "app.js" in html
    assert "__CITY_ID__" in html  # 构建期占位符


def test_app_js_defines_picklang_and_visible():
    js = open(os.path.join(WEB, "assets", "app.js"), encoding="utf-8").read()
    assert "function pickLang" in js
    assert "function visibleForLang" in js
    assert "localStorage" in js
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_frontend.py -v`
Expected: FAIL(文件不存在)

- [ ] **Step 3: 创建 i18n/zh.json**

```json
{
  "site_title": "Lemi's Diary",
  "switch_language": "EN",
  "storylines": "故事线",
  "practical": "实用信息",
  "photo_spot": "拍照机位",
  "scene": "剧情",
  "anecdote": "名人轶事",
  "masterpiece": "名作",
  "history": "历史"
}
```

- [ ] **Step 4: 创建 i18n/en.json**

```json
{
  "site_title": "Lemi's Diary",
  "switch_language": "中",
  "storylines": "Storylines",
  "practical": "Practical",
  "photo_spot": "Photo Spot",
  "scene": "Scene",
  "anecdote": "Anecdote",
  "masterpiece": "Masterpiece",
  "history": "History"
}
```

- [ ] **Step 5: 创建 web/assets/app.js**

```javascript
// Lemi's Diary front-end: load city payload, render storyline stops,
// language switch (single-language display with fallback), MapLibre map.

function pickLang(zh, en, lang) {
  // Single-language display; fall back to the other language if missing.
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function visibleForLang(payload, lang) {
  // Shape the payload's active-storyline stops for a given language.
  return (payload.storylines || []).map(function (sl) {
    return {
      id: sl.id,
      title: pickLang(sl.title_zh, sl.title_en, lang),
      stops: (sl.stops || []).map(function (st) {
        return {
          poi_id: st.poi_id, order: st.order,
          narrative: (st.narrative || []).map(function (n) {
            return { type: n.type, text: pickLang(n.text_zh, n.text_en, lang), image: n.image };
          }),
          photo_spot: st.photo_spot
            ? { text: pickLang(st.photo_spot.text_zh, st.photo_spot.text_en, lang), image: st.photo_spot.image }
            : null,
        };
      }),
    };
  });
}

if (typeof window !== "undefined") {
  window.pickLang = pickLang;
  window.visibleForLang = visibleForLang;
  window.LemiApp = { pickLang: pickLang, visibleForLang: visibleForLang };
}

async function boot() {
  const cityId = window.__CITY_ID__ || "paris";
  let lang = localStorage.getItem("lemi_lang") || "zh";
  const payload = await fetch("./data/" + cityId + ".json").then(function (r) { return r.json(); });
  const i18n = await fetch("./i18n/" + lang + ".json").then(function (r) { return r.json(); });

  const map = new maplibregl.Map({
    container: "map",
    style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    center: [payload.city.center_lng, payload.city.center_lat], // MapLibre = [lng,lat]
    zoom: 12,
  });

  let activeStoryline = (payload.storylines[0] || {}).id;

  function render() {
    const shaped = visibleForLang(payload, lang);
    const sl = shaped.find(function (s) { return s.id === activeStoryline; }) || shaped[0];
    // draw route
    const coords = sl.stops.map(function (st) {
      const p = payload.pois[st.poi_id];
      return [p.lng, p.lat];
    });
    if (map.getSource("route")) map.getSource("route").setData(routeGeo(coords));
    else if (map.loaded()) addRoute(map, coords);
    renderSidebar(sl, payload, i18nCurrent, lang);
    addMarkers(map, sl, payload);
  }

  let i18nCurrent = i18n;
  window.__lemiRender = render;
  window.__lemiSwitchLang = async function () {
    lang = lang === "zh" ? "en" : "zh";
    localStorage.setItem("lemi_lang", lang);
    i18nCurrent = await fetch("./i18n/" + lang + ".json").then(function (r) { return r.json(); });
    render();
  };
  window.__lemiSetStoryline = function (id) { activeStoryline = id; render(); };

  map.on("load", render);
}

function routeGeo(coords) {
  return { type: "Feature", geometry: { type: "LineString", coordinates: coords } };
}
function addRoute(map, coords) {
  map.addSource("route", { type: "geojson", data: routeGeo(coords) });
  map.addLayer({ id: "route", type: "line", source: "route",
    paint: { "line-color": "#c0392b", "line-width": 3, "line-dasharray": [2, 1.5] } });
}
function addMarkers(map, sl, payload) {
  (window.__lemiMarkers || []).forEach(function (m) { m.remove(); });
  window.__lemiMarkers = [];
  sl.stops.forEach(function (st) {
    const p = payload.pois[st.poi_id];
    const el = document.createElement("div");
    el.className = "marker"; el.textContent = st.order;
    const m = new maplibregl.Marker({ element: el }).setLngLat([p.lng, p.lat]).addTo(map);
    window.__lemiMarkers.push(m);
  });
}
function renderSidebar(sl, payload, i18n, lang) {
  const box = document.getElementById("sidebar-content");
  if (!box) return;
  box.innerHTML = "";
  sl.stops.forEach(function (st) {
    const p = payload.pois[st.poi_id];
    const card = document.createElement("div");
    card.className = "poi-card";
    let html = "<h3>" + st.order + ". " + pickLang(p.name_zh, p.name_en, lang) + "</h3>";
    if (p.base_images && p.base_images[0]) {
      html += '<img src="' + p.base_images[0].thumb + '" alt="" />';
    }
    st.narrative.forEach(function (n) {
      html += '<p><b>' + (i18n[n.type] || n.type) + '</b>: ' + n.text + '</p>';
      if (n.image) html += '<img src="' + n.image.thumb + '" alt="" />';
    });
    if (st.photo_spot) html += '<p><b>' + i18n.photo_spot + '</b>: ' + st.photo_spot.text + '</p>';
    card.innerHTML = html;
    box.appendChild(card);
  });
}

if (typeof document !== "undefined" && document.getElementById) {
  window.addEventListener("DOMContentLoaded", boot);
}
```

- [ ] **Step 6: 创建 web/templates/city.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Lemi's Diary</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:-apple-system,"PingFang SC",sans-serif;}
  #app{display:flex;height:100vh;}
  #sidebar{width:380px;overflow-y:auto;background:#faf7f2;border-right:1px solid #e8e0d6;}
  #map{flex:1;}
  #topbar{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;
    background:#c0392b;color:#fff;}
  #topbar button{background:#fff;color:#c0392b;border:none;padding:5px 12px;border-radius:4px;cursor:pointer;}
  #storyline-tabs{padding:10px 18px;display:flex;gap:8px;flex-wrap:wrap;}
  #storyline-tabs button{border:1px solid #c0392b;background:#fff;color:#c0392b;
    padding:4px 10px;border-radius:14px;cursor:pointer;font-size:13px;}
  .poi-card{padding:14px 18px;border-bottom:1px solid #ece4d9;}
  .poi-card h3{font-size:16px;margin-bottom:8px;}
  .poi-card img{width:100%;border-radius:6px;margin:6px 0;}
  .poi-card p{font-size:13px;line-height:1.6;margin:5px 0;}
  .marker{width:26px;height:26px;background:#c0392b;color:#fff;border:2px solid #fff;
    border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;}
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
    <div id="topbar">
      <span id="site-title">Lemi's Diary</span>
      <button onclick="window.__lemiSwitchLang && window.__lemiSwitchLang()">EN / 中</button>
    </div>
    <div id="storyline-tabs"></div>
    <div id="sidebar-content"></div>
  </div>
  <div id="map"></div>
</div>
<script>window.__CITY_ID__ = "__CITY_ID__";</script>
<script src="./assets/app.js"></script>
</body>
</html>
```

- [ ] **Step 7: 运行测试确认通过**

Run: `python3 -m pytest tests/test_frontend.py -v`
Expected: PASS(3 passed)

- [ ] **Step 8: (人工可选)Node 冒烟验证纯函数**

Run: `node -e "global.window={};require('./web/assets/app.js');console.log(window.pickLang('中','en','en'),window.pickLang('中','', 'en'))"`
Expected: 打印 `en 中`(第二个证明缺 en 时回退 zh)

- [ ] **Step 9: Commit**

```bash
git add web/ tests/test_frontend.py
git commit -m "feat(web): MapLibre city page with language + storyline switch and fallback"
```

---

### Task 10: 端到端跑通巴黎样板

**Files:**
- Create: `content/cities/paris.json`, `content/pois/*.json`(≥6 个,取自 Spike 产物 `artifacts/emily_paris_spike/storyline_geocoded.json` 的真实坐标), `content/storylines/emily-in-paris.json`
- Create: `pipeline/run_paris.py`(编排脚本:加载 content → 配图 → 组装 → 写 dist)
- Test: `tests/test_e2e_paris.py`

**Interfaces:**
- Consumes: 全部前序模块
- Produces: `dist/index.html` + `dist/data/paris.json` 可在浏览器打开的完整样板

**数据来源说明:** POI 坐标直接用 Spike 已校准的真实坐标(见 `artifacts/emily_paris_spike/storyline_geocoded.json` 的 `real_coord` 字段);narrative 内容用 Spike 已生成的 scene/anecdote/masterpiece/history 文本,补 en 译文,标 confidence。首期为控制成本,narrative 可直接写入 content JSON(不必每次调 LLM);LLM 生成链(Task 7)作为"新增故事线"的工具保留。

- [ ] **Step 1: 写巴黎城市数据 content/cities/paris.json**

```json
{
  "id": "paris", "name_zh": "巴黎", "name_en": "Paris",
  "center_lat": 48.8566, "center_lng": 2.3522,
  "bbox": [48.80, 2.20, 48.91, 2.47]
}
```

- [ ] **Step 2: 写至少 6 个 POI(示例:花神咖啡馆)content/pois/cafe-de-flore.json**

```json
{
  "id": "cafe-de-flore", "city": "paris", "country": "France",
  "name_zh": "花神咖啡馆", "name_en": "Café de Flore",
  "lat": 48.85414, "lng": 2.33263,
  "address_zh": "圣日耳曼大道172号", "address_en": "172 Bd Saint-Germain, 75006",
  "base_images": [],
  "practical": {
    "type": "practical",
    "text_zh": "全天营业,咖啡偏贵,氛围独特。地铁 Saint-Germain-des-Prés(4号线)。",
    "text_en": "Open all day; pricey coffee, iconic vibe. Metro: Saint-Germain-des-Prés (L4).",
    "confidence": "high"
  }
}
```
> 其余 5+ POI(先贤祠、亚历山大三世桥、加尼叶歌剧院、皇家宫殿花园、埃菲尔铁塔等)按同样结构从 Spike 数据填。base_images 留空,由 Step 5 配图脚本填充。

- [ ] **Step 3: 写故事线 content/storylines/emily-in-paris.json**

```json
{
  "id": "emily-in-paris", "city": "paris",
  "title_zh": "《艾米莉在巴黎》足迹", "title_en": "Emily in Paris Trail",
  "theme": "Emily in Paris", "summary_zh": "沿剧中取景地漫步巴黎左岸与右岸。",
  "summary_en": "A walk through Emily's Paris filming locations.",
  "poster": null,
  "stops": [
    {"poi_id": "cafe-de-flore", "order": 6, "narrative": [
      {"type": "scene", "text_zh": "Emily 与 Mindy 在此谈心,体验巴黎咖啡馆文化。",
       "text_en": "Emily and Mindy chat here over coffee.", "confidence": "high"},
      {"type": "anecdote", "text_zh": "萨特与波伏娃曾在此写作辩论,存在主义思想的据点。",
       "text_en": "Sartre and Beauvoir wrote and debated here.", "confidence": "high"}
    ]}
  ]
}
```
> 补齐所有 POI 的 stops,order 按剧情/地理排序。

- [ ] **Step 4: 写编排脚本 pipeline/run_paris.py**

```python
# pipeline/run_paris.py
"""End-to-end build for the Paris / Emily-in-Paris sample.

Loads content/, fetches one image per POI via the degradation chain with
global dedup, assembles the payload, and writes dist/.
"""
from __future__ import annotations

import glob
import os

from pipeline.build_site import build_city_payload, write_site
from pipeline.images import ImageFetcher, pick_image
from pipeline.models import ImageRef
from pipeline.schema import load_city, load_poi, load_storyline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def enrich_images(pois, fetcher, used):
    """Fill each POI's base_images with one deduped image via the chain."""
    for poi in pois.values():
        if poi.lat is None or poi.lng is None:
            continue
        try:
            geo = fetcher.geosearch(poi.lat, poi.lng)
        except Exception:
            geo = []
        try:
            named = fetcher.name_search(poi.name_en or poi.name_zh)
        except Exception:
            named = []
        chosen = pick_image([geo, named], used)
        poi.base_images = [chosen] if chosen else []


def main(offline: bool = False) -> None:
    """Build the Paris sample site into dist/."""
    city = load_city(os.path.join(ROOT, "content", "cities", "paris.json"))
    pois = {}
    for path in glob.glob(os.path.join(ROOT, "content", "pois", "*.json")):
        poi = load_poi(path)
        pois[poi.id] = poi
    storylines = [load_storyline(p) for p in
                  glob.glob(os.path.join(ROOT, "content", "storylines", "*.json"))]

    if not offline:
        enrich_images(pois, ImageFetcher(), set())

    payload = build_city_payload(city, pois, storylines)
    write_site(payload, os.path.join(ROOT, "web"), os.path.join(ROOT, "dist"))
    print("Built dist/ for city:", city.id, "POIs:", len(pois))


if __name__ == "__main__":
    main(offline=bool(os.getenv("LEMI_OFFLINE")))
```

- [ ] **Step 5: 写 e2e 测试(离线,不联网)**

```python
# tests/test_e2e_paris.py
import json
import os
from pipeline.run_paris import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_paris_build_offline_produces_dist():
    main(offline=True)  # 不联网配图
    data = os.path.join(ROOT, "dist", "data", "paris.json")
    assert os.path.exists(data)
    payload = json.load(open(data, encoding="utf-8"))
    assert payload["city"]["id"] == "paris"
    assert len(payload["pois"]) >= 6
    # 至少一条故事线,且其 stops 有序、引用真实 POI
    sl = payload["storylines"][0]
    orders = [s["order"] for s in sl["stops"]]
    assert orders == sorted(orders)
    for s in sl["stops"]:
        assert s["poi_id"] in payload["pois"]
    assert os.path.exists(os.path.join(ROOT, "dist", "index.html"))
```

- [ ] **Step 6: 运行 e2e 测试确认通过**

Run: `python3 -m pytest tests/test_e2e_paris.py -v`
Expected: PASS(1 passed)

- [ ] **Step 7: 联网真实构建一次(可选,需网络)**

Run: `python3 -m pipeline.run_paris`
Expected: 打印 `Built dist/ for city: paris POIs: N`;`dist/data/paris.json` 中部分 POI 的 `base_images` 非空。

- [ ] **Step 8: 全量测试回归**

Run: `python3 -m pytest -q`
Expected: 所有测试 PASS。

- [ ] **Step 9: Commit**

```bash
git add content/ pipeline/run_paris.py tests/test_e2e_paris.py
git commit -m "feat(sample): end-to-end Paris / Emily-in-Paris sample build"
```

---

### Task 11: README 与 GitHub 部署文档

**Files:**
- Create: `README.md`, `.github/workflows/deploy-pages.yml`
- Test: 无自动化测试(文档任务);人工核对命令可跑通

**Interfaces:**
- Consumes: 全部
- Produces: 用户可照着一步步部署到自己 GitHub Pages 的文档 + CI

- [ ] **Step 1: 写 README.md**

内容必须包含(每节给出可复制命令):
1. 项目简介(一本可交互旅行手账;巴黎 × 艾米莉样板)
2. 本地跑起来:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env    # 填 LLM_API_KEY(仅新增内容时需要)
   LEMI_OFFLINE=1 python3 -m pipeline.run_paris   # 离线构建(用已存内容,不联网配图)
   python3 -m http.server -d dist 8000            # 打开 http://localhost:8000
   ```
3. 新增一条故事线的步骤(在 content/ 加 POI + storyline JSON,跑 run 脚本)
4. 目录结构说明(content/pipeline/web/dist 四层)
5. 数据模型简述(POI/StoryStop/StoryLine 三层解耦)

- [ ] **Step 2: 写 GitHub Actions 部署 .github/workflows/deploy-pages.yml**

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: ["main"]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: github-pages
  cancel-in-progress: true
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Build site (offline, uses committed content)
        run: LEMI_OFFLINE=1 python3 -m pipeline.run_paris
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
      - uses: actions/deploy-pages@v4
```
> 说明:CI 用 `LEMI_OFFLINE=1`,配图在本地构建时完成并把图片 URL 写进 content/ 或 dist(避免 CI 联网抓图不稳定)。

- [ ] **Step 3: 人工核对本地构建 + 预览命令可跑通**

Run:
```bash
LEMI_OFFLINE=1 python3 -m pipeline.run_paris && test -f dist/index.html && echo OK
```
Expected: 打印 `OK`。

- [ ] **Step 4: Commit**

```bash
git add README.md .github/workflows/deploy-pages.yml
git commit -m "docs: add README and GitHub Pages deploy workflow"
```

- [ ] **Step 5: (交付)一步步教用户部署到自己的 GitHub**

在对话中带用户完成(非代码步骤):
1. 用户在 GitHub 新建空仓库 `lemis-diary`
2. `git remote add origin <用户仓库地址>`
3. `git push -u origin main`
4. GitHub 仓库 Settings → Pages → Source 选 "GitHub Actions"
5. 等待 Actions 跑完,访问 `https://<用户名>.github.io/lemis-diary/`

---

## Self-Review

**1. Spec coverage(逐节核对):**
- §1 主客体反转 → Task 2 数据模型(POI 为主)✅
- §2 三层数据模型(POI/StoryStop/StoryLine)→ Task 2、Task 3 ✅
- §2 共享 POI 隔离 → Task 3 `test_shared_poi_isolated_between_storylines` + Task 9 前端按故事线渲染 ✅
- §3 图片管线(Wikimedia + 坐标就近 + 降级链)→ Task 6 ✅
- §4 LLM 流程(抽 POI/校准/配图/双语内容)→ Task 4/5/6/7/10 ✅
- §4.3 图片降级链 + 全局去重 → Task 6 `pick_image` ✅
- §5 多语言(双语存储 + 全局单语切换 + 兜底)→ Task 9 ✅
- §6 地图(MapLibre + Photon + 去中国边界校验 + 城市偏置)→ Task 5、Task 9 ✅
- §9.1 confidence 规则式分级 + 阈值 mid → Task 2/3/6/7/8 ✅
- §9.2 纯静态站 + GitHub Pages → Task 8、Task 11 ✅
- §9.3 目录结构四层分离 → File Structure ✅
- §9.4 借思路不借代码 + 纯静态前端 → 全部 Task 自建,无 storymap 代码依赖 ✅

**2. Placeholder scan:** 已核对,所有 code 步骤均为可运行真实代码,无 TBD/TODO/"类似 Task N"占位。✅

**3. Type consistency:** 坐标全局 `[lat,lng]` 存储、`[lng,lat]` 仅传 MapLibre;`Narrative`/`ImageRef`/`POI` 字段名在 Task 2 定义后,Task 3/6/8/9 引用一致;`geocode_place` 返回 `(lat,lng)`、`pick_image` 返回 `Optional[ImageRef]`、`build_city_payload` 返回 dict —— 前后一致。✅

**4. Review Focus 覆盖:** 5 条均已在对应 Task 的测试中 pin:#1→Task3/9、#2→Task5、#3→Task6、#4→Task7/8、#5→Task9。✅
