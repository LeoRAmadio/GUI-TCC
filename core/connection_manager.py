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
        self._holder = None  # (dono, callback que fecha a porta)

    def set_config(self, port: str, baud: int):
        self._port = port
        self._baud = baud
        # Notifica toda a aplicação que a porta mudou!
        self.config_updated.emit(self._port, self._baud)

    def get_port(self):
        return self._port

    def get_baud(self):
        return self._baud

    # No Windows uma porta COM só pode estar aberta em um lugar por vez ("Acesso negado").
    # Quem vai abrir a porta chama claim_port(); o dono anterior é avisado para fechá-la antes.
    def claim_port(self, owner: str, release_cb) -> None:
        holder = self._holder
        if holder is not None and holder[0] != owner:
            self._holder = None
            holder[1]()
        self._holder = (owner, release_cb)

    def release_port(self, owner: str) -> None:
        if self._holder is not None and self._holder[0] == owner:
            self._holder = None

    def is_port_present(self) -> bool:
        """Verifica se a porta configurada existe fisicamente (placa plugada no USB)."""
        if any(p.device == self._port for p in list_ports.comports()):
            return True
        # Em sistemas POSIX, cobre symlinks (/dev/serial/by-id/...) e pseudo-terminais
        return os.name != 'nt' and os.path.exists(self._port)
