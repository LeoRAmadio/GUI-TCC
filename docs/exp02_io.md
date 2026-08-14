# Experimento 2: Entrada e Saída Mapeada em Memória (GPIO & UART)

## 1. Objetivos

Ao final desta sessão prática, você será capaz de:

- Explicar o conceito de **I/O mapeado em memória** (*memory-mapped I/O*) e diferenciá-lo de arquiteturas com espaço de I/O separado.
- Escrever, compilar e transferir firmware em linguagem C real para um SoC RISC-V físico, fechando o ciclo completo *edit → compile → flash → observe*.
- Interpretar o **mapa de memória do SoC**, relacionando cada endereço físico a um periférico concreto (LEDs, chaves, UART).
- Reconhecer, no próprio código C, o padrão de *polling* usado para sincronizar o processador com um periférico serial mais lento que ele.

## 2. Fundamentação Teórica e Aplicações

Um processador, sozinho, não serve para muita coisa: ele precisa conversar com o mundo exterior — acender um LED, ler uma chave, enviar texto para um terminal. A técnica mais comum para viabilizar essa conversa em sistemas embarcados é o **I/O mapeado em memória**: em vez de criar instruções especiais de entrada/saída, o projetista de hardware simplesmente reserva uma faixa de endereços do espaço de memória e conecta essa faixa, via barramento, aos registradores de controle dos periféricos. Para o software, ler ou escrever em um LED é *literalmente idêntico* a ler ou escrever em uma posição de memória comum — o truque todo está em qual endereço você usa.

No código C desta aba, essa ideia aparece de forma explícita:

```c
#define GPIO_BASE 0x20000000
#define REG_LEDS  (*(volatile uint32_t *)(GPIO_BASE + 0x00))
```

A palavra-chave `volatile` é crucial e frequentemente mal compreendida por iniciantes: ela instrui o compilador a **nunca otimizar** o acesso àquela variável, porque seu valor pode mudar por razões que o compilador não enxerga (o hardware, não o próprio programa, alterando o conteúdo). Sem `volatile`, um compilador agressivo poderia perceber que o programa "nunca lê de volta" o valor escrito em `REG_LEDS` e simplesmente eliminar a escrita como código morto — um bug clássico e traiçoeiro em programação de baixo nível.

A UART (*Universal Asynchronous Receiver/Transmitter*) é o periférico serial mais onipresente em sistemas embarcados: é o canal usado por praticamente todo microcontrolador para depuração via terminal, antes mesmo de existir uma interface gráfica ou uma pilha USB. Ela é lenta, simples e assíncrona (não compartilha um sinal de clock entre transmissor e receptor) — exatamente por isso, é o primeiro periférico que qualquer engenheiro de firmware aprende a dominar.

## 3. Trade-offs Arquiteturais

- **Polling vs. Interrupção:** o driver `uart_putc()` deste laboratório usa *polling*: `while (REG_UART_STATUS & UART_TX_BUSY);`. O processador fica preso em um laço, consultando repetidamente um bit de status, até que a UART sinalize que está livre. Essa abordagem é simples de implementar e depurar, mas desperdiça ciclos de CPU que poderiam estar executando outra tarefa. A alternativa — I/O orientado a interrupção — libera a CPU para fazer outra coisa enquanto espera, mas exige uma unidade de controle de interrupções e um tratamento de contexto muito mais complexo (você vai revisitar essa tensão de forma mais estruturada no laboratório de **DMA**).
- **Espaço de endereçamento compartilhado vs. dedicado:** ao mapear periféricos no mesmo espaço de endereços usado para instruções e dados, o projetista simplifica o conjunto de instruções (nenhuma instrução `IN`/`OUT` especial é necessária), mas "rouba" endereços que poderiam ser usados por memória RAM. Em sistemas com pouca memória, essa decisão de particionamento do mapa de endereços é uma escolha de projeto delicada.
- **Throughput vs. simplicidade do protocolo:** a UART transmite um bit por vez, de forma serial, o que a torna extremamente lenta comparada a um barramento paralelo. Mas seu protocolo simples (poucos fios, sem necessidade de clock compartilhado) a torna barata, robusta a ruído em distâncias maiores, e universal — daí sua sobrevivência em praticamente todo projeto embarcado, décadas depois de sua criação.

## 4. Procedimento Prático

