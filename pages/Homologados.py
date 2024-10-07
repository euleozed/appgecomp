import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime
import os


# Configurações da página
st.set_page_config(page_title='Timeline', layout='wide', page_icon='⏳')

# Carregar arquivos
df = pd.read_csv(r'./data/processed/df_homologados.csv',
                 dtype={'Usuário': str,
                        'Protocolo': str},
                 parse_dates=['Data/Hora'])
df_objeto = pd.read_excel(r'./data/database/objetos.xlsx')

# Exclui linhas onde 'Nome', 'Protocolo' e 'Documento' estão vazios
df = df.dropna(subset=['Nome', 'Protocolo', 'Documento'], how='all')


# Título

st.markdown(
    "<h1 style='text-align: center;'>LINHA DO TEMPO DE PROCESSOS ⏳</h1>",
    unsafe_allow_html=True
)

# Caminho para a pasta onde os arquivos CSV estão armazenados
caminho_pasta = 'downloads'

# Lista para armazenar as datas de modificação
datas_modificacao = []

# Percorrer todos os arquivos na pasta
for arquivo in os.listdir(caminho_pasta):
    if arquivo.endswith('.csv'):
        # Obtendo o caminho completo do arquivo
        caminho_arquivo = os.path.join(caminho_pasta, arquivo)
        # Obtendo a data da última modificação
        data_modificacao = os.path.getmtime(caminho_arquivo)
        # Convertendo para um formato legível
        datas_modificacao.append(data_modificacao)

# Verificando se há datas de modificação
if datas_modificacao:
    # Convertendo as timestamps para um formato legível
    datas_modificacao_legiveis = [datetime.fromtimestamp(d).strftime('%d/%m/%Y') for d in datas_modificacao]
    ultima_data = max(datas_modificacao_legiveis)  # Considerando a data mais recente
    st.write(f"Data última atualização: {ultima_data}")
else:
    st.write("Nenhuma data de modificação encontrada nos documentos CSV.")

# ----------------

st.divider()

# Métricas
c1, c2, c3 = st.columns(3)

# Quantidade de processos homologados
qtd_processos = df['Processo'].nunique()

# Quantidade de termos de referência
df_termos = df[df['Documento'] == 'Termo de Referência'].groupby('Protocolo')['Documento'].size().reset_index()
qtd_termos = df_termos['Protocolo'].count()

# Quantidade de documentos produzidos pela gecomp
df_qtd_documentos_gecomp = df[(df['Unidade'] == 'SESAU-GECOMP') &
    (~df['Documento'].str.contains('remetido', case=False, na=False))].groupby('Protocolo')['Documento'].size().reset_index()
qtd_documentos_gecomp = df_qtd_documentos_gecomp['Protocolo'].count()

# Cards
c1.metric("Quantidade de Processos Homologados:", value=qtd_processos)
c2.metric("Quantidade de Termos de Referência Elaborados:", qtd_termos)
c3.metric("Quantidade de Documentos Elaborados pela GECOMP:", value=qtd_documentos_gecomp)
style_metric_cards(background_color= 'rainbow')
st.divider()
# Ordenando o DataFrame pelo número do processo e pela data
df = df.sort_values(by=['Processo', 'Data/Hora']).reset_index(drop=True)

# Converter a coluna 'Data' para datetime
df['Data/Hora'] = pd.to_datetime(df['Data/Hora'])

# Criando a coluna para a quantidade de dias entre o documento 2 e o documento 1
df['Dias entre Documentos'] = df.groupby('Processo')['Data/Hora'].diff().dt.days

# Criando a coluna para a quantidade de dias acumulados entre o primeiro documento e o documento atual
df['Dias Acumulados'] = df.groupby('Processo')['Data/Hora'].transform(lambda x: (x - x.min()).dt.days)

# Mesclar df e df_objeto com base na coluna 'Processo'
df_combinado = pd.merge(df, df_objeto, on='Processo', how='inner')

# Criar lista combinando número do processo e o texto do objeto
opcoes = df_combinado['Processo'].astype(str) + ' - ' + df_combinado['objeto'].astype(str)

# Inicializando df_selected como um DataFrame vazio
df_selected = pd.DataFrame()

# Função para filtrar opções com base na palavra-chave
def filtrar_opcoes(palavra_chave, opcoes):
    return [opcao for opcao in opcoes if palavra_chave.lower() in opcao.lower()]

# Criando o selectbox para escolher o processo
processo_selecionado = st.selectbox('Selecione o processo:', options=opcoes.unique())

