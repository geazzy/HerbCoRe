import requests
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd
from pandas import json_normalize

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
        limit = 5000  # inicializando com o valor máximo permitido de 5000
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
                if(offset == 0): # somente se for a primeira pagina
                    numberMatched = data.get('numberMatched', 0) # extrai o valor do campo numberMatched e passa para numberMatched
                                                                 # se não existir, assume o valor 0
                total_records += numberReturned  # atualiza o total de registros recebidos
                
                # print(numberMatched) # esses dois prints sao so pra ver se realmente ta rodando e que nao travou
                # print(numberReturned)
                if(total_records >= numberMatched): # se todos os registros identificados forem recebidos por total_records
                    break
            
                offset += limit  # atualiza o offset para a próxima página de resultados
            
            else:
                print("erro ao obter os registros de biodiversidade")
                return None

        return data #, numberMatched, numberReturned < variáveis retornadas para teste, por isso, comentadas
    
    def insert_into_mysql(self, records, db_config):
        try:
            conn = mysql.connector.connect(**db_config) # conexão com o banco MySQL usando
                                                        # as configurações no dicionário db_config

            if conn.is_connected(): # se a conexão está ativa
                print("conexão bem-sucedida")
            
            cursor = conn.cursor() # cria um cursor permite executar comandos SQL no banco de dados

            df = json_normalize(records, 'features', errors='ignore') # criação do dataframe pandas
                                                    # converte a lista de JSONs em um dataframe:
                                                    # records é o que está sendo convertido, features é o argumento
                                                    # utilizado para especificar os dados de interesse para normalização
                                                    # erros='ignore' instrui o Pandas a ignorar erros e continuar a operação
                                                    # mesmo com dificuldades de normalizar os dados
            # pré normalização dos dados, embora parecesse com um dicionário, records era somente uma representação textual de dados.
            # após a normalização, ele se torna um dicionário.

            for index, row in df.iterrows():  # index armazena o índice (contagem) da linha atual do df durante a iteração
                                              # df.iterrows itera sobre as linhas do df em pares (índice, série)
                                              # primeiro elemento é o índice da linha e o segundo é a própria linha
                                              # como uma série (estrutura de dados de qualquer tipo) do Pandas

                # acessando diretamente cada coluna do dataframe:
                properties = row.to_dict() # properties irá conter o dicionário, mantendo as chaves em linhas individuais

                barcode = properties.get('properties.barcode', '') # extrai cada valor do registro para variáveis individuais
                                                                   # se não tiver, o valor retornado será nulo
                collectioncode = properties.get('properties.collectioncode', '')
                catalognumber = properties.get('properties.catalognumber', '')
                scientificname = properties.get('properties.scientificname', '')
                kingdom = properties.get('properties.kingdom', '')
                family = properties.get('properties.family', '')
                genus = properties.get('properties.genus', '')
                yearcollected = properties.get('properties.yearcollected', '')
                monthcollected = properties.get('properties.monthcollected', '')
                daycollected = properties.get('properties.daycollected', '')
                country = properties.get('properties.country', '')
                stateprovince = properties.get('properties.stateprovince', '')
                county = properties.get('properties.county', '')
                locality = properties.get('properties.locality', '')
                institutioncode = properties.get('properties.institutioncode', '')
                phylum = properties.get('properties.phylum', '')
                basisofrecord = properties.get('properties.basisofrecord', '')
                verbatimlatitude = properties.get('properties.verbatimlatitude', '')
                verbatimlongitude = properties.get('properties.verbatimlongitude', '')
                identifiedby = properties.get('properties.identifiedby', '')
                collectionid = properties.get('properties.collectionid', 0)
                specificepithet = properties.get('properties.specificepithet', '')
                recordedby = properties.get('properties.recordedby', '')
                decimallongitude = properties.get('properties.decimallongitude', '')
                decimallatitude = properties.get('properties.decimallatitude', '')
                modified = properties.get('properties.modified', '')
                scientificnameauthorship = properties.get('properties.scientificnameauthorship', '')
                recordnumber = properties.get('properties.recordnumber', '')
                occurrenceremarks = properties.get('properties.occurrenceremarks', '')

                # inserção no MySQL
                insert_query = """
                    INSERT INTO projeto_herbario.registros_biodiversidade 
                    (barcode, collectioncode, catalognumber, scientificname, kingdom, family, genus, 
                     yearcollected, monthcollected, daycollected, country, stateprovince, county, 
                     locality, institutioncode, phylum, basisofrecord, verbatimlatitude, verbatimlongitude, identifiedby,
                     collectionid, specificepithet, recordedby, decimallongitude, decimallatitude, 
                     modified, scientificnameauthorship, recordnumber, occurrenceremarks) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                data = (
                    barcode, collectioncode, catalognumber, scientificname, kingdom, family, genus,
                    yearcollected, monthcollected, daycollected, country, stateprovince, county,
                    locality, institutioncode, phylum, basisofrecord, verbatimlatitude, verbatimlongitude, identifiedby,
                    collectionid, specificepithet, recordedby, decimallongitude, decimallatitude,
                    modified, scientificnameauthorship, recordnumber, occurrenceremarks
                ) # dados extraídos são adicionados em uma tupla chamada data

                cursor.execute(insert_query, data) # adiciona no MySQL

            conn.commit() # salva as mudanças feitas
            print(f"inserção de registros concluída - total de registros: {len(df)}")

        except mysql.connector.Error as erro:
            print(f"erro ao conectar: {erro}")

        finally: # fecha a conexão, independentemente se deu erro ou não
            if conn and conn.is_connected(): # se a conexão existe e está ativa
                conn.close() # fecha a conexão
                print("conexão encerrada")
