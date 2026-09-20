# Lemi's Diary —— 设计规格(Design Spec)

> 面向出境旅游的 POI 文化展示站:以「故事线」串联城市 POI,每个 POI 附名人轶事、名作介绍、真实图片与拍照机位。
> 技术路线:改造复用开源项目 **storymap**(方案 A)。
> 本文档为架构设计规格,经确认后进入实现计划(writing-plans)。

---

## 0. 一句话定位

**Lemi's Diary** 是一本「可交互的旅行手账」📖:打开一张城市地图,沿着一条条故事线(如《艾米莉在巴黎》)走遍城市里的文化 POI,每到一处,展开它背后的名人轶事、关联名作、历史、拍照机位与实用信息,并配上真实图片。面向出境游的文史爱好者,重「好看好逛」的展示体验,而非行程工具。

- **主入口**:地图为主。
- **灵魂**:故事线串联 POI。
- **气质**:宁缺毋滥——只展示确定可信的好内容。

---

## 1. 战略:主客体反转(相对 storymap)

| | storymap | Lemi's Diary |
| --- | --- | --- |
| **主角对象** | 历史人物 | **POI(地点)** |
| **轨迹含义** | 人物一生的足迹线 | **一部作品/主题串起的故事线** |
| 名人/名作 | 就是主角本身 | 降级为 POI 的内容标签 |
| 页面类型 | 人物页 | POI 页 / 故事线页 / 城市页 |

storymap 的地图轨迹渲染逻辑几乎原样复用,仅连线语义从「人物去过哪」变为「这条故事线打卡了哪」。

---

## 2. 数据模型

> **核心设计:三层解耦。** 同一个知名 POI(如花神咖啡馆)可能出现在多条故事线里,各自讲不同的名人轶事(艾米莉线讲剧情,存在主义线讲波伏娃)。因此**客观信息跟着 POI 走,主观叙事跟着「故事线的这一站」走**。三层为:POI(共享地点)/ StoryStop(故事线的一站,= POI × 故事线)/ StoryLine(故事线)。

### 2.1 POI(共享地点对象)

只存"客观、与故事线无关"的信息;同一 POI 全局只存一份,被多条故事线共享。

```
POI
 ├─ id / city / country
 ├─ name            (双语:zh / en)
 ├─ coord           (地理编码校准后的真实经纬度)
 ├─ address         (双语)
 ├─ base_images[]   (地点基础图:Wikimedia 坐标就近;可为空)
 │    └─ { url, thumb, author, license, source_page, confidence }
 ├─ practical       (🎫 实用信息:开放时间/门票/交通 —— 地点固有,跨故事线【共享】,双语,带 confidence)
 └─ default_photo_spot?  (📸 默认拍照机位 —— 【共享】,StoryStop 可覆盖;双语,带 confidence)
```

### 2.2 StoryStop(故事线的一站 = POI × 故事线)★核心

主观叙事内容挂在这里。同一 POI 在不同故事线中有各自的 StoryStop,内容互不干扰。

```
StoryStop
 ├─ storyline_id + poi_id      (指向哪条线的哪个点)
 ├─ order                      (在这条线里的顺序)
 ├─ narrative[]                (叙事内容数组,每条带 confidence + 双语 + 可选图片)
 │    └─ { type, text_zh, text_en, image?, confidence }
 └─ photo_spot_override?       (📸 覆盖 POI 默认机位;不填则用 POI.default_photo_spot)
```

**narrative type 枚举**(均可选、均双语、均带 confidence,属于"因故事线而异"的主观内容):

| type | 图标 | 含义 |
| --- | --- | --- |
| `scene` | 🎬 | 剧情:该 POI 在本故事线关联作品中的情节 |
| `anecdote` | 👤 | 名人轶事:在本故事线语境下,这里发生过谁的什么故事 |
| `masterpiece` | 📖 | 名作介绍:本故事线关联的文学/艺术/影视作品 |
| `history` | 🏛️ | 历史事件 |

> **字段归属速查**:
> - 🌍 **跨故事线共享**(挂 POI):坐标、名称、地址、基础图、实用信息🎫、默认机位📸
> - 📖 **因故事线而异**(挂 StoryStop):剧情🎬、轶事👤、名作📖、历史🏛️、机位覆盖📸
> - 📸 机位:默认共享(POI),某条线需要特殊机位时可在 StoryStop 覆盖。

> **关键约束(宁缺毋滥)**:每条 narrative / practical 与每张 image 都带 `confidence`,低于阈值直接不展示,不做人工复核队列。图片降级与去重见 §4.3。

### 2.3 故事线 StoryLine(组织者)

```
StoryLine
 ├─ id / city
 ├─ title           (双语)
 ├─ theme/work      (关联作品或主题,如「Emily in Paris」)
 ├─ summary         (双语)
 ├─ stops[]         (有序 StoryStop 列表:剧情/地理排序;每个 stop 引用一个 POI)
 ├─ poster?         (官方海报,不用正片截图)
 └─ path_geojson    (按 stops 顺序连成的路径)
```

