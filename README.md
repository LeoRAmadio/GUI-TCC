# GUI-TCC — Plataforma Didática RISC-V

Aplicação desktop (PyQt5) para ensino de Arquitetura de Computadores e Sistemas Embarcados, combinando **simulação de software** e **execução em hardware real** (FPGA) sobre um SoC RISC-V.

Cada aba da interface é um experimento independente, cobrindo desde o datapath de um processador multiciclo até a inferência de uma rede neural acelerada por uma NPU dedicada:

| Aba | Módulo | Foco |
|---|---|---|
| **RV32I** | `ui/tabs/rv32i_widget.py` | Datapath multiciclo (IF/ID/EX/MEM/WB), registradores, breakpoints |
| **I/O** | `ui/tabs/io_widget.py` | GPIO/UART mapeados em memória, compilação C → FPGA |
| **DMA** | `ui/tabs/dma_widget.py` | Arbitragem de barramento, Burst/Cycle Stealing/Round-Robin/Weighted |
| **OS Console** | `ui/tabs/os_console_widget.py` | Multitarefa preemptiva (CLINT/PLIC), heap e desfragmentação |
| **NPU** | `ui/tabs/npu_widget.py` | Systolic Array 3x3, pipeline de pós-processamento (PPU) |
| **Tiling** | `ui/tabs/tiling_widget.py` | Multiplicação de matrizes em blocos sobre hardware pequeno |
| **Neural Network** | `ui/tabs/nn_widget.py` | Inferência MNIST na NPU (PyTorch + hardware) |

## Estrutura do projeto

```
GUI-TCC/
├── main.py              # Ponto de entrada da aplicação
├── ui/                   # Widgets e estilos da interface (PyQt5)
│   └── tabs/             # Um widget por experimento/aba
├── core/                 # Modelos e lógica de simulação (emulador, NPU, drivers seriais)
├── controllers/          # Camada de controle (MVC) entre UI e core
├── artefacts/            # Binários e firmware (kernel, bootloader, pesos treinados)
├── build/                # Artefatos de build gerados para a FPGA
└── docs/                 # Manual de laboratório (MkDocs) — ver seção abaixo
```

## Como rodar a aplicação

1. Crie o ambiente virtual:
```bash
python3 -m venv .venv
```

2. Ative o ambiente:
```bash
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip3 install -r requirements.txt
```

4. Execute o script de entrada:
```bash
python3 main.py
```

> Para usar as abas que dependem de hardware real (Upload FPGA, Sync Hardware, OS Console, NN Inference), é necessário ter a placa FPGA conectada via USB/serial.

## Manual de Laboratório

Os roteiros didáticos de cada experimento estão em [`docs/`](docs/index.md), publicados como um site com [MkDocs](https://www.mkdocs.org/). Para visualizar, acesso o link: [Roteiros](https://risc-v-azedinha.github.io/GUI-TCC/exp01_rv32i/).