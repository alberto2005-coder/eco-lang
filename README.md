# eco

**eco** es un lenguaje de programación propio, con su intérprete
(lexer → parser → evaluador), su **IDE de escritorio**, su **CLI `eco`** y su
**instalador**. Las palabras clave son **en español**: ese es el sello.

**Código y documentación:** <https://github.com/alberto2005-coder/eco-lang>

```text
hola.eco                           →  eco  (o F5 en el IDE)
```
```text
variable nombre = "Mundo";
escribe "Hola, ${nombre}!";
```

| Pieza | Archivo | Qué hace |
|---|---|---|
| Léxico | `lexer.py` | El texto → **tokens** (`variable`, `10`, `+`, `;`…). |
| Sintáctico | `parser.py` | **Descenso recursivo** → **AST**. |
| Evaluador | `interpreter.py` | Ámbitos, bucles, funciones, listas, diccionarios, `${}`, `entrada()`. |
| Núcleo | `runtime.py` | Empaqueta las 3 fases para CLI/IDE/servidor (+ servidor vivo). |
| CLI | `main.py` | `eco archivo`, `eco`, `eco -e`, `eco --analyze`, `eco --server`. |
| IDE | `ide.py` | Editor + depurador + consola + Tokens/AST (tkinter). |
| Tests | `tests.py` / `tests_ide.py` | Las 3 fases, y el editor del IDE. |
| Docs | `docs/` | Requisitos, guías, arquitectura y desarrollo. |

---

## Documentación

Está en [`docs/`](docs/README.md), con el detalle que este README resume:

| Documento | Qué contiene |
|---|---|
| [docs/REQUISITOS.md](docs/REQUISITOS.md) | Requisitos funcionales (RF) y no funcionales (RNF), alcance y criterios de aceptación |
| [docs/INSTALACION.md](docs/INSTALACION.md) | Instalador, uso sin instalar, IDE web y problemas comunes |
| [docs/GUIA-DEL-LENGUAJE.md](docs/GUIA-DEL-LENGUAJE.md) | De cero a módulos: tipos, instrucciones, métodos, gramática EBNF y errores |
| [docs/GUIA-DEL-IDE.md](docs/GUIA-DEL-IDE.md) | Interfaz, todos los atajos, buscar/reemplazar, menú contextual y depurador |
| [docs/GUIA-DE-LA-CLI.md](docs/GUIA-DE-LA-CLI.md) | Comandos `eco`, códigos de salida, REPL y el JSON de `--analyze` |
| [docs/GUIA-DEL-SERVIDOR-WEB.md](docs/GUIA-DEL-SERVIDOR-WEB.md) | Endpoints, seguridad y limitaciones del IDE web |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Flujo lexer → parser → evaluador, contratos y cómo ampliar el lenguaje |
| [docs/DESARROLLO.md](docs/DESARROLLO.md) | Tests, compilación con PyInstaller e Inno Setup, checklist de versión |

---

## Instalación

Todo está compilado: **no necesitas Python**.

1. Ejecuta **`dist\eco-setup.exe`** (no pide administrador).
2. Abre una terminal **nueva**:

```bash
eco --version                 # 0.4.0
eco -e "escribe 2 + 3 * 4;"   # 14
eco ejemplos\saludo.eco       # ejecuta un archivo
eco                           # REPL
```

3. El **IDE** aparece en el Menú Inicio (*eco IDE*) y los `.eco` se abren
   con doble clic.

Desinstalar: *Menú Inicio → eco → Desinstalar eco*
(borra programa, PATH, accesos directos y asociación).

### Compilar desde cero

```bash
build.bat                                              # eco.exe + eco-ide.exe + instalador
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss   # solo el instalador (6 o 7)
```

> Los `.bat` son solo para desarrollo. Para usar eco basta con el instalador.

---

## El lenguaje

### Palabras clave (reservadas)

```text
variable  const  escribe  si  sino  mientras  para  en
funcion   devuelve  romper  continuar
verdadero  falso  nulo  y  o  no
importar  como
```

> `y`, `o`, `no`, `en`, `importar` y `como` están reservadas: no sirven como
> nombres de variable.

Guía completa con ejemplos y referencia de métodos, gramática y errores:
[**docs/GUIA-DEL-LENGUAJE.md**](docs/GUIA-DEL-LENGUAJE.md).

### Tipos

