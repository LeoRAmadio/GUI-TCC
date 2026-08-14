# Experimento 6: Tiling — Escalando um Hardware Pequeno para Problemas Grandes

## 1. Objetivos

Ao final desta sessão prática, você será capaz de:

- Explicar o problema fundamental que motiva a técnica de **Tiling** (também chamada *blocking*): um array de hardware fisicamente limitado precisa processar matrizes maiores que suas próprias dimensões.
- Descrever, passo a passo, como uma multiplicação de matrizes 6x6 é decomposta em uma sequência de multiplicações de blocos 3x3 compatíveis com o hardware do Experimento 5.
- Relacionar o conceito de **acumulação de parciais** (*partial sums*) entre múltiplos passes de hardware com o resultado final correto.
- Refletir sobre o custo de reuso de hardware fixo (tempo) em contraposição ao custo de construir hardware maior (área/energia).

## 2. Fundamentação Teórica e Aplicações

No Experimento 5, você trabalhou com um Systolic Array de exatamente 3x3 elementos de processamento, multiplicando matrizes de exatamente 3x3. Mas redes neurais reais trabalham com matrizes de centenas ou milhares de dimensões. Construir um array de hardware do tamanho exato de cada camada de rede neural que existe (ou que ainda vai ser inventada) é fisicamente impossível — o array precisa ter um tamanho fixo, definido uma vez na fabricação do chip.

A técnica de **Tiling** (particionamento em blocos) resolve essa limitação através de software/controle, não de hardware adicional: uma matriz grande é dividida em blocos menores, do tamanho exato que o array físico suporta, e o array processa esses blocos **um de cada vez, sequencialmente**, reutilizando o mesmo hardware físico múltiplas vezes.

Neste laboratório, uma multiplicação de matrizes 6x6 é decomposta em quatro blocos 3x3 (quadrantes) para cada matriz de entrada. A multiplicação de matrizes em blocos segue exatamente a mesma regra algébrica da multiplicação de matrizes convencional, aplicada recursivamente:

```
[A11 A12]   [B11 B12]   [ (A11·B11 + A12·B21)   (A11·B12 + A12·B22) ]
[A21 A22] × [B21 B22] = [ (A21·B11 + A22·B21)   (A21·B12 + A22·B22) ]
```

Repare que cada quadrante da matriz resultado **C** exige **duas** multiplicações de blocos 3x3 seguidas de uma soma (uma acumulação) — nunca apenas uma. É exatamente esse padrão de "carregar, multiplicar, acumular, repetir" que você vai observar na máquina de estados desta simulação.

**Por que isso importa na prática?** Toda biblioteca de deep learning industrial (cuDNN da NVIDIA, oneDNN da Intel, os compiladores de TPU do Google) implementa alguma variante sofisticada de tiling para mapear as enormes multiplicações de matrizes de uma rede neural real sobre um hardware de tamanho fisicamente fixo. O algoritmo que orquestra qual bloco carregar e quando é, com frequência, tão importante para o desempenho final quanto o próprio hardware do array multiplicador.

## 3. Trade-offs Arquiteturais

- **Tempo vs. Área de silício:** o trade-off central deste laboratório. Um array 6x6 nativo resolveria a mesma multiplicação em um único passe (mais rápido), mas custaria proporcionalmente mais área de chip, mais energia estática e um roteamento de fios muito mais complexo. Um array 3x3 com tiling resolve o mesmo problema reutilizando hardware menor **ao custo de tempo** — são necessários 4 passes (blocos) em vez de 1, cada um multiplicando parciais que ainda precisam ser somadas.
- **Custo de movimentação de dados:** cada "passo" da simulação envolve recarregar um novo par de blocos de A e B na memória local do array (visível nos quadrantes destacados). Esse recarregamento consome tempo e energia adicionais que não existiriam se o array fosse grande o suficiente para conter a matriz inteira de uma vez. Esse é o chamado custo de **movimentação de dados** (*data movement overhead*), frequentemente mais caro, em termos de energia, do que a computação aritmética em si.
- **Escalabilidade vs. complexidade de controle:** tiling permite que o *mesmo* hardware físico processe matrizes de qualquer tamanho (desde que múltiplo do tamanho do array, ou com padding), tornando o design escalável para cargas de trabalho futuras maiores. O preço dessa flexibilidade é uma lógica de controle mais sofisticada — um "escalonador" que precisa saber exatamente qual bloco carregar, quando acumular em vez de sobrescrever, e quando um quadrante de saída está definitivamente pronto.

## 4. Procedimento Prático

