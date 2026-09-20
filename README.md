# Lemi's Diary

一本可交互的旅行手账 —— 把城市讲成一条条「故事线」，而不是一堆孤立的景点。

首个样板：**巴黎 × 《艾米莉在巴黎》**。沿着剧中取景地漫步左岸与右岸，每个地点都带有场景、轶事、名作、历史四类叙事，中英双语，配 Wikimedia 授权图片，落在一张 MapLibre 交互地图上。

站点是**纯静态**的：一条内容管线把 `content/` 里的 JSON 编译成 `dist/` 下的静态页面，可直接托管到 GitHub Pages，无需任何后端。

## 本地跑起来

```bash
pip install -r requirements.txt
cp .env.example .env    # 填 LLM_API_KEY(仅新增内容时需要)
LEMI_OFFLINE=1 python3 -m pipeline.run_paris   # 离线构建(用已存内容,不联网配图)
python3 -m http.server -d dist 8000            # 打开 http://localhost:8000
```

说明：

- `LEMI_OFFLINE=1` 走离线构建，直接用 `content/` 里已存的内容与图片 URL，不联网抓图，稳定可复现。
- 去掉 `LEMI_OFFLINE`（`python3 -m pipeline.run_paris`）会联网走图片管线（Wikimedia 坐标就近 + 名称搜索 + 降级链 + 全局去重）为每个 POI 补一张图，需要网络。
- 只有在**新增/生成内容**（调用 LLM 抽取 POI、生成双语叙事）时才需要 `.env` 里的 `LLM_API_KEY`；纯离线构建不需要。

## 新增一条故事线

内容全部是 `content/` 下的 JSON，加一条故事线只需三步：

1. **加 POI**：在 `content/pois/` 下为每个新地点建一个 JSON（客观信息：`id` / `city` / `country` / 中英名 / `lat` / `lng` / 中英地址 / `practical`）。若某个 POI 已存在（如埃菲尔铁塔），可直接被多条故事线复用，不必重复创建。

   ```json
   {
     "id": "cafe-de-flore", "city": "paris", "country": "France",
     "name_zh": "花神咖啡馆", "name_en": "Café de Flore",
     "lat": 48.8541444, "lng": 2.3326307,
     "address_zh": "圣日耳曼大道172号,75006", "address_en": "172 Bd Saint-Germain, 75006",
     "base_images": [],
     "practical": { "type": "practical", "text_zh": "…", "text_en": "…", "confidence": "high" }
   }
   ```

2. **加 storyline**：在 `content/storylines/` 下新建一个 JSON，用 `stops[].poi_id` 按 `order` 串起若干 POI，并为每一站写 `narrative`（四类：`scene` / `anecdote` / `masterpiece` / `history`，均双语 + `confidence`）。同一个共享 POI 在不同故事线里可以讲不同的故事——叙事挂在 stop 上，互不干扰。

3. **构建**：跑构建脚本，重新生成 `dist/`。

   ```bash
   LEMI_OFFLINE=1 python3 -m pipeline.run_paris
   python3 -m http.server -d dist 8000
   ```

> 目前构建入口 `pipeline/run_paris.py` 面向巴黎样板（读 `content/cities/paris.json` + 全部 `content/pois/*` + 全部 `content/storylines/*`）。要做一座新城市时，按同样结构增加 `content/cities/<city>.json` 并复制一份 run 脚本即可。

## 目录结构

四层职责分离：

```
content/     # 数据层:纯 JSON,人可读可编辑(cities / pois / storylines)
pipeline/    # 管线层:Python,把 content/ 编译成 dist/(模型/地理编码/配图/内容生成/构建)
web/         # 模板层:静态站模板与前端资产(templates / assets / i18n)
dist/        # 产物层:构建输出的纯静态站(可直接部署,已被 .gitignore 忽略)
```

- `content/` —— 所有内容以 JSON 存放：`cities/`（城市与地图配置）、`pois/`（共享地点）、`storylines/`（故事线）。
- `pipeline/` —— `models.py`（数据模型）、`geocode.py`（地理编码）、`images.py`（Wikimedia 配图与降级链）、`content_gen.py`（LLM 双语叙事生成）、`build_site.py`（组装城市 payload + 渲染静态站）、`run_paris.py`（端到端构建入口）。
- `web/` —— `templates/board.html`（游戏页模板）、`assets/core/`（storage、mapkit 基础封装）、`assets/game/`（骰子、卡片、格子、卡册、主循环、页面编排）、`assets/styles/`（base.css + game.css）、`i18n/`（界面文案）。
- `dist/` —— 构建产物（`index.html` + `data/` + `assets/` + `i18n/`），部署到 GitHub Pages 的就是它。

## 数据模型:三层解耦

核心设计是把「一个地方」和「关于这个地方的故事」拆开，让同一个 POI 能被多条故事线复用并各讲各的故事（见 `pipeline/models.py`）：

- **POI（共享地点）** —— 只放客观信息：名称、坐标、地址、实用信息、基础图片。跨故事线共享，一处即可复用。
- **StoryStop（故事站 = POI × 故事线）** —— 主观叙事挂在这里：`scene` / `anecdote` / `masterpiece` / `history` 四类双语 `Narrative`，各带 `confidence`。同一个 POI 在不同故事线里对应不同的 StoryStop，因此可以讲完全不同的故事，互不串味。
- **StoryLine（故事线）** —— 一条有主题、有顺序的城市路线，由若干 StoryStop 组成（`title` / `theme` / `summary` 均双语）。

