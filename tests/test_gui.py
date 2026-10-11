import logging
import queue
import tkinter as tk
from pathlib import Path

import pandas as pd
import pytest

import gui
import main


@pytest.fixture(scope="module")
def tk_root():
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Sem display disponível para testes de Tkinter.")
    yield root
    root.destroy()


@pytest.fixture
def janela(tk_root, monkeypatch):
    monkeypatch.setattr(gui, "carregar_config", lambda: {
        "pasta_entrada": None, "nucleos": None, "tamanho_lote": None, "tolerancia_conciliacao": 0.01,
    })
    topo = tk.Toplevel(tk_root)
    topo.withdraw()
    app = gui.JanelaPrincipal(topo)
    yield app
    topo.destroy()


def test_janela_inicia_com_nucleos_padrao_do_sistema(janela):
    assert janela._var_cores.get() == main.limite_seguro_cores()


def test_janela_inicia_com_lote_padrao_5(janela):
    assert janela._var_lote.get() == 5


def test_janela_inicia_com_tolerancia_padrao(janela):
    assert janela._var_tolerancia.get() == 0.01


def test_iniciar_processamento_com_pasta_invalida_mostra_erro(janela, monkeypatch, tmp_path):
    chamado = {}
    monkeypatch.setattr(gui.messagebox, "showerror", lambda titulo, msg: chamado.setdefault("msg", msg))
    janela._var_pasta.set(str(tmp_path / "nao_existe"))

    janela._iniciar_processamento()

    assert chamado.get("msg")
    assert janela._processando is False


def test_queue_handler_coloca_mensagem_formatada_na_fila():
    fila = queue.Queue()
    handler = gui.QueueHandler(fila)
    handler.setFormatter(logging.Formatter("%(message)s"))
    record = logging.LogRecord("teste", logging.INFO, __file__, 1, "ola mundo", None, None)

    handler.emit(record)

    tipo, mensagem = fila.get_nowait()
    assert tipo == "log"
    assert mensagem == "ola mundo"


def test_processar_fila_atualiza_progresso(janela):
    janela._fila.put(("progresso", "ZIPs", 2, 5))
    janela._processar_fila()

    assert janela._barra_progresso["value"] == 2
    assert janela._barra_progresso["maximum"] == 5
    assert janela._label_progresso.cget("text") == "ZIPs: 2/5"


def test_processar_fila_processa_resultado_com_sucesso(janela):
    resultado = main.ResultadoExecucao(
        caminho_excel=Path("relatorio.xlsx"),
        duplicadas={"nfe": 1, "cte": 0, "cancelamento": 0, "nfse": 0, "nfse_abrasf": 0},
        divergencias=pd.DataFrame(),
        total_zips=2,
        total_xmls=0,
    )
    janela._fila.put(("resultado", resultado))
    janela._processar_fila()

    assert janela._processando is False
    assert janela._ultimo_resultado is resultado
    assert "Duplicadas ignoradas: 1" in janela._label_resultado.cget("text")


def test_processar_fila_processa_erro(janela, monkeypatch):
    chamado = {}
    monkeypatch.setattr(gui.messagebox, "showerror", lambda titulo, msg: chamado.setdefault("msg", msg))
    janela._fila.put(("erro", "algo deu errado"))
    janela._processar_fila()

    assert janela._processando is False
    assert chamado.get("msg") == "algo deu errado"
