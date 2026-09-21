# StoryMap 完整还原 PRD（逆向复刻规格）

> 本文档基于对 storymap 仓库（github: cuizicheng1024/storymap）**全部文件**的逐一源码分析逆向而成（2166 个文件，逐目录读完 306 个 .py、22 个 .js、两个巨型 HTML 模板、9 个 css、全部 docs/data 说明）。
> 目标：把 storymap 的**用户完整链路 + 每一个功能点**完整、无遗漏地记录成 PRD，作为后续改造为「旅行故事线」项目的基线。
> 所有功能点均可回溯到 `文件:行号`（见括注）。
>
> **产品一句话**：输入一个历史人物名 → LLM 生成结构化人物传记 → 地理编码古今地名 → 渲染出「人生足迹地图 + 时间轴 + 穿越时空对话 + 关系图谱 + 考点」的可交互静态人物页；首页是「人类群星闪耀时」星图/地图/搜索发现入口。作者：崔成。

---

## 第 0 章 · 系统定位与两种运行形态

### 0.1 产品定位
- 「人物—时空—事件」叙事的**历史人物时空分析 Agent**。单一数据源 = 每人一份约定格式的中文 Markdown 传记（`storymap/examples/story/*.md`），经构建管线转成静态 HTML 人物页 + 首页星图 + JSON 语料索引。
- 技术栈：FastAPI + uvicorn（后端）、LangGraph（多 Agent，可选）、Neo4j（图后端，可选）、MiniMax LLM（`MiniMax-M3`）、高德 AMap + GeoVis + Cesium（地图三栈）、Preact/React（人物页 SPA）、Phaser（Office 场景）。

### 0.2 两种运行形态（最关键的能力边界，README.md:106-118）
| 能力 | 静态版（GitHub Pages，无后端） | 全功能版（FastAPI 后端） |
|---|---|---|
| 浏览已生成人物页 / 首页 / 检索 | ✅ | ✅ |
| 地图轨迹联动（配 AMAP_KEY） | ✅ | ✅ |
| GeoJSON/CSV 导出下载 | ✅（文件已存在） | ✅ |
| CLI 从 Markdown 批量渲染 HTML | ✅（无 LLM） | ✅ |
| 提交新人物实时生成 `/generate` | ❌ | ✅（LLM + 多 Agent） |
| 任务状态查询 `/task` | ❌ | ✅ |
| 穿越时空对话 `/api/ai/proxy` | ❌ | ✅（LLM，可降级本地问答） |
| 坐标补点 `/coords/bulk`、健康探针、config 注入 | ❌ | ✅ |

- 前端通过 `window.MAP_STORY_STATIC_SITE` 感知自身形态（`profile/renderer.py:302-347`）；静态版顶部显示「静态演示版」提示条，若配 `MAP_STORY_API_BASE` 则提示「已接入外部后端」。
- 运行时判定点：`generate/precheck` 返回 `cached`（静态页可秒开）vs `generatable`（需后端生成）（`generation.py:92-190`）。

---

## 第 1 章 · 用户完整链路（端到端动线）

### 链路 A：发现（首页）→ 浏览已有人物页
1. 进入首页 `index.html`（星图默认视角）→ 页面 `story_map_page_open` 埋点（GA + 火山 APM）。
2. 三种发现方式任选：**① 搜索框**输入人名（联想下拉带打分/命中原因/暂未生成徽标）→ ② **时间分布星图**（按年代散点，拖时间窗滑块筛年代，点节点看浮层）→ ③ **空间分布地图**（高德，人物出生地打点，按省搜索/Top5 面板）。
3. 命中已生成人物 → 打开该人物页 HTML（新标签）。
4. 人物页：头部档案 → journey-shell 双栏（左时间轴 × 右足迹地图）→ 点站/自动播放看人生轨迹 → 穿越时空对话 → 关系图谱跳转到其他人物 → 考点/作品 tooltip。

