# Manual de Laboratório — Arquitetura de Computadores e Sistemas Embarcados

Bem-vindo(a) ao manual de laboratório do **GUI-TCC**, uma plataforma educacional que combina simulação de software e execução em hardware real (FPGA) para ensinar, na prática, os conceitos fundamentais de Arquitetura de Computadores e Sistemas Embarcados.

Cada capítulo deste manual corresponde a uma aba da interface gráfica e a um experimento de laboratório independente. Os roteiros foram escritos para serem seguidos **na ordem sugerida**, pois cada experimento constrói sobre os conceitos apresentados no anterior — começando pelo núcleo do processador e terminando em uma aplicação completa de inteligência artificial rodando em hardware dedicado.

## Como usar este manual

Cada roteiro segue a mesma estrutura:

1. **Objetivos** — o que você deve ser capaz de fazer ao final da aula.
2. **Fundamentação Teórica e Aplicações** — os conceitos necessários e sua relevância no mundo real.
3. **Trade-offs Arquiteturais** — as decisões de projeto que todo arquiteto de hardware precisa ponderar.
4. **Procedimento Prático** — o passo a passo exato para operar a interface.
5. **Análise de Resultados** — o que observar e por que o sistema se comporta daquela forma.
6. **Desafios Práticos e Investigação** — exercícios para você testar, quebrar e entender os limites do simulador.

Antes de começar, certifique-se de que o ambiente está configurado conforme o `README.md` do projeto, e que a interface gráfica (`python3 main.py`) está em execução.

## Roteiro de Experimentos

| # | Experimento | Foco |
|---|---|---|
| 1 | [O Processador RV32I Multiciclo](exp01_rv32i.md) | Datapath, ciclo de instrução, breakpoints |
| 2 | [Entrada e Saída Mapeada em Memória](exp02_io.md) | GPIO, UART, polling |
| 3 | [Acesso Direto à Memória (DMA)](exp03_dma.md) | Arbitragem de barramento, throughput vs. latência |
| 4 | [Console de um Sistema Operacional Embarcado](exp04_os_console.md) | Boot, processos, heap, panic |
| 5 | [Micro-Arquitetura de um Systolic Array (NPU)](exp05_npu.md) | MAC, output-stationary, quantização |
| 6 | [Tiling — Escalando um Hardware Pequeno](exp06_tiling.md) | Blocking, reuso de hardware, localidade |
| 7 | [Inferência de Rede Neural (MNIST)](exp07_nn.md) | Treino vs. inferência, IA na borda |