1. Abra a aba **Tiling**. Observe as três matrizes 6x6: **MATRIX A (INPUT)**, **MATRIX B (WEIGHTS)** e **MATRIX C (OUTPUT)**, cada uma visualmente dividida em quatro quadrantes de 3x3 por uma pequena margem entre as células.
2. Note que **MATRIX C** começa zerada, e que as matrizes A e B foram preenchidas com valores aleatórios (função `populate_random()`) — não há necessidade de calcular manualmente o resultado completo neste experimento, pois o foco é a **sequência de operações**, não os valores numéricos exatos.
3. Clique em **Step Tile** uma única vez. Observe: um quadrante de A é destacado em laranja, um quadrante de B é destacado em mostarda, e um quadrante de C é destacado em verde — simultaneamente. Leia a descrição da operação no rótulo **NPU Core**, que exibe algo como `LOADING TILES... MULTIPLY [(0, 0)] x [(0, 0)]`.
4. Leia a linha correspondente no **TILING STATE MACHINE LOG**, na parte inferior — ela documenta exatamente qual sub-multiplicação está sendo executada (por exemplo, `C_11 (P1) = A_11 * B_11`).
5. Clique em **Step Tile** novamente. Observe que o mesmo quadrante de C (`C_11`) é destacado de novo, mas desta vez a operação é rotulada como `MULTIPLY + ACCUMULATE`, e o log indica `C_11 (P2) = C_11 + (A_12 * B_21)  [C_11 DONE]`.
6. Continue clicando em **Step Tile** e, a cada passo, anote no papel: qual quadrante de A, qual quadrante de B, e qual quadrante de C estão envolvidos, e se a operação é uma primeira parcela (`P1`, sobrescreve) ou uma segunda parcela (`P2`, acumula e finaliza aquele quadrante de C).
7. Depois de observar 2 ou 3 passos manualmente, clique em **Reset Data** para reiniciar com novos valores aleatórios, e desta vez use **Auto Run** para deixar a simulação completar sozinha os 8 passos totais, em intervalos de 1,2 segundos.
8. Ao final, confirme a mensagem de sucesso no log: `[SUCESSO] Multiplicação 6x6 concluída usando hardware 3x3!`.

## 5. Análise de Resultados

Contando os passos observados no procedimento, você deve confirmar que a simulação completa uma multiplicação 6x6 usando exatamente **8 passos** de um hardware 3x3 — não 4 (um por quadrante de saída), como um raciocínio apressado poderia sugerir. Isso acontece porque, como discutido na fundamentação teórica, cada quadrante de C precisa de **duas** contribuições de blocos (`P1` e `P2`) antes de estar completo: `C_11` recebe uma contribuição de `A_11 × B_11` e outra de `A_12 × B_21`, e apenas a soma das duas está correta.

Observe atentamente a ordem em que os quadrantes de C são processados no log: `C_11`, `C_11` (de novo), `C_12`, `C_12` (de novo), `C_21`, `C_21` (de novo), `C_22`, `C_22` (de novo). Note que a simulação **termina completamente um quadrante de C** (ambas as parcelas) antes de começar o próximo — essa é uma escolha de escalonamento específica; ela poderia, em teoria, ter processado todos os `P1` de todos os quadrantes primeiro, e todos os `P2` depois. A ordem escolhida aqui minimiza o número de vezes que um resultado parcial precisa ser "guardado de lado" e recuperado depois — o quadrante de C fica ativo na memória local só pelo tempo necessário para ser somado com sua segunda parcela.

Repare também que o rótulo **NPU Core** alterna entre `MULTIPLY` (na primeira parcela) e `MULTIPLY + ACCUMULATE` (na segunda) — refletindo, em texto, exatamente a mesma distinção algébrica entre "escrever o primeiro produto" e "somar o segundo produto ao que já está lá", tal como você formalizou na Seção 2 desta aula.

## 6. Desafios Práticos e Investigação

1. **Contando o custo real de escalar.** Uma multiplicação de matrizes 3x3 no Experimento 5 levou 8 ciclos de clock do array systolic para produzir um resultado completo (do início ao fim). Uma multiplicação 6x6 aqui leva 8 *passos de tiling*, e cada passo de tiling, por trás dos panos, corresponderia a rodar o array systolic do zero (mais 8 ciclos de clock cada). Estime: quantos ciclos de clock, no total, um hardware 3x3 real levaria para completar essa multiplicação 6x6 via tiling (considerando os 8 passos observados)? Compare esse número com o tempo que um array **nativo 6x6** (hipotético, sem tiling) levaria para fazer o mesmo trabalho em um único passe. Que fator de desaceleração o tiling introduz, e por que ele não é simplesmente "o dobro", visto que a matriz dobrou de tamanho em cada dimensão?
2. **E se a matriz não for múltipla do tamanho do array?** Este laboratório usa uma matriz 6x6 dividida perfeitamente em quadrantes 3x3 (sem sobra). Na prática, uma rede neural real dificilmente terá dimensões "redondas" como essa. Pesquise (ou reflita, com base no que você já sabe de estruturas de dados) sobre a técnica de **zero-padding**: preencher artificialmente uma matriz com zeros até que suas dimensões sejam múltiplas do tamanho do array de hardware. Que desperdício computacional o zero-padding introduz (dica: pense no que acontece com um PE processando `0 × valor`)? Esse desperdício justifica, em alguns projetos de hardware reais, o uso de arrays com suporte a tamanhos variáveis ou "irregulares" — você consegue imaginar como esse tipo de suporte tornaria o controle do hardware mais complexo?
3. **Ordem alternativa de escalonamento.** No Experimento, os passos seguem a ordem: completar `C_11`, depois `C_12`, depois `C_21`, depois `C_22`. Descreva (em texto, você não precisa implementar) uma ordem alternativa de escalonamento em que todas as primeiras parcelas (`P1`) de todos os quadrantes são calculadas antes de qualquer segunda parcela (`P2`). Que vantagem essa ordem alternativa teria se os quatro blocos de entrada `A_11, A_12, A_21, A_22` estivessem sendo transferidos de uma memória externa lenta (como DRAM) e pudessem ser reaproveitados em cache antes de descartados? Relacione sua resposta ao conceito de **localidade de dados**, que você provavelmente já viu (ou verá) em Organização de Computadores ao estudar hierarquia de memória e cache.
