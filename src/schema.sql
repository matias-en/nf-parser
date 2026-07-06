CREATE TABLE IF NOT EXISTS nfe (
    chave                TEXT PRIMARY KEY,
    numero               INTEGER,
    modelo               INTEGER,
    data                 TEXT,
    cnpj_emitente        TEXT,
    tipo_doc_emitente    TEXT,
    razao_emitente       TEXT,
    uf_emitente          TEXT,
    operacao             TEXT,
    cnpj_dest            TEXT,
    tipo_doc_dest        TEXT,
    razao_dest           TEXT,
    uf_dest              TEXT,
    valor_total          REAL,
    bc_icms              REAL,
    icms                 REAL,
    ipi                  REAL,
    pis                  REAL,
    cofins               REAL
);

CREATE TABLE IF NOT EXISTS produtos (
    chave       TEXT,
    n_item      TEXT,
    numero      INTEGER,
    data        TEXT,
    x_prod      TEXT,
    ncm         TEXT,
    cfop        INTEGER,
    u_com       TEXT,
    q_com       REAL,
    v_un_com    REAL,
    v_prod      REAL,
    v_tot_trib  REAL,
    v_icms      REAL,
    v_pis       REAL,
    v_cofins    REAL,
    v_ipi       REAL,
    PRIMARY KEY (chave, n_item),
    FOREIGN KEY (chave) REFERENCES nfe(chave)
);

CREATE TABLE IF NOT EXISTS cte (
    chave_cte             TEXT PRIMARY KEY,
    numero                INTEGER,
    cfop                  INTEGER,
    data                  TEXT,
    operacao              TEXT,
    cnpj_transportadora   TEXT,
    tipo_doc_transportadora TEXT,
    transportadora        TEXT,
    doc_remetente         TEXT,
    tipo_doc_remetente    TEXT,
    remetente             TEXT,
    doc_destinatario      TEXT,
    tipo_doc_destinatario TEXT,
    destinatario          TEXT,
    valor_frete           REAL,
    icms_cte              REAL,
    nfe_referenciada      TEXT
);

CREATE TABLE IF NOT EXISTS cancelamentos (
    chave_vinculada  TEXT,
    data_evento      TEXT,
    status           TEXT,
    protocolo        TEXT,
    cnpj_emitente    TEXT,
    tipo_doc_emitente TEXT,
    justificativa    TEXT,
    PRIMARY KEY (chave_vinculada, protocolo)
);

CREATE TABLE IF NOT EXISTS nfse (
    chave            TEXT PRIMARY KEY,
    numero           INTEGER,
    data             TEXT,
    cnpj_prestador   TEXT,
    tipo_doc_prestador TEXT,
    razao_prestador  TEXT,
    cnpj_tomador     TEXT,
    tipo_doc_tomador TEXT,
    razao_tomador    TEXT,
    valor_total      REAL,
    aliq_issqn       REAL,
    issqn            REAL,
    issqn_retido     TEXT,
    irrf             REAL,
    cpp              REAL,
    csrf             REAL,
    valor_liquido    REAL
);

CREATE TABLE IF NOT EXISTS nfse_abrasf (
    numero              INTEGER,
    data                TEXT,
    cnpj_prestador      TEXT,
    tipo_doc_prestador  TEXT,
    razao_prestador     TEXT,
    cnpj_tomador        TEXT,
    tipo_doc_tomador    TEXT,
    razao_tomador       TEXT,
    valor_total         REAL,
    aliq_issqn          REAL,
    issqn               REAL,
    issqn_retido        TEXT,
    irrf_retido         REAL,
    cpp_retido          REAL,
    csll_retido         REAL,
    cofins_retido       REAL,
    pis_retido          REAL,
    valor_liquido       REAL,
    PRIMARY KEY (numero, data, cnpj_prestador)
);

CREATE TABLE IF NOT EXISTS erros (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    detalhe  TEXT,
    origem   TEXT
);
