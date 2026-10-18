# Arquitectura de eco

Cómo está hecho el código, dónde tocar para cada cosa y qué contratos existen
entre piezas.

---

## 1. El flujo de un programa

```
fuente (.eco)
   │
   ▼
lexer.py ── tokenize() ──▶ [Token]          (type, value, line, col)
   │                         │ LexError
   ▼
parser.py ── parse() ────▶ [AST]            (nodos dataclass)
   │                         │ ParseError
   ▼
interpreter.py ── run() ──▶ salida (stdout) o RunError
```

Las tres fases **no se mezclan**: el léxico nunca sabe de instrucciones, el
parser no ejecuta y el evaluador no mira el texto original. Eso permite
mostrar tokens y AST por separado (pestañas del IDE) y dar mensajes con la fase
que corresponde.

### Nodos del AST

`parser.py` define `dataclass` planas (una por construcción), cada una con su
`line` y, donde importa, su `col`:

| Grupo | Nodos |
|---|---|
| Programa y sentencias | `Program`, `Print`, `ExprStatement`, `Block` |
| Declaración y asignación | `Let`, `Assign`, `IndexAssign`, `AttrAssign`, `Incremento` |
| Control de flujo | `If`, `While`, `For`, `ForIn`, `Return`, `Break`, `Continue` |
| Funciones y módulos | `Function`, `Importar` |
| Expresiones | `Binary`, `Unary`, `Call`, `Var`, `Index`, `Attribute` |
| Literales | `Number`, `Text`, `Boolean`, `Null`, `Lista`, `Diccionario` |

---

## 2. Módulos y responsabilidad

| Archivo | Responsabilidad | No debe hacer |
|---|---|---|
| `lexer.py` | Texto → tokens; `//`, escapes, `${}`, `i++` | Saber de bloques o funciones |
| `parser.py` | Tokens → AST; reporta *falta `;`*, *falta `}`* | Evaluar nada |
| `interpreter.py` | Ámbitos, bucles, funciones, métodos, errores de ejecución y **los módulos** (`importar` lee, cachea y ejecuta el fichero) | Conocer la CLI ni la ventana |
| `runtime.py` | Empaqueta las 3 fases en un dict JSON; gestiona el worker `eco --server` | Conocer tkinter ni HTTP |
| `main.py` | CLI: archivo, REPL, `-e`, `--analyze`, `--server`, códigos de salida | Lógica del lenguaje |
| `ide.py` | Ventana tkinter: editor, depurador, consola, Tokens/AST, modal | Implementar fases (usa `runtime` o `eco.exe`) |
| `server.py` | HTTP local: `web/index.html` + `/analyze` | Lógica del lenguaje (usa `runtime`) |
| `web/index.html` | Editor del IDE web, resaltador propio, pestañas | — |
| `tests.py` / `tests_ide.py` | Lenguaje y editor | — |

### Qué hace `runtime.py` (la pieza central)

```python
analyze(source, filename=None, ...)   # 3 fases → dict JSON
run_analysis(source, filename=None)   # analyze + nombre del runtime
```

El dict devuelto es **el contrato** de todo el sistema:

```json
{"version": "...", "output": "...", "error": null, "phase": null,
 "detenido": null, "tokens": [...], "ast": {...}, "runtime": "eco.exe"}
```

Además:

- **Prefiere `eco.exe`**: si existe junto al proceso, lanza ese; si no, ejecuta
  las fases en el propio proceso con los módulos de Python.
- **Worker vivo**: mantiene un `eco --server` en segundo plano para no pagar el
  arranque del `.exe` (≈700 ms) en cada *Ejecutar*. Si muere o tarda más de
  `EXE_TIMEOUT` (15 s), se reinicia; como último recurso, ejecución one-shot.
- **`CREATE_NO_WINDOW`**: los lanzamientos desde el IDE no abren ventanas de
  terminal (verificado por `prueba_sin_ventana.py`).
- **`entrada()`** se enruta con `set_input_handler`; sin canal devuelve
  `SIN_ENTRADA` (un mensaje claro, nunca bloqueo).
- **Depuración** con `set_debug_hook` / `crear_hook_debug`: el hook devuelve
  `"step"`, `"continue"` o `"stop"`.

---

## 3. Contratos entre piezas

