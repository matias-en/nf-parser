from lxml import etree
from pathlib import Path
from excel_gen import salvar_excel
from datetime import datetime

# Configurações de pastas
base_dir = Path(__file__).resolve().parent.parent
input_dir = base_dir / "data" / "input"
output_dir = base_dir / "data" / "output"

# Cria a pasta output em caso não exista.
output_dir.mkdir(parents=True, exist_ok=True)

arquivos = list(input_dir.glob("*.xml"))
nfse_nacional = {'nfse_sped': 'http://www.sped.fazenda.gov.br/nfse'}

# Aqui cria uma "receita de bolo" de como ler o xml e transformar ele em um formato melhor para navegar "arvore".
def carregar_xml(caminho_arquivo):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(caminho_arquivo), parser)

if __name__ == "__main__":
    if arquivos:
        print(f"Encontrei {len(arquivos)} arquivos. \nIniciando o processamento.")
        lista_final = []

        for nota_atual in arquivos:
            arvore = carregar_xml(nota_atual)

            def limpar_int(xpath_str):
                res = arvore.xpath(xpath_str, namespaces=nfse_nacional)
                if res:
                    texto_limpo = res[0].strip()
                    return int(texto_limpo) if texto_limpo.isdigit() else 0
                return 0

            def pegar_valor(xpath_str):
                res = arvore.xpath(xpath_str, namespaces=nfse_nacional)
                return res[0] if res else ""

            def limpar_num(xpath_str):
                res = arvore.xpath(xpath_str, namespaces=nfse_nacional)
                if res:
                    return float(res[0].replace(',', '.'))
                return 0.0
            
            # Busca os dados do número e data de competência da NFSe.
            numero = limpar_int('//nfse_sped:nNFSe/text()')
            data_competencia = pegar_valor('//nfse_sped:dCompet/text()')
        
            # Busca os dados de CNPJ ou CPF e nome do Prestador.
            doc_p = pegar_valor('//nfse_sped:emit/nfse_sped:CNPJ/text()') or pegar_valor('//nfse_sped:emit//nfse_sped:CPF/text()')
            nome_p = pegar_valor('//nfse_sped:emit/nfse_sped:xNome/text()')

            # Busca os dados de CNPJ ou CPF e nome do Tomador.
            doc_t = pegar_valor('//nfse_sped:toma/nfse_sped:CNPJ/text()') or pegar_valor('//nfse_sped:toma/nfse_sped:CPF/text()')
            nome_t = pegar_valor('//nfse_sped:toma/nfse_sped:xNome/text()')
        
            # Busca os valores de serviço e impostos.
            v_total = limpar_num('//nfse_sped:valores/nfse_sped:vServPrest/nfse_sped:vServ/text()')
            v_issqn = limpar_num('//nfse_sped:valores/nfse_sped:vISSQN/text()')
            aliq = limpar_num('//nfse_sped:valores/nfse_sped:pAliqAplic/text()') / 100
            v_liq = limpar_num('//nfse_sped:valores/nfse_sped:vLiq/text()')
            # v_irrf = limpar_num('//nfse_sped:valores/nfse_sped:vIRRF/text()') Preciso Ler a nota técnica para ver qual nome do campo.
            # v_cpp = limpar_num('//nfse_sped:valores/nfse_sped:vCP/text()') Preciso Ler a nota técnica para ver qual nome do campo.
            # v_csll = limpar_num('//nfse_sped:valores/nfse_sped:vCSLL/text()') Preciso Ler a nota técnica para ver qual nome do campo.

            
            # Busca a informação se o ISS é retido e retorna indicando Sim ou Não, conforme nota técnica da RFB.
            ret_cod = pegar_valor('//nfse_sped:tribMun/nfse_sped:tpRetISSQN/text()')
            ret_texto = "Sim" if ret_cod == "2" else "Não"

            if numero and data_competencia:
                try:
                    data_final = datetime.strptime(data_competencia, "%Y-%m-%d").date()
                except:
                    data_final = data_competencia

                dados_nota = {

                    "Numero": numero,
                    "Data": data_final,
                    "CNPJ/CPF Prestador": doc_p,
                    "Razão Prestador": nome_p,
                    "CNPJ/CPF Tomador": doc_t,
                    "Razão Tomador": nome_t,
                    "Valor Total": v_total,
                    "Aliq ISSQN": aliq,
                    "ISSQN": v_issqn,
                    "ISSQN Retido": ret_texto,
                    #"IRRF": v_irrf
                    #"CPP": v_cpp
                    #"CSRF": v_csll
                    "Valor Liquido": v_liq
                }
                
                lista_final.append(dados_nota)
        
        print("\nProcessamento concluído")
        excel_dir = output_dir / "relatorio_notas.xlsx"
        salvar_excel(lista_final, nome_arquivo=excel_dir)
    else:
        print("Nenhum arquivo XML encontrado na pasta data/input.")