### 链路 B：发现未收录人物 → 实时生成（仅全功能版）
1. 搜索一个未收录人物 → `precheck` 判定 `generatable` → 预检卡提示「可生成」。
2. 点「开始分析」→ `POST /generate`（幂等键 + 每日配额）→ 返回 task_id。
3. 右下角 Story Console / 橙子 Agent 面板可视化生成进度（6 步流水线 + 5 Agent 卡）→ `pollTask` 轮询状态机 → 完成后打开新人物页，首页刷新。

### 链路 C：延伸体验
- 从特定人物页（如王安石）→ 「延伸游戏」入口 → 进入《回到大宋当宰相·王安石变法》剧情抉择游戏。
- 首页/人物页 → Office 面板（橙子科技/Star Office，Phaser 像素办公室看板，展示 AI 助手工作状态）。

### 链路 D：内容生产（构建期，开发者）
- 写/改 Markdown 传记 → `python3 tools/build_all.py` 全量构建 → 产出人物页 HTML + 首页 + 索引 → 部署 GitHub Pages / OpenDeploy / ECS。

---

## 第 2 章 · 首页功能点（index.html，6595 行）

### 2.1 顶部搜索区
| 功能点 | 交互细节 | 依赖 | 定位 |
|---|---|---|---|
| **人物搜索输入框 `#q`** | input/focus/keydown；↑↓循环高亮联想、Esc 关闭、Enter 提交 | 纯前端 | `index.html:5303-5338` |
| 输入校验 | 最长 12 字符；仅允许汉字/字母/连接符；非法显示中文原因 | 纯前端 | `:2964-3005,2231-2232` |
| **提交按钮 `#go`（开始分析）** | 命中已有→聚焦+打开人物页；未命中→生成流程；loading 呼吸动画 | 命中纯前端/生成需后端 | `:5246-5273,4414-4434` |
| **联想下拉 `#searchSuggest`** | 分层打分：本名精确1200→别名1120→外文1090→拼音1060→前缀980-900→模糊860-740；排序=分数→has_story→年份→locale | 纯前端 | `:5104-5159` |
| 命中原因徽标 | reason 码→「本名精确/别名前缀/拼音精确/外文模糊/关键词模糊」 | 纯前端 | `:2536-2551,5160-5203` |
| 「暂未生成」徽标 | has_story===false 显琥珀色 badge | 纯前端 | `:5184-5186` |
| 作品名 chip + 悬浮卡 `#workTip` | hover《…》作品名出摘要浮层，视口翻转定位 | 纯前端 | `:5178-5183,2484-2526` |
| 热门人物按钮（李白/苏轼/关羽） | 点击回填并搜索 | 纯前端 | `:1903-1905,5276-5283` |
| **预检卡 `#precheckCard`** | badge：可生成/已有页面/已收录可秒开/不建议生成/需重试；按钮 retry/试试李白/试试苏轼 | 预检需后端 | `:4328-4359,5284-5302` |

### 2.2 生成流程 + Story Console（橙子 Agent 面板）
| 功能点 | 交互细节 | 依赖 | 定位 |
|---|---|---|---|
| **像素进度看板 `#pixelGenPanel`**（右下角固定，可折叠） | 悬停展开/↗新标签开 orange-office/摘要卡展开 | 纯前端展示 | `:1912-2015,4259-4292` |
| 阶段流可视化 | 6 步：排队→检索→定位→成稿→审阅→交付 | 纯前端 | `:3801-3808,4109-4119` |
| Agent 卡 | Search/Map/Editor/Critic/Deliver 五卡 | 纯前端 | `:3809-3815,4145-4156` |
| 空闲随机场景 + 动画 | 待命/小睡/巡查 7-12s 轮换；状态灯脉冲/猫尾/打字爪/光标/打字机气泡 | 纯前端 | `:3816-3954,4077-4097` |
| 运营指示条 | 浏览态/生成态/队列/依赖 chip | 后端 health | `:3882-3920` |
| 进度条 + 日志 | 按阶段索引算百分比；最近 5 条日志 | 后端轮询驱动 | `:4165-4242` |
| 内嵌 iframe | `./orange-office.html` lazy 加载 | — | `:1933-1940` |
| **生成主流程** openPerson→ensurePersonGenerated→pollTask | precheck→cached 直开/否则 POST generate（幂等键 sessionStorage）→ task 存 localStorage→轮询 900-1800ms | 后端 | `:4612-4991` |
| 中断任务恢复 | visibilitychange + 启动 300ms 恢复轮询 | 后端 | `:4971-4992` |
| **运行时健康检查** | `GET health/ready` 每 30s；映射 active/serve_unready/generate_paused/backend_unreachable/browser_only | 后端 | `:5048-5103` |

