"""Núcleo compartido: las tres fases del intérprete empaquetadas en un dict JSON.

Lo usan el CLI (`main.py`), el servidor web (`server.py`) y el IDE de escritorio
(`ide.py`). Prefiere ejecutar el código con `eco.exe` si existe; si no, lo
interpreta en el propio proceso con los módulos de Python.
"""

import io
import json
import subprocess
import sys
import threading
import atexit
from contextlib import redirect_stdout
from dataclasses import fields, is_dataclass
from pathlib import Path

from lexer import tokenize, LexError
from parser import parse, ParseError
from interpreter import Interpreter, RunError, Detener, set_debug_hook, \
    set_input_handler, get_input_handler, crear_hook_debug

VERSION = "0.4.0"
CLI_NAME = "eco.exe"        # el intérprete compilado (tipo node)
EXE_TIMEOUT = 15  # segundos

# En Windows, un proceso gráfico (el IDE) que lanza un .exe de consola (eco)
# crea una ventana de terminal parpadeante. CREATE_NO_WINDOW la suprime sin
# perder la salida, que llega igual por las tuberías (capture_output).
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def to_json(obj):
    """AST (dataclass) o Token -> estructura JSON con el nombre del nodo."""
    if is_dataclass(obj) and not isinstance(obj, type):
        data = {"_type": type(obj).__name__}
        for f in fields(obj):
            data[f.name] = to_json(getattr(obj, f.name))
        return data
    if isinstance(obj, list):
        return [to_json(x) for x in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return repr(obj)


def analyze(source: str, filename=None) -> dict:
    """Ejecuta lexing + parsing + evaluación y devuelve el resultado de las 3 fases.

    `filename` es el archivo de origen: de ahí salen las rutas relativas de
    `importar`. Si la depuración detiene el programa, el resultado lleva
    `"detenido": <línea>` (sin error).
    """
    output = io.StringIO()
    error = None
    phase = None
    tokens = None
    ast = None
    detenido = None
    with redirect_stdout(output):
        try:
            tokens = tokenize(source)          # fase 1: análisis léxico
            ast = parse(tokens)                # fase 2: análisis sintáctico
            Interpreter(filename=filename).run(ast)   # fase 3: evaluación
        except LexError as e:
            error, phase = str(e), "lex"
        except ParseError as e:
            error, phase = str(e), "parse"
        except RunError as e:
            error, phase = str(e), "run"
        except Detener as e:                   # el usuario pulsó "Detener"
            detenido = e.line
        except Exception as e:                 # nunca devolvemos una excepción cruda
            error, phase = f"Error interno del intérprete: {e!r}", "run"
    return {
        "version": VERSION,
        "output": output.getvalue(),
        "error": error,
        "phase": phase,
        "detenido": detenido,
        "tokens": to_json(tokens) if tokens is not None else None,
        "ast": to_json(ast),
    }


def find_cli_exe():
    """Busca el intérprete compilado: junto al programa, en dist/ o en la fuente."""
    cands = []
    if getattr(sys, "frozen", False):                     # ejecutable compilado
        cands.append(Path(sys.executable).resolve().parent / CLI_NAME)
    here = Path(__file__).resolve().parent
    cands += [here / "dist" / CLI_NAME, here / CLI_NAME]
    for c in cands:
        if c.is_file():
            return c
    return None


find_mini_exe = find_cli_exe        # nombre antiguo, por compatibilidad


def _analyze_with_exe(exe, source: str):
    try:
        proc = subprocess.run([str(exe), "--analyze"],
                              input=source.encode("utf-8"),
                              capture_output=True, timeout=EXE_TIMEOUT,
                              creationflags=CREATE_NO_WINDOW)
        if proc.returncode not in (0, 1):
            return None
        return json.loads(proc.stdout.decode("utf-8"))
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def runtime_name() -> str:
    return CLI_NAME if find_cli_exe() else \
        f"python {sys.version_info.major}.{sys.version_info.minor}"


SIN_ENTRADA = {
    "version": VERSION,
    "output": "",
    "error": "Este programa pide datos por teclado (entrada()) y aquí no se puede "
             "preguntar: ejecútalo con eco.exe en una terminal o con el IDE de escritorio.",
    "phase": "run",
    "detenido": None,
    "tokens": None,
    "ast": None,
}


class _Worker:
    """Mantiene `eco --server` vivo para no pagar su arranque (~700 ms)
    en cada Ejecutar. Si algo falla, se reinicia y se usa el modo one-shot."""

    def __init__(self, exe):
        self.exe = str(exe)
        self.proc = None
        self.lock = threading.Lock()

    def _stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        for paso in (0, 1):
            try:
                (proc.stdin.close() if paso == 0 else proc.kill())
                if paso == 1:
                    proc.wait(timeout=1)
            except Exception:
                pass

    def _start(self):
        self.proc = subprocess.Popen(
            [self.exe, "--server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)

    def _escribir(self, obj) -> bool:
        try:
            self.proc.stdin.write(json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n")
            self.proc.stdin.flush()
            return True
        except (OSError, ValueError, AttributeError):
            return False

    def _leer_linea(self, timeout: float):
        """Una línea JSON del servidor (o None si algo va mal)."""
        lectura = []
        fin = threading.Event()
        proc = self.proc

        def _leer():
            try:
                # Popen.stdout ya es binario: no existe .buffer (eso es de sys.stdout)
                lectura.append(proc.stdout.readline())
            except Exception:
                lectura.append(b"")
            fin.set()

        threading.Thread(target=_leer, daemon=True).start()
        if not fin.wait(timeout) or not lectura or not lectura[0]:
            return None
        return lectura[0].decode("utf-8", "replace")

    def ask(self, source: str, on_input=None, timeout: float = EXE_TIMEOUT,
            filename=None, debug: bool = False, on_debug=None) -> dict:
        """Ejecuta `source`. Si el programa hace entrada(...), se llama a
        `on_input(pregunta) -> respuesta` (p. ej. un diálogo en el IDE).
        Si `debug`, el servidor avanza instrucción a instrucción y llama a
        `on_debug(línea, variables) -> "step" | "continue" | "stop"`."""
        with self.lock:
            if self.proc is None or self.proc.poll() is not None:
                self._start()
            req = {"source": source}
            if filename:
                req["file"] = str(filename)
            if debug:
                req["debug"] = True
            if not self._escribir(req):
                self._stop()
                return None

            while True:
                linea = self._leer_linea(timeout)
                if linea is None:
                    self._stop()      # reinicio: el flujo ya no estaría sincronizado
                    return None
                try:
                    obj = json.loads(linea)
                except ValueError:
                    self._stop()
                    return None

                if obj.get("tipo") == "entrada":        # el programa pide datos
                    if on_input is None:
                        self._stop()
                        return dict(SIN_ENTRADA)
                    try:
                        respuesta = on_input(obj.get("pregunta", ""))
                    except Exception as e:
                        self._stop()
                        d = dict(SIN_ENTRADA)
                        d["error"] = f"entrada(): {e}"
                        return d
                    if not self._escribir({"entrada": "" if respuesta is None
                                           else str(respuesta)}):
                        self._stop()
                        return None
                    continue

                if obj.get("tipo") == "paso":           # depuración paso a paso
                    accion = "stop" if on_debug is None else _safe_debug(
                        on_debug, obj.get("linea"), obj.get("variables") or {})
                    if not self._escribir({"accion": accion}):
                        self._stop()
                        return None
                    continue
                return obj


_worker = None
_worker_lock = threading.Lock()


def _get_worker(exe):
    """Crea el servidor bajo demanda (no se gasta un proceso al importar)."""
    global _worker
    with _worker_lock:
        if _worker is None or _worker.exe != str(exe):
            if _worker is not None:
                _worker._stop()
            _worker = _Worker(exe)
            atexit.register(_worker._stop)
        return _worker


def _safe_debug(on_debug, linea, variables) -> str:
    """Llama a `on_debug` sin dejar que un fallo del IDE mate la ejecución."""
    try:
        accion = on_debug(linea, variables)
    except Exception:
        return "stop"
    return accion if accion in ("step", "continue", "stop") else "stop"


def run_analysis(source: str, on_input=None, filename=None, debug=False,
                 on_debug=None) -> dict:
    """Ejecuta el código: con eco.exe si está disponible, si no en el proceso.

    - `on_input(pregunta)` responde a `entrada(...)`; sin él, el resultado es
      un error claro en lugar de quedarse colgado.
    - `filename` es el archivo de origen: de ahí salen las rutas relativas
      de `importar "otro.eco"`.
    - Con `debug` se instala la depuración paso a paso y se llama a
      `on_debug(línea, variables) -> "step" | "continue" | "stop"` en cada
      instrucción.
    """
    exe = find_cli_exe()
    if exe:
        data = _get_worker(exe).ask(source, on_input=on_input, filename=filename,
                                    debug=debug, on_debug=on_debug)
        if data is None:                       # el servidor falló: one-shot
            data = _analyze_with_exe(exe, source)
        if data is not None:
            data["runtime"] = CLI_NAME
            data.setdefault("detenido", None)
            return data
    return _run_local(source, on_input=on_input, filename=filename,
                      debug=debug, on_debug=on_debug)


def _run_local(source, on_input=None, filename=None, debug=False, on_debug=None):
    """Ejecución en el propio proceso (sin eco.exe, o como respaldo)."""
    temporales = []
    if debug:
        set_debug_hook(crear_hook_debug(on_debug or (lambda _l, _v: "stop")))
        temporales.append("debug")
    if on_input is not None and get_input_handler() is None:
        set_input_handler(on_input)            # nadie ha instalado el suyo
        temporales.append("entrada")
    try:
        data = analyze(source, filename=filename)
    finally:
        if "debug" in temporales:
            set_debug_hook(None)
        if "entrada" in temporales:
            set_input_handler(None)
    data["runtime"] = runtime_name()
    return data
