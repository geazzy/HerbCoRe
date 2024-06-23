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

# se receber um erro sobre o tamanho de ocurrencemarks não ser o suficiente:
ALTER TABLE projeto_herbario.registros_biodiversidade
MODIFY occurrenceremarks VARCHAR(500);

# variáveis que usei para teste
SELECT COUNT(*) FROM registros_biodiversidade;
SELECT * FROM registros_biodiversidade WHERE id = '1';
DELETE FROM registros_biodiversidade WHERE id != '';
SET SQL_SAFE_UPDATES = 0;

