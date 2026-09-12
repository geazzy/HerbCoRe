# Critérios do dataset `10familias`

Documento dos critérios usados para montar o acervo de exsicatas em `10familias/`. A fonte das imagens é o [speciesLink](https://specieslink.net/). A lista de famílias, espécies e taxonomistas de referência está em `familias.txt`.

Estado atual: **1.000 imagens JPEG**, **10 famílias**, **5 espécies por família**, **20 imagens por espécie**.

---

## 1. Escopo taxonômico

O acervo cobre dez famílias botânicas. Em cada família foram escolhidas **cinco espécies comuns**, com identificadores de referência (especialistas) usados como filtro `identifiedby` na busca.

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

Nem todos os taxonomistas da lista precisam aparecer no manifesto: eles autorizam a busca. Só entram imagens cujo identificador está nessa lista para a família.

---

## 2. Fonte, formato e organização

- **Fonte:** galeria pública do speciesLink (`flags=photo`), com família e nome científico da espécie.
- **Download:** JPEG via endpoint `osd-dezoomify`. Só é aceito arquivo que começa com assinatura JPEG (`FF D8`) e tem tamanho útil.
- **Caminho:** `10familias/<Família>/<Espécie>/<CODIGO>.jpg` (espaços e caracteres especiais viram `_`).
- **Inventário:** `10familias/manifesto_imagens.csv` — uma linha por imagem.
- **Não há filtro geográfico nem de herbário.** O conjunto concentra registros do Brasil, mas inclui outros países quando a imagem atende aos demais critérios.

---

## 3. Cota por espécie

Cada espécie deve ter **exatamente 20 imagens**.

- Trocas mantêm a cota: uma removida, uma substituta da mesma família e espécie.
- Se a espécie ficar abaixo de 20, busca-se complemento só com os especialistas de `familias.txt`.
- Sem substituta válida, a imagem antiga **permanece** (não se reduz a cota à força).

---

## 4. Tipo de imagem: só exsicata

O acervo é de **pranchas de herbário** (exsicatas). Fotos de planta viva, detalhes de rótulo isolado e outras cenas fora da prancha são recusadas.

A coluna `exsicata?` no manifesto registra a revisão:

| Valor | Significado |
|---|---|
| `TRUE` | Confirmada visualmente como exsicata |
| `FALSE` | Não é exsicata — removida e substituída |
| `PENDENTE` | Substituta nova, ainda sem revisão visual |

Imagens `FALSE` não permanecem no conjunto.

**Filtro automático de foto de campo:** dimensões típicas de foto de planta viva (menor lado entre 1900 e 2100 px e maior lado ≤ 3200 px, padrão observado em folhas MO ~2000×3008) são recusadas na galeria e depois do download.

---

## 5. Resolução mínima

Largura **e** altura devem ser **≥ 1024 px**.

- A galeria do speciesLink já informa dimensões; candidatas abaixo do limiar nem são baixadas.
- Depois do download, a resolução real é medida no arquivo. Se falhar o limiar, o JPEG é apagado e o código não entra no manifesto.
- Imagens que já estavam no acervo abaixo de 1024 px foram listadas e substituídas.

---

## 6. Taxonomista de referência

A imagem precisa ter sido identificada por um especialista da família em `familias.txt`.

- A busca prioriza `identifiedby` com esses nomes.
- Imagens cujo taxonomista **não** estava na lista foram removidas e substituídas.
- Substitutas herdam a família e a espécie e só entram se o identificador for um dos autorizados.

---

## 7. Unicidade do espécime (código / vistas)

Cada imagem no acervo corresponde a **um código único**. Não se reutiliza:

- código já presente no manifesto;
- código já descartado (`10familias/codigos_descartados.csv`);
- código já removido no rastreio de substituições.

**Vistas do mesmo espécime** (mesmo barcode com sufixo `_e1`, `_v1`, `_nd1`, `_1`, `_01` etc.) contam como o mesmo registro. Só uma vista permanece.

Quando há várias vistas, a mantida é a melhor nesta ordem:

1. `exsicata?` `TRUE`, depois `PENDENTE`, depois o restante;
2. código sem sufixo de vista, preferido ao código com sufixo;
3. menor número no sufixo;
4. código em ordem lexicográfica.

---

## 8. Unicidade da coleta (duplicata de herbário)

Duplicata aqui é a **mesma coleta** depositada em herbários diferentes, não a segunda foto do mesmo barcode.

A chave de coleta (`chave_coleta`) junta:

1. **primeiro coletor**, sem acento, só letras e números, em maiúsculas;
2. **número do coletor**, nas mesmas regras.

Exemplos de número tratado como ausente (não geram chave): `s.n.`, `s/n`, `sn`, `sine numero`, `sem número`. Sem coletor **ou** sem número, a chave fica vazia e a folha não entra no agrupamento de duplicatas.

No grupo com a mesma `chave_coleta` e barcodes diferentes:

- **mantém-se a de maior resolução** (maior área em pixels);
- empate: `TRUE` > `PENDENTE` > demais;
- empate seguinte: código.

A extra só sai se existir substituta com **outra** `chave_coleta`, ainda não usada no acervo. Sem substituta, a extra permanece.

---

## 9. Coletor e número (`s.n.`)

Prefere-se folha com coletor **e** número de coleta, para dar para marcar duplicata.

- Imagens sem `chave_coleta` foram trocadas quando havia substituta com chave inédita.
- Sem substituta com coletor e número, a imagem antiga **não é removida**.

Exceção conhecida no acervo atual: `SMDB005093` (*Cestrum strigilatum*, coletor Silva, E.M.A., sem número). O speciesLink não ofereceu outra folha com número para essa espécie/especialista.

---

## 10. Códigos excluídos em definitivo

Todo código removido entra em `10familias/codigos_descartados.csv` e não volta a ser baixado (nem outra vista do mesmo prefixo).

Motivos registrados:

| Motivo | O que foi recusado |
|---|---|
| `nao_exsicata` | Não é prancha de herbário |
| `resolucao_menor_1024` | Largura ou altura abaixo de 1024 px |
| `vista_duplicada` | Segunda (ou posterior) vista do mesmo barcode |
| `taxonomista_nao_listado` | Identificador fora de `familias.txt` |
| `coletor_ou_numero_ausente` | Sem coletor/número, substituída por folha com chave |
| `duplicata_coleta` | Extra da mesma coleta, substituída por outra coleta |

---

## 11. Regras da substituta

Uma candidata só entra se cumprir **todos** os itens abaixo:

1. mesma família e mesma espécie da imagem a repor (ou da cota a completar);
2. identificada por taxonomista de referência da família;
3. código e prefixo de barcode livres (acervo, rastreio e lista de descartados);
4. largura e altura ≥ 1024 px no arquivo baixado;
5. não parecer foto de campo (heurística da seção 4);
6. ser JPEG válido;
7. nos lotes de `s.n.` e de duplicata de coleta: ter `chave_coleta` preenchida **e inédita** no acervo.

Substituta nova entra no manifesto como `exsicata?=PENDENTE` até a revisão visual.

---

## 12. Metadados gravados no manifesto

Depois do download, cada código é consultado no registro público do speciesLink. Campos usados no acervo:

- identificação: barcode, herbário, instituição, número de catálogo, nome científico, autor, determinador;
- coleta: coletor, primeiro coletor, número, chave de coleta, ano/mês/dia;
- local: país, estado, município, localidade, latitude, longitude, altitude;
- outros: notas, tipo (type status), URL do registro;
- flags internas: `duplicata_acervo`, `n_duplicatas_acervo`, `duplicatas_codigos`, `status_metadados`.

A marcação `duplicata_acervo=TRUE` só ocorre quando **dois ou mais prefixos de barcode** compartilham a mesma `chave_coleta`. Vistas do mesmo espécime não contam como duplicata de coleta.

---

## 13. Sincronização e rastreio

Cada troca (remoção + inclusão) é lançada em `rastreio_substituicoes.csv`, com caminho local e caminho no Google Drive (`Família/Espécie/CODIGO.jpg`). Lotes usados:

- `nao_exsicata`
- `vistas_duplicadas`
- `taxonomista_nao_listado`
- `baixa_resolucao`
- `sem_chave_coleta`
- `duplicata_coleta`
- `completar`

O Drive é o espelho de `10familias/` (imagens + `manifesto_imagens.csv` + `codigos_descartados.csv`).

---

## 14. Estado atual (após os filtros)

| Critério | Situação |
|---|---|
| Imagens | 1.000 |
| Espécies com 20 imagens | 50 / 50 |
| `exsicata?=TRUE` | 910 |
| `exsicata?=PENDENTE` | 90 (aguardam revisão visual) |
| `exsicata?=FALSE` | 0 |
| Resolução &lt; 1024 px | 0 |
| Duplicata de coleta no acervo | 0 |
| Sem coletor/número | 1 (`SMDB005093`) |
| Metadados do speciesLink | 1.000 com `status_metadados=ok` |

As 90 `PENDENTE` vieram das últimas trocas (77 `s.n.` + 13 duplicatas de coleta) e ainda precisam de conferência visual para virar `TRUE` ou ser trocadas de novo se não forem exsicata.

---

## 15. Arquivos de referência

| Arquivo | Papel |
|---|---|
| `familias.txt` | Famílias, espécies e taxonomistas de referência |
| `10familias/manifesto_imagens.csv` | Inventário completo (caminhos, resolução, `exsicata?`, metadados) |
| `10familias/codigos_descartados.csv` | Códigos que não devem ser baixados de novo |
| `rastreio_substituicoes.csv` | Histórico de remoções e inclusões (também usado no Drive) |
| `ferramenta_herbcore/baixar_imagens_especies.py` | Download inicial (cota, família, espécie, taxonomista) |
| `ferramenta_herbcore/substituir_nao_exsicatas.py` | Substituições (exsicata, resolução, vistas, taxonomista, s.n., duplicata) |
| `ferramenta_herbcore/listar_resolucoes.py` | Medição de resolução e lista abaixo de 1024 px |
| `ferramenta_herbcore/enriquecer_manifesto.py` | Metadados do speciesLink e `chave_coleta` |
| `ferramenta_herbcore/atualizar_google_drive.py` | Espelhamento do rastreio no Drive |
