# Requisitos de eco

Especificación de lo que el proyecto **debe** hacer. Cada requisito indica cómo
se verifica hoy (tests automatizados, prueba manual o ambas).

- **Proyecto:** lenguaje de programación `eco` + intérprete + CLI + IDE de
  escritorio + IDE web + instalador.
- **Versión cubierta:** 0.4.0.
- **Plataforma principal:** Windows 10/11 x64.

---

## 1. Alcance

### 1.1 En alcance

- Intérprete completo de un lenguaje con palabras clave **en español**
  (léxico → sintaxis → evaluación).
- CLI tipo `node`: ejecutar archivo, REPL, evaluar código suelto, analizar a JSON.
- IDE de escritorio con editor, resaltado, depurador paso a paso y consola.
- IDE web servido por un proceso local.
- Distribución: instalador de Windows que no requiere administrador ni Python.
- Suite de tests automatizados.

### 1.2 Fuera de alcance (0.4.0)

- Ejecución en Linux/macOS (los `.exe` son de Windows; la fuente corre con
  Python en cualquier sistema).
- IDE web con depuración o con `entrada()`.
- Módulos de terceros / repositorio de paquetes.
- Tipos estáticos, compilación a binario nativo.

---

## 2. Requisitos funcionales — lenguaje

| ID | Requisito | Verificación |
|---|---|---|
| RF-L01 | El programa fuente se convierte en tokens con **línea y columna**. | `tests.py` → sección léxico |
| RF-L02 | Reconoce las palabras clave reservadas: `variable const escribe si sino mientras para en funcion devuelve romper continuar verdadero falso nulo y o no importar como`. | `tests.py` → sintaxis |
| RF-L03 | Soporta tipos: número, texto, booleano, lista, diccionario, nulo y función. | `tests.py` → tipos y errores |
| RF-L04 | Declaración `variable` (mutable) y `const` (inmutable: escribir sobre ella es error). | `tests.py` → variables |
| RF-L05 | Salida `escribe` con varios argumentos separados por espacio y sin `;` perdido. | `tests.py` → léxico/sintaxis |
| RF-L06 | Control de flujo: `si`/`sino si`/`sino`, `mientras`, `para` clásico y `para ... en`, `romper`, `continuar`. | `tests.py` → condicionales y bucles |
| RF-L07 | `si` y `mientras` admiten la condición **con o sin paréntesis**; `para` exige paréntesis. | `tests.py` → condicionales/bucles |
| RF-L08 | Contadores `i++` e `i--` como instrucción y como paso de `para`. | `_prueba_nuevo.py`, `ejemplos/inventario.eco` |
| RF-L09 | Funciones con parámetros, `devuelve`, recursión y **funciones de primera clase** (`f = doble; f(21)`). | `tests.py` → funciones |
| RF-L10 | Azúcar `funcion f(x) = expresión;`. | `tests.py` → funciones |
| RF-L11 | Listas con índice (negativo cuenta desde el final), concatenación `+` y longitud. | `tests.py` → listas |
| RF-L12 | Diccionarios con clave por índice (`d["a"]`) y por punto (`d.a`), creación de clave al asignar. | `tests.py` → diccionarios |
| RF-L13 | Textos con interpolación `${...}`, escapes (`\n \t \" \\ \$`) y comillas simples `'...'`. | `tests.py` → textos e interpolación, comillas simples |
| RF-L14 | Operadores aritméticos (`^` potencia asociativa por la derecha), comparación y lógicos `y o no` con **evaluación corta**. | `tests.py` → expresiones |
| RF-L15 | Ámbitos: lo declarado dentro de un bloque no se ve fuera. | `tests.py` → ámbitos |
| RF-L16 | `importar "ruta" [como alias];` con ruta **relativa a quien importa**, con o sin `.eco`. | `tests.py` → módulos |
| RF-L17 | Un módulo se ejecuta **una sola vez** aunque se importe varias veces. | `tests.py` → módulos |
| RF-L18 | Un módulo exporta sus `variable`, `const` y `funcion` como claves de un diccionario. | `tests.py` → módulos |
| RF-L19 | `entrada([msg])` lee una línea: por consola en terminal, con diálogo en el IDE de escritorio, y **error claro** (no bloqueo) cuando no hay canal. | `tests.py` → entrada |
| RF-L20 | Funciones incorporadas: `entrada longitud rango agregar claves valores texto numero tipo`. | `tests.py` → funciones/entradas |
| RF-L21 | Métodos por tipo: texto (10), lista (10), diccionario (6), número (4). | `tests.py`, `_prueba_nuevo.py` |
| RF-L22 | Cualquier error (léxico, sintáctico o de ejecución) se reporta con **fase, línea y, si existe, columna**, en español. | `tests.py` → tipos y errores |

