import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / 'dist'
PACKAGE_NAME = 'blender_gamedev_navigation'
ARCHIVE_NAME = 'Blender-GameDev-Navigation.zip'
STAGING_DIR = DIST_DIR / PACKAGE_NAME
ARCHIVE_PATH = DIST_DIR / ARCHIVE_NAME


def main():
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True)

    shutil.copy2(ROOT / 'Blender-GameDev-Navigation.py', STAGING_DIR / '__init__.py')
    shutil.copytree(
        ROOT / 'locales',
        STAGING_DIR / 'locales',
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
    )

    with zipfile.ZipFile(ARCHIVE_PATH, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(STAGING_DIR.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(DIST_DIR))

    shutil.rmtree(STAGING_DIR)
    print(ARCHIVE_PATH)


if __name__ == '__main__':
    main()
