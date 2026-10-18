"""Comprueba que ejecutar un programa NO abre ventanas de terminal.

Se lanza con pythonw.exe (sin consola), igual que el IDE, y va lanzando
eco.exe 20 veces. Si CREATE_NO_WINDOW no funcionara, cada lanzamiento
abriría una ventana de terminal que el vigilante de la prueba detectaría.
"""
import sys
import time

import runtime

t0 = time.time()
ok = 0
n = 20
for _ in range(n):
    d = runtime.run_analysis("escribe 2 + 3 * 4;")
    if d.get("output", "").strip() == "14":
        ok += 1

with open(sys.argv[1], "w", encoding="utf-8") as f:
    f.write(f"runtime={runtime.runtime_name()} | aciertos={ok}/{n} | "
            f"tiempo={time.time() - t0:.2f}s\n")
