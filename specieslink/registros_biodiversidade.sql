USE projeto_herbario;

DROP TABLE IF EXISTS registros_biodiversidade;


CREATE TABLE registros_biodiversidade (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(255),
    collectioncode VARCHAR(255),
    catalognumber VARCHAR(255),
    scientificname VARCHAR(255),
    kingdom VARCHAR(255),
    family VARCHAR(255),
    genus VARCHAR(255),
    yearcollected VARCHAR(255),
    monthcollected VARCHAR(255),
    daycollected VARCHAR(255),
    country VARCHAR(255),
    stateprovince VARCHAR(255),
    county VARCHAR(255),
    locality VARCHAR(255),
    # coordinateprecision VARCHAR(255),
    institutioncode VARCHAR(255),
    phylum VARCHAR(255),
    basisofrecord VARCHAR(255),
    verbatimlatitude VARCHAR(255),
    verbatimlongitude VARCHAR(255),
    identifiedby VARCHAR(255),
    collectionid INT,
    specificepithet VARCHAR(255),
    recordedby VARCHAR(255),
    decimallongitude VARCHAR(255),
    decimallatitude VARCHAR(255),
    modified VARCHAR(255),
    scientificnameauthorship VARCHAR(255),
    recordnumber VARCHAR(255),
	occurrenceremarks VARCHAR(255)
);

# se os IDs começarem fora do 1:
ALTER TABLE registros_biodiversidade AUTO_INCREMENT = 1;

# se receber um erro sobre o tamanho de um campo não ser o suficiente:
ALTER TABLE projeto_herbario.registros_biodiversidade
MODIFY occurrenceremarks VARCHAR(4000);
ALTER TABLE projeto_herbario.registros_biodiversidade
MODIFY locality VARCHAR(4000);

# variáveis que usei para teste
SELECT COUNT(*) FROM registros_biodiversidade;
SELECT barcode_att FROM registros_biodiversidade WHERE barcode_att IS NOT NULL;
SELECT * FROM registros_biodiversidade;
DELETE FROM registros_biodiversidade WHERE id != '';
SELECT * FROM registros_biodiversidade
WHERE barcode = 'P04P1N0023';
SELECT COUNT(*) FROM registros_biodiversidade where barcode_att IS NOT NULL;
SET SQL_SAFE_UPDATES = 0; # caso ele diga que está no safe mode

SELECT COUNT(*) FROM registros_biodiversidade
WHERE country NOT IN('Brasil', 'Brazil');

SELECT COUNT(*) FROM registros_biodiversidade
WHERE country_att IS NOT NULL;

SELECT COUNT(*) FROM registros_biodiversidade
WHERE stateProvince_att IS NOT NULL;

#preparando para o crawler
SELECT barcode FROM registros_biodiversidade; # utilizaremos somente os barcodes

#FILTRAGEM:
# Não deletaremos os registros que não desejamos. Ao invés disso,
# criaremos colunas extras dentro da tabela, para filtrarmos somente o desejado.
# A partir disso, consultas serão feitas com barcode_att ao invés de barcode;
# nota: acabei esquecendo de incluir os valores originais já corretos dentro dos novos
# campos. Por isso, em alguns comentários você verá: numero1+numero2. O segundo número
# é após a adição dos valores originais, por exemplo, quando fiz country_att = country onde country = Brasil.

#country
SELECT country_att FROM registros_biodiversidade;

SELECT country FROM registros_biodiversidade
GROUP BY country; # opções: VE, Brazil, AR, Brasil, Nicaragua, Colombia, NULL,
				  # Panamá, Venezuela, Ecuador, Bolivia, Suriname

ALTER TABLE registros_biodiversidade
ADD COLUMN country_att VARCHAR(255); # tabela extra para não deletar os registros

UPDATE registros_biodiversidade
SET country_att = 'Brasil'
WHERE country = 'Brazil'; # mudou 23068 registros

UPDATE registros_biodiversidade
SET country_att = 'Brasil'
WHERE country = 'Brasil'; # mudou 52842 registros

#stateProvince
SELECT stateProvince FROM registros_biodiversidade
GROUP BY stateProvince;

ALTER TABLE registros_biodiversidade
ADD COLUMN stateProvince_att VARCHAR(255); # tabela extra para não deletar os registros

SELECT stateProvince_att from registros_biodiversidade;

#RIO DE JANEIRO
UPDATE registros_biodiversidade
SET stateProvince_att = 'Rio de Janeiro'
WHERE stateProvince IN('RJ', 'Rio de Janriro', 'Rio de Janeiro'); # 158+5101 colunas mudadas

#MINAS GERAIS
UPDATE registros_biodiversidade
SET stateProvince_att = 'Minas Gerais'
WHERE stateProvince IN('Minas gerais', 'MG', 'Minas Gerais.', 'MINAS GERAIS, MG', 'Minas Gerais'); # 7656 colunas mudadas

#BAHIA
UPDATE registros_biodiversidade
SET stateProvince_att = 'Bahia'
WHERE stateProvince IN('BAHIA, BA', 'BA', 'Bahia'); # 121+6234 colunas mudadas

#CEARA
UPDATE registros_biodiversidade
SET stateProvince_att = 'Ceará'
WHERE stateProvince IN('CE', 'Ceara', 'Ceará'); # 411 colunas mudadas

#SANTA CATARINA
UPDATE registros_biodiversidade
SET stateProvince_att = 'Santa Catarina'
WHERE stateProvince IN('SC', 'Santa Catarina'); # 321+5286 colunas mudadas

