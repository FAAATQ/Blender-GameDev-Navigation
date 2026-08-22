# Contributing Translations

The add-on loads translation catalogs automatically from this directory. Adding a language does not require changes to `Blender-GameDev-Navigation.py`.

## Add a language

1. Copy `_template.json` to a file named after Blender's locale, for example `ja_JP.json`.
2. Set `locale` to the locale used by Blender.
3. Add compatibility locale identifiers to `aliases` only when needed.
4. Translate values in `messages`. Keep every English key unchanged because it must match the source UI text exactly.
5. Empty translations are ignored, so incomplete catalogs are allowed.
6. Save the file as UTF-8 JSON and submit it in a pull request.

Example:

```json
{
  "locale": "ja_JP",
  "aliases": [],
  "language": "日本語",
  "messages": {
    "Enable GameDev Navigation": "GameDev ナビゲーションを有効化"
  }
}
```

## Validation

From the repository root, validate every catalog against the complete template with:

```bash
python locales/validate.py
```

The validator rejects malformed JSON, duplicate locale aliases, missing source keys, and unknown source keys. Empty translation values are allowed for work-in-progress catalogs and are ignored at runtime.

Then install the complete add-on directory or release ZIP in Blender, select the language under **Edit → Preferences → Interface → Translation**, and verify:

- **Edit → Preferences → Add-ons → GameDev Navigation**

## Packaging note

The translation files are runtime resources. A release must include both `Blender-GameDev-Navigation.py` and the `locales/` directory. Installing the Python file by itself still works, but only the built-in English UI is available.
