# Projeto-Herbario
Catalogação do meu código sobre a HerbCoRe: uma ferramenta para seleção e filtragem de acervos de dados relacionados à plantas de herbários, com auxílio do professor André Luis Schwerz.

## Sobre a pasta specieslink:
Código feito para consulta de metadados, tais como tipos, listas ou dados de coleção e/ou instituição, além de informações sobre um conjunto de dados, através de uma API do specieslink. Na pasta, encontra-se a ferramenta das consultas e a table e script SQL.

Há possibilidade de filtrar os registros de biodiversidade para receber dados mais específicos - o retorno não possui limitação de tamanho.

Capaz de passar os dados para o MySQL, colocando os registros dentro de uma tabela para pesquisas mais profundas.

Utilize do crawler encontrado [aqui](https://github.com/xaaaandao/downloader-specieslink/tree/master) para conseguir as URLs e as imagens.
Leia mais sobre o catálogo de Leipzig e o lcvplants [aqui](https://github.com/idiv-biodiversity/lcvplants).

Obtenha uma chave para a API se cadastrando no species_link [aqui](https://specieslink.net/ws/1.0/)

## Pré-requisitos:
- Utilizar de ```requirements.txt``` para instalar os requisitos utilizando o seguinte comando:
```
pip install -r requirements.txt
```

## Como usar a ferramenta:
A ferramenta te pede um conjunto de comandos pelo terminal para executar o que se pede. Caso desconheça os parâmetros necessários para a busca, você pode usar de ```-h``` e ver os comentários com ajuda adicionados.
```python ferramenta.py -h``` lhe mostrará o seguinte:
```

interface dos métodos da ferramenta

positional arguments:
  {metadata,participants,instituition,collection,dataset,records}
                        método a ser executado
    metadata            metadados de espécies
    participants        instituições participantes
    instituition        instiuições específicas
    collection          coleções específicas
    dataset             conjunto de dados específicos
    records             registros filtrados
    export              realiza uma consulta SQL e retorna um CSV
    update              atualiza registros do banco baseado em parâmetros
```

Procurar por algo mais específico, como os parâmetros dos métodos demonstrados acima, requer que você especifique o método quando der o comando de ajuda.
Por exemplo, ```python ferramenta.py metadata -h``` lhe mostrará o seguinte:
```
usage: ferramenta.py metadata [-h] --api_key API_KEY [--name NAME] [--id ID]

options:
  -h, --help         show this help message and exit
  --name NAME        nome a ser identificado
  --id ID            id a ser identificado
```

### Exemplos de uso dos comandos, na ordem dos métodos:
```python
python ferramenta.py metadata --name "Secretaria Estadual" --id "400"
python ferramenta.py participants
python ferramenta.py instituition --acronym "USP" --id "393" --lang "en"  
python ferramenta.py collection --acronym "ESA" --id "8" --lang "pt-br"
python ferramenta.py dataset --id "8"
python ferramenta.py records --filters family=piperaceae barcode="FURB38192" --table tabela_exemplo
python ferramenta.py export --filters family=piperaceae --table tabela_exemplo --colums "coluna_exemplo" --output_csv_path resultados.csv
python ferramenta.py update --filters stateprovince="São Paulo" --update_values="Santa Catarina" --table tabela_exemplo
```
