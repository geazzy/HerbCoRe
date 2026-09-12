Esta análise examina a base de dados de exsicatas digitalizadas da tabela **manifesto_imagens**, juntamente com as diretrizes de anotação registradas na aba **divisão**. O conjunto de dados compõe um acervo estruturado de imagens de plantas para pesquisa taxonômica e treinamento de modelos de visão computacional (segmentação binária de máscaras).

---

### 1. Estruturação Balanceada do Dataset Taxonômico

O acervo apresenta um planejamento de amostragem perfeitamente equilibrado entre táxons, o que favorece o treinamento homogêneo de modelos de inteligência artificial sem viés de classe.

* **Distribuição Uniforme por Família e Espécie:** A base contém exatas **1.000 exsicatas digitalizadas** (100% com status de metadados válidos), distribuídas igualmente em **10 famílias botânicas** (100 espécimes cada): *Asteraceae*, *Cyperaceae*, *Lauraceae*, *Malpighiaceae*, *Melastomataceae*, *Meliaceae*, *Myrtaceae*, *Pteridaceae*, *Sapindaceae* e *Solanaceae*.
* **Controle Estrito por Espécie:** Cada uma das 10 famílias é representada por exatamente **5 espécies** (totalizando 50 espécies), possuindo cada espécie uma cota fixa de **20 imagens digitalizadas** (ex.: *Baccharis dracunculifolia*, *Nectandra megapotamica*, *Solanum americanum*).
* **Pipeline de Anotação Mapeado:** A aba de divisão estabelece atribuições específicas de segmentação manual de imagem por responsável (ex.: João atribuído a *Lauraceae*, *Myrtaceae* e *Cyperaceae*; Geazzy atribuído a *Solanaceae* e *Malpighiaceae*), definindo o padrão de máscara binária (fundo preto e área vegetal em branco).

---

### 2. Concentração Institucional e Rede de Herbários Provedores

Apesar do equilíbrio taxonômico, a origem física dos espécimes digitalizados é concentrada em um número reduzido de acervos botânicos de grande porte.

* **Ampla Rede com Núcleo Centralizador:** Um total de **59 herbários** contribuem com imagens para o projeto. Contudo, os **5 principais herbários** respondem por **480 dos 1.000 registros (48,0%)**.
* **Destaques de Contribuição:** O gráfico **"Principais Herbários Provedores de Imagens (Top 10)"** ilustra a liderança do *New York Botanical Garden* (NY) com **136 exsicatas (13,6%)**, seguido pelo *Herbário da Universidade Federal de Uberlândia* (HUFU) com **105 exsicatas (10,5%)**, a *Universidade Estadual de Feira de Santana* (HUEFS) com **95 (9,5%)**, o *Museu Botânico Municipal de Curitiba* (MBM) com **72 (7,2%)** e a *Universidade Federal do Paraná* (UPCB) com **70 (7,0%)**.
* **Integração Internacional:** Embora a imensa maioria dos espécimes provenha de acervos nacionais, parcerias internacionais como o herbário NY e a inclusão de coletas em países vizinhos (como Guiana, Paraguai, Argentina e Colômbia) enriquecem a representatividade da coleção.

---

### 3. Cobertura Geográfica e Recorte Temporal das Coletas

A profundidade temporal e espacial da coleção reflete a evolução histórica da amostragem botânica no Brasil, concentrando-se nas últimas quatro décadas.

* **Amplitude Temporal Quase Bi-secular:** As datas de coleta documentadas nas exsicatas variam do ano de **1831 até 2025**.
* **Pico de Amostragem Contemporâneo:** Como observado no gráfico **"Evolução Histórica do Volume de Coletas por Década"**, o volume de amostras cresce expressivamente a partir da década de 1960 (60 amostras), atingindo seu ápice entre 1980 e 2019, período que concentra **814 das 1.000 exsicatas (81,4%)**. As décadas mais representadas são os anos 2000 (**281 coletas**) e 1990 (**224 coletas**).
* **Concentração Geográfica Regional:** O gráfico **"Distribuição Geográfica das Coletas por Estado (Top 10)"** evidencia que a amostragem provém predominantemente do Sul e Sudeste do Brasil, liderada pelo estado do **Paraná (211 coletas; 21,1%)**, seguido por **Minas Gerais (142 coletas; 14,2%)**, **São Paulo (131 coletas; 13,1%)**, **Bahia (101 coletas; 10,1%)** e **Santa Catarina (84 coletas; 8,4%)**.

---

### Premissas e Notas Metodológicas

* As siglas estaduais (ex.: *PR*, *SP*, *MG*) foram padronizadas aos nomes completos dos estados correspondentes para evitar duplicidades de contagem.
* O conjunto de dados selecionado pela célula ativa foi interpretado como o contexto geral da tabela principal (`manifesto_imagens`).
