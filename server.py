"""Servidor del IDE web de eco.

Sirve el frontend (web/index.html) y habla con el intérprete:

    GET  /            -> el IDE (editor + consola)
    GET  /examples    -> los .eco de la carpeta ejemplos/
    GET  /status      -> qué runtime ejecuta el código (eco.exe / Python)
    GET  /download    -> descarga el ejecutable eco.exe
    POST /analyze     -> lexing + parsing + evaluación, con tokens y AST

El IDE prefiere `dist/eco.exe`; si no existe, usa el intérprete de Python.
Solo biblioteca estándar:  py server.py [--port 8787]
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import runtime
from runtime import VERSION

BASE = Path(__file__).resolve().parent
INDEX = BASE / "web" / "index.html"
EXAMPLES_DIR = BASE / "ejemplos"
EXE = runtime.find_cli_exe() or (BASE / "dist" / runtime.CLI_NAME)
MAX_SOURCE = 500_000  # bytes de código fuente aceptados por petición


def run_analysis(source: str, filename: str | None = None) -> dict:
    """El mismo núcleo que el IDE de escritorio (servidor vivo + eco.exe).

    `entrada()` no se puede responder desde el navegador: devuelve un error
    claro en lugar de bloquear la petición.

    `filename` es el ejemplo del que vino el código: de ahí salen las rutas
    relativas de `importar "modulos/utilidades"`.
    """
    return runtime.run_analysis(source, filename=filename)


def ruta_ejemplo(nombre) -> str | None:
    """Ruta absoluta de un ejemplo por su nombre ('importar'), o None.

    Solo se aceptan nombres planos de la carpeta ejemplos/ (nada de rutas
    ni de '..': el navegador manda texto, no caminos).
    """
    if not isinstance(nombre, str) or not nombre.strip():
        return None
    p = Path(nombre.strip())
    if p.suffix == ".eco":
        p = p.with_suffix("")
    if p.name != str(p) or p.name in ("", ".", ".."):
        return None
    cand = EXAMPLES_DIR / (p.name + ".eco")
    return str(cand) if cand.is_file() else None


class Handler(BaseHTTPRequestHandler):
    server_version = f"EcoIDE/{VERSION}"

    def log_message(self, fmt, *args):         # log silencioso
        pass

    # ------------------------------------------------------------ helpers
    def send_bytes(self, payload: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, data, status: int = 200):
        blob = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_bytes(blob, "application/json; charset=utf-8", status)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_SOURCE:
            return None
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        return data if isinstance(data, dict) else None

    # ------------------------------------------------------------ rutas
    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path in ("/", "/index.html"):
            self.send_bytes(INDEX.read_bytes(), "text/html; charset=utf-8")

        elif path == "/examples":
            items = []
            if EXAMPLES_DIR.is_dir():
                for f in sorted(EXAMPLES_DIR.glob("*.eco")):
                    items.append({"name": f.stem, "source": f.read_text(encoding="utf-8")})
            self.send_json({"examples": items})

        elif path == "/status":
            self.send_json({
                "version": VERSION,
                "exe": EXE.is_file(),
                "exe_name": EXE.name,
                "exe_size": EXE.stat().st_size if EXE.is_file() else 0,
                "runtime": runtime.CLI_NAME if EXE.is_file()
                           else f"python {sys.version_info.major}.{sys.version_info.minor}",
            })

        elif path == "/download":
            if EXE.is_file():
                self.send_bytes(EXE.read_bytes(), "application/octet-stream")
            else:
                self.send_json({"error": f"{runtime.CLI_NAME} aún no está compilado. "
                                         "Ejecuta build.bat para generarlo."}, 404)

        else:
            self.send_bytes(b"404", "text/plain; charset=utf-8", 404)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/analyze":
            self.send_bytes(b"404", "text/plain; charset=utf-8", 404)
            return
        data = self.read_json()
        if data is None:
            self.send_json({"error": "Petición inválida"}, 400)
            return
        source = data.get("source", "")
        if not isinstance(source, str):
            self.send_json({"error": "'source' debe ser texto"}, 400)
            return
        self.send_json(run_analysis(source, filename=ruta_ejemplo(data.get("file"))))


def main():
    port = 8787
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"IDE web de eco en  http://127.0.0.1:{port}   (Ctrl+C para parar)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")


if __name__ == "__main__":
    main()
