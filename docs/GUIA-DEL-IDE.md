# Guía del IDE de escritorio

`eco-ide.exe` (o `py ide.py` / `IDE.bat` desde la fuente).

---

## 1. Arranque

| Desde | Cómo |
|---|---|
| Instalado | *Menú Inicio → eco IDE*, doble clic en un `.eco`, o acceso directo del escritorio |
| Fuente | `py ide.py` o `IDE.bat` |
| Sin Python | No se puede: usa el instalador |

El IDE ejecuta el código con `eco.exe` si lo encuentra junto a él; si no, con el
intérprete de Python. Lo indica el **chip de la esquina superior derecha**
(`runtime: eco.exe` / `runtime: python 3.14`).

---

## 2. Interfaz

```
┌ Archivo  Ejecutar  Ayuda ───────────────────────────────────────────┐
│ ▶ Ejecutar (F5)  🐞 Depurar (F9)  Nuevo  Abrir…  Guardar   ejemplo: ▾ │ runtime: eco.exe
├───────────────────────────────┬──────────────────────────────────────┤
│ 🔍 [Buscar]     3/12  ◀ ▶ Aa ✕│  Salida │ Tokens │ AST │ Variables   │
│ (solo con Ctrl+F o Ctrl+H)    │                                      │
│  1  variable x = 1;           │   Salida del programa, errores       │
│  2  escribe x;                │   en rojo y la pestaña activa        │
│  3                            │                                      │
├───────────────────────────────┴──────────────────────────────────────┤
│ Listo                                                 Ln 1, Col 1   │
└──────────────────────────────────────────────────────────────────────┘
```

| Zona | Qué hay |
|---|---|
| **Barra de herramientas** | Ejecutar, Depurar, Nuevo, Abrir…, Guardar, desplegable de **ejemplos** y el chip de runtime |
| **Barra del depurador** | Aparece con `F9`: Paso (F10), Seguir (F11), Detener (Esc) y el estado actual |
| **Editor** | Números de línea a la izquierda, resaltado de sintaxis, scrollbar |
| **Panel derecho** | Pestañas **Salida**, **Tokens**, **AST** y **Variables** |
| **Barra de estado** | Mensaje del momento a la izquierda (`Listo`, `⏳ ejecutando…`, `🐞 depurando…`, `✓ OK · 3 línea(s) de salida`, `Guardado: archivo.eco`), posición `Ln, Col` a la derecha |

Menús: **Archivo** (Nuevo `Ctrl+N`, Abrir `Ctrl+O`, Guardar `Ctrl+S`, Guardar
como…, Salir) · **Ejecutar** (Ejecutar, Depurar, Paso a paso, Seguir al
próximo punto, Detener depuración, Limpiar consola) · **Ayuda** (Acerca de…).

---

## 3. Atajos

### Ejecución y depuración

| Tecla | Qué hace |
|---|---|
| `F5` | Ejecuta el programa |
| `F9` | Depura: se detiene en la primera instrucción |
| `F10` | Paso a paso: avanza una instrucción |
| `F11` | Sigue hasta el próximo punto de ruptura |
| `Esc` | Detiene la depuración (o cierra la barra de búsqueda) |

### Archivo

| Tecla | Qué hace |
|---|---|
| `Ctrl+N` | Archivo nuevo |
| `Ctrl+O` | Abrir… |
| `Ctrl+S` | Guardar |

### Editor

| Tecla | Qué hace |
|---|---|
| `Ctrl+Z` / `Ctrl+Y` | Deshacer / rehacer (`Ctrl+Shift+Z` también rehace) |
| `Ctrl+F` | Buscar (contador `3/12`, botones `◀` `▶`, `Aa` distingue mayúsculas) |
| `Ctrl+H` | Buscar **y reemplazar** (uno o todos) |
| `F3` / `Shift+F3` | Siguiente / anterior coincidencia |
| `Ctrl+A` | Seleccionar todo |
| `Ctrl+G` | Ir a la línea |
| `Enter` / `Shift+Enter` | En la caja: siguiente / anterior coincidencia |

---

## 4. Buscar y reemplazar

`Ctrl+F` abre la barra sobre el editor (no tapa los números de línea):

- Mientras escribes se resaltan **todas** las coincidencias y, en otro color, la
  actual; el contador muestra `posición/total` (`0/0` si no hay).
- `Aa` activa distinguir mayúsculas.
- `◀` `▶` recorren; `F3`/`Shift+F3` también; `Enter` / `Shift+Enter` dentro de
  la caja hacen lo mismo.
- `Ctrl+H` añade la fila **Cambiar por** con dos botones: *Reemplazar* (la
  actual) y *Todo*.