### 2.3 多视角可视化
| 功能点 | 交互细节 | 依赖 | 定位 |
|---|---|---|---|
| **视角 Tab**（时间分布/空间分布） | setTab 切 pane/高亮/工具条/首次进图初始化 AMap | 纯前端/地图需SDK | `:5735-5773,6146-6147` |
| **星图 Canvas `#c`**（时间分布） | 按年代着色；外国人方块/毛泽东"太阳"特殊标记；关系连线（bio/same_book/manual）；选中邻居高亮 | 纯前端 | `:3421-3676` |
| 星图动画 | rAF 缓入缓出+正弦浮动；尊重 reduced-motion | 纯前端 | `:3686-3702` |
| 星图交互 | mousemove hover 浮层；单击选中/双击开人物页（220ms 区分）；右键/中键/Shift 平移 | 纯前端 | `:6249-6296` |
| 人物浮层 `#tip` | 生卒/时代/身份/别名/领域/出生地+短评+暂未生成徽标 | 纯前端 | `:2393-2425,3721-3727` |
| **时间窗滑块** | 双手柄拖拽/刷选/整体平移；非线性时间轴（近现代加权）；双击重置 | 纯前端 | `:6338-6436` |
| 年份输入框 | Enter/change/blur 应用，范围 -800~2000 归一化 | 纯前端 | `:6437-6450,3025-3074` |
| 朝代预设条 | 13 个（全部/春秋战国/秦/汉/…/现代）快捷设窗 | 纯前端 | `:6148-6166,2895-2934` |
| 窗口计数 + 持久化 | `#activeCount`；窗口存 localStorage（防抖 260ms） | 纯前端 | `:3140-3146,5580-5592` |
| **空间地图 `#chinaMap`**（高德） | 懒加载 SDK；胡焕庸线；出生地 marker（圆/外国人方块/毛泽东太阳）；活跃点 twinkle | 高德 SDK+key | `:5453-5920` |
| 地图 marker 交互 | hover 浮层；click InfoWindow（含「打开人物页」）；dblclick 开人物页 | 纯前端 | `:5992-6074` |
| 地图省份搜索 `#mapSearchInput` | 140ms 防抖；缩放到匹配框；建议列表；Enter/Esc/↑↓ | 纯前端 | `:6175-6245` |
| 省份 Top5 面板 | 按出生地统计窗口内各省人数条形图 | 纯前端 | `:3346-3377` |
| 坐标缓存 + 回填 | localStorage 缓存；缺坐标高德 Geocoder 补齐→批量回传 `coords/bulk` | 回传需后端 | `:5489-5710` |
| WGS84↔GCJ02 纠偏 | 坐标系转换 | 纯前端 | `:2329-2349` |

### 2.4 首页其它
| 功能点 | 说明 | 定位 |
|---|---|---|
| B站横幅/标题链接 | 跳 B 站 demo 视频 | `:1866-1885` |
| 深链/初始聚焦 | `?person=`/`?highlight=`/localStorage → 自动聚焦 | `:5216-5244` |
| 数据分层加载 | 主 `stellar_home_data.json` 先载；detail 重字段 requestIdleCallback 补载 | `:6494-6592,2590-2626` |
| 主题 | 无明暗切换；CSS 变量；地图样式固定 macaron | `:14-58,5405` |
| 埋点 | GA gtag（G-B8F24PMY4F）+ 火山 APMPlus（aid 1002542） | `:10` |
| PWA（sw.js） | 缓存策略已写但**首页未注册 sw**（实际未生效） | `sw.js:1-76` |
| i18n | 首页硬编码 zh-CN 单语（多语仅在 Office 面板 zh/en/ja） | `:2` |

---

