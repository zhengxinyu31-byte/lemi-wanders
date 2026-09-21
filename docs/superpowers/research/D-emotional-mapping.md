# 情感/氛围如何在地图上表达

> 调研日期：2026-09-21。核心问题：把"情感/氛围"画到地图上，一共有哪些具体手法、如何权衡氛围与信息、女性主义地理学为何与之强相关、非视觉通道的价值。
> 纪律说明：本报告结论均来自 WebFetch/正文抓取，非仅搜索摘要；关键结论标注多来源。找不到一手的作品明确标"未核实"。

---

## 一、情感地图手法总表（最重要）

下表综合 IEEE VIS 2025 论文《Mapping What I Feel》的分类体系与各实证作品。论文把手法分为两大策略——**Sensations（感官编码）** 与 **Narratives（叙事编码）**，共 7 大类 15 种低层技法（括号内为该论文在 62 个作品语料中的出现频次）。来源：[arXiv:2507.11841v1](https://arxiv.org/html/2507.11841v1)。

| 手法 | 出处作品 | 具体做法 | 效果 | 代价 |
|---|---|---|---|---|
| **色彩/明暗**（Color, n=24；论文中最常见的感官手法） | 《红楼梦情绪地图》"由明转暗"（未核实，见下）；Victorian London 用红/蓝分区"Dreadful/Light" | 用色相/明度映射情绪极性或命运走向；随时间推移整体压暗表达衰败 | 直觉、即时可读，无需图例也能"感到"氛围 | 色相→情绪的映射是文化约定，易误读；压暗会牺牲细节可读性 |
| **写实图像/照片**（Realistic images/photos, n=18） | Victorian London（Historypin 叠加 1893–96 实测地图）| 用真实照片/历史地图底图承载年代感 | 增强"在场"与真实感 | 图像会锁定单一视角，压过抽象数据 |
| **符号/隐喻**（Symbol/metaphor, n=17；占语料 27.4%，显著高于一般情感可视化）| 女性主义/批判制图作品普遍使用 | 用象征物代替标准点线面（如心、伤口、根系）| 承载修辞和情绪，信息密度高 | 需解读，牺牲精确性；论文明确指出这是地理数据"修辞性丰富"的体现 |
| **实体材料/物化**（Tangible materials, n=14）| Kate McLean 把气味装进香水瓶陈列在地图下方 | 把情绪/感官做成可触摸、可嗅的实物 | 调动身体感知，记忆更深 | 无法数字分发/规模化，只能在展览现场 |
| **形状**（Shape, n=8）| —— | 用轮廓/形态本身编码情绪 | 前语义、快速 | 语义模糊 |
| **声音**（Sound, n=7）| 《世界女神图鉴》原语言发音（未核实）；谭盾《女书》交响乐（[永州政府网](https://www.yzcity.gov.cn/cnyz/nswh/202211/96d9eeef3842451db02b4edf1521437a.shtml)）| 环境音、原语言发音、配乐 | 增加沉浸与文化真实性 | 需要主动播放、依赖设备与环境；见第四节 |
| **风格**（Style, n=6）| 女书视觉设计、手账拼贴风 | 手绘感/笔触/纹理传递情绪基调 | 一眼定调，"软"氛围 | 风格越强，可读性/权威感越弱 |
| **布局/尺度扭曲**（Layout, n=3，含"鱼眼"变形）| 批判制图（Iconoclasistas 等）常放大被忽视之地 | 重要的地方画大、变形空间关系 | 强调价值判断、引导注意 | 违背"科学空间逻辑"，不能用于导航/测距 |
| **动画/模拟**（Animation/simulation, n=3）| 情绪地图"可播放"、命运随时间演进；气味的扩散动画 | 时间性：播放、渐变、脉动 | 表达"过程"与情绪流变 | 需时间成本观看，不能一眼看全 |
| **字体**（Typeface, n=2）| 女书"长脚文"本身即女性化字形 | 字形/排版传情绪 | 细腻 | 影响弱 |
| **标注内容/关联故事**（Annotated content, n=33；论文中**最高频**的手法）| Victorian London 引文；Nold Emotion Map 参与者注释 | 在地点上挂引语、故事、个人观察 | 第一人称在场感最强、可信度高 | 需要阅读，信息量大易过载 |
| **拼贴**（Collage, n=10）| 女性主义制图、手账风 | 多素材拼贴叠加 | 主观、丰富、"手作"温度 | 视觉噪声、难以系统读取 |
| **肢体语言**（Body language, n=5）| 参与式绘图（Nold 工作坊、Iconoclasistas）| 用身体动作/具身参与产生数据 | 真实、参与感 | 难标准化 |
| **措辞/用词**（Wording/phrasing, n=3）| Victorian London 分类名"Dreadful London"等 | 用带情绪的命名 | 定调 | 主观框定 |
| **个性化视觉**（Personalized visual, n=3）| Nold 个人情绪轨迹 | 为个体定制视觉 | 亲密、个人化 | 不通用 |

**补充手法（论文语料之外，来自实证项目）：**
- **留白/遮蔽/去底图**：Kate McLean 的气味地图**刻意去掉街名、地标、河流**，只留气味点与色彩等高线——"没被记录的地方"即空白，让感官成为唯一导航。来源：[The Common](https://www.thecommononline.org/sensory-maps/)、[ArchDaily](https://www.archdaily.com/985983/sensory-maps-what-the-sense-of-smell-can-reveal-about-urban-environments)。
- **等高线语言的挪用**：McLean 借用地形图的等高线，但把"海拔"替换成"气味扩散范围"（*Smells of Auld Reekie*）。来源：[The Common](https://www.thecommononline.org/sensory-maps/)。
- **生理数据映射**：Christian Nold 的 Bio Mapping 用 GSR（皮肤电反应）测情绪唤起，与 GPS 位置绑定，生成"高/低唤起点"地图。来源：[biomapping.net](http://biomapping.net/)、[softhook.com](http://www.softhook.com/emot.htm)。
- **情感曲线（narrative arc）**：把文本情绪值随进度画成一条起伏线（非地图但常与文学地图并置）。Reagan 等归纳出六种基本形状：rags-to-riches / riches-to-rags / man-in-a-hole / Icarus / Cinderella / Oedipus。来源：[MIT Technology Review](https://www.technologyreview.com/2016/07/06/158961/data-mining-reveals-the-six-basic-emotional-arcs-of-storytelling/)、[The Cut](https://www.thecut.com/2016/11/stories-have-six-emotional-shapes.html)。

---

## 二、IEEE VIS 2025 论文单列：《Mapping What I Feel》

**已拿到论文正文（arXiv HTML 全文）。** 这就是任务描述里说的那篇——虽然主标题是"Mapping What I Feel"而非字面的"emotional geography"，但正是"用地图沟通空间中的情感 + 62 个作品语料 + 附作品集网站"这一篇，完全吻合。

- 标题：**"Mapping What I Feel": Understanding Affective Geovisualization Design Through the Lens of People-Place Relationships**
- 作者：Xingyu Lan（复旦大学）、Yutong Yang（上海交大）、Yifan Wang（复旦大学）
- 发表：IEEE VIS 2025 / IEEE TVCG 2025，DOI 10.1109/TVCG.2025.3633878
- 一手来源：[arXiv:2507.11841](https://arxiv.org/abs/2507.11841)（[HTML 全文](https://arxiv.org/html/2507.11841v1)）、[IEEE VIS 2025 会议页](https://ieeevis.org/year/2025/program/paper_33761c1b-3649-4d86-8e2f-41cdb361e6a6.html)、[PubMed 41269824](https://pubmed.ncbi.nlm.nih.gov/41269824/)
- **作品集网站：https://affectivegeovis.github.io** （论文正文给出。注：该站是纯 JavaScript 单页应用，脚本抓取只拿到空壳，**62 个作品的逐条清单未能抓取，标未核实**；但作品总数、频次、分类体系均来自论文正文，可靠。）

### 方法论
从 313 篇论文中筛出 **62 个 affective geovisualization 设计**（含学术论文与"in-the-wild"项目），用地理学的 **Person-Process-Place (PPP) 模型** 编码，再用 K-Modes + 层次聚类得出设计范式。

### 分类体系（完整）
**PPP 三维度：**
- **Person（谁）**：个体 vs 群体（33 个体 / 29 群体）；身份特征。**80.6% 涉及具体身份**（居民、难民、原住民等），只有 19.4%（12 例）是泛化"用户"。
- **Place（何处）**：地理尺度 + 解释层级——**Physical（物理，39）/ Memorized（记忆化，11）/ Psychological（心理化，12）**。
- **Process（如何）**：情绪数据来源 + 情绪表征（即第一节的 7 类 15 技法）。

**情绪表征：7 大类 15 种技法**（详见第一节表格，论文另提出一个新类别 "performance/表演"）。两大策略：Sensations（色彩、写实图像、符号隐喻、实体材料、形状、声音、风格、布局、动画、字体）与 Narratives（标注内容、拼贴、肢体语言、措辞、个性化视觉）。

**四大设计范式：**
1. **Computational（计算）**：作者是开发者，做公共表达/社交互动工具（如情感分析）。
2. **Anthropological（人类学/人种志）**：作者是记录者，"为特定群体发声"，用田野/访谈；可视化是"放大器"。
3. **Social activism（社会行动主义）**：作者是组织者，办参与式活动；可视化是"催化剂"。（位于科学/艺术/人文/社科四象限的交叉中心）
4. **Art（艺术）**：作者是体验者，传递个人情感；可视化"像一首诗"。

### 论文对"氛围 vs 信息"trade-off 的明确讨论
论文把这个矛盾编码进了 **Place 的解释层级**：
- **Memorized places（记忆化地点）**表现出"认知压缩、情绪放大、时序错乱"，产出**模糊、带缺失/不确定性**的描绘。
- **Psychological places（心理化地点）**"不受物理规律或历史准确性约束"，用隐喻几何"偏离科学空间逻辑"。
- 论文明确把地图作为"科学工具"（优化距离/路线）与情感设计做对照：情感设计**偏好非效率的探索、偏好具象而非抽象的表达**。
这正是本项目要的那个 trade-off 的权威表述——它不是被回避，而是被当作设计维度主动选择。

---

## 三、各作品/项目分述

### 3.1 Mapping Emotions in Victorian London（斯坦福文学实验室，2015）★经典必查
- 斯坦福 Literary Lab + Center for Spatial and Textual Analysis，Historypin 平台，Mellon 资助。
- 做法：从 1,402 部（一说 1,400）19 世纪小说中提取 4,363 段涉及伦敦地点的文字，众包（Amazon Mechanical Turk）标注情绪，归入 "Dreadful London""London in the Light""A Day in the Life of Old London" 等类别，标注在 1893–96 实测地图（叠在 Google Maps 上）。
- 关键手法：**引文标注（annotated content）+ 情绪分类命名（wording）+ 历史实测底图（realistic image）+ 底部时间轴（时间性）**。
- 值得注意的 trade-off 自白：Hyperallergic 明确指出"**不要指望精确地理**"——同一地点的所有引文被**聚在一起**（如切尔西全堆在 King's Road），"映射虚构不是对某时某地的精确再现"。这是氛围优先牺牲空间精度的典型。
- 来源：[NYTimes](https://www.nytimes.com/2015/04/14/books/stanford-literary-lab-maps-emotions-in-victorian-london.html)、[Hyperallergic](https://hyperallergic.com/using-fiction-to-retrieve-the-emotional-geography-of-victorian-london/)、[NonprofitQuarterly](https://nonprofitquarterly.org/emotional-geography-and-one-dickens-of-a-crowdsourcing-project/)、[Historypin](https://about.historypin.org/2015/04/14/mapping-emotions-in-victorian-london/)。

### 3.2 Christian Nold — Bio Mapping / Emotional Cartography（2004–）
- 参与者佩戴测 GSR（皮肤电，情绪唤起指标）的设备边走边记，回来生成"高/低唤起点"地图，再由群体共同注释。覆盖 25+ 城市、2000+ 人。
- 手法：**生理数据映射 + 个性化视觉 + 群体标注 + 参与式（body language）**。
- 编有开放 PDF 文集《Emotional Cartography》(2008)，收艺术家/设计师/神经科学家论文。
- 来源：[biomapping.net](http://biomapping.net/)、[softhook.com/emot.htm](http://www.softhook.com/emot.htm)、[3 Quarks Daily](https://3quarksdaily.com/3quarksdaily/2009/05/emotional-cartography-christian-nold-and-william-blakefrom-the-indispensable-psychology-and-neurosci.html)、[UW Now Urbanism](https://uwcitiescollab.wordpress.com/2011/12/14/emotional-cartography/)。

### 3.3 Kate McLean — Sensory / Smell Maps（2010–）★非视觉通道范例
- 用"smellwalk"和"sensory ethnography"（街头访问居民）采集气味，做成两类产物：(1) 纯视觉气味地图——**刻意删除街名、地标、河流、公园**，只用气味点+色彩等高线暗示空间；(2) 装进香水瓶的实体气味，陈列在视觉地图下方。
- 手法集大成：**声音/嗅觉（sensory）+ 实体物化（tangible）+ 留白去底图 + 等高线挪用 + 参与式标注**。
- 核心主张：世界"强烈偏向视觉与听觉信息"，气味地图是一种**纠偏**；气味与记忆、情绪紧密相连。
- 来源：[WIRED](https://www.wired.com/story/smell-maps/)、[ArchDaily](https://www.archdaily.com/985983/sensory-maps-what-the-sense-of-smell-can-reveal-about-urban-environments)、[The Common](https://www.thecommononline.org/sensory-maps/)、[Amex Essentials](https://www.amexessentials.com/kate-mclean-interview-smellscape-smellmap-sensory-map/)。

### 3.4 女书信息可视化 / 女书文化
- 女书是**世界上唯一仍在使用的女性专用文字**（湖南江永），长菱形"长脚文"，仅点/竖/斜/弧四种笔画，表音，多写在三朝书、歌扇、帕书、绣字上，七言诗体，题材多为婚姻、私情、逸闻。字形"斜体修长、阴柔之美"——**字体本身即情绪/性别表达（typeface 手法）**。
- 谭盾《女书》微电影音乐史诗（2013）：12 个长镜头微电影 + 费城交响乐团配乐，从人类学角度打造"女书视觉的交响乐"——**声音通道**的文化情感表达。
- 品牌 INTO YOU 曾以女书为核心做"自在出色"女性主题传播（互动海报等）。
- 说明：这些是女书的可视化/传播实践；任务所指那个具体"偏视觉设计向"的信息可视化作品未能定位到唯一一手页面（**具体作品未核实**），但女书作为素材的视觉特征已核实。
- 来源：[永州政府网·女书文化](https://www.yzcity.gov.cn/cnyz/nswh/202211/96d9eeef3842451db02b4edf1521437a.shtml)、[百度百科·女书](https://baike.baidu.com/item/%E5%A5%B3%E4%B9%A6/608945)、[设计在线](https://www.dolcn.com/archives/21717)。

### 3.5 《红楼梦情绪地图》APP（vibe coding 作品）— 未核实
- 任务描述其为把章节、贾府空间、人物出场、情绪变化做成可播放的文学地图，"光线随剧情由明转暗"表达宿命感。
- **多轮检索（社交媒体向关键词、独立开发者、vibe coding）均未找到该作品的一手页面**，搜索命中的是《红楼梦》情感分析可视化（Flask+SnowNLP+ECharts 折线图，非地图）、思维导图、galgame 等无关物。**该作品可能只存在于社交媒体短视频，无法抓取正文，标未核实。**
- 可佐证的背景（非作品本身）：红楼梦结构本身确有"由盛转衰"的四段式（前 18 回序幕→鼎盛→抄检大观园转折→查抄衰败），命运基调"白茫茫大地真干净"——"光线由明转暗"与文本命运曲线吻合，是合理的设计动机。来源：[中国青年作家报·红楼梦结构](http://qnzj.cyol.com/html/2020-12/01/nw.D110000qnzjb_20201201_1-08.htm)。

### 3.6 《世界女神图鉴》互动地图（vibe coding 作品）— 未核实
- 任务描述其为 298 位跨文化女神的互动地图，可搜索简介、影响范围、**听原语言发音**、按文化地区筛选。
- **检索未找到该作品一手页面**（命中的是萌娘百科"女神"词条、上科大通识课、游戏《女神领域》等无关物）。**标未核实。** 其"原语言发音"若属实，属于第一节"声音（sound）"手法在文化地图上的应用。

### 3.7 批判制图 / 反抗式制图（理论+实践背景）
- **Counter-mapping / critical cartography**：反对"地图是客观中立"的传统观，主张地图历来服务于统治阶级利益。代表团体：Iconoclasistas（阿根廷，2008 起以"集体制图"为主要介入形式，发展"象形语法/pictographic grammars"）、Bureau d'Études（法国）、Counter-Cartographies Collective（美国）、kollektiv orangotango。手法：把被主流地图排除的东西（剥夺、抗争、街头骚扰、多样性）画出来，常用符号/隐喻+尺度扭曲+拼贴。
- 来源：[Wikipedia: Critical cartography](https://en.wikipedia.org/wiki/Critical_cartography)、[notanatlas.org PDF](https://notanatlas.org/wp-content/uploads/2018/11/Counter-Cartographies_-Politics-Arts-and-the-Insurrection-of-Maps-.pdf)、[Adventure Uncovered](https://adventureuncovered.com/stories/meet-the-counter-cartographers-using-maps-as-a-tool-for-social-change/)、[SciELO Brazil](https://www.scielo.br/j/vb/a/d5NBLRYxZqkY44rBQLddMGh/?lang=en)。

---

## 四、"氛围"和"信息"的冲突：谁明确讨论过 trade-off

有多方明确讨论，结论一致——**强氛围表达牺牲可读性/精确性，且这常常是主动的设计选择：**

1. **IEEE VIS 2025 论文**（最权威）：把 trade-off 编码进 Place 的解释层级。记忆化地点"认知压缩/情绪放大/时序错乱"、心理化地点"不受物理规律或历史准确性约束"；情感设计"偏好非效率探索、具象而非抽象"。来源：[arXiv:2507.11841v1](https://arxiv.org/html/2507.11841v1)。
2. **Victorian London**：明确承认牺牲精确地理（引文按地点聚簇，"不是精确再现"）。来源：[Hyperallergic](https://hyperallergic.com/using-fiction-to-retrieve-the-emotional-geography-of-victorian-london/)。
3. **Kate McLean**：主动**删掉**街名/地标/河流等常规制图要素，用气味取代地理——极端的"氛围压倒信息"。来源：[The Common](https://www.thecommononline.org/sensory-maps/)。
4. **地理学的 Griffin & McQuoid (2012)**："At the Intersection of Maps and Emotion: The Challenge of Spatially Representing Experience"——标题即点明"空间再现体验"的挑战。（来源见搜索命中的学术引用，[Academia PDF](https://www.academia.edu/39608958/Mapping_Emotional_Cartography)，单源，未核实全文。）

**共识**：这个矛盾不需要"解决"，而是按目的取舍——导航/分析型地图重精度，情感/文学型地图重氛围与在场感。

---

## 五、女性主义地理学为何与情感地图强相关（简短，够用）

核心主张：**传统制图把"人的经验"等同于"男性经验"，否认或轻视女性经验；地图的"客观、理性、去身体化"话语本身就是一种排除。** Anderson & Smith 提出"emotional geographies"时说："忽略情感，就是排除了生活得以展开、社会得以形成的一整套关键关系。"（论文引用）

因此女性主义地理学把**情感、身体、主观、日常、被忽视者的声音**重新引入地图——这与"把情感画在地图上"是同一诉求的两面。这也解释了为什么用户给的清单里女性文学地图密集：女书、女神图鉴、女性主义制图，都是"为被主流制图排除的女性经验发声"。

- 佐证：feminist cartography 研究发现地图的"去身体化和理性修辞"确实排除女性经验（[ResearchGate](https://www.researchgate.net/publication/337262271_Feminist_cartography_and_the_United_Nations_Sustainable_Development_Goal_on_gender_equality_Emotional_responses_to_three_thematic_maps)）；"carto-fiction"主张在制图**过程中**书写主观反思（[ACME Journal PDF](https://acme-journal.org/index.php/acme/article/download/2083/1651/12178)）。斯坦福图书馆把 Feminist geography 列为 counter-mapping 的核心主题词（[Stanford Guide](https://guides.library.stanford.edu/countermapping)）。
- 与 IEEE VIS 论文呼应：论文强调情感地图聚焦"具体身份的人"（居民、难民、原住民——80.6%），而非泛化"用户"，正是女性主义地理学"具身、有身份的经验"主张的可视化落地。

---

## 六、感官通道：非视觉通道（声音/发音）的价值与我们的取舍

**用了非视觉通道的项目：**
- Kate McLean 气味/触觉地图（嗅觉+实体触觉，见 3.3）——效果：调动身体记忆，"闻到才想起"，但**只能在展览现场，无法数字分发**。
- 谭盾《女书》交响乐（听觉，见 3.4）——用原生态歌谣+配乐承载女性哀婉。
- IEEE VIS 语料中 sound 出现 7 次，是承认但非主流的手法（远低于色彩 24、标注 33）。
- 《世界女神图鉴》原语言发音（未核实）——若属实，是"声音承载文化真实性"的典型。

**效果**：声音/发音带来两样视觉给不了的东西——(1) **文化真实性**（听到原语言=听到"她自己的声音"）；(2) **具身沉浸/情绪记忆**（气味、声音直连情绪记忆）。

**我们项目明确不做音效，会损失什么：**
- 损失"原语言发音"这类**文化在场感**（尤其涉及女性文字/女神这类"她的声音"主题时，损失较明显）。
- 损失声音带来的**时间性节奏**（如剧情推进的环境音渐变）。

但这一损失**可控且可补偿**——因为在 IEEE VIS 62 作品语料里，声音本就是低频手法（7/62），情感表达的主力是**色彩(24)、标注/引语(33)、写实图像(18)、符号隐喻(17)**，全是视觉手法。放弃音效不会动摇情感表达的根基。

---

## 七、对 Lemi's Diary 的启示

我们的既定风格：**手账拼贴视觉 + 白天/夜晚两段光照 + 不做音效**。对照上述手法：

**已经踩在最强手法上（继续做深）：**
- **拼贴（collage, n=10）**：手账拼贴天然命中论文的 Narratives 策略，是"主观、有温度、手作感"的正解。建议加强**素材层次与手写标注**，因为"标注内容/关联故事"是论文里**最高频（33/62）**的情感手法。
- **明暗/色彩（color, n=24，最高频感官手法）**：白天/夜晚两段光照直接对应《红楼梦情绪地图》"由明转暗"的命运表达，也对应 Victorian London 的 Dreadful/Light 分区。这是我们最大的优势，应把光照做成**可随内容情绪推进的渐变**（对应"动画/时间性"手法），而非仅两个静态档。

**应该补的（低成本、高情感回报）：**
1. **第一人称引语/标注**（annotated content，论文最高频手法）——在地点上挂手写的日记片段/引语。这是**替代音效损失的最佳补偿**：用文字承载"她的声音"。
2. **留白与遮蔽**（McLean 手法）——没被记录/未解锁的地方留白或做旧、模糊，用"缺失"表达情绪，成本极低。
3. **尺度扭曲/重点放大**（layout, n=3；批判制图常用）——把情感重要的地点画大，弱化次要空间，强化手账的主观性。
4. **符号/隐喻**（n=17，占 27.4%）——手账贴纸天然是隐喻载体，用象征物（花、信、月亮）替代标准图钉。

**可以放心放弃的：**
- **音效**：如第六节所述，声音在语料里本就低频（7/62），视觉手法足以撑起情感。放弃它换取更轻的产品体验是合理取舍——**但要用"手写引语+光照渐变+留白"三件套补上它本可承载的文化在场感与时间节奏。**
- **生理数据/实体物化/参与式采集**（Nold、McLean 的重资产手法）——与手账产品形态不符，无需追。

**一句话**：我们的"拼贴+双段光照"已站在论文验证的两大最强手法（标注叙事 + 色彩）之上；补齐"第一人称引语、留白遮蔽、尺度扭曲、隐喻贴纸"即可，音效可安全舍弃。

---

## 八、局限与缺口

1. **62 个作品逐条清单未拿到**：作品集网站 https://affectivegeovis.github.io 是 JS 单页应用，脚本抓取只得空壳，无法列出 62 件作品明细。分类体系、频次、范式来自论文正文（可靠），但**具体哪 62 件、各用什么手法的一一对应未核实**。
2. **《红楼梦情绪地图》APP 未核实**：多轮检索无一手页面，疑似仅存于社交媒体短视频。"光线由明转暗"这一具体手法**无法从一手来源确认**，本报告仅按任务描述转述并标注。
3. **《世界女神图鉴》未核实**：同样无一手页面，"298 位/原语言发音/文化筛选"均按任务描述转述，标注未核实。
4. **女书具体"信息可视化作品"未定位到唯一一手**：女书文化背景已核实，但那个"偏视觉设计向"的特定作品未找到。
5. **Griffin & McQuoid (2012)** 关于"地图与情感交叉挑战"仅见二手引用，未读全文（单源）。
