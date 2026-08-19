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
    assert len(app.number_input) == 5
    assert app.toggle[0].label == "毎年リバランスする"

    # The second radio is the knowledge quiz. Choose its correct first option.
    app.radio[1].set_value(app.radio[1].options[0])
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "16歳"
    assert app.expander[0].label == "🔍 なぜ増えた？なぜ減った？｜11歳→16歳"