## 第 3 章 · 人物页功能点（profile_page.html，11710 行，Preact SPA）

### 3.1 数据模型（ProfileData，构建期注入 `const data=__DATA__`）
- **根对象 15 键**：`person / locations / coordinateSystem("WGS84") / mapStyle / textbookPoints / examPoints / workTexts / workSummaries / markdown / relatedGraph / personRedirects / allPeopleNames / templateSignature / artifactMeta`（`builder.py:1023-1042`, `renderer.py:434-468`）。
- **person 字段**：name/foreignName/dynasty/birthplace/nativePlace/birth{date,location,lat,lng}/death{...}/lifespan/avatar/avatarSource/aliases/courtesyName(字)/artName(号)/descriptionHighlights[]/highlights{honor,status,identities,works[],reviews[]}（`builder.py:907-948`）。
- **location（足迹节点）字段**：name/ancientName/modernName/lat/lng/coordSystem/type(birth/death/normal/move/travel)/event/time/duration/significance/works[]/quoteLines[]/poster/geocodeConfidence/geocodeSource/geocodeAliasChain（`profile_location_utils.py:525-541`）。

### 3.2 journey-shell 双栏
| 功能点 | 交互细节 | 定位 |
|---|---|---|
| 三段式壳体 | 上排（左时间轴+分隔条+右地图）+ 下方对话区 | `:10747-11310` |
| 可拖拽分隔条（左右/上下） | mousemove 算百分比，左右钳 24-58%，上下钳 42-78% | `:11015-11033,9526-9552` |
| 面板高度自适应 | 全屏100%/否则 clamp(480px,68vh,760px)；syncMapViewport 同步三引擎尺寸 | `:4568-4571,9589-9636` |

### 3.3 时间轴（左栏）
| 功能点 | 交互细节 | 定位 |
|---|---|---|
| 事件卡全字段渲染 | 序号徽标(彩色圆)/地名/年龄徽标/人生阶段(少时·成长·盛年·晚年·暮年·身后)/事件类型徽章(作品·文学·战争·仕途·行旅)/古称:今称/地理编码溯源注记/时间/停留时间/生命进度条/事件描述 | `:10841-11009` |
| 单站地图注记开关 | 每卡复选框切该站标签显隐，偏好持久化 localStorage | `:10961-10980,4576-4662` |
| 时间轴节点/连接线 | is-passed（彩色渐变）/is-future（灰）；节点 halo 随激活放大；生命色五段渐变 | `:10862-10894,5899-5911` |
| 上/下事件 + 计数 | ←→ 按钮，首尾禁用；显示「当前年龄·N/总数」 | `:10809-10837` |
| 自动播放开关 | 见 3.5 | `:10771-10777` |
| 总行程统计 | Haversine 累加总里程 | `:5321-5348,10799-10806` |

### 3.4 时间轴 ↔ 地图双向联动
| 功能点 | 交互细节 | 定位 |
|---|---|---|
| changeEvent（时间轴→地图核心） | 启动逐段生长动画/更新 activeIndex/写 hash #loc=N/aria-live 播报/applySelectionToMap；地图未就绪轮询重试 | `:6178-6258` |
| 镜头行为 applySelectionToMap | **select 模式仅 panTo 不 flyTo 不改缩放**（防眩晕，明确决策）；focus 模式 fitBounds；stabilize 多次重放 | `:6321-6379` |
| 地图 marker→时间轴（反向） | MapLibre 点层/序号 marker/AMap/Cesium 点击 → setActiveIndex + focusIndex | `:8280-8290,8041-8061,9395-9406` |
| 激活态同步 | activeIndex 变化滚动时间轴卡入视口 | `:9744-9769` |

### 3.5 自动播放（视频高光）
| 功能点 | 交互细节 | 定位 |
|---|---|---|
| 播放循环 + 动态停留时长 | **delay = clamp(相邻两点距离/3, 1200ms, 3200ms)**；到末站自动停；末站再播回第 0 站 | `:7229-7252,6386-6395` |
| 逐段生长动画 | rAF 逐帧推进 progress；自动播放 1150ms/手动 820ms；镜头沿段中心跟随 | `:4975-5024,4958-4964` |
| 三引擎镜头跟随 | MapLibre jumpTo / AMap setCenter / Cesium camera.setView | `:8397-8410,7129-7135,9446-9462` |
| 段视觉状态 | 高亮当前段/淡化未来段 | `:6441-6455` |

