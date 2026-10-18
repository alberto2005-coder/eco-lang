# Guía del lenguaje eco

De cero a módulos. Al final está la referencia: todos los métodos, la gramática
EBNF y los mensajes de error.

---

## 1. Primer programa

```text
variable nombre = "Mundo";
escribe "Hola, ${nombre}!";
```

Guarda como `hola.eco` y ejecuta:

```bash
eco hola.eco        # con el instalador
py main.py hola.eco # desde la fuente
```

O en el IDE: `F5`.

**Tres reglas que lo explican todo:**

1. Las instrucciones terminan en **`;`**.
2. Los bloques van entre **`{ }`**.
3. Las palabras clave están **en español** y son reservadas.

---

## 2. Sintaxis básica

```text
// comentario de una línea
variable edad = 30;         // declaración mutable
const PI = 3.1416;          // constante: escribir sobre ella es error
edad = edad + 1;            // asignación
```

- El `;` cierra instrucciones, **no** líneas: puede haber varias en una línea
  o una instrucción en varias.
- `si` y `mientras` aceptan la condición **con o sin paréntesis**:

```text
si (edad >= 18) { escribe "mayor"; }
si edad >= 18 { escribe "mayor"; }          // lo mismo
mientras (quedan > 0) { quedan = quedan - 1; }
```

- `para` **sí** necesita paréntesis.
- El fichero puede empezar con BOM (lo añaden algunos editores de Windows):
  se ignora.

---

## 3. Tipos

| Tipo | Ejemplos |
|---|---|
| número | `10`, `3.14`, `-2` |
| texto | `"hola"`, `'también'` |
| booleano | `verdadero`, `falso` |
| lista | `[1, 2, 3]`, `[]` |
| diccionario | `{"a": 1}`, `{nombre: "Ana"}` |
| nulo | `nulo` |
| función | `doble` (el nombre de una `funcion` definida) |

`tipo(x)` devuelve su nombre como texto.

---

## 4. Salida

```text
escribe "Hola";
escribe "año", 2026;              // varios valores, separados por espacio
escribe 2 + 3 * 4;                // 14
escribe [1, 2], {"a": 1};         // también listas y diccionarios
```

---

## 5. Operadores

### Aritméticos

```text
+  -  *  /  %  ^        // ^ es potencia
```

- `^` va **por la derecha**: `2^3^2` es `2^(3^2)` = `512`.
- `/` entre cero y `%` entre cero son errores con mensaje claro.
- Todo se guarda como número con decimales (no hay enteros y flotantes
  separados).

### Comparación

```text
==  !=  <  <=  >  >=
```

Solo se comparan números con números y textos con textos.

### Lógicos

```text
y   o   no
```

Funcionan **solo con booleanos** y con evaluación corta: en `falso y (1/0 == 0)`
nunca se llega a evaluar la parte derecha, así que no revienta.

### Concatenación con `+`

`+` combina números con números, textos con textos o listas con listas; cualquier
otra mezcla da un error que lo dice:

```text
escribe "a" + "b";        // "ab"
escribe [1] + [2, 3];      // [1, 2, 3]
escribe "a" + 1;           // Error: '+' no puede combinar texto y número...
```

### Índice

```text
lista[0]        // primer elemento ([-1] es el último)
texto[1]        // un carácter
d["clave"]      // por clave
d.clave         // lo mismo, por punto
```

---

## 6. Control de flujo

### `si` / `sino si` / `sino`

```text
si (edad >= 18) {
    escribe "mayor de edad";
} sino si (edad >= 13) {
    escribe "adolescente";
} sino {
    escribe "niño";
}
```

### `mientras`

```text
variable i = 0;
mientras (i < 3) {
    escribe i;
    i++;
}
```

### `para` clásico

```text
para (variable i = 0; i < 5; i = i + 1) { escribe i; }
para (variable i = 0; i < 5; i++) { escribe i; }      // paso compacto
para (; i < 3; ) { ... }                              // partes opcionales
```

### `para ... en` (listas y diccionarios)

```text
para (n en [1, 2, 3]) { escribe n; }
para (clave en persona) { escribe "${clave}"; }   // en un diccionario: las claves
para (clave en persona) { escribe persona[clave]; }
```

Solo admite **lista o diccionario**: recorrer un texto con `para x en "hola"` da
un error (`'para x en ...' necesita una lista o un diccionario`). Para recorrer
un texto, usa sus índices:

```text
variable frase = "hola";
para (i en rango(longitud(frase))) { escribe frase[i]; }
```

### `romper` y `continuar`

