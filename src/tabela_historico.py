import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

import os
import time
from io import StringIO
import re

# Configuração do WebDriver
service = Service(ChromeDriverManager().install())
chrome_options = webdriver.ChromeOptions()

# Diretório de downloads
download_dir = r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\downloads'
chrome_options.add_experimental_option('prefs', {
    'download.default_directory': download_dir,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True
})

driver = webdriver.Chrome(service=service, options=chrome_options)
driver.maximize_window()

# Acessar o site e realizar login
driver.get('https://sei.sistemas.ro.gov.br/sip/login.php?sigla_orgao_sistema=RO&sigla_sistema=SEI')

# Exemplo de login (substitua pelas suas credenciais)
usuario = driver.find_element(By.ID, 'txtUsuario')
senha = driver.find_element(By.ID, 'pwdSenha')
orgao = driver.find_element(By.ID, 'selOrgao')

usuario.send_keys('00840207255')
senha.send_keys('Setembro10')
orgao.send_keys('SEOSP')
senha.send_keys(webdriver.common.keys.Keys.RETURN)

# Carregar os números de processo a partir do CSV
csv_path = r'C:\Users\00840207255\OneDrive - Minha Empresa\Aplicativos\App timeline\data\database\numeros_processos.csv'
df_documentos = pd.read_csv(csv_path, dtype={'numero_processo': str})

# Função para substituir caracteres especiais por _
def substituir_caracteres_especiais(nome):
    return re.sub(r'[^\w\s]', '_', nome)

# Garantir que o diretório de download exista
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Função para aguardar iframe e retornar ao conteúdo principal
def alternar_para_iframe(id_iframe):
    WebDriverWait(driver, 30).until(EC.frame_to_be_available_and_switch_to_it((By.ID, id_iframe)))
    print(f"Alternando para o iframe '{id_iframe}'.")

# Função para realizar a pesquisa do processo
def pesquisar_processo(numero_processo):
    try:
        pesquisa = WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.ID, 'txtPesquisaRapida'))
        )
        pesquisa.clear()
        pesquisa.send_keys(numero_processo)
        pesquisa.send_keys(webdriver.common.keys.Keys.RETURN)
        print(f"Processo {numero_processo} pesquisado.")
        time.sleep(2)  # Espera adicional para garantir que o conteúdo carregue
    except Exception as e:
        print(f"Erro ao pesquisar o processo {numero_processo}: {str(e)}")

