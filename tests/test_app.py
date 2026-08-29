from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_start_and_first_turn_render_without_error():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not app.exception
    assert app.text_input[0].label == "子どもの名前"
    assert app.slider[0].label == "いま何歳？"

    app.text_input[0].input("悠然")
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "11歳"
    assert len(app.number_input) == 6
    assert app.number_input[0].label == "毎月の投資金額（円）"
    assert [item.label for item in app.number_input[1:]] == ["投資割合（%）"] * 5
    assert app.toggle[0].label == "毎年リバランスする"

    # The second radio is the knowledge quiz. Choose its correct first option.
    app.radio[1].set_value(app.radio[1].options[0])
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "16歳"
    assert app.expander[0].label == "🔍 なぜ増えた？なぜ減った？｜11歳→16歳"


def test_career_step_calculates_take_home_and_accepts_budget():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.slider[0].set_value(17)
    app.slider[1].set_value(18)
    app.button[0].click().run()
    assert not app.exception

    app.radio[1].set_value(app.radio[1].options[0])
    app.button[0].click().run()
    assert not app.exception
    assert "月の手取り" in [item.label for item in app.metric]
    assert {item.label for item in app.number_input} == {
        "🏠 家賃",
        "💡 光熱費",
        "📱 通信費",
        "🍚 食費",
        "🎈 交際費",
        "🚃 交通費",
        "🌱 投資",
    }

    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "18歳"
    assert app.number_input[0].label == "毎月の投資金額（円）"
