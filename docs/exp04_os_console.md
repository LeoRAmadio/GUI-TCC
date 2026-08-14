# Experimento 4: Multitarefa, Interrupções e Memória Dinâmica em um SO Embarcado

## 1. Objetivos

Ao final desta sessão prática, você será capaz de:

- Comprovar, observando o terminal, que o **Uptime** e o **LED** são *tarefas* independentes do SO — rodando concorrentemente com o shell e com a *task idle* — e não apenas texto impresso pelo comando que você digitou.
- Relacionar esse comportamento concorrente ao **CLINT** (*Core Local Interruptor*), o periférico que gera interrupções de tempo (*timer ticks*) usadas pelo escalonador para trocar de tarefa.
- Relacionar a digitação no terminal ao **PLIC** (*Platform-Level Interrupt Controller*), o periférico que roteia a interrupção de "caractere recebido na UART" até a tarefa correta.
- Usar os comandos de heap para observar, na prática, alocação dinâmica de memória e o efeito de uma rotina de desfragmentação.

## 2. Fundamentação Teórica e Aplicações

Um SO só é realmente um SO quando consegue fazer **mais de uma coisa ao mesmo tempo** com um único núcleo. Este laboratório conecta você, via porta serial, a um SO minimalista rodando sobre o mesmo núcleo RV32I do Experimento 1 — mas agora com um *scheduler* de verdade orquestrando várias tarefas.

Duas peças de hardware tornam isso possível:

- **CLINT (Core Local Interruptor):** um temporizador de hardware que dispara uma interrupção em intervalos regulares (o *tick* do sistema). É essa interrupção que o *scheduler* usa para **interromper a tarefa atual à força** e dar a vez à próxima — o mecanismo que torna o *multitasking* **preemptivo** (a tarefa não precisa "pedir licença" para ser trocada).
- **PLIC (Platform-Level Interrupt Controller):** um roteador de interrupções externas — de periféricos como a UART — até o núcleo. Quando você digita um caractere, a UART não é *checada* repetidamente (isso seria *polling*, como no Experimento 2); ela **avisa** a CPU através do PLIC, que acorda a tarefa responsável por tratar aquele caractere.

Com esses dois mecanismos, o kernel mantém pelo menos quatro tarefas rodando "ao mesmo tempo" (na verdade, se revezando rapidamente no único núcleo disponível):

| Tarefa | O que faz | Disparada por |
|---|---|---|
| **Shell** | Lê o que você digita e executa macros/comandos | Interrupção da UART (via PLIC) |
| **Uptime** | Incrementa um contador de tempo decorrido | Interrupção do timer (via CLINT) |
| **LED** | Alterna o estado de um LED periodicamente | Interrupção do timer (via CLINT) |
| **Idle** | Não faz nada de útil — só "ocupa" o processador quando nenhuma outra tarefa tem trabalho | Executa quando o *scheduler* não tem mais nada para escalonar |

Além do escalonamento, o kernel também gerencia **memória dinâmica**: cada vez que uma tarefa precisa de um bloco de memória, o alocador de heap procura um espaço livre compatível. Blocos alocados e liberados repetidamente, em tamanhos variados, tendem a deixar a memória livre **fragmentada** — espalhada em pedaços pequenos, mesmo que a soma total ainda seja suficiente. Um `Defrag Heap` reorganiza esses pedaços.

**Por que isso importa na prática?** Esse trio — timer de escalonamento, controlador de interrupções externas e alocador de heap — é o coração de praticamente qualquer RTOS real (FreeRTOS, Zephyr) e do próprio kernel do Linux. Entender esses três mecanismos em um SO de poucas KB é a forma mais direta de entender como qualquer SO maior faz a mesma coisa em escala.

## 3. Trade-offs Arquiteturais

- **Preemptivo (CLINT) vs. Cooperativo:** um *scheduler* preemptivo (baseado em timer) garante que nenhuma tarefa monopolize a CPU para sempre, mesmo que tenha um bug (laço infinito). O custo é a complexidade de salvar/restaurar o contexto de uma tarefa interrompida a qualquer momento, e o overhead de executar a própria rotina de interrupção do timer com frequência.
- **Interrupção (PLIC) vs. Polling:** como no Experimento 2, checar repetidamente um periférico gasta ciclos de CPU. Usar o PLIC libera a CPU para executar outras tarefas (ou a *task idle*, economizando energia) enquanto nada acontece na UART — ao custo de uma lógica de hardware adicional para priorizar e rotear interrupções de múltiplas fontes.
- **Granularidade do tick do timer:** um tick muito frequente torna a troca de tarefas mais responsiva (o **Uptime** e o **LED** parecem mais "suaves"), mas cada interrupção consome ciclos de CPU só para o próprio mecanismo de troca de contexto — um tick raro demais economiza CPU, mas torna o sistema menos responsivo.
- **Heap dinâmico vs. alocação estática:** liberdade de alocar/liberar em tempo de execução tem o preço da fragmentação. Sistemas embarcados críticos (marcapassos, freios ABS) costumam evitar heap dinâmico por completo, preferindo alocação estática — sem esse risco, mas sem flexibilidade.