# Verificando se um processo foi selecionado
if processo_selecionado:
    # Separar o número do processo selecionado
    processo_escolhido = processo_selecionado.split(' - ')[0]

    # Filtrando o DataFrame com base no processo selecionado
    df_selected = df_combinado[df_combinado['Processo'] == processo_escolhido]

    # Definindo o novo registro
    data_hoje = datetime.now()
    novo_registro = {
        'Processo': processo_escolhido,
        'Data/Hora': data_hoje,
        'Documento': "Dias desde a última movimentação",
        'Unidade': '',
        'Dias entre Documentos': 0,
        'Dias Acumulados': 0
    }

    # Adicionando o novo registro ao DataFrame
    df_selected = pd.concat([df_selected, pd.DataFrame([novo_registro])], ignore_index=True)

    # Converter a coluna 'Data' para datetime
    df_selected['Data'] = pd.to_datetime(df_selected['Data/Hora'])

    # Recalculando as colunas 'Dias entre Documentos' e 'Dias Acumulados'
    df_selected['Dias entre Documentos'] = df_selected.groupby('Processo')['Data/Hora'].diff().dt.days
    df_selected['Dias Acumulados'] = df_selected.groupby('Processo')['Data/Hora'].transform(lambda x: (x - x.min()).dt.days)

    # Ajustando os valores nulos de 'Dias entre Documentos'
    df_selected['Dias entre Documentos'] = df_selected['Dias entre Documentos'].fillna(0)

    # Criar uma coluna de rótulo com 'Documento' e 'Dias entre Documentos'
    df_selected['Rotulo'] = df_selected['Documento'] + ': ' + df_selected['Dias entre Documentos'].astype(int).astype(str) + 'd' + ' - ' + df_selected['Protocolo']

    # Converter a data para formato legível
    df_selected['Data Documento'] = df_selected['Data/Hora'].dt.strftime('%d/%m/%y')

    # Definir dataframe apenas com top 10 valores
    df_fig = df_selected.nlargest(10, 'Dias entre Documentos').sort_values(by='Data/Hora')

    
    c1, c2 = st.columns(2)
    df_termos = df_selected[df_selected['Documento'] == 'Termo de Referência'].groupby('Protocolo')['Documento'].size().reset_index()
    qtd_termos = df_termos['Protocolo'].count()
    qtd_setores = df_selected['Unidade'].nunique()
    
    df_qtd_documentos_gecomp = df_selected[(df_selected['Unidade'] == 'SESAU-GECOMP') &
    (~df_selected['Documento'].str.contains('remetido', case=False, na=False))].groupby('Protocolo')['Documento'].size().reset_index()
    qtd_documentos_gecomp = df_qtd_documentos_gecomp['Protocolo'].count()

    c1.metric("Quantidade de Termos de Referência no Processo:", qtd_termos)
    c1.metric("Quantidade de Setores Envolvidos:", qtd_setores)
    c1.metric("Quantidade de Documentos Produzidos pela GECOMP:", qtd_documentos_gecomp)
    
    # tempo em cada setor
    df_setor_prazos_geral = df_selected.groupby('Unidade').agg(Dias=("Dias entre Documentos", "sum")).nlargest(10, 'Dias').sort_values(by="Dias").reset_index()
    fig_prazos = px.bar(df_setor_prazos_geral,
                        x='Unidade',
                        y='Dias',
                        text_auto=True,)
                        #orientation = 'h',
                        #title = "Duração acumulada em cada setor")
    fig_prazos.update_traces(textposition="outside")
    c2.markdown(f"<h5 style='text-align: center;'>Duração acumulada em cada setor</h5>", unsafe_allow_html=True)
    c2.plotly_chart(fig_prazos)
    style_metric_cards(background_color= 'rainbow')   
    st.divider()
    
    # Criar o gráfico
    st.markdown(f"<h5 style='text-align: center;'>Linha do Tempo do Processo: {processo_escolhido}</h5>", unsafe_allow_html=True)    
    fig = px.area(df_fig,
                  x='Data Documento',
                  y='Dias entre Documentos',
                  markers=True,
                  text='Rotulo')

    # Atualizar a posição dos rótulos
    fig.update_traces(textposition="top center")

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)
    st.divider()

    # Tabela da linha do tempo
    st.markdown(f"<h5 style='text-align: center;'>Tabela do Processo: {processo_escolhido}</h5>", unsafe_allow_html=True)
    df_table = df_selected[['Unidade', 'Nome', 'Protocolo', 'Documento', 'Data Documento', 'Dias entre Documentos', 'Dias Acumulados']].sort_values(by='Dias Acumulados', ascending=False)
    st.dataframe(df_table, hide_index=True, width=1750, height=750)

    st.divider()
    

    


    

else:
    st.write("Por favor, selecione um processo.")