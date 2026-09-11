import os
from serial.tools import list_ports
from PyQt5.QtCore import QObject, pyqtSignal

class ConnectionManager(QObject):
    """
    Singleton que gere globalmente as configurações da Porta Serial.
    Qualquer widget pode assinar o sinal 'config_updated' para atualizar a sua UI.
    """
    _instance = None
    _initialized = False

    # Sinal emitido sempre que as configurações mudam (envia porta e baudrate)
    config_updated = pyqtSignal(str, int)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # O Python chama __init__ a cada ConnectionManager(); reinicializar o QObject
        # descartaria as conexões de sinal já feitas pelas outras abas.
        if ConnectionManager._initialized:
            return
        super().__init__()
        ConnectionManager._initialized = True
        # Configurações padrão seguras (podem ser lidas de um ficheiro JSON/INI no futuro)
        self._port = "/dev/ttyUSB1"
        self._baud = 921600

    def set_config(self, port: str, baud: int):
        self._port = port
        self._baud = baud
        # Notifica toda a aplicação que a porta mudou!
        self.config_updated.emit(self._port, self._baud)

    def get_port(self):
        return self._port

    def get_baud(self):
        return self._baud

    def is_port_present(self) -> bool:
        """Verifica se a porta configurada existe fisicamente (placa plugada no USB)."""
        if any(p.device == self._port for p in list_ports.comports()):
            return True
        # Em sistemas POSIX, cobre symlinks (/dev/serial/by-id/...) e pseudo-terminais
        return os.name != 'nt' and os.path.exists(self._port)
