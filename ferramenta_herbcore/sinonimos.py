import os
os.environ["R_HOME"] = r"C:\\Program Files\\R\\R-4.4.2" 
os.environ["PATH"] = r"C:\\Program Files\\R\\R-4.4.2\\bin\\x64" + ";" + os.environ["R_HOME"] 

import re # pra mexer na string
import csv # auto-explicativo
import rpy2.robjects as robjects # mexer com r a partir do python
from rpy2.robjects.packages import importr # importar pacotes r pro python
from rpy2.robjects.vectors import StrVector # importar o vetor r

txt_file = 'plantas_exemplo.txt'  # txt de entrada
csv_file = 'csv_exemplo.csv'  # csv de saída
result_txt_file = 'resultado.txt' # txt de saída

input_txt = "input.txt"  # pra filtragem dos campos relevantes
output_txt = "output.txt"

robjects.r('Sys.setlocale("LC_ALL", "en_US.UTF-8")')

# le txt e extrai o nome das plantas
def extract_plants_from_txt(txt_file):
    with open(txt_file, 'r') as file:
        content = file.read()
    
    # extraindo plantas entre as aspas
    plant_names = re.findall(r'"([^"]+)"', content)
    return plant_names

# salva a lista de plantas em um arquivo CSV
def save_plants_to_csv(plant_names, csv_file):
    with open(csv_file, 'w') as file:
        # escrevendo cada planta no formato com vírgula e quebra de linha após cada uma
        for name in plant_names[:-1]: # pra todos os nomes menos o ultimo
            file.write(f'"{name}",\n')  # para todos, coloca vírgula e quebra de linha
        file.write(f'"{plant_names[-1]}"\n')  # menos pro ultimo, que é so quebra de linha

# lê os nomes das plantas do csv
def read_plants_from_csv(csv_file):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        # remove aspas e extrai os nomes das plantas
        plants = [row[0].strip('"') for row in reader]
    return plants

# busca fuzzy no R com base nos nomes do csv
def perform_lcvp_fuzzy_search(csv_file, max_distance=0.1): # distancia maxima dita qual a ''margem de erro''
    plant_names = read_plants_from_csv(csv_file) # pegando as plantas

    print(plant_names)

    r_plant_names = StrVector(plant_names) # conexão com o R, convertendo os nomes pra um vetor de R pra que ele consiga reconhecer a lista
    
    lcvp_plants = importr('lcvplants')  # importando a biblioteca lcvp_plants
    result = robjects.r['lcvp_fuzzy_search'](r_plant_names, max_distance=max_distance) # realiza a pesquisa

    # convertendo o resultado pra um dataframe do R
    result_df = robjects.r['as.data.frame'](result)
    return result_df

# salva o resultado do R em um arquivo TXT com alinhamento visual
def save_result_to_txt_aligned(result_df, output_file):
    with open(output_file, 'w') as file:
        columns = list(result_df.colnames) # extraindo as colunas do data frame R e converte pra uma lista do python
        
        # pra cada coluna, pega o seu nome e o dado de maior valor, e o tamanho da coluna vai ser determinado por qual for maior entre os dois
        max_widths = [max(len(col), max(len(str(val)) for val in result_df[i])) for i, col in enumerate(columns)]
        
        # pra cada coluna, ajusta o tamanho do dado pro valor do tamanho da coluna max_width, preenchendo com ' ' se precisar
        header = '  '.join(col.ljust(max_widths[i]) for i, col in enumerate(columns))
        file.write(header + '\n') # escreve o cabeçalho e quebra a linha
        file.write('-' * len(header) + '\n')  # linha separadora com o tamanho do cabeçalho pra separar das respostas
        
        # convertendo o data frame do R pra ser iterável no python
        rows = [list(row) for row in zip(*[result_df[i] for i in range(len(columns))])]
        # acessa os dados de cada coluna do df, e zip cria uma tupla com os dados de cada coluna.
        # list converte cada tupla em uma lista, criando uma lista de listas - uma lista de linhas
        
        for row in rows:
            # converte o valor em string, e ajusta o valor da coluna pro seu tamanho máximo
            # depois junta os valores ajustados com '  ' de espaçamento entre eles
            formatted_row = '  '.join(str(val).ljust(max_widths[i]) for i, val in enumerate(row))
            file.write(formatted_row + '\n')


