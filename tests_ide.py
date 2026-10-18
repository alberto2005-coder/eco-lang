"""Tests del IDE de escritorio: editor (deshacer, buscar/reemplazar, Ctrl+A),
menú contextual y el modal de "cambios sin guardar".

Se ejecutan con:  py tests_ide.py
(enseña la ventana del IDE un par de segundos y la cierra sola)
"""
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
import tkinter as tk
import tkinter.ttk as ttk

import ide


def ver(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  ok  {msg}")


app = ide.Ide()
app.deiconify()
app.update()              # con la ventana oculta Tk no acepta el foco y los
ed = app.editor           # eventos de tecla (Ctrl+A…) no llegan al editor

# ---------------------------------------------------- 1) Ctrl+Z / Ctrl+Y
app.set_source("hola", None)
ed.insert("end", " mundo")
app.update()
ed.focus_set()
ed.event_generate("<Control-z>")
app.update()
ver(ed.get("1.0", "end-1c") == "hola", f"Ctrl+Z deshace -> {ed.get('1.0', 'end-1c')!r}")
ed.event_generate("<Control-y>")
app.update()
ver(ed.get("1.0", "end-1c") == "hola mundo",
    f"Ctrl+Y rehace -> {ed.get('1.0', 'end-1c')!r}")
app._deshacer()           # no debe reventar
app._reher()
ver(True, "deshacer/rehacer sin historial no revienta")

# ---------------------------------------------------- 2) Ctrl+F: buscar
app.set_source("escribe 1;\nescribe 2;\nESCRIBE 3;\nvariable x = escribe;", None)
ed.focus_set()
ed.event_generate("<Control-f>")
app.update()
ver(app.barra_visible, "Ctrl+F abre la barra")
ver(app.fila_reemplazo.winfo_manager() != "pack", "Ctrl+F no muestra la fila de reemplazo")
ver(app.ent_buscar.get() == "", "con el cursor sin selección empieza vacía")
app.ent_buscar.delete(0, "end")
app.ent_buscar.insert(0, "escribe")
app._resaltar()
cont = app.lbl_cont.cget("text")
ver(cont == "1/4", f"contador sin 'Aa' (insensible: escribe + ESCRIBE): {cont}")
ver(bool(ed.tag_ranges("buscar")), "las coincidencias quedan resaltadas")
ver(bool(ed.tag_ranges("buscar_actual")), "hay una coincidencia actual marcada")
app._saltar(1)
ver(app.lbl_cont.cget("text") == "2/4", "F3/▶ avanza a la 2/4")
app._saltar(-1)
ver(app.lbl_cont.cget("text") == "1/4", "Shift+F3/◀ vuelve a la 1/4")
app.var_aa.set(True)
app._resaltar()
ver(app.lbl_cont.cget("text") == "1/3", "con 'Aa' distingue mayúsculas: 3")
app.var_aa.set(False)
app._resaltar()

# ------------------------------------------- 3) Ctrl+H: buscar y reemplazar
ed.event_generate("<Control-h>")
app.update()
ver(app.barra_visible and app.fila_reemplazo.winfo_manager() == "pack",
    "Ctrl+H abre la barra con la fila de reemplazo")
# regresión: dentro de la caja, Ctrl+H no debe borrar una letra (Tk lo toma
# como retroceso) y aún así abre la fila de reemplazo
app.ent_buscar.delete(0, "end")
app.ent_buscar.insert(0, "escribe")
app.ent_buscar.focus_set()
app.ent_buscar.event_generate("<Control-h>")
app.update()
ver(app.ent_buscar.get() == "escribe",
    f"Ctrl+H en la caja no borra caracteres (queda {app.ent_buscar.get()!r})")
ver(app.fila_reemplazo.winfo_manager() == "pack", "y la fila de reemplazo sigue abierta")
app.ent_reemplazar.delete(0, "end")
app.ent_reemplazar.insert(0, "imprime")
app._reemplazar_todo()
texto = ed.get("1.0", "end-1c")
ver(texto.splitlines()[0] == "imprime 1;",
    f"la 1ª línea queda limpia: {texto.splitlines()[0]!r}")
ver("escribe" not in texto and texto.count("imprime") == 4,
    f"reemplazar todo -> {texto.splitlines()[0]!r} (+{texto.count('imprime')} en total)")
ver(app.lbl_cont.cget("text") == "0/0", "contador a 0/0 tras reemplazar todo")
app._reemplazar_uno()      # sin coincidencias: no debe reventar
ver(True, "reemplazar sin coincidencias no revienta")

# ------------------------------------------------------ 4) Esc cierra la barra
app._escape()
app.update()
ver(not app.barra_visible, "Esc cierra la barra")
ver(not ed.tag_ranges("buscar"), "Esc borra los resaltados")
app._saltar(1)             # F3 con la barra cerrada: la reabre con el último término
ver(app.barra_visible, "F3 reabre la barra con el término anterior")
app._escape()
app.ent_buscar.delete(0, "end")
app._saltar(1)             # y sin término no hace nada
ver(not app.barra_visible, "F3 sin barra y sin término no la abre")

# ------------------------------------------------------ 5) Ctrl+A selecciona
ed.tag_remove("sel", "1.0", "end")
ed.event_generate("<Control-a>")
app.update()
ver(bool(ed.tag_ranges("sel")), "Ctrl+A selecciona todo")

# ------------------------------------------------------ 6) menú contextual
capturado = {}


class MenuFalso:
    def __init__(self, *a, **k):
        self.items = []

    def add_command(self, label=None, **k):
        self.items.append((label, k.get("state", "normal")))

    def add_separator(self):
        self.items.append(("---", None))

    def tk_popup(self, x, y):
        capturado["m"] = self

    def grab_release(self):
        pass


ed.tag_remove("sel", "1.0", "end")           # sin selección
real = ide.tk.Menu
ide.tk.Menu = MenuFalso
try:
    app._menu_contexto(type("Evt", (), {"x_root": 8, "y_root": 8})())
    sin_sel = [i for i in capturado["m"].items if i[0] != "---"]
    ed.tag_add("sel", "1.0", "1.6")           # con selección
    app._menu_contexto(type("Evt", (), {"x_root": 8, "y_root": 8})())
    con_sel = [i for i in capturado["m"].items if i[0] != "---"]
finally:
    ide.tk.Menu = real

esperadas = ["Deshacer (Ctrl+Z)", "Rehacer (Ctrl+Y)", "Cortar (Ctrl+X)",
             "Copiar (Ctrl+C)", "Pegar (Ctrl+V)", "Borrar (Supr)",
             "Seleccionar todo (Ctrl+A)", "Buscar (Ctrl+F)",
             "Reemplazar (Ctrl+H)", "Ir a la línea (Ctrl+G)"]
faltan = [e for e in esperadas if e not in [i[0] for i in sin_sel]]
ver(not faltan, f"el menú tiene las 10 opciones con su atajo (faltan: {faltan})")
estado = dict(sin_sel)
ver(estado["Cortar (Ctrl+X)"] == "disabled" and estado["Copiar (Ctrl+C)"] == "disabled",
    "sin selección: Cortar/Copiar/Borrar deshabilitados")
estado = dict(con_sel)
ver(estado["Cortar (Ctrl+X)"] == "normal" and estado["Borrar (Supr)"] == "normal",
    "con selección: Cortar/Copiar/Borrar activos")
print("  menú:", " | ".join(i[0] for i in sin_sel))

app.set_source("escribe 'fin';", None)
ver(not ed.tag_ranges("buscar"), "cargar archivo limpia la búsqueda")

# ======================================= modal de cambios sin guardar
problemas = []


def _botones(w):
    out = []
    for h in w.winfo_children():
        if isinstance(h, ttk.Button):
            out.append(h)
        out.extend(_botones(h))
    return out


def _dialogo():
    for w in app.winfo_children():
        if isinstance(w, tk.Toplevel) and w.title() == "Cambios sin guardar":
            return w
    return None


def pulsar(accion, retardo=250):
    """A los 250 ms pulsa `accion` en el modal (si aparece)."""
    def buscar():
        dlg = _dialogo()
        if dlg is None:
            problemas.append(f"no apareció el modal (quería «{accion}»)")
            return
        for b in _botones(dlg):
            if b.cget("text") == accion:
                b.invoke()
                return
        problemas.append(f"no encontré el botón «{accion}»")
    app.after(retardo, buscar)


tmp = Path(tempfile.mkdtemp(prefix="eco_modal_")) / "prueba.eco"
buffer = lambda: ed.get("1.0", "end-1c")

# 1) escribir marca cambios sin guardar
ed.insert("1.0", "escribe 1;")
app.update()
ver(app.dirty and app.title().endswith("*"),
    f"escribir marca dirty y el título con * -> {app.title()!r}")

# 2) Cancelar deja todo como estaba
pulsar("Cancelar")
app.new_file()
app.update()
ver(app.dirty and "escribe" in buffer(), "Cancelar no toca nada")

# 3) Descartar limpia el editor
pulsar("Descartar")
app.new_file()
app.update()
ver(not app.dirty and buffer() == "", "Descartar limpia el editor")

# 4) Guardar escribe en disco (sin pasar por el diálogo "Guardar como")
app.file = str(tmp)
ed.insert("1.0", "variable x = 7;")
app.update()
pulsar("Guardar")
app.new_file()
app.update()
ver(tmp.read_text(encoding="utf-8") == "variable x = 7;", "Guardar escribe el archivo")
ver(not app.dirty and "*" not in app.title(), "y quita el * del título")

# 5) al cerrar, Cancelar no cierra
ed.insert("1.0", "escribe 2;")
app.update()
pulsar("Cancelar")
app._quit()
app.update()
try:
    app.winfo_exists()
    sigue = True
except tk.TclError:
    sigue = False
ver(sigue and app.dirty, "cerrar + Cancelar deja el IDE abierto")

# 6) al cerrar, Descartar cierra
pulsar("Descartar")
app._quit()
try:
    app.winfo_exists()
    cerro = False
except tk.TclError:
    cerro = True
ver(cerro, "cerrar + Descartar cierra el IDE")
ver(not problemas, f"el modal respondió en todos los intentos {problemas}")

print("resultado: OK")
