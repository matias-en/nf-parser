import sqlite3
import tempfile
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# MAPEAMENTOS: chave do dicionário do parser → coluna do banco

MAPA_NFE = {
    "Chave":                 "chave",
    "Numero":                "numero",
    "Modelo NF":             "modelo",
    "Data":                  "data",
    "CNPJ Emitente":         "cnpj_emitente",
    "Tipo Doc Emitente":     "tipo_doc_emitente",
    "Razão Emitente":        "razao_emitente",
    "UF Emitente":           "uf_emitente",
    "Operação":              "operacao",
    "CNPJ Destinatário":     "cnpj_dest",
    "Tipo Doc Destinatário": "tipo_doc_dest",
    "Razão Destinatário":    "razao_dest",
    "UF Destinatário":       "uf_dest",
    "Valor Total NF":        "valor_total",
    "BC ICMS":               "bc_icms",
    "ICMS":                  "icms",
    "IPI":                   "ipi",
    "PIS":                   "pis",
    "COFINS":                "cofins",
}

MAPA_PRODUTOS = {
    "Chave":    "chave",
    "Numero":   "numero",
    "Data":     "data",
    "nItem":    "n_item",
    "xProd":    "x_prod",
    "NCM":      "ncm",
    "CFOP":     "cfop",
    "uCom":     "u_com",
    "qCom":     "q_com",
    "vUnCom":   "v_un_com",
    "vProd":    "v_prod",
    "vTotTrib": "v_tot_trib",
    "vICMS":    "v_icms",
    "vPIS":     "v_pis",
    "vCOFINS":  "v_cofins",
    "vIPI":     "v_ipi",
}

MAPA_CTE = {
    "Chave CTe":               "chave_cte",
    "Numero":                  "numero",
    "CFOP":                    "cfop",
    "Data":                    "data",
    "Operação":                "operacao",
    "CNPJ Transportadora":     "cnpj_transportadora",
    "Tipo Doc Transportadora": "tipo_doc_transportadora",
    "Transportadora":          "transportadora",
    "Doc Remetente":           "doc_remetente",
    "Tipo Doc Remetente":      "tipo_doc_remetente",
    "Remetente":               "remetente",
    "Doc Destinatário":        "doc_destinatario",
    "Tipo Doc Destinatário":   "tipo_doc_destinatario",
    "Destinatário":            "destinatario",
    "Valor Frete":             "valor_frete",
    "ICMS CTe":                "icms_cte",
    "NFe Referenciada":        "nfe_referenciada",
}

MAPA_CANCELAMENTO = {
    "Chave Vinculada":   "chave_vinculada",
    "Data do Evento":    "data_evento",
    "Status":            "status",
    "Protocolo Evento":  "protocolo",
    "CNPJ Emitente":     "cnpj_emitente",
    "Tipo Doc Emitente": "tipo_doc_emitente",
    "Justificativa":     "justificativa",
}

MAPA_NFSE = {
    "Chave":               "chave",
    "Numero":              "numero",
    "Data":                "data",
    "CNPJ/CPF Prestador":  "cnpj_prestador",
    "Tipo Doc Prestador":  "tipo_doc_prestador",
    "Razão Prestador":     "razao_prestador",
    "CNPJ/CPF Tomador":    "cnpj_tomador",
    "Tipo Doc Tomador":    "tipo_doc_tomador",
    "Razão Tomador":       "razao_tomador",
    "Valor Total":         "valor_total",
    "Aliq ISSQN":          "aliq_issqn",
    "ISSQN":               "issqn",
    "ISSQN Retido":        "issqn_retido",
    "IRRF":                "irrf",
    "CPP":                 "cpp",
    "CSRF":                "csrf",
    "Valor Líquido":       "valor_liquido",
}

MAPA_NFSE_ABRASF = {
    "Numero":              "numero",
    "Data":                "data",
    "CNPJ/CPF Prestador":  "cnpj_prestador",
    "Tipo Doc Prestador":  "tipo_doc_prestador",
    "Razão Prestador":     "razao_prestador",
    "CNPJ/CPF Tomador":    "cnpj_tomador",
    "Tipo Doc Tomador":    "tipo_doc_tomador",
    "Razão Tomador":       "razao_tomador",
    "Valor Total":         "valor_total",
    "Aliq ISSQN":          "aliq_issqn",
    "ISSQN":               "issqn",
    "ISSQN Retido":        "issqn_retido",
    "IRRF Retido":         "irrf_retido",
    "CPP Retido":          "cpp_retido",
    "CSLL Retido":         "csll_retido",
    "COFINS Retido":       "cofins_retido",
    "PIS Retido":          "pis_retido",
    "Valor Líquido":       "valor_liquido",
}


