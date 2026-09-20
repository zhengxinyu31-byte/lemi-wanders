# 内容验证结果(已通过交叉验证 + 对抗性审查)

用于填充 content/street/ 与 content/cards/ 的 quote 字段。
所有条目 verified=true 的依据记录在此,便于日后复核。

## 街头卡 5 条(全部通过)

### paris-cafe-pricing (rule)
- text_zh: 在巴黎的咖啡馆,同一杯咖啡的价格看你在哪儿喝:站在吧台(au comptoir)通常最便宜,坐店内(en salle)贵一点,坐露台(en terrasse)最贵。这不是宰客——价目表按法规必须公示,不同区域标不同价是合法惯例,不会额外加"服务费"到账单上。
- text_en: At a Paris café, the same coffee costs differently depending on where you have it: cheapest standing at the bar (au comptoir), more sitting inside (en salle), most on the terrace (en terrasse). It's not a scam — prices must be posted by law, and charging different rates by area is a legitimate practice, with no separate "service" line added to your bill.
- near_poi_id: cafe-de-flore
- sources:
  - https://inlovewithfrance.com/8321/the-love-france-guide-%E2%84%96-005-cafe-bistro-etiquette/
  - https://frenchtoenglish.com/french-cafe-culture-rules-etiquette/
- 措辞收紧:法律强制的是「明码标价公示」,不是「必须分级定价」。原先写成法律规定分级是错的。
  另有单一价小店,故用「通常」。

### paris-metro-doors (transit)
- text_zh: 巴黎地铁部分较旧车厢(如 MF67、MF77 车型)的车门到站不会自动开——你得自己按按钮,或扳起门上那个小金属把手用点力才能打开。别傻等门自动开。较新车型(如 14 号线及 2025 年起陆续投入的 MF19)则是自动门。
- text_en: On many older Paris metro cars (e.g. MF67, MF77 stock), the doors don't open automatically at a stop — you press a button or lift a small metal latch (and pull firmly). Don't just wait for them to open. Newer trains (like Line 14 and the MF19 rolling out from 2025) have automatic doors.
- near_poi_id: pantheon
- sources:
  - https://en.wikipedia.org/wiki/MF_77
  - https://www.urbansider.com/dos-and-donts-of-the-paris-metro/
- 措辞收紧:必须写「部分较旧车厢」。MF67/MF77 仍在运营,MF19 2025-10 才首上 10 号线,替换要到 2030 年代;
  14 号线全自动。一刀切说「巴黎地铁门要自己开」是错的。

### paris-bonjour (etiquette)
- text_zh: 在巴黎,进店、进咖啡馆、上出租车前,先对店员说一声"Bonjour"(天黑后说"Bonsoir")是基本礼貌,离开说"Au revoir"。不打招呼就直接开口问东西,常被当成没礼貌,对方态度可能明显变冷。加一句"s'il vous plaît"(请)更稳妥。
- text_en: In Paris, greet the staff with "Bonjour" ("Bonsoir" after dark) before you ask for anything in a shop, café, or taxi, and say "Au revoir" when leaving. Launching straight into a request without a greeting often reads as rude, and service may noticeably cool. Adding "s'il vous plaît" (please) helps.
- near_poi_id: place-estrapade
- sources:
  - https://www.afscv.org/blog/guide-to-french-etiquette/
  - https://www.afreno.org/post/the-most-important-word-in-french-is
- 措辞:用「常被当成」「可能变冷」,因反应因人而异,是社交观感非硬规则。

### paris-haussmann (trivia)
- text_zh: 巴黎大道两旁那种统一的米白色石砌六层楼房,多数是 1853-1870 年奥斯曼(Haussmann)改造留下的:当时规定沿新大道的建筑须用切割石材(多为本地的卢台西亚石灰岩),连楼高、阳台位置都有统一要求,才有了今天整齐划一的街景。
- text_en: Those uniform cream-colored six-story stone buildings lining Paris's boulevards mostly date from Haussmann's 1853-1870 overhaul: buildings along the new boulevards had to be built or faced in cut stone (usually local cream Lutetian limestone), with standardized heights and balcony placement — hence the harmonized streetscape you see today.
- near_poi_id: palais-garnier
- sources:
  - https://en.wikipedia.org/wiki/Haussmann%27s_renovation_of_Paris
  - https://study.com/academy/lesson/georges-eugene-haussmann-s-urban-renewal-of-paris.html
