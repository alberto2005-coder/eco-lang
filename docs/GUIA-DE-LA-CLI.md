# Guía de la CLI `eco`

La CLI se usa como `node`, `python` o `java`: un comando, un archivo, una
terminal.

---

## 1. Comandos

| Comando | Qué hace |
|---|---|
| `eco archivo.eco` | Ejecuta un archivo |
| `eco` | Abre el **REPL** interactivo |
| `eco -e "código"` | Evalúa código suelto (`--eval`) |
| `eco --analyze archivo.eco` | Analiza y emite **una línea JSON** (salida, tokens, AST) |
| `eco --analyze` | Igual, leyendo el código por **stdin** (lo usa el IDE) |
| `eco --server` | Modo servidor JSON por stdin/stdout (interno, para el IDE) |
| `eco --version` · `eco -v` | Imprime la versión (`0.4.0`) |
| `eco --help` · `eco -h` | Imprime la ayuda |

```bash
eco --version                     # 0.4.0
eco -e "escribe 2 + 3 * 4;"       # 14
eco ejemplos\saludo.eco           # ejecuta un ejemplo
eco mi_programa.eco
```

Los módulos que se importan con `importar` se resuelven **relativos al archivo
que los trae**, así que puedes llamar a `eco` desde cualquier carpeta.

---

## 2. Códigos de salida

| Código | Significado |
|---|---|
| `0` | Todo correcto |
| `1` | Error de programa (léxico, sintaxis o ejecución) o archivo ilegible |
| `2` | Uso incorrecto de la CLI (p. ej. `-e` sin código) |

```bash
eco roto.eco
echo $?        # 1
```

---

## 3. REPL

```bash
eco
```

```
eco 0.4.0 — escribe "salir" o Ctrl+Z + Enter para terminar
eco> variable x = 5;
... escribe x * 2;
10
eco> salir
```

- `eco> ` pide la primera línea; `... ` continúa un bloque abierto (si llaman
  más `{` que `}`, sigue leyendo hasta cerrarlo).
- Termina con `salir`, `exit`, `quit` o `Ctrl+Z` + `Enter`.
- Las instrucciones se ejecutan **una por línea**; un error no corta la sesión.
- El estado (variables y funciones) **se conserva** entre líneas.

---

## 4. `--analyze`: el programa como JSON

Devuelve exactamente **una línea JSON** con el resultado de las tres fases:

| Clave | Contenido |
|---|---|
| `version` | Versión del intérprete |
| `output` | Todo lo que imprimió `escribe` |
| `error` | Mensaje de error o `null` |
| `phase` | `"lex"`, `"parse"` o `"run"` (o `null` si no hay error) |
| `detenido` | Línea en la que se detuvo la depuración, o `null` |
| `tokens` | Lista de tokens (o `null` si falló el léxico) |
| `ast` | Árbol sintáctico (o `null` si falló el parser) |

```bash
eco --analyze ejemplos\saludo.eco
```

```json
{"version": "0.4.0", "output": "Hola, Mundo!\nTienes 30 años.\nEs mayor de edad\n",
 "error": null, "phase": null, "detenido": null,
 "tokens": [{"_type": "Token", "type": "VARIABLE", "value": "variable",
             "line": 2, "col": 1}, ...],
 "ast": {"_type": "Program", ...}}
```

Cada token lleva `_type`, `type`, `value`, `line` y `col`; cada nodo del AST
lleva `_type` con el nombre del nodo. Así los consume el IDE (pestañas
**Tokens** y **AST**).

También se puede alimentar por stdin (sin argumentos):

```bash
eco --analyze < mi_programa.eco
```

---

## 5. `--server`: protocolo para el IDE

Modo interno: un JSON por línea en stdin → un JSON por línea en stdout,
UTF-8. No está pensado para uso manual; es lo que mantiene `runtime.py` vivo
para no pagar el arranque del `.exe` en cada *Ejecutar*.

### Petición

```json
{"source": "escribe 1;", "file": "C:\\...\\ejemplos\\saludo.eco"}
```

- `source` (obligatorio): el código.
- `file` (opcional): archivo de origen; de ahí salen las rutas de `importar`.
- `debug` (opcional, booleano): activa el paso a paso.
- `{"cmd": "exit"}` termina el servidor.

### Respuesta

La misma línea JSON de `--analyze` (`version, output, error, phase, detenido,
tokens, ast`).

### Mensajes intercalados

Si el programa pide datos:

```json
{"tipo": "entrada", "pregunta": "¿Cómo te llamas? "}
```
→ responde por stdin: `{"entrada": "Ana"}`

Si `debug: true`, en cada instrucción:

```json
{"tipo": "paso", "linea": 7, "variables": {"x": 5}}
```
→ responde por stdin: `{"accion": "step"}` · `{"accion": "continue"}` ·
`{"accion": "stop"}`

Si la comunicación se corta, el servidor interpreta `stop` y termina.

---

## 6. Ejemplos en scripts

```bat
@echo off
eco --version > nul || (echo falta eco en el PATH & exit /b 1)
eco programa.eco
if errorlevel 1 (echo el programa fallo & exit /b 1)
```

```bash
# comprobar que un programa imprime lo esperado
salida=$(eco miseria.eco)
[ "$salida" = "42" ] && echo bien
```

Para inspeccionar fases (sin ejecutar):

```bash
eco --analyze roto.eco | python -c "import json,sys; d=json.load(sys.stdin); print(d['phase'], d['error'])"
```

---

## Siguiente paso

- Cómo está hecho por dentro: [ARQUITECTURA.md](ARQUITECTURA.md)
- Compilar la CLI: [DESARROLLO.md](DESARROLLO.md)