### 3.6 底图切换（三地图栈）
| 功能点 | 交互细节 | 定位 |
|---|---|---|
| 底图下拉 MapDropdown | 矢量/影像/地形/3D地形 四选项带预览缩略图；悬停展开可 pin | `:4186-4262,11206-11216` |
| 引擎路由 | 2D(vector/imagery/terrain)→GeoVis MapLibre；3D→Cesium(地形+影像叠加+罗盘) | `:8821-9500` |
| 三引擎容器切换 | #map-maplibre/#map-amap/#map-cesium 可见性 | `:11065-11067,6539-6567` |
| 3D 俯仰 | terrain-3d 时 pitch=66°/bearing=-22° easeTo 过渡 | `:6517-6538` |
| **降级容错链** | GeoVis 失败/超时12s→高德回退；3D 失败→切回2D；overlay 自愈；SVG 兜底覆盖层 | `:6743-7221,8834-8873,7581-7649` |
| 懒加载 | IntersectionObserver 进视口才初始化+2.5s safety-net | `:6652-6729` |

### 3.7 地图控件
| 功能点 | 定位 |
|---|---|
| 2D 总览按钮（fit-all） | `:10641-10643,11123-11153` |
| 3D 缩放/罗盘（抬头/俯视/旋转/回正朝北） | `:11078-11106,5912-5928` |
| 全屏/打开收起对话/生成图片按钮 | `:11217-11241,11137-11150` |
| 底图状态提示 toast | 显示 provider+layerType+重试/切换 | `:11156-11203` |

### 3.8 地点详情浮卡
- 触发：点时间轴卡或地图 marker（selectedLoc 非空）。内容：地名/事件正文/相关图片 poster/历史意义/名篇名句(或作品带 tooltip)。✕ 关闭/点地图空白关闭（markerClickSuppressRef 防误关）。（`:11244-11296`）

### 3.9 穿越时空对话（AI 聊天）
| 功能点 | 交互细节 | 依赖 | 定位 |
|---|---|---|---|
| 对话面板 | 标题「与{人物}对话」+当前地图节点指示+情绪指示点+成员列表(N/3) | — | `:11310-11562` |
| @多人邀请 | 末尾 @ 触发候选浮层(↑↓/Enter/Tab/Esc)；候选=主角+关系图谱+allPeopleNames；上限3人；新成员插「X加入群聊」系统消息 | 纯前端组织 | `:4430-4548,10476-10510` |
| SSE 流式 + 降级 | 端点 `/api/ai/proxy`；SSE 逐块打字机(24ms节流)；首块30s/后续45s超时→回退非流式；LLM 不可达→本地档案回答 | **后端 LLM** | `:10149-10637` |
| 情绪感知 | 回复正则匹配6类情绪(pleased/solemn/nostalgic/agitated/wistful/neutral)驱动指示点颜色+脉冲 | 纯前端 | `:10566-10577` |
| 场景感知 | system prompt 注入【当前场景】(当前 selectedLoc)，使「这里/此地」指代当前地图节点 | 后端 | `:9770-9869` |
| 持久化 + 开场白 | localStorage `storymap_chat_{name}`；按身份生成开场白(帝王「朕」/诗人「在下」)；自动存最近30条 | 纯前端 | `:4313-4401` |
| 消息渲染 | 用户/AI/系统三态气泡；AI 头像用肖像/首字兜底；Markdown 渲染 | 纯前端 | `:11376-11472` |

### 3.10 推荐追问（纯前端规则引擎，不依赖 LLM）
- 画像打分：9 类身份(ruler/military/reformer/literary/scholar/artist/explorer/religious/revolutionary)按角色文本+描述池正则加权，取 top3（`:10977-10997`）。
- 定制映射：孔子/李白/诸葛亮/刘禅/鲁迅/牛顿/曹操 硬编码专属追问（`:10033-10061`）。
- 每画像生成 3-4 条(结合真实地名/首作品/首句)，不足4条兜底；渲染彩色卡片，点击 sendChat（`:10062-10148,11542-11552`）。