**número** (`10`, `3.14`) · **texto** (`"hola"`) · **booleano** (`verdadero`,
`falso`) · **lista** (`[1, 2, 3]`) · **diccionario** (`{"a": 1}`) · **nulo** ·
**función**

### Instrucciones

```text
variable edad = 30;              // declaración (mutable)
const PI = 3.1416;               // constante (no se puede modificar)
edad = edad + 1;                 // asignación
escribe "año", 2026;             // varios valores separados por espacio

si (cond) { ... } sino si (...) { ... } sino { ... }
mientras (cond) { ... }
para (variable i = 0; i < 10; i = i + 1) { ... }   // clásico
para (x en [1, 2, 3]) { ... }                      // recorrer listas y diccionarios
romper;  continuar;

funcion doble(n) { devuelve n * 2; }
doble(21);
```

### Expresiones

```text
+ - * / % ^            // ^ es potencia y va por la derecha: 2^3^2 = 512
== != < <= > >=
y  o  no               // evaluación corta: falso y (1/0 == 0) no revienta
lista[0]               // índice (los negativos cuentan desde el final)
texto[1]               // un carácter
d["clave"]             // índice de diccionario
[1, 2] + [3]           // concatenación de listas
```

### Textos con estilo

```text
variable nombre = "Ana";
escribe "Hola, ${nombre} tienes ${10 * 3} puntos";   // interpolación
escribe 'comillas simples también';                  // '  y  "  son equivalentes
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

- La ruta sale del archivo que importa (`ejemplos/`, `ejemplos/modulos/`…),
  con o sin `.eco`.
- El módulo se ejecuta **una sola vez**, aunque lo importen varios programas
  o lo importes dos veces con y sin alias.
- Exporta sus `variable`, `const` y `funcion` como claves de un diccionario:
  se leen con punto y sirve todo lo de diccionarios (`claves`, `longitud`…).
- Ejemplo completo: **`ejemplos\importar.eco`**, que usa
  **`ejemplos\modulos\utilidades.eco`** (está en subcarpeta para no aparecer
  en la lista de ejemplos del IDE).

### Leer del teclado

```text
variable nombre = entrada("¿Cómo te llamas? ");
variable edad = numero(entrada("¿Qué edad tienes? "));
escribe "${nombre} tiene ${edad} años";
```

En la terminal se escribe en la consola; en el IDE de escritorio se abre un
diálogo. (En el IDE web no está disponible: usa la terminal o el IDE de
escritorio.)

### Funciones incorporadas

| Función | Qué hace |
|---|---|
| `entrada([msg])` | Lee una línea por teclado. |
| `longitud(x)` | Nº de elementos de lista/diccionario o caracteres de texto. |
| `rango(n)` / `rango(a, b)` / `rango(a, b, paso)` | Lista de números. |
| `agregar(lista, v)` | Añade `v` al final de `lista`. |
| `claves(d)` / `valores(d)` | Listas con las claves o los valores de un diccionario. |
| `texto(x)` | Convierte a texto. |
| `numero("3,5")` | Convierte a número (admite coma o punto). |
| `tipo(x)` | `"número"`, `"texto"`, `"booleano"`, `"lista"`, `"diccionario"`, `"nulo"`, `"función"`. |

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
CADENA      := '"' (cualquier cosa | escape | '${' ... '}')* '"'
             | "'" (cualquier cosa | escape)* "'"
```

### Mensajes de error

Siempre con línea y columna y en la fase que corresponda:

```text
Error: [línea 3, columna 12] Carácter inesperado '@'
Error: [línea 5, columna 9] Falta ';' al final de la instrucción (encontrado: EOF)
Error: [línea 7] 'salario' no está declarada
Error: [línea 9] 'PI' es una constante y no se puede modificar
Error: [línea 12] Índice fuera de rango (7) al acceder: la lista tiene 3 elemento(s)
Error: [línea 15] La clave 'peso' no existe en el diccionario (tiene: "nombre", "edad")
```

---

## Uso sin instalar

```bash
cd eco
py main.py ejemplos/saludo.eco   # ejecuta un archivo
py main.py                       # REPL
py ide.py                         # IDE de escritorio
py tests.py                       # tests
py tests_ide.py                   # tests del editor del IDE (abre la ventana)
py server.py                      # IDE web opcional (http://127.0.0.1:8787)
```

## Editor del IDE

