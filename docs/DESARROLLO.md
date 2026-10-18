# Desarrollo, pruebas y compilación

Guía para quien toca el código: cómo ejecutar las pruebas, cómo compilar y qué
comprobar antes de subir de versión.

---

## 1. Entorno

| Pieza | Versión / nota |
|---|---|
| Python | 3.13+ (probado con **3.14.4**), con `py` o `python` en el PATH |
| Dependencias | Ninguna: solo biblioteca estándar y tkinter |
| PyInstaller | Lo instala `build.bat` si falta (`py -m pip install pyinstaller`) |
| Inno Setup | **6 o 7** para el instalador (`C:\Program Files\Inno Setup 7\ISCC.exe`); opcional |

Editar con cualquier editor; para cambios en el IDE es útil tener una terminal
a mano para lanzar los tests.

---

## 2. Pruebas

### Suites

| Comando | Qué cubre | Salida esperada |
|---|---|---|
| `py -u tests.py` | Léxico, sintaxis, expresiones, variables, condicionales, bucles, funciones, listas, textos e interpolación, tipos y errores, ámbitos, diccionarios, entrada, comillas simples, módulos, depurador | `OK — todos los tests pasaron` |
| `py -u tests_ide.py` | Editor del IDE: deshacer/rehacer, buscar y reemplazar, saltos, `Ctrl+A`, menú contextual y las 6 ramas del modal de guardado (36 comprobaciones) | `resultado: OK` |
| `py -u _prueba_nuevo.py` | Chequeo rápido de las funciones nuevas de la última versión | líneas `OK`/`FALLO` |
| `py prueba_sin_ventana.py salida.txt` | Comprueba que ejecutar **no** abre ventanas de terminal (20 lanzamientos desde `pythonw`) | escribe `runtime=... aciertos=20/20` |

`tests_ide.py` **abre la ventana** (~2 s). Nota: con la ventana `withdraw()` Tk
no acepta foco y los eventos de tecla no llegan al editor, por eso el test hace
`deiconify()` antes de simular atajos.

### Convenciones de los tests

- `expect_output(código, esperado)` y `expect_error(código, excepción, texto)`
  en `tests.py`.
- Cada fase se agrupa con un comentario `# --- nombre de la sección`.
- Si un test falla por una asunción mal puesta del test (y no del código),
  se corrige **el test**, dejándolo estricto.

### Antes de dar un cambio por bueno

```bash
py -u tests.py
py -u tests_ide.py
```

---

## 3. Compilación

Un solo comando:

```bat
cmd /c build.bat
```

o doble clic en **`build.bat`** (usa `chcp 65001` para que la consola muestre
bien los acentos).

### Qué hace (3 pasos)

1. **`dist\eco.exe`** — PyInstaller `--onefile` de `main.py` (CLI de consola).
2. **`dist\eco-ide.exe`** — PyInstaller `--onefile --windowed` de `ide.py`,
   con `ejemplos/` empaquetado dentro (`--add-data`).
3. **`dist\eco-setup.exe`** — Inno Setup con `instalador.iss`
   (detecta `%ProgramFiles(x86)%\Inno Setup*`, `%ProgramFiles%\Inno Setup*` y
   la versión **7**; si no hay Inno, se salta el instalador sin fallar el build).

`build/` guarda `.spec` y temporales; se puede borrar (`--clean` lo limpia).

### Reglas importantes

- **No miente**: si PyInstaller devuelve error, el script va a `:fallo` y **no**
  firma instaladores con ejecutables viejos.
- **Mata los procesos primero**: si hay un `eco.exe` o `eco-ide.exe` en marcha,
  PyInstaller falla con `PermissionError`:

  ```powershell
  Get-Process eco, eco-ide -ErrorAction SilentlyContinue | Stop-Process -Force
  ```
- El proceso del `build.bat` **acaba con exit code 1** cuando se le cierra la
  entrada por el `pause` final; el indicador real de éxito es la línea final
  `OK: dist\eco.exe, dist\eco-ide.exe ...`.

### Verificar el interior de un `.exe`

Útil para confirmar que el paquete nuevo lleva el código nuevo:

```python
from PyInstaller.archive.readers import CArchiveReader
a = CArchiveReader(r"dist\eco-ide.exe")
# clave "PYZ.pyz" → extraer → ZlibArchiveReader.extract("runtime")
# y barrer co_consts buscando "0.4.0"
```

Comprobación rápida también: `dist\eco.exe --version` debe imprimir la versión.

---

## 4. Instalador (`instalador.iss`)

- Inno Setup **6 o 7**, interfaz en español.
- `PrivilegesRequired=lowest`: instala en `%LOCALAPPDATA%\Programs\eco`, **sin**
  pedir administrador.
- Opciones marcables: acceso directo en escritorio, añadir `{app}` al PATH del
  usuario y asociar `.eco` con el IDE.
- `[Code]` desregistra PATH, accesos y asociación al desinstalar.
- Versión: `MyAppVersion` debe coincidir con `VERSION` de `runtime.py`.

---

## 5. Checklist de versión

Cuando cambies la versión (p. ej. `0.4.0` → `0.5.0`):

1. `runtime.py` → `VERSION = "0.5.0"` (única fuente de verdad).
2. `instalador.iss` → `MyAppVersion "0.5.0"`.
3. `web/index.html` → `eco v0.5.0`.
4. `README.md` → `eco --version # 0.5.0` + entrada nueva en el changelog.
5. `ejemplos/inventario.eco` (saludo) y cualquier texto con la versión.
6. `py -u tests.py` → `OK`.
7. `py -u tests_ide.py` → `OK`.
8. `build.bat` → `OK: dist\...`.
9. Comprobar `FileVersion` de `dist\eco-setup.exe` y `eco.exe --version`.

---

## 6. Estilo y convenciones

- Comentarios y mensajes **en español**, como el lenguaje.
- Mensajes de error: `fase + [línea N, columna M] + explicación + pista`.
- Nada de dependencias fuera de la estándar.
- Código ASCII en `.py` donde no aporte nada; UTF-8 en `.eco`, `.md` y `.bat`
  (`chcp 65001`).
- Un cambio que toca el lenguaje lleva su test en `tests.py`; uno que toca el
  editor, en `tests_ide.py`.
- Borradores de prueba (los que empiezan por `_`, como `_prueba_nuevo.py`) se
  mantienen solo si son útiles para regresiones; los temporales (`_t_*.py`) se
  borran al terminar.

---

## 7. Estructura de un cambio típico

1. Reproducir el bug o decidir la mejora.
2. Escribir primero el test que lo demuestra (`tests.py` / `tests_ide.py`).
3. Arreglar en el módulo que corresponda (ver
   [ARQUITECTURA.md §2](ARQUITECTURA.md#2-módulos-y-responsabilidad)).
4. Ambas suites en verde.
5. Actualizar documentación (`README.md` y `docs/`).
6. Si es función nueva: changelog y, si procede, nueva versión con el
   checklist de arriba.

---

## Siguiente paso

- Dónde tocar cada cosa: [ARQUITECTURA.md](ARQUITECTURA.md)
- Criterios formales: [REQUISITOS.md](REQUISITOS.md#9-criterios-de-aceptación)
