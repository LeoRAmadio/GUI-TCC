# Experimento 1: O Processador RV32I Multiciclo

## 1. Objetivos

Ao final desta sessão prática, você será capaz de:

- Explicar, com suas próprias palavras, o que acontece dentro de um processador a cada pulso de clock, distinguindo os cinco estágios de um datapath multiciclo (**IF**, **ID**, **EX**, **MEM**, **WB**).
- Relacionar cada instrução Assembly RISC-V com o caminho de dados que ela percorre (quais estágios ela visita e quais ela pula).
- Usar *breakpoints* para pausar a execução em um ponto específico do programa e inspecionar o estado da máquina (registradores e memória).
- Comparar o comportamento do processador em **simulação local** (em Python, dentro da própria GUI) com o comportamento do **mesmo núcleo rodando em hardware real** (FPGA), percebendo o que se perde e o que se ganha em cada abordagem.

## 2. Fundamentação Teórica e Aplicações

Todo processador, por mais complexo que pareça por fora, resolve o mesmo problema repetidamente: buscar uma instrução, entender o que ela pede, executá-la e guardar o resultado. A forma como esse ciclo é organizado no tempo é uma das decisões arquiteturais mais fundamentais em Arquitetura de Computadores.

Neste laboratório usamos uma implementação **multiciclo**: cada instrução é dividida em até cinco estágios sequenciais, e a máquina avança um estágio por pulso de clock.

- **IF (Instruction Fetch)** — busca a instrução na memória de código, no endereço apontado pelo *Program Counter* (PC).
- **ID (Instruction Decode)** — interpreta o opcode e os operandos, lendo os registradores de origem necessários.
- **EX (Execute)** — a ULA (Unidade Lógico-Aritmética) realiza o cálculo: uma soma, o cálculo de um endereço de memória, ou a comparação de um desvio condicional.
- **MEM (Memory Access)** — apenas instruções de acesso à memória (`lw`, `sw`) usam este estágio para ler ou escrever um dado.
- **WB (Write-Back)** — o resultado é escrito de volta no banco de registradores.

Repare que nem toda instrução passa pelos cinco estágios. Uma instrução `add` (registrador-registrador) não precisa de **MEM**, pois não toca a memória de dados — ela pula direto de **EX** para **WB**. Já uma instrução de desvio (`beq`, `bne`, `j`) resolve tudo em **EX** e retorna direto para **IF**, sem nunca escrever em um registrador. Essa "rota variável" pelo datapath é exatamente o que torna a arquitetura multiciclo mais simples de entender do que uma arquitetura em pipeline (onde todos os estágios são sempre percorridos, mesmo que ociosos).

**Por que isso importa na prática?** Entender o datapath multiciclo é o primeiro passo para entender arquiteturas mais avançadas (pipeline, superescalar, out-of-order). Processadores embarcados de baixo custo — em microcontroladores de eletrodomésticos, sensores IoT e controladores automotivos simples — frequentemente ainda usam variantes de datapaths multiciclo ou de pipeline curto, justamente pela simplicidade de projeto, verificação e baixo consumo de área de silício.

## 3. Trade-offs Arquiteturais

Ao projetar um processador multiciclo, o arquiteto de hardware enfrenta decisões que trocam uma vantagem por uma desvantagem. Não existe "opção certa" — existe a opção certa **para um objetivo específico**.

- **Simplicidade de controle vs. Desempenho (CPI):** o datapath multiciclo tem uma unidade de controle simples (uma máquina de estados finitos, como você pode ver no código de `core/emulator.py`), mas cada instrução gasta múltiplos ciclos de clock para completar — o CPI (*Cycles Per Instruction*) é maior que 1. Um pipeline clássico busca CPI próximo de 1, ao custo de uma unidade de controle e de *forwarding* muito mais complexas.
- **Área de silício vs. Latência:** como os estágios compartilham a mesma ULA e os mesmos barramentos internos ao longo do tempo (em vez de ter uma ULA dedicada por estágio, como em pipeline), o multiciclo economiza área de chip. Essa economia de área tem um preço: a latência total de uma instrução (do IF ao WB) é maior, pois os recursos não podem ser reutilizados em paralelo por instruções diferentes.

## 4. Procedimento Prático

1. Abra a aba **RV32I** da interface. Observe que o painel esquerdo já vem populado com um código Assembly de exemplo no editor **Código Assembly**.
2. Confirme que o indicador **⚡ MODO: SIMULAÇÃO LOCAL** está ativo no topo do editor — isso indica que o emulador Python (`core/emulator.py`) está executando o código, sem nenhum hardware conectado.
3. Clique uma única vez no botão **Step (Clock)**. Observe a barra de pipeline no topo direito: o estágio **IF** deve acender.
4. Continue clicando em **Step (Clock)** repetidamente e acompanhe:
   - Qual estágio acende a cada clique;
   - As mensagens que aparecem no **OS Console / Execution Log**, na parte inferior da tela — elas descrevem exatamente o que a ULA, o decodificador ou a memória fizeram naquele ciclo;
   - Os valores no **Banco de Registradores (RegFile)**, à direita — valores que mudaram de um ciclo para o outro aparecem destacados em laranja.
