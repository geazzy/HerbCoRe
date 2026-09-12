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

A composição do acervo segue critérios de escopo taxonômico, origem das imagens, resolução mínima e unicidade da coleta. Esses critérios definem o que entra no manifesto e o que pode ser substituído.

#### Escopo taxonômico

O acervo cobre dez famílias botânicas. Em cada família foram escolhidas **cinco espécies comuns**, com identificadores de referência (especialistas) usados como filtro `identifiedby` na busca. A imagem precisa ter sido identificada por um especialista da família em `familias.txt`. Nem todos os taxonomistas da lista precisam aparecer no manifesto: eles autorizam a busca. Só entram imagens cujo identificador está nessa lista para a família.

| Família | Taxonomistas de referência | Espécies |
|---|---|---|
| Lauraceae | M.L. Brotto, H. van der Werff | *Nectandra megapotamica*, *Ocotea puberula*, *Ocotea pulchella*, *Endlicheria paniculata*, *Nectandra lanceolata* |
| Myrtaceae | M. Sobral | *Myrcia guianensis*, *Eugenia florida*, *Eugenia punicifolia*, *Myrciaria floribunda*, *Blepharocalyx salicifolius* |
| Solanaceae | J.R. Stehmann, L.A. Mentz | *Solanum americanum*, *Solanum pseudoquina*, *Petunia integrifolia*, *Cestrum strigilatum*, *Solanum sisymbriifolium* |
| Malpighiaceae | M.C.H. Mamede, W.R. Anderson, R.F. Almeida | *Byrsonima intermedia*, *Niedenzuella multiglandulosa*, *Alicia anisopetala*, *Diplopterys pubipetala*, *Byrsonima crassifolia* |
| Cyperaceae | R. Trevisan, M. Alves | *Cyperus hermaphroditus*, *Fimbristylis dichotoma*, *Eleocharis montana*, *Eleocharis sellowiana*, *Eleocharis maculosa* |
| Meliaceae | T.D. Pennington, J.R. Pirani | *Guarea guidonia*, *Guarea kunthiana*, *Trichilia pallida*, *Cedrela fissilis*, *Trichilia catigua* |
| Pteridaceae | J. Prado, F. Gonzatti, A.L. Gasper, P. Labiak, A. Salino | *Vittaria lineata*, *Pityrogramma calomelanos*, *Adiantum latifolium*, *Doryopteris concolor*, *Adiantum raddianum* |
| Asteraceae | J.N. Nakajima, G. Heiden | *Heterocondylus alatus*, *Chromolaena laevigata*, *Lepidaploa rufogrisea*, *Baccharis linearifolia*, *Baccharis dracunculifolia* |
| Melastomataceae | R. Goldenberg, F.S. Meyer, F.A. Michelangeli | *Miconia pusilliflora*, *Miconia albicans*, *Acisanthera alsinaefolia*, *Chaetogastra gracilis*, *Tococa guianensis* |
| Sapindaceae | M.S. Ferrucci, A. Rosado, P. Acevedo-Rodríguez | *Urvillea ulmacea*, *Serjania lethalis*, *Paullinia elegans*, *Matayba guianensis*, *Allophylus edulis* |

#### Fonte, formato e organização

* **Fonte:** galeria pública do speciesLink (`flags=photo`), com família e nome científico da espécie.
* **Download:** JPEG via endpoint `osd-dezoomify`. Só é aceito arquivo que começa com assinatura JPEG (`FF D8`) e tem tamanho útil.
* **Caminho:** `10familias/<Família>/<Espécie>/<CODIGO>.jpg` (espaços e caracteres especiais viram `_`).
* **Inventário:** `10familias/manifesto_imagens.csv` — uma linha por imagem.
* **Cobertura espacial:** não há filtro geográfico nem de herbário. O conjunto concentra registros do Brasil, mas inclui outros países quando a imagem atende aos demais critérios.

#### Resolução mínima

Largura **e** altura devem ser **≥ 1024 px**. A galeria do speciesLink já informa dimensões; candidatas abaixo do limiar nem são baixadas. Depois do download, a resolução real é medida no arquivo. Se falhar o limiar, o JPEG é apagado e o código não entra no manifesto.

#### Unicidade da coleta (duplicata de herbário)

Duplicata, neste acervo, é a **mesma coleta** depositada em herbários diferentes, e não a segunda foto do mesmo barcode.

A chave de coleta (`chave_coleta`) junta:

1. **primeiro coletor**, sem acento, só letras e números, em maiúsculas;
2. **número do coletor**, nas mesmas regras.

Exemplos de número tratado como ausente (não geram chave): `s.n.`, `s/n`, `sn`, `sine numero`, `sem número`. Sem coletor **ou** sem número, a chave fica vazia e a folha não entra no agrupamento de duplicatas.

No grupo com a mesma `chave_coleta` e barcodes diferentes:

* **mantém-se a de maior resolução** (maior área em pixels);
* empate: `TRUE` > `PENDENTE` > demais;
* empate seguinte: código.

A extra só sai se existir substituta com **outra** `chave_coleta`, ainda não usada no acervo. Sem substituta, a extra permanece.

#### Coletor e número (`s.n.`)

Prefere-se folha com coletor **e** número de coleta, para permitir a marcação de duplicata. Imagens sem `chave_coleta` foram trocadas quando havia substituta com chave inédita. Sem substituta com coletor e número, a imagem antiga **não é removida**.

Exceção conhecida no acervo atual: `SMDB005093` (*Cestrum strigilatum*, coletor Silva, E.M.A., sem número). O speciesLink não ofereceu outra folha com número para essa espécie/especialista.
