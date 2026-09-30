from openpyxl import load_workbook
from extraction.schemas import empty
from template.populate_template import populate


def test_template_values_and_blanks(tmp_path):
    raw = empty()
    raw['gross_premium_gbp'].update(value=2450000, source_text='=HYPERLINK("evil")', source_location='page 1')
    raw['claim_count']['value'] = 0
    raw['rate_change_pct']['value'] = 7.5
    path = tmp_path / 'review.xlsx'
    populate(raw, path)
    book = load_workbook(path)
    sheet = book.active
    assert sheet['B4'].value is None
    assert sheet['B6'].value == 2450000
    assert sheet['B7'].value == 0
    assert sheet['B9'].value == .075
    assert sheet['C6'].data_type == 's'
