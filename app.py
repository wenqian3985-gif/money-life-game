from __future__ import annotations

import pandas as pd
import streamlit as st

from content import LIFE_STAGES, STRATEGIES
from game_engine import (
    annual_salary,
    available_budget,
    create_new_game,
    current_quiz,
    current_stage,
    ending_profile,
    play_turn,
    real_net_worth,
    total_assets,
)


st.set_page_config(
    page_title="未来マネークエスト",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp {background: linear-gradient(180deg, #f4fbf6 0%, #fffaf0 100%);}
    .block-container {max-width: 1120px; padding-top: 1.4rem; padding-bottom: 3rem;}
    .hero {
        padding: 1.5rem 1.7rem; border-radius: 24px;
        color: #173f35; background: linear-gradient(135deg, #d9f7e8, #fff0bd);
        border: 1px solid rgba(21, 94, 73, .13); margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0 0 .35rem 0; font-size: 2.25rem;}
    .hero p {margin: .2rem 0; font-size: 1.05rem;}
    .card {
        padding: 1.15rem 1.25rem; border-radius: 18px; background: rgba(255,255,255,.92);
        border: 1px solid #dfeae4; box-shadow: 0 5px 18px rgba(44, 84, 66, .06);
        margin: .55rem 0 1rem 0;
    }
    .event-card {border-left: 7px solid #ffb547;}
    .learn-card {border-left: 7px solid #4ea98a;}
    .result-card {border-left: 7px solid #6c83e6;}
    .tiny {font-size: .82rem; color: #5f6f67;}
    .big-number {font-size: 1.65rem; font-weight: 800; color: #175d48;}
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.88); border: 1px solid #e0ebe5;
        padding: .75rem; border-radius: 15px;
    }
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        border-radius: 999px; font-weight: 700; min-height: 3rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def yen(value: float) -> str:
    return f"{value:,.0f}万円"


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🌳 学べること")
        st.markdown(
            """
- お金の「使う・守る・育てる」
- 複利と72の法則
- 預金・分散投資・高リスク商品の違い
- 家賃、保険、失業など人生の固定費と予想外
- 「必ずもうかる」話から身を守る方法
"""
        )
        st.info("資産額だけが勝ちではありません。幸福・知識・挑戦のバランスも結末に反映されます。")
        st.caption("金額と運用結果は学習用に単純化した架空のシミュレーションです。実際の投資成果を予測・保証するものではありません。")
        st.markdown("---")
        st.markdown("**参考にした動画**")
        st.link_button(
            "PIVOTの動画を開く",
            "https://www.youtube.com/watch?v=U35WMjyVdmI",
            use_container_width=True,
        )


def render_last_result(result: dict | None) -> None:
    if not result:
        return
    with st.expander(f"📬 前のターンの結果：{result['stage']}", expanded=True):
        quiz_mark = "正解！" if result["quiz_correct"] else "今回は不正解"
        st.markdown(
            f"""
<div class="card result-card">
<b>選択からの学び</b><br>{result['choice_lesson']}<br><br>
<b>クイズ：</b>{quiz_mark} — {result['quiz_explanation']}
</div>
""",
            unsafe_allow_html=True,
        )
        market = result["market"]
        cols = st.columns(3)
        cols[0].metric("インデックス市場", f"年 {market['index_rate'] * 100:+.0f}%")
        cols[1].metric("個別株市場", f"年 {market['stock_rate'] * 100:+.0f}%")
        cols[2].metric("暗号資産・FX", f"{market['challenge_multiplier']:.1f}倍")
        if result["event_cost"]["original_cost"]:
            original = result["event_cost"]["original_cost"]
            actual = result["event_cost"]["actual_cost"]
            st.caption(f"突然の出費：本来 {yen(original)} → 自己負担 {yen(actual)}")


def start_screen() -> None:
    st.markdown(
        """
<div class="hero">
  <h1>🌳 未来マネークエスト</h1>
  <p>18歳から65歳まで、5つの選択で未来を育てる金融人生ゲーム</p>
  <p class="tiny">サイコロで職業が決まり、家賃・保険・予想外の出費・投資の波を体験します。</p>
</div>
""",
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("### このゲームのゴール")
        st.markdown(
            """
「一番お金持ち」になることではありません。目の前の楽しみ、困ったときの現金、
未来を育てる投資、自分の力を高める学びを、自分で考えて組み合わせることがゴールです。
"""
        )
        st.markdown(
            """
<div class="card learn-card">
💡 <b>親子で遊ぶコツ</b><br>
選ぶ前に「どうしてそう思った？」と一言だけ聞いてください。正解を先に教えるより、
子どもの理由を言葉にしてもらう方が学びが残ります。
</div>
""",
            unsafe_allow_html=True,
        )
    with right:
        with st.form("start_form"):
            name = st.text_input("プレイヤー名", value="悠然", max_chars=12)
            difficulty = st.radio("学習モード", ["小学校高学年", "中学生"], horizontal=True)
            started = st.form_submit_button("🎲 職業を決めてスタート", use_container_width=True)
        if started:
            st.session_state.game = create_new_game(name, difficulty)
            st.rerun()


def game_screen(state: dict) -> None:
    stage = current_stage(state)
    quiz = current_quiz(state)
    budget = available_budget(state)
    profession = state["profession"]

    st.markdown(
        f"""
<div class="hero">
  <h1>{profession['emoji']} {state['player_name']}の未来マネークエスト</h1>
  <p>{profession['name']} — {profession['message']}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.progress(state["turn"] / len(LIFE_STAGES), text=f"ステージ {state['turn'] + 1}/{len(LIFE_STAGES)}：{stage['label']}")
    metrics = st.columns(5)
    metrics[0].metric("いまの年齢", f"{state['age']}歳")
    metrics[1].metric("推定年収", yen(annual_salary(state)))
    metrics[2].metric("純資産", yen(total_assets(state)))
    metrics[3].metric("幸福", f"{state['happiness']}/100")
    metrics[4].metric("金融知識", f"{state['knowledge']}/100")

    render_last_result(state.get("last_result"))

    st.markdown(
        f"""
<div class="card event-card">
  <span class="tiny">{stage['age']}歳 → {stage['next_age']}歳</span>
  <h3>🎴 {stage['event']['title']}</h3>
  <p>{stage['event']['description']}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form(f"turn_form_{state['turn']}"):
        option_labels = {o["label"]: o["key"] for o in stage["event"]["options"]}
        event_label = st.radio("あなたならどうする？ まず理由を声に出してから選ぼう", list(option_labels))

        st.markdown("#### 🧠 1問クイズ")
        st.write(quiz["question"])
        quiz_label = st.radio(
            "答えを選ぶ",
            quiz["options"],
            index=None,
            key=f"quiz_{state['turn']}",
            label_visibility="collapsed",
        )

        st.markdown("#### 💰 この期間のお金を配分")
        st.caption(f"生活費などを引いた後、選べるお金は約 {yen(budget)}。どの作戦にしますか？")
        strategy_labels = {f"{v['name']}｜{v['description']}": k for k, v in STRATEGIES.items()}
        strategy_label = st.radio("作戦", list(strategy_labels), index=1, label_visibility="collapsed")

        submitted = st.form_submit_button("この選択で未来へ進む ➜", use_container_width=True)

    if submitted:
        if quiz_label is None:
            st.warning("クイズの答えを選んでください。")
            return
        new_state = play_turn(
            state,
            strategy_labels[strategy_label],
            option_labels[event_label],
            quiz["options"].index(quiz_label),
        )
        st.session_state.game = new_state
        st.rerun()

    st.markdown("#### 現在の資産の中身")
    asset_df = pd.DataFrame(
        {
            "資産": ["現金", "インデックス", "個別株", "暗号資産・FX", "借金"],
            "万円": [state["cash"], state["index"], state["stock"], state["challenge"], state["debt"]],
        }
    ).set_index("資産")
    st.bar_chart(asset_df, color="#4ea98a", horizontal=True)


def ending_screen(state: dict) -> None:
    profile = ending_profile(state)
    net = total_assets(state)
    real = real_net_worth(state)
    baseline = state["baseline_cash"]

    st.markdown(
        f"""
<div class="hero">
  <h1>{profile['emoji']} 65歳のあなたは「{profile['title']}」</h1>
  <p>{profile['message']}</p>
</div>
""",
        unsafe_allow_html=True,
    )
    render_last_result(state.get("last_result"))

    cols = st.columns(4)
    cols[0].metric("最終純資産", yen(net))
    cols[1].metric("今の物価に直した価値", yen(real))
    cols[2].metric("幸福", f"{state['happiness']}/100")
    cols[3].metric("金融知識", f"{state['knowledge']}/100")

    st.caption(
        f"同じ投資可能額を低金利の現金だけで持った参考ケース：約 {yen(baseline)}。"
        "結果が上でも下でも、1回のゲームで将来の運用成果は決まりません。"
    )

    history = pd.DataFrame(state["history"])
    chart = history.set_index("age")[["total_assets", "real_assets"]].rename(
        columns={"total_assets": "純資産（名目）", "real_assets": "今の物価に直した価値"}
    )
    st.markdown("### 資産の旅")
    st.line_chart(chart, color=["#31866d", "#e2993f"])

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("### 最後の資産配分")
        final_assets = pd.DataFrame(
            {
                "資産": ["現金", "インデックス", "個別株", "暗号資産・FX", "借金"],
                "万円": [state["cash"], state["index"], state["stock"], state["challenge"], state["debt"]],
            }
        ).set_index("資産")
        st.bar_chart(final_assets, horizontal=True)
    with right:
        st.markdown("### 親子で振り返る3問")
        st.markdown(
            """
1. 一番迷った選択はどれ？ なぜ迷った？
2. もう一度なら、何を変えてみたい？
3. お金が増えたら、どんな挑戦や人助けに使いたい？
"""
        )
        st.markdown(
            """
<div class="card learn-card">
<b>今回の核心</b><br>
若いときのお金には「時間」があります。けれど、全部を投資すればよいわけではありません。
今を楽しむお金、困ったときの現金、長期で育てるお金を分けることが大切です。
</div>
""",
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)
    if col1.button("🔁 違う選択でもう一度", use_container_width=True):
        st.session_state.game = create_new_game(state["player_name"], state["difficulty"])
        st.rerun()
    if col2.button("🏠 最初の画面へ", use_container_width=True):
        st.session_state.pop("game", None)
        st.rerun()


render_sidebar()
if "game" not in st.session_state:
    start_screen()
elif st.session_state.game["ended"]:
    ending_screen(st.session_state.game)
else:
    game_screen(st.session_state.game)

