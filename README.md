# 未来マネークエスト

小学校高学年〜中学生向けの、金融教育用Streamlit人生ゲームです。

18歳から65歳までの5ステージで、職業・給与・住まい・保険・突然の出費・詐欺対策・投資を疑似体験します。資産額だけを競うのではなく、「使う・守る・育てる・学ぶ」のバランスを親子で話し合う設計です。

## 学習テーマ

- キャッシュレス時代の「見えないお金」
- 複利と72の法則
- 現金、インデックス、個別株、暗号資産・FXのリスク差
- 家賃や保険などの固定費
- 緊急予備費と借金
- 「必ずもうかる」投資詐欺への対応
- 現在の満足と将来の機会費用

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

## Streamlit Community Cloudで公開

1. このフォルダをGitHubリポジトリへpushします。
2. [Streamlit Community Cloud](https://share.streamlit.io/)でリポジトリを選びます。
3. Main file pathに `app.py` を指定してデプロイします。

## 設計の参考

- PIVOT「投資歴30年パックンが教える最強の投資法」
  - 見えないお金
  - 72の法則
  - 職業、給与、家賃、保険、失業を扱うリアル人生ゲーム
  - 若い時期ほど大きくなる複利効果
  - 個別株、暗号資産、FXのリスク・リターン体験

## 注意

このアプリの金額、運用利率、市場イベントは学習用に単純化した架空のものです。特定の金融商品を推奨せず、実際の投資成果を予測または保証しません。

