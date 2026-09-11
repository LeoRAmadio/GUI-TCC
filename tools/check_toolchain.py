"""
Verifica o GCC RISC-V compilando o firmware padrão do Lab 2 com os mesmos
parâmetros usados pela aplicação (core.toolchain.gcc_command).

Uso:
    python tools/check_toolchain.py                    # qualquer toolchain encontrado
    python tools/check_toolchain.py --require-bundled  # exige o de toolchain/ (CI da release)
"""
import argparse
import ast
import os
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.toolchain import add_bundled_to_path, bundled_bin_dir, find_toolchain, gcc_command  # noqa: E402

ENTRY_ADDR = 0x80000800  # ORIGIN(ram) em artifacts/link.ld


def default_firmware() -> str:
    """Extrai o código C padrão do editor do Lab 2 (ui/tabs/io_widget.py) sem importar o Qt."""
    with open(os.path.join(ROOT, "ui", "tabs", "io_widget.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "default_code" for t in node.targets):
            return node.value.value
    sys.exit("ERRO: default_code não encontrado em ui/tabs/io_widget.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--require-bundled", action="store_true")
    args = parser.parse_args()

    add_bundled_to_path()
    toolchain = find_toolchain()
    if toolchain is None:
        sys.exit("ERRO: nenhum GCC RISC-V encontrado")
    gcc, objcopy, libc_flags = toolchain
    print(f"gcc:     {gcc}")
    print(f"objcopy: {objcopy}")
    print(f"libc:    {'picolibc' if libc_flags else 'newlib'}")

    if args.require_bundled and not os.path.normcase(gcc).startswith(os.path.normcase(bundled_bin_dir())):
        sys.exit("ERRO: o GCC encontrado não é o distribuído em toolchain/")

    with tempfile.TemporaryDirectory() as tmp:
        c_file = os.path.join(tmp, "firmware.c")
        elf_path = os.path.join(tmp, "firmware.elf")
        bin_path = os.path.join(tmp, "firmware.bin")
        with open(c_file, "w", encoding="utf-8") as f:
            f.write(default_firmware())

        for cmd in (gcc_command(gcc, libc_flags, elf_path, c_file), [objcopy, "-O", "binary", elf_path, bin_path]):
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(result.stdout + result.stderr)
                sys.exit(f"ERRO: {os.path.basename(cmd[0])} falhou (código {result.returncode})")

        with open(elf_path, "rb") as f:
            f.seek(0x18)  # e_entry (ELF32)
            entry = struct.unpack("<I", f.read(4))[0]
        size = os.path.getsize(bin_path)

    if entry != ENTRY_ADDR:
        sys.exit(f"ERRO: ponto de entrada 0x{entry:08X}, esperado 0x{ENTRY_ADDR:08X}")
    print(f"OK: firmware do Lab 2 compilado ({size} bytes, entrada 0x{entry:08X})")


if __name__ == "__main__":
    main()
