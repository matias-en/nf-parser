from src.config import carregar_config, salvar_config, CHAVES_PADRAO


def test_carregar_config_sem_arquivo_retorna_padroes(tmp_path):
    config = carregar_config(tmp_path / "nao_existe.yaml")
    assert config == CHAVES_PADRAO


def test_carregar_config_le_valores_do_arquivo(tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(
        "pasta_entrada: C:/notas\nnucleos: 2\ntamanho_lote: 10\ntolerancia_conciliacao: 0.05\n",
        encoding="utf-8",
    )

    config = carregar_config(caminho)
    assert config["pasta_entrada"] == "C:/notas"
    assert config["nucleos"] == 2
    assert config["tamanho_lote"] == 10
    assert config["tolerancia_conciliacao"] == 0.05


def test_carregar_config_arquivo_parcial_mantem_padroes_do_resto(tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text("nucleos: 4\n", encoding="utf-8")

    config = carregar_config(caminho)
    assert config["nucleos"] == 4
    assert config["pasta_entrada"] is None
    assert config["tolerancia_conciliacao"] == 0.01


def test_carregar_config_arquivo_invalido_retorna_padroes(tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text("isto: nao: e: yaml: valido: [", encoding="utf-8")

    config = carregar_config(caminho)
    assert config == CHAVES_PADRAO


def test_carregar_config_arquivo_vazio_retorna_padroes(tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text("", encoding="utf-8")

    config = carregar_config(caminho)
    assert config == CHAVES_PADRAO


def test_salvar_e_recarregar_config(tmp_path):
    caminho = tmp_path / "config.yaml"
    salvar_config({"pasta_entrada": "C:/notas", "nucleos": 3, "tamanho_lote": 8, "tolerancia_conciliacao": 0.02}, caminho)

    config = carregar_config(caminho)
    assert config["pasta_entrada"] == "C:/notas"
    assert config["nucleos"] == 3
    assert config["tamanho_lote"] == 8
    assert config["tolerancia_conciliacao"] == 0.02
