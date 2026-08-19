from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_start_and_first_turn_render_without_error():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not app.exception
    assert app.text_input[0].label == "プレイヤー名"

    app.text_input[0].input("悠然")
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "18歳"

    # The second radio is the knowledge quiz. Choose its correct second option.
    app.radio[1].set_value(app.radio[1].options[1])
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "25歳"
    assert app.expander[0].label == "📬 前のターンの結果：社会人スタート"