| De → a | Contrato |
|---|---|
| CLI / IDE / servidor → intérprete | JSON por línea (ver [CLI §5](GUIA-DE-LA-CLI.md#5---server-protocolo-para-el-ide)) |
| `runtime` → `eco.exe` | mismo JSON, por stdin/stdout, UTF-8 |
| IDE → `runtime` | `run_analysis(source, filename)` |
| IDE → usuario | mensajes `fase + [línea N, columna M] + texto` |
| `server` → navegador | JSON con `Content-Type: application/json` |

Toda excepción inesperada se convierte en `Error interno del intérprete`
(`analyze()` captura `Exception`): ninguna de las tres fases puede tumbar el
proceso que la llama.

---

## 4. Puntos de extensión

### Añadir una función incorporada

1. Implementar en `interpreter.py`: `def _mifuncion(interp, a, line): ...`
   (`interp.fail(line, "msg")` para un error bonito).
2. Registrarla en la lista de nativas (cerca de
   `("longitud", _longitud, 1, 1)`) con su **mínimo y máximo de argumentos**.
3. Test en `tests.py`.

### Añadir un método a un tipo

1. Definir `def _texto_mimethodo(interp, r, a, line)` (`r` es el receptor, `a`
   la lista de argumentos).
2. Meterlo en el diccionario `METODOS["texto"]` (o lista/diccionario/número)
   como `("mimethodo", min, max, función)`.
3. Test + actualizar la tabla de [GUIA-DEL-LENGUAJE.md](GUIA-DEL-LENGUAJE.md#14-métodos-se-usan-con-punto).

### Añadir una palabra clave

1. `lexer.py` → `KEYWORDS["nueva"] = "NUEVA"`.
2. `parser.py` → tratarla en `statement()` y construir su nodo.
3. `interpreter.py` → ejecutar el nodo (`exec`/`eval`).
4. Documentarla en la lista de palabras clave (README y guía).

### Añadir una instrucción

Sigue el mismo camino que `mientras` (parser: `statement()` → `condicion()` +
`block()`; intérprete: rama en `exec` con `Env` propio para el ámbito).

### Añadir un ejemplo

Crear `ejemplos/mi_ejemplo.eco` con un comentario de cabecera. Aparece solo en
el combo del IDE, en `GET /examples` y se empaqueta en `eco-ide.exe` con
`build.bat`. Para ficheros de apoyo de `importar`, van en `ejemplos/modulos/`
(no aparecen en el combo).

### Añadir un endpoint

En `server.py`: rama en `do_GET`/`do_POST` + `self._json(...)`. Recordar
tamaño máximo y no aceptar rutas libres.

---

## 5. Estructura del repositorio

```
eco/
├── lexer.py  parser.py  interpreter.py   el lenguaje
├── runtime.py                             núcleo compartido + worker
├── main.py                                CLI
├── ide.py                                 IDE de escritorio (tkinter)
├── server.py  web/index.html             IDE web
├── tests.py   tests_ide.py                suites
├── build.bat   instalador.iss             build e instalador
├── build/   eco.spec   eco-ide.spec       artefactos de PyInstaller
├── dist/    eco.exe  eco-ide.exe  eco-setup.exe
├── ejemplos/  *.eco  modulos/utilidades.eco
├── IDE.bat    _prueba_nuevo.py    prueba_sin_ventana.py
├── README.md  docs/
└── __pycache__/                           no versionar
```

---

## 6. Decisiones de diseño (y por qué)

| Decisión | Motivo |
|---|---|
| Palabras clave en español | El sello del proyecto; el lector entiende el programa sin traducir |
| Todo números con decimales | Un solo tipo numérico: menos casos raros en `==` y `/` |
| Sin dependencias (solo stdlib + tkinter) | Instalar es un `.exe`, no un entorno Python |
| Formato JSON único entre piezas | CLI, IDE y web leen lo mismo; `--analyze` sirve para depurar |
| Worker vivo `eco --server` | Evita ~700 ms por ejecución |
| `CREATE_NO_WINDOW` | El IDE no debe abrir ventanas de CMD |
| Tk en vez de Qt/Electron | Cero dependencias, arranque inmediato, se empaqueta en un `.exe` |
| `si`/`mientras` con paréntesis opcionales | Amabilidad con quien viene de otros lenguajes |
| Errores con `fase + línea + columna` | El IDE puede marcar la línea exacta |

---

## Siguiente paso

- Guía del lenguaje: [GUIA-DEL-LENGUAJE.md](GUIA-DEL-LENGUAJE.md)
- Tests y build: [DESARROLLO.md](DESARROLLO.md)