### 3.11 关系图谱
- 数据 relatedGraph.nodes/links（后端三级回退 SQLite→Neo4j→JSON，`graph_service.py`）。中心圆+左右两列(奇偶分配)，每项姓名+meta(朝代·身份)按生年着色，点击跳转人物页，hover tooltip。（`:11587-11651`）

### 3.12 其它人物页功能
| 功能点 | 定位 |
|---|---|
| 考点/知识点模块（textbookPoints+examPoints，6色轮转，展开/收起） | `:11567-11585,3992-4184` |
| 作品名 tooltip（hover《…》出作者/时代/体裁/关联人物/名句/摘要，Portal 智能翻转） | `:3386-3502` |
| 全屏（原生 requestFullscreen 优先/CSS 回退） | `:9637-9653` |
| 导出图片（getDisplayMedia 截当前标签页→PNG） | `:9654-9694` |
| 键盘导航（←→上下站/Home/End 首末站，输入框不拦截） | `:6259-6310` |
| 无障碍（marker role=button+tabindex+aria-label；aria-live 播报「第N站共M站」；焦点环） | `:5851-5861,6203-6234` |
| hash 定位（#loc=N replaceState 分享/刷新还原；locZoom query 控缩放） | `:4284-4303,6190-6199` |
| reduced-motion（禁用脉冲/marker/骨架动画；hash 定位 jumpTo 替 flyTo） | `:602-604,8530-8534` |
| 朝代动态主题（14 朝代各配 primary/accent/bg/border/text；注入 CSS 变量+html[data-dynasty]） | `:4406-4429,9877-9894` |
| 头像/肖像（多级回退：映射→静态hash→/portrait API→jpg/png/webp/svg；AI肖像角标+来源tooltip） | `:5211-5304` |
| 内容纠错反馈（页脚按钮，自动附人物/URL/构建版本，mailto/剪贴板） | `:2106-2149,11655-11665` |
| 人物简介展开/收起（3行截断） | `:6153-6177` |
| 叙事文本语义高亮（时间/地点/转折/引用/作品着色）+延伸观看/游戏徽章 | `:3591-3788` |
| 轨迹曲线渲染（Catmull-Rom 贴角小弧；跨洲远距断开不连线；同坐标螺旋散开） | `:2308-2532` |

---

## 第 4 章 · 延伸游戏《回到大宋当宰相·王安石变法》

> 纯前端、无后端、文字互动式历史抉择游戏（visual-novel/剧情分支类），从王安石人物页「延伸游戏」入口进入。文件：`artifacts/story_map/song-minister-game/{index.html,game.js,style.css}` + assets（人物立绘/场景图/史料图/bgm.mp3）。

| 功能点 | 规则 | 定位 |
|---|---|---|
| 六维国势状态 | 皇帝信任80/朝廷支持35/民间承受55/财政压力80/改革推进0/旧党反弹60；均 clamp 0-100；财政压力与旧党反弹为 invert(越低越好) | `game.js:6-18` |
| 出场人物 | 王安石(玩家)/宋神宗/司马光/郑侠/苏轼 | `game.js:21-27` |
| 剧情图谱 | 7 幕线性+分支：第一幕4选项分4支线(青苗/均输市易/保甲/试点)→汇流旱蝗→苏轼寄诗→验雨→流民图死谏→崇政殿召对 | `game.js:30-211` |
| 选项结构 | {标题,说明,状态增量fx,下一场景}；选择时 clamp 累加+飘字显示增减(520ms后跳场) | `game.js:328-404` |
| 结局判定 | 综合评分公式(reform*1.0+(100-finance)*0.7+people*0.5+emperor*0.4+court*0.3-oldParty*0.6)；硬失败优先(罢相/人亡政息/国库崩坏)；正向分级(千古名相/富国强兵/毁誉参半)；兜底壮志未酬 | `game.js:214-291` |
| 结局呈现 | 每结局含背景图/结局文/点评/时人评说(神宗/司马光/苏轼/王安石依立场) | `game.js:336-366` |
| 史料出处弹层 | 标注取材《熙宁七年的雨》+BGM授权 | `index.html:104-124` |
| BGM 双实现 | 首选 bgm.mp3(淡入淡出+音量持久化)；失败降级 Web Audio 实时合成 D 宫五声古筝(look-ahead调度+混响+木鱼) | `game.js:451-757` |

