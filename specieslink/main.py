import requests
import mysql.connector
from mysql.connector import Error
import pandas as pd
import json

class species_link():
    def __init__(self, api_key): # __init__ é como um construtor
        self.apikey = api_key # self é uma referencia a propria instancia da classe;
                              # api_key é o parametro que se espera receber ao instanciar a classe;

    # metadados básicos
    def get_metadata(self):
        url = "https://specieslink.net/ws/1.0/info"
        response = requests.get(url, params={"apikey": self.apikey}) # params recebe o parametro da URL da requisição HTTP GET
                                                                     # onde a chave é apikey e o valor é self.apikey
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter os metadados")
            return None

    # todas as coleções e instituições participantes
    def get_participants(self):
        url = "https://specieslink.net/ws/1.0/participants"
        response = requests.get(url, params={"apikey": self.apikey}) # params recebe o parametro da URL da requisição HTTP GET
                                                                     # onde a chave é apikey e o valor é self.apikey
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter as coleções e instituições participantes")
            return None

    # dados de uma instituição por sigla ou identificador
    def get_institution_data(self, identifier, lang=None): # lang = none inicialmente indica que é opcional
        url = f"https://specieslink.net/ws/1.0/ins/{identifier}/" # f-string deixa adicionar expressões
        params = {"apikey": self.apikey} # params é um dicionário; recebe o parametro da URL da requisição HTTP GET
                                         # onde a chave é apikey e o valor é self.apikey
        if (lang):
            params["lang"] = lang # adicionando parametro lang ao dicionario params para filtragem
        response = requests.get(url, params=params) # HTTP GET para a URL requisitada passando os parametros
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter os dados da instituição")
            return None

    # dados de uma coleção por sigla ou identificador
    def get_collection_data(self, identifier, lang=None): # lang = none inicialmente indica que é opcional
        url = f"https://specieslink.net/ws/1.0/col/{identifier}/"  # f-string deixa adicionar expressões
        params = {"apikey": self.apikey} # params é um dicionário; recebe o parametro da URL da requisição HTTP GET
                                         # onde a chave é apikey e o valor é self.apikey
        if (lang):
            params["lang"] = lang # adicionando parametro lang ao dicionario params para filtragem 
        response = requests.get(url, params=params)  # HTTP GET para a URL requisitada passando os parametros
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter os dados da coleção")
            return None
    
    # dados de um conjunto de dados com um identificador especifico
    def get_dataset_info(self, id_dataset):
        url = f"https://specieslink.net/ws/1.0/dts/{id_dataset}/"
        # não tem parâmetro lang
        response = requests.get(url, params={"apikey": self.apikey}) # params recebe o parametro da URL da requisição HTTP GET
                                                                     # onde a chave é apikey e o valor é self.apikey
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter informações do conjunto de dados")
            return None

    # busca por registros de biodiversidade
    def search_records(self, filters):
        url = "https://specieslink.net/ws/1.0/search"
        offset = 0
        limit = 5000  # Inicializando com o valor máximo permitido de 5000
        # infelizmente não encontrei uma maneira de burlar esse limite ainda. segundo a propria API, esse é seu limite máximo por
        # consultas, então talvez não seja sequer possível
        params = {"apikey": self.apikey} # params é um dicionário; recebe o parametro da URL da requisição HTTP GET
                                         # onde a chave é apikey e o valor é self.apikey
        params.update(filters) #update para pegar os filtros utilizados
        
        numberMatched = 0 # numero total de requests que bateram com os requisitos
        numberReturned = 0 # numero total de requests que foram retornadas; máximo é o limit, que é 5000, como ditado pela API
        data = None # nenhum resultado armazenado ainda
        total_records = 0 # variável utilizada para a iteração da quantidade de numeros retornados

        while True: # loop infinito
            params.update({"offset": offset, "limit": limit}) # atualização dos parametros do dicionario
            response = requests.get(url, params=params) # HTTP GET para a URL requisitada passando os parametros
            
            if (response.status_code == 200):  # solicitação feita com sucesso se ACK HTTP = 200
                data = response.json()
                numberReturned = data.get('numberReturned', 0) # extrai o valor do campo numberReturned e passa para numberReturned
                                                               # se não existir, assume o valor 0
                numberMatched = data.get('numberMatched', 0)   # extrai o valor do campo numberMatched e passa para numberMatched
                                                               # se não existir, assume o valor 0
                total_records += numberReturned  # atualiza o total de registros recebidos
                
                if (total_records >= 5000): # se o número de retornos for maior ou igual ao limite, é a última página
                    break
            
                offset += limit  # atualiza o offset para a próxima página de resultados
            
            else:
                print("Erro ao obter os registros de biodiversidade")
                return None

        return data #, numberMatched, numberReturned < variáveis retornadas para teste, por isso, comentadas


    def insert_into_mysql(self, records, db_config): # edição atual: REALMENTE PERCEBEU OS 5000 mas nao insere...
        try: # conectando ao MySQL
            conn = mysql.connector.connect(**db_config) #  conexão com o banco MySQL usando
                                                        # as configurações no dicionário db_config

            if conn.is_connected():
                print("Conexão ao MySQL bem-sucedida!")

            cursor = conn.cursor() # permite executar comandos SQL no banco de dados (?)

            df = pd.DataFrame(records) # criação do dataframe pandas
                                       # converte a lista de records em um dataframe

            for index, row in df.iterrows(): # itera sob o dataframe pd
                if 'properties' in row and isinstance(row['properties'], dict): # verifica se a coluna 'properties'
                                                                                # existe na linha atual e se é um dicionário
                    properties = row['properties']

                    barcode = properties.get('barcode', '') # se sim, extrai cada campo do registro para variáveis individuais
                    collectioncode = properties.get('collectioncode', '')
                    catalognumber = properties.get('catalognumber', '')
                    scientificname = properties.get('scientificname', '')
                    kingdom = properties.get('kingdom', '')
                    family = properties.get('family', '')
                    genus = properties.get('genus', '')
                    yearcollected = properties.get('yearcollected', '')
                    monthcollected = properties.get('monthcollected', '')
                    daycollected = properties.get('daycollected', '')
                    country = properties.get('country', '')
                    stateprovince = properties.get('stateprovince', '')
                    county = properties.get('county', '')
                    locality = properties.get('locality', '')
                    institutioncode = properties.get('institutioncode', '')
                    basisofrecord = properties.get('basisofrecord', '')
                    verbatimlatitude = properties.get('verbatimlatitude', '')
                    verbatimlongitude = properties.get('verbatimlongitude', '')
                    collectionid = properties.get('collectionid', 0)
                    specificepithet = properties.get('specificepithet', '')
                    recordedby = properties.get('recordedby', '')
                    decimallongitude = properties.get('decimallongitude', '')
                    decimallatitude = properties.get('decimallatitude', '')
                    modified = properties.get('modified', '')
                    scientificnameauthorship = properties.get('scientificnameauthorship', '')
                    recordnumber = properties.get('recordnumber', '')
                    occurrenceremarks = properties.get('occurrenceremarks', '')

                    # inserção no MySQL
                    insert_query = """ 
                        INSERT INTO registros_biodiversidade 
                        (barcode, collectioncode, catalognumber, scientificname, kingdom, family, genus, 
                         yearcollected, monthcollected, daycollected, country, stateprovince, county, 
                         locality, institutioncode, basisofrecord, verbatimlatitude, verbatimlongitude, 
                         collectionid, specificepithet, recordedby, decimallongitude, decimallatitude, 
                         modified, scientificnameauthorship, recordnumber, occurrenceremarks) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    data = (
                        barcode, collectioncode, catalognumber, scientificname, kingdom, family, genus,
                        yearcollected, monthcollected, daycollected, country, stateprovince, county,
                        locality, institutioncode, basisofrecord, verbatimlatitude, verbatimlongitude,
                        collectionid, specificepithet, recordedby, decimallongitude, decimallatitude,
                        modified, scientificnameauthorship, recordnumber, occurrenceremarks
                    ) # dados extraídos são adicionados em uma tupla chamada data

                    cursor.execute(insert_query, data) # usa o objeto cursor pra executar a insert_query
                    # com os dados da tupla, inserindo um registro na tabela registros_biodiversidade no banco

            conn.commit() # salva as mudanças feitas
            print(f"inserção de registros concluída - total de registros: {len(df)}")

        except mysql.connector.Error as err: # exceção de erros
            print(f"erro ao conectar: {err}")

        finally: # fecha a conexão, independentemente se deu erro ou não
            if conn and conn.is_connected():
                conn.close()
                print("conexão encerrada")

