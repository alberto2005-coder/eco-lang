#!/usr/bin/env python3
"""IDE de escritorio para eco (tkinter, sin dependencias externas).

    py ide.py               arranca el IDE
    py ide.py --version     versión del programa

El botón Ejecutar (F5) manda el código a `runtime.run_analysis()`, que usa
`eco.exe` si está instalado o el intérprete de Python si no. Si el programa
hace `entrada(...)`, se abre un diálogo para responder.

Depuración (F9): pulsa en los números de línea para marcar puntos de ruptura;
después F9 depura, F10 avanza un paso, F11 sigue hasta el próximo punto y
Esc detiene. La pestaña "Variables" muestra los valores en cada paso.
"""

import json
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, simpledialog

import interpreter
from runtime import VERSION, run_analysis, runtime_name

# ---------------------------------------------------------------- colores
BG        = "#0b0e14"
PANEL     = "#11151f"
PANEL2    = "#151a26"
LINE      = "#232a3a"
EDITOR_BG = "#0d1119"
FG        = "#dbe4f0"
DIM       = "#7d8aa3"
ACCENT    = "#7aa2ff"
OK        = "#4ade80"
BAD       = "#ff6b6b"
C_KW, C_STR, C_NUM, C_COM, C_OP, C_ID = "#c792ea", "#8be9a8", "#ffc66d", "#5b6578", "#89ddff", "#dbe4f0"

KW = {"variable", "const", "escribe", "si", "sino", "mientras", "para", "en",
      "funcion", "devuelve", "romper", "continuar", "verdadero", "falso",
      "nulo", "y", "o", "no", "importar", "como"}
OPERADORES = "+-*/%=!<;^,(){}[]."

DEMO = """// Escríbeme y pulsa  F5
variable nombre = "Mundo";
variable edad = 30;

escribe "Hola, ${nombre}! Tienes ${edad} años.";

si (edad >= 18) {
    escribe "mayor de edad";
} sino {
    escribe "menor";
}

variable suma = 0;
para (variable i = 0; i < 5; i = i + 1) {
    suma = suma + i;
}
escribe "suma 0..4 = ${suma}";

funcion doble(n) {
    devuelve n * 2;
}
escribe doble(21);
"""

FASE = {"lex": "análisis léxico", "parse": "análisis sintáctico", "run": "ejecución"}


def examples_dir():
    cands = []
    if getattr(sys, "frozen", False):
        cands.append(Path(sys.executable).resolve().parent / "ejemplos")
        cands.append(Path(getattr(sys, "_MEIPASS", "")) / "ejemplos")
    cands.append(Path(__file__).resolve().parent / "ejemplos")
    for c in cands:
        if c and c.is_dir():
            return c
    return None


