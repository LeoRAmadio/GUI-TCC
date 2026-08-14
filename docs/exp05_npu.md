# Experimento 5: Micro-Arquitetura de um Systolic Array (NPU)

## 1. Objetivos

Ao final desta sessão prática, você será capaz de:

- Explicar por que multiplicação de matrizes é a operação central de uma rede neural e por que ela justifica um acelerador de hardware dedicado.
- Descrever o funcionamento ciclo a ciclo de um **Systolic Array** (arranjo sistólico) *Output-Stationary* 3x3, incluindo o papel do *skew* espacial dos dados de entrada.
- Manipular manualmente os pesos e ativações de entrada e prever o resultado da multiplicação antes de o hardware confirmá-lo.
- Compreender o papel de uma **PPU (Post-Processing Unit)** no pipeline de inferência, incluindo bias, ativação ReLU e quantização.

## 2. Fundamentação Teórica e Aplicações

O núcleo de praticamente toda operação de rede neural — de uma camada totalmente conectada a uma convolução — é a multiplicação de matrizes: uma sequência massiva de multiplicações e somas (operações *Multiply-Accumulate*, ou **MAC**). Em uma CPU convencional, essa operação é feita basicamente uma multiplicação por vez, usando a ULA de propósito geral. Para redes neurais de qualquer porte razoável, isso é lento demais.

Um **Systolic Array** é uma arquitetura especializada para acelerar exatamente esse tipo de cálculo. A ideia central: em vez de um único elemento de processamento (PE) fazendo todo o trabalho sequencialmente, uma **grade bidimensional de pequenos elementos de processamento** (aqui, 3x3 = 9 PEs) processa os dados em paralelo, com cada dado "pulsando" (daí o nome *systolic*, uma analogia às contrações cardíacas) de um PE para o vizinho a cada ciclo de clock — como um coração bombeando dados através do array.

Este laboratório implementa a variante **Output-Stationary**: cada PE é responsável por calcular e **acumular** um único elemento fixo da matriz de saída C, do início ao fim. Os dados de entrada (matriz A) fluem horizontalmente através das linhas, e os pesos (matriz B) fluem verticalmente através das colunas — enquanto o **resultado parcial permanece parado** (*stationary*) dentro do PE, sendo incrementado a cada ciclo.

Para que os dados cheguem a cada PE no momento certo (sincronizados com os dados vizinhos necessários para o cálculo), a matriz de entrada precisa passar por um **skew espacial**: zeros são inseridos como atraso artificial antes das linhas/colunas mais profundas do array, garantindo que o PE `(r, c)` só comece a calcular no ciclo `r + c`, exatamente quando os dois operandos corretos chegam simultaneamente até ele.

**Por que isso importa na prática?** Arranjos sistólicos são a base de aceleradores de IA reais e comerciais — a TPU (*Tensor Processing Unit*) do Google, por exemplo, usa exatamente essa arquitetura em escala muito maior (arrays de 128x128 ou mais). Entender um array 3x3 manualmente, ciclo a ciclo, é o caminho mais direto para entender por que esse tipo de hardware processa redes neurais ordens de grandeza mais rápido que uma CPU de propósito geral.

## 3. Trade-offs Arquiteturais

- **Output-Stationary vs. outras estratégias de fluxo de dados:** existem outras variantes de systolic array (*Weight-Stationary*, *Input-Stationary*), cada uma otimizando a reutilização de um operando diferente para minimizar o tráfego de memória. A escolha Output-Stationary, usada aqui, minimiza o movimento do acumulador (que fica parado), mas exige que tanto A quanto B fluam continuamente através do array — uma decisão de projeto que impacta diretamente o consumo de energia, já que mover dados através de um chip consome mais energia do que a própria operação aritmética.
- **Tamanho do array vs. área de silício e potência:** um array 3x3 é pequeno o suficiente para observar manualmente, mas na prática limita o tamanho da multiplicação que pode ser feita em um único passe (você vai revisitar esse limite diretamente no próximo laboratório, sobre **Tiling**). Arrays maiores processam mais dados por ciclo, mas custam proporcionalmente mais área de chip e potência dissipada — um trade-off de **Área vs. Desempenho**.
- **Quantização (Int8) vs. precisão numérica:** o toggle **Quantization (Int8)** na PPU reduz a precisão do resultado (de um acumulador amplo para um valor limitado a 8 bits com sinal, entre -128 e 127), truncando o valor (`val >> 2`) e saturando os extremos. Essa perda de precisão é aceita deliberadamente na indústria de aceleradores de IA porque reduz drasticamente o consumo de memória, a largura de banda necessária e a energia por operação — com impacto geralmente pequeno na acurácia final da rede, se calibrado corretamente.

## 4. Procedimento Prático

