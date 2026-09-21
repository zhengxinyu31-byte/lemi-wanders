# 学术级文学地图与作家数据库：数据模型调研

> 调研日期：2026-09-21。本文事实性结论均力求来自 WebFetch/PDF **正文**；凡「仅搜索摘要未见正文」「单一来源」「找不到」的，均在句内或节末明确标注。技术标识符（字段名、实体名）保留原文。

**正文抓取成功率概览**：11 个必查/扩搜目标项目中，成功抓到一手或权威二手正文的 **8 个**（CBDB、MQWW、搜韵、唐宋文学编年地图、Authorial London、A Literary Atlas of Europe、Mapping the Republic of Letters、Mapping Emotions in Victorian London、Digital Literary Atlas of Ireland、Placing Literature —— 实际达 10 个）；**2 个**（大地之书·全球文学时空图志、世界文学地图/文学群星闪耀时）**经多轮多关键词搜索无法定位到任何官方页/一手介绍，判定为"找不到"**。

---

## 一、数据库类（重点：数据模型）

### 1. CBDB 中国历代人物传记资料库

**技术形态**：关系型数据库；提供**在线查询版**（input.cbdb.fas.harvard.edu）、可下载的 **MS Access 单机版**与 **SQLite 单机版**、以及 **API**（MQWW 即通过此 API 共享数据）。规模 2024-02 版约 535,181 人。来源：[The China Biographical Database — Digital Orientalist](https://digitalorientalist.com/2024/04/30/the-china-biographical-database-cbdb-an-introduction-and-conversation-with-professor-peter-bol/)、[CBDB单机版安装配置 — CSDN](https://blog.csdn.net/xfractal/article/details/119696316)。

**建模思路（三类码表）**：库由三层构成——① **实体表(entity tables)**：人(people)、地点(places)、社会机构(social institutions)、文本(texts)、官僚组织(bureaucratic organizations)，其中**人是核心实体**，性别、生年、卒年、族属(ethnicity)等为其属性；② **关系表(relation tables)**：描述实体间关系；③ **关系类型表(relation-type tables)**：描述关系性质（如某地是出生地/迁入地/葬地）。来源：[Digital Orientalist](https://digitalorientalist.com/2024/04/30/the-china-biographical-database-cbdb-an-introduction-and-conversation-with-professor-peter-bol/)。

**主要实体与字段**（来自 [中国历史人物传记数据库CBDB若干表简介 — 博客园](https://www.cnblogs.com/oikoumene/p/6782242.html) 正文）：
- **人物 `BIOG_MAIN`**：`c_personid`、`c_name`/`c_name_chn`、`c_index_year`（指数年/盛年）、`c_female`（性别）、`c_ethnicity_code`（族属）、生卒年。
- **地址 `ADDRESS`**：`c_addr_id`、地名拼音/汉字、`c_firstyear`/`c_lastyear`（地名设置始末年）、`c_admin_type`（行政级别）、`x_coord`/`y_coord`（经纬度）、`belongs1_id/name`（上级行政区）——地理为省—府—州—县多层级链条。
- **官职**：`OFFICE_CODES`(`c_office_id`、`c_dy`朝代、`c_office_chn`) + 任官关联 `POSTED_TO_OFFICE_DATA`(人—官)、`POSTED_TO_ADDR_DATA`(人—官—任职地)。
- **社会关系**：`ASSOC_CODES`(社会联系代码+中文描述+类别id) / `ASSOC_TYPES`(类别) / `ASSOC_DATA`(人物id、关联人id、联系代码)。
- **亲属关系**：`KINSHIP_CODES`(`c_kin_code`、`c_kinrel_chn`) / `KIN_DATA`(人物id、亲属id、亲属关系代码)。
- **社会机构**：`SOCIAL_INSTITUTION_NAME_CODES` + `BIOG_INST_DATA`。
- **著作/文本**：著述(writings)是记录主要维度之一，经 person id 与人物关联，有独立著作编码表。**注：著作表具体字段未能从抓到正文的来源中确认。**

**关系类型数量（实际数字）**：
- **社会关系整体**：共 **10 种关系类(classes)、34 种关系子类(subclasses)、241 种关系条目(types)**。来源：[CBDB总览 — 北大DH/QVIS](https://cbdb-qvis.pkudh.org/dataset.html)（正文）。
- **亲属关系(kinship)**：量级为 **400+ / 约 480 种**，由约 10 种基本关系加修饰符派生（每种关系分别记录男性/女性方向）。来源：[CBDB Kinship Regularized Dataset — Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/5LO4V2)（"more than 400 relations"，**仅搜索摘要，正文未抓到**）+ 知乎摘要交叉印证（**弱来源**）。**"241 关系条目"是社会关系整体口径，与亲属"480"不同口径，勿混淆。**

**时间如何表达**：
- **指数年(index year, `c_index_year`)**：核心机制——用人"顶峰时期年份，常用 60 岁那年"来匹配人物与年代，查询用 `c_index_year between X and Y` 圈活跃段。来源：[CBDB总览](https://cbdb-qvis.pkudh.org/dataset.html)、[博客园](https://www.cnblogs.com/oikoumene/p/6782242.html)。
- **朝代(dynasty, `c_dy`)**、**生卒年**、**地名始末年(`c_firstyear`/`c_lastyear`)**。
- **模糊/近似时间**：CBDB schema 含年号编码(`c_by_nh_code` 等)与 before/during/after/around（之前/之間/之後/約）区间近似标记。**此条来自内部检索交叉印证，公开正文未直接读到 `c_range`/`c_approx` 字段说明（Harvard 官方结构页对 WebFetch 返回 403），标注为「单一/未充分验证」，建议以官方 User's Guide 复核。**

**不确定性 / 史料矛盾如何处理**：
- **忠实录入、保留矛盾**："factual errors and contradictory information would also be included in the entries, as long as they are from the primary source"——只要出自原始史料，错误与矛盾一并录入。来源：[China Biographical Database — Wikipedia](https://en.wikipedia.org/wiki/China_Biographical_Database)（正文）。
- **不做可靠性判断**，靠**来源著录(source citation)**支撑（2021-12 起各表单加入记录来源信息）——即用"标注出处 + 忠实录入"代替"打可信度评分"。来源：CSDN 正文 + [CBDB Sources 页](https://cbdb.hsites.harvard.edu/cbdb-sources)（**仅摘要**）。**未见明确的"可信度评分字段"。**

**无法访问的一手资料**：CBDB 官方 [Structure of the CBDB](https://cbdb.hsites.harvard.edu/structure-cbdb)、User's Guide PDF —— WebFetch 反复 **403 Forbidden**，只能得摘要。亲属关系精确数量与模糊时间字段建议用浏览器/带鉴权工具到 input.cbdb.fas.harvard.edu 码表页最终核实。

---

### 2. MQWW 明清妇女著作（Ming Qing Women's Writings）

主要依据 [Grace Fong, "Historical Research through the Lens of Women: The MQWW Digital Archive and Database" — Cambridge JCH 2020](https://www.cambridge.org/core/journals/journal-of-chinese-history/article/historical-research-through-the-lens-of-women-the-ming-qing-womens-writings-digital-archive-and-database/DE420E636CDC3FC35911D0D39F39CE45)（正文）、MQWW 官方项目页一次成功正文、[Shen Shanbao — Wikipedia](https://en.wikipedia.org/wiki/Shen_Shanbao)（正文）。

**性质**：基于**元数据(metadata)**的数据库（非全文库，全文是"遥远目标"），收录 400+ 部女性著作集（17 世纪—20 世纪初）。

**建模的实体层次**（Fong 论文正文）：
- **作者层(author)**：姓名、性别、族属、婚姻状况(marital status)；含女性与男性（写序跋、评点者）。
- **著作集层(collection)**：题名、出版年、藏书机构、版本类型（刻本/石印本/铅印本/排印本/抄本），每部集附**分析型目录(analyzed table of contents)**。
- **文本层(text)**：以"作者、题名、体裁(genre)、子体裁(subgenre)"标识；类型含序、诗、词、散文、传记、墓志、跋、弹词等。
- **体裁/诗体(form)**：诗体、词牌、文体。
- **关系层(relational)**：家族/亲属、朋友、社会/文学网络——用户"can link between women based on **poetic exchange and correspondence**"（基于诗歌唱和/往来连接诗人）。

**时间与地点**：以元数据字段承载，可对接外部工具可视化——**ArcGIS**（地图/迁徙路线/书籍流通）、**SPSS/Pajek/Gephi**（统计与社会网络）。检索入口含"地区(region)"。数字对象用 **XML(METS schema 子集)** 存页面影像，全库 UTF-8。来源：Fong 论文正文 + 官方项目页摘要。

**与 CBDB 的关联**：MQWW 原为文学工具、非为传记研究而建；为补传记维度，**与 Harvard CBDB 合建 API**，将 MQWW 传记数据存入 CBDB，经"每个作者页嵌入的链接"查询；并**仿 CBDB 模式自 2015 年起提供可下载 MS Access 版，每年 12 月更新**。两库自 2008 年起合作。来源：Fong 论文正文；[HU Jia-jia 论文摘要](https://www.davidpublisher.com/index.php/Home/Article/index?id=35923.html)（仅摘要）。

**沈善宝(Shen Shanbao)为例**：Wikipedia 明确"her poems and references to her appear in Ming Qing Women Writers Database"。生平（据 Wikipedia 正文）：1808–1862，字湘佩，杭州人；著《名媛诗话》为 500 位清代女诗人提供传记材料；1837 年嫁武凌云迁北京，加入女性写作圈（顾太清、龚自珍等），有"逾百名女弟子"，与丁佩交好（丁为其 1836 年首部诗集作序）。**据数据模型可推**其在 MQWW 中可查作者著作集、分析型目录、诗作条目、序跋、婚姻籍贯元数据、基于唱和的社会网络连接，并经作者页跳 CBDB 查传记数据——**但沈善宝记录页实际字段因该页正文未抓到(sinica 站点 socket 反复中断)无法逐项确认**。

**在线状态**：**仍在线，但已从 McGill(digital.library.mcgill.ca/mingqing) 迁至 Academia Sinica(mhdb.mh.sinica.edu.tw) 托管**（McGill 原址正文为迁移通知）。精确"最后数据更新日期"**找不到**。

---

### 3. 搜韵 sou-yun.cn

**性质**：专业古诗词门户，**2009 年由陈逸云创建**。来源：[搜韵-诗词门户 — 检索客](https://www.jiansuoke.com/db/sou-yun)。用户规模"全球超 500 万用户、日活超 4 万"**（单一来源，为搜韵自述经第三方转述）**：[唐宋文学编年地图 — 地图书](https://www.ditushu.com/book/27/)。

**功能维度**（首页正文）：阅读（诗话/词话/古籍检索/类书）、查询（诗词/典故/对仗/词谱/曲谱/**诗词地图**）、韵典、校注、课堂等。检索可按位置（诗题/诗句/第几句第几字）、作者、朝代、体裁、韵部、对仗类型筛选；开放 Web API(api.sou-yun.com)。来源：[搜韵首页](https://sou-yun.cn/)、[搜韵诗词库Web API接口开发指南](https://opendata.library.sh.cn/2020/download/docs/18/广州搜韵文化发展有限公司/搜韵诗词库Web%20API接口开发指南-宋铁镛.pdf)。

**知识图谱与人物实体**（实抓 [知识图谱人物页](https://sou-yun.cn/KnowledgeGraph.aspx?id=85018&type=People&resourceType=Author) 正文）：**确有"人物"实体**（URL `type=People&resourceType=Author`，每作者有独立 ID），维度含姓名字号/生卒/籍贯/朝代/收录作品数/相关诗词数/**相关人物数**/词学图录/多源人物简介。**关键局限：页面只做"相关人物"聚合列表，不标注人物间关系的性质（师徒/唱和/交游）——关系类型不显式建模。**

**闺秀—两性文人互动（骆绮兰—王文治—袁枚）核实**：史实可确证（骆绮兰"为袁枚、王文治弟子"，袁枚为其诗集作序，见 [画里看江苏 — 搜狐](https://m.sohu.com/a/942028684_120596020/)、[湖楼请业图 — 王英志](http://economy.guoxue.com/?p=1399)）；但**搜韵是否把这层师承网络显式建模/可视化，抓到的正文无直接证据——找不到**。这类三方交游网络更接近 CBDB 的社会网络分析(SNA)能力，而三人谈中 CBDB 的 SNA 正是被王兆鹏/郑永晓当作**对标**（非搜韵已实现）讨论：[三人谈《借器之势，出道之新》 — 搜狐](https://www.sohu.com/a/360668579_745113)。

**状态**：活跃维护中；知识图谱已迁 cnkgraph.com 域名、由苏州图谱信息技术有限公司运营（页脚 © 2026）。

---

## 二、文学地图类

### 4. 唐宋文学编年地图（王兆鹏团队，中南民族大学）

**性质与来历**：源自国家社科基金重大招标项目《唐宋文学编年系地信息平台建设》，**2012 年立项、100 多人团队、历时 5 年、2017 年 3 月上线**，挂搜韵网免费开放。来源：[王兆鹏长江讲坛讲稿(一) — 搜狐](https://m.sohu.com/a/782452913_121856534/)。

**"360 余位诗人"需修正为动态口径**：上线时(2017.3)各报道为约 150/151/135 位（王兆鹏自述"上传数据只有 156 家"，[三人谈](https://www.sohu.com/a/360668579_745113)）；2020.9 增至 **400 余位**（[李白是黄鹤楼代言人 — 湖北日报](http://m.cnhubei.com/content/2020-09/27/content_13361793.html)）。所以更准确说法是"上线约 150 位，后增至 400 余位"，"360 余位"是某中间时点近似值。

**数据模型**（讲稿+三人谈正文，证据充分）：两大组成——① 基础数据=作家活动与创作的"**编年系地**"数据；② 将谭其骧《中国历史地图》**矢量化**的地图。核心概念"编年（按年排生活经历）+系地（活动地点定位到坐标）"时空一体。数据从**作家年谱、诗文集编年笺注、生平考证论文**三类文献提取，团队考订补全。生产方式：Excel 模板，**字段含时间、地点、人物、活动、作品编年、交往人物**，多人物表格融合成关系型结构化数据库。**四维度可视化：地理、时间、作家、作品。** 来源：[讲稿(一)](https://m.sohu.com/a/782452913_121856534/)、[名师云讲堂 — 上海师大](https://renwen.shnu.edu.cn/_t745/f5/f9/c26238a718329/page.htm)。

**作品/人生节点如何绑定到地图**（[中国社科院图书馆介绍](http://lib.cssn.cn/zy/dzzy/mfxszy/202105/t20210514_5333385.shtml) 实测正文）：主体为可缩放地图，左侧诗人列表，右侧显示所选诗人人生阶段与辗转地点；**绿色坐标=停留地、红色线段=行程路线**；点击绿色坐标列出该诗人在此地作品；另有"统计报表"以峰图展示各年份诗词产出。

**底图切换（核实：可以切换）**："地理地图背景不仅是当代地图，还可自由选择唐朝、宋朝、五代十国等时期版图"。来源：[中国社科院图书馆](http://lib.cssn.cn/zy/dzzy/mfxszy/202105/t20210514_5333385.shtml)（**单一来源，但描述具体**）。

**"上线两天 220 万点击"核实（属实）**：多源一致——《环球时报》报道经搜狐转载"两天点击超 220 万"（[搜狐](https://m.sohu.com/a/135066943_106413/)）；王兆鹏对《中国科学报》"第一天超 100 万、两天到 220 万"（[博客园转载](https://www.cnblogs.com/amengduo/p/9586922.html)）。

**后续发展与留存（重点）**：
- **后续明确活跃**：2019.5 以"优秀"结项（完成 1000 多万字数据库 + 600 多万字丛书，[国家民委结项公告](https://www.neac.gov.cn/seac/xwzx/201905/1133494.shtml)）；2022.8 数据在"地图书"知识库(ditushu.com)发布并开放 API（[地图书](https://www.ditushu.com/book/27/)）；王兆鹏转任四川大学并主持新的重大项目《汉魏六朝文学编年地图平台建设》（[光明日报](http://www.nopss.gov.cn/n1/2025/0430/c459959-40471575.html)）。
- **地图本体已迁 cnkgraph.com/Map/PoetLife；匿名抓取时返回"微信登录"二维码登录墙**；旧手机版 sou-yun.cn/MPoetLifeMap.aspx 抓取返回 HTTP 500。即**原始唐宋地图的匿名可访问性已下降**，"最后更新时间"无公开标注——**找不到确切日期**。
- **关于"点击量高但留存差/昙花一现"**：**未找到王兆鹏本人或权威访谈的原话直陈"留存差"——找不到直接证据**（220 万是首发爆发流量，之后无公开长期留存数据）。仅找到间接线索：① 一篇知乎文章称团队"市场化尝试……叫好不叫座，处处碰壁……很难融到一分钱"（[知乎 p/95078948](https://zhuanlan.zhihu.com/p/95078948)，**单一、非官方**），指向**商业化困境**而非用户留存；② 三人谈里学界的方法论反思：刘京臣警示数字人文项目恐"沦为旧成果的展示台/新技术的炫耀场"，郑永晓引钱钟书"能帮助人的电脑需要人的更多帮助"，点出**依赖学者持续人工投入**是可持续性软肋（[三人谈](https://www.sohu.com/a/360668579_745113)）。③ 最贴近"反思/复盘"的王贺《虚实之间："重绘中国文学地图"说予数字人文研究之启示》(知乎 p/609802948) **返回 403 未取得正文——已知缺口**。

---

### 5. Authorial London（斯坦福）

官网 [authorial.stanford.edu](https://authorial.stanford.edu/) 可连通（JS 单页，正文取不到）。核心事实来自 [Explore the Literary Geography of London — Geography Realm](https://www.geographyrealm.com/explore-literary-geography-london/)（正文）。

**规模（核实）**：**193 部作品、47 位作家，14—20 世纪**。"约 1,600 处地点引用、12 个文学社群(时期)"**仅见搜索摘要、正文未证实，标注单一来源**。

**【最关键】"作者的伦敦" vs "作品中的伦敦"的区分**：每个地理点按"在何种意义上重要"**着色分类**——**黄色=作者生平(the author's life，真实足迹)、红色=文学作品(literary works，文本/虚构地点)、橙色=两者皆是(both)**。即同一伦敦地名在模型里被拆成"传记维度"与"作品维度"两种归属，一个点可同时属两者。**这就是"真实足迹 vs 虚构/文本地点"的落地方式：用点的归属类型(life / works / both)作为分类字段。** 来源：[Geography Realm](https://www.geographyrealm.com/explore-literary-geography-london/)。

**底图切换（年份全部核实）**：默认现代底图，可按时代切换三张 georeferenced 历史底图——18 世纪早期 = **1723 Thomas Taylor 图**、18 世纪晚期 = **1783 Bowles 图**、19 世纪晚期 = **1880 图**，托管于斯坦福 **EarthWorks(earthworks.stanford.edu)** 地理平台叠加。来源：[Geography Realm](https://www.geographyrealm.com/explore-literary-geography-london/)。

**过滤维度**：genre(题材)、form(散文/诗歌/戏剧)、social standing(社会阶层)、period(时期)；可限定最多 3 位作家、选特定街区(neighborhood)、下钻到具体作品地点。**时间**通过 period/文学社群分类 + 历史底图年代切换双重表达。

**状态**：在线；**最后更新时间找不到**（Geography Realm 文章 2016-04-11 可作至少活跃到 2016 年的旁证）。

---

### 6. 大地之书·全球文学时空图志 —— **找不到**

经多轮多关键词搜索（项目名 + 独特特征词"文字之城""我的地图""作家迁移 导出 GeoJSON"等，叠加机构词），**未定位到该 WebGIS 项目的任何官方页/一手介绍正文**。"大地之书"命中的均为同名诗集/散文集等无关物。四模块（文学地图/作家迁移/文字之城/我的地图）、"我的地图"用户自建功能、作家迁移建模、导出 PNG/GeoJSON —— **全部无法核实**。

特征相近但**不同**的真实项目（供参考、非本项目）：南京大学陈静团队"**文都时空**"文学大数据平台(njlit.com，获 2022 数字人文年会最佳项目奖，[南大艺术学院](https://art.nju.edu.cn/91/43/c55327a627011/page.htm)）；地图书/观沧海(ditushu.com，支持时间轴与 GeoJSON 导出的人文地图编辑器)。**若需补全，须向用户索取该项目确切 URL。**

---

### 7. 世界文学地图 / 文学群星闪耀时 —— **找不到**

经多轮搜索（"3D地球 11大区 34国 72城""流派传播 平行时空 时间轴"等），**未定位到该 3D 交互项目的官方页/一手介绍**。"世界文学地图"命中徐艳华同名图书(天津人民 2008)、Martin Vargic 静态插画地图、《文艺报》专栏；"文学群星闪耀时"命中茨威格书名、一个 PICO/阿里影业 XR 电影《群星闪耀时》(与文学地图无关)。三层结构数字(11/34/72)、地理层级、流派传播动效 —— **全部无法核实**。**若需补全，须向用户索取确切链接/平台。**

---

## 三、扩搜到的项目

### A. A Literary Atlas of Europe（ETH Zürich，Piatti / Reuschel / Hurni）★对我们最有价值

正文最充分：官方 Data Model 页 + 两篇 Piatti 论文 PDF 全文。

**地点分类法（核心！5 大空间类别）**，来源：[Data Model — literaturatlas.eu](https://www.literaturatlas.eu/project/project-structure/data-model/index.html)、[CO-237.pdf(ICC2011)](https://icaci.org/files/documents/ICC_proceedings/ICC2011/Oral%20Presentations%20PDF/C2-Map%20in%20narratives%20and%20for%20narratives%20analysis/CO-237.pdf)、[Piatti_ICC2013_final.pdf](https://www.literaturatlas.eu/files/2014/01/Piatti_ICC2013_final.pdf)：
1. **Setting(场景地)**：情节发生地，人物在场。
2. **Zone of action(行动区)**：多个 setting/projected space 的聚合。
3. **Projected space(投射空间)**：人物**不在场**的记忆/渴望/梦境之地（如《包法利夫人》Emma 靠地图幻想巴黎、《三姊妹》渴望莫斯科），常由触发物唤起；**setting 与 projected space 可在情节中互相转化、甚至空间重叠**。
4. **Topographical marker(拓扑标记)**：仅被提及、人物未在场之地，界定作品地理视野。
5. **Path/Route(路径)**：人物在虚构空间移动的路线。
（任务提到的"marker of movement"实际对应 topographical marker 与 path 两个不同概念，正文无此确切术语。）

**实体-关系与时间**：数据库分 4 部分——文本总信息(含书目、model region)、作者数据、**情节的时间结构(temporal structure of the plot)**、空间对象(核心)；地理基于 **Simple Features Specification(OGC 标准)**；实现于 RDBMS + 供文学学者填写的在线录入表单，自动生成地图。

**地点多重身份 / 不确定性（对我们最关键）**：Setting 分 composite/single；single setting 再分 **exact / imprecise / indeterminate（精确/不精确/不确定）三档**；**Unmappable settings** 只留描述属性无几何；**作者迁移过的地点**单独存一份几何、标为 "geometrically transformed Settings"（区分"真实原型地"与"作者挪移后的虚构地"）；属性可绑定到整个文本并由子对象继承。每个地图对象携带两个元信息维度：**定位精度**与**作者是否改动**。ICC2011 论文明确把"**不确定性可视化**"列为先进文学制图的关键要素。

**底图**：叠在克制的"简单底图"上；有"Work with historical maps"(2012) 条目但**切换机制正文未详述**。另有"statistical surfaces"呈现"文学密度"、区分密集书写区与"未书写空白(blank spaces)"。

**状态**：站点 [literaturatlas.eu](https://www.literaturatlas.eu/en/) 可访问(HTTP 200)，但 Data Model 页脚注明**"已存档、不再维护(archived and no longer maintained)"**，活跃期约 2006–2013 —— **内容存档可读、项目已结项**。

### B. Mapping the Republic of Letters（斯坦福）

来源：[OKFN blog](https://blog.okfn.org/2012/03/22/mapping-the-republic-of-letters/)（正文）。
- **实体**：persons(通信人)、letters(书信)、places(城市，作 source & destination)。
- **关系**：书信=寄件人↔收件人连接；网络图可揭示无直接通信者的**二度连接**(Voltaire↔Franklin)。
- **时间**：timeline + histogram 展示数百年书信分布。
- **不确定性**：明确把"**可视化历史记录中的 gaps, uncertainty and ambiguity**"当作核心挑战与研究机会，为此与米兰 DensityDesign 合作。
- **底图/历史地图**：正文未提历史底图切换。正式数据库 schema/字段结构 **找不到**（OKFN 正文未涉及，单一来源）。

### C. Mapping Emotions in Victorian London（斯坦福 Literary Lab + CESTA，Historypin 平台）

来源：[NYT](https://www.nytimes.com/2015/04/14/books/stanford-literary-lab-maps-emotions-in-victorian-london.html)、[Hyperallergic](https://hyperallergic.com/using-fiction-to-retrieve-the-emotional-geography-of-victorian-london/)、[NPQ](https://nonprofitquarterly.org/emotional-geography-and-one-dickens-of-a-crowdsourcing-project/)。
- **规模/实体**：1,402 本书(700+ 位作家)中 4,363 段文学引文、167 个伦敦地名。链条：书/作家→引文段落→地名→情感类别。
- **情感绑定（众包）**：情感由 **Amazon Mechanical Turk 匿名众包**判定；分类为主题化情感范畴("Dreadful London""London in the Light"等)，一段引文对应一个众包情感。
- **多重身份**：同一地点聚合来自不同作品的多段引文、各带情感归类——"layers upon layers of imaginaries"。
- **不确定性/定位精度**：刻意非精确——同一地点所有 pin **聚簇一处**(如 Chelsea 全堆在 King's Road)。
- **底图（明确的历史底图叠加案例）**：4,000+ 引文绘在 **1893–96 苏格兰国家图书馆 Ordnance Survey 历史地图**上，经 Historypin 叠加在 Google Maps 之上，底部时间轴显示引文年份。
- **状态**：2015 上线；Historypin 官方博客原文现 **404**。

### D. Digital Literary Atlas of Ireland, 1922–1949（TCD / UT Arlington，Charles Travis）

来源：[UTA 项目页](https://websites.uta.edu/travisc/research/digital-literary-atlas-of-ireland-1922-1949/)、[GeoHumanities 目录](https://geohumanities.org/?page_id=125)。
- **规模**：14 位爱尔兰作家，1922–1949。**数据模型**：地图数据存于 GIS，与每位作家作品关联，把"作品中的美学景观(aesthetic landscapes)"链到地理数据。
- **作者传记 vs 作品地点是否分层、不确定性处理、历史底图切换 —— 正文均未说明，找不到细节。**
- **状态**：信息页在线；GeoHumanities 备注 "Back from the dead"，交互工具**基本处于存档/半失效状态**。

### E. Placing Literature（New Haven，纯众包）

来源：[Placing Literature blog](https://placingliterature.wordpress.com/)、[2016 新版发布稿](https://placingliterature.wordpress.com/2016/02/02/welcome-to-the-new-placing-literature/)、[Mental Floss](https://www.mentalfloss.com/geography/maps/interactive-map-lets-you-explore-locations-your-favorite-books)。
- **性质**：纯众包"全球定位式文学信息清算所"，读者/作者提交**书中场景发生地**，类 Google Maps 落 pin。
- **核心实体 `scene`(场景)**（URL /scene/{id}）：每张 "place card" 含书目、场景、地点、照片、外链、check-in(打卡)。检索维度 location / author / book。
- **多重身份**：同址可承载不同作者/作品多个场景；支持机构策展的 **collections**(如 Dickens 集、Sherlock Holmes 集)。
- **不确定性/时间/历史底图 —— 找不到**（轻量众包，无系统建模）。
- **状态**：2013 上线、2016 改版；curl 实测 placingliterature.com **返回 SSL 证书错误(HTTP 000)**，**疑似已停更/维护不佳**。

### F. 日本文学地图项目
- **兵庫文学館「文学マップ」**([artm.pref.hyogo.jp](https://www.artm.pref.hyogo.jp/bungaku/jousetsu/bungakumap/))：按地域组织，**近代/江户按"与地域有渊源的人物"、室町以前按"与地域有渊源的作品"**——用时代切分实体类型(人物 vs 作品)，静态展示、无不确定性建模。
- **日本文学史マップ(余標舎)**([rinzo-yohyosha.com](https://rinzo-yohyosha.com/contents/literature-history-map/))：实为"文艺誌×年代"二维矩阵（非地理 GIS），基于青空文库(1,188 作家/15,725 作品)，建模了"作家跨刊物发表履历"与"流派 overlay"，值得参考的是"实体=作家/作品/刊物/流派、关系=发表于/属于流派"。

**不确定性建模强度排序**：ETH(最系统：三档精度 + 复合几何 + 文本级属性继承 + transformed 几何) ＞ Republic of Letters(明确把 gaps/uncertainty 当可视化目标但无 schema) ＞ Victorian London(靠 pin 聚簇刻意模糊) ＞ Placing Literature / Ireland / 日本项目(基本无)。

---

## 四、【核心】对 Lemi's Diary 三层模型的诊断

我们的模型：`POI`(地点，经纬度/图片/实用信息) → `StoryStop`(某故事线在某 POI 的叙事，含 scene/anecdote/masterpiece/history 四类文本块) → `StoryLine`(串起多个 stop 的故事线)。下面对照学术库逐条诊断。

### 诊断 1：缺「人物」一等实体 —— 这是最大结构性缺陷

**学术库无一例外把"人物"作为一等实体**：CBDB 以 person 为绝对核心（`c_personid` 贯穿全库），MQWW 以 author 为记录起点，搜韵有独立人物 ID 页，唐宋编年地图字段含"人物/交往人物"，Authorial London 的 author 是着色分类的一极，ETH 有独立 author 数据部分。来源：[Digital Orientalist](https://digitalorientalist.com/2024/04/30/the-china-biographical-database-cbdb-an-introduction-and-conversation-with-professor-peter-bol/)、[CBDB总览](https://cbdb-qvis.pkudh.org/dataset.html)、[Fong JCH 2020](https://www.cambridge.org/core/journals/journal-of-chinese-history/article/historical-research-through-the-lens-of-women-the-ming-qing-womens-writings-digital-archive-and-database/DE420E636CDC3FC35911D0D39F39CE45)、[搜韵知识图谱页](https://sou-yun.cn/KnowledgeGraph.aspx?id=85018)、[Geography Realm](https://www.geographyrealm.com/explore-literary-geography-london/)。

**我们把名人只当文本里的名字，会带来的具体问题**：
- **无法聚合**：同一人物（如"苏轼"）散落在多个 StoryStop 的文本块里，系统无法回答"苏轼一共出现在哪些 stop / 哪些 storyline"、"苏轼的行迹连起来是什么"——而这恰恰是唐宋编年地图/Authorial London 的核心能力。
- **无法去歧义/规范化**：文本里的"东坡""苏子瞻""苏轼"无法归一；CBDB 用 person id + 别名表解决。
- **无法做人物维度的导航与检索**：用户不能"按人物浏览"，只能"按地点/故事线浏览"。
- **无法承载关系**（见诊断 2）。
- **建议吸收**：至少引入轻量 `Person` 实体（id + 规范名 + 别名 + 生卒/朝代），让 StoryStop 文本块中的人名以引用(mention)方式挂到 Person，即可解锁"按人物聚合行迹"。

### 诊断 2：缺关系建模 —— 按产品定位决定，但至少需要"人物-地点"和"人物-作品"两类

**学术库的关系建模是其学术价值来源**：CBDB 有 **10 类/34 子类/241 条目**社会关系 + 400+ 种亲属关系（[CBDB总览](https://cbdb-qvis.pkudh.org/dataset.html)、[Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/5LO4V2)）；MQWW 以"诗歌唱和/往来"连接诗人（[Fong](https://www.cambridge.org/core/journals/journal-of-chinese-history/article/historical-research-through-the-lens-of-women-the-ming-qing-womens-writings-digital-archive-and-database/DE420E636CDC3FC35911D0D39F39CE45)）；Republic of Letters 以书信连接人物、能揭示二度关系（[OKFN](https://blog.okfn.org/2012/03/22/mapping-the-republic-of-letters/)）。

**对我们的判断**：作为面向游客/读者的旅行叙事产品，**不必照搬 CBDB 的 200+ 关系类型**（那是史学研究基础设施）。但值得吸收两类最基本、且直接服务于"讲好地点故事"的关系：
- **人物 ↔ 地点**（且关系要**带类型**）：这正是各库共识——同一地点对某人物可能是"出生地/居住地/流放地/写作地/纪念地"。这直接引出诊断 3。
- **人物 ↔ 作品**（masterpiece 文本块里的名篇应挂到作者与作品实体）。
- **注意搜韵的反面教训**：搜韵虽有人物页，但"相关人物"只做**无类型聚合**、不标注师徒/唱和关系性质——这是"有人物实体但关系建模不足"的典型，说明**光有实体不够，关系要带语义类型才有价值**。

### 诊断 3：地点的"多重身份"完全没区分 —— 我们最该立刻吸收的设计

我们的 `POI` 是单一的物理地点，`StoryStop` 只是"某故事线在此的叙事"，**没有区分"这个地点对这个人物/作品意味着什么"**。而这正是学术库设计最精华处：
- **Authorial London**：用 **life(黄)/works(红)/both(橙)** 三态着色，区分"作者真实足迹" vs "作品中写到的地点"。[Geography Realm](https://www.geographyrealm.com/explore-literary-geography-london/)
- **ETH Literary Atlas of Europe**：把地点细分 **setting / projected space(记忆渴望地) / topographical marker(仅提及) / zone of action / path**，且 setting 与 projected space 可互相转化。[Data Model](https://www.literaturatlas.eu/project/project-structure/data-model/index.html)
- 我们的四类文本块 `scene / anecdote / masterpiece / history` 其实**已隐含**了类似维度（scene≈作品场景、history≈真实史实、masterpiece≈作品、anecdote≈轶事），但它们只是**并列的文本块，没有上升为"地点身份类型"的结构化字段**，因此无法做"只看某人真实住过的地方""只看作品里虚构的地方"这类过滤与着色。
- **建议吸收**：为 StoryStop（或"人物-地点"关系）增加一个**地点身份类型**枚举字段，至少区分 `real_footprint(真实足迹/住过) / fictional_setting(作品中的地点) / commemoration(后人纪念)`——这是投入产出比最高的一处改造，直接对齐 Authorial London 的核心设计。

### 诊断 4：`confidence: high/mid` 相比学术库的不确定性处理太粗、且维度错位

我们的 `confidence` 是**单维、粗粒度**的整体标记。学术库的差距在于**它们把"不确定性"拆成多个正交维度、并落到具体对象上**：
- **CBDB**：不打整体可信度分，而是"**忠实录入 + 标注 source citation**"，甚至**保留矛盾信息**（只要出自原始史料）。即把判断权交给用户、把出处透明化。[Wikipedia CBDB](https://en.wikipedia.org/wiki/China_Biographical_Database)
- **ETH**：把不确定性拆为**定位精度(exact/imprecise/indeterminate)**、**是否可上图(unmappable)**、**作者是否改动过原型地**三个正交维度，各自独立建模。[Data Model](https://www.literaturatlas.eu/project/project-structure/data-model/index.html)
- **CBDB 时间不确定性**：用指数年 + before/during/after/around 近似标记 + 生年不详的专门处理（**此条正文未完全证实，标注单一来源**）。
- **具体差距**：
  1. **维度缺失**：我们只有一个总 confidence，无法分别表达"地理坐标不确定" vs "这件事是否真发生过" vs "年代存疑"——而这些在学术库是分开的。
  2. **没有 source/出处字段**：学术库靠"挂来源"支撑可信度；我们没有 provenance，用户无法核验，也无法像 CBDB 那样"保留矛盾+标注出处"。
  3. **没有时间不确定性表达**：我们（据现有三层模型）似乎没有对"生卒不详/年代存疑/时间段 vs 时间点"的建模，而 CBDB 有专门机制。
  4. **前端呈现**：学术库把不确定性**可视化**（ETH 的 imprecise 用不同符号、Victorian London 用 pin 聚簇表达"别指望精确"）；我们的 high/mid 若只是隐藏字段则毫无产品价值。
- **建议吸收**：(a) 至少把 confidence 拆成"地理定位精度"与"史实可信度"两维；(b) 增加 `source`/出处字段（哪怕是自由文本），对齐 CBDB 的透明化思路；(c) 为时间增加"时间段/约/存疑"的表达能力；(d) 前端对低置信内容用视觉手段(虚化/问号/不同符号)呈现，而非静默。

---

## 五、局限与缺口（本次调研未能坐实的部分）

- **CBDB 官方一手文档(Structure of the CBDB / User's Guide)** 对 WebFetch 返回 **403**，亲属关系精确数量(400+/480)与模糊时间字段(`c_range`/`c_approx`)**仅得摘要/内部交叉印证，未由官方正文坐实**。
- **MQWW 沈善宝记录页实际字段** 因 sinica 站点 socket 中断**未抓到正文**，其在库内可见字段为据数据模型推断。
- **唐宋文学编年地图的"留存差/昙花一现"** 无王兆鹏本人或权威访谈原话直陈——**找不到直接证据**；最相关的王贺反思论文(知乎 p/609802948) **403 未取得**。项目最后更新日期无公开标注。
- **大地之书·全球文学时空图志** 与 **世界文学地图/文学群星闪耀时** 两个项目**经多轮搜索无法定位到任何官方页/一手介绍——判定"找不到"**，其数据模型、"我的地图"自建功能、三层结构数字等全部无法核实。若这两项对结论重要，**建议向用户索取确切 URL/主办方**后再补。
- **Authorial London 的 ~1600 处引用/12 社群、Republic of Letters 与 Ireland 的正式 schema、Placing Literature 的不确定性建模** 均为单一来源或找不到细节。
