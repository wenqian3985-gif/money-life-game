"""Game content for the child-friendly financial life simulation."""

PROFESSIONS = [
    {
        "name": "ものづくりエンジニア",
        "emoji": "🛠️",
        "salary": 360,
        "growth": 0.035,
        "message": "技術を磨くほど、できる仕事が増えていく職業です。",
    },
    {
        "name": "デザイナー",
        "emoji": "🎨",
        "salary": 310,
        "growth": 0.04,
        "message": "アイデアと経験が収入につながる職業です。",
    },
    {
        "name": "セールスプランナー",
        "emoji": "🤝",
        "salary": 340,
        "growth": 0.04,
        "message": "人の困りごとを見つけ、解決する力が大切な職業です。",
    },
    {
        "name": "ケアワーカー",
        "emoji": "🌱",
        "salary": 300,
        "growth": 0.03,
        "message": "人を支えることが社会の価値になる職業です。",
    },
    {
        "name": "フードクリエイター",
        "emoji": "🍳",
        "salary": 320,
        "growth": 0.035,
        "message": "工夫と信用がリピーターを生む職業です。",
    },
]


LIFE_STAGES = [
    {
        "age": 18,
        "next_age": 25,
        "label": "社会人スタート",
        "living_cost": 210,
        "event": {
            "title": "初任給で何を買う？",
            "description": "友達が最新スマホを買いました。あなたも10万円の新機種が気になります。",
            "options": [
                {
                    "key": "new_phone",
                    "label": "最新機種を買う（10万円）",
                    "effect": {"cost": 10, "happiness": 8},
                    "lesson": "今の満足も大切。ただし、使ったお金は将来増える可能性を失います。",
                },
                {
                    "key": "used_phone",
                    "label": "中古機種を買う（4万円）",
                    "effect": {"cost": 4, "happiness": 5, "knowledge": 2},
                    "lesson": "満足と支出のバランスを取るのも立派な選択です。",
                },
                {
                    "key": "keep_phone",
                    "label": "今の機種を使い続ける",
                    "effect": {"knowledge": 3},
                    "lesson": "買わない選択は、未来に使えるお金を残します。",
                },
            ],
        },
    },
    {
        "age": 25,
        "next_age": 35,
        "label": "暮らしをつくる",
        "living_cost": 245,
        "event": {
            "title": "住まいをどう選ぶ？",
            "description": "便利で広い部屋と、少し遠いコンパクトな部屋。家賃は毎月かかります。",
            "options": [
                {
                    "key": "premium_home",
                    "label": "駅近の広い部屋に住む",
                    "effect": {"cost": 35, "happiness": 10, "budget_modifier": -0.10},
                    "lesson": "高い家賃は満足を生みますが、毎年の自由資金を減らします。",
                },
                {
                    "key": "standard_home",
                    "label": "価格と便利さのバランスを取る",
                    "effect": {"cost": 15, "happiness": 6},
                    "lesson": "固定費は長く続くため、一度の買い物以上に影響があります。",
                },
                {
                    "key": "compact_home",
                    "label": "家賃を抑えた部屋に住む",
                    "effect": {"cost": 8, "happiness": 2, "budget_modifier": 0.06, "knowledge": 2},
                    "lesson": "固定費を抑えると、毎年選べるお金が増えます。",
                },
            ],
        },
    },
    {
        "age": 35,
        "next_age": 45,
        "label": "守りを考える",
        "living_cost": 275,
        "event": {
            "title": "保険をどう考える？",
            "description": "もしもの出費に備えたい一方、保険料を払いすぎると投資や貯金に回せません。",
            "options": [
                {
                    "key": "simple_insurance",
                    "label": "必要な分だけ入る（10万円）",
                    "effect": {"cost": 10, "insurance": 1, "knowledge": 4},
                    "lesson": "起きたら困る大きな損失に、必要な範囲で備える考え方です。",
                },
                {
                    "key": "heavy_insurance",
                    "label": "心配なのでたくさん入る（30万円）",
                    "effect": {"cost": 30, "insurance": 2, "happiness": 2},
                    "lesson": "安心は増えますが、保険料にも機会費用があります。",
                },
                {
                    "key": "no_insurance",
                    "label": "保険に入らず、現金で備える",
                    "effect": {"insurance": 0, "knowledge": 1},
                    "lesson": "十分な緊急予備費があるなら選択肢になりますが、大きな出費には注意が必要です。",
                },
            ],
        },
    },
    {
        "age": 45,
        "next_age": 55,
        "label": "予想外に備える",
        "living_cost": 285,
        "event": {
            "title": "突然の大きな出費！",
            "description": "病気と家の修理が重なり、80万円が必要になりました。保険があれば負担が軽くなります。",
            "intro_effect": {"cost": 80, "insurable": True},
            "options": [
                {
                    "key": "rebuild_cash",
                    "label": "生活を少し見直し、予備費を戻す",
                    "effect": {"happiness": -3, "budget_modifier": 0.05, "knowledge": 4},
                    "lesson": "現金の予備費は、投資を安値で売らずに済むクッションになります。",
                },
                {
                    "key": "learn_side_job",
                    "label": "10万円で副業スキルを学ぶ",
                    "effect": {"cost": 10, "skill": 12, "knowledge": 3},
                    "lesson": "自分の力への投資は、将来の収入を増やす可能性があります。",
                },
                {
                    "key": "refresh_trip",
                    "label": "20万円で気分転換の旅行をする",
                    "effect": {"cost": 20, "happiness": 10},
                    "lesson": "お金は人生を楽しむためにも使います。無理のない範囲かを確認しましょう。",
                },
            ],
        },
    },
    {
        "age": 55,
        "next_age": 65,
        "label": "未来を仕上げる",
        "living_cost": 260,
        "event": {
            "title": "『必ず2倍』の投資話",
            "description": "SNSで知り合った人が『絶対に損しない。今だけ』と勧めてきました。",
            "options": [
                {
                    "key": "accept_scam",
                    "label": "チャンスだと思い40万円を渡す",
                    "effect": {"cost": 40, "happiness": -8},
                    "lesson": "『必ずもうかる』『今だけ』は危険信号。高い利益に保証はありません。",
                },
                {
                    "key": "ask_expert",
                    "label": "家族や専門家に相談する",
                    "effect": {"cost": 2, "knowledge": 8, "happiness": 2},
                    "lesson": "一人で即決せず、信頼できる人と情報源を確認することが防御になります。",
                },
                {
                    "key": "decline_scam",
                    "label": "断ってブロックする",
                    "effect": {"knowledge": 6},
                    "lesson": "うますぎる話から離れる判断も、お金を守る立派な行動です。",
                },
            ],
        },
    },
]


