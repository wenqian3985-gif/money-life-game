from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from content import CAREERS, PRODUCTS
from game_engine import (
    ASSET_KEYS,
    BUDGET_KEYS,
    MINOR_NISA_TOTAL_LIMIT,
    annual_salary,
    career_probability,
    choose_career,
    create_new_game,
    current_event,
    current_quiz,
    default_household_budget,
    ending_profile,
    estimate_take_home,
    max_monthly_investment_yen,
    next_checkpoint_age,
    play_period,
    real_net_worth,
    set_household_budget,
    total_assets,
)


BUDGET_LABELS = {
    "rent": "🏠 家賃",
    "utilities": "💡 光熱費",
    "communications": "📱 通信費",
    "food": "🍚 食費",
    "social": "🎈 交際費",
    "transport": "🚃 交通費",
    "investment": "🌱 投資",
}


st.set_page_config(
    page_title="未来マネークエスト",
    page_icon="🐿️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    :root {--ink:#193b35; --green:#44a77a; --cream:#fff9e9;}
    .stApp {background: radial-gradient(circle at 8% 3%, #ddf8eb 0, transparent 28%), linear-gradient(180deg,#fffdf5,#f4fbff);}
    .block-container {max-width:1180px; padding-top:1.25rem; padding-bottom:4rem;}
    .hero {position:relative; overflow:hidden; padding:1.45rem 1.7rem; border-radius:28px; color:var(--ink);
      background:linear-gradient(125deg,#c9f3df,#fff1b9 72%,#ffd8dd); border:2px solid rgba(34,123,91,.12);
      box-shadow:0 10px 30px rgba(54,101,82,.10); margin-bottom:1rem; min-height:145px;}
    .hero h1 {margin:0 0 .35rem; font-size:clamp(1.8rem,4vw,2.7rem); max-width:82%;}
    .hero p {margin:.25rem 0; font-size:1.02rem; max-width:78%;}
    .mascot {position:absolute; right:3%; bottom:-6px; font-size:5.8rem; filter:drop-shadow(0 7px 3px rgba(44,75,60,.16));
      animation:floaty 2.8s ease-in-out infinite; transform-origin:bottom center;}
    .coin {display:inline-block; animation:spin 3s linear infinite;}
    @keyframes floaty {0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-10px) rotate(3deg)}}
    @keyframes spin {0%,100%{transform:rotateY(0)}50%{transform:rotateY(180deg)}}
    .card {padding:1rem 1.15rem; border-radius:19px; background:rgba(255,255,255,.94); border:1px solid #dcebe4;
      box-shadow:0 5px 18px rgba(44,84,66,.06); margin:.45rem 0 .9rem;}
    .speech {border-left:7px solid #ffb54b;}
    .learn {border-left:7px solid #4fae88;}
    .career {border-left:7px solid #7a8ee8;}
    .tiny {font-size:.84rem; color:#60736c;}
    .pill {display:inline-block; padding:.25rem .62rem; border-radius:999px; background:#fff; margin:.15rem .18rem .15rem 0;
      border:1px solid #d7e7de; font-size:.85rem;}
    .product-card {min-height:126px; padding:.9rem; border-radius:18px; background:#fff; border:2px solid #e1eee8; margin-bottom:.3rem;}
    .product-card .emoji {font-size:2rem;}
    div[data-testid="stMetric"] {background:rgba(255,255,255,.9); border:1px solid #dceae4; padding:.72rem; border-radius:16px;}
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {border-radius:999px; font-weight:800; min-height:3rem;}
    div[data-testid="stPopover"] button {border-radius:999px;}
    @media (max-width:720px) {.mascot{font-size:4rem}.hero p{max-width:72%}.hero{padding:1.1rem}.hero h1{max-width:78%}}
</style>
""",
    unsafe_allow_html=True,
)


def yen(value: float) -> str:
    return f"{value:,.1f}万円"


def monthly_yen(value: int | float) -> str:
    return f"{value:,.0f}円"


def hero(title: str, message: str, sub: str = "") -> None:
    st.markdown(
        f"""
<div class="hero">
  <h1>{title}</h1><p>{message}</p><p class="tiny">{sub}</p>
  <div class="mascot">🐿️<span class="coin">🪙</span></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🗺️ 冒険ガイド")
        st.markdown(
            """
- 🪙 **守る**：すぐ使える現金
- 🌱 **育てる**：時間と分散を味方に
- 🎓 **学ぶ**：夢に近づく準備
- 🎈 **楽しむ**：今の幸せも大切
"""
        )
        st.info("資産額だけが勝ちではありません。『なぜこの配分？』を親子で話すことがゴールです。")
        if "game" in st.session_state:
            if st.button("🔄 最初から遊ぶ", use_container_width=True):
                del st.session_state.game
                st.rerun()
        st.markdown("---")
        st.markdown("#### 📚 制度・データの出典")
        st.link_button("金融庁：こどもNISA", "https://www.fsa.go.jp/access/r7/270.html", use_container_width=True)
        st.link_button("日本FP協会：小学生の夢", "https://www.jafp.or.jp/personal_finance/yume/syokugyo/", use_container_width=True)
        st.link_button("厚労省 job tag", "https://shigoto.mhlw.go.jp/", use_container_width=True)
        st.link_button("参考にしたPIVOT動画", "https://www.youtube.com/watch?v=U35WMjyVdmI", use_container_width=True)
        st.caption("金額、相場、職業到達確率は学習用に単純化したゲーム設定です。投資成果・就職・年収を予測または保証しません。")


def render_product_allocation(state: dict) -> dict[str, int]:
    """Show each product's explanation together with its allocation input."""
    st.markdown("#### 🧩 ⑤ 商品を知って、投資割合を決める")
    st.caption("説明を読んでから、その商品の割合を入力してください。5つの合計を100%にします。")
    allocation: dict[str, int] = {}
    cols = st.columns(5)
    for col, (key, product) in zip(cols, PRODUCTS.items()):
        with col:
            st.markdown(
                f"""<div class="product-card" style="border-top:7px solid {product['color']}">
                <div class="emoji">{product['emoji']}</div><b>{product['name']}</b><br>
                <span class="tiny">ゆれ：{product['risk']}</span></div>""",
                unsafe_allow_html=True,
            )
            with st.popover("🔎 くわしく見る", use_container_width=True):
                st.markdown(f"### {product['emoji']} {product['name']}")
                st.success(product["story"])
                st.write(product["detail"])
                st.markdown(f"**こどもNISA：** {product['nisa']}")
            allocation[key] = int(
                st.number_input(
                    "投資割合（%）",
                    min_value=0,
                    max_value=100,
                    value=int(state["target_allocation"][key]),
                    step=5,
                    key=f"allocation_{state['turn']}_{key}",
                )
            )
    st.markdown(f"**割合の合計：{sum(allocation.values())}%**")
    return allocation


def render_asset_chart(state: dict) -> None:
    st.markdown("### 📊 年齢ごとの資産の育ち方")
    frame = pd.DataFrame(state["history"])
    long = frame.melt(id_vars=["age"], value_vars=list(ASSET_KEYS), var_name="asset", value_name="value")
    labels = {key: f"{item['emoji']} {item['name']}" for key, item in PRODUCTS.items()}
    long["商品"] = long["asset"].map(labels)
    domain = list(labels.values())
    colors = [PRODUCTS[key]["color"] for key in ASSET_KEYS]
    chart = (
        alt.Chart(long)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("age:O", title="年齢", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("sum(value):Q", title="資産（万円）", stack="zero"),
            color=alt.Color("商品:N", scale=alt.Scale(domain=domain, range=colors), legend=alt.Legend(orient="bottom")),
            tooltip=[alt.Tooltip("age:O", title="年齢"), alt.Tooltip("商品:N"), alt.Tooltip("sum(value):Q", title="金額（万円）", format=",.1f")],
        )
        .properties(height=360)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("棒の色は資産の種類。借金は資産ではないため積み上げず、画面上部の『借金』に別表示します。")


def render_last_result(result: dict | None) -> None:
    if not result:
        return
    with st.expander(f"🔍 なぜ増えた？なぜ減った？｜{result['age_range']}", expanded=True):
        quiz_mark = "🎉 正解" if result["quiz_correct"] else "🌱 次は正解できる"
        st.markdown(
            f"""<div class="card learn"><b>{result['event_title']}</b>：{result['event_choice']}<br>
            {result['lesson']}<br><br><b>クイズ：</b>{quiz_mark} — {result['quiz_explanation']}</div>""",
            unsafe_allow_html=True,
        )
        if result["learning_spend"]:
            st.caption(f"夢の準備に使ったお金：{yen(result['learning_spend'])}")
        st.caption(f"設定した毎月の投資金額：{monthly_yen(result['monthly_investment_yen'])}")
        if result["nisa_added"]:
            st.caption(f"この期間に、こどもNISA対象として数えた積立：{yen(result['nisa_added'])}")
        breakdown = pd.DataFrame(result["breakdown"])
        st.dataframe(
            breakdown,
            column_config={
                "開始": st.column_config.NumberColumn(format="%.1f万円"),
                "積立": st.column_config.NumberColumn(format="%+.1f万円"),
                "配分調整": st.column_config.NumberColumn(format="%+.1f万円"),
                "値動き": st.column_config.NumberColumn(format="%+.1f万円"),
                "終了": st.column_config.NumberColumn(format="%.1f万円"),
            },
            hide_index=True,
            use_container_width=True,
        )


def start_screen() -> None:
    hero(
        "🐿️ 未来マネークエスト",
        "ほんとうの年齢から始めて、お金と夢を育てる親子ゲーム",
        "配分も、リバランスも、社会人になる年齢も、自分で決められます。",
    )
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("### 🎯 このゲームのゴール")
        st.write("お金持ちになる競争ではありません。現金、分散投資、学び、今の楽しみを『なぜそうするか』考えることがゴールです。")
        st.markdown(
            """<div class="card speech">💬 <b>親子で遊ぶ合言葉</b><br>
            選ぶ前に「どうしてそう思った？」。正解を先に言わず、子どもの理由を聞いてみよう。</div>""",
            unsafe_allow_html=True,
        )
        st.info("2027年1月開始予定の『こどもNISA』は0～17歳が対象。年60万円、非課税保有限度額600万円としてゲームに反映しています。")
    with right:
        with st.form("start_form"):
            st.markdown("### 🌱 冒険の設定")
            name = st.text_input("子どもの名前", value="悠然", max_chars=12)
            start_age = st.slider("いま何歳？", 0, 17, 11)
            social_age = st.slider("何歳から社会人になる？", 18, 30, 22)
            monthly = st.slider("最初の毎月の投資金額", 0, 50_000, 10_000, 5_000, format="%d円")
            difficulty = st.radio("ことばの難しさ", ["小学校高学年", "中学生"], horizontal=True)
            started = st.form_submit_button("🚀 この設定でスタート", use_container_width=True)
        if started:
            st.session_state.game = create_new_game(name, start_age, social_age, monthly, difficulty)
            st.rerun()


def career_screen(state: dict) -> None:
    hero(
        f"🎓 {state['age']}歳、夢の仕事を選ぼう",
        "子どもに人気の仕事から、あこがれの進路を1つ選びます。",
        "確率は実際の就職率ではなく、準備の効果を体験するためのゲーム内設定です。",
    )
    st.markdown(
        f"""<div class="card career">ここまでの<b>夢の準備ポイント：{state['preparation']:.1f}</b>／金融知識：{state['knowledge']}<br>
        学びに時間やお金を使った分だけ、すべての仕事のゲーム内確率が少し上がります。</div>""",
        unsafe_allow_html=True,
    )
    rows = []
    for career in CAREERS:
        rows.append(
            {
                "夢の仕事": f"{career['emoji']} {career['name']}",
                "ゲーム内の到達確率": career_probability(state, career["key"]),
                "参考年収": career["salary"],
                "準備のヒント": career["skills"],
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        column_config={
            "ゲーム内の到達確率": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%"),
            "参考年収": st.column_config.NumberColumn(format="%d万円"),
        },
        hide_index=True,
        use_container_width=True,
    )
    label_to_key = {f"{item['emoji']} {item['name']}": item["key"] for item in CAREERS}
    selected_label = st.radio(
        "いちばん挑戦したい仕事",
        list(label_to_key),
        horizontal=False,
        key=f"career_choice_{state['turn']}",
    )
    selected = next(item for item in CAREERS if item["key"] == label_to_key[selected_label])
    st.info(f"{selected['message']}\n\n準備：{selected['skills']}")

    # The career result is deterministic for a given game and choice, so the
    # actual starting salary can be used to build the budget before confirming.
    preview_state = choose_career(state, selected["key"])
    career_result = preview_state["career_result"]
    profession = preview_state["profession"]
    icon = "🎉" if career_result["achieved"] else "🧭"
    st.markdown(
        f"""<div class="card career">{icon} <b>{profession['emoji']} {profession['name']}として働く場合</b><br>
        ゲーム内確率 {career_result['probability']}%／サイコロ {career_result['roll']} — {career_result['message']}</div>""",
        unsafe_allow_html=True,
    )

    salary = annual_salary(preview_state)
    take_home = estimate_take_home(salary, state["age"])
    st.markdown("### 🧾 給料から手取りを計算しよう")
    pay_cols = st.columns(5)
    pay_cols[0].metric("月の総支給", monthly_yen(salary * 10_000 / 12))
    pay_cols[1].metric("社会保険料", f"−{monthly_yen(take_home['social_insurance'] * 10_000 / 12)}")
    pay_cols[2].metric("所得税", f"−{monthly_yen(take_home['income_tax'] * 10_000 / 12)}")
    pay_cols[3].metric("住民税", f"−{monthly_yen(take_home['resident_tax'] * 10_000 / 12)}")
    pay_cols[4].metric("月の手取り", monthly_yen(take_home["monthly_take_home_yen"]))
    st.caption(
        "2026年の公表税率を参考に、東京在住・会社員・扶養なしとして単純化した学習用概算です。"
        "実際の手取りは地域、年齢、扶養、会社の制度などで変わります。"
    )

    st.markdown("### 🏠 手取りの使い道を決めよう")
    st.caption("家賃などを自分で設定し、残った範囲で毎月の投資金額を決めます。")
    defaults = default_household_budget(int(take_home["monthly_take_home_yen"]))
    budget: dict[str, int] = {}
    budget_cols = st.columns(2)
    for index, key in enumerate(BUDGET_KEYS):
        with budget_cols[index % 2]:
            budget[key] = int(
                st.number_input(
                    BUDGET_LABELS[key],
                    min_value=0,
                    max_value=int(take_home["monthly_take_home_yen"]),
                    value=defaults[key],
                    step=1_000,
                    format="%d",
                    key=f"budget_{selected['key']}_{key}",
                    help="1か月あたりの金額（円）",
                )
            )

    monthly_total = sum(budget.values())
    monthly_remaining = int(take_home["monthly_take_home_yen"]) - monthly_total
    summary_cols = st.columns(3)
    summary_cols[0].metric("手取り", monthly_yen(take_home["monthly_take_home_yen"]))
    summary_cols[1].metric("設定した支出＋投資", monthly_yen(monthly_total))
    summary_cols[2].metric("まだ使い道を決めていないお金", monthly_yen(monthly_remaining))
    if monthly_remaining < 0:
        st.error(f"手取りを{monthly_yen(abs(monthly_remaining))}超えています。金額を見直してください。")
    else:
        st.success("手取りの範囲に収まっています。残りは予備費や自由費として考えられます。")

    if st.button("🌟 この仕事と家計でスタート", use_container_width=True):
        if monthly_remaining < 0:
            st.error("支出と投資を手取り以内にしてから進んでください。")
        else:
            st.session_state.game = set_household_budget(preview_state, budget)
            st.rerun()


def game_screen(state: dict) -> None:
    profession = state.get("profession")
    role = f"{profession['emoji']} {profession['name']}" if profession else "🎒 夢を準備中"
    hero(
        f"{state['player_name']}の未来マネークエスト",
        role,
        f"{state['age']}歳から{next_checkpoint_age(state)}歳までの作戦を決めよう。",
    )
    progress = (state["age"] - state["start_age"]) / max(1, 65 - state["start_age"])
    st.progress(progress, text=f"人生マップ：{state['age']}歳 → 65歳")
    metrics = st.columns(6)
    metrics[0].metric("いま", f"{state['age']}歳")
    metrics[1].metric("純資産", yen(total_assets(state)))
    metrics[2].metric("年収", yen(annual_salary(state)) if profession else "準備中")
    metrics[3].metric("借金", yen(state["debt"]))
    metrics[4].metric("幸福", f"{state['happiness']}/100")
    metrics[5].metric("金融知識", f"{state['knowledge']}/100")

    career_result = state.get("career_result")
    if career_result:
        icon = "🎉" if career_result["achieved"] else "🧭"
        st.markdown(
            f"""<div class="card career">{icon} <b>{career_result['dream']}への挑戦結果</b><br>
            ゲーム内確率 {career_result['probability']}%／サイコロ {career_result['roll']} — {career_result['message']}</div>""",
            unsafe_allow_html=True,
        )

    if state["age"] < 18:
        remaining = MINOR_NISA_TOTAL_LIMIT - state["minor_nisa_total"]
        st.info(
            f"👶 こどもNISA学習メーター：累計 {yen(state['minor_nisa_total'])}／600万円（残り {yen(remaining)}）。"
            " 対象として数えるのは、条件を満たす債券・バランス投信とインデックス投信だけです。"
        )

    render_last_result(state.get("last_result"))
    event = current_event(state)
    quiz = current_quiz(state)
    target_age = next_checkpoint_age(state)
    st.markdown(
        f"""<div class="card speech"><span class="tiny">🎴 {state['age']}歳→{target_age}歳の出来事</span>
        <h3>{event['title']}</h3><p>{event['description']}</p></div>""",
        unsafe_allow_html=True,
    )
    with st.form(f"period_form_{state['turn']}"):
        option_labels = {item["label"]: item["key"] for item in event["options"]}
        event_label = st.radio("① あなたならどうする？", list(option_labels))
        st.markdown("#### 🧠 ② 1問クイズ")
        st.write(quiz["question"])
        quiz_label = st.radio("答え", quiz["options"], index=None, label_visibility="collapsed")

        if state["age"] < state["social_age"]:
            learning_percent = st.slider(
                "③ 毎月の積立予定のうち、夢の準備（本・習い事・体験）に使う割合",
                0,
                30,
                10,
                5,
                format="%d%%",
            )
        else:
            learning_percent = 0
            take_home = estimate_take_home(annual_salary(state), state["age"])
            household_budget = state.get("household_budget") or {}
            living_costs = sum(
                int(household_budget.get(key, 0))
                for key in BUDGET_KEYS
                if key != "investment"
            )
            st.markdown("#### 🧾 ③ 現在の毎月の家計")
            cashflow_cols = st.columns(3)
            cashflow_cols[0].metric("手取り", monthly_yen(take_home["monthly_take_home_yen"]))
            cashflow_cols[1].metric("生活費", monthly_yen(living_costs))
            cashflow_cols[2].metric("投資に回せる上限", monthly_yen(max_monthly_investment_yen(state)))
            st.caption("生活費は職業を選んだときの設定です。給料は年齢とともにゲーム内で変化します。")

        st.markdown("#### 💴 ④ 毎月の投資金額を決める")
        monthly_max = max_monthly_investment_yen(state) if profession else 50_000
        monthly_default = min(int(state["monthly_contribution_yen"]), monthly_max)
        monthly_investment = int(
            st.number_input(
                "毎月の投資金額（円）",
                min_value=0,
                max_value=monthly_max,
                value=monthly_default,
                step=1_000,
                format="%d",
                help="この金額を、下で決める割合に分けて毎月投資します。",
            )
        )
        st.caption(f"1年間では {monthly_yen(monthly_investment * 12)} を投資する設定です。")

        allocation = render_product_allocation(state)
        rebalance = st.toggle(
            "毎年リバランスする",
            value=bool(state["rebalance"]),
            help="増減でずれた資産の割合を、毎年この目標配分へ戻します。オフなら、新しい積立だけを目標配分で買います。",
        )
        submitted = st.form_submit_button(f"🚀 {target_age}歳まで進む", use_container_width=True)

    if submitted:
        if quiz_label is None:
            st.warning("クイズの答えを選んでください。")
        elif sum(allocation.values()) != 100:
            st.error(f"配分の合計が{sum(allocation.values())}%です。100%になるよう直してください。")
        else:
            try:
                st.session_state.game = play_period(
                    state,
                    allocation,
                    rebalance,
                    option_labels[event_label],
                    quiz["options"].index(quiz_label),
                    learning_percent,
                    monthly_investment,
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    render_asset_chart(state)
    if state["reason_history"]:
        with st.expander("📒 これまでの増減理由をすべて見る"):
            st.dataframe(pd.DataFrame(state["reason_history"]), hide_index=True, use_container_width=True)


def ending_screen(state: dict) -> None:
    profile = ending_profile(state)
    hero(
        f"{profile['emoji']} 65歳のあなたは『{profile['title']}』",
        profile["message"],
        "1回のサイコロで本当の未来は決まりません。配分を変えて、もう一度比べてみよう。",
    )
    metrics = st.columns(5)
    metrics[0].metric("最終純資産", yen(total_assets(state)))
    metrics[1].metric("今の物価での価値", yen(real_net_worth(state)))
    metrics[2].metric("借金", yen(state["debt"]))
    metrics[3].metric("幸福", f"{state['happiness']}/100")
    metrics[4].metric("金融知識", f"{state['knowledge']}/100")
    render_last_result(state.get("last_result"))
    render_asset_chart(state)
    with st.expander("📒 全期間の増減理由", expanded=False):
        st.dataframe(pd.DataFrame(state["reason_history"]), hide_index=True, use_container_width=True)
    if st.button("🔄 違う年齢・配分で、もう一度遊ぶ", use_container_width=True):
        del st.session_state.game
        st.rerun()


# A deployment can briefly reconnect an open browser with the previous version's
# session dictionary. Reset only that incompatible in-memory state.
if "game" in st.session_state:
    required_state_keys = {"start_age", "household_budget"}
    if not required_state_keys.issubset(st.session_state.game):
        del st.session_state.game

render_sidebar()
if "game" not in st.session_state:
    start_screen()
else:
    game = st.session_state.game
    if game["ended"]:
        ending_screen(game)
    elif game.get("career_pending"):
        career_screen(game)
    else:
        game_screen(game)
