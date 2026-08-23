# Changelog

All notable changes to this project are documented in this file.

## [0.3.0] - 2026-07-28

### Added

- Unity-style modal navigation for Blender's 3D Viewport.
- Configurable mouse sensitivity, acceleration, damping, speed, boost, timer interval, and speed overlay.
- Global Blender Add-on Preferences for persistent configuration.
- Automatic keymap updates when the add-on or navigation trigger changes.
- English, Simplified Chinese, and Traditional Chinese interfaces.
- Extensible JSON locale catalogs, a translation template, and locale validation tooling.
- Reproducible release ZIP build script.

### Changed

- Add-on key bindings prefer Blender's add-on keyconfig instead of modifying the primary user keyconfig.
- Navigation remembers the trigger used to start a session and exits when that same trigger is released.

### Fixed

- Add-on installation under Blender 5.2 restricted registration context.
- Translation of operator buttons such as **Rebuild GameDev Navigation Keymap**.
- Cleanup of keymaps, timers, draw handlers, and translation catalogs during disable or reload.