QUIZZES = [
    {
        "question": "図書館の本は、社会全体で見ても完全に0円？",
        "options": ["はい。誰もお金を払っていない", "いいえ。税金などで運営されている", "本によって違う"],
        "correct": 1,
        "explanation": "利用時は無料でも、建物・本・働く人の費用は税金などから支払われます。",
    },
    {
        "question": "年7.2%で複利運用できたと仮定すると、72の法則では約何年で2倍？",
        "options": ["約5年", "約10年", "約20年"],
        "correct": 1,
        "explanation": "72 ÷ 7.2 = 10。実際の運用成績は毎年変わり、2倍を保証する式ではありません。",
    },
    {
        "question": "一般に、大きなリターンを狙う商品ほどどうなる？",
        "options": ["損する可能性も大きくなる", "必ず早く増える", "値段が動かなくなる"],
        "correct": 0,
        "explanation": "高いリターンの可能性と、大きく損する可能性は表裏一体です。",
    },
    {
        "question": "物価が毎年2%ずつ上がると、同じ100万円で買える量は長期的にどうなる？",
        "options": ["増える", "変わらない", "減る"],
        "correct": 2,
        "explanation": "現金の数字が同じでも、物価が上がると買えるものは少なくなります。",
    },
    {
        "question": "『元本保証で、半年後に必ず2倍』と言われたら最初にすることは？",
        "options": ["すぐ申し込む", "借金して増額する", "断り、信頼できる人や公的情報で確認する"],
        "correct": 2,
        "explanation": "『必ず』『今だけ』と急がせる話は詐欺を疑い、まず距離を取りましょう。",
    },
]


STRATEGIES = {
    "steady": {
        "name": "🛡️ じっくり安心型",
        "description": "使う20%・現金45%・インデックス30%・個別株5%",
        "allocation": {"enjoy": 20, "cash": 45, "index": 30, "stock": 5, "challenge": 0, "skill": 0},
    },
    "balanced": {
        "name": "⚖️ バランス型",
        "description": "使う20%・現金20%・インデックス45%・個別株10%・挑戦資産5%",
        "allocation": {"enjoy": 20, "cash": 20, "index": 45, "stock": 10, "challenge": 5, "skill": 0},
    },
    "self_growth": {
        "name": "🚀 自分も育てる型",
        "description": "使う15%・現金15%・インデックス35%・個別株5%・学び30%",
        "allocation": {"enjoy": 15, "cash": 15, "index": 35, "stock": 5, "challenge": 0, "skill": 30},
    },
    "thrill": {
        "name": "🎢 ハイリスク挑戦型",
        "description": "使う25%・現金5%・インデックス20%・個別株20%・暗号資産/FX30%",
        "allocation": {"enjoy": 25, "cash": 5, "index": 20, "stock": 20, "challenge": 30, "skill": 0},
    },
}

