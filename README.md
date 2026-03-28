# 📑 NFe & NFSe XML Parser to Excel
Este projeto pessoal automatiza a extração de dados de Notas Fiscais Eletrônicas (NFe) e Notas Fiscais de Serviços Eletrônicas (NFSe) diretamente de arquivos XML. O objetivo é transformar a complexidade dos documentos fiscais brasileiros em planilhas organizadas e fáceis de analisar.

## 🚀 Funcionalidades

- **Identificação Automática:** Detecta se o arquivo é uma NFe (Modelo 55) ou NFSe (Padrão Nacional). *Obs. Novos padrões a serem implementados no futuro.
- **Processamento em Lote:** Suporte para leitura de arquivos individuais ou pacotes compactados (**ZIP**) sem necessidade de extração prévia.
- **Saída Inteligente:** Gera um arquivo Excel (.xlsx) consolidado com três abas principais:
    1. **Geral:** Dados de emitente, destinatário e valores totais.
    2. **Itens e Tributos (NFe):** Detalhamento de produtos, CFOP, CST, NCM, ICMS, IPI, PIS e COFINS.
    3. **Serviços e Retenções (NFSe):** Código e descrição do serviço e retenções de impostos (ISS, INSS, CSRF, etc).

## 🛠️ Tecnologias Utilizadas

**A ser preenchido no decorrer dos estudos.**

## 📁 Estrutura do Projeto

```text
nfe-parser-xml/
├── src/                # Lógica de extração e processamento
├── data/               # Input de XMLs e Output de planilhas (Ignorado no Git)
├── tests/              # Testes unitários de extração e cálculos
├── main.py             # Arquivo principal para execução
└── requirements.txt    # Dependências do projeto
```

## ⚖️ LGPD & Privacidade

Este projeto foi desenvolvido para fins de estudo. O código não armazena nem compartilha dados sensíveis. O arquivo .gitignore está configurado para garantir que nenhum dado fiscal real (.xml ou .xlsx) seja enviado ao repositório público.

