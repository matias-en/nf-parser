# 📑 Processador de Documentos Fiscais — NFe, CTe & NFSe para Excel

Projeto pessoal em desenvolvimento contínuo. A ideia surgiu da necessidade de transformar grandes volumes de documentos fiscais eletrônicos brasileiros — que chegam em XML dentro de pacotes ZIP — em planilhas organizadas e prontas para análise. O que começou como um parser simples de NFe foi crescendo conforme eu fui entendendo melhor as estruturas fiscais e identificando novos casos de uso no meu dia a dia.

---

## 🚀 O que o projeto faz hoje

- **Identificação automática do tipo de documento:** detecta NFe, CTe, NFSe (Padrão Nacional e ABRASF) e eventos de cancelamento a partir do namespace XML de cada arquivo — sem depender do nome do arquivo ou da pasta.
- **Processamento em lote com suporte a ZIP:** lê arquivos XML diretamente de dentro dos pacotes compactados, sem precisar extrair antes. Suporte a múltiplos ZIPs em paralelo.
- **Paralelismo com múltiplos núcleos:** utiliza `ProcessPoolExecutor` para processar os ZIPs simultaneamente, aproveitando o hardware disponível. O número de núcleos é escolhido pelo usuário na inicialização.
- **Deduplicação de documentos:** documentos com a mesma chave fiscal (44 dígitos) processados mais de uma vez no mesmo lote são ignorados automaticamente, evitando dados duplicados no relatório.
- **Relatório Excel consolidado:** gera um único arquivo `.xlsx` com abas separadas por tipo de documento:
  - **Mercadorias (NFe):** emitente, destinatário, valores totais, ICMS, IPI, PIS e COFINS.
  - **Produtos:** detalhamento de itens por nota — NCM, CFOP, quantidade, valor unitário e tributos por produto.
  - **Transporte (CTe):** transportadora, remetente, destinatário, valor do frete, ICMS e NFe referenciada.
  - **Cancelamentos:** chave vinculada, data, protocolo e justificativa.
  - **Serviços (Nacional):** NFSe padrão RFB — prestador, tomador, valores e retenções (ISSQN, IRRF, CPP, CSLL).
  - **Serviços (ABRASF):** NFSe padrão municipal — mesma estrutura adaptada ao padrão da ABRASF.

---

## 🗂️ Tipos de documento suportados

| Documento | Padrão | Status |
|---|---|---|
| NFe | Modelo 55 — `portalfiscal.inf.br/nfe` | ✅ Implementado |
| NFC-e | Modelo 65 — mesmo namespace da NFe | 🔲 Planejado |
| CTe | `portalfiscal.inf.br/cte` | ✅ Implementado |
| MDF-e | `portalfiscal.inf.br/mdfe` | 🔲 Planejado |
| NFSe Nacional | `sped.fazenda.gov.br/nfse` | ✅ Implementado |
| NFSe ABRASF | `abrasf.org.br/nfse.xsd` | ✅ Implementado |
| Cancelamento NFe | Evento `tpEvento 110111` | ✅ Implementado |
| Cancelamento CTe | Evento próprio do CTe | 🔲 Planejado |
| Cancelamento NFSe | Nacional e ABRASF | 🔲 Planejado |

---

## 🛠️ Tecnologias utilizadas

| Biblioteca | Uso |
|---|---|
| `lxml` | Parsing de XML e consultas XPath |
| `pandas` | Consolidação dos dados e geração de DataFrames |
| `openpyxl` | Escrita do relatório Excel |
| `tqdm` | Barra de progresso no terminal |
| `concurrent.futures` | Paralelismo com `ProcessPoolExecutor` |
| `zipfile` | Leitura de XMLs diretamente dentro dos ZIPs |
| `sqlite3` | Armazenamento temporário durante o processamento *(em desenvolvimento)* |

---

## 📁 Estrutura do projeto

```text
projeto/
├── src/
│   ├── loader.py              # Leitura de ZIPs e XMLs do disco
│   ├── processor.py           # Funções utilitárias (limpar_num, formatar_data, etc.)
│   ├── nfe_parser.py          # Extração de dados de NFe
│   ├── cte_parser.py          # Extração de dados de CTe
│   ├── nfse_parser.py         # Extração de dados de NFSe Nacional
│   ├── nfse_abrasf_parser.py  # Extração de dados de NFSe ABRASF
│   ├── event_parser.py        # Extração de eventos de cancelamento
│   ├── excel_gen.py           # Geração do relatório Excel
│   ├── db.py                  # Conexão e inserção no SQLite (em desenvolvimento)
│   └── schema.sql             # Definição das tabelas do banco (em desenvolvimento)
├── data/                      # Ignorado no Git
│   ├── input/                 # XMLs e ZIPs a processar
│   ├── output/                # Relatório Excel gerado
│   └── processados/           # Arquivos já processados (movidos automaticamente)
├── tests/                     # Testes unitários por tipo de documento
├── main.py                    # Ponto de entrada — execução principal
└── requirements.txt           # Dependências do projeto
```

---

## ▶️ Como usar

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Coloque os arquivos XML ou ZIP na pasta `data/input/`.

3. Execute:
```bash
python main.py
```

4. Escolha o número de núcleos a utilizar quando solicitado.

5. O relatório será gerado em `data/output/relatorio_notas_completo.xlsx`.

---

## 🗺️ O que está sendo desenvolvido

- **Deduplicação via SQLite temporário (`:memory:` / arquivo temp):** substituir o controle em memória por um banco SQLite descartável, aproveitando `PRIMARY KEY` e `INSERT OR IGNORE` para garantir unicidade, além de permitir cruzamentos via `JOIN` (NFe × Cancelamento, NFe × CTe) e resumos via `GROUP BY` diretamente em SQL.
- **Organização dos arquivos processados por empresa:** após o processamento, cada XML será movido para `processados/{CNPJ} - {Razão Social}/`, organizando automaticamente os documentos por emitente/transportadora/prestador.
- **Input via terminal:** em vez de pasta fixa, o usuário poderá indicar qualquer caminho no terminal ao iniciar o programa — tornando o projeto utilizável por outras pessoas sem precisar editar o código.
- **Executável standalone:** empacotamento via PyInstaller para distribuição sem necessidade de Python instalado.
- **Novos tipos de documento:** NFC-e, MDF-e, cancelamentos de CTe e NFSe.
- **Melhorias no relatório Excel:** formatação de moeda (R$), datas, ajuste automático de largura de colunas e aba de resumo com totais por CFOP, mês e empresa.
- **Testes unitários:** cobertura de cada parser com XMLs de exemplo, para proteger contra regressões.

---

## ⚖️ LGPD & Privacidade

Projeto desenvolvido para fins de estudo e uso pessoal. O código não armazena nem compartilha dados sensíveis. O `.gitignore` está configurado para que nenhum dado fiscal real (`.xml` ou `.xlsx`) seja enviado ao repositório.