import logging
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

import main
from src.config import carregar_config, salvar_config


class QueueHandler(logging.Handler):
    def __init__(self, fila: queue.Queue):
        super().__init__()
        self._fila = fila

    def emit(self, record):
        self._fila.put(("log", self.format(record)))


class JanelaPrincipal:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NF Parser")
        self.root.geometry("720x560")
        self.root.minsize(640, 480)

        self._config = carregar_config()
        self._fila = queue.Queue()
        self._processando = False
        self._ultimo_resultado = None

        self._construir_layout()
        self.root.after(150, self._processar_fila)

    def _construir_layout(self):
        frame_topo = ttk.Frame(self.root, padding=10)
        frame_topo.pack(fill="x")

        ttk.Label(frame_topo, text="Pasta com XML/ZIP:").grid(row=0, column=0, sticky="w")
        self._var_pasta = tk.StringVar(value=self._config.get("pasta_entrada") or "")
        ttk.Entry(frame_topo, textvariable=self._var_pasta, width=60).grid(row=0, column=1, padx=5, sticky="we")
        ttk.Button(frame_topo, text="Procurar...", command=self._escolher_pasta).grid(row=0, column=2)
        frame_topo.columnconfigure(1, weight=1)

        frame_opcoes = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frame_opcoes.pack(fill="x")

        maximo_cores = main.limite_seguro_cores() * 2
        ttk.Label(frame_opcoes, text="Núcleos:").grid(row=0, column=0, sticky="w")
        self._var_cores = tk.IntVar(value=self._config.get("nucleos") or main.limite_seguro_cores())
        ttk.Spinbox(frame_opcoes, from_=1, to=max(maximo_cores, 1), textvariable=self._var_cores, width=6).grid(row=0, column=1, padx=(5, 20))

        ttk.Label(frame_opcoes, text="ZIPs por lote:").grid(row=0, column=2, sticky="w")
        self._var_lote = tk.IntVar(value=self._config.get("tamanho_lote") or 5)
        ttk.Spinbox(frame_opcoes, from_=1, to=999, textvariable=self._var_lote, width=6).grid(row=0, column=3, padx=(5, 20))

        ttk.Label(frame_opcoes, text="Tolerância (R$):").grid(row=0, column=4, sticky="w")
        self._var_tolerancia = tk.DoubleVar(value=self._config.get("tolerancia_conciliacao", 0.01))
        ttk.Spinbox(frame_opcoes, from_=0, to=1000, increment=0.01, textvariable=self._var_tolerancia, width=8).grid(row=0, column=5, padx=5)

        frame_acoes = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frame_acoes.pack(fill="x")

        self._var_salvar_config = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_acoes, text="Salvar estas configurações como padrão", variable=self._var_salvar_config).pack(side="left")

        self._botao_processar = ttk.Button(frame_acoes, text="Processar", command=self._iniciar_processamento)
        self._botao_processar.pack(side="right")

        frame_progresso = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frame_progresso.pack(fill="x")

        self._barra_progresso = ttk.Progressbar(frame_progresso, mode="determinate")
        self._barra_progresso.pack(fill="x", side="left", expand=True)
        self._label_progresso = ttk.Label(frame_progresso, text="")
        self._label_progresso.pack(side="left", padx=(10, 0))

        self._texto_log = scrolledtext.ScrolledText(self.root, height=16, state="disabled")
        self._texto_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        frame_resultado = ttk.LabelFrame(self.root, text="Resultado", padding=10)
        frame_resultado.pack(fill="x", padx=10, pady=(0, 10))

        self._label_resultado = ttk.Label(frame_resultado, text="Nenhum processamento realizado ainda.", justify="left")
        self._label_resultado.pack(side="left", fill="x", expand=True)

        self._botao_abrir_pasta = ttk.Button(frame_resultado, text="Abrir pasta", command=self._abrir_pasta_resultado, state="disabled")
        self._botao_abrir_pasta.pack(side="right", padx=(5, 0))
        self._botao_abrir_excel = ttk.Button(frame_resultado, text="Abrir relatório", command=self._abrir_excel_resultado, state="disabled")
        self._botao_abrir_excel.pack(side="right")

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com os XML/ZIP")
        if pasta:
            self._var_pasta.set(pasta)

    def _log(self, mensagem: str):
        self._texto_log.configure(state="normal")
        self._texto_log.insert("end", mensagem + "\n")
        self._texto_log.see("end")
        self._texto_log.configure(state="disabled")

    def _iniciar_processamento(self):
        if self._processando:
            return

        pasta = self._var_pasta.get().strip()
        if not pasta or not Path(pasta).is_dir():
            messagebox.showerror("Pasta inválida", "Selecione uma pasta existente com os arquivos XML/ZIP.")
            return

        cores = max(1, int(self._var_cores.get()))
        lote = max(1, int(self._var_lote.get()))
        tolerancia = max(0.0, float(self._var_tolerancia.get()))

        if self._var_salvar_config.get():
            salvar_config({
                "pasta_entrada": pasta,
                "nucleos": cores,
                "tamanho_lote": lote,
                "tolerancia_conciliacao": tolerancia,
            })

        self._processando = True
        self._botao_processar.configure(state="disabled", text="Processando...")
        self._botao_abrir_pasta.configure(state="disabled")
        self._botao_abrir_excel.configure(state="disabled")
        self._label_resultado.configure(text="Processando...")
        self._barra_progresso.configure(value=0, maximum=1)
        self._label_progresso.configure(text="")

        thread = threading.Thread(
            target=self._executar_pipeline_em_thread,
            args=(Path(pasta), cores, lote, tolerancia),
            daemon=True,
        )
        thread.start()

    def _executar_pipeline_em_thread(self, pasta: Path, cores: int, lote: int, tolerancia: float):
        handler = QueueHandler(self._fila)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        try:
            resultado = main.executar_pipeline(
                pasta, cores, lote,
                tolerancia_conciliacao=tolerancia,
                progresso_zip=lambda atual, total: self._fila.put(("progresso", "ZIPs", atual, total)),
                progresso_xml=lambda atual, total: self._fila.put(("progresso", "XMLs", atual, total)),
                handlers_log_extra=[handler],
            )
            self._fila.put(("resultado", resultado))
        except main.NenhumArquivoEncontrado:
            self._fila.put(("erro", "Nenhum arquivo XML/ZIP encontrado na pasta indicada."))
        except Exception as e:
            self._fila.put(("erro", str(e)))

    def _processar_fila(self):
        try:
            while True:
                item = self._fila.get_nowait()
                tipo = item[0]
                if tipo == "log":
                    self._log(item[1])
                elif tipo == "progresso":
                    _, rotulo, atual, total = item
                    self._barra_progresso.configure(maximum=total, value=atual)
                    self._label_progresso.configure(text=f"{rotulo}: {atual}/{total}")
                elif tipo == "resultado":
                    self._on_resultado(item[1])
                elif tipo == "erro":
                    self._on_erro(item[1])
        except queue.Empty:
            pass
        self.root.after(150, self._processar_fila)

    def _on_resultado(self, resultado):
        self._processando = False
        self._ultimo_resultado = resultado
        self._botao_processar.configure(state="normal", text="Processar")
        self._botao_abrir_pasta.configure(state="normal")
        self._botao_abrir_excel.configure(state="normal")

        total_duplicadas = sum(resultado.duplicadas.values())
        linhas = [f"Relatório: {resultado.caminho_excel.name}"]
        linhas.append(f"ZIPs processados: {resultado.total_zips}  |  XMLs soltos: {resultado.total_xmls}")
        linhas.append(f"Duplicadas ignoradas: {total_duplicadas}" if total_duplicadas else "Nenhuma nota duplicada.")
        if not resultado.divergencias.empty:
            linhas.append(f"Divergências entre total e soma dos itens: {len(resultado.divergencias)} NFe(s).")
        else:
            linhas.append("Nenhuma divergência de valores encontrada.")

        self._label_resultado.configure(text="\n".join(linhas))

    def _on_erro(self, mensagem: str):
        self._processando = False
        self._botao_processar.configure(state="normal", text="Processar")
        self._label_resultado.configure(text="Falha no processamento.")
        messagebox.showerror("Erro no processamento", mensagem)

    def _abrir_pasta_resultado(self):
        if self._ultimo_resultado:
            os.startfile(self._ultimo_resultado.caminho_excel.parent)

    def _abrir_excel_resultado(self):
        if self._ultimo_resultado:
            os.startfile(self._ultimo_resultado.caminho_excel)


def main_gui():
    root = tk.Tk()
    JanelaPrincipal(root)
    root.mainloop()


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main_gui()
