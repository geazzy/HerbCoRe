from main import species_link

def main():
    specieslink = species_link(api_key="EgNGJb7pLEwV67CttplJ")

    # metadados básicos

    metadata = specieslink.get_metadata()
    if metadata:
        print("metadados básicos:\n")
        print(metadata)

    # coleções e instituições participantes

    participants = specieslink.get_participants()
    if participants:
        print("\n\ncoleções e instituições participantes:\n")
        print(participants)

    # dados de uma instituição por sigla

    institution_data = specieslink.get_institution_data("USP", lang="pt-br")
    if institution_data:
        print("\n\ndados da instituição USP na linguagem escolhida:\n")
        print(institution_data)

    # dados de uma coleção por identificador

    collection_data = specieslink.get_collection_data(identifier=10, lang="pt-br")
    if collection_data:
        print("\n\ndados da coleção com identificador escolhido em português:\n")
        print(collection_data)

    # dados de um conjunto de dados com um identificador especifico
    dataset_info = specieslink.get_dataset_info(id_dataset=8)
    if dataset_info:
        print("\nInformações sobre o conjunto de dados com o identificador especificado:")
        print(dataset_info)

if __name__ == "__main__":
    main()
