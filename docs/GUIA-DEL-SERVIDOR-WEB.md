# Guía del IDE web

El IDE web es **opcional**: sirve un editor en el navegador y ejecuta el código
con el mismo intérprete que la CLI. Es local: solo tú ves tu equipo.

---

## 1. Arranque

```bash
py server.py                 # http://127.0.0.1:8787
py server.py --port 9000     # otro puerto
```

Abre `http://127.0.0.1:8787` y pulsa `Ctrl+Enter` para ejecutar. Detener con
`Ctrl+C`.

Si existe `dist/eco.exe` se usa ese; si no, el intérprete de Python (lo indica
el chip `runtime:` de arriba y del pie). Con `build.bat` lo tienes más rápido.

---

## 2. Qué hay en pantalla

| Zona | Qué hace |
|---|---|
| **▶ Ejecutar** (`Ctrl+Enter`) | Ejecuta el código y rellena la pestaña Salida |
| **— ejemplos —** | Desplegable con los `.eco` de `ejemplos/` |
| **Abrir…** | Carga un archivo `.eco` de tu equipo |
| **Guardar** | Descarga el código como archivo |
| **Limpiar consola** | Vacía la Salida |
| **Cómo compilarlo** | Muestra/oculta los comandos de `build.bat` |
| **⬇ Descargar eco.exe** | Descarga el intérprete compilado (si ya existe) |
| Editor | Con números de línea y resaltado de sintaxis |
| Pestañas **Salida** / **Tokens** / **AST** | Resultado de cada fase |
| `#status` | `Listo`, `⏳ ejecutando…`, `✓ OK · N línea(s) de salida` o el error |

Si un error trae línea, su número se marca en rojo en el margen y el error se
muestra con su fase (`léxico`, `sintaxis` o `ejecución`).

---

## 3. Endpoints

Base: `http://127.0.0.1:8787`

| Método y ruta | Qué devuelve |
|---|---|
| `GET /` (o `/index.html`) | El IDE (`web/index.html`) |
| `GET /examples` | `{"examples": [{"name": "saludo", "source": "..."}]}` — los `.eco` de `ejemplos/`, ordenados |
| `GET /status` | `{"version": "0.4.0", "exe": true, "exe_name": "eco.exe", "exe_size": 123, "runtime": "eco.exe"}` |
| `GET /download` | Los bytes de `eco.exe` (404 en JSON si no está compilado) |
| `POST /analyze` | Ejecuta y devuelve el resultado (abajo) |
| cualquier otra | `404` |

### `POST /analyze`

Petición:

```json
{"source": "escribe 2 + 2;", "file": "saludo"}
```

- `source` (obligatorio): el código.
- `file` (opcional): **nombre** del ejemplo del que vino el código; hace que
  `importar "modulos/utilidades"` se resuelva relativo a `ejemplos/`.

Respuesta: el mismo objeto de `eco --analyze` (`version, output, error, phase,
detenido, tokens, ast`) más `runtime` con el nombre del intérprete usado.

Ejemplo de error:

```json
{"version": "0.4.0", "output": "", "error": "[línea 1] ...", "phase": "run",
 "detenido": null, "tokens": [...], "ast": {...}, "runtime": "eco.exe"}
```

---

## 4. Seguridad

- El servidor escucha **solo en `127.0.0.1`**: no se expone a la red.
- El tamaño máximo de código por petición es de **500 000 bytes** (más allá,
  responde `400`).
- `file` solo acepta **nombres planos** de dentro de `ejemplos/`: cualquier
  ruta, extensión rara o `..` se descarta (`server.py::ruta_ejemplo`), así que
  el navegador no puede leer ficheros arbitrarios.

---

## 5. Limitaciones

| Límite | Qué hacer |
|---|---|
| **No hay `entrada()`** | Devuelve un error claro en lugar de bloquear: ejecuta el programa con `eco.exe` en terminal o en el IDE de escritorio |
| **No hay depurador** (F9, puntos de ruptura) | Usa el IDE de escritorio |
| **No hay autoguardado** | *Guardar* descarga el archivo; *Abrir…* lo vuelve a cargar |
| **`eco.exe` sin compilar** | Todo funciona con Python, pero más lento al arrancar; `build.bat` lo soluciona |

---

## 6. Problemas comunes

| Síntoma | Solución |
|---|---|
| `✕ sin conexión con el intérprete` | El servidor se cayó: relanza `py server.py` |
| `No llegué al intérprete: ...` | Igual; mira la terminal donde corre el servidor |
| `Petición inválida` (400) | Código demasiado grande o JSON malformado |
| El puerto está ocupado | `py server.py --port 8788` |

---

## 7. Cómo encaja

```
navegador ──HTTP──▶ server.py ──▶ runtime.run_analysis()
                                       │
                     ¿hay eco.exe? ────┤
                          sí          no
                           ▼           ▼
                  worker eco --server   lexer/parser/interpreter
                  (vivo, JSON por línea)   en el proceso Python
```

El mismo flujo que usa el IDE de escritorio; la única diferencia es que aquí
`entrada()` no tiene canal de respuesta.

- Detalles del protocolo: [GUIA-DE-LA-CLI.md](GUIA-DE-LA-CLI.md#5---server-protocolo-para-el-ide)
- Por dentro de `runtime.py`: [ARQUITECTURA.md](ARQUITECTURA.md)
