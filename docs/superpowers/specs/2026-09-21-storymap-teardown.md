# storymap 产品逆向拆解（PRD 参考基线）

> 目标仓库：https://github.com/cuizicheng1024/storymap （Apache-2.0，作者 崔成）
> 本文把 storymap 当作一个产品逆向出其 PRD：页面、状态、交互、数据流、运镜、章节、AI 人格、移动端。
> **依据标注规范**：每个结论后用 `【依据：文件:行】` 标注来源。读不到的部分标注「未能获取，推断」。
>
> **成功读取的源文件**（本地下载后 grep/read）：
> - `artifacts/story_map/index.html`（首页，6595 行）
> - `artifacts/story_map/landing.html`（营销落地页，435 行）
> - `artifacts/story_map/冯异.html`（人物页样例，2424 行，含 `window.__EXPORT_DATA__` 完整数据）
> - `artifacts/story_map/static/profile-app.js`（人物页核心逻辑，9738 行，Babel 转译非压缩）
> - `artifacts/story_map/people_summary_index.json`、`amap-config.js`（部分）、`ai_portraits_registry.json`
> - `冯异.geojson`（空文件，`{"type":"FeatureCollection","features":[]}`）
> - 目录树：`storymap/script/*`（后端 Python）、`storymap/docs/*`（prompt 规范）、`artifacts/story_map/*`
>
> **未能完整读取**：后端 `storymap/script/api/*.py`（`generation_api.py`、`proxy.py` 等，仅见文件名）、`storymap/docs/story_system_prompt.md` 等 prompt 正文、`install.md`（404）。相关结论已标注推断。

---

## 1. 产品定位与用户旅程

### 一句话定位
**storymap（故事地图 / 人类群星闪耀时）**：输入一个历史人物名，AI 生成该人物"时间—空间"人生足迹地图 + 结构化人物档案 + 可与"人物本人"第一人称对话的交互式教学/展示产品。面向语文、历史、地理跨学科教学。【依据：README；landing.html 标题「人类群星闪耀时 — 故事地图」】

### 三个入口页面
1. **landing.html** — 营销落地页（星空 + 生成流水线动画），CTA 跳 `index.html`。【landing.html】
2. **index.html** — 真正首页：搜索框 + 全量人物的「时间分布/空间分布」双视图可视化 + 生成入口。【index.html】
3. **`<人物名>.html`** — 人物故事地图页（Preact 单页应用），产品核心。【冯异.html + profile-app.js】

### 完整用户路径
```
landing.html（可选）
  └─[点 CTA]→ index.html
       ├─ 看到：搜索框、热门人物按钮(李白/苏轼/关羽)、时间轴星图(528人)、地图分布
       ├─[点星图上某个人物节点]→ 若已生成→ 打开 <人物>.html
       ├─[搜索框输入人名 + 回车/点击"go"]
       │     ├─ precheck 存在性 → 已有页面→ 直接跳转 <人物>.html
       │     └─ 不存在→ 触发后端 /generate（静态站点无后端→ 提示"需部署 FastAPI"）
       │           └─ 生成过程用 pixelGenPanel(橙子Agent 像素办公室 iframe) 展示进度
       └─ 进入 <人物>.html：
             ├─ 默认全景 fitBounds 展示所有足迹点 + 轨迹线
             ├─ 左侧时间线(章节)，右侧地图，下方"与人物对话"聊天区
             ├─[点时间线节点/地图marker/键盘←→/自动播放]→ 地图运镜聚焦该站
             └─[在聊天框提问/@其他人物]→ 以第一人称"人物本人"口吻回答(SSE 流式)
```
【依据：index.html:4042/4467/4527；profile-app.js:4266 changeEvent、8532 sendChat】

---

## 2. 页面 / 视图清单

### 2.1 landing.html（落地页）
- **承载**：品牌介绍、生成流水线可视化、统计数字（528 人 / 2000+ 年跨度 / 6000+ 数据点）。
- **默认状态**：星空 canvas 动画 + nebula 视差。
- **可见元素**：hero 标题「故事地图」、CTA(→index.html)、3 张特性卡(⏳时间/🗺️空间/📍足迹)、5 段流水线(人物检索→Markdown生成→地理编码→地图渲染→完成)、footer。
- **进入**：直接访问 / 外部分享。**退出**：点 CTA → index.html。
- **交互 JS**：`startGeneration()` 先 HEAD 探测页面是否存在→存在则快速跳转；否则调 `/api/generate`；后端不可达时 `simulatePipeline()` 走 mock 序列并显示 CLI fallback 命令。【WebFetch landing.html 摘要】