> 另有 Star Office「橙子科技公司」Phaser 动画看板（`static/game.js`，1034行）：展示 AI 助手工作状态，依赖后端 `/status`/`/agents`/`/set_state`/`/yesterday-memo`，纯静态版不工作。

---

## 第 5 章 · 后端能力（全功能版，FastAPI）

### 5.1 API 端点全清单
- **生成类**：`GET/POST /generate`、`POST /generate/precheck`（准入判定：空/虚构角色/敏感现代人/多人/已收录cached/可生成）+ 幂等键 + 每日配额（`generation.py`）。
- **任务类**：`GET /task?id=`（前端轮询）、`/task/debug`、`GET /tasks`、`/task/storage(+maintain)`、`POST /task/cancel`、`/task/retry`（`tasks.py`）。
- **AI 代理**：`POST /api/ai/proxy`（时空对话后端，stream=true 走 SSE；人设注入+熔断器+降级链，`ai_proxy.py`/`proxy.py`）。
- **地理编码**：`POST /coords/bulk`（批量坐标校正，`coords.py`）。
- **健康/指标**：`/health`、`/health/ready`(serve_ready/generate_ready)、`/health/runtime`、`/metrics`(Prometheus)、`/status`/`/agents`/`/yesterday-memo`(Star Office)（`health.py`）。
- **肖像**：`/portrait/status`、`POST /portrait/generate`、`GET /portrait/{name}`（`portrait.py`）。
- **静态分发**：`/amap-config.js`、`/geovis-config.js`(注入key)、`/vendor/{name}`(白名单+回源)、`/`、`/{path}`(catch-all)（`static_pages.py`）。

### 5.2 任务状态机
- 终态：completed/failed/partial_failed/interrupted/cancelled/timed_out；活跃态：queued/running；展示派生态：ok/watch/degraded/empty。
- 执行模型：ThreadPoolExecutor(默认2并发)异步线程池；submit 立即返回，后台线程跑。
- 幂等/恢复：uuid task_id；活跃态同文本去重；Idempotency-Key(TTL 6h)；启动恢复中断任务(SQLite优先)→改判 interrupted→自动重试(默认开)；巡检孤儿任务；协作式取消/超时(默认240s)。
- 持久化：SQLite WAL(artifacts/runtime/task_state.sqlite3) + legacy JSON 回退；TTL 清理(默认3600s)+容量裁剪(默认200)。

### 5.3 多 Agent 生成管线（六 Agent）
- Supervisor（决策 next_step）/ SearchAgent（检索资料）/ GeocodeAgent（并行地理编码，线程池max5）/ EditorAgent（生成Markdown）/ CriticAgent（质量审校+pass/修订判定）/ DeliverAgent（渲染HTML+完成）。
- 默认计划 Search→Map→Editor→Critic；LangGraph Runner + Manual Runner(默认Manual更稳)；CriticAgent pass 标准=无 confidence≥0.7 的问题。
- 五工具（各带 timeout/retry/熔断器）：search_person_info/fetch_ancient_place_map/queue_hard_place_review/generate_markdown/validate_markdown。
- 断点续传：阶段枚举 start/markdown_generation/build_profile/rendering/render_done/done/failed；步骤级 checkpoint(原子写)；生成重试(默认2次)+负缓存。

### 5.4 内容质量门禁（三层）
- **质量检查层（quality/）**：16 条规则只标记不隐藏（LLM思考泄漏/坐标越界/章节号乱/占位符过多等），auto_fixable 标志。
- **Agent 校验层（validation_rules.py）**：pass=NOT(任一issue confidence≥0.7)，pass=False 拦截该稿重生。硬失败规则：时间线乱序/古今地名映射错/享年不符/名篇当名句/真理名言误植/身份混淆/高风险声明(亚里士多德名言/郑和原名/霍去病地名等内嵌纠正 conf≥0.9)。
- **发布真实性门禁（project_paths.py）**：扫前40行声明行，命中「虚构/神话/示例模板/无史料支持」→不可发布(整篇不展示)。这是唯一整篇拦截。

