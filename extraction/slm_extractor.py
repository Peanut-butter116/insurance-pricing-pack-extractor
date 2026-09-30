import json
from extraction.schemas import Extraction, empty
from extraction.prompts import SYSTEM


def extract(document, backend):
    # Explicit allowlist prevents layout/split/truth metadata entering the model.
    payload = json.dumps({'format': document['format'], 'segments': document['segments']}, ensure_ascii=False)
    attempts = []
    for attempt in range(2):
        log = {'attempt': attempt + 1}
        try:
            raw, stats = backend.generate(SYSTEM, payload)
            log.update(stats, raw=raw)
            text = raw.strip()
            if text.startswith('```') and text.endswith('```'):
                text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            result = Extraction.model_validate_json(text).model_dump()
            log['success'] = True
            attempts.append(log)
            return result, attempts, None
        except Exception as exc:
            log.update(success=False, error=f'{type(exc).__name__}: {exc}')
            attempts.append(log)
            payload += '\nReturn valid JSON with exactly all eight fields and value/source_text/source_location for each.'
    return empty(), attempts, 'SLM failed both attempts; nulls are failure placeholders'