- 措辞收紧:用「多数」「沿新大道」。规定约束的是新辟大道沿线,不是全巴黎每栋楼。

### paris-wallace-fountain (trivia)
- text_zh: 巴黎街头那些墨绿色、顶上顶着四位女神像的铸铁小亭子叫"华莱士饮水泉"(Wallace Fountain),提供免费可直饮的自来水。它由英国慈善家 Richard Wallace 在 1870 年普法战争后捐资、1872 年起安装,一个多世纪后仍是免费喝水点,通常每年春末到秋季(约 3 月中至 11 月中)供水。
- text_en: Those dark-green cast-iron kiosks topped by four female statues on Paris streets are "Wallace Fountains," giving out free drinkable tap water. Funded by British philanthropist Richard Wallace after the 1870 Franco-Prussian War and installed from 1872, they still serve free water over 150 years later — typically from late spring to autumn (around mid-March to mid-November).
- near_poi_id: pont-alexandre-iii
- sources:
  - https://wallacefountains.org/about-sir-wallace-and-his-fountains/
  - https://www.francetraveltips.com/free-water-in-paris-wallace-fountains/
- 措辞:季节性供水,故用「通常…春末到秋季」,不能说全年。

## 被丢弃的街头卡候选
- 餐厅 service compris 无需小费:属实,但东京也不给小费 → 不满足「巴黎独有」
- 法棍 tradition française 法定标准:属实,但全法适用非巴黎独有

---

## 引语 4 条(7 个 POI 中仅 4 个通过)

### tour-eiffel
- text_original: J'ai quitté Paris et même la France, parce que la tour Eiffel finissait par m'ennuyer trop.
- text_zh: 我离开了巴黎,甚至离开了法国,只因为埃菲尔铁塔终究让我厌烦透顶。
- source: 莫泊桑《漂泊的一生》(La Vie errante) 首篇《Lassitude》开篇第一句,Ollendorff,1890
- source_url: https://fr.wikisource.org/wiki/La_Vie_errante_(Ollendorff,_1890)/Lassitude

### pantheon
- text_original: Aux grands hommes la patrie reconnaissante
- text_zh: 祖国感念伟人
- source: 先贤祠正立面山花楣镌刻铭文,源自 1791 年制宪议会法令
- source_url: https://fr.wikipedia.org/wiki/Panth%C3%A9on_(Paris)
- 备注:这是建筑铭文而非人物台词。可实地核对,无误传空间。

### jardin-palais-royal
- text_original: Nous ne regardons, nous ne regarderons jamais assez, jamais assez juste, jamais assez passionnément.
- text_zh: 我们从未看得够,永远看得不够,不够准确,不够热忱。
- source: 科莱特《我窗前的巴黎》(Paris de ma fenêtre),写于 1940-1944 年皇家宫殿寓所
- source_url: https://www.amisdecolette.fr/ressources/citations/
- 备注:句子偏长,手写体可截取前半句。

### palais-garnier
- text_original: Le fantôme de l'Opéra a existé.
- text_zh: 歌剧院的幽灵确曾存在。
- source: 加斯东·勒鲁《歌剧魅影》序言开篇第一句,Pierre Lafitte,1910
- source_url: https://www.livredepoche.com/livre/le-fantome-de-lopera-9782253009504/

## 留白的 3 个 POI(无合格引语,卡片不设手写体栏)
- place-estrapade:找不到可精确到季集且可核验的《艾米莉在巴黎》台词
- pont-alexandre-iii:无与此桥确有关联且有明确出处的引语
- cafe-de-flore:萨特名句只有二手站点互抄,查不到一手出处 → 按宁缺毋滥否决

## ⚠️ 已剔除的杜撰内容(重要)
**莫泊桑「每天在铁塔餐厅吃饭,因为那是巴黎唯一看不见铁塔的地方」= 杜撰。**
经 Quote Investigator 考证:1914 年最早安在 William Morris 头上,1975 年(洛杉矶时报)
才移花接木到莫泊桑名下,而莫泊桑 1893 年已去世。所有版本均为后人层层转贴,
查不到任何莫泊桑本人说过或写过的原始文献。**切勿使用。**