def process_plant_data(input_txt, output_txt):
    with open(input_txt, 'r') as file:
        lines = file.readlines() # salva todas as linhas do arquivo na lista
    
    # remove a linha separadora de --------------
    lines = [line for line in lines if not line.startswith('-')]
    
    # extrair cabeçalho e linhas de dados
    header = lines[0].strip().split() # pega o cabeçalho, remove os espaços e divide em colunas
    data = [line.strip().split(maxsplit=len(header) - 1) for line in lines[1:]] # para cada linha além do cabeçalho, remove espaços e divide em colunas;
    
    # índices relevantes no cabeçalho pra uso posterior
    genus_idx = header.index("Input.Genus")
    epitheton_idx = header.index("Input.Epitheton")


    results = []
    seen_names = set()  # pra garantir que o nome não se repete
    
    for row in data:
        genus = row[genus_idx]
        epitheton = row[epitheton_idx]
        
        original_name = f"{genus} {epitheton}" # nome original, como colocado no banco
        
        if original_name in seen_names: # o nome já foi registrado?
            continue  # se sim, ignora ele
        seen_names.add(original_name) # caso não, adiciona na lista
        
        # buscando Output.Taxon - dois campos após o segundo número de 6 dígitos - por causa de um bug não posso usar ele diretamente
        try:
            # encontrar números de 6 dígitos e pegar os dois campos seguintes (gênero e epíteto)
            numbers = [item for item in row if re.match(r'\d{6}', item)] # é um numero de 6 digitos
            
            if len(numbers) >= 2:
                # se é um número maior do que debug: por enquanto 2
                second_number_index = row.index(numbers[1]) # esse é o segundo maior numero
                
                # pegar os dois próximos campos após o segundo número de 6 dígitos
                output_taxon = f"{row[second_number_index + 1]} {row[second_number_index + 2]}"
        except Exception as e:
            output_taxon = 'NA'
            print(f"erro ao tentar capturar Output.Taxon: {e}")
        
        # eeterminar se é aceito e definir o nome final
        if "accepted" in row or "accepted" in original_name: # se o nome é aceito
            accepted = "sim"
            final_name = original_name  # o nome aceito é o nome original
        elif "synonym" in row or "synonym" in original_name: # se o nome é um sinônimo
            accepted = "nao"
            final_name = output_taxon  # o nome final é o nome do sinônimo
        else:
            accepted = "teste"  # o nome por algum motivo não se encaixa em accepted/synonym (pode ser unresolved) e por enquanto será marcado como teste
            final_name = original_name  # o nome final é o nome original por agora
        
        results.append((original_name, accepted, final_name)) # adiciona o resultado à lista
    
    # escreve os resultados no arquivo de saída
    with open(output_txt, 'w') as file:
        file.write("NOME ORIGINAL\tACEITO\tNOME FINAL\n")
        for original, accepted, final in results:
            file.write(f"{original}\t{accepted}\t{final}\n")

# DESCOMENTE O QUE FOR NECESSÁRIO

# plant_names = extract_plants_from_txt(txt_file)

# save_plants_to_csv(plant_names, csv_file)

# print("executando lcvp_fuzzy_search no R...")
# result = perform_lcvp_fuzzy_search(csv_file)
# print(result)

# save_result_to_txt_aligned(result, result_txt_file)
# print(f"resultado salvo em: {result_txt_file}")

# filtragem dos dados relevantes do txt fornecido anteriormente
process_plant_data(input_txt, output_txt)

print(f"resultado salvo em: {output_txt}")
