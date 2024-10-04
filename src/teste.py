import pandas as pd
import streamlit as st

def calcular_duracoes(df, coluna_data):
    # Certificar-se de que a coluna de datas está no formato datetime
    df[coluna_data] = pd.to_datetime(df[coluna_data])
    
    # Calcular a diferença entre datas consecutivas
    df['Duração'] = df[coluna_data].diff()
    
    return df

# Exemplo de uso
df = pd.read_csv(r"C:\Users\00840207255\OneDrive\SESAU\01 GAD\App Buscar Andamento\downloads\andamentos_consolidados.csv")

# Calcular durações
df_resultado = calcular_duracoes(df, 'Data/Hora')

print(df_resultado)

st.set_page_config()

st.dataframe(df_resultado)

# Criando a coluna para a quantidade de dias entre o documento 2 e o documento 1
df['Dias entre Documentos'] = df.groupby('Processo')['Data'].diff().dt.days

# Criando a coluna para a quantidade de dias acumulados entre o primeiro documento e o documento atual
df['Dias Acumulados'] = df.groupby('Processo')['Data'].transform(lambda x: (x - x.min()).dt.days)