def _normalizar(dicionario: dict, mapeamento: dict) -> dict:
    """Converte as chaves do dicionário do parser para os nomes das colunas do banco."""
    return {
        coluna: dicionario.get(chave_parser)
        for chave_parser, coluna in mapeamento.items()
    }


class BancoFiscal:
    """
    Banco SQLite temporário (arquivo em disco, descartado ao final).
    Usar sempre como context manager:

        with BancoFiscal() as banco:
            banco.inserir_nfe(cabecalho, produtos)
            dfs = banco.gerar_dataframes()
    """

    def __init__(self):
        self._arquivo_temp = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False, prefix="nf_parser_"
        )
        self._caminho = self._arquivo_temp.name
        self._arquivo_temp.close()

        self.conn = sqlite3.connect(self._caminho)
        self._aplicar_pragmas()
        self._criar_tabelas()
        logger.info(f"Banco temporário criado em: {self._caminho}")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._fechar()

    def _fechar(self):
        try:
            self.conn.close()
        except Exception:
            pass
        if os.path.exists(self._caminho):
            os.remove(self._caminho)
            logger.info("Banco temporário removido.")

    def _aplicar_pragmas(self):
        for pragma in [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA temp_store = MEMORY",
            "PRAGMA cache_size = -64000",
            "PRAGMA foreign_keys = ON",
        ]:
            self.conn.execute(pragma)

    def _criar_tabelas(self):
        caminho_schema = Path(__file__).parent / "schema.sql"
        with open(caminho_schema, encoding="utf-8") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def inserir_nfe(self, cabecalho: dict, produtos: list) -> bool:
        dado = _normalizar(cabecalho, MAPA_NFE)
        cur = self.conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO nfe
                (chave, numero, modelo, data,
                 cnpj_emitente, tipo_doc_emitente, razao_emitente, uf_emitente, operacao,
                 cnpj_dest, tipo_doc_dest, razao_dest, uf_dest,
                 valor_total, bc_icms, icms, ipi, pis, cofins)
            VALUES
                (:chave, :numero, :modelo, :data,
                 :cnpj_emitente, :tipo_doc_emitente, :razao_emitente, :uf_emitente, :operacao,
                 :cnpj_dest, :tipo_doc_dest, :razao_dest, :uf_dest,
                 :valor_total, :bc_icms, :icms, :ipi, :pis, :cofins)
        """, dado)

        nova = cur.rowcount > 0
        if nova and produtos:
            self.conn.executemany("""
                INSERT OR IGNORE INTO produtos
                    (chave, numero, data, n_item, x_prod, ncm, cfop,
                     u_com, q_com, v_un_com, v_prod, v_tot_trib,
                     v_icms, v_pis, v_cofins, v_ipi)
                VALUES
                    (:chave, :numero, :data, :n_item, :x_prod, :ncm, :cfop,
                     :u_com, :q_com, :v_un_com, :v_prod, :v_tot_trib,
                     :v_icms, :v_pis, :v_cofins, :v_ipi)
            """, [_normalizar(p, MAPA_PRODUTOS) for p in produtos])
        return nova

    def inserir_cte(self, dados: dict):
        self.conn.execute("""
            INSERT OR IGNORE INTO cte
                (chave_cte, numero, cfop, data, operacao,
                 cnpj_transportadora, tipo_doc_transportadora, transportadora,
                 doc_remetente, tipo_doc_remetente, remetente,
                 doc_destinatario, tipo_doc_destinatario, destinatario,
                 valor_frete, icms_cte, nfe_referenciada)
            VALUES
                (:chave_cte, :numero, :cfop, :data, :operacao,
                 :cnpj_transportadora, :tipo_doc_transportadora, :transportadora,
                 :doc_remetente, :tipo_doc_remetente, :remetente,
                 :doc_destinatario, :tipo_doc_destinatario, :destinatario,
                 :valor_frete, :icms_cte, :nfe_referenciada)
        """, _normalizar(dados, MAPA_CTE))

    def inserir_cancelamento(self, dados: dict):
        self.conn.execute("""
            INSERT OR IGNORE INTO cancelamentos
                (chave_vinculada, data_evento, status, protocolo,
                 cnpj_emitente, tipo_doc_emitente, justificativa)
            VALUES
                (:chave_vinculada, :data_evento, :status, :protocolo,
                 :cnpj_emitente, :tipo_doc_emitente, :justificativa)
        """, _normalizar(dados, MAPA_CANCELAMENTO))

    def inserir_nfse(self, dados: dict):
        self.conn.execute("""
            INSERT OR IGNORE INTO nfse
                (chave, numero, data,
                 cnpj_prestador, tipo_doc_prestador, razao_prestador,
                 cnpj_tomador, tipo_doc_tomador, razao_tomador,
                 valor_total, aliq_issqn, issqn, issqn_retido,
                 irrf, cpp, csrf, valor_liquido)
            VALUES
                (:chave, :numero, :data,
                 :cnpj_prestador, :tipo_doc_prestador, :razao_prestador,
                 :cnpj_tomador, :tipo_doc_tomador, :razao_tomador,
                 :valor_total, :aliq_issqn, :issqn, :issqn_retido,
                 :irrf, :cpp, :csrf, :valor_liquido)
        """, _normalizar(dados, MAPA_NFSE))

    def inserir_nfse_abrasf(self, dados: dict):
        self.conn.execute("""
            INSERT OR IGNORE INTO nfse_abrasf
                (numero, data,
                 cnpj_prestador, tipo_doc_prestador, razao_prestador,
                 cnpj_tomador, tipo_doc_tomador, razao_tomador,
                 valor_total, aliq_issqn, issqn, issqn_retido,
                 irrf_retido, cpp_retido, csll_retido, cofins_retido,
                 pis_retido, valor_liquido)
            VALUES
                (:numero, :data,
                 :cnpj_prestador, :tipo_doc_prestador, :razao_prestador,
                 :cnpj_tomador, :tipo_doc_tomador, :razao_tomador,
                 :valor_total, :aliq_issqn, :issqn, :issqn_retido,
                 :irrf_retido, :cpp_retido, :csll_retido, :cofins_retido,
                 :pis_retido, :valor_liquido)
        """, _normalizar(dados, MAPA_NFSE_ABRASF))

    def inserir_erro(self, detalhe: str, origem: str = ""):
        self.conn.execute(
            "INSERT INTO erros (detalhe, origem) VALUES (?, ?)",
            (detalhe, origem)
        )

    def commit(self):
        self.conn.commit()

    def gerar_dataframes(self) -> dict:
        import pandas as pd

        def _converter_datas(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
            """
            Converte colunas de data de string (YYYY-MM-DD vindo do SQLite)
            para datetime — necessário para o openpyxl gravar como célula
            de data real e o Excel habilitar filtros por data.
            """
            for col in colunas:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            return df

        df_nfe = pd.read_sql_query("""
            SELECT
                n.chave              AS "Chave",
                n.numero             AS "Numero",
                n.modelo             AS "Modelo NF",
                n.data               AS "Data",
                n.cnpj_emitente      AS "CNPJ Emitente",
                n.tipo_doc_emitente  AS "Tipo Doc Emitente",
                n.razao_emitente     AS "Razão Emitente",
                n.uf_emitente        AS "UF Emitente",
                n.operacao           AS "Operação",
                n.cnpj_dest          AS "CNPJ Destinatário",
                n.tipo_doc_dest      AS "Tipo Doc Destinatário",
                n.razao_dest         AS "Razão Destinatário",
                n.uf_dest            AS "UF Destinatário",
                n.valor_total        AS "Valor Total NF",
                n.bc_icms            AS "BC ICMS",
                n.icms               AS "ICMS",
                n.ipi                AS "IPI",
                n.pis                AS "PIS",
                n.cofins             AS "COFINS",
                CASE WHEN c.chave_vinculada IS NOT NULL
                     THEN 'Cancelada' ELSE 'Normal'
                END                  AS "Status"
            FROM nfe n
            LEFT JOIN cancelamentos c ON n.chave = c.chave_vinculada
        """, self.conn)
        df_nfe = _converter_datas(df_nfe, ["Data"])

        df_produtos = pd.read_sql_query("""
            SELECT
                chave      AS "Chave",
                numero     AS "Numero",
                data       AS "Data",
                n_item     AS "nItem",
                x_prod     AS "xProd",
                ncm        AS "NCM",
                cfop       AS "CFOP",
                u_com      AS "uCom",
                q_com      AS "qCom",
                v_un_com   AS "vUnCom",
                v_prod     AS "vProd",
                v_tot_trib AS "vTotTrib",
                v_icms     AS "vICMS",
                v_pis      AS "vPIS",
                v_cofins   AS "vCOFINS",
                v_ipi      AS "vIPI"
            FROM produtos
        """, self.conn)
        df_produtos = _converter_datas(df_produtos, ["Data"])

        df_cte = pd.read_sql_query("""
            SELECT
                chave_cte               AS "Chave CTe",
                numero                  AS "Numero",
                cfop                    AS "CFOP",
                data                    AS "Data",
                operacao                AS "Operação",
                cnpj_transportadora     AS "CNPJ Transportadora",
                tipo_doc_transportadora AS "Tipo Doc Transportadora",
                transportadora          AS "Transportadora",
                doc_remetente           AS "Doc Remetente",
                tipo_doc_remetente      AS "Tipo Doc Remetente",
                remetente               AS "Remetente",
                doc_destinatario        AS "Doc Destinatário",
                tipo_doc_destinatario   AS "Tipo Doc Destinatário",
                destinatario            AS "Destinatário",
                valor_frete             AS "Valor Frete",
                icms_cte                AS "ICMS CTe",
                nfe_referenciada        AS "NFe Referenciada"
            FROM cte
        """, self.conn)
        df_cte = _converter_datas(df_cte, ["Data"])

        df_cancelamentos = pd.read_sql_query("""
            SELECT
                chave_vinculada   AS "Chave Vinculada",
                data_evento       AS "Data do Evento",
                status            AS "Status",
                protocolo         AS "Protocolo Evento",
                cnpj_emitente     AS "CNPJ Emitente",
                tipo_doc_emitente AS "Tipo Doc Emitente",
                justificativa     AS "Justificativa"
            FROM cancelamentos
        """, self.conn)
        df_cancelamentos = _converter_datas(df_cancelamentos, ["Data do Evento"])

        df_nfse = pd.read_sql_query("""
            SELECT
                chave              AS "Chave",
                numero             AS "Numero",
                data               AS "Data",
                cnpj_prestador     AS "CNPJ/CPF Prestador",
                tipo_doc_prestador AS "Tipo Doc Prestador",
                razao_prestador    AS "Razão Prestador",
                cnpj_tomador       AS "CNPJ/CPF Tomador",
                tipo_doc_tomador   AS "Tipo Doc Tomador",
                razao_tomador      AS "Razão Tomador",
                valor_total        AS "Valor Total",
                aliq_issqn         AS "Aliq ISSQN",
                issqn              AS "ISSQN",
                issqn_retido       AS "ISSQN Retido",
                irrf               AS "IRRF",
                cpp                AS "CPP",
                csrf               AS "CSRF",
                valor_liquido      AS "Valor Líquido"
            FROM nfse
        """, self.conn)
        df_nfse = _converter_datas(df_nfse, ["Data"])

        df_nfse_abrasf = pd.read_sql_query("""
            SELECT
                numero             AS "Numero",
                data               AS "Data",
                cnpj_prestador     AS "CNPJ/CPF Prestador",
                tipo_doc_prestador AS "Tipo Doc Prestador",
                razao_prestador    AS "Razão Prestador",
                cnpj_tomador       AS "CNPJ/CPF Tomador",
                tipo_doc_tomador   AS "Tipo Doc Tomador",
                razao_tomador      AS "Razão Tomador",
                valor_total        AS "Valor Total",
                aliq_issqn         AS "Aliq ISSQN",
                issqn              AS "ISSQN",
                issqn_retido       AS "ISSQN Retido",
                irrf_retido        AS "IRRF Retido",
                cpp_retido         AS "CPP Retido",
                csll_retido        AS "CSLL Retido",
                cofins_retido      AS "COFINS Retido",
                pis_retido         AS "PIS Retido",
                valor_liquido      AS "Valor Líquido"
            FROM nfse_abrasf
        """, self.conn)
        df_nfse_abrasf = _converter_datas(df_nfse_abrasf, ["Data"])

        df_erros = pd.read_sql_query("""
            SELECT detalhe AS "Detalhe", origem AS "Origem" FROM erros
        """, self.conn)

        df_resumo_cfop = pd.read_sql_query("""
            SELECT
                cfop                  AS "CFOP",
                COUNT(*)              AS "Qtd Itens",
                ROUND(SUM(v_prod), 2) AS "Total vProd"
            FROM produtos
            GROUP BY cfop
            ORDER BY cfop
        """, self.conn)

        df_resumo_mensal = pd.read_sql_query("""
            SELECT
                SUBSTR(data, 1, 7)         AS "Mês",
                COUNT(*)                   AS "Qtd NFe",
                ROUND(SUM(valor_total), 2) AS "Total NF"
            FROM nfe
            GROUP BY SUBSTR(data, 1, 7)
            ORDER BY SUBSTR(data, 1, 7)
        """, self.conn)

        return {
            "Mercadorias (NFe)":   df_nfe,
            "Produtos":            df_produtos,
            "Transporte (CTe)":    df_cte,
            "Cancelamentos":       df_cancelamentos,
            "Serviços (Nacional)": df_nfse,
            "Serviços (ABRASF)":   df_nfse_abrasf,
            "Resumo CFOP":         df_resumo_cfop,
            "Resumo Mensal":       df_resumo_mensal,
            "Erros":               df_erros,
        }
