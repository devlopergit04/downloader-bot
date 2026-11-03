# PyInstaller spec for the Downloader Bot GUI (frozen single-file build).
# Build with:  pyinstaller build/downloader-bot.spec

from PyInstaller.utils.hooks import collect_all

# Bundle the media engines and their data files so the frozen app can call
# them via their Python APIs (yt_dlp, gallery_dl) at runtime.
datas, binaries, hiddenimports = [], [], []
for pkg in ("yt_dlp", "gallery_dl"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += [
    "requests", "PyQt6", "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets",
    # common yt-dlp optional deps
    "certifi", "websockets", "mutagen", "Crypto", "pycountry",
]

a = Analysis(
    ["gui_main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DownloaderBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/logo.ico" if __import__("os").path.exists("assets/logo.ico") else None,
)