## 3. Requisitos funcionales — CLI

| ID | Requisito | Verificación |
|---|---|---|
| RF-C01 | `eco archivo.eco` ejecuta el archivo. | `tests.py`, manual |
| RF-C02 | `eco` (sin argumentos) abre un REPL con prompt `eco> ` y continúa si el bloque quedó abierto. | manual |
| RF-C03 | `salir` / `exit` / `quit` y `Ctrl+Z` + `Enter` terminan el REPL. | manual |
| RF-C04 | `eco -e "código"` evalúa código suelto. | manual |
| RF-C05 | `eco --analyze [archivo]` imprime **una línea JSON** con `version, output, error, phase, detenido, tokens, ast`. | `tests.py`, IDE |
| RF-C06 | `eco --server` habla JSON por línea (stdin/stdout) para el IDE. | IDE de escritorio |
| RF-C07 | `eco --version` / `-v` imprime la versión; `-h` / `--help` la ayuda. | manual |
| RF-C08 | Códigos de salida: `0` correcto, `1` error de programa/lectura, `2` uso incorrecto de la CLI. | manual |

## 4. Requisitos funcionales — IDE de escritorio

| ID | Requisito | Verificación |
|---|---|---|
| RF-I01 | Abrir, crear y guardar archivos (`Ctrl+N`, `Ctrl+O`, `Ctrl+S`) y "Guardar como". | `tests_ide.py` |
| RF-I02 | Si hay cambios sin guardar, cualquier acción que los pierda pregunta con el modal **Guardar / Descartar / Cancelar** (Enter/Esc incluidos). | `tests_ide.py` (6 casos) |
| RF-I03 | El título muestra `*` mientras haya cambios. | `tests_ide.py` |
| RF-I04 | Resaltado de sintaxis, números de línea y barra de estado con `Ln, Col`. | manual |
| RF-I05 | Ejecutar con `F5` y ver la salida en la pestaña **Salida**. | manual |
| RF-I06 | Pestañas **Tokens** y **AST** con el resultado de cada fase. | manual |
| RF-I07 | Depurador: `F9` detiene en la primera instrucción, `F10` paso a paso, `F11` al próximo punto de ruptura, `Esc` detiene. | `tests.py` (depurador), manual |
| RF-I08 | Puntos de ruptura con clic en el número de línea. | `tests.py`, manual |
| RF-I09 | Pestaña **Variables** con los valores en cada paso y resaltado de la línea detenida. | manual |
| RF-I10 | Deshacer/rehacer: `Ctrl+Z`, `Ctrl+Y`, `Ctrl+Shift+Z`. | `tests_ide.py` |
| RF-I11 | Buscar: `Ctrl+F` con contador (`3/12`), navegación, `Aa` (distinguir mayúsculas), resaltado en vivo. | `tests_ide.py` |
| RF-I12 | Reemplazar: `Ctrl+H`, reemplazo individual y de todos. | `tests_ide.py` |
| RF-I13 | `F3`/`Shift+F3` siguiente/anterior; con la barra cerrada la reabre con el último término. | `tests_ide.py` |
| RF-I14 | `Ctrl+A` seleccionar todo, `Ctrl+G` ir a la línea. | `tests_ide.py` |
| RF-I15 | Menú contextual (clic derecho) con los atajos entre paréntesis y las opciones de selección deshabilitadas cuando no hay selección. | `tests_ide.py` |
| RF-I16 | `entrada()` se responde con un diálogo. | `ejemplos/entrada.eco`, manual |
| RF-I17 | Combo de ejemplos de `ejemplos/` que se carga en el editor. | manual |
| RF-I18 | Chip de la barra que indica qué runtime ejecuta (`eco.exe` o `Python x.y`). | manual |

## 5. Requisitos funcionales — IDE web

| ID | Requisito | Verificación |
|---|---|---|
| RF-W01 | `py server.py` sirve el editor en `http://127.0.0.1:8787`. | manual |
| RF-W02 | `GET /examples` devuelve los `.eco` de `ejemplos/`. | manual |
| RF-W03 | `POST /analyze` ejecuta y devuelve tokens, AST, salida y error. | manual |
| RF-W04 | El código de un ejemplo manda su nombre para que `importar` funcione, y solo se aceptan **nombres planos** dentro de `ejemplos/` (sin rutas ni `..`). | `server.py::ruta_ejemplo` |
| RF-W05 | `GET /status` y `GET /download` informan y descargan `eco.exe`. | manual |
| RF-W06 | `entrada()` no disponible devuelve un error claro, no se queda colgado. | `runtime.SIN_ENTRADA` |

