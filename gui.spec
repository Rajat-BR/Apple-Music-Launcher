# -*- mode: python ; coding: utf-8 -*-
#
# Builds gui.py into AppleMusicLauncher.app.
# Run on macOS with: pyinstaller gui.spec
#
# Assumes this file, gui.py, launcher_backend.py, banner.png,
# icon.png, and icon.icns all live in the same project folder.
# config.json is NOT bundled - it lives in
# ~/Library/Application Support/AppleMusicLauncher/ and is created
# automatically on first run.

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('banner.png', '.'),
        ('icon.png', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AppleMusicLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AppleMusicLauncher',
)

app = BUNDLE(
    coll,
    name='AppleMusicLauncher.app',
    icon='icon.icns',
    bundle_identifier='com.personal.applemusiclauncher',
    info_plist={
        'NSHighResolutionCapable': 'True',
    },
)