- Si hay una palabra seleccionada al abrir la barra, se usa como término de
  búsqueda.
- Con la barra cerrada, `F3` la reabre con el último término.
- `Esc` o el botón `✕` la cierra y devuelve el foco al editor.

---

## 5. Menú contextual (clic derecho)

Se abre sobre el editor, con el atajo entre paréntesis (10 opciones, en una
columna con separadores):

```
Deshacer (Ctrl+Z)
Rehacer (Ctrl+Y)
─────────────
Cortar (Ctrl+X)
Copiar (Ctrl+C)
Pegar (Ctrl+V)
Borrar (Supr)
─────────────
Seleccionar todo (Ctrl+A)
─────────────
Buscar (Ctrl+F)
Reemplazar (Ctrl+H)
Ir a la línea (Ctrl+G)
```

Cortar, Copiar y Borrar aparecen **deshabilitados** si no hay texto
seleccionado.

---

## 6. Ejecutar y leer la salida

1. Pulsa `▶ Ejecutar (F5)`.
2. La pestaña **Salida** muestra lo que imprime `escribe`, y en rojo los
   errores con su línea.
3. La barra de estado pasa de `⏳ ejecutando…` a `✓ OK · N línea(s) de
   salida` (o se queda en el error).
4. `Ejecutar → Limpiar consola` vacía la pestaña.

Si el programa hace `entrada()`, se abre un **diálogo** para responder.

---

## 7. Las cuatro pestañas

| Pestaña | Contenido |
|---|---|
| **Salida** | Lo impreso por el programa y los errores |
| **Tokens** | Tabla con las 3 columnas del análisis léxico: Tipo, Valor, Posición |
| **AST** | El árbol sintáctico en JSON legible |
| **Variables** | Solo la usa el depurador: nombre y valor en cada paso |

---

## 8. Depurador paso a paso

1. (Opcional) Haz **clic en un número de línea** para marcar un punto de
   ruptura: el número queda en **rojo**. Otro clic lo quita.
2. Pulsa `🐞 Depurar (F9)` (o `F9`): aparece la barra del depurador y el
   programa se para en la primera instrucción, **resaltada en azul**.
3. Avanza:
   - `F10` **Paso** → una instrucción (entra dentro de funciones y bucles).
   - `F11` **Seguir** → hasta el siguiente punto de ruptura o el final.
   - `Esc` **Detener** → corta la ejecución.
4. En cada paso, la pestaña **Variables** se actualiza con los valores visibles
   en ese punto (de fuera adentro: globales → funciones → bloques).

Si el programa termina sin llegar a un punto de ruptura, el IDE lo indica y
vuelve al modo normal (la línea resaltada se quita).

---

## 9. Guardado y cambios sin guardar

- El título lleva un `*` mientras haya cambios sin guardar
  (`eco IDE — programa.eco *`).
- Cualquier acción que los perdería (cerrar la ventana, `Ctrl+N`, `Ctrl+O`,
  cargar un ejemplo) abre el modal:

  | Botón | Qué hace |
  |---|---|
  | **Guardar** (`Enter`) | Graba (y pide ruta si el archivo es nuevo) y continúa |
  | **Descartar** | Tira los cambios y continúa |
  | **Cancelar** (`Esc`) | No hace nada, la acción se anula |

- `Ctrl+S` guarda directamente; `Guardar como…` siempre pide ruta.

---

## 10. Ejemplos

El desplegable **`ejemplo:`** de la barra de herramientas lista los `.eco` de
`ejemplos/` y los carga en el editor (si había cambios sin guardar, pregunta
antes). `ejemplos/modulos/` no aparece en la lista: son ficheros de apoyo para
`importar`.

---

## 11. Detalles que conviene saber

- **Resaltado:** palabras clave, textos, números, comentarios (`//`) y
  operadores se colorean al escribir.
- **Línea del error:** si el programa falla, su número de línea se marca en el
  margen con fondo rojo oscuro.
- **`entrada()`** se responde en un diálogo; la respuesta también se refleja en
  la consola.
- **Sin ventanas de terminal:** ejecutar desde el IDE no abre ventanas de CMD
  (`CREATE_NO_WINDOW`); `prueba_sin_ventana.py` lo verifica.
- **Runtime:** si `eco.exe` no está, el chip avisa de que todo va con Python
  (más lento al arrancar).

---

## Siguiente paso

- La sintaxis del código: [GUIA-DEL-LENGUAJE.md](GUIA-DEL-LENGUAJE.md)
- Cómo se hace por dentro: [ARQUITECTURA.md](ARQUITECTURA.md)