## 6. Requisitos funcionales — distribución

| ID | Requisito | Verificación |
|---|---|---|
| RF-D01 | El usuario final **no necesita Python**: `eco-setup.exe` instala todo. | manual |
| RF-D02 | La instalación no pide administrador (todo en `%LOCALAPPDATA%\Programs\eco`). | `instalador.iss` (`PrivilegesRequired=lowest`) |
| RF-D03 | Opcionales en la instalación: acceso directo de escritorio, añadir `{app}` al PATH del usuario, asociar `.eco` con el IDE. | `instalador.iss` `[Tasks]` |
| RF-D04 | Menú Inicio con *eco IDE*, *eco REPL*, *Ejemplos* y *Desinstalar eco*. | `instalador.iss` `[Icons]` |
| RF-D05 | La desinstalación borra programa, entrada del PATH, accesos y asociación. | `instalador.iss` `[Code]`, manual |
| RF-D06 | El instalador lleva la versión correcta en sus propiedades de archivo. | `build.bat` + verificación de `FileVersion` |
| RF-D07 | `build.bat` **no miente**: si PyInstaller falla, no firma instaladores con `.exe` viejos. | `build.bat` (`if errorlevel 1 goto fallo`) |
| RF-D08 | El instalador instala `README.md`, `ejemplos/` y las 9 guías de `docs/`. | `instalador.iss` `[Files]`; verificado con instalación en silencio (9 `.md`) |
| RF-D09 | La casilla **Añadir eco al PATH** es la que decide: desmarcada, el registro no se toca. | `instalador.iss` (`Tasks: addpath`); probado en las dos direcciones |

---

## 7. Requisitos no funcionales

| ID | Requisito | Cómo se cumple |
|---|---|---|
| RNF-01 | **Cero dependencias para el usuario final**: solo biblioteca estándar de Python y Tk. | sin `requirements.txt`; PyInstaller empaqueta todo |
| RNF-02 | **Arranque rápido del "Ejecutar"**: no pagar el arranque del `.exe` en cada ejecución. | worker vivo `eco --server` en `runtime.py` |
| RNF-03 | **No bloquear nunca**: toda excepción se convierte en un mensaje con línea y fase. | `analyze()` captura `Exception` → `"Error interno del intérprete"` |
| RNF-04 | **Sin ventanas de terminal parpadeantes** al ejecutar desde el IDE. | `CREATE_NO_WINDOW` en `runtime.py` (verificado por `prueba_sin_ventana.py`) |
| RNF-05 | **Seguridad en local**: el servidor solo escucha en `127.0.0.1`, limita el tamaño del código a **500 000 bytes** y no acepta rutas arbitrarias. | `server.py` |
| RNF-06 | **Robustez del runtime**: si el worker muere o no responde en **15 s**, se reinicia o se cae a ejecución one-shot. | `runtime.EXE_TIMEOUT`, `_Worker.ask` |
| RNF-07 | **Pruebas automatizadas** del lenguaje y del IDE; no se considera terminado un cambio sin pasarlas. | `tests.py`, `tests_ide.py` |
| RNF-08 | **Interfaz en español**, coherente con las palabras clave del lenguaje. | menús, etiquetas, mensajes de error |
| RNF-09 | **Consola legible**: los `.bat` usan UTF-8 (`chcp 65001`). | `build.bat`, `IDE.bat` |
| RNF-10 | **Reproducibilidad del build**: un solo comando genera CLI, IDE e instalador y detiene el proceso si algo falla. | `build.bat` |

---

## 8. Supuestos y restricciones

- Windows 10/11 de 64 bits (el instalador declara `x64compatible`).
- El usuario puede abrir una terminal nueva (para que el PATH surta efecto).
- El IDE web es **local y opcional**: no está pensado para exponerlo en red.
- Python 3.13+ para desarrollar (probado con 3.14.4); `py` o `python` en el PATH.

## 9. Criterios de aceptación

Un cambio se acepta si:

1. `py -u tests.py` termina con `OK — todos los tests pasaron`.
2. `py tests_ide.py` termina con `resultado: OK`.
3. Si toca la versión, se cumple el [checklist de DESARROLLO.md](DESARROLLO.md#checklist-de-versión).
4. Si toca la compilación, `build.bat` acaba con `OK: dist\eco.exe, dist\eco-ide.exe`
   (y `dist\eco-setup.exe` si hay Inno Setup).