| Tecla | Qué hace |
|---|---|
| `Ctrl+Z` / `Ctrl+Y` | Deshacer / rehacer |
| `Ctrl+F` | Buscar (contador `3/12`, `◀` `▶` para saltar, `Aa` distingue mayúsculas) |
| `Ctrl+H` | Buscar y reemplazar (uno o todos) |
| `F3` / `Shift+F3` | Siguiente / anterior coincidencia |
| `Ctrl+A` | Seleccionar todo |
| `Ctrl+G` | Ir a la línea |
| `Esc` | Cierra la barra de búsqueda (o detiene la depuración) |

`Enter` en la caja salta a la siguiente coincidencia y `Shift+Enter` a la
anterior; si la barra está cerrada, `F3` la reabre con el último término.
Las coincidencias se resaltan mientras escribes, y la actual en otro color.

El **clic derecho** en el editor abre el menú típico con su atajo entre
paréntesis: Deshacer, Rehacer, Cortar, Copiar, Pegar, Borrar, Seleccionar
todo, Buscar, Reemplazar e Ir a la línea (los que necesitan selección se
deshabilitan solos si no hay texto seleccionado).

## Depurador del IDE

| Tecla | Qué hace |
|---|---|
| `F5` | Ejecuta el programa |
| `F9` | Depura: se detiene en la primera instrucción |
| `F10` | Paso a paso: avanza una instrucción |
| `F11` | Sigue hasta el próximo punto de ruptura |
| `Esc` | Detiene la depuración |

Haz clic en los **números de línea** para marcar o quitar puntos de ruptura.
La pestaña **Variables** muestra los valores en cada paso y la línea donde está
detenido el programa se resalta en el editor.

---

## De la 0.3.0 a la 0.4.0

- [x] Editor con **deshacer/rehacer** (`Ctrl+Z`/`Ctrl+Y`), **buscar y
  reemplazar** (`Ctrl+F`/`Ctrl+H`, `F3`/`Shift+F3`, `Aa` para mayúsculas,
  contador de coincidencias), `Ctrl+A`, `Ctrl+G` y **menú contextual** al clic
  derecho con los atajos entre paréntesis.
- [x] Corregido: `Ctrl+H` dentro de la caja de búsqueda borraba una letra
  (Tk lo tomaba como retroceso) y, al reabrir la barra, la selección del
  editor se comía lo escrito en la caja.
- [x] **`tests_ide.py`**: 36 comprobaciones del editor (deshacer, buscar y
  reemplazar, menú contextual) y del modal de guardado.

---

## De la 0.2.0 a la 0.3.0

- [x] Modal **Guardar / Descartar / Cancelar** al cerrar la ventana, crear un
  archivo nuevo, abrir otro o cargar un ejemplo con cambios sin guardar (y el
  título ahora marca `*` mientras haya cambios).
- [x] Ejemplo de módulos: **`ejemplos\importar.eco`**, que usa
  `ejemplos\modulos\utilidades.eco`.
- [x] El IDE web también entiende `importar` (manda el nombre del ejemplo
  cargado, y solo acepta nombres dentro de `ejemplos/`).
- [x] `build.bat` detecta Inno Setup 6 y 7, y ya **no miente**: si PyInstaller
  falla se detiene con un error en vez de firmar un instalador con `.exe` viejos.
- [x] Tests de módulos en `tests.py` (alias, rutas relativas, ejecución única,
  módulo inexistente) y tests del depurador del IDE.

---

## De la 0.1.0 a la 0.2.0

- [x] Diccionarios con métodos (`persona.nombre`) y listas encadenables.
- [x] Módulos: `importar "otro.eco" [como alias]`, relativos a quien importa.
- [x] `mientras` con contador compacto (`i++`) y `para ... en rango(a, b, paso)`.
- [x] Depuración paso a paso en el IDE.
- [x] Más funciones de texto y de números (`.mayusculas()`, `.redondear()`…).

Todo eso junto en un solo programa de ejemplo: **`ejemplos\inventario.eco`**,
y los módulos en **`ejemplos\importar.eco`** (con
`ejemplos\modulos\utilidades.eco`).

---

## Licencia

**MIT con adenda personalizada** → [LICENSE](LICENSE)

Libre para uso personal, educativo y comercial. Solo hay que conservar el aviso
de autoría (Alberto Ortiz) y no usar el nombre «eco» para avalar una versión
derivada sin permiso. El lenguaje, sus ejemplos y la documentación pueden
ensenarse y publicarse sin más citar el proyecto.
