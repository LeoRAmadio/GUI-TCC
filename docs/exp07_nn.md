# Experimento 7: Inferência de Rede Neural (MNIST) em Hardware Real

## 1. Objetivos

Ao final desta sessão prática, você será capaz de:

- Diferenciar claramente as fases de **treinamento** e de **inferência** de uma rede neural, e identificar qual delas está sendo executada fisicamente na NPU deste laboratório.
- Descrever o caminho completo de um dado, desde um desenho feito pelo usuário até uma predição numérica, passando por pré-processamento, transferência via barramento serial e execução em hardware dedicado.
- Relacionar a arquitetura *Output-Stationary* estudada no Experimento 5 com uma aplicação de reconhecimento de dígitos manuscritos do mundo real.
- Avaliar criticamente a confiança (incerteza) de uma predição de rede neural, não apenas seu resultado mais provável.

## 2. Fundamentação Teórica e Aplicações

Uma rede neural passa por duas fases distintas em seu ciclo de vida. Na fase de **treinamento**, a rede ajusta iterativamente seus milhões de parâmetros (pesos e bias) observando milhares (ou milhões) de exemplos rotulados, tipicamente em um computador com GPUs potentes, consumindo bastante tempo e energia. Na fase de **inferência**, os parâmetros já estão fixos (congelados) — a rede simplesmente recebe uma nova entrada, nunca vista antes, e produz uma predição. É a fase de inferência que precisa rodar, muitas vezes, em dispositivos de borda (*edge*) com recursos extremamente limitados — um sensor IoT, uma câmera de segurança, ou, neste laboratório, uma pequena FPGA.

Este experimento usa o clássico problema de **reconhecimento de dígitos manuscritos MNIST** como estudo de caso. O fluxo completo é:

1. O treinamento (ou carregamento de um modelo já treinado) acontece **localmente em Python, usando PyTorch**, no computador que executa esta GUI — veja `core/nn_model.py` e `core/nn_worker.py`.
2. Os pesos treinados de duas camadas (uma convolucional, `w_conv`/`b_conv`, e uma totalmente conectada, `w_fc`/`b_fc`) são então **empacotados e transferidos via porta serial** para os registradores da NPU física na FPGA (veja `core/npu_driver.py`, método `upload_modelo`).
3. A partir daí, toda a inferência acontece **fisicamente no hardware**: cada traço que você desenha na lousa é convertido em uma imagem 28x28 pixels, quantizada para inteiros de 8 bits, e enviada byte a byte para a NPU, que devolve os 10 *logits* de saída (um "placar de confiança" bruto para cada dígito de 0 a 9).

**Por que isso importa na prática?** Esse é exatamente o modelo empregado por assistentes de voz que reconhecem uma palavra de ativação sem depender da nuvem, por câmeras de segurança que detectam movimento localmente, e por qualquer aplicação de "IA na borda" (*Edge AI*) que precisa responder com baixa latência, sem depender de conectividade de rede, e com consumo de energia mínimo.

## 3. Trade-offs Arquiteturais

- **Onde treinar vs. onde inferir:** este laboratório ilustra um padrão de projeto extremamente comum na indústria — treinar em um ambiente com recursos abundantes (aqui, PyTorch rodando na CPU/GPU do computador do usuário) e implantar (*deploy*) a inferência em um ambiente de recursos escassos (a NPU da FPGA). Tentar treinar diretamente na FPGA seria impraticável com o hardware disponível; tentar depender da nuvem para cada inferência introduziria latência de rede inaceitável para uma aplicação interativa.
- **Latência de inferência vs. precisão do modelo:** a barra de status ao final de cada inferência exibe a **LATÊNCIA** medida em milissegundos. Modelos maiores e mais profundos tendem a ser mais precisos, mas também mais lentos e mais caros em termos de área de silício da NPU. O projeto de uma rede neural para inferência embarcada é sempre um exercício de equilíbrio entre acurácia aceitável e latência/custo de hardware aceitável.
- **Temperatura de calibração da confiança (Softmax):** repare, no código-fonte, uma constante `T = 15.0` usada para "esfriar" os *logits* brutos antes da normalização por Softmax (`probs = softmax(logits / T)`). Esse ajuste de temperatura não muda qual dígito a rede escolhe como resposta mais provável, mas muda **o quão confiante (ou espalhada) a distribuição de probabilidade parece** — uma decisão de calibração que afeta diretamente a interpretabilidade da saída para um ser humano, sem alterar a decisão final do classificador.

## 4. Procedimento Prático