## 4. Procedimento Prático

**Parte A — Comprovando a concorrência (o ponto mais importante deste laboratório)**

1. Abra a aba **OS Console** e clique em **OPEN CONNECTION**.
2. Assim que o console ficar disponível, **não digite nada ainda**. Apenas observe a barra de status: **Uptime** deve estar contando sozinho e **LED** deve estar piscando sozinho.
3. Agora digite um comando qualquer, como `help`, mas **antes de apertar Enter**, pause por 5 a 10 segundos olhando para a barra de status.
4. Observe: o **Uptime** continua incrementando e o **LED** continua alternando **enquanto o caractere fica parado no *prompt*, esperando você apertar Enter**.
5. Confirme o comando com Enter e clique em **Process Status** para ver a lista de tarefas ativas no kernel — procure pelas tarefas Shell, Uptime, LED e Idle (ou nomes equivalentes).

**Parte B — Heap e fragmentação**

6. Clique em **Heap Usage** e anote os números exibidos (memória livre, usada, maior bloco livre).
7. Se o `help` listar algum comando de alocação manual, use-o para alocar 4 ou 5 blocos pequenos e libere alguns deles fora de ordem (por exemplo, o 1º e o 3º).
8. Rode **Heap Usage** novamente e compare com o passo 6. Em seguida, rode **Defrag Heap** e consulte **Heap Usage** uma última vez.

**Parte C — Falha controlada**

9. Clique em **Trigger Panic** e leia a saída com calma — é o comportamento esperado.
10. Finalize com **Reboot OS**, ou desconecte pelo botão **✕** no canto superior direito do terminal.

## 5. Análise de Resultados

O ponto central deste laboratório é o que você observou na **Parte A**: o **Uptime** e o **LED** nunca param, **mesmo que você não aperte tecla nenhuma, mesmo enquanto você está digitando**. Se este fosse um sistema de tarefa única (*bare-metal*, como no Experimento 1), o contador de tempo só avançaria quando o código chegasse até a linha que o incrementa — e ficaria parado à espera do Enter. O fato de ele **não parar** é a prova direta de que existe um *scheduler* preemptivo, orquestrado pelas interrupções do **CLINT**, trocando entre a tarefa Shell (parada, esperando você digitar) e as tarefas Uptime/LED (que continuam avançando) várias vezes por segundo, sem que você perceba a troca.

Quando você digita um caractere, é o **PLIC** que acorda a tarefa Shell — ela não estava "checando o teclado" o tempo todo (isso desperdiçaria CPU e roubaria tempo das tarefas Uptime/LED); ela estava dormente até a interrupção da UART avisar que havia um caractere novo para tratar. Em **Process Status**, você deve ver essa tarefa alternando entre um estado de "bloqueada/dormente" (esperando entrada) e "pronta/rodando" (processando o comando).

Na **Parte B**, compare os números de **Heap Usage** antes e depois das alocações irregulares: a memória *livre total* pode continuar praticamente a mesma, mas o tamanho do **maior bloco livre contíguo** tende a diminuir — esse é o sintoma clássico de fragmentação. Depois do **Defrag Heap**, esse maior bloco contíguo deve crescer de volta, mesmo sem nenhuma memória adicional ter sido liberada — a defragmentação reorganiza o que já existia, não cria memória nova.

## 6. Desafios Práticos e Investigação

1. **Meça a granularidade do tick.** Usando o **Uptime**, cronometre (com um relógio externo) quanto tempo real leva para o contador avançar uma unidade. Em seguida, tente estimar quantas vezes por segundo o CLINT deve estar interrompendo o processador para manter esse contador tão preciso quanto ele aparenta ser — lembre-se de que cada interrupção de tick também precisa "dar carona" para o *scheduler* verificar se é hora de trocar de tarefa. O que aconteceria com a resposta do shell às suas teclas se esse tick fosse 100x mais raro?
2. **Prove a concorrência sem olhar para o Uptime.** Descubra uma forma diferente de provar que a tarefa LED roda de forma independente do shell — por exemplo, mantenha pressionada uma tecla, gerando uma rajada rápida de interrupções da UART, e observe se o LED continua piscando no mesmo ritmo ou se "engasga". O que esse comportamento (ou a ausência dele) revela sobre a prioridade relativa que o *scheduler* dá à tarefa LED em comparação à tarefa Shell?
3. **Fragmentação proposital.** Repita a Parte B, mas desta vez tente criar deliberadamente um cenário onde uma alocação **falha** por fragmentação (memória total livre suficiente, mas nenhum bloco contíguo grande o bastante). Anote a sequência exata de alocações/liberações que você usou. Depois, rode **Defrag Heap** e confirme que a mesma alocação passa a funcionar. Que garantias o *scheduler* precisaria dar (por exemplo: pausar outras tarefas?) para que mover blocos de memória em uso durante a defragmentação não corrompa um ponteiro que outra tarefa ainda está usando?
