import requests
import json
# import mysql.connector
# from mysql.connector import Error
import pandas as pd
from pandas import json_normalize
import pymysql
import csv

class species_link():
    def __init__(self, api_key): # __init__ é como um construtor
        self.apikey = api_key # self é uma referencia a propria instancia da classe;
                              # api_key é o parametro que se espera receber ao instanciar a classe;

    # metadados básicos
    def get_metadata(self, name=None, id=None):
        url = "https://specieslink.net/ws/1.0/info"
        params = {"apikey": self.apikey}
        response = requests.get(url, params=params) # params recebe o parametro da URL da requisição HTTP GET
                                                                     # onde a chave é apikey e o valor é self.apikey
        if name:
            params['name'] = name
        if id:
            params['id'] = id
        

        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter os metadados")
            return None

    # todas as coleções e instituições participantes
    def get_participants(self):
        url = "https://specieslink.net/ws/1.0/participants"
        params = {"apikey": self.apikey}
        response = requests.get(url, params=params) # params recebe o parametro da URL da requisição HTTP GET
                                                                     # onde a chave é apikey e o valor é self.apikey
            
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter as coleções e instituições participantes")
            return None

    # dados de uma instituição por sigla ou identificador
    def get_institution_data(self, acronym=None, lang=None, id=None): # lang = none inicialmente indica que é opcional
        if acronym:
            url = f"https://specieslink.net/ws/1.0/ins/{acronym}/" # f-string deixa adicionar expressões
        elif id:
            url = f"https://specieslink.net/ws/1.0/ins/{id}/"
        else:
            print("é necessário fornecer um 'acronym' ou um 'id'.")
            return None
        
        params = {"apikey": self.apikey} # params é um dicionário; recebe o parametro da URL da requisição HTTP GET
                                         # onde a chave é apikey e o valor é self.apikey
        if (lang):
            params["lang"] = lang # adicionando parametro lang ao dicionario params para filtragem
        # valores de acronym ou id não são passados pois já estão embutidos na URL, não são parte da query string

        response = requests.get(url, params=params) # HTTP GET para a URL requisitada passando os parametros
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter os dados da instituição")
            return None

    # dados de uma coleção por sigla ou identificador
    def get_collection_data(self, acronym=None, lang=None, id=None): # lang = none inicialmente indica que é opcional
        if acronym:
            url = f"https://specieslink.net/ws/1.0/col/{acronym}/" # f-string deixa adicionar expressões
        elif id:
            url = f"https://specieslink.net/ws/1.0/col/{id}/"
        else:
            print("é necessário fornecer um 'acronym' ou um 'id'.")
            return None
        
        params = {"apikey": self.apikey} # params é um dicionário; recebe o parametro da URL da requisição HTTP GET
                                         # onde a chave é apikey e o valor é self.apikey
        if (lang):
            params["lang"] = lang # adicionando parametro lang ao dicionario params para filtragem 
            # valores de acronym ou id não são passados pois já estão embutidos na URL, não são parte da query string

        response = requests.get(url, params=params)  # HTTP GET para a URL requisitada passando os parametros
        if (response.status_code == 200): # solicitação feita com sucesso se ACK HTTP = 200
            data = response.json()
            return data
        else:
            print("erro ao obter os dados da coleção")
            return None
    
    # dados de um conjunto de dados com um identificador especifico
    def get_dataset_info(self, id=None):
        if id:
            url = f"https://specieslink.net/ws/1.0/dts/{id}/"
        else:
            print("é necessário fornecer um 'id'.")
            return None

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
        limit = 5000 # inicializando com o valor máximo permitido de 5000
        params = {"apikey": self.apikey} # params é um dicionário; recebe o parametro da URL da requisição HTTP GET
                                         # onde a chave é apikey e o valor é self.apikey

        params.update(filters) # update para pegar os filtros utilizados
        
        numberMatched = 0 # numero total de requests que bateram com os requisitos
        numberReturned = 0 # numero total de requests que foram retornadas; máximo é o limit, que é 5000, como ditado pela API
        data = None # nenhum resultado armazenado ainda
        
        while True: # loop infinito
            params.update({"offset": offset, "limit": limit}) # atualização dos parametros do dicionario
            response = requests.get(url, params=params)  # HTTP GET para a URL requisitada passando os parametros
            
            if response.status_code == 200: # solicitação feita com sucesso se ACK HTTP = 200
                response_data = response.json()
                numberReturned = response_data.get('numberReturned', 0) # extrai o valor do campo numberReturned e passa para numberReturned
                                                                        # se não existir, assume o valor 0
                
                if offset == 0: # se for a primeira pagina
                    numberMatched = response_data.get('numberMatched', 0) # extrai o valor do campo numberMatched e passa para numberMatched
                                                                          # se não existir, assume o valor 0
                    data = {'features': []}  # inicializa data como um dicionário vazio, chave features
                
                
                if 'features' in response_data: # se os records dentro do JSON em response_data tiverem o campo features
                    data['features'].extend(response_data['features']) # acumula os registros diretamente em data['features']
                
                print(f"dados passados até o momento: {len(data['features'])}") # print de teste
                print(f"numeros que batem: {numberMatched}") # esses dois prints sao so pra ver se realmente ta rodando e que nao travou
                print(f"numeros retornados: {numberReturned}")
                
                if len(data['features']) >= numberMatched: # se a quantidade de dados com feature adicionados for maior ou igual
                                                           # ao número total de requests que bateram com os requisitos
                                                           # todos os dados foram adicionados
                    break
                
                offset += limit # atualiza o offset para a próxima página de resultados
            
            else:
                print("erro ao obter os registros de biodiversidade")
                return None
    
        return data
    
    def insert_into_mysql(self, records, db_config, table):
        conn = None
        try:
            conn = pymysql.connect(**db_config) # conexão com o banco MySQL usando
                                                # as configurações no dicionário db_config

            if conn.open: # se a conexão está ativa
                print("conexão bem-sucedida")
            else:
                print("falha na conexão com o banco")
                return
            
            cursor = conn.cursor() # cria um cursor permite executar comandos SQL no banco de dados

            df = json_normalize(records, 'features', errors='ignore') # criação do dataframe pandas
                                                    # converte a lista de JSONs em um dataframe:
                                                    # records é o que está sendo convertido, features é o argumento
                                                    # utilizado para especificar os dados de interesse para normalização
                                                    # erros='ignore' instrui o Pandas a ignorar erros e continuar a operação
                                                    # mesmo com dificuldades de normalizar os dados
            # pré normalização dos dados, embora parecesse com um dicionário, records era somente uma representação textual de dados.
            # após a normalização, ele se torna um dicionário.

            df = json_normalize(records, 'features', errors='ignore') # transforma json em pandas
            df = df.where(pd.notna(df), None)  # substitui NaN por None

            for index, row in df.iterrows():  # index armazena o índice (contagem) da linha atual do df durante a iteração
                                              # df.iterrows itera sobre as linhas do df em pares (índice, série)
                                              # primeiro elemento é o índice da linha e o segundo é a própria linha
                                              # como uma série (estrutura de dados de qualquer tipo) do Pandas
                print(f"inserindo registro {index+1}...")
                # acessando diretamente cada coluna do dataframe:
                #properties = row.to_dict() # properties irá conter o dicionário, mantendo as chaves em linhas individuais
                properties = row.replace({pd.NA: None}).to_dict()

                barcode = properties.get('properties.barcode', None) # extrai cada valor do registro para variáveis individuais
                                                                   # se não tiver, o valor retornado será nulo
                collectioncode = properties.get('properties.collectioncode', None)
                catalognumber = properties.get('properties.catalognumber', None)
                scientificname = properties.get('properties.scientificname', None)
                kingdom = properties.get('properties.kingdom', None)
                family = properties.get('properties.family', None)
                genus = properties.get('properties.genus', None)
                yearcollected = properties.get('properties.yearcollected', None)
                monthcollected = properties.get('properties.monthcollected', None)
                daycollected = properties.get('properties.daycollected', None)
                country = properties.get('properties.country', None)
                stateprovince = properties.get('properties.stateprovince', None)
                county = properties.get('properties.county', None)
                locality = properties.get('properties.locality', None)
                institutioncode = properties.get('properties.institutioncode', None)
                phylum = properties.get('properties.phylum', None)
                basisofrecord = properties.get('properties.basisofrecord', None)
                verbatimlatitude = properties.get('properties.verbatimlatitude', None)
                verbatimlongitude = properties.get('properties.verbatimlongitude', None)
                identifiedby = properties.get('properties.identifiedby', None)
                collectionid = properties.get('properties.collectionid', 0)
                specificepithet = properties.get('properties.specificepithet', None)
                recordedby = properties.get('properties.recordedby', None)
                decimallongitude = properties.get('properties.decimallongitude', None)
                decimallatitude = properties.get('properties.decimallatitude', None)
                modified = properties.get('properties.modified', None)
                scientificnameauthorship = properties.get('properties.scientificnameauthorship', None)
                recordnumber = properties.get('properties.recordnumber', None)
                occurrenceremarks = properties.get('properties.occurrenceremarks', None)

                # inserção no MySQL
                insert_query = f"""
                    INSERT INTO {db_config['database']}.{table}
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
                print(f"registro {index+1} inserido com sucesso")

            conn.commit() # salva as mudanças feitas
            print(f"inserção de registros concluída - total de registros: {len(df)}")

        except pymysql.MySQLError as erro:
            print(f"erro ao conectar: {erro}")
        except Exception as e:
                print(f"erro inesperado: {e}")

        finally: # fecha a conexão, independentemente se deu erro ou não
            if conn and conn.open: # se a conexão existe e está ativa
                conn.close() # fecha a conexão
                print("conexão encerrada")

    def export_to_csv(self, filters, db_config, table, columns=None, output_csv_path=None):
        conn = None
        try:
            conn = pymysql.connect(**db_config) # conexão com o banco MySQL usando
                                                # as configurações no dicionário db_config
            if conn.open: # se a conexão está ativa
                print("conexão bem-sucedida")
            else:
                print("falha na conexão com o banco")
                return

            cursor = conn.cursor()

            where_clauses = [] # constrói o WHERE com base nos filtros passados
            values = []

            for column, value in filters.items(): # para cada valor em cada coluna dos argumentos passados para filtragem
                where_clauses.append(f"{column} = %s") # copia a coluna para servir de pré-condição da filtragem
                values.append(value) # salva os valores requisitados pelo filtro, completando o argumento

            if where_clauses:  # se tem parâmetros WHERE
                where_clause = " AND ".join(where_clauses) # AND será o separador de todos os argumentos, ou seja, X AND Y AND Z
            else:
                where_clause = "1=1" # 1=1 é usado para retornar tudo caso nao tenha parâmetros

            # se columns for fornecido, usamos ele, caso contrário, pegamos todas as colunas
            if columns:
                query_columns = columns  # usamos as colunas especificadas
            else:
                query_columns = "*"  # se não for especificado, pegamos todas as colunas

            query = f"""
                SELECT 
                    {query_columns}
                FROM {db_config['database']}.{table}
                WHERE {where_clause}
            """

            print(f"query gerada: {query}")

            # executa a query com os filtros
            cursor.execute(query, values)
            results = cursor.fetchall() # recupera os resultados

            print(f"número de registros encontrados: {len(results)}")

            if results:  # se tiver resultados
                with open(output_csv_path, mode='w', newline=None, encoding='utf-8') as csv_file:
                    writer = csv.writer(csv_file)

                    if columns:  # se tiver colunas especificadas
                        writer.writerow([columns])
                    else:
                        # se não tiver especificado, usa todas as colunas do banco
                        column_names = [desc[0] for desc in cursor.description]
                        writer.writerow(column_names)

                    # escreve os dados
                    for row in results:
                        writer.writerow(row)

                print(f"exportação concluída. arquivo salvo em: {output_csv_path}")
            else:
                print("nenhum registro encontrado com os filtros aplicados.")

        except pymysql.MySQLError as erro:
            print(f"erro ao conectar: {erro}")
        except Exception as e:
                print(f"erro inesperado: {e}")
        finally:
            if conn and conn.open:
                conn.close()
                print("conexão encerrada")

    def update_records(self, filters, update_values, db_config, table):
        conn = None
        try:
            conn = pymysql.connect(**db_config) # conexão com o banco MySQL usando
                                                # as configurações no dicionário db_config
            if conn.open: # se a conexão está ativa
                print("conexão bem-sucedida")
            else:
                print("falha na conexão com o banco")
                return

            cursor = conn.cursor()
            cursor.execute("SET SQL_SAFE_UPDATES = 0;") # desativa a segurança de updates

            where_clauses = []  # constrói o WHERE com base nos filtros passados
            set_clauses = []  # # constrói o SET com base nos filtros passados
            values = []  

            for column, value in filters.items(): # para cada valor em cada coluna dos argumentos passados para filtragem
                where_clauses.append(f"{column} = %s") # copia a coluna para servir de pré-condição da filtragem
                values.append(value) # salva os valores requisitados pelo filtro, completando o argumento


            for column, value in update_values.items(): # para cada valor em cada coluna dos valores para update
                set_clauses.append(f"{column} = %s") # copia a coluna
                values.insert(0, value) # insere o valor na primeira posição de value, substituindo o anterior
                                        # (ou seja, SET x = valor_novo WHERE x = valor_antigo)

            if where_clauses: # se tem parâmetros WHERE
                where_clause = " AND ".join(where_clauses) # AND será o separador de todos os argumentos, ou seja, X AND Y AND Z
            else:
                raise ValueError("nenhum filtro fornecido para o update")

            if set_clauses: # se tem parâmetros SET
                set_clause = ", ".join(set_clauses) # ',' será o separador de todos os argumentos, ou seja, SET X = x, Y = y
            else:
                raise ValueError("nenhum valor para atualização fornecido.")

            # atualizando o SQL
            query = f"""
                UPDATE {db_config['database']}.{table}
                SET {set_clause}
                WHERE {where_clause}
            """
            print("query gerada para UPDATE:", query)
            print("valores para UPDATE:", values)

            # executa a query com os filtros
            cursor.execute(query, values)
            conn.commit() # salva

            print(f"{cursor.rowcount} registro(s) atualizado(s).")

        except pymysql.MySQLError as erro:
            print(f"erro ao conectar: {erro}")
        except Exception as e:
                print(f"erro inesperado: {e}")
        finally:
            if conn and conn.open:
                conn.close()
                print("conexão encerrada")
