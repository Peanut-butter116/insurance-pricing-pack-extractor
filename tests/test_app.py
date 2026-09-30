from streamlit.testing.v1 import AppTest
from config import ROOT


def test_rules_review_and_export():
    app = AppTest.from_file(ROOT / 'app/streamlit_app.py', default_timeout=30).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 8
    app.button[1].click().run()
    assert not app.exception