#AMAZONAS
UPDATE registros_biodiversidade
SET stateProvince_att = 'Amazonas'
WHERE stateProvince IN('AM', 'Amazonas'); # 21+7893 colunas mudadas

#GOIAS
UPDATE registros_biodiversidade
SET stateProvince_att = 'Goiás'
WHERE stateProvince IN('Goias', 'GO', 'Goiás'); # 1955 colunas mudadas

#SÃO PAULO
UPDATE registros_biodiversidade
SET stateProvince_att = 'São Paulo'
WHERE stateProvince IN('Sao Paulo', 'SP', 'São Paulo'); # 9448 colunas mudadas

#ACRE
UPDATE registros_biodiversidade
SET stateProvince_att = 'Acre'
WHERE stateProvince IN('AC', 'Acre'); # 57+2053 colunas mudadas

#RORAIMA
UPDATE registros_biodiversidade
SET stateProvince_att = 'Roraima'
WHERE stateProvince IN('RO', 'Roraima (?)'); # 128+124 colunas mudadas

#PARANÁ
UPDATE registros_biodiversidade
SET stateProvince_att = 'Paraná'
WHERE stateProvince IN('Parana', 'PR', 'Paraná'); # 9150 colunas mudadas

#RIO GRANDE DO SUL
UPDATE registros_biodiversidade
SET stateProvince_att = 'Rio Grande do Sul'
WHERE stateProvince IN('RS', 'Rio Grande do Sul'); # 1031+2104 colunas mudadas

#MATO GROSSO
UPDATE registros_biodiversidade
SET stateProvince_att = 'Mato Grosso'
WHERE stateProvince IN('MT', 'Mato Grosso'); # 40+1887 colunas mudadas

#ESPÍRITO SANTO
UPDATE registros_biodiversidade
SET stateProvince_att = 'Espírito Santo'
WHERE stateProvince IN('ESPÍRITO SANTO, ES', 'ES', 'Espirito Santo', 'Espírito Santo'); # 3713 colunas mudadas

#PERNAMBUCO
UPDATE registros_biodiversidade
SET stateProvince_att = 'Pernambuco'
WHERE stateProvince IN('PE', 'Pernambuco'); # 23+976 colunas mudadas

#PIAUÍ
UPDATE registros_biodiversidade
SET stateProvince_att = 'Piauí'
WHERE stateProvince IN('Piaui', 'PI', 'Piauí'); # 48 colunas mudadas

#DISTRITO FEDERAL
UPDATE registros_biodiversidade
SET stateProvince_att = 'Distrito Federal'
WHERE stateProvince IN('Distrito Federal', 'Distrito federal', 'Brasília', 'Brasilia', 'Districto Federal - DF'); # 963 colunas mudadas

#MATO GROSSO DO SUL
UPDATE registros_biodiversidade
SET stateProvince_att = 'Mato Grosso do Sul'
WHERE stateProvince IN('MS', 'Mato Grosso do Sul'); # 107+1251 colunas mudadas

#TOCANTINS
UPDATE registros_biodiversidade
SET stateProvince_att = 'Tocantins'
WHERE stateProvince IN('TO', 'Tocantins'); # 163+124 colunas mudadas

#ALAGOAS
UPDATE registros_biodiversidade
SET stateProvince_att = 'Alagoas'
WHERE stateProvince IN('AL', 'Alagoas'); # 12+482 colunas mudadas

#PARAÍBA
UPDATE registros_biodiversidade
SET stateProvince_att = 'Paraíba'
WHERE stateProvince IN('Paraiba', 'PB', 'Paraíba'); # 270 colunas mudadas

#SERGIPE
UPDATE registros_biodiversidade
SET stateProvince_att = 'Sergipe'
WHERE stateProvince IN('SE', 'Sergipe'); # 141 colunas mudadas

#RIO GRANDE DO NORTE
UPDATE registros_biodiversidade
SET stateProvince_att = 'Rio Grande do Norte'
WHERE stateProvince IN('Rio Grade do Norte', 'RN', 'Rio Grande do Norte'); # 1+24 colunas mudadas

#RONDÔNIA
UPDATE registros_biodiversidade
SET stateProvince_att = 'Rondônia'
WHERE stateProvince IN('Rondônia', 'Rondonia', 'Rondonia (Terr.)', 'Rondônia (Terr.)', 'RO'); # 1448+124 colunas mudadas

#AMAPÁ
UPDATE registros_biodiversidade
SET stateProvince_att = 'Amapá'
WHERE stateProvince IN('Amapa', 'Amapá (Terr.)', 'Amapa (Terr.)', 'AP'); # 678 colunas mudadas

#MARANHÃO
UPDATE registros_biodiversidade
SET stateProvince_att = 'Maranhão'
WHERE stateProvince IN('Maranhão', 'Maranhao', 'MA'); # 189 colunas mudadas

#PARÁ
UPDATE registros_biodiversidade
SET stateProvince_att = 'Pará'
WHERE stateProvince IN('Pará', 'Para', 'PA'); # 3219 colunas mudadas

#barcode
ALTER TABLE registros_biodiversidade
ADD COLUMN barcode_att VARCHAR(255); # tabela extra pra não deletar os registros

SELECT * FROM registros_biodiversidade WHERE barcode_att IS NOT NULL;
SELECT COUNT(*) from registros_biodiversidade WHERE barcode_att IS NOT NULL;

UPDATE registros_biodiversidade
SET barcode_att = barcode
WHERE barcode IS NOT NULL AND stateProvince_att IS NOT NULL AND country_att IS NOT NULL;
# 47348 registros mudados