### 2.2 index.html（首页）
- **承载**：搜索 + 全量人物两种分布可视化 + 生成编排。
- **默认状态**：`tabGraph`（时间分布）激活，canvas `#c` 绘制时间轴散点星图；`tabMap`（空间分布）未激活。【index.html:2022-2023, 2193-2194】
- **可见元素**：
  - demo banner（B 站视频链接）；
  - 搜索卡 `.home-search-card`：输入框 `#q`、提交按钮 `#go`、校验 `#searchValidation`、热门人物按钮 `data-hot-person`（李白/苏轼/关羽）、`#precheckCard`、建议 `#searchSuggest`、状态 `#genStatus`；【index.html:1903-1907】
  - 像素进度面板 `#pixelGenPanel`（默认 `is-collapsed`）：内嵌 iframe `#pixelGenOfficeFrame`(`./orange-office.html`)、`#pixelGenSteps`/`#pixelGenAgents`/`#pixelGenLog`/`#pixelGenFill`/`#pixelGenPercent` 等，"橙子Agent"人格化进度展示，标注"只读展示，不能手动暂停或恢复"；【index.html:1912-2009】
  - 图表面板 `.card.graph`：tab `#tabGraph`/`#tabMap`、canvas `#c`(在 `#graphPane`)、地图容器 `#chinaMap`(在 `#mapPane`)、省份曲线面板 `#provinceCurvePanel`、时间范围滑块（`.range-rail` + 手柄 `#h1`/`#h2` + `#sel` + `#startYearInput`/`#endYearInput` + 朝代预设 `#presetBar`）；
  - 作品浮层 `#workTip`。
- **进入**：landing CTA / 直接访问。**退出**：点人物节点/搜索命中 → `<人物>.html`（`window.location.href` 或 `window.open` 新标签）。【index.html:4467/4514】

### 2.3 `<人物名>.html`（人物故事地图页）
- **承载**：单个人物完整故事地图 + AI 对话。
- **静态 DOM 极简**：`<div id="boot-fallback">`（加载/诊断，含 `#boot-diag`「页面加载中…」）+ `<div id="root">`（Preact 挂载点，初始空）。真正 UI 由 `profile-app.js` 客户端渲染。【冯异.html】
- **运行时结构（由 CSS 类 + JS 推断）**：
  - 外层 `.journey-shell` / `.journey-shell-content`；主行 `.journey-main-row`（`.journey-timeline-column` + `.journey-map-column`）；聊天区 `.journey-chat-section`。
  - 地图容器 `#map`（高 620px），三套画布 `#map-maplibre` / `#map-amap` / `#map-cesium`（`.map-canvas`）。
  - 时间线 `.timeline-card` / `.timeline-node`（状态 `.is-passed`/`.is-active`/`.is-future`）/ `.life-rail`。
  - 聊天 `.journey-chat-list` / 推荐问题卡 `.recommended-question-card`。
  - 地图控件 `.map-layer-switch`（矢量/影像/地形/3D地形）、`.map-zoom-stack`（缩放）、`.terrain-compass`（3D 重置视角）、`.map-lazy-overlay`（懒加载遮罩）。
  - 关联人物图 `.related-graph-board` / `.related-graph-core`。
- **进入**：首页节点点击 / 搜索命中 / 直接 URL。支持 URL 参数 `#loc=N`（定位到第 N 站）、`?locZoom=`（覆盖聚焦缩放）、`?amapKey=` 等。【profile-app.js:2270, 4276, 6655】
- **退出**：无显式返回按钮（静态标记中未见），靠浏览器后退。【冯异.html 未见 back button】

---

## 3. 全量交互事件表（最重要）

> 术语：`activeIndex`=当前激活站点索引；`focusZoom`=聚焦缩放（默认单点 5.6 / 多点 10，可被 `?locZoom` 覆盖，clamp 到 [3,18]）。【profile-app.js:2265-2274】

### 3.1 首页 index.html

