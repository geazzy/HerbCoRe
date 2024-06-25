# Projeto-Herbario
Catalogação do meu código sobre um projeto de machine learning focado especialmente em plantas do herbário da UTFPR, com auxílio do professor André Luis Schwerz.

## Sobre a pasta specieslink:
Código feito para consulta de metadados, tais como tipos, listas ou dados de coleção e/ou instituição, além de informações sobre um conjunto de dados, através de uma API do specieslink. Na pasta, encontra-se a ferramenta das consultas, o script SQL, e um arquivo onde realizei alguns testes.

Há possibilidade de filtrar os registros de biodiversidade para receber dados mais específicos - o retorno não possui limitação de tamanho.

Capaz de passar os dados para o MySQL, colocando os registros dentro de uma tabela para pesquisas mais profundas.

## Pré-requisitos:
- Ter a linguagem Python instalada, e um ambiente python;
- Obter as bibliotecas utilizadas:
  ```python
  pip install pandas
  pip install mysql-connector-python
  ```
- Instalar e configurar o MySQL, utilizando da tabela registros_biodiversidade;
