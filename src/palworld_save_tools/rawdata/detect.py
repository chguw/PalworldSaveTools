from loguru import logger


class ChangeCollector:
    _changes = []
    _enabled = False

    @classmethod
    def enable(cls):
        cls._enabled = True
        cls._changes = []

    @classmethod
    def disable(cls):
        cls._enabled = False

    @classmethod
    def record(cls, source, change_type, context, data_hint=''):
        if not cls._enabled:
            return
        entry = {
            'source': source,
            'type': change_type,
            'context': context,
            'data_hint': data_hint,
        }
        cls._changes.append(entry)
        logger.debug(f'[DETECT] {source}: {change_type} ({context})')

    @classmethod
    def get_report(cls):
        if not cls._changes:
            return 'No structural changes detected.'
        lines = ['Detected Changes Report', '=' * 50]
        for c in cls._changes:
            lines.append(f'  [{c["type"]}] {c["source"]}')
            lines.append(f'    Context: {c["context"]}')
            if c['data_hint']:
                lines.append(f'    Data: {c["data_hint"]}')
        return '\n'.join(lines)

    @classmethod
    def clear(cls):
        cls._changes = []