1. Abra a aba **Neural Network Inference (MNIST)**. Note que toda a interface de desenho e inferência começa **bloqueada** (lousa acinzentada, painéis sem o brilho neon) — isso é proposital: sem pesos carregados na NPU, não faz sentido permitir desenhos.
2. Confirme (ou edite) o campo de porta serial ao lado do botão de programação (valor padrão: `/dev/ttyUSB1`).
3. Clique em **Programar FPGA**. Acompanhe a barra de carregamento e as mensagens de status na parte inferior da tela — elas devem evoluir de "Transferindo Dados..." para mensagens específicas do processo (calibração do modelo, conexão serial, upload do firmware, transferência dos pesos Conv2D via DMA).
4. Aguarde a mensagem de sucesso: "FPGA Programada com Sucesso! NPU populada e pronta para inferência." A interface deve desbloquear automaticamente, e o indicador **NPU Core** deve mudar para o estado **IDLE / READY** (com brilho roxo).
5. Desenhe um dígito de 0 a 9 na área **ENTRADA DE DESENHO (0-9)**, usando o mouse. Tente desenhar de forma razoavelmente centralizada e com traço espesso.
6. Observe, em tempo real, a área **VISÃO DA NPU (28x28)** sendo atualizada — essa é a imagem exata (reduzida, recortada e centralizada) que está sendo enviada para o hardware.
7. Solte o botão do mouse e aguarde a predição final. Leia o dígito grande no círculo **PREVISÃO** e observe a barra de status inferior, que mostra a **LATÊNCIA** medida em milissegundos daquela inferência específica.
8. Examine as dez barras em **CONFIANÇA** — cada uma corresponde à probabilidade estimada (softmax) de o desenho representar aquele dígito específico.
9. Clique em **LIMPAR LOUSA** e repita o processo desenhando um dígito ambíguo de propósito (por exemplo, um "1" muito fino, ou um "7" que possa ser confundido com "1").

## 5. Análise de Resultados

Ao desenhar um dígito claramente formado (por exemplo, um "0" bem redondo, centralizado), você deve observar uma barra de confiança dominante — próxima de 100% para o dígito correto — e as demais nove barras próximas de zero. Isso reflete uma rede neural "confiante": os *logits* brutos produzidos pela NPU para o dígito vencedor são muito maiores que os demais, e o Softmax amplifica essa diferença exponencialmente.

Ao desenhar um dígito ambíguo (como o "7" fino do passo 9 do procedimento), espere ver a barra de confiança do dígito vencedor menos dominante, com uma ou duas barras "concorrentes" (tipicamente "1" competindo com "7") exibindo uma porcentagem não-trivial. Esse é o comportamento correto e esperado de uma rede neural bem calibrada: incerteza real na entrada deve se refletir como incerteza na distribuição de probabilidade de saída, não como uma falsa confiança absoluta em uma resposta errada.

Observe também a área **VISÃO DA NPU (28x28)**: qualquer desenho que você faça, não importa onde na lousa 420x420 pixels, é recortado pela borda do desenho (`getbbox()`), redimensionado para caber em uma caixa de 20x20 mantendo a proporção original, e então centralizado dentro de uma imagem final de 28x28 preenchida com fundo preto. Esse pré-processamento existe porque o modelo foi **treinado** com imagens do dataset MNIST, que seguem exatamente essa convenção de centralização e escala — uma rede neural só funciona corretamente sobre dados que "se parecem" estatisticamente com os dados usados no seu treinamento.

Quanto à **LATÊNCIA**, ela mede o tempo entre o envio do pacote de imagem via serial e a chegada dos 10 bytes de resposta (`self.ser.read(10)` em `npu_driver.py`) — esse valor inclui não apenas o tempo de computação da NPU em si, mas também o tempo de transmissão serial (que pode ser significativo, dependendo do *baud rate* configurado).

## 6. Desafios Práticos e Investigação

1. **Ataque adversarial "manual".** Tente desenhar deliberadamente um símbolo que não é nenhum dígito reconhecível (por exemplo, um "X" grande, ou um rabisco aleatório sem forma). Observe o círculo de **PREVISÃO** e as barras de **CONFIANÇA**. A rede se recusa a responder, ou ela sempre "aposta" em algum dígito, mesmo sem ter uma base real para essa escolha? O que essa observação revela sobre uma limitação fundamental de classificadores treinados apenas para escolher "a opção menos ruim entre 10", mesmo quando nenhuma das 10 opções é realmente apropriada?
2. **Meça e explique a latência.** Realize 5 inferências consecutivas (desenhando e limpando a lousa a cada vez) e anote o valor de **LATÊNCIA** de cada uma. Os valores são consistentes entre si, ou variam significativamente? Se você tiver acesso ao parâmetro de *baud rate* da conexão serial (em `core/npu_driver.py`, o padrão é `baud=921600`), reflita: se você reduzisse esse valor pela metade, você esperaria que a latência medida aumentasse, diminuísse, ou permanecesse igual? Que parte do tempo total medido é dominada pela transmissão serial, e que parte é dominada pelo cálculo real da NPU?
3. **A temperatura Softmax e a percepção de confiança.** No código-fonte de `nn_widget.py`, localize a constante `T = 15.0`, usada para dividir os *logits* antes do cálculo do Softmax (`logits_scaled = logits_np / T`). Sem alterar o código, apenas raciocinando: se essa temperatura fosse um valor muito maior (por exemplo, `T = 100.0`), o que aconteceria com a diferença visual entre a barra do dígito vencedor e as demais barras — ficariam mais parecidas entre si, ou mais desiguais? E se `T` fosse um valor muito pequeno (`T = 1.0`)? Essa constante muda qual dígito a rede escolhe como resposta final? Por que não? Que diferença prática existe entre "mudar a decisão de uma rede neural" e "mudar apenas como comunicamos visualmente a confiança dessa decisão"?
