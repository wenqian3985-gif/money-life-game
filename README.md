# 未来マネークエスト

0～17歳の実年齢から始められる、親子向け金融教育Streamlit人生ゲームです。社会人になる年齢、夢の職業、金融商品の配分、リバランスを自分で決め、65歳までを1年単位でシミュレーションします。

## 主な機能

- 子どもの実年齢（0～17歳）と社会人になる年齢（18～30歳）を設定
- 最初の一括投資金額を0～100万円で設定し、初回に毎月投資と同じ商品割合へ分配
- 2027年1月開始予定の「こどもNISA」を学習用に反映（年60万円、総枠600万円）
- 現金、債券・バランス投信、世界株インデックス、個別株、暗号資産・FXの説明と割合設定を一体化
- 毎月の投資金額と5商品の目標配分を自由入力し、毎年リバランスするか選択
- 子どもに人気の10職種から夢を選択し、就職1年目モデル年収・公開参考年収・ゲーム内到達確率を表示
- 公開平均年収を初任給として使わず、年齢・就業年数に応じて年収と手取りを更新
- 職業の年収から所得税・住民税・社会保険料を概算し、毎月の手取りを自動表示
- 家賃、光熱費、通信費、食費、交際費、交通費、その他、投資を手取りの範囲で設定
- 就職後は各年齢ステップで手取りの使い道を見直し
- 学びへの支出でゲーム内の職業到達確率が上昇
- 年齢別の積み上げ棒グラフと「積立・配分調整・値動き・イベント」の増減理由
- 借金が生じた支出・借入と、年4%の利息による増加理由を表示
- 「前のステップに戻る」で、直前の年齢区間や職業選択へ戻る
- アニメーションするリスのガイド、絵文字、色分けカード

## 起動方法

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## テスト

```bash
python -m pytest -q
```

## Streamlit Community Cloud

- Repository: `wenqian3985-gif/money-life-game`
- Branch: `main`
- Main file path: `app.py`

## 参考情報

- [金融庁「こどもNISA」](https://www.fsa.go.jp/access/r7/270.html)
- [日本FP協会「小学生『夢をかなえる』作文コンクール なりたい職業ランキング」](https://www.jafp.or.jp/personal_finance/yume/syokugyo/)
- [厚生労働省 職業情報提供サイト job tag](https://shigoto.mhlw.go.jp/)
- [厚生労働省「令和7年賃金構造基本統計調査」](https://www.mhlw.go.jp/toukei/itiran/roudou/chingin/kouzou/z2025/index.html)
- [JILPT「新規学卒者の賃金」](https://www.jil.go.jp/kokunai/statistics/shuyo/0303.html)
- [Jリーグ「選手契約制度の改定」](https://www.jleague.jp/news/article/28943/)
- [国税庁「給与所得者と税」](https://www.nta.go.jp/publication/pamph/koho/kurashi/html/02_1.htm)
- [日本年金機構「厚生年金保険料額表」](https://www.nenkin.go.jp/service/kounen/hokenryo/ryogakuhyo/index.html)
- [協会けんぽ「令和8年度保険料額表」](https://www.kyoukaikenpo.or.jp/about/business/insurance_rate/premium_prefectures/r08/index.html)
- [PIVOT「投資歴30年パックンが教える最強の投資法」](https://www.youtube.com/watch?v=U35WMjyVdmI)

## 注意

このアプリは金融教育用の架空シミュレーションです。相場、職業到達確率、一部の参考年収は学習用に単純化しており、投資成果・就職・収入を予測または保証しません。制度や対象商品は変更される可能性があるため、実際の利用時は金融庁・取扱金融機関の最新情報を確認してください。