```text
para (x en rango(10)) {
    si (x == 5) { romper; }
    si (x % 2 == 0) { continuar; }
    escribe x;
}
```

---

## 7. Funciones

```text
funcion doble(n) {
    devuelve n * 2;
}
escribe doble(21);        // 42
```

Corto, cuando el cuerpo es una sola devolución:

```text
funcion triple(n) = n * 3;
```

Recursión:

```text
funcion factorial(n) {
    si (n <= 1) { devuelve 1; }
    devuelve n * factorial(n - 1);
}
```

**Las funciones son valores**: se pueden guardar en variables y pasar.

```text
variable f = doble;
escribe f(21);            // 42
```

Sin `devuelve`, la función devuelve `nulo`.

---

## 8. Listas

```text
variable notas = [7, 8.5, 6, 9.5];
escribe notas[0];            // 7
escribe notas[-1];           // 9.5  (desde el final)
escribe longitud(notas);     // 4
notas[0] = 8;                // por índice
agregar(notas, 10);          // añade al final
escribe notas + [11];        // concatenación
```

Recorrer:

```text
para (n en notas) { escribe n; }
```

---

## 9. Textos

```text
variable nombre = "Ana";
escribe "Hola, ${nombre} tienes ${10 * 3} puntos";  // interpolación
escribe 'comillas simples también';                  // ' y " son equivalentes
escribe "${persona['nombre']}";                      // simples dentro de ${}
escribe "salto\nde línea";                           // \n \t \" \\
escribe "literal \${no se interpola}";               // \$ deja el ${} tal cual
```

Solo las comillas dobles interpolan; entre `'...'` todo es literal.

---

## 10. Diccionarios

```text
variable persona = {nombre: "Ana", edad: 30, idiomas: ["es", "en"]};
escribe persona["nombre"];   // Ana
escribe persona.nombre;      // lo mismo, por punto
persona.pais = "España";     // crea la clave si no existía
escribe longitud(persona);   // 4
escribe claves(persona);     // ["nombre", "edad", "idiomas", "pais"]
escribe valores(persona);
para (k en persona) { escribe k; }
escribe persona.tiene("edad");        // verdadero
```

---

## 11. Módulos

`ejemplos/modulos/utilidades.eco`:

```text
const PI = 3.1416;
funcion doble(n) { devuelve n * 2; }
variable saludo = "hola desde el módulo";
```

Quien importa:

```text
importar "utilidades";                      // relativo a quien importa
importar "modulos/utilidades.eco" como u;   // con extensión y alias

escribe utilidades.PI;
escribe utilidades.doble(21);
escribe u.doble(3);        // el alias apunta al mismo módulo
```

Reglas:

- La ruta es **relativa al fichero que importa**, con o sin `.eco`.
- Exporta sus `variable`, `const` y `funcion` como claves de un diccionario:
  se leen con punto y sirven todas las funciones de diccionario.
- El módulo se ejecuta **una sola vez**, aunque lo importen varios programas.
- Si no existe, el error dice qué módulo y **dónde lo buscó**.

---

## 12. Leer del teclado

```text
variable nombre = entrada("¿Cómo te llamas? ");
variable edad = numero(entrada("¿Qué edad tienes? "));
escribe "${nombre} tiene ${edad} años";
```

Dónde se responde:

| Entorno | Cómo |
|---|---|
| Terminal (`eco.exe`) | Se escribe en la consola |
| IDE de escritorio | Se abre un diálogo |
| IDE web | **No disponible**: devuelve un error claro |

---

## 13. Funciones incorporadas

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

---

## 14. Métodos (se usan con punto)

### Texto

| Método | Ejemplo |
|---|---|
| `.longitud()` | `"hola".longitud()` → `4` |
| `.mayusculas()` / `.minusculas()` | `"hola".mayusculas()` → `"HOLA"` |
| `.recortar()` | `"  x  ".recortar()` → `"x"` |
| `.contiene(t)` | `"hola".contiene("ol")` → `verdadero` |
| `.empiezaPor(t)` / `.terminaPor(t)` | `"hola".empiezaPor("ho")` |
| `.reemplazar(a, b)` | `"a-b".reemplazar("-", "+")` → `"a+b"` |
| `.partir(sep)` | `"a,b".partir(",")` → `["a", "b"]` |
| `.indice(t)` | `"hola".indice("ol")` → `1` |

### Lista

