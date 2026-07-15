# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ["src/automate_desktop/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=["PySide6.QtSvg", "PySide6.QtNetwork"],
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
    name="Automate",
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
bundle = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Automate",
)
if sys.platform == "darwin":
    app = BUNDLE(
        bundle,
        name="Automate.app",
        icon=None,
        bundle_identifier="com.automate.desktop",
        version="0.2.0",
        info_plist={
            "CFBundleDisplayName": "Automate",
            "LSApplicationCategoryType": "public.app-category.developer-tools",
            "NSHighResolutionCapable": True,
        },
    )
