# 📑 NFe, NFSe & CTe XML Parser to Excel
Este projeto pessoal automatiza a extração de dados de documentos fiscais eletrônicos brasileiros — Notas Fiscais Eletrônicas (NFe), Notas Fiscais de Serviços Eletrônicas (NFSe, padrão nacional e ABRASF), Conhecimentos de Transporte Eletrônico (CTe) e eventos de cancelamento — diretamente de arquivos XML. O objetivo é transformar a complexidade desses documentos em planilhas organizadas e fáceis de analisar.

## 🚀 Funcionalidades

- **Identificação Automática:** Detecta o tipo de documento pelo namespace do XML — NFe (Modelo 55, incluindo emitentes do Simples Nacional via CSOSN), NFSe (Padrão Nacional), NFSe (padrão ABRASF), CTe e eventos de cancelamento de NFe.
- **Processamento em Lote e Paralelo:** Lê arquivos `.xml` soltos ou pacotes `.zip` (sem extração prévia) e processa vários ZIPs em paralelo com `ProcessPoolExecutor`, em lotes configuráveis para controlar o uso de RAM.
- **Organização Automática:** Arquiva cada XML processado em `processados/<CNPJ> - <Razão Social>/`, agrupando por empresa; XMLs não identificados ou corrompidos vão para `processados/_nao_classificados/`, e os ZIPs originais para `processados/_zips_originais/` (backup).
- **Conciliação de Valores:** Compara o total de produtos declarado no cabeçalho da NFe com a soma dos itens e sinaliza divergências acima de uma tolerância configurável (padrão R$ 0,01).
- **Contador de Duplicadas:** Notas já processadas (mesma chave, reaparecendo em ZIPs diferentes) são ignoradas na consolidação e contabilizadas por tipo de documento.
- **Saída Consolidada em Excel (.xlsx)** com uma aba por tipo de documento, mais abas de resumo:
    - **Mercadorias (NFe)** — cabeçalho, emitente, destinatário e valores totais, com status (Normal/Cancelada).
    - **Produtos** — itens de cada NFe: CFOP, CST/CSOSN, NCM, ICMS, IPI, PIS e COFINS.
    - **Transporte (CTe)** — dados de frete, transportadora, remetente/destinatário e NFe referenciada.
    - **Cancelamentos** — eventos de cancelamento vinculados à chave da NFe.
    - **Serviços (Nacional)** e **Serviços (ABRASF)** — dados de prestador/tomador, código de tributação nacional do serviço (NFSe Nacional) e retenções (ISS, IRRF, CSRF/CSLL, PIS/COFINS retidos).
    - **Resumo CFOP** e **Resumo Mensal** — totais agregados prontos para análise.
    - **Resumo Execução** — quantas notas únicas e duplicadas foram processadas, por tipo de documento.
    - **Divergências** — NFes onde o total declarado não bate com a soma dos itens.
    - **Erros** — XMLs que falharam no parse ou não puderam ser classificados, com a origem (ZIP/arquivo).

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- [`lxml`](https://lxml.de/) — parse dos XMLs via XPath (parser configurado sem resolução de entidades externas nem DTD, como mitigação de XXE, já que os arquivos costumam vir de terceiros).
- **SQLite** (via `sqlite3`, biblioteca padrão) — banco temporário em disco usado como camada de consolidação/deduplicação antes de gerar o Excel; descartado ao final da execução (nunca persiste entre execuções, já que cada rodada normalmente é de uma empresa/período diferente).
- [`pandas`](https://pandas.pydata.org/) — geração dos DataFrames que viram as abas do relatório.
- [`openpyxl`](https://openpyxl.readthedocs.io/) — escrita do `.xlsx` com formatação (moeda, data, percentual, cabeçalho estilizado).
- [`tqdm`](https://tqdm.github.io/) — barra de progresso no terminal.
- [`PyYAML`](https://pyyaml.org/) — leitura/escrita do `config.yaml`.
- `tkinter` (biblioteca padrão) — interface gráfica opcional (`gui.py`).
- `concurrent.futures.ProcessPoolExecutor` — paralelismo por processo no processamento dos ZIPs.
- [`pytest`](https://docs.pytest.org/) — suíte de testes automatizados (veja [Testes](#-testes)).
- **PyInstaller** — geração do executável standalone da GUI (`NF-Parser.spec`; pastas `build/` e `dist/` geradas localmente, ignoradas no Git).

## ▶️ Como usar

### Interface gráfica

```bash
python gui.py
```

Escolha a pasta com os XMLs/ZIPs, ajuste núcleos/lote/tolerância se quiser, e clique em **Processar**. O progresso e o log aparecem na própria janela; ao final, um resumo mostra duplicadas ignoradas e divergências encontradas, com botões para abrir a pasta do relatório ou o Excel gerado direto. Marcando "Salvar estas configurações como padrão", os valores escolhidos vão para o `config.yaml` (veja abaixo) e voltam a preencher os campos na próxima abertura.

### Linha de comando — modo interativo (padrão)

```bash
python main.py
```

Pergunta a pasta, os núcleos de CPU e o tamanho do lote.

### Linha de comando — modo não interativo

Útil para rodar via agendador de tarefas ou outro script:

```bash
python main.py --input "C:\caminho\para\xmls" --cores 4 --batch-size 5 --tolerancia 0.01
```

| Argumento | Descrição |
|---|---|
| `--input`, `-i` | Pasta com os XMLs/ZIPs de entrada. Se informado, pula todos os prompts interativos. |
| `--cores`, `-c` | Núcleos de CPU a usar (padrão: metade dos núcleos disponíveis). |
| `--batch-size`, `-b` | Quantidade de ZIPs por lote (padrão: 5). |
| `--tolerancia`, `-t` | Tolerância em R$ para a conciliação de valores (padrão: 0.01). |

O relatório é salvo como `relatorio_notas_AAAAMMDD_HHMMSS.xlsx` na própria pasta de entrada.

### Arquivo de configuração (`config.yaml`)

Copie `config.example.yaml` para `config.yaml` (na raiz do projeto, ou ao lado do `.exe` quando empacotado) para fixar padrões e evitar digitar os mesmos argumentos toda vez:

```yaml
pasta_entrada: null
nucleos: null
tamanho_lote: 5
tolerancia_conciliacao: 0.01
```

Ordem de prioridade: argumentos de linha de comando > `config.yaml` > prompts interativos. Se `pasta_entrada` estiver preenchido no `config.yaml`, `python main.py` (sem nenhum argumento) já roda direto, sem perguntar nada. O `config.yaml` é local (fica fora do Git) — cada máquina/empresa pode ter o seu.

## 📦 Gerando o executável (.exe)

A interface gráfica pode ser empacotada num `.exe` standalone com [PyInstaller](https://pyinstaller.org/), sem precisar instalar Python na máquina que for rodar:

```bash
pip install pyinstaller
pyinstaller NF-Parser.spec
```

O executável fica em `dist/NF-Parser.exe`. Coloque um `config.yaml` na mesma pasta do `.exe` para fixar a pasta de entrada padrão (mesma lógica do modo script, veja acima).

`NF-Parser.spec` empacota só a `gui.py` (interface gráfica) num único arquivo (`--onefile`), sem console (`--windowed`), incluindo o `src/schema.sql` necessário para o banco temporário. Para regenerar o `.spec` do zero ou ajustar as opções (ex.: usar `--onedir` para abrir mais rápido, em troca de distribuir uma pasta em vez de um arquivo único):

```bash
pyinstaller --name NF-Parser --onefile --windowed --add-data "src/schema.sql;." gui.py
```

`main.py` (a CLI) não é empacotado por este `.spec` — ele continua rodando via `python main.py`, útil para agendadores de tarefas que já têm Python instalado.

## 🧪 Testes

```bash
pip install -r requirements.txt
pytest
```

A suíte cobre as funções utilitárias (`src/processor.py`), cada parser de documento fiscal (com XMLs sintéticos, sem nenhum dado real), a camada de banco (`src/db.py`), a conciliação de valores (`src/conciliacao.py`), o `config.yaml` (`src/config.py`), o pipeline completo (`main.py`) e a interface gráfica (`gui.py`).

## 📁 Estrutura do Projeto

```text
NF-Parser/
├── src/                    # Lógica de extração, banco temporário, conciliação e geração do Excel
├── tests/                  # Testes automatizados (pytest)
├── data/                   # Input de XMLs e Output de planilhas (Ignorado no Git)
├── main.py                 # Pipeline + CLI (interativa ou não interativa)
├── gui.py                  # Interface gráfica (Tkinter)
├── NF-Parser.spec          # Empacotamento da GUI em .exe (PyInstaller)
├── config.example.yaml     # Modelo de configuração (copie para config.yaml)
├── pytest.ini              # Configuração do pytest
└── requirements.txt        # Dependências do projeto
```

## ⚖️ LGPD & Privacidade

Este projeto foi desenvolvido para fins de estudo. O código não armazena nem compartilha dados sensíveis. O arquivo `.gitignore` está configurado para garantir que nenhum dado fiscal real (`.xml`, `.xlsx`, `.csv`, `.zip`, a pasta `data/` ou o `config.yaml` de cada máquina) seja enviado ao repositório público. Os testes automatizados usam apenas XMLs fictícios, escritos diretamente no código.
