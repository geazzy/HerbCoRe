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

# DESCOMENTE O QUE FOR NECESSÁRIO

# plant_names = extract_plants_from_txt(txt_file)

# save_plants_to_csv(plant_names, csv_file)

# print("executando lcvp_fuzzy_search no R...")
# result = perform_lcvp_fuzzy_search(csv_file)
# print(result)

# save_result_to_txt_aligned(result, result_txt_file)
# print(f"resultado salvo em: {result_txt_file}")