1. Abra a aba **NPU**. Observe as três matrizes no topo: **INPUT MEMORY (A)**, à esquerda, com valores editáveis pré-preenchidos de 1 a 9; **WEIGHT MEMORY (B)**, acima do array, pré-preenchida como uma matriz identidade (1 na diagonal, 0 nas demais posições).
2. Antes de rodar, calcule manualmente (no papel) o resultado esperado de `C = A × B` com os valores padrão. Como B é a matriz identidade, o que você espera que aconteça com C?
3. Clique em **Step Clock** uma única vez. Observe o contador **Global Clock** (que deve ir de 0 para 1) e note que as células `A[0][0]` e `B[0][0]` ficam destacadas (coloridas sólidas) — indicando que esse par de valores acabou de "entrar" no PE `PE_00`.
4. Continue clicando em **Step Clock** e acompanhe, dentro de cada bloco da **SYSTOLIC ARRAY (CORE)**, os valores de `a*b` (multiplicação sendo realizada naquele ciclo) e o acumulador crescendo a cada ciclo subsequente.
5. Observe atentamente em qual ciclo cada PE exibe o rótulo **DONE** — anote a relação entre a posição `(r, c)` do PE e o número do ciclo em que ele termina.
6. Continue até o final (8 ciclos) e compare os valores finais em **OUTPUT MEMORY (C)** com o cálculo manual que você fez no passo 2.
7. Clique em **Reset** (se disponível) ou recarregue a página, e desta vez ative o toggle **Add Bias (+5)** no painel **PPU PIPELINE** antes de rodar novamente com **Auto Run**. Compare os novos valores de saída.
8. Repita o processo ativando **ReLU Activation** com uma matriz A contendo pelo menos um valor negativo (edite manualmente uma célula da matriz A para um número negativo antes de rodar).
9. Por fim, ative **Quantization (Int8)** e observe o efeito sobre valores de saída que ultrapassem o intervalo de -128 a 127.

## 5. Análise de Resultados

Se você usou os valores padrão (B = matriz identidade), o resultado em **OUTPUT MEMORY (C)** deve ser idêntico à matriz A original — multiplicar qualquer matriz pela identidade a preserva. Esse é um bom "teste de sanidade" para confirmar que você entendeu corretamente o fluxo de dados antes de passar a matrizes mais complexas.

Observando os PEs individualmente, você deve confirmar que o PE `PE_00` (canto superior esquerdo) é o primeiro a exibir **DONE**, seguido por `PE_01` e `PE_10` no mesmo ciclo, e assim sucessivamente em diagonais — uma consequência direta do *skew* espacial mencionado na fundamentação teórica: o PE na posição `(r, c)` só recebe seus dois operandos completos no ciclo `r + c`, e passa dois ciclos acumulando parcelas antes de finalizar. Isso demonstra visualmente por que a "onda" de processamento se propaga na diagonal, de canto a canto, em vez de terminar todos os PEs simultaneamente.

Ao comparar as execuções com e sem o **Add Bias (+5)** ativado, você deve observar que *todo* elemento da saída aumenta em exatamente 5 unidades — o bias é aplicado uniformemente, após o cálculo do produto matricial, e antes de qualquer outra etapa da PPU. Já com **ReLU Activation** ativado (que já vem ligado por padrão) e um valor negativo na entrada, você deve observar que qualquer resultado negativo é zerado (`max(0, val)`) — o comportamento clássico da função de ativação ReLU usada extensivamente em redes neurais modernas.

Com **Quantization (Int8)** ativado, note que o valor exibido passa por duas transformações visíveis no código: uma divisão por 4 (aproximando uma redução de escala de um acumulador maior para 8 bits) seguida de um *clipping* (saturação) para o intervalo [-128, 127]. Se um dos seus valores de saída, antes da quantização, era muito grande, você deve observar o valor final "grudado" exatamente em 127 (ou -128, se negativo) — a assinatura visual de saturação numérica.

## 6. Desafios Práticos e Investigação

1. **Multiplicação não-trivial.** Substitua a matriz B por uma matriz de sua escolha (não a identidade) e recalcule manualmente o produto esperado `C = A × B` no papel, célula por célula. Rode a simulação completa com **Auto Run** e compare cada célula da saída com sua conta manual. Se houver alguma divergência, revise seu cálculo — o simulador reflete fielmente a matemática de multiplicação de matrizes.
2. **A ordem dos operadores da PPU importa?** No código-fonte (`npu_widget.py`, método `update_ui`), observe que a PPU aplica, nesta ordem fixa: Bias → ReLU → Quantização. Ative **Add Bias (+5)** e **ReLU Activation** simultaneamente, usando uma matriz A com um valor bem negativo (por exemplo, -20) na posição que gera a saída `C[0][0]`. Calcule manualmente dois cenários: (a) aplicar bias antes do ReLU, como o simulador faz, e (b) aplicar ReLU antes do bias, invertendo a ordem. Os resultados são diferentes? Em que caso um valor originalmente negativo "sobrevive" ao ReLU graças ao bias, e em que caso ele seria zerado de qualquer forma? Por que a ordem das operações em um pipeline de pós-processamento de rede neural não é arbitrária?
3. **Custo da quantização em valores pequenos.** Configure a matriz A e B de forma que o resultado esperado em pelo menos uma célula de C seja um número pequeno, como 1, 2 ou 3 (sem bias, sem ReLU). Ative apenas **Quantization (Int8)** e observe o que acontece com esse valor pequeno após a divisão por 4 (deslocamento de 2 bits). Existe perda de informação mesmo para valores que já cabem folgadamente em 8 bits? Isso te ajuda a entender por que, na prática, engenheiros de Machine Learning aplicam uma técnica chamada *calibração de escala* antes de quantizar uma rede neural real — em vez de usar um fator de escala fixo (aqui, sempre dividir por 4) para todas as camadas?
