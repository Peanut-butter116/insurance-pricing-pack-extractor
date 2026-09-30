from pathlib import Path


def parse(path):
    path = Path(path)
    from parsers.pdf_parser import segments as pdf
    from parsers.excel_parser import segments as excel
    from parsers.powerpoint_parser import segments as ppt
    kind, parser = {'.pdf': ('pdf', pdf), '.xlsx': ('excel', excel), '.pptx': ('powerpoint', ppt)}[path.suffix.lower()]
    content = parser(path)
    if not content:
        raise ValueError('No extractable text. Scanned images need OCR, which is outside this pilot.')
    return {'document_id': path.stem, 'format': kind, 'segments': content}
