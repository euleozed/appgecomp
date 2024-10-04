import os
import pandas as pd

# Definir o diretório onde os arquivos CSV estão armazenados
download_dir = r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\downloads'
combined_csv_path = os.path.join(download_dir, r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\raw\tabela_historico.csv')

# Inicializar uma lista vazia para armazenar todos os DataFrames
lista_dfs = []

# Percorrer o diretório de downloads e carregar todos os arquivos CSV em DataFrames
for file_name in os.listdir(download_dir):
    if file_name.endswith('.csv'):
        file_path = os.path.join(download_dir, file_name)
        df = pd.read_csv(file_path)
        lista_dfs.append(df)

# Concatenar todos os DataFrames em um único DataFrame
df = pd.concat(lista_dfs, ignore_index=True)

# Salvar o DataFrame consolidado em um arquivo CSV
df.to_csv(combined_csv_path, index=False, encoding='utf-8')
print(f"Arquivo consolidado salvo em: {combined_csv_path}")
