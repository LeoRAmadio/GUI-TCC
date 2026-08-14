# Experimento 3: Acesso Direto à Memória (DMA) e Arbitragem de Barramento

## 1. Objetivos

Ao final desta sessão prática, você será capaz de:

- Explicar por que um controlador de DMA existe e qual problema ele resolve em relação à transferência de dados feita exclusivamente pela CPU.
- Descrever, comparar e simular quatro políticas distintas de arbitragem de barramento: **Burst Mode**, **Cycle Stealing**, **Round-Robin** e **Weighted Priority**.
- Medir, na prática, o impacto de cada política sobre o desempenho da CPU (via *stalls*) e sobre o tempo total de uma transferência.
- Relacionar a carga de trabalho da CPU (tráfego de barramento gerado por ela) com a escolha da melhor política de arbitragem para um cenário específico.

## 2. Fundamentação Teórica e Aplicações

Imagine que seu processador precisa copiar um bloco de 10.000 palavras de um dispositivo de entrada para a memória RAM. Sem nenhum hardware auxiliar, a única forma de fazer isso é a CPU executar, ela mesma, um laço que lê uma palavra e escreve uma palavra, 10.000 vezes — gastando ciclos preciosos de busca de instrução, decodificação e execução em uma tarefa que é, essencialmente, burocrática: mover bytes de um lugar para o outro.

O **DMA (Direct Memory Access)** resolve exatamente esse problema. É um controlador de hardware dedicado que, uma vez programado pela CPU com um endereço de origem, um endereço de destino e uma contagem de palavras (o **BCR — Byte/Word Count Register**), assume sozinho a tarefa de mover os dados através do barramento do sistema, **sem** precisar da CPU para cada palavra individual. Quando termina, o DMA sinaliza a CPU com uma interrupção (IRQ), e não antes disso.

O problema é que tanto a CPU quanto o controlador de DMA precisam do mesmo recurso físico para se comunicar com a memória: o **barramento do sistema**. E um barramento, fisicamente, só pode ser utilizado por um mestre (*bus master*) por vez. É aqui que entra o **Árbitro de Barramento (Bus Arbiter)**: um componente de hardware responsável por decidir, a cada ciclo em que há conflito, quem ganha o direito de usar o barramento naquele instante.

**Por que isso importa na prática?** Qualquer sistema com um periférico de alta largura de banda — uma placa de rede, um controlador de disco, um conversor A/D de áudio ou vídeo — depende de DMA. Sem ele, a CPU de qualquer computador moderno passaria a maior parte do seu tempo copiando bytes, e não executando o software que realmente importa ao usuário.

## 3. Trade-offs Arquiteturais

A política de arbitragem escolhida pelo projetista de hardware define um espectro de comportamento entre dois extremos: dar total prioridade ao DMA (maximizando o throughput da transferência) ou dar total prioridade à CPU (minimizando a latência de resposta do processador). Este laboratório simula quatro pontos desse espectro:

- **Burst Mode `[0]`:** o DMA, uma vez com a posse do barramento, não o libera até terminar toda a transferência. **Throughput máximo** para o DMA, à custa de **latência máxima** para a CPU — que fica completamente paralisada (em *stall*) enquanto a transferência dura. Adequado quando a transferência é curta e a CPU pode esperar (ex.: inicialização de um buffer crítico).
- **Cycle Stealing `[1]`:** o DMA "rouba" apenas um ciclo por vez, sendo obrigado a devolver o barramento à CPU no ciclo seguinte. Um compromisso: a transferência demora mais para terminar (throughput reduzido), mas a CPU nunca fica presa por muito tempo (latência limitada e previsível).
- **Round-Robin `[2]`:** em caso de conflito, o árbitro simplesmente alterna, de forma justa, entre CPU e DMA (1 para 1). É uma política simples de justiça igualitária, sem considerar a urgência real de nenhum dos dois lados.
- **Weighted Priority `[3]`:** o projetista define um peso configurável (o slider **DMA Priority Weight**) que determina a probabilidade do DMA vencer um conflito. Este é o modelo mais próximo de árbitros reais configuráveis, permitindo ao projetista de sistema ajustar o equilíbrio conforme o perfil da aplicação (mais peso ao DMA para *streaming* de vídeo; mais peso à CPU para sistemas interativos sensíveis à latência).

O trade-off subjacente a todas essas políticas é sempre o mesmo: **throughput de transferência vs. latência de resposta da CPU**. Não existe política universalmente melhor — existe a política certa para a característica de carga (*workload*) do sistema.

## 4. Procedimento Prático

