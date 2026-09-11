"""
Baixa o GCC RISC-V do xPack e extrai em toolchain/ apenas o necessário para o
Lab 2 (compilação de C para rv32i/ilp32 com -nostdlib).

O pacote completo tem ~1.3 GB (multilibs, C++, Fortran, LTO, GDB + Python);
filtrar durante a extração reduz isso drasticamente e evita caminhos longos no Windows.

Uso:
    python tools/fetch_toolchain.py                      # plataforma atual
    python tools/fetch_toolchain.py --platform win32-x64 # usado no CI da release
"""
import argparse
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

VERSION = "13.4.0-1"
URL = ("https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/"
       "v{v}/xpack-riscv-none-elf-gcc-{v}-{p}.{ext}")
TRIPLET = "riscv-none-elf"
MULTILIB = ("rv32i", "ilp32")  # -march=rv32i -mabi=ilp32

KEEP_BIN = {f"{TRIPLET}-{tool}" for tool in
            ("gcc", "cpp", "as", "ld", "ld.bfd", "objcopy", "objdump", "size", "readelf", "nm")}
DROP_LIBEXEC = {"cc1plus", "f951", "lto1", "g++-mapper-server"}
DROP_LIBS = ("stdc++", "supc++", "gfortran")  # bibliotecas de C++/Fortran da multilib


def _stem(name: str) -> str:
    return name[:-4] if name.lower().endswith(".exe") else name


def _multilib_ok(parts) -> bool:
    """Mantém diretórios que não são multilib e só a multilib rv32i/ilp32."""
    if not parts[0].startswith("rv"):
        return True
    if parts[0] != MULTILIB[0]:
        return False
    if len(parts) >= 3 and any(lang in parts[-1] for lang in DROP_LIBS):
        return False
    return len(parts) < 3 or parts[1] == MULTILIB[1]


def should_keep(rel: str) -> bool:
    """Decide se um arquivo do pacote (caminho relativo à raiz dele) vai para toolchain/."""
    parts = [p for p in rel.split("/") if p]
    if not parts:
        return False
    top = parts[0]

    if top in ("share", "distro-info"):
        return False

    if top == "bin":
        if len(parts) == 1:
            return True
        if len(parts) > 2:  # bin/DLLs, bin/Lib: Python embutido do GDB
            return False
        name = parts[1].lower()
        if name.endswith(".dll"):
            return not name.startswith("python")
        return _stem(parts[1]) in KEEP_BIN

    if top == "libexec" and len(parts) >= 5:  # libexec/gcc/<triplet>/<versão>/<arquivo>
        if len(parts) > 5:  # plugin/, install-tools/
            return False
        return _stem(parts[4]) not in DROP_LIBEXEC

    if top == "lib" and len(parts) >= 2:
        if parts[1].startswith("python"):
            return False
        if parts[1] == "gcc" and len(parts) >= 5:  # lib/gcc/<triplet>/<versão>/...
            if parts[4] in ("plugin", "install-tools"):
                return False
            return _multilib_ok(parts[4:])
        return True

    if top == TRIPLET and len(parts) >= 2:
        if parts[1] == "share":
            return False
        if parts[1] == "include" and len(parts) >= 3 and parts[2] == "c++":
            return False
        if parts[1] == "lib" and len(parts) >= 3:
            return _multilib_ok(parts[2:])

    return True


def _strip_root(name: str) -> str:
    """Remove o diretório raiz do pacote (xpack-riscv-none-elf-gcc-<versão>/)."""
    return name.replace("\\", "/").split("/", 1)[1] if "/" in name.replace("\\", "/") else ""


def extract(archive: str, dest: str) -> int:
    kept = 0
    if archive.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                rel = _strip_root(info.filename)
                if info.is_dir() or not rel or not should_keep(rel):
                    continue
                target = os.path.join(dest, *rel.split("/"))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
                kept += info.file_size
    else:
        with tarfile.open(archive) as tf:
            members = []
            for m in tf.getmembers():
                rel = _strip_root(m.name)
                if not rel or not should_keep(rel):
                    continue
                m.name = rel
                if m.islnk():
                    m.linkname = _strip_root(m.linkname)
                members.append(m)
                kept += m.size
            tf.extractall(dest, members=members, filter="fully_trusted")
    return kept


def main():
    default_platform = "win32-x64" if sys.platform == "win32" else "linux-x64"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", default=default_platform, choices=["win32-x64", "linux-x64"])
    parser.add_argument("--dest", default=os.path.join(root, "toolchain"))
    parser.add_argument("--archive", help="usa um pacote já baixado em vez de baixar")
    args = parser.parse_args()

    ext = "zip" if args.platform.startswith("win32") else "tar.gz"
    with tempfile.TemporaryDirectory() as tmp:
        archive = args.archive
        if not archive:
            url = URL.format(v=VERSION, p=args.platform, ext=ext)
            archive = os.path.join(tmp, f"toolchain.{ext}")
            print(f"Baixando {url}")
            urllib.request.urlretrieve(url, archive)

        if os.path.exists(args.dest):
            shutil.rmtree(args.dest)
        print(f"Extraindo (somente C / {'/'.join(MULTILIB)}) em {args.dest}")
        kept = extract(archive, args.dest)

    print(f"Toolchain pronto: {kept / 2**20:.0f} MB")


if __name__ == "__main__":
    main()