| 触发源 | 前置状态 | 系统响应 | 后置状态 |
|---|---|---|---|
| 点 tab「时间分布」`#tabGraph` | 任意 | 显示 `#graphPane` canvas 星图，隐藏 `#mapPane` | 时间视图 |
| 点 tab「空间分布」`#tabMap` | 任意 | 显示 `#chinaMap` 地图分布，懒加载详情数据 `stellar_home_data_detail.json` | 空间视图 |
| 拖动时间滑块 `#h1`/`#h2` 或输入 `#startYearInput`/`#endYearInput` | 有 startYear/endYear | `renderTicks()` 重绘刻度，按 `y>=startYear&&y<=endYear` 过滤节点重绘星图 | 年代区间收窄 |
| 点朝代预设 `#presetBar` 按钮 | 任意 | 设定 start/end 年份区间，高亮对应按钮 | 区间跳变 |
| 输入 `#q` + 键入 | 空/有值 | `renderSearchSuggest()` 出联想；`renderMapSearchSuggest()` | 建议下拉 |
| 点热门人物 `data-hot-person` | 任意 | 填入人名并触发搜索流程 | 同"提交搜索" |
| 提交搜索(`#go`/回车) | 输入人名 | ① `probeGeneratedPersonHtml()` HEAD 探测 `./<人物>.html` 是否 ok ② `precheckPerson()` POST `generate/precheck`（8s 超时） | 命中→跳转；未命中→生成 |
| 搜索命中已有页面 | HEAD ok | `navigateToRelativeHtml()`：`window.location.href = "./"+encodeURIComponent(人物.html)` | 离开首页 |
| 搜索未命中（有后端） | STATIC 关或有 API_BASE | `window.open()` 预开人物 tab（先落 `orange-office.html?person=`），轮询 `task?id=` 生成任务，完成后把 tab 导向 `<人物>.html` | 生成中→人物页 |
| 搜索未命中（静态站点无后端） | `STATIC_SITE && !API_BASE` | `requireBackend()` 返回"需要单独部署 FastAPI 后端"提示 | 阻断 |
| 点星图人物节点 | 已加载 data | 取 `node.file` → `navigateToRelativeHtml(file)` | 离开首页 |
| 生成进行中 | 任务运行 | `#pixelGenPanel` 展开，iframe 播"橙子Agent"像素动画，`#pixelGenLog`/`#pixelGenFill`/`#pixelGenPercent` 更新（只读，不可暂停/恢复） | 进度可视化 |

【依据：index.html:2022-2023, 2129-2130, 2157, 2616, 4438-4527, 6494】

### 3.2 人物页 `<人物>.html`（profile-app.js）

| 触发源 | 前置状态 | 系统响应（地图动作 + DOM + 状态写入） | 后置状态 |
|---|---|---|---|
| 页面进入，URL 有 `#loc=N` | 地图 ready | 若 `prefers-reduced-motion` 或无 flyTo→ `map.jumpTo({center,zoom:focusZoom})`；否则 `map.flyTo({center,zoom:focusZoom,duration:700,curve:1.4,speed:1.2,easing:t=>1-(1-t)^3})` | activeIndex=N |
| 页面进入，无 `#loc` | 地图 ready | `applyFitBounds()`：`fitBounds` 全景展示所有点 | 全景 |
| 地图容器进入视口 | 未初始化 | IntersectionObserver(`rootMargin:'240px'`)/2.5s 安全网 触发懒加载地图 SDK | 地图初始化 |
| 点时间线节点 `.timeline-node` | activeIndex=a | `changeEvent(b)`：`startSegmentTransition(a,b)` 动画轨迹；`activeIndexRef=b`；`setActiveIndex(b)`；`replaceState(#loc=b)`；写 aria-live「第 b+1 站，共 N 站」；`applySelectionToMap(b,{pulse:true})` | activeIndex=b，地图聚焦+脉冲 |
| 点地图 marker | activeIndex=a | `focusPoint()`：`markerClickSuppress=true`；`setActiveIndex(idx)`；`focusIndex(idx,true)`（带 pulse） | 同上，聚焦该点 |
| 键盘 ← / → | 焦点非输入框 | `setIsAutoPlaying(false)` + `changeEvent(±1)` | 上/下一站，停自动播放 |
| 键盘 Home / End | 同上 | `changeEvent(0)` / `changeEvent(N-1)` | 首站 / 末站 |
| 点「自动播放」按钮 | isAutoPlaying=false | `toggleAutoPlay()`：若在末站先回到 0；逐站 setTimeout 前进，delay=`clamp(dist/3,1200,3200)`ms（按两点距离）；段动画 duration=1150ms | 巡演中 |
| 自动播放到末站 | activeIndex=N-1 | effect 检测 `activeIndex>=totalEvents-1`→`setIsAutoPlaying(false)` | 停止 |
| 再点「自动播放」（暂停） | isAutoPlaying=true | `setIsAutoPlaying(false)`，clearTimeout | 暂停 |
| 点缩放 +/- `.map-zoom-stack` | 任意 | MapLibre：`easeTo({zoom:±1,duration:260})`（clamp [2,18]）；AMap：`zoomIn/zoomOut` | 缩放 |
| 点「全部/复位」 | 任意 | `fitAll()`：多点 `fitBounds(duration:420)`，单点 `easeTo(focusZoom,420)` | 全景 |
| 切底图 `.map-layer-switch`（矢量/影像/地形/3D地形） | mapLayerType | `setMapLayerType()`；GeoVis 加载对应瓦片；3D 走 Cesium；AMap 回退模式仅支持矢量/影像（选地形弹 warning notice「恢复 GeoVis」） | 底图切换 |
| 3D 地形「重置视角」`.terrain-compass` | Cesium | `adjustCesiumView('reset-bearing')`：相机 heading 归零 | 正北 |
| 聊天框输入并发送（回车/发送按钮/点推荐问题卡） | 非 loading | `sendChat(text)`：解析 @mention；追加 user 消息 + 空 assistant(streaming)；`_postChat()` SSE 流式；逐字渲染；结束后情绪检测 setChatEmotion | 出现回答 |
| 聊天中 @ 人物 | 输入含 @ | 弹 mention picker（↑↓/回车/Esc 导航）；加入 `joinedPartners`（上限 3，不含本人物）；注入多人对话 system 追加提示 | 多人群聊 |
| 聊天请求失败/无后端 | fetch 抛错 | `buildArchiveFallbackAnswer()` 用本地档案兜底回答 + `setChatError(fallback notice)` | 降级回答 |
| 聊天流式空闲超时 | 有请求 | idle watch：首块前 30s / 有块后 45s 无新块→ `controller.abort()` | 中断 |

