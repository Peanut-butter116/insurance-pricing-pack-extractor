import pymupdf


def segments(path):
    output = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, 1):
            text = page.get_text(sort=True).strip()
            if text:
                output.append({'location': f'page {i}', 'text': text})
    return output
