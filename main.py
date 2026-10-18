"""CLI del intérprete `eco` — igual que `node` o `java`.

    eco archivo.eco        ejecuta un archivo
    eco                     REPL interactivo
    eco --analyze f.eco    analiza y emite JSON (salida, tokens, AST)
    eco --analyze           ... leyendo el código por stdin (lo usa el IDE)
    eco --server            modo servidor JSON por stdin/stdout (interno)
    eco --version           versión del intérprete

Un archivo puede traer otros con:   importar "otro.eco" [como alias];
"""

import json
import sys

from lexer import tokenize, LexError
from parser import parse, ParseError
from interpreter import Interpreter, RunError, set_input_handler, \
    set_debug_hook, crear_hook_debug
from runtime import VERSION, analyze


def compile_and_run(source: str, interp: Interpreter):
    """Las tres fases: lexing -> parsing -> evaluación."""
    interp.run(parse(tokenize(source)))


def run_file(path: str, interp: Interpreter) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"No se pudo abrir el archivo: {e}", file=sys.stderr)
        return 1
    try:
        compile_and_run(source, interp)
    except (LexError, ParseError, RunError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def repl(interp: Interpreter):
    print(f"eco {VERSION} — escribe \"salir\" o Ctrl+Z + Enter para terminar")
    buffer = ""
    while True:
        try:
            line = input("... " if buffer else "eco> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not buffer and line.strip().lower() in ("salir", "exit", "quit"):
            break

        buffer += line + "\n"
        # si quedó un bloque abierto, seguimos leyendo
        if buffer.count("{") > buffer.count("}"):
            continue

        source, buffer = buffer, ""
        if not source.strip():
            continue
        try:
            compile_and_run(source, interp)
        except (LexError, ParseError, RunError) as e:
            print(f"Error: {e}")
        except Exception as e:  # nunca caemos sin mensaje
            print(f"Error interno: {e}")


def _puente_entrada(salida, entrada):
    """Manejador de `entrada()` en modo servidor.

    Avisa al IDE con  {"tipo": "entrada", "pregunta": ...}  y espera en stdin
    la respuesta  {"entrada": "..."}  (el IDE abre un diálogo y responde).
    """

    def leer(pregunta):
        salida.write(json.dumps({"tipo": "entrada", "pregunta": pregunta},
                                ensure_ascii=False).encode("utf-8") + b"\n")
        salida.flush()
        linea = entrada.readline()
        if not linea:
            raise EOFError("se cortó la comunicación con quien ejecuta el programa")
        datos = json.loads(linea.decode("utf-8", "replace"))
        return str(datos.get("entrada", ""))

    return leer


def _puente_debug(salida, entrada):
    """Depuración paso a paso en modo servidor.

    Avisa con  {"tipo": "paso", "linea": N, "variables": {...}}  y espera en
    stdin la acción:  {"accion": "step" | "continue" | "stop"}.
    """

    def enviar(linea, variables):
        salida.write(json.dumps({"tipo": "paso", "linea": linea,
                                 "variables": variables},
                                ensure_ascii=False).encode("utf-8") + b"\n")
        salida.flush()
        crudo = entrada.readline()
        if not crudo:
            return "stop"                      # se cortó la comunicación
        datos = json.loads(crudo.decode("utf-8", "replace"))
        accion = datos.get("accion", "continue")
        return accion if accion in ("step", "continue", "stop") else "continue"

    return enviar


def main() -> int:
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    if args and args[0] in ("-v", "--version"):
        print(VERSION)
        return 0

    if args and args[0] in ("-e", "--eval"):
        if len(args) < 2:
            print("Error: -e necesita código, p. ej.  eco -e \"escribe 2 + 2;\"",
                  file=sys.stderr)
            return 2
        try:
            compile_and_run(args[1], Interpreter())
        except (LexError, ParseError, RunError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        return 0

    if args and args[0] == "--server":
        # modo servidor (interno): un JSON por línea en stdin -> un JSON en
        # stdout. Si el programa hace `entrada(...)`, se intercala un aviso
        # {"tipo": "entrada", ...} y la respuesta entra por stdin; y si la
        # petición trae "debug": true, cada instrucción avisa con
        # {"tipo": "paso", ...} y espera {"accion": ...}.
        # Lo usa el IDE para no pagar el arranque del .exe en cada run.
        salida_real, entrada_real = sys.stdout.buffer, sys.stdin.buffer
        set_input_handler(_puente_entrada(salida_real, entrada_real))
        for raw in entrada_real:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except ValueError:
                req = {}
            if req.get("cmd") == "exit":
                break
            src = req.get("source")
            filename = req.get("file")
            if not isinstance(filename, str) or not filename:
                filename = None
            if req.get("debug"):
                set_debug_hook(crear_hook_debug(
                    _puente_debug(salida_real, entrada_real)))
            try:
                result = analyze(src if isinstance(src, str) else "",
                                 filename=filename)
            finally:
                set_debug_hook(None)
            salida_real.write(json.dumps(result, ensure_ascii=False).encode("utf-8") + b"\n")
            salida_real.flush()
        set_input_handler(None)
        return 0

    if args and args[0] == "--analyze":
        origen = None
        if len(args) > 1:
            origen = args[1]
            try:
                with open(args[1], encoding="utf-8") as f:
                    source = f.read()
            except OSError as e:
                print(json.dumps({"version": VERSION, "output": "",
                                  "error": f"No se pudo abrir: {e}", "phase": "run",
                                  "detenido": None, "tokens": None, "ast": None},
                                 ensure_ascii=False))
                return 1
        else:
            source = sys.stdin.read()   # el IDE manda el código por stdin
        print(json.dumps(analyze(source, filename=origen), ensure_ascii=False))
        return 0

    if args:
        return run_file(args[0], Interpreter(args[0]))
    repl(Interpreter())
    return 0


if __name__ == "__main__":
    sys.exit(main())