【依据：profile-app.js:4266-4373(changeEvent), 4346-4380(键盘), 4477-4490(autoplay), 4930-4960(marker click), 5163-5340(AMap focus), 6318-6700(MapLibre focus/fly), 8532-8720(sendChat), 8383-8420(idle watch)】

### 3.3 边界情形
- **首站/末站**：自动播放到末站自动停；键盘 Home/End 直达；`changeEvent` 越界(`<0`或`>=totalEvents`)直接 return。【4267】
- **无坐标点**：`applySelectionToMap` 中 `hasCoords=false` 时只 `setActive`（更新时间线高亮），不移动地图。【4416】
- **单点人物**：`defaultFocusZoom=5.6`（多点为 10）；`fitAll` 单点走 `easeTo`。【2265, 6491】
- **快速滚动/连点**：`selectionTokenRef` 令牌机制丢弃过期选择；`overlayRebuild` 有防抖上限（`overlayRebuildMaxConsecutive`）防反馈循环。【4380-4410, 6707】
- **相邻非连续跳转**（如从第1站直接点第4站）：`startSegmentTransition` 检测 `end !== start+1` 时不播放段动画，直接跳。【3149-3160】
- **prefers-reduced-motion**：进入时用 `jumpTo` 代替 `flyTo`。【6657】
- **地图 SDK 加载失败**：GeoVis→AMap 回退（`activateAmapFallback`），弹 notice。【4823】

---

## 4. 状态机

### 4.1 人物页全局状态（Preact useState/useRef）
| 状态 | 读者 | 写者 | 说明 |
|---|---|---|---|
| `activeIndex` / `activeIndexRef` | 时间线渲染、地图 setActive、聊天 system prompt | `changeEvent`、marker click、键盘、autoplay、`__STORY_MAP_TEST__` | 当前站点索引，核心状态 |
| `selectedLoc` | 聊天「当前场景」上下文、tooltip | `changeEvent`、marker click | 当前 location 对象 |
| `isAutoPlaying` / `isAutoPlayingRef` | autoplay effect、段动画 duration | toggleAutoPlay、键盘、末站 effect | 巡演开关 |
| `mapLayerType` / `currentBaseLayerRef` | 底图渲染、线宽/颜色 | 底图切换按钮、AMap 回退 | vector/imagery/terrain/terrain-3d |
| `mapLoadState` | 懒加载遮罩 | 地图初始化/complete 回调 | loading→ready |
| `chatMessages` | 聊天列表渲染 | sendChat、localStorage 恢复 | 会话消息 |
| `chatDraft` / `chatMentionPicker` / `chatEmotion` | 输入框 / 联想 / 头像情绪 | 输入事件、回答情绪检测 | |
| `joinedPartners` / `joinedPartnersRef` | 多人对话计数 | sendChat @ 解析 | 上限 `MAX_CHAT_PARTNERS=3` |
| `mapNotice` | 回退提示条 | 底图失败 | |
| `segmentAnimationStateRef` | followSegmentProgress 帧 | startSegmentTransition tick | 轨迹生长进度 |

### 4.2 URL / localStorage 参与
- **URL hash `#loc=N`**：`changeEvent` 用 `history.replaceState` 同步写入（不产生历史记录）；进入时读取定位。【4276-4283, 6655】
- **URL query**：`?locZoom=`（聚焦缩放）、`?amapKey=`、`?storymap_debug_*`（调试）、`?clear_chat=1`（清空该人物聊天记录）。【2270, 2288】
- **localStorage**：`storymap_chat_<人物名>` 保存最近 30 条非流式消息（含情绪），进入时恢复；`?clear_chat=1` 清空。【2280-2371】
- **首页无 hash 路由**，纯 fetch 数据渲染。【index.html:6494】

### 4.3 转换关系
```
mapLoadState: (init) → loading → ready ─[GeoVis失败]→ AMap fallback → ready
activeIndex:  任意 N ─changeEvent/marker/键盘/autoplay→ M （同步 #loc=M、aria-live、地图运镜）
isAutoPlaying: false ─点播放→ true ─逐站 setTimeout→ ... ─到末站/任意手动操作→ false
chat: idle → [发送] loading(streaming) → done / error(archive fallback) / aborted
```

