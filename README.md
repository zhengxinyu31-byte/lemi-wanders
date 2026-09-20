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