class Ide(tk.Tk):
    def __init__(self):
        super().__init__()
        self.file = None
        self.dirty = False
        self.busy = False
        self.err_line = None
        self.q = queue.Queue()
        self._cola_entradas = queue.Queue()   # diálogos de entrada() (hilo -> Tk)
        self.examples = {}
        self.example_path = None              # ruta del ejemplo elegido (para importar)

        # ---- depuración paso a paso (F9/F10/F11/Esc) ----
        self.bp = set()                       # líneas con punto de ruptura
        self._cola_debug = queue.Queue()      # pasos: hilo de ejecución -> Tk
        self._dbg_respuesta = None            # cola para contestar al hilo
        self._dbg_modo = "step"               # "step" | "continue" | "stop"
        self._dbg_activo = False
        self._dbg_primero = True              # siempre paramos en la 1ª instrucción
        self._dbg_tab_vista = False

        self._build()
        self._bind_events()
        self.set_source(DEMO, None)
        self.after(60, self._procesar_entradas)
        self.after(60, self._procesar_debug)
        self.after(80, self._poll)
        self.after(150, self._refresh_runtime)
        # si no hay eco.exe, el intérprete corre dentro del IDE: mismo diálogo
        interpreter.set_input_handler(self._pedir_entrada)

    # ------------------------------------------------------------ interfaz
    def _build(self):
        self.title("eco IDE")
        self.geometry("1220x780")
        self.minsize(880, 540)
        self.configure(bg=PANEL)

        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure(".", background=PANEL, foreground=FG, fieldbackground=EDITOR_BG,
                     bordercolor=LINE, lightcolor=LINE, darkcolor=LINE)
        st.configure("TFrame", background=PANEL)
        st.configure("Panel.TFrame", background=EDITOR_BG)
        st.configure("TLabel", background=PANEL, foreground=DIM)
        st.configure("Chip.TLabel", background=PANEL2, foreground=OK)
        st.configure("Dbg.TLabel", background=PANEL2, foreground=ACCENT)
        st.configure("TButton", background=PANEL2, foreground=FG)
        st.map("TButton", background=[("active", LINE)])
        st.configure("Run.TButton", background=ACCENT, foreground="#08101f")
        # el tema deja el texto gris al deshabilitarlo y sobre el azul no se ve
        st.map("Run.TButton",
               background=[("disabled", "#5b82d6"), ("active", "#93b7ff")],
               foreground=[("disabled", "#08101f"), ("active", "#08101f")])
        st.configure("TNotebook", background=PANEL, borderwidth=0)
        st.configure("TNotebook.Tab", background=PANEL2, foreground=DIM, padding=(12, 6))
        st.map("TNotebook.Tab", background=[("selected", EDITOR_BG)],
               foreground=[("selected", ACCENT)])
        st.configure("Treeview", background=EDITOR_BG, foreground=FG,
                     fieldbackground=EDITOR_BG, rowheight=24, borderwidth=0)
        st.configure("Treeview.Heading", background=PANEL2, foreground=DIM)
        st.configure("Vertical.TScrollbar", background=PANEL2, troughcolor=EDITOR_BG,
                     bordercolor=PANEL, arrowcolor=DIM)

        self._build_menu()

        # ---------------- barra de herramientas ----------------
        bar = ttk.Frame(self, padding=(10, 8))
        bar.pack(fill="x")
        self.btn_run = ttk.Button(bar, text="▶  Ejecutar  (F5)", style="Run.TButton",
                                  command=self.run)
        self.btn_run.pack(side="left")
        self.btn_dbg = ttk.Button(bar, text="🐞  Depurar  (F9)", command=self.debug)
        self.btn_dbg.pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Nuevo", command=self.new_file).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Abrir…", command=self.open_file).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Guardar", command=self.save_file).pack(side="left", padx=(6, 0))

        ttk.Label(bar, text="   ejemplo:").pack(side="left", padx=(14, 4))
        self.cmb_ex = ttk.Combobox(bar, state="readonly", width=22, values=["— elegir —"])
        self.cmb_ex.set("— elegir —")
        self.cmb_ex.pack(side="left")
        self.cmb_ex.bind("<<ComboboxSelected>>", self._load_example)

        self.lbl_rt = ttk.Label(bar, text="runtime: …", style="Chip.TLabel")
        self.lbl_rt.pack(side="right")

        # --------------- barra del depurador (visible solo con F9) ---------------
        self.dbg_bar = ttk.Frame(self, padding=(10, 5), relief="flat")
        self.btn_step = ttk.Button(self.dbg_bar, text="⏭  Paso  (F10)",
                                   command=self.dbg_step)
        self.btn_step.pack(side="left")
        self.btn_cont = ttk.Button(self.dbg_bar, text="⏭  Seguir  (F11)",
                                   command=self.dbg_continue)
        self.btn_cont.pack(side="left", padx=(6, 0))
        self.btn_stop = ttk.Button(self.dbg_bar, text="■  Detener  (Esc)",
                                   command=self.dbg_stop)
        self.btn_stop.pack(side="left", padx=(6, 0))
        ttk.Label(self.dbg_bar,
                  text="   clic en el número de línea = punto de ruptura"
                  ).pack(side="left", padx=(14, 0))
        self.lbl_dbg = ttk.Label(self.dbg_bar, text="", style="Dbg.TLabel")
        self.lbl_dbg.pack(side="right")

        # ---------------- cuerpo ----------------
        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        self.body = body

        # ---- editor con números de línea ----
        left = ttk.Frame(body, style="Panel.TFrame")
        body.add(left, weight=3)

        self._crear_barra_buscar(left)      # Ctrl+F / Ctrl+H (empaqueta al abrirla)

        self.gutter = tk.Text(left, width=4, padx=6, pady=10, takefocus=0,
                              relief="flat", borderwidth=0, font=("Consolas", 11),
                              bg="#0b0f17", fg="#465065", insertwidth=0, wrap="none",
                              state="disabled", highlightthickness=0)
        self.gutter.pack(side="left", fill="y")
        self.gutter.bind("<Button-1>", self._gutter_click)   # clic = punto de ruptura

        self.editor = tk.Text(left, relief="flat", borderwidth=0, padx=12, pady=10,
                              font=("Consolas", 11), bg=EDITOR_BG, fg=C_ID,
                              insertbackground=ACCENT, selectbackground="#2b3f66",
                              selectforeground=FG, wrap="none", undo=True,
                              highlightthickness=0, tabs=(32,))
        sb = ttk.Scrollbar(left, orient="vertical", command=self._scrollbar)
        self.editor.configure(yscrollcommand=self._on_yscroll)
        sb.pack(side="left", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)
        self._sb = sb

        for tag, col in (("kw", C_KW), ("str", C_STR), ("num", C_NUM),
                         ("com", C_COM), ("op", C_OP), ("id", C_ID)):
            self.editor.tag_configure(tag, foreground=col)
        # línea donde está detenido el depurador (solo fondo: conserva los colores)
        self.editor.tag_configure("dbg", background="#1d3b63")
        # coincidencias de la búsqueda (Ctrl+F): la actual encima de las demás
        self.editor.tag_configure("buscar", background="#23364e")
        self.editor.tag_configure("buscar_actual", background="#3f5f96")

        # ---- consola con pestañas ----
        right = ttk.Frame(body)
        body.add(right, weight=2)

        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True)

        f_out = ttk.Frame(self.nb, style="Panel.TFrame")
        self.nb.add(f_out, text="  Salida  ")
        self.out = tk.Text(f_out, relief="flat", borderwidth=0, padx=12, pady=10,
                           font=("Consolas", 11), bg=EDITOR_BG, fg="#cfe3ff",
                           wrap="word", state="disabled", highlightthickness=0)
        osb = ttk.Scrollbar(f_out, orient="vertical", command=self.out.yview)
        self.out.configure(yscrollcommand=osb.set)
        osb.pack(side="right", fill="y")
        self.out.pack(fill="both", expand=True)
        for tag, col in (("err", "#ffb3bd"), ("tag", "#ffd0d6"), ("ok", OK)):
            self.out.tag_configure(tag, foreground=col)

        f_tok = ttk.Frame(self.nb, style="Panel.TFrame")
        self.nb.add(f_tok, text="  Tokens  ")
        self.tree = ttk.Treeview(f_tok, columns=("valor", "pos"), show="tree headings")
        self.tree.heading("#0", text="Tipo")
        self.tree.heading("valor", text="Valor")
        self.tree.heading("pos", text="Posición")
        self.tree.column("#0", width=110, stretch=False)
        self.tree.column("valor", width=170)
        self.tree.column("pos", width=80, stretch=False)
        tsb = ttk.Scrollbar(f_tok, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        tsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        f_ast = ttk.Frame(self.nb, style="Panel.TFrame")
        self.nb.add(f_ast, text="  AST  ")
        self.ast = tk.Text(f_ast, relief="flat", borderwidth=0, padx=12, pady=10,
                           font=("Consolas", 10), bg=EDITOR_BG, fg="#9fb6d8",
                           wrap="word", state="disabled", highlightthickness=0)
        asb = ttk.Scrollbar(f_ast, orient="vertical", command=self.ast.yview)
        self.ast.configure(yscrollcommand=asb.set)
        asb.pack(side="right", fill="y")
        self.ast.pack(fill="both", expand=True)

        # ---- variables (la usa el depurador paso a paso) ----
        f_var = ttk.Frame(self.nb, style="Panel.TFrame")
        self.nb.add(f_var, text="  Variables  ")
        self.tree_var = ttk.Treeview(f_var, columns=("valor",), show="tree headings")
        self.tree_var.heading("#0", text="Nombre")
        self.tree_var.heading("valor", text="Valor")
        self.tree_var.column("#0", width=150, stretch=False)
        self.tree_var.column("valor", width=260)
        vsb = ttk.Scrollbar(f_var, orient="vertical", command=self.tree_var.yview)
        self.tree_var.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree_var.pack(fill="both", expand=True)

        # ---------------- barra de estado ----------------
        bar2 = ttk.Frame(self, padding=(12, 6))
        bar2.pack(fill="x")
        self.lbl_state = ttk.Label(bar2, text="Listo")
        self.lbl_state.pack(side="left")
        self.lbl_pos = ttk.Label(bar2, text="Ln 1, Col 1")
        self.lbl_pos.pack(side="right")
        ttk.Label(bar2, text="  ·  ").pack(side="right")

    def _build_menu(self):
        m = tk.Menu(self, tearoff=0, bg=PANEL2, fg=FG, activebackground=LINE,
                    activeforeground=FG, borderwidth=0)
        arch = tk.Menu(m, tearoff=0, bg=PANEL2, fg=FG, activebackground=LINE,
                       activeforeground=FG)
        arch.add_command(label="Nuevo", accelerator="Ctrl+N", command=self.new_file)
        arch.add_command(label="Abrir…", accelerator="Ctrl+O", command=self.open_file)
        arch.add_command(label="Guardar", accelerator="Ctrl+S", command=self.save_file)
        arch.add_command(label="Guardar como…", command=self.save_file_as)
        arch.add_separator()
        arch.add_command(label="Salir", command=self._quit)
        m.add_cascade(label="Archivo", menu=arch)

        ej = tk.Menu(m, tearoff=0, bg=PANEL2, fg=FG, activebackground=LINE,
                     activeforeground=FG)
        ej.add_command(label="Ejecutar", accelerator="F5", command=self.run)
        ej.add_command(label="Depurar", accelerator="F9", command=self.debug)
        ej.add_command(label="Paso a paso", accelerator="F10", command=self.dbg_step)
        ej.add_command(label="Seguir al próximo punto", accelerator="F11",
                       command=self.dbg_continue)
        ej.add_command(label="Detener depuración", accelerator="Esc",
                       command=self.dbg_stop)
        ej.add_separator()
        ej.add_command(label="Limpiar consola", command=self.clear_console)
        m.add_cascade(label="Ejecutar", menu=ej)

        ay = tk.Menu(m, tearoff=0, bg=PANEL2, fg=FG, activebackground=LINE,
                     activeforeground=FG)
        ay.add_command(label="Acerca de…", command=self._about)
        m.add_cascade(label="Ayuda", menu=ay)
        self.config(menu=m)

    # NOTA: no se llama _bind() — eso pisa a tkinter.Misc._bind() y revienta
    def _bind_events(self):
        self.bind_all("<F5>", lambda e: self.run())
        self.bind_all("<F9>", lambda e: self.debug())
        self.bind_all("<F10>", lambda e: self.dbg_step())
        self.bind_all("<F11>", lambda e: self.dbg_continue())
        self.bind_all("<Escape>", lambda e: self._escape())
        self.bind_all("<Control-n>", lambda e: self.new_file())
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-s>", lambda e: self.save_file())
        # buscar / reemplazar / ir a línea: en toda la ventana, y también
        # sobre el editor (el del widget va primero: así Ctrl+H no borra
        # carácteres y no se ejecuta dos veces)
        for tecla, fn in (("<Control-f>", lambda e: self._buscar_abrir(False)),
                          ("<Control-h>", lambda e: self._buscar_abrir(True)),
                          ("<Control-g>", lambda e: self._ir_a_linea()),
                          ("<F3>", lambda e: self._saltar(1)),
                          ("<Shift-F3>", lambda e: self._saltar(-1))):
            self.bind_all(tecla, fn)
            self.editor.bind(tecla, lambda e, f=fn: f(e) or "break", add="+")
        # deshacer/rehacer/seleccionar: solo donde se escribe (las entradas
        # de la barra de búsqueda se quedan con su propio comportamiento)
        self.editor.bind("<Control-z>", self._deshacer, add="+")
        self.editor.bind("<Control-y>", self._reher, add="+")
        self.editor.bind("<Control-Shift-z>", self._reher, add="+")
        self.editor.bind("<Control-a>", self._seleccionar_todo, add="+")
        self.bind_all("<Control-z>", lambda e: self._deshacer())
        self.bind_all("<Control-y>", lambda e: self._reher())
        self.bind_all("<Control-Shift-z>", lambda e: self._reher())
        # menú contextual del editor (como en Visual Studio Code)
        self.editor.bind("<Button-3>", self._menu_contexto, add="+")
        self.editor.bind("<<Modified>>", self._on_modified)
        for ev in ("<KeyRelease>", "<ButtonRelease-1>"):
            self.editor.bind(ev, lambda e: self._cursor(), add="+")
        self.protocol("WM_DELETE_WINDOW", self._quit)

    # ------------------------------------------------------------ scroll
    def _scrollbar(self, *a):
        self.editor.yview(*a)
        self.gutter.yview(*a)

    def _on_yscroll(self, first, last):
        self._sb.set(first, last)
        try:
            self.gutter.yview_moveto(float(first))
        except (ValueError, TypeError):
            pass

    # ------------------------------------------------------------ editor
    def set_source(self, text, path):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.file = path
        self.dirty = False
        self.err_line = None
        self.example_path = None
        self.bp.clear()
        self.editor.tag_remove("dbg", "1.0", "end")
        self._limpiar_resaltado()               # la búsqueda no sobrevive a otro archivo
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self._after_change()
        self._titulo()
        if getattr(self, "barra_visible", False):
            self._resaltar()

    def _on_modified(self, _evt=None):
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            if not self.dirty:
                self.dirty = True            # hay cambios sin guardar
                self._titulo()
            self._after_change()

    def _after_change(self):
        self._refresh_gutter()
        self._highlight()
        self._cursor()

    def _refresh_gutter(self):
        n = int(self.editor.index("end-1c").split(".")[0])
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", "\n".join(str(i) for i in range(1, n + 1)))
        self.gutter.configure(state="disabled")
        self.gutter.tag_configure("bad", background="#4a1d24", foreground="#ff9b9b")
        self.gutter.tag_configure("bp", background="#5e1b26", foreground="#ff6b6b")
        if self.err_line and self.err_line <= n:
            self.gutter.tag_add("bad", f"{self.err_line}.0", f"{self.err_line}.end")
        for linea in sorted(self.bp):
            if 1 <= linea <= n:
                self.gutter.tag_add("bp", f"{linea}.0", f"{linea}.end")
        self.gutter.yview_moveto(self.editor.yview()[0])

    def _highlight(self):
        ed = self.editor
        text = ed.get("1.0", "end-1c")
        for t in ("kw", "str", "num", "com", "op", "id"):
            ed.tag_remove(t, "1.0", "end")

        def mark(tag, a, b):
            if b > a:
                ed.tag_add(tag, f"1.0 + {a} chars", f"1.0 + {b} chars")

        i, n = 0, len(text)
        while i < n:
            c = text[i]
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                j = text.find("\n", i)
                j = n if j < 0 else j
                mark("com", i, j); i = j
            elif c == '"':
                j = i + 1
                while j < n and text[j] != '"' and text[j] != "\n":
                    if text[j] == "\\":
                        j += 1
                    j += 1
                j = min(j + 1, n)
                mark("str", i, j); i = j
            elif c.isdigit() or (c == "." and i + 1 < n and text[i + 1].isdigit()):
                j = i
                while j < n and (text[j].isdigit() or text[j] == "."):
                    j += 1
                mark("num", i, j); i = j
            elif c.isalpha() or c == "_":
                j = i
                while j < n and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                mark("kw" if text[i:j] in KW else "id", i, j); i = j
            elif c in OPERADORES:
                mark("op", i, i + 1); i += 1
            else:
                i += 1

    def _cursor(self):
        line, col = self.editor.index(tk.INSERT).split(".")
        self.lbl_pos.config(text=f"Ln {line}, Col {int(col) + 1}")
        self._titulo()

    def _titulo(self):
        name = Path(self.file).name if self.file else "programa.eco"
        self.title(f"eco IDE — {name}{' *' if self.dirty else ''}")

    def _goto_line(self, n):
        if not n:
            return
        self.editor.see(f"{n}.0")
        end = self.editor.index(f"{n}.end")
        self.editor.tag_remove("sel", "1.0", "end")
        self.editor.tag_add("sel", f"{n}.0", end)
        self.editor.focus_set()

    # ------------------------------------------------------------ ejecución
    def _pedir_entrada(self, pregunta):
        """Lo llama el hilo que ejecuta el programa: encola y espera la respuesta."""
        respuesta = queue.Queue(maxsize=1)
        self._cola_entradas.put((pregunta or "", respuesta))
        return respuesta.get()

    def _procesar_entradas(self):
        """Hilo principal: pinta los diálogos que llegan desde la ejecución."""
        try:
            pregunta, respuesta = self._cola_entradas.get_nowait()
        except queue.Empty:
            pass
        else:
            valor = simpledialog.askstring("eco — entrada", pregunta or "Escribe un valor:",
                                           parent=self)
            respuesta.put("" if valor is None else valor)
        self.after(60, self._procesar_entradas)

    def run(self):
        if self.busy:
            return
        self.busy = True
        self.btn_run.configure(state="disabled")
        self.btn_dbg.configure(state="disabled")
        self.lbl_state.config(text="⏳ ejecutando…", foreground=DIM)
        src = self.editor.get("1.0", "end-1c")
        threading.Thread(target=self._worker, args=(src,), daemon=True).start()

    def _worker(self, src):
        t0 = time.time()
        try:
            data = run_analysis(src, on_input=self._pedir_entrada,
                                filename=self.file or self.example_path)
        except Exception as e:                     # nunca dejamos morir el hilo
            data = {"output": "", "error": f"Error interno: {e!r}",
                    "phase": "run", "tokens": None, "ast": None, "runtime": runtime_name()}
        data["ms"] = (time.time() - t0) * 1000
        self.q.put(data)

    # ------------------------------------------------------ depuración (F9)
    def _gutter_click(self, evt):
        """Clic en los números de línea: marca o quita un punto de ruptura."""
        try:
            linea = int(self.gutter.index(f"@{evt.x},{evt.y}").split(".")[0])
        except (ValueError, TypeError, tk.TclError):
            return
        if linea in self.bp:
            self.bp.discard(linea)
        else:
            self.bp.add(linea)
        self._refresh_gutter()

    def debug(self):
        """F9: arranca la depuración y para en la primera instrucción."""
        if self.busy:
            return
        self.busy = True
        self.btn_run.configure(state="disabled")
        self.btn_dbg.configure(state="disabled")
        self.dbg_bar.pack(fill="x", before=self.body)
        self._dbg_activo = True
        self._dbg_modo = "step"
        self._dbg_primero = True
        self._dbg_tab_vista = False
        self._dbg_respuesta = None
        self.lbl_state.config(text="🐞 depurando… (F10 paso · F11 seguir · Esc parar)",
                              foreground=ACCENT)
        self.lbl_dbg.config(text="⏸ arrancando…")
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.configure(state="disabled")
        src = self.editor.get("1.0", "end-1c")
        threading.Thread(target=self._worker_debug, args=(src,), daemon=True).start()

    def _worker_debug(self, src):
        t0 = time.time()
        try:
            data = run_analysis(src, on_input=self._pedir_entrada,
                                filename=self.file or self.example_path,
                                debug=True, on_debug=self._dbg_cb)
        except Exception as e:
            data = {"output": "", "error": f"Error interno: {e!r}",
                    "phase": "run", "tokens": None, "ast": None,
                    "runtime": runtime_name(), "detenido": None}
        data["ms"] = (time.time() - t0) * 1000
        data["_debug"] = True
        self.q.put(data)

    def _dbg_cb(self, linea, variables):
        """Hilo de ejecución: entrega cada instrucción al hilo de Tk y espera.

        Si no hay que parar (modo "seguir" y sin punto de ruptura) contesta
        aquí mismo, sin pasar por Tk: si no, un bucle largo se quedaría
        esperando al refresco de la interfaz (60 ms por instrucción).
        """
        if self._dbg_modo == "stop":
            return "stop"
        if self._dbg_modo == "continue" and not self._dbg_primero \
                and linea not in self.bp:
            return "continue"
        respuesta = queue.Queue(maxsize=1)
        self._cola_debug.put((linea, variables or {}, respuesta))
        return respuesta.get()

    def _procesar_debug(self):
        """Hilo principal: pinta el paso y espera a F10 / F11 / Esc."""
        if self._dbg_activo:
            try:
                linea, variables, respuesta = self._cola_debug.get_nowait()
            except queue.Empty:
                pass
            else:
                if self._dbg_modo == "stop":
                    respuesta.put("stop")
                elif self._dbg_primero or self._dbg_modo != "continue" \
                        or linea in self.bp:
                    self._dbg_primero = False
                    self._dbg_modo = "step"
                    self._dbg_respuesta = respuesta
                    self._mostrar_paso(linea, variables)
                else:
                    respuesta.put("continue")
        self.after(60, self._procesar_debug)

    def _mostrar_paso(self, linea, variables):
        """Resalta la línea, rellena la pestaña Variables y actualiza el estado."""
        try:
            n = int(linea)
        except (TypeError, ValueError):
            n = None
        self.editor.tag_remove("dbg", "1.0", "end")
        if n:
            self.editor.tag_add("dbg", f"{n}.0", f"{n}.end")
            self.editor.see(f"{n}.0")
            self.lbl_state.config(text=f"⏸ depurando · línea {n}", foreground=ACCENT)
        self.lbl_dbg.config(text="⏸ F10 paso · F11 seguir · Esc parar")

        self.tree_var.delete(*self.tree_var.get_children())
        for k, v in (variables or {}).items():
            self.tree_var.insert("", "end", text=k, values=(v,))
        if not variables:
            self.tree_var.insert("", "end", text="—", values=("sin variables",))
        if not self._dbg_tab_vista:
            self.nb.select(3)                     # pestaña "Variables"
            self._dbg_tab_vista = True

    def dbg_step(self):
        """F10: avanza una instrucción y vuelve a parar."""
        if not self._dbg_activo:
            return
        self._dbg_modo = "step"
        self._responder("step")

    def dbg_continue(self):
        """F11: sigue hasta el próximo punto de ruptura (o el final)."""
        if not self._dbg_activo:
            return
        self._dbg_modo = "continue"
        self.lbl_dbg.config(text="▶ continuando…")
        self._responder("continue")

    def dbg_stop(self):
        """Esc: detiene la depuración."""
        if not self._dbg_activo:
            return
        self._dbg_modo = "stop"
        self.lbl_dbg.config(text="■ deteniendo…")
        self._responder("stop")

    def _responder(self, accion):
        respuesta, self._dbg_respuesta = self._dbg_respuesta, None
        if respuesta is not None:
            respuesta.put(accion)

    def _fin_debug(self, detenido=None):
        self._dbg_activo = False
        self._dbg_modo = "step"
        if self._dbg_respuesta is not None:            # no dejamos al hilo colgado
            self._dbg_respuesta.put("stop")
        self._dbg_respuesta = None
        self.dbg_bar.pack_forget()
        self.btn_run.configure(state="normal")
        self.btn_dbg.configure(state="normal")
        if not detenido:                          # si se paró, la línea se queda
            self.editor.tag_remove("dbg", "1.0", "end")
        while True:                               # descarta pasos huérfanos
            try:
                self._cola_debug.get_nowait()
            except queue.Empty:
                break

    def _poll(self):
        try:
            data = self.q.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.btn_run.configure(state="normal")
            self.btn_dbg.configure(state="normal")
            self._show_result(data)
        self.after(80, self._poll)

    def _show_result(self, d):
        if self._dbg_activo:
            self._fin_debug(d.get("detenido"))

        # ---------- salida ----------
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        if d.get("error"):
            self.out.insert("end", f" [{FASE.get(d['phase'], 'error')}] ", "tag")
            self.out.insert("end", d["error"] + "\n", "err")
            if d.get("output"):
                self.out.insert("end", "\n— salida parcial —\n", "tag")
                self.out.insert("end", d["output"])
        else:
            self.out.insert("end", d.get("output") or "(sin salida)\n")
        self.out.configure(state="disabled")

        # ---------- marcador de error + estado ----------
        import re
        m = re.search(r"\[línea (\d+)", d.get("error") or "")
        self.err_line = int(m.group(1)) if m else None
        self._refresh_gutter()

        if d.get("error"):
            self.lbl_state.config(
                text=f"✕ error en el {FASE.get(d['phase'], '?')}", foreground=BAD)
            self.nb.select(0)
            if self.err_line:
                self._goto_line(self.err_line)
        else:
            n = len([l for l in (d.get("output") or "").splitlines() if l.strip()])
            if d.get("detenido"):
                self.lbl_state.config(
                    text=f"⏸ depuración detenida en la línea {d['detenido']} · "
                         f"{d['ms']:.0f} ms", foreground=ACCENT)
            else:
                self.lbl_state.config(text=f"✓ OK · {n} línea(s) de salida · "
                                           f"{d['ms']:.0f} ms", foreground=OK)

        # ---------- tokens ----------
        self.tree.delete(*self.tree.get_children())
        for t in d.get("tokens") or []:
            self.tree.insert("", "end",
                             text=str(t["type"]),
                             values=(("" if t["value"] is None else t["value"]),
                                     f"{t['line']}:{t['col']}"))
        if not d.get("tokens"):
            self.tree.insert("", "end", text="—", values=("no se generaron tokens", ""))

        # ---------- AST ----------
        self.ast.configure(state="normal")
        self.ast.delete("1.0", "end")
        self.ast.insert("1.0", json.dumps(d.get("ast"), indent=2, ensure_ascii=False)
                        if d.get("ast") else "(no hay AST: el análisis falló)")
        self.ast.configure(state="disabled")

        # ---------- runtime ----------
        rt = d.get("runtime") or runtime_name()
        self.lbl_rt.config(text=f"runtime: {rt}")

    def clear_console(self):
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("end", "(consola vacía)")
        self.out.configure(state="disabled")
        self.lbl_state.config(text="Listo", foreground=DIM)

    # ------------------------------------------------------------ archivos
    def _preguntar_guardar(self, accion: str) -> str:
        """Modal clásico '¿Guardar los cambios?'.

        Devuelve "guardar", "descartar" o "cancelar".
        """
        nombre = Path(self.file).name if self.file else "programa.eco"
        res = {"r": "cancelar"}

        dlg = tk.Toplevel(self)
        dlg.title("Cambios sin guardar")
        dlg.transient(self)                    # se asienta sobre la ventana principal
        dlg.resizable(False, False)

        caja = ttk.Frame(dlg, padding=(18, 16, 18, 14))
        caja.pack(fill="both", expand=True)

        fila = ttk.Frame(caja)
        fila.pack(fill="x")
        ttk.Label(fila, text="⚠", font=("Segoe UI Symbol", 20),
                  foreground="#ffc66d").pack(side="left", padx=(0, 12))
        col = ttk.Frame(fila)
        col.pack(side="left", fill="x", expand=True)
        ttk.Label(col, text=f"Tienes cambios sin guardar en «{nombre}».",
                  font=("Segoe UI", 10, "bold"), foreground=FG).pack(anchor="w")
        ttk.Label(col, text=f"¿Guardarlos antes de {accion}?",
                  foreground=DIM).pack(anchor="w", pady=(3, 0))

        pie = ttk.Frame(caja)
        pie.pack(fill="x", pady=(18, 0))

        def cerrar(r):
            res["r"] = r
            dlg.destroy()

        b_guardar = ttk.Button(pie, text="Guardar", style="Run.TButton",
                               command=lambda: cerrar("guardar"))
        b_guardar.pack(side="left")
        ttk.Button(pie, text="Descartar",
                   command=lambda: cerrar("descartar")).pack(side="left", padx=8)
        ttk.Button(pie, text="Cancelar",
                   command=lambda: cerrar("cancelar")).pack(side="right")

        dlg.protocol("WM_DELETE_WINDOW", lambda: cerrar("cancelar"))
        dlg.bind("<Return>", lambda e: cerrar("guardar"))
        dlg.bind("<Escape>", lambda e: cerrar("cancelar"))

        dlg.update_idletasks()                 # centrada sobre el IDE
        x = self.winfo_rootx() + max((self.winfo_width() - dlg.winfo_reqwidth()) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - dlg.winfo_reqheight()) // 3, 0)
        dlg.geometry(f"+{x}+{y}")

        dlg.deiconify()
        b_guardar.focus_set()
        dlg.grab_set()                         # modal: lo de fuera no responde
        self.wait_window(dlg)
        return res["r"]

    def _confirm(self, accion: str = "continuar") -> bool:
        """True si se puede seguir; False si el usuario canceló.

        Con cambios sin guardar abre el modal Guardar / Descartar / Cancelar.
        """
        if not self.dirty:
            return True
        r = self._preguntar_guardar(accion)
        if r == "guardar":
            return self.save_file()            # si cancela el "Guardar como", cancela
        return r == "descartar"

    def new_file(self):
        if not self._confirm("crear un archivo nuevo"):
            return
        self.set_source("", None)

    def open_file(self):
        if not self._confirm("abrir otro archivo"):
            return
        path = filedialog.askopenfilename(
            filetypes=[("Programas eco", "*.eco"), ("Texto", "*.txt"), ("Todos", "*.*")])
        if not path:
            return
        try:
            self.set_source(Path(path).read_text(encoding="utf-8"), path)
        except OSError as e:
            messagebox.showerror("No se pudo abrir", str(e))

    def save_file(self) -> bool:
        if self.file:
            return self._write(self.file)
        return self.save_file_as()

    def save_file_as(self) -> bool:
        path = filedialog.asksaveasfilename(defaultextension=".eco",
                                            initialfile=Path(self.file).name if self.file
                                            else "programa.eco",
                                            filetypes=[("Programas eco", "*.eco")])
        if not path:
            return False
        return self._write(path)

    def _write(self, path) -> bool:
        try:
            Path(path).write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
            self.file = path
            self.dirty = False
            self.lbl_state.config(text=f"Guardado: {Path(path).name}", foreground=OK)
            self._cursor()                      # refresca el título (quita el *)
            return True
        except OSError as e:
            messagebox.showerror("No se pudo guardar", str(e))
            return False

    # ------------------------------------------- buscar, deshacer y menú
    def _crear_barra_buscar(self, padre):
        """Barra de buscar/reemplazar (Ctrl+F / Ctrl+H). No se empaqueta hasta
        que se pide: así no ocupa sitio mientras escribes."""
        self.barra = ttk.Frame(padre, padding=(8, 6))
        self.barra_visible = False
        self._coincidencias = []
        self._idx = -1

        fila1 = ttk.Frame(self.barra)
        fila1.pack(fill="x")
        ttk.Label(fila1, text="🔍").pack(side="left")
        self.ent_buscar = ttk.Entry(fila1, width=26)
        self.ent_buscar.pack(side="left", padx=(6, 6))
        self.lbl_cont = ttk.Label(fila1, text="0/0", width=8, style="Dbg.TLabel")
        self.lbl_cont.pack(side="left")
        ttk.Button(fila1, text="◀", width=3,
                   command=lambda: self._saltar(-1)).pack(side="left", padx=(6, 0))
        ttk.Button(fila1, text="▶", width=3,
                   command=lambda: self._saltar(1)).pack(side="left", padx=(2, 0))
        self.var_aa = tk.BooleanVar(value=False)          # "Aa" = distinguir mayúsculas
        ttk.Checkbutton(fila1, text="Aa", variable=self.var_aa,
                        command=self._resaltar).pack(side="left", padx=(10, 0))
        ttk.Button(fila1, text="✕", width=3,
                   command=self._buscar_cerrar).pack(side="right")

        fila2 = ttk.Frame(self.barra)                     # solo con Ctrl+H
        self.fila_reemplazo = fila2
        ttk.Label(fila2, text="Cambiar por").pack(side="left")
        self.ent_reemplazar = ttk.Entry(fila2, width=26)
        self.ent_reemplazar.pack(side="left", padx=(6, 6))
        ttk.Button(fila2, text="Reemplazar",
                   command=self._reemplazar_uno).pack(side="left")
        ttk.Button(fila2, text="Todo", command=self._reemplazar_todo).pack(
            side="left", padx=(4, 0))

        self.ent_buscar.bind("<KeyRelease>", lambda e: self._resaltar())
        self.ent_buscar.bind("<Return>", self._enter_buscar)
        self.ent_buscar.bind("<Shift-Return>", self._enter_buscar_inverso)
        self.ent_reemplazar.bind("<Return>", self._enter_reemplazar)
        # Ctrl+H dentro de una caja: Tk lo toma como retroceso y borra una
        # letra; aquí solo debe abrir la fila de reemplazo.
        for ent in (self.ent_buscar, self.ent_reemplazar):
            ent.bind("<Control-h>", self._abrir_reemplazar, add="+")

    def _abrir_reemplazar(self, _evt=None):
        self._buscar_abrir(True)
        return "break"

    def _buscar_abrir(self, con_reemplazo=False, _evt=None):
        recien_abierta = not self.barra_visible
        if recien_abierta:
            self.barra.pack(side="top", fill="x", before=self.gutter)
            self.barra_visible = True
        if con_reemplazo:
            self.fila_reemplazo.pack(fill="x", pady=(6, 0))
        else:
            self.fila_reemplazo.pack_forget()
        if recien_abierta:                           # solo al abrir: si no,
            sel = self.editor.tag_ranges("sel")      # se comería lo que llevas
            if sel:                                  # escrito en la caja
                texto = self.editor.get(sel[0], sel[1])
                if texto and "\n" not in texto:
                    self.ent_buscar.delete(0, "end")
                    self.ent_buscar.insert(0, texto)
        self.ent_buscar.focus_set()
        self.ent_buscar.selection_range(0, "end")
        self._resaltar()

    def _buscar_cerrar(self, _evt=None):
        if self.barra_visible:
            self.barra.pack_forget()
            self.barra_visible = False
        self._limpiar_resaltado()
        self.editor.focus_set()
        return "break"

    def _escape(self, _evt=None):
        """Esc cierra la barra si está abierta; si no, detiene la depuración."""
        if getattr(self, "barra_visible", False):
            return self._buscar_cerrar()
        self.dbg_stop()

    def _calcular_coincidencias(self) -> list:
        """Offsets (desde el inicio) de cada coincidencia de la búsqueda."""
        texto = self.editor.get("1.0", "end-1c")
        patron = self.ent_buscar.get()
        self._coincidencias = []
        if not patron:
            return self._coincidencias
        if not self.var_aa.get():
            texto, patron = texto.lower(), patron.lower()
        i = texto.find(patron)
        while i != -1:
            self._coincidencias.append(i)
            i = texto.find(patron, i + len(patron))
        return self._coincidencias

    def _resaltar(self, _evt=None):
        """Recalcula y pinta las coincidencias (al escribir o al editar)."""
        antes = self._idx
        self._calcular_coincidencias()
        if not self._coincidencias:
            self._idx = -1
        elif antes < 0 or antes >= len(self._coincidencias):
            desde = len(self.editor.get("1.0", self.editor.index("insert")))
            self._idx = next((k for k, o in enumerate(self._coincidencias)
                              if o >= desde), 0)
        self._pintar()

    def _pintar(self):
        self._limpiar_resaltado()
        n = len(self._coincidencias)
        if not n:
            self.lbl_cont.config(text="0/0", foreground=BAD)
            return
        largo = len(self.ent_buscar.get())
        for k, off in enumerate(self._coincidencias):
            ini = self.editor.index(f"1.0 + {off} chars")
            fin = self.editor.index(f"1.0 + {off + largo} chars")
            if k == self._idx:
                self.editor.tag_add("buscar_actual", ini, fin)
                self.editor.see(ini)
            self.editor.tag_add("buscar", ini, fin)
        self.lbl_cont.config(text=f"{self._idx + 1}/{n}", foreground=ACCENT)

    def _limpiar_resaltado(self):
        self.editor.tag_remove("buscar", "1.0", "end")
        self.editor.tag_remove("buscar_actual", "1.0", "end")

    def _saltar(self, direccion, _evt=None):
        """1 = siguiente coincidencia, -1 = anterior (F3 / Shift+F3)."""
        if not self.barra_visible:
            if not self.ent_buscar.get():
                return
            self._buscar_abrir(False)                   # F3 sin barra: la abre
            return
        self._calcular_coincidencias()
        n = len(self._coincidencias)
        if not n:
            self._idx = -1
            self._pintar()
            return
        if self._idx < 0 or self._idx >= n:
            self._idx = 0 if direccion > 0 else n - 1
        else:
            self._idx = (self._idx + direccion) % n
        self._pintar()

    def _enter_buscar(self, _evt):
        self._saltar(1)
        return "break"

    def _enter_buscar_inverso(self, _evt):
        self._saltar(-1)
        return "break"

    def _enter_reemplazar(self, _evt):
        self._reemplazar_uno()
        return "break"

    def _reemplazar_uno(self):
        if not self._coincidencias or self._idx < 0 \
                or self._idx >= len(self._coincidencias):
            self._resaltar()
        if self._idx < 0 or self._idx >= len(self._coincidencias):
            return
        largo = len(self.ent_buscar.get())
        if not largo:
            return
        off = self._coincidencias[self._idx]
        ini = self.editor.index(f"1.0 + {off} chars")
        fin = self.editor.index(f"1.0 + {off + largo} chars")
        nuevo = self.ent_reemplazar.get()
        self.editor.edit_separator()
        self.editor.delete(ini, fin)
        self.editor.insert(ini, nuevo)
        self.editor.edit_separator()
        self.editor.mark_set("insert", f"{ini} + {len(nuevo)} chars")
        self.editor.see("insert")
        self._resaltar()                                # recalcula y marca la siguiente

    def _reemplazar_todo(self):
        coins = self._calcular_coincidencias()
        largo = len(self.ent_buscar.get())
        if not coins or not largo:
            return
        nuevo = self.ent_reemplazar.get()
        self.editor.edit_separator()
        for off in reversed(coins):                     # de atrás adelante: no se mueven
            ini = self.editor.index(f"1.0 + {off} chars")
            fin = self.editor.index(f"1.0 + {off + largo} chars")
            self.editor.delete(ini, fin)
            self.editor.insert(ini, nuevo)
        self.editor.edit_separator()
        self.lbl_state.config(text=f"Reemplazados: {len(coins)}", foreground=OK)
        self._resaltar()

    def _deshacer(self, _evt=None):
        if isinstance(self.focus_get(), (ttk.Entry, tk.Entry)):
            return None                     # las entradas se quedan con lo suyo
        try:
            self.editor.edit_undo()
        except tk.TclError:
            self.editor.bell()              # no hay nada que deshacer
        self._after_change()                # por si <<Modified>> no saltó
        return "break"

    def _reher(self, _evt=None):
        if isinstance(self.focus_get(), (ttk.Entry, tk.Entry)):
            return None
        try:
            self.editor.edit_redo()
        except tk.TclError:
            self.editor.bell()
        self._after_change()
        return "break"

    def _seleccionar_todo(self, _evt=None):
        self.editor.tag_add("sel", "1.0", "end-1c")
        self.editor.focus_set()
        return "break"

    def _ir_a_linea(self, _evt=None):
        ultima = int(self.editor.index("end-1c").split(".")[0])
        n = simpledialog.askinteger("Ir a la línea", f"Línea (1-{ultima}):",
                                    parent=self, minvalue=1, maxvalue=ultima)
        if n:
            self._goto_line(n)
        return "break"

    def _editar(self, evento):
        self.editor.focus_set()
        self.editor.event_generate(evento)              # <<Cut>> <<Copy>> <<Paste>>

    def _borrar_sel(self):
        self.editor.delete("sel.first", "sel.last")

    def _menu_contexto(self, evt):
        """Clic derecho en el editor: las opciones de siempre con su atajo."""
        hay_sel = bool(self.editor.tag_ranges("sel"))
        estado = "normal" if hay_sel else "disabled"
        m = tk.Menu(self, tearoff=0, bg=PANEL2, fg=FG, activebackground="#2b3f66",
                    activeforeground=FG, disabledforeground=DIM,
                    font=("Segoe UI", 9), borderwidth=1, relief="solid")
        m.add_command(label="Deshacer (Ctrl+Z)", command=self._deshacer)
        m.add_command(label="Rehacer (Ctrl+Y)", command=self._reher)
        m.add_separator()
        m.add_command(label="Cortar (Ctrl+X)", command=lambda: self._editar("<<Cut>>"),
                      state=estado)
        m.add_command(label="Copiar (Ctrl+C)", command=lambda: self._editar("<<Copy>>"),
                      state=estado)
        m.add_command(label="Pegar (Ctrl+V)", command=lambda: self._editar("<<Paste>>"))
        m.add_command(label="Borrar (Supr)", command=self._borrar_sel, state=estado)
        m.add_separator()
        m.add_command(label="Seleccionar todo (Ctrl+A)", command=self._seleccionar_todo)
        m.add_separator()
        m.add_command(label="Buscar (Ctrl+F)", command=lambda: self._buscar_abrir(False))
        m.add_command(label="Reemplazar (Ctrl+H)",
                      command=lambda: self._buscar_abrir(True))
        m.add_command(label="Ir a la línea (Ctrl+G)", command=self._ir_a_linea)
        try:
            m.tk_popup(evt.x_root, evt.y_root)
        finally:
            m.grab_release()
        return "break"

    # ------------------------------------------------------------ varios
    def _load_example(self, _evt=None):
        name = self.cmb_ex.get()
        src = self.examples.get(name)
        if src is None:
            return
        if not self._confirm("cargar el ejemplo"):
            self.cmb_ex.set("— elegir —")
            return
        self.set_source(src, None)
        d = examples_dir()
        if d and (d / name).is_file():
            self.example_path = str(d / name)     # para que `importar "…"` funcione
        self.cmb_ex.set("— elegir —")
        self._cursor()

    def _load_examples(self):
        d = examples_dir()
        if not d:
            return
        for f in sorted(d.glob("*.eco")):
            try:
                self.examples[f.name] = f.read_text(encoding="utf-8")
            except OSError:
                continue
        if self.examples:
            self.cmb_ex.configure(values=["— elegir —"] + sorted(self.examples))

    def _refresh_runtime(self):
        self._load_examples()
        rt = runtime_name()
        self.lbl_rt.config(text=f"runtime: {rt}")

    def _about(self):
        messagebox.showinfo(
            "Acerca de eco IDE",
            f"eco IDE v{VERSION}\n\n"
            "Lenguaje de programación propio con lexer, parser y evaluador.\n"
            f"Runtime: {runtime_name()}\n\n"
            "Atajos: F5 ejecutar · F9 depurar · F10 paso · F11 seguir · Esc para\n"
            "Ctrl+N nuevo · Ctrl+O abrir · Ctrl+S guardar")

    def _quit(self):
        if self._confirm("cerrar el IDE"):
            self.destroy()


def main():
    if any(a in sys.argv for a in ("-v", "--version")):
        print(VERSION)
        return 0
    app = Ide()
    if len(sys.argv) > 1:                     # doble clic en un .eco
        path = Path(sys.argv[1])
        if path.is_file():
            try:
                app.set_source(path.read_text(encoding="utf-8"), str(path))
                app._cursor()
            except OSError:
                pass
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
