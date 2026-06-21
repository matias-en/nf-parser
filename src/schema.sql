CREATE TABLE IF NOT EXIST nfe (
    chave          TEXT PRIMARY KEY,
    numero         INTEGER,
    modelo         INTEGER,
    data           TEXT,
    cnpj_emitente  TEXT,
    razao_emitente TEXT,
    operacao       TEXT,
    cnpj_dest      TEXT,
    razao_dest     TEXT,
    valor_total    REAL,
    bc_icms        REAL,
    icms           REAL,
    ipi            REAL,
    pis            REAL,
    cofins         REAL
);