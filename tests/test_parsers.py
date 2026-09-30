import pytest
from config import ROOT
from data.generate_documents import generate
from parsers.common import parse


@pytest.mark.parametrize('format_', ['pdf', 'excel', 'powerpoint'])
def test_parse_formats(format_):
    record = next(r for r in generate() if r['format'] == format_ and r['layout'] == 'A')
    doc = parse(ROOT / record['path'])
    assert doc['format'] == format_
    assert doc['segments']
    text = ' '.join(s['text'] for s in doc['segments'])
    assert 'Gross Premium' in text and 'SYNTHETIC' in text
    assert all(s['location'] for s in doc['segments'])


def test_excel_percent_and_coordinates(tmp_path):
    from openpyxl import Workbook
    book = Workbook()
    book.active['A1'] = 'Rate change'
    book.active['B1'] = .075
    book.active['B1'].number_format = '0.0%'
    path = tmp_path / 'input.xlsx'
    book.save(path)
    segment = parse(path)['segments'][0]
    assert '7.5%' in segment['text'] and 'B1' in segment['location']


def test_uncached_excel_formula_fails(tmp_path):
    from openpyxl import Workbook
    book = Workbook()
    book.active['A1'] = '=1+1'
    path = tmp_path / 'input.xlsx'
    book.save(path)
    with pytest.raises(ValueError, match='Uncached formula'): parse(path)