---

## 5. 数据模型

### 5.1 人物页数据（`window.__EXPORT_DATA__`，内联在 `<人物>.html`）
真实样例（冯异.html:2399）关键字段：
```json
{
  "person": {
    "name":"冯异","courtesyName":"公孙","dynasty":"东汉初年",
    "description":"...","descriptionHighlights":[{"phrase":"归附刘秀","category":"turning"},{"phrase":"大树将军","category":"event"}],
    "aliases":["公孙"],"birthplace":"颍川父城（今河南省平顶山市宝丰县一带）",
    "avatar":"冯异-ddde473b9349.jpg","avatarSource":"ai","avatarSourceLabel":"MiniMax AI 生成",
    "birth":{"date":"","location":"颍川父城...","lat":33.869,"lng":113.054,"coordSystem":"WGS84"},
    "death":{"date":"34年（存疑）","location":"军中病逝","lat":25.94,"lng":119.50,"coordSystem":"WGS84"},
    "highlights":{"identities":"东汉开国将领、云台二十八将之一","achievements":"...","works":[],"reviews":[]}
  },
  "locations":[
    {"name":"颍川父城","ancientName":"颍川父城","modernName":"河南省平顶山市宝丰县一带",
     "lat":33.869,"lng":113.054,"coordSystem":"WGS84","type":"birth",
     "event":"出身颍川地方社会...","time":"生年不详","significance":"...","works":[],"quoteLines":[]},
    {"...type":"normal"...}, {"...type":"death"...}
  ],
  "coordinateSystem":"WGS84",
  "mapStyle":{"pathColor":"#1e40af","markers":{"normal":{"color":"#3498db"},"birth":{"color":"#2ecc71"},"death":{"color":"#e74c3c"}}},
  "markdown":"# 冯异\n## 一、人物档案...",
  "relatedGraph":{"center":{...},"nodes":[...],"links":[]},
  "personRedirects":{"苏东坡":"苏轼","唐三藏":"玄奘",...},
  "allPeopleNames":["John Snow","上官婉儿",...528人],
  "artifactMeta":{"artifact_version":"80348c95d7cf","build_at":"2026-07-06T06:43:41Z","source_commit":"..."}
}
```
【依据：冯异.html:2399, 85108(window.__EXPORT_DATA__)】

### 5.2 字段 → 视图映射
| 字段 | 渲染到 |
|---|---|
| `person.name/dynasty/description` | 页头档案、聊天 system prompt 身份 |
| `person.descriptionHighlights[].phrase/category` | 描述文本内高亮着色（turning/event 分类） |
| `person.avatar` + `avatarSourceLabel` | 人物头像（标注"MiniMax AI 生成"） |
| `locations[]` | 时间线节点 + 地图 marker + 轨迹线（**核心驱动数据**） |
| `location.type` (birth/normal/death) | marker 颜色（绿/蓝/红）+ 端点样式 |
| `location.lat/lng` | marker 位置、轨迹线折点、运镜 center；WGS84 经 `wgs84ToGcj02` 转换后喂 AMap |
| `location.time/event/significance` | 时间线节点文字 + 聊天「当前场景」上下文 |
| `location.quoteLines` | 名句摘录（聊天 prompt、tooltip） |
| `mapStyle.pathColor/markers` | 轨迹线与 marker 默认色（实际另有 `getLifeColor` 按年代/生命阶段动态覆盖） |
| `relatedGraph.nodes` | 关联人物图 + 聊天可 @ 的候选人 |
| `personRedirects` | 别名重定向（苏东坡→苏轼） |
| `allPeopleNames` | 聊天 @mention 候选、跨人物搜索 |

### 5.3 首页数据
- `stellar_home_data.json`（主，人物摘要用于星图/地图）+ `stellar_home_data_detail.json`（详情，切到空间视图时懒加载）。【index.html:2129-2130, 2616】
- `people_summary_index.json`：人物档案摘要索引（spotlight/quotes/review/works 等，样例仅 1 条 test 数据）。
- `<人物>.geojson`：样例（冯异）为**空 FeatureCollection** —— geojson 通道存在但当前未填充数据。
- **矛盾提示**：README 称静态站点"仅支持首页浏览与查看已生成页面，不支持 /generate 实时生成"，与首页代码中完整的生成编排逻辑一致（静态站点走 `requireBackend` 阻断）。无矛盾，但需注意 GitHub Pages 版是阉割版。

---

## 6. 地图运镜策略（精确参数）

### 6.1 三引擎架构
- **MapLibre GL 4.7.1**（默认，unpkg）+ **GeoVisEarth** 瓦片（矢量/影像/地形）；
- **Cesium 1.124.0**（3D 地形，jsDelivr）；
- **AMap 2.0**（高德，回退引擎，仅矢量/影像）。均**懒加载**。【profile-app.js WebFetch 摘要 + 4823】

