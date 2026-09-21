# F. 失败模式与可持续性(主控亲自核实)

## F1. 数字人文项目的死亡率:有硬数据

### 证据 1:数字学术版本的寿命
Schildkamp & Mathiak (2019) 用 Internet Archive 比对首见版本与最后可见版本:

> "of 466 digital editions, 376 had disappeared"
> "The average life time is 8.5 years, while the half life time is about 6 years."

即 **466 个中 376 个已消失(80.7%)**,平均寿命 8.5 年,半衰期约 6 年。
消失原因原文列举:"diminishing funding, lack of institutional support and, over time, lack of personnel support"(经费递减、缺机构支持、人员流失——研究者转岗或转方向)。

来源:[Sustainability Strategies for Digital Humanities Systems (DH2020)](https://dh2020.adho.org/wp-content/uploads/2020/07/565_SustainabilityStrategiesforDigitalHumanitiesSystems.html)

### 证据 2:DH 项目的"货架寿命"
Meneses & Furuta,*Shelf life: Identifying the abandonment of online digital humanities projects*(DSH, 2019)。方法:从 2006-2016 年 DH 会议论文摘要集中解析出 **5,845 个唯一 URL**,用 Python Requests 取 HTTP 响应码,分为 valid 与 decayed 两类;**HTTP 重定向被视为衰退的早期指标**。

> "we approximate the average shelf life of a digital humanities project to 5 years—which aligns with reports from previous work."

原因:"loss of funding, change in personnel or simply decay in interest"。
作者自述该研究为 exploratory / preliminary,且仅分析首页。

来源:[Shelf life (Digital Scholarship in the Humanities)](https://academic.oup.com/dsh/article/34/Supplement_1/i129/5270841)

### 证据 3:中文语境下的同一诊断
> "又因为数字人文项目拿的是国家的钱,所以就按学术考核、职称晋升那一套标准走。当项目完结,平台也就宣告死亡。数字人文成果和著作成果不一样,著作可以通过出版社不断重印继续供其他人使用,应用平台却需要创建者长期持续维护。"

来源:[数字人文基础设施的意义和技术实践 — 地图书知识库](https://www.ditushu.com/book/43/forum/108)

### 证据 4:Harvard 的应对框架(2026-01)
哈佛图书馆保存服务部门明确提出要为项目"sunset / sustain / preserve"三条路做决策框架,并指出:

> "The recurring refrain in digital humanities over the years has been 'plan for sunsetting or sustaining intentions at the project outset.' Faculty are often unaware of the total costs of stewardship associated with maintaining projects and do not account for those recurring costs after the active project phase."

来源:[Experiments in sustainable digital humanities projects (Harvard Preservation Services, 2026-01)](https://preservation.library.harvard.edu/news/2026/01/experiments-sustainable-digital-humanities-projects)

---

## F2. 一个活下来的反例:唐宋文学编年地图

这是本轮最有价值的对照。

| 事实 | 证据 |
|---|---|
| 2012 年立项(国家社科基金重大招标项目《唐宋文学编年系地信息平台建设》),团队超百人,历时 5 年 | 搜索摘要,[地图书](https://www.ditushu.com/book/27/)(页面为 JS 渲染,正文未能抓取,**标为摘要级证据**) |
| 2017 年 3 月在**搜韵网**上线;上线两天点击量超 220 万 | 同上 + [唐宋文学编年地图上线(媒体报道)](http://m.toutiao.com/group/6439455804188868865/) |
| 上线时报道为 **151 位**诗人;用户提供的资料为 **360 余位** | 两者差值即证明项目上线后持续扩充(报道明确写"目前该地图正值试用期,更多唐宋文学家的资料会不断上传") |
| 技术开发由搜韵网负责,"为相关研究者和诗词爱好者提供**长期稳定的免费服务**" | [地图书](https://www.ditushu.com/book/27/)(摘要级) |
| 搜韵网成立于 2009 年,全球超 500 万用户,日活超 4 万 | 同上(摘要级) |
| **2026-09-21 主控实测:`sou-yun.cn/PoetLifeMap.aspx` 返回 HTTP 429(限流),非 404** | 主控 curl 实测 |

**429 而非 404 是关键**:限流意味着服务活着且有真实流量。该平台已运行 **9 年半**,远超"平均 5 年"与"半衰期 6 年"。

**它为什么活下来(可检验的机制,非猜测)**:
技术平台不挂在课题经费或某位研究者的职位上,而是**托付给一个有独立商业生命的高流量站点**(搜韵网,2009 年至今,500 万用户)。课题结项不影响平台存续。
2022 年 8 月又经联合授权把数据发布到地图书知识库,提供可视化地图、知识图谱和 **API 接口** —— 即**数据与展示解耦**,数据可被再利用,不随某一个前端的死亡而消失。

---

## F3. 对 Lemi's Diary 的直接启示

### 启示 1:我们的技术选型已经在正确的一侧
我们是**纯静态站**:无后端、无数据库、无账号、无 API key。这正是"planned for sustaining"的最强形态——
- 无服务器可关停;无数据库可损坏;无依赖服务可涨价
- 只要托管方(GitHub Pages)活着,站点就活着;即使不活,`dist/` 目录可原样搬到任何静态托管
- 对照 Schildkamp & Mathiak 列出的三大死因(经费递减/缺机构支持/人员流失),纯静态站对**前两条完全免疫**

这不是事后合理化:v1 就定下"纯静态、无后端"约束,现在有数据支持这个选择是对的。

### 启示 2:数据与展示必须解耦(我们做到了一半)
唐宋地图能活,部分因为数据可经 API 被再利用。我们的现状:
- ✅ 内容以 JSON 存在 `content/`,与前端解耦,Python 管线生成 `dist/`
- ✅ 已验证内容独立记录在 `content/VERIFIED_CONTENT.md`,前端死了内容还在
- ⚠️ **但我们没有数据导出口**。参考项目「大地之书」支持导出 PNG 和 GeoJSON

**建议**:v3 增加一个极低成本的导出 —— 卡册页提供"导出我的收集(JSON)"。成本几行代码,收益是数据不被锁在 localStorage 里。

### 启示 3:「点击量高但留存差」是这个品类的典型病
唐宋地图两天 220 万点击,这是**上线爆发**,不是留存。我未找到该项目的留存数据(明确标为缺口)。
但这个模式值得警惕:文化类地图项目容易靠新奇感获得一次性流量,然后无人回访。

**这恰恰是我们做集卡玩法的正当性**:v1 是"7 POI × 5 字段 = 35 个信息块"的信息清单,看一次就没有第二次理由打开。大富翁 + 集卡给出了回访理由(卡册没集满)。
反过来说,**如果集卡设计得让人集满一次就走,我们就又回到了"高点击低留存"**。这是 E 路调研(收集机制)要回答的问题。

### 启示 4:80.7% 的消失率意味着「可归档性」本身是设计目标
纯静态站的额外好处:**可被 Internet Archive 完整抓取**。
一个依赖后端 API 的地图,Wayback Machine 抓下来是坏的;纯静态站抓下来能用。
这对一个文化内容项目是真实价值 —— 我们做的内容(已交叉验证的巴黎街头知识、有出处的引语)本身有留存价值。

---

## F4. 局限与缺口(诚实记录)

- **AIUCD 2025 "Life and Death of DH Projects" 论文正文未能获取**:PDF 为图像型,文本层无法解出。搜索摘要提到"academic projects are 4.15 times more likely to sustain their digital resources than non-academic ones"和"68% of early funded projects",**这两个数字我未能在原文核实,故不采用**。
- **地图书 `/book/27/` 页面为 JS 渲染**,正文未能抓取。该页相关事实(立项年份、团队规模、搜韵网用户数、"长期稳定免费服务"表述)**仅为搜索摘要级证据**,已在表格中标注。
- **唐宋地图的留存数据不存在于公开资料**。220 万是上线两天点击量,不能推断留存。
- **sou-yun.cn 返回 429**,我未能读到页面内容,因此"360 位诗人"这个当前数字未经一手核实;只能确认服务在线。
- 未找到任何文学地图项目公开发布过留存率 / DAU / 回访率数据。这类数据在学术项目中通常不被采集或不被公开。

---

## F5. 圆周旅迹核查结果(主控亲验,修正 A 路的悬案)

A 路调研未能核实"香港女作家文学散步地图""台湾文学圣地巡礼地图"是否存在。我补查后可以确定性更高地结论:

**圆周旅迹(PiTravel)是通用智能行程规划 App**,开发者超超世世科技(上海)有限公司,App Store 中国区旅游榜 #11,2848 个评分 4.6 分,最新版 5.12.0(2026-09-20 更新)。
来源:[App Store 页面](https://apps.apple.com/cn/app/id6473148424)、[应用宝](https://sj.qq.com/appdetail/com.chaochaoshishi.slytherin)

**其官方功能列表(完整)**:一键复刻全网攻略(解析小红书/公众号链接抽取地点)、智能规划定制路线、好友共同编辑、附近地点精选推荐、**「地点精选专题」(编辑部每周更新)**。

**结论**:官方功能里**没有任何文学主题地图**。用户列表中的两张"文学地图"极可能是其**「地点精选专题」运营内容**(官方文案明确该栏目分类为"周边推荐/吃点好的/出门转转/有点意思/买买必去/当季限定"),或小红书账号图文。**不构成一个"文学地图产品"**,A 路标为未核实是正确的。

### 但查到了更有价值的东西:圆周旅迹的「足迹打卡」机制

官方文案(多个应用商店一致):

> **【足迹打卡】个人地理日记本**,记录生活,探索世界…在地图上查看打卡足迹。想了解你对世界的探索程度?立刻开始打卡记录,**解锁点亮地图**,留下属于你走过世界的痕迹。

另一处版本文案提到:

> **「足迹星图」系统**,用渐变光点标记你的探索轨迹
> **世界地图探索度统计**:用热力图显示足迹分布,**标记未探索大陆板块**

来源:[下么软件园(v2.0.1 文案)](https://www.xiame.com/app/8090.html)、[多多软件站(v3.12.1 文案)](https://m.ddooo.com/softdown/146429.htm)
注:应用商店的第三方站文案属转载,但多站一致且与 App Store 官方描述风格吻合,**交叉验证通过**;"足迹星图"为特定版本文案,标为 `(单站来源,未二次核实)`。

**这是「迷雾探索 / 点亮地图」机制**,由一个成熟商业产品在用。核心是**让用户看见自己还没去过哪里**——与"未获得卡显示剪影"是同一心理机制,但作用面不同:

| | 作用对象 | 我们的现状 |
|---|---|---|
| 剪影卡位 | **卡册**(收集品清单) | ✅ 已设计 |
| 点亮地图 / 探索度 | **空间本身**(世界/城市/棋盘) | ❌ 未设计 |

### 对 Lemi's Diary 的直接建议(低成本)

我们的三层空间结构是「世界地图 → 城市 → 故事线棋盘」,其中世界地图层本期不做。但**"探索度"可以极低成本地补在已有界面上**:

1. **棋盘层**:走过的格子已有 `visited` 视觉区分(v2 已实现)。可再加一条"本条故事线 n/20 格"的进度。
2. **城市层**:巴黎 3 条故事线,本期仅 1 条可玩。卡册里 SSR 位已显示 `n/3` 碎片进度——**这其实就是城市探索度**,只是没说成"探索度"。建议在文案上显式化("巴黎 · 已解锁 1/3 条故事线")。
3. **未来世界层**:若做城市选择页,未解锁城市应显示为**暗色剪影**而非隐藏——同一机制复用。

这条与 A 路启示 3(随机化降低选择成本)、E 路待验的收集机制形成一套:**看见缺口(剪影/暗色)→ 降低决策成本(骰子/随机)→ 给出完成反馈(进度/探索度)**。
