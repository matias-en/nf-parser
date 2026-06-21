import sqlite3
import tempfile
import os
from pathlib import Path

def conectar():
    arquivo_temp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    caminho = arquivo_temp.name
    arquivo_temp.close()

    conn = sqlite3.connect(caminho)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA foreign_keys = ON")

    return conn, caminho

def criar_tabelas(conn: sqlite3.Connection):
    caminho_schema = Path(__file__).parent / "schema.sql"
    with open(caminho_schema, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

def fechar_e_limpar(conn: sqlite3.Connection, caminho: str):
    conn.close()
    if os.path.exists(caminho):
        os.remove(caminho)