### 6.2 何时飞 / 平移 / 不动
| 场景 | 动作 | 参数 |
|---|---|---|
| 进入页面带 `#loc=N` | **flyTo**（有运动偏好时） | `duration:700, curve:1.4, speed:1.2, easing:t=>1-(1-t)^3, essential:true` |
| 进入页面带 `#loc=N` + reduce-motion | **jumpTo**（瞬移） | `{center,zoom:focusZoom}` |
| 进入无 `#loc` | **fitBounds** 全景 | `applyFitBounds()` |
| 单站聚焦(strict) | **easeTo** | `zoom:focusZoom, duration: pulse?650:0` |
| 多站聚焦（连接点≥2） | **fitBounds** | `padding:getFocusPadding(按容器宽), maxZoom:focusZoom, duration:650` |
| `setView` 通用 | **easeTo** | `duration:600`（AMap 用 `setZoomAndCenter` 瞬时） |
| 缩放 +/- | **easeTo** | `duration:260`，clamp zoom [2,18] |
| fitAll 全部 | **fitBounds/easeTo** | `duration:420` |
| 自动播放段过渡 | **followSegmentProgress**（沿轨迹 jumpTo 跟随） | 段动画 duration `1150ms`(自动)/`820ms`(手动) |
| 点选 select 模式 | **不移动地图**（panToIndex 未定义→只 setActive） | 仅高亮时间线 |
| 无坐标点 | **不动** | 仅 setActive |
- **focusZoom**：`locations.length<=1 ? 5.6 : 10`，可被 `?locZoom` 覆盖，clamp [3,18]。【2265-2274】

> **重要观察**：`applySelectionToMap` 的 `mode:'select'` 分支调用 `controller.panToIndex()`，但**三个 controller（amap/maplibre/cesium）均未定义 `panToIndex`**，try 会静默失败 → select 模式下地图实际只更新高亮不重新居中，真正的运镜发生在 `mode:'focus'`（marker 点击、`#loc` hash、focusIndex）。这是一个可复用的"轻交互不打断地图"设计。【profile-app.js:4427(调用) vs 全局无 `panToIndex:` 定义】

### 6.3 轨迹线（polyline）
- **构建**：`buildCurvedSegmentPath(from,to,idx,prev,next)` —— Catmull-Rom/Hermite 风格曲线，用前后点算切线做平滑；`tension` 默认 `{min:0.06,max:0.22,base:0.06,span:0.16}`；`steps` 默认 `{min:24,max:64,divisorKm:60,base:16}`（按距离细分）；急转弯(`dot<-0.55`)时 `sharpDamping=0.12` 抑制过冲。可被 `window.STORY_CURVES_CONFIG` 覆盖。【243-340】
- **样式**：AMap `Polyline` `strokeWeight:6, strokeOpacity:0.88, lineJoin/Cap:'round'`，段色 = 两端 `getLifeColor` 的 `mixHex(...,0.5)`；MapLibre 线宽 `vector:5.6 / terrain:6.4 / terrain-3d:11.6`，halo `15.5/18.5/24.5`。【4524-4525, 4930-4960】
- **动画生长**：`startSegmentTransition` 用 rAF 逐帧推进 `progress` 0→1，`buildPartialSegmentPath` 画部分路径实现轨迹"生长"，自动播放时相机 `followSegmentProgress` 沿线跟随。【3146-3200】
- **方向箭头**：`ensureSegmentArrow` 在每段中点放 `.map-segment-arrow`，`computeSegmentBearing` 算朝向 `rotate(deg)`。【4094-4120, 5818-5992】

