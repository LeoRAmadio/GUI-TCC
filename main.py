# main.py
import os
import sys
import platform

# =====================================================================
# TRUQUES AGRESSIVOS PARA MODO ESCURO E SCALING (LINUX & WINDOWS)
# =====================================================================
if platform.system() == "Linux":
    # Desativa o Wayland nativo para o Qt (que força barras brancas e causa erros)
    # e força o uso do servidor X11 (XWayland), que respeita o Dark Mode do sistema.
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
    os.environ['GTK_THEME'] = 'Adwaita:dark'

    # FIX DO ZOOM: Desativa o auto-scaling agressivo do Linux e aplica um zoom
    # manual de 125% (1.25). Se achar que ainda está pequeno, mude para '1.5'.
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
    os.environ['QT_SCALE_FACTOR'] = '1.50'

elif platform.system() == "Windows":
    sys.argv += ['-platform', 'windows:darkmode=1']

# --selftest: usado pelo CI da release. Abre a janela principal, fecha em seguida e grava
# o resultado em selftest.log (o executável não tem console para exibir erros).
SELFTEST = "--selftest" in sys.argv


def main():
    # O torch precisa ser carregado ANTES do PyQt5: no Windows, o Qt traz um runtime
    # Visual C++ antigo (msvcp140 14.26) e, se ele for carregado primeiro, as DLLs do
    # torch (compiladas com MSVC >= 14.40) falham ao inicializar ("WinError 1114").
    import torch  # noqa: F401

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer, Qt
    from ui.styles import STYLESHEET

    from core.emulator import RISCV_Emulator
    from core.npu import NPUModel
    from ui.main_window import RiscVEduApp
    from controllers.main_controller import MainController
    from controllers.npu_controller import NPUController
    from core.toolchain import add_bundled_to_path, find_toolchain

    # Disponibiliza o GCC RISC-V distribuído com a aplicação (Lab 2) para os subprocessos
    add_bundled_to_path()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # FIX DA LINHA: Limpeza rigorosa das bordas e alturas para garantir
    # que o menu da esquerda e o cabeçalho casam pixel a pixel.
    PATCH_CSS = """
    #AppTitle {
        min-height: 70px;
        max-height: 70px;
        border: none;
        border-bottom: 1px solid #1e293b;
        margin: 0px;
        padding: 0px 20px;
    }
    #Header {
        min-height: 70px;
        max-height: 70px;
        border: none;
        border-bottom: 1px solid #1e293b;
        margin: 0px;
        padding: 0px;
    }
    """
    app.setStyleSheet(STYLESHEET + PATCH_CSS)

    main_window = RiscVEduApp()

    rv32i_model = RISCV_Emulator()
    rv32i_controller = MainController(rv32i_model, main_window.rv32i_view)
    main_window.stacked_widget.currentChanged.connect(rv32i_controller.on_tab_changed)

    rv32i_controller.io_view = main_window.io_view
    main_window.io_view.request_compile_and_upload.connect(rv32i_controller.handle_io_compile_upload)
    main_window.io_view.request_uart_send.connect(rv32i_controller.handle_io_uart_transmit)

    npu_model = NPUModel()
    npu_controller = NPUController(npu_model, main_window.npu_view)

    app.aboutToQuit.connect(rv32i_controller.cleanup_hardware)

    main_window.show()

    if SELFTEST:
        toolchain = find_toolchain()
        _selftest_log(f"torch {torch.__version__}: tensor {torch.ones(2).sum().item()}")
        _selftest_log(f"toolchain: {toolchain[0] if toolchain else 'NAO ENCONTRADO'}")
        _selftest_log(f"janela principal: {main_window.windowTitle()}")
        QTimer.singleShot(1500, app.quit)

    sys.exit(app.exec_())


def _selftest_log(line: str) -> None:
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "selftest.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    if not SELFTEST:
        main()
    else:
        try:
            main()
        except SystemExit as exit_:
            _selftest_log("OK" if not exit_.code else f"FALHA: código de saída {exit_.code}")
            raise
        except BaseException:
            import traceback
            _selftest_log("FALHA:\n" + traceback.format_exc())
            os._exit(1)