### 2.4 城市 City(容器)

```
City
 ├─ id / name(双语) / center_coord
 ├─ pois[]          (本市所有共享 POI)
 ├─ storylines[]    (本市所有故事线)
 └─ 城市首页聚合数据(地图上一个 POI 一个点;点击按"当前故事线"展示对应 StoryStop 内容)
```

### 2.5 生成侧如何判定"哪个名人名作属于哪条线"

**生成按故事线进行,而非按 POI**:生成某条故事线时,Prompt 锁定该线的作品/主题上下文,LLM 只产出属于这条线的 StoryStop 内容,天然不串味。共享 POI(如花神)会被涉及它的每条线各自生成一个 StoryStop,自动归位到对应故事线。


---

## 3. 图片管线(全新子系统)

storymap 仅有「文生图头像」,无真实图片管线,需新建。

```
POI 坐标
  └─▶ Wikimedia Commons GeoSearch(按经纬度+半径找附近带地理标记的图)
        ├─ 命中 ▶ 取图 + 抓取 author/license/source ▶ 缓存本地 ▶ confidence 高
        └─ 未命中 ▶ 按 POI 名称搜图 ▶ confidence 低
                     └─ 低于阈值 ▶ 不展示(不入人工队列)
```

- **来源**:Wikimedia Commons(免费可商用),记录许可证信息以合规。
- **配得准的保证**:**坐标就近优先**——用经纬度找图,天然避免「巴黎铁塔配成东京铁塔」。名称搜图仅作补充且置信度低。
- **影视**:只用**官方海报/宣传物料**,不使用正片截图(规避 Netflix 等版权风险)。
- **机位样片**:同样走 Wikimedia,作为 `photo_spot` 字段的可选配图。

---

## 4. LLM 生成流程(改造 storymap 的 Agent 链)

```
输入:城市 + 作品/主题
  ① LLM 抽 POI 列表 + 排故事线          (Spike 已验证:命中率 100%)
  ② 地理编码校准坐标                     (Photon,带城市偏置;不信 LLM 直出坐标)
  ③ Wikimedia 配图(POI 图 + 机位样片)   (坐标就近)
  ④ LLM 双语生成内容字段 + 打 confidence  (中英)
  ⑤ 渲染 POI 页 / 故事线页 / 城市页
```

### 4.1 复用 storymap 的 LangGraph 编排,重写 Prompt 为「POI 视角 + 故事线抽取 + 双语」。
### 4.2 坐标:必须地理编码校准(Spike 证明 LLM 直出坐标平均偏 140m、最差 450m)。
### 4.3 图片降级链与去重

**图片降级链**(每个 POI 依次尝试,取到即止):

```
① POI 实拍图(Wikimedia GeoSearch,坐标就近)     ← 最优
② 关联名人 / 名作图(Wikimedia 名称搜图,公有领域优先)  ← 无实拍图但有经典轶事时的替代
③ 都没有 ▶ 不展示图片                            ← 宁缺毋滥
```

- **纳入规则(放宽)**:POI 真实图**不再是硬性必须**。只要 POI 有经典/有趣的内容(如花神咖啡馆的波伏娃故事),即便无实拍图,也可纳入故事线,用关联名人/名作图替代展示。
- **全局配图去重**:同一故事线(乃至同一城市)内,各 POI 的配图**尽量不重复**。生成阶段维护一个"已用图片指纹集",命中重复则回退到降级链的下一候选;实在只剩重复图则该 POI 不展示图片。


---

## 5. 多语言(i18n,全新)

- **数据层(双语存储)**:POI 内容字段、故事线标题/摘要、城市名均以 `_zh` / `_en` 双语**存储**(不存双语就无法切换);由 LLM 在生成阶段一次产出双语。
- **展示层(全局切换,单语显示)**:界面同一时刻**只显示一种语言**,不同时并列双语。顶部全局语言开关,一键切换整站(UI 文案 + 内容);语言状态持久化(localStorage)。
- **UI 文案**:走 i18n 资源表(zh.json / en.json)。
- **初版**:中文 + 英文。架构预留扩展到更多语种(字段命名 `_xx` + 资源表可加文件)。

### 图片字段无需翻译,但 `alt`/图注双语。


---

## 6. 地图前端

- **底图/引擎**:MapLibre GL + CARTO 底图(Spike 已验证连通、海外覆盖好、免费)。替换 storymap 的高德 AMap。
- **地理编码**:Photon(OSM),带城市偏置。替换 storymap 的高德 geocode,去掉中国边界校验。
- **交互**:复用 storymap 思路——地图打点、故事线连线、点击弹卡、进视口延迟加载。
- **区分展示**:POI 标记按故事线顺序编号;`photo_spot` 作为 POI 卡片内的一节呈现。

---

## 7. storymap 家底处置清单