叙事都带 `confidence`（`low` / `mid` / `high`），构建时按阈值（默认 `mid`）过滤，低置信内容不展示，保证呈现质量。

## v2:大富翁棋盘 + 双模式

v2 在原有的「故事线漫步」之上，新增了一套**大富翁式集卡玩法**，并把整个站点拆成两种入口互不干扰的模式。

### 玩法说明

- 摇骰子，Lemi 沿一条 **20 格棋盘**逐格前进（首末格都是 POI，途中穿插 photo / street / chance / easter 等格子）。
- 走到 **POI 格**：镜头俯冲到该地点，弹出一张拍立得卡片，从模糊显影为清晰，点击任意处即可收入卡册。
- 走到 **photo 格**：提示为「下一站」提前取景（它挂在下一个 POI 上，不是死格子）。
- 走到 **street / chance / easter 格**：分别掉落街头小贴士、冷知识问答、彩蛋卡。
- 走过**第 13 格**后切入夜景（`night_from_index = 13`），铁塔格夜间可见。
- **卡册共 10 张**（7 张 R + 3 张 SR），外加 5 条街头卡；卡册分母固定为 10，未获得的卡显示剪影 `?` 占位；重复掉落不重复计数。
- 全流程尊重系统「减弱动态效果」：开启后动效降级但流程仍可走完（`flyTo` 均带 `essential: true`，不会被降级成瞬移）。

### 两种模式入口

站点构建出两个页面，共享同一份 `dist/data/<city>.json` 数据，仅共享 `lemi_lang` 语言偏好：

| 模式 | 入口 | 说明 |
|---|---|---|
| **游戏模式** | `dist/index.html` | 摇骰子、集卡、卡册。玩家状态存于 `localStorage`（`lemi_state`）。页面右上角有「📖 图鉴」入口。 |
| **图鉴模式** | `dist/codex.html` | 只读的滚动叙事（scrollytelling）：滚动驱动地图沿故事线飞行，URL 出现 `#stop=N`，刷新/分享可恢复到该站。 |

> **图鉴模式与玩家状态完全解耦**：它不读写 `localStorage`（`lemi_lang` 除外）、不显示任何集卡进度、不显示角标。服务的是「只想查资料的人」，与游戏模式在状态上彻底分开。图鉴模式经 CDN 引入 Scrollama 依赖整页滚动，CSS 一律用 `dvh`/百分比而非 `vh`（移动端滚动会改变 `vh` 并触发 resize 抖动）。

### `content/` 各目录职责

内容仍全部是人可读可编辑的 JSON：

- `content/cities/` —— 城市与地图中心配置。
- `content/pois/` —— 共享地点（客观信息，跨故事线复用）。
- `content/storylines/` —— 故事线（`stops[].poi_id` 按 `order` 串联，叙事挂在 stop 上）。
- `content/boards/` —— 棋盘配置：`storyline_id`、`filler_plan`（各类填充格数量）、`total_filler`、`content_map`（格子类型 → 内容池映射）、`night_from_index`。
- `content/cards/` —— 集卡卡面（R / SR / SSR），带 `rarity`、双语标题正文、可选 `quote`。
- `content/street/` —— 街头卡（实用贴士，带 `category` 与 `near_poi_id`）。
- `content/chance/` —— 机会格问答（冷知识）。

### `VERIFIED_CONTENT.md` 的作用与新增内容的验证要求

`content/VERIFIED_CONTENT.md` 是 `content/street/` 与 `content/cards/` 中 `quote`、事实性文案的**验证台账**：记录每条内容 `verified=true` 的依据，便于日后复核。构建时 `pipeline/verify.py` 会据此对街头卡与引文做 gate 过滤，未通过验证的引文不会输出到前端。

**新增任何事实性内容（街头卡、卡面引文、冷知识）时必须：**

1. **交叉验证 ≥ 2 个独立来源**：在 `VERIFIED_CONTENT.md` 对应条目下列出 `sources`（至少两个可访问链接）。
2. **对抗性审查**：主动找反例、边界情况与例外，确认没有「一刀切」的错误概括。
3. **措辞不说绝**：对存在例外/因人而异的情形，用「通常」「部分」「常被当成」「可能」等收紧措辞，并在条目下记录收紧理由（例：地铁门只有「部分较旧车厢」需手动开；咖啡分级定价是「合法惯例」而非「法律强制」）。

### 本地预览与部署

```bash
# 离线构建(用已存内容,不联网配图),同时产出 index.html 与 codex.html
LEMI_OFFLINE=1 python3 -m pipeline.run_paris

# 本地预览:游戏模式 http://localhost:8090/  图鉴模式 http://localhost:8090/codex.html
cd dist && python3 -m http.server 8090 --bind 0.0.0.0
```

部署：`dist/` 是纯静态产物，直接托管到 GitHub Pages 即可（见 `.github/workflows/deploy-pages.yml`）。构建会渲染 `web/templates/board.html → dist/index.html` 与 `web/templates/codex.html → dist/codex.html`，并复制 `web/assets/`（含 `core/`、`game/`、`codex/`）与 `i18n/`。
