from main_f import species_link
import json
# import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser(description='interface dos métodos da ferramenta')
    subparsers = parser.add_subparsers(dest="command", help="método a ser executado") # subparsers permitem que métodos utilizem de argumentos diferentes e serem chamados ou não

    metadados = subparsers.add_parser("metadata", help="metadados de espécies") # cria um objeto argumentparser e descreve seu script quando alguém usa -h ou --help
    metadados.add_argument("--api_key", type=str, required=True, help="chave da API") # argumento --api_key, obrigatório, que pede a chave do usuario
    metadados.add_argument('--name', type=str, help='nome a ser identificado') # argumento --name, opcional, para a filtragem de um nome
    metadados.add_argument('--id', type=str, help='id a ser identificado')

    participantes = subparsers.add_parser("participants", help="instituições participantes")
    participantes.add_argument("--api_key", type=str, required=True, help="chave da API")

    instituition = subparsers.add_parser("instituition", help="instiuições específicas")
    instituition.add_argument("--api_key", type=str, required=True, help="chave da API")
    instituition.add_argument('--acronym', type=str, help='sigla a ser identificada')
    instituition.add_argument('--id', type=str, help='id a ser identificado')
    instituition.add_argument('--lang', type=str, help='linguagem escolhida')

    collection = subparsers.add_parser("collection", help="coleções específicas")
    collection.add_argument("--api_key", type=str, required=True, help="chave da API")
    collection.add_argument('--acronym', type=str, help='sigla a ser identificada')
    collection.add_argument('--id', type=str, help='id a ser identificado')
    collection.add_argument('--lang', type=str, help='linguagem escolhida')

    dataset = subparsers.add_parser("dataset", help="conjunto de dados específicos")
    dataset.add_argument("--api_key", type=str, required=True, help="chave da API")
    dataset.add_argument('--id', type=str, help='id a ser identificado')

    records = subparsers.add_parser("records", help="registros filtrados")
    records.add_argument('--api_key', type=str, required=True, help="chave da API")
    records.add_argument('--filters', required=True, nargs='*', help="filtros no formato chave=valor (ex: família=rosas)") # nargs permite múltiplos filtros no formato chave=valor
    records.add_argument('--schema', type=str, required=True, help="schema do banco de dados")

    args = parser.parse_args()

    # metadados básicos

    specieslink = species_link(api_key=args.api_key) # o usuario passa sua propria chave da API

    if args.command == "metadata":
        metadata = specieslink.get_metadata(name=args.name, id=args.id) # parametro do método, por ex pede o nome da instituiçao
        if metadata: # se tiver metadados sendo requisitados
            print("\n\nMetadados básicos:\n")
            print(json.dumps(metadata, indent=4, ensure_ascii=False)) # print formatado


    # # coleções e instituições participantes

    elif args.command == "participants":
        participants = specieslink.get_participants()
        if participants:
            print("\n\nParticipantes:\n")
            print(json.dumps(participants, indent=4, ensure_ascii=False)) # print formatado


    # # dados de uma instituição por sigla

    elif args.command == "instituition":
        instituition = specieslink.get_institution_data(acronym=args.acronym, id=args.id, lang=args.lang)
        if instituition:
            print("\n\nInstituições específicas:\n")
            print(json.dumps(instituition, indent=4, ensure_ascii=False)) # print formatado


    # # dados de uma coleção por identificador
    
    elif args.command == "collection":
        collection = specieslink.get_collection_data(acronym=args.acronym, id=args.id, lang=args.lang)
        if collection:
            print("\n\nColeções específicas:\n")
            print(json.dumps(collection, indent=4, ensure_ascii=False)) # print formatado 

    # # dados de um conjunto de dados com um identificador especifico

    elif args.command == "dataset":
        dataset = specieslink.get_dataset_info(id=args.id)
        if dataset:
            print("\n\nConjunto de dados específicos:\n")
            print(json.dumps(dataset, indent=4, ensure_ascii=False)) # print formatado

    # # registros filtrados

    elif args.command == "records":
        filters = {} # dicionário de filtros
        for item in args.filters: # para cada filtro adicionado
            key, value = item.split('=') # divide chave e valor com = como delimitador
            filters[key] = value # adiciona o par ao dicionário

        records = specieslink.search_records(filters=filters)
        if records:
            print("\n\nRegistros filtrados:\n")
            print(json.dumps(records, indent=4, ensure_ascii=False)) # print formatado
            
            db_config = {
                'user': 'root',
                'password': 'root',
                'host': '127.0.0.1',
                'database': args.schema
            }

            specieslink.insert_into_mysql(records, db_config, args.schema)        

if __name__ == "__main__":
    main()
