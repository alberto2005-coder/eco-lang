# eco

[![Release](https://img.shields.io/github/v/release/alberto2005-coder/eco-lang?label=eco)](https://github.com/alberto2005-coder/eco-lang/releases/latest)
[![Python](https://img.shields.io/badge/Python-3%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/IDE-Tkinter-FFD43B?logo=python&logoColor=black)](https://docs.python.org/3/library/tkinter.html)
[![GPL-3.0](https://img.shields.io/badge/Licencia-GPL--3.0-blue)](LICENSE)

[Español](#español) · [English](#english)

---

## Español

### Índice

- [Descripción](#descripción)
- [Instalación](#instalación)
- [Inicio rápido](#inicio-rápido)
- [El lenguaje](#el-lenguaje)
- [Tipos y expresiones](#tipos-y-expresiones)
- [Diccionarios](#diccionarios)
- [Módulos](#módulos)
- [Funciones incorporadas](#funciones-incorporadas)
- [Gramática (EBNF)](#gramática-ebnf)
- [Mensajes de error](#mensajes-de-error)
- [CLI](#cli)
- [IDE de escritorio](#ide-de-escritorio)
- [Depurador](#depurador)
- [IDE web](#ide-web)
- [Uso sin instalar](#uso-sin-instalar)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Documentación](#documentación)
- [Novedades de la 0.4.0](#novedades-de-la-040)
- [Licencia](#licencia)

### Descripción

**eco** es un lenguaje de programación propio con su intérprete (**lexer → parser → evaluador**), un **IDE de escritorio**, una **CLI `eco`**, un **IDE web** opcional y un **instalador para Windows**. Sus palabras clave están **en español**: ese es su sello distintivo.

```text
variable nombre = "Mundo";
escribe "Hola, ${nombre}!";
```

**Descarga:** [`eco-setup.exe`](https://github.com/alberto2005-coder/eco-lang/releases/latest)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Léxico | `lexer.py` | Texto → **tokens** (`variable`, `10`, `+`, `;`…) |
| Sintáctico | `parser.py` | Descenso recursivo → **AST** |
| Evaluador | `interpreter.py` | Ámbitos, bucles, funciones, listas, diccionarios, `${}`, `entrada()` |
| Núcleo | `runtime.py` | Empaqueta las tres fases para CLI, IDE y servidor |
| CLI | `main.py` | `eco archivo`, `eco`, `eco -e`, `eco --analyze`, `eco --server` |
| IDE | `ide.py` | Editor, depurador, consola y vistas de Tokens/AST con tkinter |
| Tests | `tests.py`, `tests_ide.py` | Las tres fases y el editor del IDE |

### Instalación

Todo está compilado: **no necesitas Python**.

1. Descarga **[`eco-setup.exe`](https://github.com/alberto2005-coder/eco-lang/releases/latest)** (o usa `dist\eco-setup.exe` si lo compilaste tú).
2. Ejecútalo; no pide administrador.
3. Abre una terminal **nueva**.

El **IDE** aparece en el Menú Inicio como *eco IDE* y los archivos `.eco` se abren con doble clic. Para desinstalar: *Menú Inicio → eco → Desinstalar eco* (borra programa, PATH, accesos directos y asociación de archivos).

**Compilar desde cero**

```bash
build.bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss
```

`build.bat` genera `eco.exe`, `eco-ide.exe` y el instalador; detecta Inno Setup 6 y 7. Los `.bat` son solo para desarrollo.

### Inicio rápido

```bash
eco --version                 # 0.4.0
eco -e "escribe 2 + 3 * 4;"   # 14
eco ejemplos\saludo.eco       # ejecuta un archivo
eco                           # REPL
```

En el IDE, `F5` ejecuta el programa abierto.

### El lenguaje

**Palabras clave reservadas:**

```text
variable  const  escribe  si  sino  mientras  para  en
funcion   devuelve  romper  continuar
verdadero  falso  nulo  y  o  no
importar  como
```

`y`, `o`, `no`, `en`, `importar` y `como` están reservadas: no sirven como nombres de variable.

**Instrucciones:**

```text
variable edad = 30;              // declaración mutable
const PI = 3.1416;               // constante, no se puede modificar
edad = edad + 1;                 // asignación
escribe "año", 2026;             // varios valores separados por espacio

si (cond) { ... } sino si (...) { ... } sino { ... }
mientras (cond) { ... }
para (variable i = 0; i < 10; i = i + 1) { ... }   // clásico
para (x en [1, 2, 3]) { ... }                      // listas y diccionarios
romper;  continuar;

funcion doble(n) { devuelve n * 2; }
doble(21);
```

### Tipos y expresiones

Tipos: **número** (`10`, `3.14`), **texto** (`"hola"`), **booleano** (`verdadero`, `falso`), **lista** (`[1, 2, 3]`), **diccionario** (`{"a": 1}`), **nulo** y **función**.

```text
+ - * / % ^            // ^ es potencia y asocia por la derecha: 2^3^2 = 512
== != < <= > >=
y  o  no               // cortocircuito: falso y (1/0 == 0) no revienta
lista[0]               // índice; los negativos cuentan desde el final
texto[1]               // un carácter
d["clave"]             // índice de diccionario
[1, 2] + [3]           // concatenación de listas
```

**Textos con estilo:**

```text
variable nombre = "Ana";
escribe "Hola, ${nombre} tienes ${10 * 3} puntos";   // interpolación
escribe 'comillas simples también';                  // ' y " son equivalentes
escribe "${persona['nombre']}";                      // simples dentro de ${}
escribe "salto\nde línea";                           // \n \t \" \\
escribe "literal \${no se interpola}";               // \$
```

### Diccionarios

```text
variable persona = {nombre: "Ana", edad: 30, idiomas: ["es", "en"]};
escribe persona["nombre"];
persona["pais"] = "España";        // crea la clave si no existe
escribe longitud(persona);         // 3
escribe claves(persona);           // ["nombre", "edad", "idiomas", "pais"]
escribe valores(persona);
para (k en persona) { escribe "${k}"; }   // recorre las claves
escribe tipo(persona);             // "diccionario"
```

### Módulos

```text
importar "utilidades";                      // relativo a quien importa
importar "modulos/utilidades.eco" como u;   // con extensión y alias

escribe utilidades.PI;         // lo importado es un diccionario
escribe utilidades.doble(21);  // con sus funciones
escribe u.doble(3);            // el alias apunta al mismo módulo
```

- La ruta se resuelve desde el archivo que importa, con o sin `.eco`.
- El módulo se ejecuta **una sola vez**, aunque lo importen varios programas o se repita con y sin alias.
- Exporta sus `variable`, `const` y `funcion` como claves de un diccionario: se leen con punto y aceptan `claves`, `longitud`, etc.
- Ejemplo completo: `ejemplos/importar.eco`, que usa `ejemplos/modulos/utilidades.eco`.

**Leer del teclado:**

```text
variable nombre = entrada("¿Cómo te llamas? ");
variable edad = numero(entrada("¿Qué edad tienes? "));
escribe "${nombre} tiene ${edad} años";
```

En la terminal se escribe en la consola; en el IDE de escritorio se abre un diálogo. El IDE web no lo soporta: usa la terminal o el IDE de escritorio.

### Funciones incorporadas

| Función | Qué hace |
|---|---|
| `entrada([msg])` | Lee una línea por teclado |
| `longitud(x)` | Número de elementos o de caracteres |
| `rango(n)` / `rango(a, b)` / `rango(a, b, paso)` | Lista de números |
| `agregar(lista, v)` | Añade `v` al final |
| `claves(d)` / `valores(d)` | Claves o valores de un diccionario |
| `texto(x)` | Convierte a texto |
| `numero("3,5")` | Convierte a número (coma o punto) |
| `tipo(x)` | `"número"`, `"texto"`, `"booleano"`, `"lista"`, `"diccionario"`, `"nulo"`, `"función"` |

### Gramática (EBNF)

```text
programa    := instrucción*
instrucción := escribe expresión ("," expresión)* ";"
             | ("variable" | "const") IDENT "=" expresión ";"
             | IDENT "=" expresión ";"
             | IDENT "[" expresión "]" "=" expresión ";"
             | si "(" expresión ")" instrucción (sino instrucción)?
             | mientras "(" expresión ")" instrucción
             | para "(" ("variable" IDENT "=" expresión ";" [expresión] ";" [paso]
                       | IDENT en expresión) ")" instrucción
             | funcion IDENT "(" (IDENT ("," IDENT)*)? ")" (bloque | "=" expresión ";")
             | devuelve [expresión] ";" | romper ";" | continuar ";"
             | bloque | expresión ";"

bloque      := "{" instrucción* "}"
expresión   := o
o           := y (o y)*
y           := comparación (y comparación)*
comparación := término (("=="|"!="|"<"|"<="|">"|">=") término)*
término     := factor (("+"|"-") factor)*
factor      := unario (("*"|"/"|"%") unario)*
unario      := ("-"|no) unario | potencia
potencia    := postfix ("^" unario)?          // asociativa por la derecha
postfix     := primario ("[" expresión "]" | "(" argumentos ")")*
primario    := NUMBER | CADENA | verdadero | falso | nulo | IDENT
             | "[" (expresión ("," expresión)*)? "]"
             | "{" (clave ":" expresión ("," clave ":" expresión)*)? "}"
             | "(" expresión ")"
clave       := IDENT | CADENA
```

### Mensajes de error

Siempre con línea y columna, y en la fase que corresponda:

```text
Error: [línea 3, columna 12] Carácter inesperado '@'
Error: [línea 5, columna 9] Falta ';' al final de la instrucción (encontrado: EOF)
Error: [línea 7] 'salario' no está declarada
Error: [línea 9] 'PI' es una constante y no se puede modificar
Error: [línea 12] Índice fuera de rango (7) al acceder: la lista tiene 3 elemento(s)
Error: [línea 15] La clave 'peso' no existe en el diccionario (tiene: "nombre", "edad")
```

### CLI

| Comando | Qué hace |
|---|---|
| `eco archivo.eco` | Ejecuta un programa |
| `eco` | REPL interactiva |
| `eco -e "código"` | Evalúa una expresión o instrucción |
| `eco --analyze archivo` | Devuelve el análisis en JSON (tokens y AST) |
| `eco --server` | Levanta el IDE web |
| `eco --version` | Muestra la versión |

Los códigos de salida y el esquema del JSON están en [docs/GUIA-DE-LA-CLI.md](docs/GUIA-DE-LA-CLI.md).

### IDE de escritorio

| Tecla | Acción |
|---|---|
| `Ctrl+Z` / `Ctrl+Y` | Deshacer / rehacer |
| `Ctrl+F` | Buscar (contador `3/12`, `◀` `▶`, `Aa` para mayúsculas) |
| `Ctrl+H` | Buscar y reemplazar (uno o todos) |
| `F3` / `Shift+F3` | Siguiente / anterior coincidencia |
| `Ctrl+A` | Seleccionar todo |
| `Ctrl+G` | Ir a la línea |
| `Esc` | Cierra la búsqueda o detiene la depuración |

`Enter` en la caja salta a la siguiente coincidencia y `Shift+Enter` a la anterior; con la barra cerrada, `F3` la reabre con el último término. Las coincidencias se resaltan al escribir y la actual usa otro color. El clic derecho abre el menú contextual con los atajos entre paréntesis.

### Depurador

| Tecla | Acción |
|---|---|
| `F5` | Ejecutar |
| `F9` | Depurar desde la primera instrucción |
| `F10` | Paso a paso |
| `F11` | Continuar hasta el próximo punto de ruptura |
| `Esc` | Detener |

Haz clic en los **números de línea** para marcar o quitar puntos de ruptura. La pestaña **Variables** muestra los valores en cada paso y el editor resalta la línea detenida.

### IDE web

```bash
py server.py      # http://127.0.0.1:8787
```

Es opcional y tiene limitaciones: no soporta `entrada()` ni acceso libre al sistema de archivos, y `importar` solo acepta nombres dentro de `ejemplos/`. Detalles y endpoints en [docs/GUIA-DEL-SERVIDOR-WEB.md](docs/GUIA-DEL-SERVIDOR-WEB.md).

### Uso sin instalar

Requiere **Python 3 con tkinter**.

```bash
py main.py ejemplos/saludo.eco   # ejecutar un archivo
py main.py                       # REPL
py ide.py                        # IDE de escritorio
py tests.py                      # tests del intérprete
py tests_ide.py                  # tests del editor (abre la ventana)
py server.py                     # IDE web
```

### Estructura del proyecto

```text
eco-lang/
├── lexer.py · parser.py · interpreter.py · runtime.py
├── main.py            # CLI y REPL
├── ide.py             # IDE de escritorio
├── server.py          # IDE web
├── tests.py · tests_ide.py
├── build.bat · instalador.iss
├── ejemplos/          # Programas de ejemplo, incluidos módulos
├── web/index.html     # Interfaz del IDE web
├── docs/              # Documentación completa
├── LICENSE
└── README.md
```

### Documentación

| Documento | Contenido |
|---|---|
| [docs/REQUISITOS.md](docs/REQUISITOS.md) | Requisitos funcionales y no funcionales, alcance y criterios de aceptación |
| [docs/INSTALACION.md](docs/INSTALACION.md) | Instalador, uso sin instalar, IDE web y problemas comunes |
| [docs/GUIA-DEL-LENGUAJE.md](docs/GUIA-DEL-LENGUAJE.md) | Tipos, instrucciones, métodos, gramática EBNF y errores |
| [docs/GUIA-DEL-IDE.md](docs/GUIA-DEL-IDE.md) | Interfaz, atajos, buscar/reemplazar y depurador |
| [docs/GUIA-DE-LA-CLI.md](docs/GUIA-DE-LA-CLI.md) | Comandos, códigos de salida, REPL y JSON de `--analyze` |
| [docs/GUIA-DEL-SERVIDOR-WEB.md](docs/GUIA-DEL-SERVIDOR-WEB.md) | Endpoints, seguridad y límites del IDE web |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Flujo lexer → parser → evaluador y cómo ampliar el lenguaje |
| [docs/DESARROLLO.md](docs/DESARROLLO.md) | Tests, PyInstaller, Inno Setup y checklist de versión |

### Novedades de la 0.4.0

- Editor con **deshacer/rehacer**, **buscar y reemplazar**, `Ctrl+A`, `Ctrl+G` y menú contextual.
- Corrección de `Ctrl+H` dentro de la caja de búsqueda y de la selección al reabrir la barra.
- `tests_ide.py`: 36 comprobaciones del editor y del modal de guardado.

Versiones anteriores: modal Guardar/Descartar/Cancelar, ejemplo de módulos, diccionarios con métodos, `importar` con alias, `mientras` con `i++` y depuración paso a paso.

### Licencia

**GNU General Public License v3.0 (GPL-3.0)** — consulta [LICENSE](LICENSE). Programa libre: puedes redistribuirlo y modificarlo bajo los términos de la GPL publicada por la Free Software Foundation, versión 3 o posterior. © 2026 Alberto Ortiz.

---

## English

### Table of contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick start](#quick-start)
- [The language](#the-language)
- [Types and expressions](#types-and-expressions)
- [Dictionaries](#dictionaries)
- [Modules](#modules)
- [Built-in functions](#built-in-functions)
- [Grammar (EBNF)](#grammar-ebnf)
- [Error messages](#error-messages)
- [CLI](#cli)
- [Desktop IDE](#desktop-ide)
- [Debugger](#debugger)
- [Web IDE](#web-ide)
- [Running without installing](#running-without-installing)
- [Project structure](#project-structure)
- [Documentation](#documentation)
- [What's new in 0.4.0](#whats-new-in-040)
- [License](#license)

### Overview

**eco** is a custom programming language with its own interpreter (**lexer → parser → evaluator**), a **desktop IDE**, an **`eco` CLI**, an optional **web IDE** and a **Windows installer**. Its keywords are **in Spanish** — that is its signature.

```text
variable nombre = "Mundo";
escribe "Hola, ${nombre}!";
```

**Download:** [`eco-setup.exe`](https://github.com/alberto2005-coder/eco-lang/releases/latest)

| Piece | File | What it does |
|---|---|---|
| Lexer | `lexer.py` | Text → **tokens** (`variable`, `10`, `+`, `;`…) |
| Parser | `parser.py` | Recursive descent → **AST** |
| Evaluator | `interpreter.py` | Scopes, loops, functions, lists, dictionaries, `${}`, `entrada()` |
| Core | `runtime.py` | Bundles the three phases for CLI, IDE and server |
| CLI | `main.py` | `eco file`, `eco`, `eco -e`, `eco --analyze`, `eco --server` |
| IDE | `ide.py` | Editor, debugger, console and Tokens/AST views with tkinter |
| Tests | `tests.py`, `tests_ide.py` | The three phases and the IDE editor |

### Installation

Everything is precompiled: **you do not need Python**.

1. Download **[`eco-setup.exe`](https://github.com/alberto2005-coder/eco-lang/releases/latest)** (or use `dist\eco-setup.exe` if you built it yourself).
2. Run it; no admin rights required.
3. Open a **new** terminal.

The **IDE** appears in the Start Menu as *eco IDE* and `.eco` files open on double-click. To uninstall: *Start Menu → eco → Uninstall eco* (removes the program, PATH entry, shortcuts and file association).

**Build from source**

```bash
build.bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss
```

`build.bat` produces `eco.exe`, `eco-ide.exe` and the installer; it detects Inno Setup 6 and 7. The `.bat` files are for development only.

### Quick start

```bash
eco --version                 # 0.4.0
eco -e "escribe 2 + 3 * 4;"   # 14
eco ejemplos\saludo.eco       # run a file
eco                           # REPL
```

In the IDE, `F5` runs the open program.

### The language

**Reserved keywords:**

```text
variable  const  escribe  si  sino  mientras  para  en
funcion   devuelve  romper  continuar
verdadero  falso  nulo  y  o  no
importar  como
```

`y`, `o`, `no`, `en`, `importar` and `como` are reserved: they cannot be used as variable names.

**Statements:**

```text
variable edad = 30;              // mutable declaration
const PI = 3.1416;               // constant, cannot be modified
edad = edad + 1;                 // assignment
escribe "year", 2026;            // several values separated by space

si (cond) { ... } sino si (...) { ... } sino { ... }
mientras (cond) { ... }
para (variable i = 0; i < 10; i = i + 1) { ... }   // classic
para (x en [1, 2, 3]) { ... }                      // lists and dictionaries
romper;  continuar;

funcion doble(n) { devuelve n * 2; }
doble(21);
```

### Types and expressions

Types: **number** (`10`, `3.14`), **text** (`"hola"`), **boolean** (`verdadero`, `falso`), **list** (`[1, 2, 3]`), **dictionary** (`{"a": 1}`), **null** and **function**.

```text
+ - * / % ^            // ^ is power, right-associative: 2^3^2 = 512
== != < <= > >=
y  o  no               // short-circuit: falso y (1/0 == 0) does not crash
lista[0]               // index; negatives count from the end
texto[1]               // a single character
d["clave"]             // dictionary index
[1, 2] + [3]           // list concatenation
```

**String interpolation:**

```text
variable nombre = "Ana";
escribe "Hola, ${nombre} tienes ${10 * 3} puntos";   // interpolation
escribe 'single quotes work too';                    // ' and " are equivalent
escribe "${persona['nombre']}";                      // single quotes inside ${}
escribe "line\nbreak";                               // \n \t \" \\
escribe "literal \${not interpolated}";              // \$
```

### Dictionaries

```text
variable persona = {nombre: "Ana", edad: 30, idiomas: ["es", "en"]};
escribe persona["nombre"];
persona["pais"] = "España";        // creates the key if missing
escribe longitud(persona);         // 3
escribe claves(persona);           // ["nombre", "edad", "idiomas", "pais"]
escribe valores(persona);
para (k en persona) { escribe "${k}"; }   // iterates keys
escribe tipo(persona);             // "diccionario"
```

### Modules

```text
importar "utilidades";                      // relative to the importer
importar "modulos/utilidades.eco" como u;   // with extension and alias

escribe utilidades.PI;         // an import is a dictionary
escribe utilidades.doble(21);  // with its functions
escribe u.doble(3);            // the alias points to the same module
```

- Paths resolve from the importing file, with or without `.eco`.
- A module runs **once**, even if several programs import it or it is imported both with and without an alias.
- It exports its `variable`, `const` and `funcion` as dictionary keys: read them with a dot and use everything dictionaries offer (`claves`, `longitud`…).
- Full example: `ejemplos/importar.eco`, which uses `ejemplos/modulos/utilidades.eco`.

**Reading from the keyboard:**

```text
variable nombre = entrada("What is your name? ");
variable edad = numero(entrada("How old are you? "));
escribe "${nombre} is ${edad} years old";
```

In the terminal it reads from the console; in the desktop IDE it opens a dialog. The web IDE does not support it: use the terminal or the desktop IDE.

### Built-in functions

| Function | What it does |
|---|---|
| `entrada([msg])` | Reads a line from the keyboard |
| `longitud(x)` | Number of items or characters |
| `rango(n)` / `rango(a, b)` / `rango(a, b, step)` | List of numbers |
| `agregar(lista, v)` | Appends `v` |
| `claves(d)` / `valores(d)` | Keys or values of a dictionary |
| `texto(x)` | Converts to text |
| `numero("3,5")` | Converts to number (comma or dot) |
| `tipo(x)` | `"número"`, `"texto"`, `"booleano"`, `"lista"`, `"diccionario"`, `"nulo"`, `"función"` |

### Grammar (EBNF)

```text
program     := statement*
statement   := escribe expression ("," expression)* ";"
             | ("variable" | "const") IDENT "=" expression ";"
             | IDENT "=" expression ";"
             | IDENT "[" expression "]" "=" expression ";"
             | si "(" expression ")" statement (sino statement)?
             | mientras "(" expression ")" statement
             | para "(" ("variable" IDENT "=" expression ";" [expression] ";" [step]
                       | IDENT en expression) ")" statement
             | funcion IDENT "(" (IDENT ("," IDENT)*)? ")" (block | "=" expression ";")
             | devuelve [expression] ";" | romper ";" | continuar ";"
             | block | expression ";"

block       := "{" statement* "}"
expression  := o
o           := y (o y)*
y           := comparison (y comparison)*
comparison  := term (("=="|"!="|"<"|"<="|">"|">=") term)*
term        := factor (("+"|"-") factor)*
factor      := unary (("*"|"/"|"%") unary)*
unary       := ("-"|no) unary | power
power       := postfix ("^" unary)?          // right-associative
postfix     := primary ("[" expression "]" | "(" arguments ")")*
primary     := NUMBER | STRING | verdadero | falso | nulo | IDENT
             | "[" (expression ("," expression)*)? "]"
             | "{" (key ":" expression ("," key ":" expression)*)? "}"
             | "(" expression ")"
key         := IDENT | STRING
```

### Error messages

Always with line and column, and in the matching phase:

```text
Error: [línea 3, columna 12] Carácter inesperado '@'
Error: [línea 5, columna 9] Falta ';' al final de la instrucción (encontrado: EOF)
Error: [línea 7] 'salario' no está declarada
Error: [línea 9] 'PI' es una constante y no se puede modificar
Error: [línea 12] Índice fuera de rango (7) al acceder: la lista tiene 3 elemento(s)
Error: [línea 15] La clave 'peso' no existe en el diccionario (tiene: "nombre", "edad")
```

The messages themselves are in Spanish, like the language.

### CLI

| Command | What it does |
|---|---|
| `eco file.eco` | Runs a program |
| `eco` | Interactive REPL |
| `eco -e "code"` | Evaluates an expression or statement |
| `eco --analyze file` | Returns the analysis as JSON (tokens and AST) |
| `eco --server` | Starts the web IDE |
| `eco --version` | Prints the version |

Exit codes and the JSON schema are documented in [docs/GUIA-DE-LA-CLI.md](docs/GUIA-DE-LA-CLI.md) (Spanish).

### Desktop IDE

| Key | Action |
|---|---|
| `Ctrl+Z` / `Ctrl+Y` | Undo / redo |
| `Ctrl+F` | Find (counter `3/12`, `◀` `▶`, `Aa` for case) |
| `Ctrl+H` | Find and replace (one or all) |
| `F3` / `Shift+F3` | Next / previous match |
| `Ctrl+A` | Select all |
| `Ctrl+G` | Go to line |
| `Esc` | Close the search bar or stop debugging |

`Enter` in the box jumps to the next match and `Shift+Enter` to the previous one; with the bar closed, `F3` reopens it with the last term. Matches are highlighted as you type and the current one uses a different colour. Right-clicking opens the context menu with shortcuts in parentheses.

### Debugger

| Key | Action |
|---|---|
| `F5` | Run |
| `F9` | Debug from the first statement |
| `F10` | Step |
| `F11` | Continue to the next breakpoint |
| `Esc` | Stop |

Click the **line numbers** to set or clear breakpoints. The **Variables** tab shows values at each step and the editor highlights the paused line.

### Web IDE

```bash
py server.py      # http://127.0.0.1:8787
```

It is optional and limited: it does not support `entrada()` or free filesystem access, and `importar` only accepts names inside `ejemplos/`. Details and endpoints in [docs/GUIA-DEL-SERVIDOR-WEB.md](docs/GUIA-DEL-SERVIDOR-WEB.md) (Spanish).

### Running without installing

Requires **Python 3 with tkinter**.

```bash
py main.py ejemplos/saludo.eco   # run a file
py main.py                       # REPL
py ide.py                        # desktop IDE
py tests.py                      # interpreter tests
py tests_ide.py                  # editor tests (opens the window)
py server.py                     # web IDE
```

### Project structure

```text
eco-lang/
├── lexer.py · parser.py · interpreter.py · runtime.py
├── main.py            # CLI and REPL
├── ide.py             # Desktop IDE
├── server.py          # Web IDE
├── tests.py · tests_ide.py
├── build.bat · instalador.iss
├── ejemplos/          # Sample programs, modules included
├── web/index.html     # Web IDE interface
├── docs/              # Full documentation
├── LICENSE
└── README.md
```

### Documentation

| Document | Contents |
|---|---|
| [docs/REQUISITOS.md](docs/REQUISITOS.md) | Functional and non-functional requirements, scope and acceptance criteria |
| [docs/INSTALACION.md](docs/INSTALACION.md) | Installer, running without installing, web IDE and common issues |
| [docs/GUIA-DEL-LENGUAJE.md](docs/GUIA-DEL-LENGUAJE.md) | Types, statements, methods, EBNF grammar and errors |
| [docs/GUIA-DEL-IDE.md](docs/GUIA-DEL-IDE.md) | Interface, shortcuts, find/replace and debugger |
| [docs/GUIA-DE-LA-CLI.md](docs/GUIA-DE-LA-CLI.md) | Commands, exit codes, REPL and the `--analyze` JSON |
| [docs/GUIA-DEL-SERVIDOR-WEB.md](docs/GUIA-DEL-SERVIDOR-WEB.md) | Endpoints, security and web IDE limits |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Lexer → parser → evaluator flow and how to extend the language |
| [docs/DESARROLLO.md](docs/DESARROLLO.md) | Tests, PyInstaller, Inno Setup and release checklist |

All documents are written in Spanish.

### What's new in 0.4.0

- Editor with **undo/redo**, **find and replace**, `Ctrl+A`, `Ctrl+G` and a context menu.
- Fixed `Ctrl+H` inside the search box and the selection behaviour when reopening the bar.
- `tests_ide.py`: 36 checks for the editor and the save dialog.

Earlier versions added the Save/Discard/Cancel dialog, the modules example, dictionary methods, `importar` with aliases, `mientras` with `i++` and step-by-step debugging.

### License

**GNU General Public License v3.0 (GPL-3.0)** — see [LICENSE](LICENSE). Free software: you may redistribute and modify it under the terms of the GPL as published by the Free Software Foundation, version 3 or later. © 2026 Alberto Ortiz.