| Método | Ejemplo |
|---|---|
| `.longitud()` | `notas.longitud()` |
| `.agregar(v)` | `notas.agregar(10)` |
| `.invertir()` / `.ordenar()` | `notas.ordenar();` |
| `.contiene(v)` | `notas.contiene(7)` |
| `.indice(v)` | `notas.indice(7)` → `0` (`-1` si no está) |
| `.primero()` / `.ultimo()` | `notas.primero()` (error si la lista está vacía) |
| `.borrar(i)` | `notas.borrar(0)` → devuelve el elemento borrado |
| `.vaciar()` | `notas.vaciar()` |

`.agregar`, `.invertir`, `.ordenar`, `.borrar` y `.vaciar` **modifican la propia
lista** (se usan como instrucción: `notas.ordenar();`).

### Diccionario

| Método | Ejemplo |
|---|---|
| `.longitud()` | `persona.longitud()` |
| `.claves()` / `.valores()` | `persona.claves()` |
| `.tiene(k)` | `persona.tiene("nombre")` |
| `.borrar(k)` | `persona.borrar("peso")` → devuelve el valor borrado |
| `.fusionar(otro)` | `persona.fusionar({"pais": "ES"})` → **devuelve un diccionario nuevo**, sin tocar el original |

### Número

| Método | Ejemplo |
|---|---|
| `.redondear()` / `.redondear(n)` | `3.7.redondear()` → `4` |
| `.absoluto()` | `(-5).absoluto()` → `5` |
| `.piso()` / `.techo()` | `3.2.piso()` → `3` |

---

## 15. Gramática (EBNF)

```text
programa    := instrucción*
instrucción := escribe expresión ("," expresión)* ";"
             | ("variable" | "const") IDENT "=" expresión ";"
             | IDENT "=" expresión ";"
             | IDENT "[" expresión "]" "=" expresión ";"
             | IDENT "." IDENT "=" expresión ";"
             | IDENT ("++" | "--") ";"
             | si "(" expresión ")" instrucción (sino instrucción)?
             | mientras "(" expresión ")" instrucción
             | para "(" ("variable" IDENT "=" expresión ";" [expresión] ";" [paso]
                       | IDENT en expresión) ")" instrucción
             | importar CADENA (como IDENT)? ";"
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
postfix     := primario ("[" expresión "]" | "(" argumentos ")" | "." IDENT)*
primario    := NUMBER | CADENA | verdadero | falso | nulo | IDENT
             | "[" (expresión ("," expresión)*)? "]"
             | "{" (clave ":" expresión ("," clave ":" expresión)*)? "}"
             | "(" expresión ")"
clave       := IDENT | CADENA
CADENA      := '"' (cualquier cosa | escape | '${' ... '}')* '"'
             | "'" (cualquier cosa | escape)* "'"
```

---

## 16. Mensajes de error

Siempre con la fase que corresponde y la posición:

```text
Error: [línea 3, columna 12] Carácter inesperado '@'
Error: [línea 5, columna 9] Falta ';' al final de la instrucción (encontrado: EOF)
Error: [línea 7] 'salario' no está declarada
Error: [línea 9] 'PI' es una constante y no se puede modificar
Error: [línea 12] Índice fuera de rango (7) al acceder: la lista tiene 3 elemento(s)
Error: [línea 15] La clave 'peso' no existe en el diccionario (tiene: "nombre", "edad")
```

| Fase | Quién lo detecta | Ejemplos |
|---|---|---|
| `lex` | `lexer.py` | carácter inesperado, texto sin cerrar |
| `parse` | `parser.py` | falta `}`, falta `;`, expresión incompleta |
| `run` | `interpreter.py` | variable no declarada, constante, tipos, índices |

En el IDE, **Salida** lo muestra en rojo; en `eco --analyze` aparece en la
clave `error` junto a `phase`.

---

## 17. Ejemplos incluidos

Están en `ejemplos/` y se cargan desde el combo del IDE.

| Fichero | Qué enseña |
|---|---|
| `saludo.eco` | Primer programa: variables y `escribe` |
| `operaciones.eco` | Precedencia, potencias, constantes y lógicos |
| `bucles.eco` | `mientras`, `para`, `romper`, `continuar` |
| `funciones.eco` | Definición, parámetros, devolución y recursión |
| `listas.eco` | Literales, índice, `longitud`, `rango` y recorridos |
| `diccionarios.eco` | Pares clave: valor y sus métodos |
| `entrada.eco` | `entrada()` en terminal y diálogo |
| `importar.eco` | Módulos (usa `modulos/utilidades.eco`) |
| `inventario.eco` | Programa completo: lo nuevo de las últimas versiones |

---

## Siguiente paso

- Atajos y depurador: [GUIA-DEL-IDE.md](GUIA-DEL-IDE.md)
- Scripts en terminal: [GUIA-DE-LA-CLI.md](GUIA-DE-LA-CLI.md)
