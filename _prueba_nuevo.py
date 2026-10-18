"""Prueba rápida de las funciones nuevas (borrar al terminar)."""
import sys, tempfile, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime import analyze, run_analysis

def check(nombre, src, esperado=None, archivo=None, con_error=False):
    d = analyze(src, filename=archivo)
    if con_error:                      # este caso DEBE fallar con un error claro
        ok = bool(d["error"])
        print(("OK  " if ok else "FALLO ") + nombre + (" (esperado)" if ok else ""))
        if not ok:
            print("   debía fallar y no lo hizo; salida:", repr(d["output"]))
        return
    ok = not d["error"]
    if esperado is not None:
        ok = ok and d["output"].strip() == esperado
    print(("OK  " if ok else "FALLO ") + nombre)
    if not ok:
        print("   error:", d["error"])
        print("   salida:", repr(d["output"]))

# --- bucles compactos ---
check("si sin parentesis", 'si verdadero { escribe "a"; } sino { escribe "b"; }', "a")
check("si sin parentesis (falso)", 'si falso { escribe "a"; } sino si verdadero { escribe "c"; }', "c")
check("mientras sin parentesis", 'variable i = 0; mientras i < 3 { i++; } escribe i;', "3")
check("mientras con parentesis", 'variable i = 0; mientras (i < 3) { i = i + 1; } escribe i;', "3")
check("para con i++", 'variable s = 0; para (variable i = 0; i < 5; i++) { s = s + i; } escribe s;', "10")
check("i--", 'variable i = 5; i--; i--; escribe i;', "3")
check("resta - -1 sigue funcionando", 'escribe 1 - -1;', "2")
check("parentesis de agrupamiento", 'si (2 + 3) == 5 { escribe "ok"; }', "ok")

# --- metodos ---
check("texto", 'escribe "hola".mayusculas();', "HOLA")
check("cadena", 'escribe "  hola ".recortar().mayusculas();', "HOLA")
check("texto metod()", 'escribe "a,b,c".partir(",");', '["a", "b", "c"]')
check("lista", 'variable l = [3,1,2]; l.ordenar(); escribe l;', "[1, 2, 3]")
check("lista cadena", 'variable l = [1]; l.agregar(2).agregar(3); escribe l;', "[1, 2, 3]")
check("diccionario clave", 'variable p = {"nombre": "Ana"}; escribe p.nombre;', "Ana")
check("diccionario clave nueva", 'variable p = {}; p.nombre = "Ana"; escribe p["nombre"] + " " + p.nombre;', "Ana Ana")
check("diccionario metodos", 'variable p = {"a": 1}; escribe p.claves(); escribe p.longitud();', '["a"]\n1')
check("numero", 'escribe (3.7).redondear(); escribe (-8).absoluto();', "4\n8")
check("metodo en interpolacion", 'variable p = {"nombre": "Ana"}; escribe "Hola ${p.nombre.mayusculas()}";', "Hola ANA")
check("clave gana sobre metodo", 'variable d = {"longitud": 7}; escribe d.longitud;', "7")
check("error metodo inexistente", 'escribe "hola".pedo();', con_error=True)
check("error clave inexistente", 'variable p = {}; escribe p.nada;', con_error=True)
check("error asignar en texto", 'variable t = "x"; t.a = 1;', con_error=True)

# --- importar ---
carpeta = tempfile.mkdtemp()
with open(os.path.join(carpeta, "utilidades.eco"), "w", encoding="utf-8") as f:
    f.write('const PI = 3.14;\n'
            'funcion doble(n) { devuelve n * 2; }\n'
            'variable saludo = "hola desde el modulo";\n')
with open(os.path.join(carpeta, "principal.eco"), "w", encoding="utf-8") as f:
    f.write('importar "utilidades";\n'
            'escribe utilidades.doble(21);\n'
            'escribe utilidades.saludo;\n'
            'escribe utilidades.PI;\n'
            'importar "utilidades.eco" como u2;\n'
            'escribe u2.doble(2);\n')
check("importar archivo", 'importar "utilidades"; escribe utilidades.doble(4); escribe utilidades.saludo;',
      "8\nhola desde el modulo", archivo=os.path.join(carpeta, "main1.eco"))
check("importar como + relativo", open(os.path.join(carpeta, "principal.eco"), encoding="utf-8").read(),
      "42\nhola desde el modulo\n3.14\n4", archivo=os.path.join(carpeta, "principal.eco"))
check("error archivo inexistente", 'importar "no_existe.eco";',
      archivo=os.path.join(carpeta, "main2.eco"), con_error=True)

# --- depuracion paso a paso ---
pasos = []
def hook(linea, variables):
    pasos.append((linea, variables.get("i")))
    if len(pasos) >= 3:
        return "stop"
    return "step"

import interpreter
interpreter.set_debug_hook(__import__("runtime").crear_hook_debug(hook))
d = analyze('variable i = 0;\nmientras i < 5 {\n  i++;\n}\nescribe i;\n')
interpreter.set_debug_hook(None)
print(("OK  " if d["detenido"] and d["error"] is None else "FALLO ") + "depuracion paso a paso",
      "->", d["detenido"], pasos)

steps = {"n": 0}
def cb(l, v):
    steps["n"] += 1
    return "stop" if steps["n"] >= 3 else "step"
d2 = run_analysis('variable i = 0; i++; i++; escribe i;', debug=True, on_debug=cb)
print(("OK  " if d2.get("detenido") else "FALLO ") + "run_analysis debug ->", d2.get("detenido"))

# si on_debug siempre dice "step", el programa termina normal y NO hay que
# marcarlo como detenido (ese era el FALLO anterior: era una expectativa mala)
d3 = run_analysis('variable i = 0; i++; i++; escribe i;', debug=True,
                  on_debug=lambda l, v: "step")
print(("OK  " if d3.get("detenido") is None and not d3.get("error") else "FALLO ")
      + "run_analysis solo step termina normal ->", d3.get("detenido"))
