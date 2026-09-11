# GUI-TCC.spec - build do executável com PyInstaller
#   pyinstaller GUI-TCC.spec --noconfirm --workpath build/pyinstaller --distpath dist
# Gera dist/GUI-TCC/GUI-TCC.exe (modo onedir: abre rápido, sem extrair o torch a cada execução).
import os
import sys

datas = [
    ('artifacts/kernel.bin', 'artifacts'),
    ('artifacts/cnn_server.bin', 'artifacts'),
    ('artifacts/cnn_pretrained.pth', 'artifacts'),
    ('artifacts/link.ld', 'artifacts'),
    ('artifacts/start.s', 'artifacts'),
    ('artifacts/bsp', 'artifacts/bsp'),
]

# GCC RISC-V do Lab 2, baixado antes do build por: python tools/fetch_toolchain.py
if os.path.isdir('toolchain'):
    datas.append(('toolchain', 'toolchain'))

a = Analysis(
    ['main.py'],
    pathex=[],
    datas=datas,
    hiddenimports=[],
    excludes=['tkinter'],
    noarchive=False,
)
# Runtime do Visual C++: o PyQt5 traz o seu próprio msvcp140/vcruntime140 14.26, antigo demais
# para as DLLs do torch (MSVC >= 14.40), o que faz o import do torch falhar com "WinError 1114".
# Mantém uma única cópia, a mais nova (a do Windows onde o build roda), na raiz do pacote.
VC_RUNTIME = ('msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'msvcp140_atomic_wait.dll',
              'msvcp140_codecvt_ids.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'concrt140.dll')
if sys.platform == 'win32':
    system32 = os.path.join(os.environ['SystemRoot'], 'System32')
    a.binaries = [b for b in a.binaries if os.path.basename(b[0]).lower() not in VC_RUNTIME]
    a.binaries += [(dll, os.path.join(system32, dll), 'BINARY')
                   for dll in VC_RUNTIME if os.path.exists(os.path.join(system32, dll))]

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