| storymap 能力 | 处置 | 说明 |
| --- | --- | --- |
| LLM Agent 生成编排(LangGraph) | ✅ 复用 | Prompt 重写为 POI 视角 + 双语 |
| 地理编码 + 坐标校准 | 🔧 改 | 去中国边界校验、换 Photon、加城市偏置 |
| 地图轨迹渲染 | 🔧 改 | 高德 → MapLibre |
| 静态页渲染 + 首页聚合 | ✅ 复用 | 主对象换成 POI/故事线/城市 |
| 任务系统 / 降级 / CI | ✅ 复用 | — |
| 文生图头像 | ❌ 去除 | 本项目用真实图片,非生成头像 |
| 人工复核队列(hard_place_review_queue) | ❌ 去除 | 宁缺毋滥,低置信度直接不展示 |
| **真实图片管线(Wikimedia)** | 🆕 新建 | §3 |
| **i18n 多语言** | 🆕 新建 | §5 |
| 拍照机位 | ✅ 并入内容字段 | 不单独建模,作为 `photo_spot` 字段 |

---

## 8. 首期范围(MVP)

- **1 城市**:巴黎
- **1 故事线**:《艾米莉在巴黎》(Spike 已产出 12 POI 底稿)
- **完整包含**:双语内容 + POI 真实图 + 拍照机位字段 + 故事线连线地图 + 中英切换
- **目标**:一个可运行的样板,验证完整生产链路与展示体验。

---

## 9. 由助手拍板的实现决策

以下几项经评估后直接定稿(用户已授权由助手决定):

### 9.1 confidence 评分(低成本方案)
不训练模型、不做复杂打分,用**规则式分级**:
- **图片 confidence**:`high` = Wikimedia GeoSearch 坐标就近命中(距 POI < 200m);`mid` = 名称精确命中带地理标记;`low` = 仅名称模糊命中 / 关联名人名作图。**展示阈值:≥ mid 才展示实拍图,名人名作替代图需 ≥ mid。**
- **内容 confidence**:LLM 生成每条内容时**自评** `high/mid/low` 并给一句依据(是否有明确史料/作品出处)。**展示阈值:≥ mid 才展示。** 成本仅为 Prompt 里多要一个字段,零额外调用。

### 9.2 部署形态(参考 storymap,从简)
- **首期=纯静态站**:LLM 生成 + 地理编码 + 配图全在**构建期**离线完成,产出静态 HTML/JSON,不需要运行时后端。
- **托管=GitHub Pages**(对标 storymap 的静态版),零成本、零运维,天然适合"展示站"定位。
- 运行时对话/实时生成等重后端能力**首期不做**(storymap 静态版也不支持),留作后续。

### 9.3 项目目录结构(简洁清晰)
```
lemis-diary/
├── README.md
├── content/                # 数据层(可 git 版本管理的"手账原稿")
│   ├── cities/paris.json
│   ├── pois/*.json         #  共享 POI(坐标/名称/地址/基础图/实用信息/默认机位)
│   └── storylines/
│       └── emily-in-paris.json   #  故事线 + 其有序 StoryStop(叙事内容挂这里)
├── pipeline/               # 构建期生产链(Python)
│   ├── extract_pois.py     #  ① LLM 抽 POI + 排故事线
│   ├── geocode.py          #  ② Photon 坐标校准(带城市偏置)
│   ├── fetch_images.py     #  ③ Wikimedia 配图 + 降级链 + 去重
│   ├── generate_content.py #  ④ LLM 双语内容 + confidence 自评
│   └── build_site.py       #  ⑤ 渲染静态站
├── web/                    # 前端(MapLibre + i18n)
│   ├── templates/
│   ├── i18n/{zh,en}.json
│   └── assets/
├── dist/                   # 构建产物(GitHub Pages 发布目录)
└── cache/images/           # Wikimedia 图片本地缓存
```
原则:**数据(content)/ 生产(pipeline)/ 展示(web)/ 产物(dist) 四层分离**,比 storymap 的 shim 兼容层更清爽。

### 9.4 技术栈落地方式(已定稿)

- **落地方式:借思路不借代码,全新精简搭建。** 不 fork storymap 代码库、不拷贝其模块。只复用其**验证过的设计思路**(结构化数据 + LLM 生成 + 坐标校准 + 静态渲染 + 地图轨迹)。理由:storymap 背着 shim 兼容层与 306 文件历史包袱,与"简洁清晰、用户能通读全部代码"的目标相悖;而 Spike 已证明核心逻辑不复杂,自建成本低且可控。
- **前端:纯静态 HTML + 原生 JS + MapLibre GL。** 无构建链、可直接用浏览器打开、GitHub Pages 友好。对标 storymap 静态版。
- **生产端:Python 构建脚本**(pipeline/),离线跑完生成 dist/ 静态产物。
- **语言/依赖**:Python 3.11+(标准库 + requests);前端零框架、零打包。最小依赖,便于用户理解与自行部署。



---

_Spike 验证产物见 `artifacts/emily_paris_spike/`。_
