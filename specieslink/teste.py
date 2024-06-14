from main import species_link
import json
import pandas as pd 

def main():
    specieslink = species_link(api_key="EgNGJb7pLEwV67CttplJ")

    # COMENTE E DESCOMENTE, QUANDO NECESSÁRIO, FUNÇÕES QUE NÃO ESTÃO SENDO UTILIZADAS:

    # metadados básicos

    metadata = specieslink.get_metadata()
    if (metadata):
        print("\n\nmetadados básicos:\n")
        print(json.dumps(metadata, indent=4, ensure_ascii=False))  # formatar a saída JSON


    # # coleções e instituições participantes

    participants = specieslink.get_participants()
    if (participants):
        print("\n\ncoleções e instituições participantes:\n")
        print(json.dumps(participants, indent=4, ensure_ascii=False))  # formatar a saída JSON


    # # dados de uma instituição por sigla

    institution_data = specieslink.get_institution_data("USP", lang="pt-br")
    if (institution_data):
        print("\n\ndados da instituição USP na linguagem escolhida:\n")
        print(json.dumps(institution_data, indent=4, ensure_ascii=False))  # formatar a saída JSON


    # # dados de uma coleção por identificador

    collection_data = specieslink.get_collection_data(identifier=10, lang="pt-br")
    if (collection_data):
        print("\n\ndados da coleção com identificador escolhido em português:\n")
        print(json.dumps(collection_data, indent=4, ensure_ascii=False))  # formatar a saída JSON


    # # dados de um conjunto de dados com um identificador especifico

    dataset_info = specieslink.get_dataset_info(id_dataset=8)
    if (dataset_info):
        print("\n\ninformações sobre o conjunto de dados com o identificador especificado:\n")
        print(json.dumps(dataset_info, indent=4, ensure_ascii=False))  # formatar a saída JSON
    

    # registro de biodiversidade filtrados
    filters = {
        "family": "piperaceae",
        "country": "Brasil",
        "stateProvince": "PR"}

    records = specieslink.search_records(filters)
    if (records):
        print("\n\nregistros de biodiversidade encontrados:\n")
        print(json.dumps(records, indent=4, ensure_ascii=False))  # formatar a saída JSON.
        # COMENTE A LINHA ACIMA SE NÃO QUISER VER TODOS OS RESULTADOS EXIBIDOS NO TERMINAL, DESCOMENTE SE QUISER VER

        db_config = {
            'user': 'root',
            'password': 'root',
            'host': '127.0.0.1',
            'database': 'projeto_herbario'
        }

        specieslink.insert_into_mysql(records, db_config)

if __name__ == "__main__":
    main()