### 5.5 时空对话后端（本地历史问答，proxy 降级兜底）
- LocalHistoryQAAgent：读本地 Markdown 档案，按问题类型(介绍/出生/去世/作品/足迹/评价)分派 answerer，否则关键词检索打分；所有回答冠「根据本地人物档案」，无匹配返回空(不编造)。**纯规则式不需 LLM**。

---

## 第 6 章 · 数据模型与构建管线

### 6.1 三层数据模型（data/corpus/）
- **SOURCE 层**：people_master.json(621人)/people_master_pep.json(326人)；手工查找表 place_aliases/historical_places_index/foreign_name_aliases。
- **DERIVED 层**（tools/build_*.py 重生成）：people_summary_index(539，首页搜索/统计)/work_summary_index(2607作品，作品tooltip)/people_knowledge_graph(关系图谱)/people_birth_coords_wgs84(565人，星图坐标)/portraits_map(507人)/description_highlights(525人高亮)/pep_people_time_index(时间线考点)。
- **OVERRIDE 层**：person_summary_overrides/person_work_exclusions(51人剔除误挂作品)/location_poster_overrides 等人工纠错补丁(按每个别名建键)。

### 6.2 构建管线（tools/build/build_all.py）
- 容错编号管线：[0]Markdown冒烟检查(硬)→[1]people_master(硬)→并行[2/5/6]索引→[3]渲染人物HTML(硬)→并行[4/8/9]坐标/游戏/知识审校→[7]首页+静态站(硬)→收尾报告。
- 核心不变式：每份可发布 md 必须同时出现在 people_master、stellar_home_data 和签名匹配的 {人物}.html，否则标记 story_html_template_stale。
- 首页产出三文件：stellar_home_data.json(核心轻量)/stellar_home_data_detail.json(重字段懒加载)/index.html。

### 6.3 部署
- 静态站不是独立生成器，而是同一构建管线把 HTML 写进 artifacts/story_map/。
- 三条路径：GitHub Pages(CI 调 cli/generate + homepage + validate) / 火山云 ECS(systemd storymap.service 端口8765) / OpenDeploy(Docker python:3.11-slim)。

---

## 第 7 章 · 完整性自检（确认无遗漏）

已逐一覆盖并可回溯源码：
- [x] 首页：搜索(打分/联想/命中原因/徽标/键盘/作品chip) · 生成流程 · Story Console像素看板 · 星图canvas · 时间窗滑块 · 空间地图 · 省份面板 · 坐标回填 · 埋点 · 分层加载 · 深链 · PWA · i18n · 主题
- [x] 人物页：数据模型15键 · 双栏拖拽 · 时间轴全字段 · 双向联动 · 自动播放(停留时长/逐段生长/panTo) · 底图切换(三引擎+降级链) · 地图控件(2D/3D罗盘) · 地点浮卡 · 时空对话(@多人/情绪/场景/SSE/降级) · 推荐追问规则引擎 · 关系图谱 · 考点 · 作品tooltip · 全屏 · 导出图片 · 键盘 · 无障碍 · hash · reduced-motion · 朝代主题 · 头像 · 纠错反馈 · 曲线渲染
- [x] 延伸游戏：王安石变法(六维/7幕/结局判定/BGM) · Star Office Phaser 看板
- [x] 后端：API全清单 · 任务状态机 · 六Agent管线 · 五工具熔断 · 三层质量门禁 · 时空对话后端 · CLI · 环境变量全清单
- [x] 数据/构建：三层数据模型 · build_all管线 · 部署三路径 · 静态vs全功能能力边界

> **本 PRD 为「完整还原」基线。** 下一份 [旅行故事线改造 PRD](./旅行故事线改造PRD.md) 在此基础上做主客体反转与旅行化改造。
