import pandas as pd
import re
import streamlit as st

# Configurações da página
st.set_page_config(page_title='Pipeline', layout='wide', page_icon='⚒️')

# Carregar os dados do CSV ou DataFrame existente
df = pd.read_csv(r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\raw\tabela_historico.csv')
df_usuarios = pd.read_csv(r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\database\lista_usuarios.csv')
df_objetos = pd.read_excel(r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\database\objetos.xlsx')

# Definir tipo string
df['Usuário'] = df['Usuário'].astype(str)
df_usuarios['CPF1'] = df_usuarios['CPF1'].astype(str)

# Renomear colunas

df.rename(columns={'numero_processo': 'Processo',
                   'Usuário': 'CPF'}, inplace=True)
df_usuarios.rename(columns={'CPF1': 'CPF',
                            'nome1': 'Nome'}, inplace=True)

# Substituir '/' por '-' na coluna 'Data/Hora'
df['Data/Hora'] = df['Data/Hora'].str.replace('/', '-')

# # Separar a data e a hora, mantendo apenas a data
# df['Data/Hora'] = df['Data/Hora'].str.split(' ').str[0]

# Converter a coluna 'Data/Hora' para formato datetime
df['Data/Hora'] = pd.to_datetime(df['Data/Hora'], format='%d-%m-%Y %H:%M')

# Função para extrair o Protocolo e o nome do documento
def extrair_texto(descricao):
    # Expressão regular para extrair o protocolo (sequência de dígitos)
    protocolo = re.search(r'Documento (\d+)', descricao)
    
    # Expressão regular para extrair o nome do documento (conteúdo entre parênteses)
    documento = re.search(r'\((.*?)\)', descricao)
    
    # Expressão regular para identificar movimentação (exemplo: recebido, enviado, etc.)
    movimentacao = re.search(r'\b(remetido)\b', descricao)
    
    # Se movimentação for encontrada, usamos ela no nome do documento
    if movimentacao:
        return protocolo.group(1) if protocolo else None, movimentacao.group(1)
    # Caso contrário, retornamos o nome do documento normal
    elif protocolo and documento:
        return protocolo.group(1), documento.group(1)
    return None, None

# Aplicar a função à coluna "Descrição" e criar duas novas colunas
df['Protocolo'], df['Documento'] = zip(*df['Descrição'].apply(extrair_texto))

# Merge através do cpf do usuário
df = pd.merge(df, df_usuarios, on='CPF', how='left')


# ------------------------------

# HOMOLOGADOS
# Filtrar o DataFrame para manter as linhas que contém "homologação"
df_homologados = df[df['Descrição'].str.contains(r'homologação', case=False, na=False)]

# definir a lista de processos que serão retirados da tabela histórico
lista_homologados = df_homologados['Processo'].unique()

df_homologados = df[df['Processo'].isin(lista_homologados)]


# Excluindo as colunas
df_homologados.drop(columns=['Descrição', 'Órgao', 'data', 'id_nivel'], inplace=True)



# ENCERRADOS
# Exclui todas as linhas onde a coluna 'Documento' possui termo de encerramento
df_encerrados = df[df['Documento'] == 'Termo de Encerramento']

# Excluindo as colunas
df_encerrados.drop(columns=['Descrição', 'Órgao', 'data', 'id_nivel'], inplace=True)

# definir a lista de processos encerrados que serão retirados da tabela histórico
lista_encerrados = df_encerrados['Processo'].unique()


# ANDAMENTO
# Filtrar o DataFrame excluindo processos que estão em 'lista_homologados' e 'lista_encerrados'
df_andamento = df[~df['Processo'].isin(lista_homologados) & ~df['Processo'].isin(lista_encerrados)]


# Filtrar o DataFrame para manter as linhas que contêm "remetido" ou "assinado"
df_andamento = df_andamento[df_andamento['Descrição'].str.contains(r'remetido|assinado', case=False, na=False)]
df_andamento.drop(columns=['Descrição', 'Órgao', 'data', 'id_nivel'], inplace=True)

# Exclui todas as linhas onde a coluna 'Documento' contém valores vazios
df_andamento = df_andamento.dropna(subset=['Documento'])



# Salvar o DataFrame atualizado em um novo arquivo CSV
df_homologados.to_csv(r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\processed\df_homologados.csv', index=False)
df_andamento.to_csv(r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\processed\df_andamento.csv', index=False)


# --------------------------------

# TERMOS DE REFERÊNCIA
# Filtrar o DataFrame para manter as linhas que contém "TERMO DE REFERÊNCIA" em Documento
df_tr = df.query('Documento == "Termo de Referência"')

# definir a lista de processos para novo webscraping
df_agrupado = df_tr.groupby('Processo')['Protocolo'].first().reset_index()
lista_protocolos_tr = df_agrupado['Protocolo']
lista_protocolos_tr = pd.DataFrame(lista_protocolos_tr, columns=['Protocolo'])
lista_protocolos_tr.to_csv(r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\processed\lista_protocolos_tr.csv', index=False)