1. Abra a aba **I/O**. Note que o modo de operação está fixo em **HARDWARE (GCC TOOLCHAIN)** — diferentemente do laboratório do RV32I, aqui não existe simulação local: o código é sempre compilado por um toolchain GCC real para RISC-V e executado fisicamente na FPGA.
2. Leia o código C padrão carregado no editor **FIRMWARE EM C**. Identifique as definições de `REG_LEDS`, `REG_SW` e os registradores da UART.
3. Observe a tabela **SOC MEMORY MAP**, no painel direito, e associe cada linha (`GPIO_LED_DATA`, `GPIO_SW_DATA`, `GPIO_HEX_DATA`, `UART_TX_DATA`) ao respectivo `#define` no código. Note a coluna **Type**: repare que `GPIO_SW_DATA` é **RO** (*Read-Only*) e `UART_TX_DATA` é **WO** (*Write-Only*) — isso já é uma pista sobre a direção do fluxo de dados de cada periférico.
4. Clique em **Compile & Flash FPGA**. Acompanhe a barra de progresso e o console inferior, que exibe a saída do processo de compilação (GCC) em tempo real.
5. Após a mensagem de sucesso, clique dentro do **INTERACTIVE UART CONSOLE** (o terminal com fundo preto e texto verde) e observe o texto chegando automaticamente — o firmware, uma vez em execução, começa a transmitir a sequência de Fibonacci via `uart_puts()`.
6. Digite qualquer caractere dentro do terminal UART. Note que **nada aparece imediatamente** na tela ao digitar — isso é intencional (veja o comentário no código-fonte de `UARTTerminal`, que desabilita o "eco local"). O caractere só reaparecerá na tela se o firmware C, rodando na FPGA, o ler de volta pela FIFO da UART e o retransmitir.
7. Edite o programa: altere o valor de um dos `for` de delay (por exemplo, o `for (i = 0; i < 100000; i++)` dentro do laço de Fibonacci) para um valor bem menor, e clique em **Compile & Flash FPGA** novamente para observar o efeito.

## 5. Análise de Resultados

Ao observar o **INTERACTIVE UART CONSOLE**, você deve notar que os LEDs físicos da placa piscam em sincronia com os números impressos no terminal — ambos são resultado da mesma variável `nextTerm`, escrita simultaneamente em `REG_LEDS` (uma escrita instantânea, paralela, de 16 bits) e transmitida via `uart_puts()` (uma transmissão serial, bit a bit, lenta). Essa diferença de velocidade entre um periférico paralelo (GPIO) e um periférico serial (UART) é visível a olho nu: o LED "salta" para o novo valor instantaneamente, enquanto o texto correspondente ainda está sendo digitado na tela, caractere por caractere.

Se você reduziu o valor do laço de delay no desafio 3 do procedimento, deve ter percebido que o terminal passa a receber texto mais rápido do que consegue exibir de forma legível, ou até que caracteres pareçam se perder ou embaralhar. Isso acontece porque a função `uart_putc()` é bloqueante — ela força a CPU a esperar (`while (REG_UART_STATUS & UART_TX_BUSY)`) — então tecnicamente nenhum dado é perdido do lado do transmissor, mas a taxa de geração de dados pode superar a capacidade humana (ou até do próprio buffer do terminal gráfico) de acompanhar visualmente.

Repare também que a rotina `print_dec()` implementa manualmente a divisão por 10 usando `simple_div_mod()`, em vez de simplesmente escrever `n / 10`. O comentário no código ("Sem LibGCC") indica o motivo: em muitos ambientes *bare-metal* minimalistas, o compilador não tem acesso à biblioteca padrão que implementa divisão inteira de 32 bits em software, então essa operação teria que ser fornecida manualmente — um lembrete prático de que, em sistemas embarcados, operações que parecem triviais em um computador de propósito geral podem exigir implementação explícita.

## 6. Desafios Práticos e Investigação

1. **Read-Only na prática.** O registrador `GPIO_SW_DATA` é marcado como **RO** na tabela de mapa de memória. Modifique o código C para ler continuamente `REG_SW` dentro do laço principal e enviar seu valor via `uart_puts()`/`print_dec()`, em vez de gerar a sequência de Fibonacci. Compile e observe o resultado no terminal. Por que faria sentido, do ponto de vista do hardware, que esse registrador nunca aceite escrita da CPU? O que aconteceria (na teoria) se um firmware mal-escrito tentasse escrever nele mesmo assim?
2. **Quantificando o custo do polling.** Modifique `uart_putc()` para incrementar um contador global toda vez que o laço `while (REG_UART_STATUS & UART_TX_BUSY);` executa uma iteração (ou seja, toda vez que a CPU "espera" pela UART). Imprima esse contador periodicamente. Compare o valor do contador ao transmitir uma string curta versus uma string longa. O que esse número representa em termos de ciclos de CPU desperdiçados? Guarde essa observação — você vai revisitar esse mesmo problema, mas resolvido de outra forma, no laboratório de **DMA**.
3. **Frequência de atualização vs. legibilidade.** Reduza drasticamente (ou remova) os laços de delay `for (i = 0; i < 500000; i++);` do programa original e recompile. Descreva o que acontece com a legibilidade do terminal UART e com o piscar dos LEDs. Depois, aumente o delay para um valor 10x maior que o original. Existe um valor de delay "ótimo"? O que esse experimento revela sobre a relação entre a velocidade de geração de dados por parte da CPU e a velocidade fixa de transmissão de um canal serial?
