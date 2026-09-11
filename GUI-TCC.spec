# GUI-TCC.spec - build do executável com PyInstaller
#   pyinstaller GUI-TCC.spec --noconfirm --workpath build/pyinstaller --distpath dist
# Gera dist/GUI-TCC/GUI-TCC.exe (modo onedir: abre rápido, sem extrair o torch a cada execução).

datas = [
    ('artifacts/kernel.bin', 'artifacts'),
    ('artifacts/cnn_server.bin', 'artifacts'),
    ('artifacts/cnn_pretrained.pth', 'artifacts'),
    ('artifacts/link.ld', 'artifacts'),
    ('artifacts/start.s', 'artifacts'),
    ('artifacts/bsp', 'artifacts/bsp'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    datas=datas,
    hiddenimports=[],
    excludes=['tkinter'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GUI-TCC',
    console=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name='GUI-TCC',
)
