# Instalación y primeros pasos

Tres formas de usar eco. Para **programar** basta la primera.

| Forma | Necesitas Python | Ideal para |
|---|---|---|
| A. Instalador (`eco-setup.exe`) | No | Cualquier equipo |
| B. Desde la fuente | Sí | Desarrollo |
| C. IDE web en el navegador | Sí (o `eco.exe`) | Pruebas rápidas sin instalar nada |

---

## A. Instalador (recomendada)

**Requisitos:** Windows 10/11 de 64 bits. No hace falta Python ni ser
administrador.

1. Ejecuta **`dist\eco-setup.exe`**.
2. En *Opcionales* puedes marcar (viene marcado lo indicado):
   - **Acceso directo en el escritorio**
   - **Añadir eco al PATH** → poder escribir `eco` en cualquier terminal (si la dejas sin marcar, no se toca el PATH)
   - **Asociar los archivos .eco con el IDE** → doble clic para abrirlos
3. Al terminar puedes abrir el IDE directamente.

Desinstalación: *Menú Inicio → eco → Desinstalar eco* (borra el programa, la
entrada del PATH, los accesos directos y la asociación de `.eco`).

### Qué se instala

```
%LOCALAPPDATA%\Programs\eco\
├── eco.exe          el intérprete, tipo node
├── eco-ide.exe      el IDE de escritorio (empaqueta los ejemplos)
├── ejemplos\        los .eco de ejemplo
├── docs\            la documentación (9 guías en Markdown)
├── README.md
└── LICENSE          licencia MIT con adenda personalizada
```

Menú Inicio: **eco IDE**, **eco REPL**, **Ejemplos**, **Desinstalar eco**.

### Primeras comprobaciones

Abre una terminal **nueva** (importante: las que ya estaban abiertas no tienen
el PATH nuevo):

```bash
eco --version            # 0.4.0
eco -e "escribe 2 + 3 * 4;"      # 14
eco ejemplos\saludo.eco          # ejecuta el ejemplo
eco                              # REPL: escribe salir para terminar
```

---

## B. Desde la fuente (desarrollo)

**Requisitos:**

- Python 3.13 o superior (probado con **3.14.4**), instalado con
  *Add Python to PATH*.
- `py` (el lanzador de Windows) o `python` en el PATH.
- Nada más: el proyecto solo usa biblioteca estándar.

```bash
cd eco
py main.py ejemplos\saludo.eco   # ejecuta un archivo
py main.py                       # REPL
py ide.py                        # IDE de escritorio
py server.py                     # IDE web (http://127.0.0.1:8787)
```

O con los lanzadores:

- **`IDE.bat`** → abre el IDE: primero con `dist\eco-ide.exe` si existe, si no
  con Python desde la fuente (y avisa con instrucciones si falta Python).
- **`build.bat`** → compila todo (ver [DESARROLLO.md](DESARROLLO.md)).

---

## C. IDE web (sin tocar el escritorio)

```bash
py server.py                # por defecto en el puerto 8787
py server.py --port 9000    # otro puerto
```

Abre `http://127.0.0.1:8787`, elige un ejemplo o escribe código y pulsa
`Ctrl+Enter`. El servidor solo escucha en `127.0.0.1` (no sale de tu equipo).

Detener: `Ctrl+C` en la terminal.

---

## Problemas comunes

| Síntoma | Causa y solución |
|---|---|
| `'eco' no se reconoce` en la terminal | La terminal estaba abierta antes de instalar → **ábrela de nuevo**, o revisa que marcaste *Añadir eco al PATH*. |
| El IDE abre pero dice `runtime: python 3.x` | No encontró `eco.exe` junto al IDE. Reinstala, o ejecuta `build.bat` si estás desarrollando. |
| `build.bat` falla con *PermissionError* | Hay un `eco.exe` o `eco-ide.exe` en marcha: cierra el IDE y las ventanas de eco, o `Get-Process eco \| Stop-Process -Force`, y vuelve a lanzarlo. |
| Windows pregunta al abrir `eco-setup.exe` | Es normal en archivos descargados: *Más información → Ejecutar de todos modos*. No pide administrador. |
| Aparece una ventana de terminal al ejecutar desde el IDE | No debería (`CREATE_NO_WINDOW`). Si pasa, avísanos: `prueba_sin_ventana.py` existe justo para detectarlo. |
| Un programa que usa `entrada()` se queda esperando en el navegador | En el IDE web no hay entrada: ejecútalo con `eco.exe` en terminal o en el IDE de escritorio. |
| `No encontre Python` al lanzar `IDE.bat` | Instala Python desde <https://www.python.org/downloads/> marcando *Add Python to PATH*. |

---

## Siguiente paso

- Programar: [GUIA-DEL-LENGUAJE.md](GUIA-DEL-LENGUAJE.md)
- Usar el IDE: [GUIA-DEL-IDE.md](GUIA-DEL-IDE.md)
- Terminal y scripts: [GUIA-DE-LA-CLI.md](GUIA-DE-LA-CLI.md)
