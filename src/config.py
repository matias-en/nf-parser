import sys
from pathlib import Path

import yaml

NOME_ARQUIVO_CONFIG = "config.yaml"

CHAVES_PADRAO = {
    "pasta_entrada": None,
    "nucleos": None,
    "tamanho_lote": None,
    "tolerancia_conciliacao": 0.01,
}


def caminho_config_padrao() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    return base / NOME_ARQUIVO_CONFIG


def carregar_config(caminho: Path = None) -> dict:
    caminho = caminho or caminho_config_padrao()
    config = dict(CHAVES_PADRAO)

    if not caminho.is_file():
        return config

    try:
        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return config

    if not isinstance(dados, dict):
        return config

    for chave in CHAVES_PADRAO:
        if dados.get(chave) is not None:
            config[chave] = dados[chave]

    return config


def salvar_config(config: dict, caminho: Path = None) -> None:
    caminho = caminho or caminho_config_padrao()
    dados = {chave: config.get(chave, valor) for chave, valor in CHAVES_PADRAO.items()}
    with open(caminho, "w", encoding="utf-8") as f:
        yaml.safe_dump(dados, f, allow_unicode=True, sort_keys=False)