1. Abra a aba **DMA**. No painel esquerdo, observe o campo **Word Count (BCR):**, que define quantas palavras serão transferidas na simulação (valor padrão: 100).
2. No seletor **ARBITRATION ALGORITHM**, deixe selecionada a opção `[0] Burst Mode (DMA Locks Bus)` para a primeira rodada. Leia a descrição dinâmica que aparece logo abaixo do slider de prioridade — ela muda conforme o algoritmo selecionado.
3. Ajuste o slider **CPU Bus Req Probability** para **60%** (valor padrão) — ele controla a probabilidade, a cada ciclo, de a CPU também requisitar o barramento (simulando uma CPU ativa competindo pelo mesmo recurso).
4. Clique em **START** e observe a animação: os blocos **CPU Core**, **BUS ARBITER** e **DMA Controller**, conectados pelo **SHARED SYSTEM BUS**, acendem em laranja (CPU) ou verde (DMA) conforme o vencedor de cada ciclo.
5. Aguarde a conclusão (ou clique em **PAUSE**/**RESET** a qualquer momento). Anote os valores finais dos três contadores: **Total Clocks**, **CPU Stalls** e **DMA Stalls**.
6. Clique em **RESET**, troque o algoritmo para `[1] Cycle Stealing (Forced Alternate)`, mantenha o **Word Count (BCR)** e o **CPU Bus Req Probability** inalterados, e repita a simulação. Anote os mesmos três valores.
7. Repita o procedimento para `[2] Round-Robin (Fair 50/50)`.
8. Repita mais uma vez para `[3] Weighted Priority (Use Slider)`, testando pelo menos dois valores diferentes de **DMA Priority Weight** (por exemplo, 2 e 9).
9. Acompanhe, durante todas as execuções, o **ARBITRATION EVENT LOG** no painel direito e o **PHYSICAL MEMORY (RAM MAP)**, que preenche visualmente os blocos de memória (em verde) conforme o DMA avança na transferência.

## 5. Análise de Resultados

Ao comparar os valores de **Total Clocks** entre as quatro políticas (com o mesmo **Word Count** e a mesma **CPU Bus Req Probability**), você deve observar que o **Burst Mode** termina a transferência no menor número de ciclos possível — o DMA nunca é interrompido, então ele consome exatamente uma palavra por ciclo disponível, sem desperdício algum de sua própria perspectiva. Em contrapartida, o contador de **CPU Stalls** nessa política tende a ser o mais alto entre as quatro, pois toda colisão é resolvida a favor do DMA.

No **Cycle Stealing**, note no **ARBITRATION EVENT LOG** o padrão de alternância característico: uma mensagem "DMA rouba o bus" seguida, no ciclo imediatamente seguinte, por "DMA devolve o bus" (sempre que há colisão). Isso produz um **Total Clocks** mais alto que o Burst Mode (a transferência demora mais), mas um **CPU Stalls** proporcionalmente menor — a CPU nunca fica presa por mais de um ciclo seguido.

No modo **Weighted Priority**, repare que o resultado se aproxima do comportamento do Burst Mode quando o peso está próximo de 10, e se aproxima do comportamento onde a CPU quase sempre vence quando o peso está próximo de 0 — validando visualmente a descrição textual do painel ("Peso 10: DMA se comporta como Burst. Peso 0: CPU dita as regras").

Um detalhe sutil de se observar no **PHYSICAL MEMORY (RAM MAP)**: mesmo quando a CPU está com a posse do barramento (bloco laranja), você ocasionalmente verá células da grade piscarem em laranja de forma aleatória — isso é apenas um efeito visual do simulador para lembrar que a CPU também está *usando* a memória para suas próprias operações (não relacionadas à transferência de DMA), competindo pelo mesmo barramento físico.

## 6. Desafios Práticos e Investigação

1. **Meça o ponto de equilíbrio.** Fixe o algoritmo em `[3] Weighted Priority` e o **CPU Bus Req Probability** em 80% (uma CPU muito ativa). Execute a simulação variando o **DMA Priority Weight** em 0, 3, 5, 7 e 10, anotando o **Total Clocks** e o **CPU Stalls** de cada rodada. Construa uma tabela com seus resultados. Existe um peso a partir do qual o ganho de throughput do DMA passa a ser marginal, mas o custo em CPU Stalls continua crescendo rapidamente? Esse é o conceito de **ponto de retorno decrescente** — onde ele aparece nos seus dados?
2. **Carga de CPU extrema.** Aumente o **CPU Bus Req Probability** para 100% e compare o **Burst Mode** com o **Cycle Stealing**, mantendo o mesmo **Word Count (BCR)**. Por que, mesmo com a CPU pedindo o barramento em *todo* ciclo, o Burst Mode ainda consegue terminar a transferência rapidamente, enquanto o Cycle Stealing dobra (aproximadamente) o tempo total? O que isso revela sobre qual política seria apropriada para um sistema de tempo real crítico, onde a CPU *não pode* ficar paralisada por muito tempo, mesmo que a transferência demore mais?
3. **Round-Robin é realmente "justo"?** Compare o Round-Robin com o Weighted Priority configurado com peso 5 (que teoricamente também deveria dar 50% de chance para cada lado). Rode ambos várias vezes com o mesmo **Word Count** e **CPU Bus Req Probability**, anotando os **CPU Stalls** de cada execução. Os resultados são idênticos entre as duas políticas? Investigue no log de eventos: qual é a diferença estrutural entre "alternar deterministicamente a cada colisão" (Round-Robin) e "sortear uma probabilidade de 50% a cada colisão" (Weighted com peso 5)? Qual das duas abordagens você esperaria ver em um árbitro de hardware real, e por quê?