5. Depois de observar alguns ciclos manualmente, clique com o botão direito sobre uma linha do editor de Assembly e escolha **🔴 Toggle Breakpoint nesta linha**. A linha ficará destacada em vermelho escuro.
6. Clique em **Run**. O botão muda para **Pause** e a execução avança automaticamente, ciclo a ciclo, até parar exatamente na linha com o breakpoint.
7. Use **⭕ Limpar Breakpoint** (no mesmo menu de contexto) para remover a marcação e clique em **Run** novamente para deixar o programa correr até o fim (**EOF**).
8. Clique em **Reset** para reiniciar o estado do emulador (PC, registradores e memória) sem alterar o código-fonte.
9. Se você tiver uma FPGA conectada, clique em **Upload FPGA** e acompanhe a barra de progresso — o código Assembly é convertido em uma imagem binária e transferido para o hardware real. Em seguida, clique em **Sync Hardware** para alternar o modo de exibição para **🔥 MODO: FPGA (HARDWARE)**.

## 5. Análise de Resultados

Ao clicar em **Step (Clock)** repetidamente para uma instrução do tipo `add rd, rs1, rs2`, você deve observar a seguinte sequência de eventos, cada um documentado no log:

- No estágio **IF**, a mensagem mostra a instrução buscada e o valor do PC no momento da busca.
- No estágio **ID**, o log informa quais registradores foram lidos e seus valores *naquele instante* — importante notar que a leitura acontece **antes** do cálculo, então esse valor ainda é o valor "antigo".
- No estágio **EX**, você vê a soma sendo realizada explicitamente (`A + B = resultado`).
- Para `add`, o estágio **MEM** é **pulado silenciosamente** — a máquina de estados do emulador (veja `clock_tick()` em `core/emulator.py`) decide isso avaliando o campo `self.op`, provando na prática que o "caminho" percorrido no datapath depende do tipo de instrução.
- No estágio **WB**, o registrador de destino é atualizado — e é exatamente nesse momento que você verá a célula correspondente na tabela **RegFile** mudar de cor.

Para uma instrução `sw` (*store word*), repare que ela **passa pelo MEM**, mas nunca chega ao **WB** — o PC é incrementado dentro do próprio estágio MEM (veja `stage_memory()`), pois não há nenhum registrador de destino a escrever. Já uma instrução `beq`/`bne`/`j` resolve tudo em **EX**, decidindo o próximo PC ali mesmo, e retorna direto para **IF** — ela nunca visita MEM nem WB.

Ao comparar o **MODO: SIMULAÇÃO LOCAL** com o **MODO: FPGA (HARDWARE)**, note que a tabela de **Memória RAM (Data)** desaparece no modo hardware. Isso acontece porque, ao rodar em uma FPGA real, a GUI não tem mais acesso direto e instantâneo ao conteúdo da memória (que agora vive fisicamente em blocos de RAM do chip) — ela depende de um canal de comunicação serial explícito para "espiar" o estado do hardware, o que é uma limitação real de observabilidade que qualquer engenheiro de bring-up de hardware enfrenta.

## 6. Desafios Práticos e Investigação

1. **Contagem de ciclos por instrução.** Escreva (ou edite o código de exemplo) um pequeno programa contendo uma instrução `add`, uma instrução `sw` e uma instrução `beq`. Usando **Step (Clock)**, conte manualmente quantos ciclos de clock cada uma dessas três instruções consome do início (IF) até retornar para IF novamente. Elas são todas iguais? Por que uma instrução de desvio "custa menos" ciclos do que uma instrução de load (`lw`)? Que consequência isso tem para o desempenho médio (CPI) de um programa cheio de desvios condicionais, como um laço `while`?
2. **Colocando um breakpoint dentro de um laço.** Marque um breakpoint em uma linha que está dentro de um laço `beq`/`bne`/`j` do código de exemplo (o Fibonacci) e clique em **Run**. Observe que a execução para *toda vez* que o PC retorna àquela linha, uma por iteração do laço. Investigue: como você usaria esse comportamento para depurar um laço infinito em um programa real, sem precisar reiniciar o processador a cada tentativa?
3. **Simulação vs. Hardware: o que se perde?** Se você tiver acesso a uma FPGA, faça o **Upload FPGA** do mesmo programa e ligue o **Sync Hardware**. Tente identificar, mesmo estando em modo hardware, o valor de uma variável que está armazenada na memória de dados. Você consegue? Escreva um parágrafo explicando por que a tabela de RAM foi ocultada nesse modo e que tipo de infraestrutura adicional (um canal de depuração, JTAG, um monitor de barramento) seria necessária para restaurar essa visibilidade sem comprometer o desempenho do hardware real.
