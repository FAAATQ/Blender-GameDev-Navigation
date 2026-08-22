import json
import sys
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = LOCALES_DIR / '_template.json'


def fail(message):
    print(f'ERROR: {message}', file=sys.stderr)
    return 1


def main():
    template = json.loads(TEMPLATE_PATH.read_text(encoding='utf-8'))
    expected_messages = set(template['messages'])
    seen_locales = set()
    errors = 0

    for path in sorted(LOCALES_DIR.glob('*.json')):
        if path.name.startswith('_'):
            continue

        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as error:
            errors += fail(f'{path.name}: invalid JSON: {error}')
            continue

        locale = data.get('locale')
        aliases = data.get('aliases', [])
        messages = data.get('messages')

        if not isinstance(locale, str) or not locale:
            errors += fail(f'{path.name}: locale must be a non-empty string')
        if not isinstance(aliases, list) or not all(isinstance(alias, str) and alias for alias in aliases):
            errors += fail(f'{path.name}: aliases must contain non-empty strings')
            aliases = []
        if not isinstance(messages, dict) or not all(
            isinstance(source, str) and isinstance(translation, str)
            for source, translation in messages.items()
        ):
            errors += fail(f'{path.name}: messages must map strings to strings')
            continue

        for locale_id in (locale, *aliases):
            if locale_id in seen_locales:
                errors += fail(f'{path.name}: duplicate locale or alias {locale_id}')
            seen_locales.add(locale_id)

        missing = expected_messages - set(messages)
        unknown = set(messages) - expected_messages
        empty = sum(not translation for translation in messages.values())
        if missing:
            errors += fail(f'{path.name}: missing keys: {sorted(missing)}')
        if unknown:
            errors += fail(f'{path.name}: unknown keys: {sorted(unknown)}')

        print(f'{path.name}: {len(messages) - empty}/{len(expected_messages)} translated')

    if errors:
        print(f'Locale validation failed with {errors} error(s).', file=sys.stderr)
        return 1

    print('All locale catalogs are valid.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