# Iterar pelos processos no CSV
for index, row in df_documentos.iterrows():
    numero_processo = str(row['numero_processo'])
    nome_arquivo = substituir_caracteres_especiais(numero_processo)

    try:
        print(f"Iniciando a busca do processo {numero_processo}.")
        pesquisar_processo(numero_processo)

        # Alternar para o iframe pai onde está o botão de "Consultar Andamento"
        alternar_para_iframe('ifrArvore')

        # Aguardar o link "Consultar Andamento" aparecer dentro do iframe
        print("Aguardando o link 'Consultar Andamento'.")
        botao_consultar = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#divConsultarAndamento > a'))
        )

        if botao_consultar.is_displayed():
            driver.execute_script("arguments[0].click();", botao_consultar)
            print("Botão 'Consultar Andamento' clicado.")
        else:
            print(f"Link 'Consultar Andamento' não está visível para o processo {numero_processo}.")

        driver.switch_to.default_content()  # Voltar para o conteúdo principal antes de mudar para o próximo iframe

        # Alternar para o iframe interno onde está a tabela
        alternar_para_iframe('ifrVisualizacao')

        # Verificar se o link "Ver histórico resumido" está visível
        try:
            botao_historico_resumido = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ancTipoHistorico" and contains(text(), "Ver histórico resumido")]'))
            )

            if botao_historico_resumido.is_displayed():
                print(f"Link 'Ver histórico resumido' está visível. Extraindo dados para o processo {numero_processo}.")

                # Criar um DataFrame vazio para armazenar todos os dados
                df_todos_dados = pd.DataFrame()

                # Variável para controle de navegação
                pagina_atual = 1
                
                while True:  # Continua até que não haja mais páginas
                    # Aguardar a tabela carregar
                    tabela = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'infraTable'))
                    )

                    # Pegar o HTML da tabela para transformar em DataFrame
                    tabela_html = tabela.get_attribute('outerHTML')
                    tabela_io = StringIO(tabela_html)
                    df_tabela = pd.read_html(tabela_io)[0]  # Converte HTML em DataFrame

                    # Adicionar a coluna com o número do processo
                    df_tabela['numero_processo'] = numero_processo

                    # Adicionar os dados da tabela atual ao DataFrame total
                    df_todos_dados = pd.concat([df_todos_dados, df_tabela], ignore_index=True)

                    # Tentar navegar para a próxima página
                    try:
                        # Esperar pelo elemento de seleção de página superior
                        pagina_seletor = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="selInfraPaginacaoSuperior"]'))
                        )

                        # Obter o valor atual da página e o total de páginas
                        total_opcoes = len(pagina_seletor.find_elements(By.TAG_NAME, 'option'))  # Total de páginas

                        # Verifica se ainda há páginas para navegar
                        if pagina_atual < total_opcoes:
                            # Mudar para a próxima página
                            pagina_atual += 1  # Incrementa para a próxima página
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", pagina_seletor, pagina_atual)
                            print(f"Navegando para a página {pagina_atual}.")

                            # Aguardar a tabela da nova página carregar
                            WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'infraTable'))  # Aguardar a tabela da nova página
                            )
                        else:
                            print(f"Não há mais páginas para o processo {numero_processo}.")
                            break  # Sai do loop se não houver mais páginas

                    except Exception as e:
                        print(f"Erro ao tentar navegar para a próxima página para o processo {numero_processo}: {str(e)}")
                        break  # Sai do loop se houver erro ao mudar de página

                # Criar nome do arquivo e salvar todos os dados em CSV
                nome_arquivo_csv = f'processo_{nome_arquivo}.csv'
                output_csv_path = os.path.join(download_dir, nome_arquivo_csv)
                df_todos_dados.to_csv(output_csv_path, index=False, encoding='utf-8')

                print(f"Tabela de andamento para o processo {numero_processo} salva em {output_csv_path}.")

            else:
                print(f"Link 'Ver histórico resumido' não está visível para o processo {numero_processo}.")

        except TimeoutException:
            # Se o botão de histórico resumido não está visível, então verifique o histórico completo
            print(f"Link 'Ver histórico resumido' não encontrado. Tentando 'Ver histórico completo' para o processo {numero_processo}.")

            # Ver histórico completo
            botao_historico_completo = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ancTipoHistorico"]'))
            )

            if botao_historico_completo.is_displayed():
                driver.execute_script("arguments[0].click();", botao_historico_completo)
                print("Botão 'botao_historico_completo' clicado.")

                # Aguardar a tabela carregar após clicar no histórico completo
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'infraTable'))  # Aguardar a tabela
                )

                # Criar um DataFrame vazio para armazenar todos os dados
                df_todos_dados = pd.DataFrame()

                # Variável para controle de navegação
                pagina_atual = 1
                
                while True:  # Continua até que não haja mais páginas
                    # Aguardar a tabela carregar
                    tabela = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'infraTable'))
                    )

                    # Pegar o HTML da tabela para transformar em DataFrame
                    tabela_html = tabela.get_attribute('outerHTML')
                    tabela_io = StringIO(tabela_html)
                    df_tabela = pd.read_html(tabela_io)[0]  # Converte HTML em DataFrame

                    # Adicionar a coluna com o número do processo
                    df_tabela['numero_processo'] = numero_processo

                    # Adicionar os dados da tabela atual ao DataFrame total
                    df_todos_dados = pd.concat([df_todos_dados, df_tabela], ignore_index=True)

                    # Tentar navegar para a próxima página
                    try:
                        # Esperar pelo elemento de seleção de página superior
                        pagina_seletor = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="selInfraPaginacaoSuperior"]'))
                        )

                        # Obter o valor atual da página e o total de páginas
                        total_opcoes = len(pagina_seletor.find_elements(By.TAG_NAME, 'option'))  # Total de páginas

                        # Verifica se ainda há páginas para navegar
                        if pagina_atual < total_opcoes:
                            # Mudar para a próxima página
                            pagina_atual += 1  # Incrementa para a próxima página
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", pagina_seletor, pagina_atual)
                            print(f"Navegando para a página {pagina_atual}.")

                            # Aguardar a tabela da nova página carregar
                            WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'infraTable'))  # Aguardar a tabela da nova página
                            )
                        else:
                            print(f"Não há mais páginas para o processo {numero_processo}.")
                            break  # Sai do loop se não houver mais páginas

                    except Exception as e:
                        print(f"Erro ao tentar navegar para a próxima página para o processo {numero_processo}: {str(e)}")
                        break  # Sai do loop se houver erro ao mudar de página

                # Criar nome do arquivo e salvar todos os dados em CSV
                nome_arquivo_csv = f'processo_{nome_arquivo}.csv'
                output_csv_path = os.path.join(download_dir, nome_arquivo_csv)
                df_todos_dados.to_csv(output_csv_path, index=False, encoding='utf-8')

                print(f"Tabela de andamento completo para o processo {numero_processo} salva em {output_csv_path}.")

            else:
                print(f"Link 'Ver histórico completo' não está visível para o processo {numero_processo}.")

    except Exception as e:
        print(f"Erro ao processar o processo {numero_processo}: {str(e)}")

    finally:
        # Garantir que o navegador volte à página de pesquisa para o próximo processo
        driver.get('https://sei.sistemas.ro.gov.br')

# Fechar o navegador
driver.quit()