### 6.4 标记点（markers）
- **三种类型状态**：`birth`(绿 #2ecc71/#34a853)、`normal`(蓝 #3498db/#1a73e8)、`death`(红 #e74c3c/#ea4335)。【mapStyle + 4930】
- **激活态**：`activePinMarker` 用 `buildSelectedPinDataUrl(color)` 换成大头针图标(26×36)，zIndex 320；非激活为 `CircleMarker`（半径 6.5~8.6，端点更大）。【5150-5157, 4934-4945】
- **时间态**：`getMapPointLabelVisualState` 按 is-passed/is-active/is-future 及"时间褪色"(`timeFadeAmount`)调整；自动播放时不褪色。【4518-4530】
- **点击**：`focusPoint` → 置 suppress、setActiveIndex、`focusIndex(idx,true)`（聚焦+脉冲 `runPulse`）。【4948-4958】
- **标签防重叠**：`getPersistentLabelIndexes`/`getPreferredLabelIndexes` + `LOCATION_RENDER_SPREAD_METERS=180` 对同城点做偏移散开。【WebFetch 摘要】

---

## 7. 章节 / 时间轴机制

- **章节 = `locations[]` 数组**，每个元素一站（出生地→重要地点…→去世地）。冯异样例 5 站（顺序：颍川父城→洛阳→关中→军中→颍川，即数据数组本身顺序，非严格按 `time` 重排 —— 时间线按数组渲染）。【冯异.html:2399】
- **空间绑定**：每站 `lat/lng` 同时驱动时间线节点、地图 marker、轨迹线折点，三者由 `activeIndex` 统一联动。
- **滚动驱动**：**不是**滚动驱动（无 scroll→章节的 scrollytelling）。地图初始化用 IntersectionObserver 懒加载，但章节切换靠**点击/键盘/自动播放**，非滚动位置。这与典型 scrollytelling 不同。【4764(IO 仅用于懒加载), 4266(changeEvent 由点击/键盘触发)】
- **进度指示**：时间线节点状态 `.is-passed/.is-active/.is-future`；aria-live 播报「第 N 站，共 M 站」；自动播放百分比隐含在段进度。【4290-4312】
- **可跳转**：时间线节点、地图 marker、键盘 ←→/Home/End、URL `#loc=N` 均可任意跳转；相邻跳有轨迹生长动画，跨站跳无。【4266, 3149】
- **自动播放**：逐站前进，间隔按两点地理距离 `clamp(dist/3, 1200, 3200)ms`（远则慢），段动画 1150ms。【4477-4490】

---

## 8. "可对话人格"实现

- **入口**：人物页下方 `.journey-chat-section` 常驻聊天区 + 4 张推荐问题卡 `.recommended-question-card`（按人物动态生成，如"你哪一次迁徙最能体现时代处境？"）。【profile-app.js:8200-8208】
- **人格 system prompt**：`historyChatSystemPrompt`（7893-7975）动态构造，核心规则：
  - "你就是<人物>本人，必须用第一人称'我'"；
  - "只基于给定资料作答，缺失则说'史料未载/存疑/我不敢妄言'，不编造地名年份"；
  - "回答≤4段、≤600字，多人对话每人≤2段"，Markdown 分点加粗；
  - **朝代语气表** `dynastyToneMap`（唐豪迈/宋温润/汉雄浑/明沉稳/清严谨/秦威严/元豪放）。
- **上下文构造**：注入【当前场景】(当前 `selectedLoc` 的时间/地点/事件，用于"这里/此地"指代)、【人物档案】、【人物要点】、【相关作品/名句】、【足迹时间线】(最多 28 站)、【名句摘录】、【关联人物】(relatedGraph 取 10 人)。【7893-7975】
- **与地图/章节联动**：`selectedLoc` 变化实时改写 system prompt 的【当前场景】，实现"地图聚焦哪站→AI 就知道你在问哪里"。这是产品最巧妙的联动点。【7940-7948】
- **多人对话**：`@` 其他历史人物（候选来自 `allPeopleNames`/relatedGraph），上限 3 人（不含本人），注入"被@人物用【人物名】开头独立第一人称发言"规则，模拟群聊。【8532-8571】
- **请求链路**：`_postChat` POST 到 `./api/ai/proxy`（或 `MAP_STORY_AI_ENDPOINT`/`MAP_STORY_API_BASE`/`127.0.0.1:8877|8765`），body `{messages,temperature:0.5,stream,context:{personName,partners}}`，SSE 流式（`data:` 分块，type=delta/meta/error），逐字渲染 + 情绪检测(pleased/solemn/nostalgic/agitated/wistful)。【8209-8236, 8320-8420】
- **无后端兜底**：fetch 失败(`LLM_ENDPOINT_UNAVAILABLE`/网络错)→ `buildArchiveFallbackAnswer()` 用本地 `__EXPORT_DATA__` 拼档案要点+时间线+名句，以"我暂时无法接通外部 LLM，先依据档案回答"口吻回复，并显示降级提示。**纯静态站点聊天仍能给出档案式回答**。【7977-8003, 8697-8712】
- **持久化**：`localStorage['storymap_chat_<人物>']` 存最近 30 条。
- **后端**：推断由 `storymap/script/api/proxy.py` + `generation_api.py` 提供 `/api/ai/proxy`，接 MiniMax LLM（README 提及）。**未能读取后端源码，此为推断**。

---

## 9. 移动端适配

- **断点**：`min-width:1024px`（桌面：`.journey-main-row` 横向 flex，`.knowledge-graph-grid` 双列）、`max-width:880px`（`.related-graph-layout` 单列、关联人物左右项改横排）、`min-width:640px`（`.recommended-question-grid` 双列）。【冯异.html:683, 2016, 2071】
- **布局变化**：
  - <1024px：时间线列 + 地图列从横向 flex 退化为纵向堆叠（`.journey-main-row` 默认 column，仅 ≥1024px 才 row）。【467-472】
  - 全屏模式 `.journey-shell.is-fullscreen`：grid `minmax(0,64%) 10px minmax(0,1fr)`（上地图下聊天），聊天折叠时 `1fr` 独占；主行 `minmax(320px,34%) 10px minmax(0,1fr)`（左时间线右地图）。【439-478】
  - <880px：关联人物图单列，中心人物上移(`order:-1`)。
  - <640px：推荐问题卡单列。
- **交互差异**：`prefers-reduced-motion` 下 flyTo→jumpTo（省电/防眩晕）；地图固定 620px 高。触摸交互复用 AMap `attachAmapPointerCompat` 做指针兼容。【6657, 4820】
- **未能获取**：具体触摸手势、移动端聊天输入法适配细节（在更完整 CSS/JS 中，本次未逐行读全）。

---

## 10. 对 Lemi's Diary 的可复用清单

### A. 直接照搬（机制 + 理由）
1. **`locations[]` 单数组同时驱动"时间线节点 + 地图 marker + 轨迹线"，用单一 `activeIndex` 联动三者** —— 文旅故事地图天然是"一段旅程多个站点"，这套数据模型和状态联动可 1:1 复用。【profile-app.js changeEvent/applySelectionToMap】
2. **AI 对话 system prompt 实时注入"当前地图聚焦站点"作为【当前场景】上下文** —— 让"聊这段旅程/这个地点"时 AI 知道你指哪里，是 Lemi's Diary"可对话人格"的关键，几乎照搬即可。【7940-7948】
3. **无后端本地档案兜底回答（`buildArchiveFallbackAnswer`）+ localStorage 会话持久化** —— 保证 demo/静态部署也能对话，降低对 LLM 可用性的强依赖。【7977-8003, 2280】
4. **URL `#loc=N` 深链 + `history.replaceState` 同步** —— 支持分享"某一站"，文旅内容分享刚需。【4276】
5. **轨迹线曲线平滑 + 生长动画 + 方向箭头 + 自动播放（间隔按距离动态）** —— 直接给旅程"讲故事"的运镜观感，参数（duration 700/650/420、curve 1.4）可作起点。【243-340, 3146, 4477】
6. **`prefers-reduced-motion` 降级 flyTo→jumpTo、地图懒加载(IntersectionObserver)** —— 性能与无障碍最佳实践。【6657, 4764】

### B. 需改造（改什么 + 为什么）
1. **三引擎(MapLibre/Cesium/AMap)回退架构** —— 对 Lemi's Diary 可能过重；文旅若聚焦国内可只用一套（AMap 或 MapLibre+国内瓦片），保留"主引擎失败弹 notice 引导"的思路但砍掉多引擎复杂度。【4823】
2. **"点选 select 不移动地图、只 focus 才运镜"** —— storymap 靠"未定义的 panToIndex 静默失败"实现，是巧合式实现；Lemi's Diary 应**显式**区分"轻选中(不打断地图)"与"聚焦(运镜)"两种交互，别依赖 undefined 兜底。【4427】
3. **章节切换靠点击/键盘而非滚动** —— 文旅内容更适合**滚动驱动(scrollytelling)**沉浸阅读；建议在 storymap 的 activeIndex 联动基础上，增加 IntersectionObserver 监听章节滚入来 setActiveIndex（storymap 的 IO 只用于地图懒加载，需扩展）。【4764】
4. **数据字段本地化** —— storymap 的 `dynasty/朝代语气/云台二十八将` 等是历史人物专用；Lemi's Diary 需替换为文旅维度（行程日期、天气、心情、POI 类型、消费、照片），`descriptionHighlights.category` 的枚举也要重定义。【冯异.html person 结构】
5. **多人对话(@ 古人)机制** —— 文旅场景可改造为"@ 同行者/@ 当地向导人格"或直接砍掉。【8532】

### C. 不适用（为什么）
1. **首页 528 人星图 + 时间/空间双分布 + 年代滑块** —— 这是"历史人物库"的聚合浏览，Lemi's Diary 是个人/单次旅行日记，不需要跨主体的宏观星图。【index.html】
2. **"橙子Agent 像素办公室"生成进度动画(pixelGenPanel/orange-office.html)** —— 强绑定 storymap 的"实时生成人物页"后端流水线；Lemi's Diary 若旅程数据是用户录入而非 AI 批量生成，此编排不适用。【index.html:1912】
3. **人物头像"MiniMax AI 生成"+ AI 画像注册表(ai_portraits_registry.json)** —— 文旅用真实照片，不需要 AI 生成古人画像的整套流程。
4. **朝代主题色/朝代语气表** —— 历史专属，文旅应换成"目的地/季节/心情"主题体系。【7920-7935】

---

*拆解基于 2026-07-06 构建版本（source_commit 80348c95d7cf）。后端 API 与部分 prompt 源码未能获取，相关结论已在文中标注为推断。*
