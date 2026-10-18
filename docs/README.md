# Documentación de eco

Repositorio: <https://github.com/alberto2005-coder/eco-lang>

Toda la documentación del proyecto, ordenada por audiencia.

| Documento | Para quién | Qué encuentra |
|---|---|---|
| [REQUISITOS.md](REQUISITOS.md) | Quien evalúa o mantiene el proyecto | Alcance, requisitos funcionales (RF) y no funcionales (RNF), criterios de aceptación |
| [INSTALACION.md](INSTALACION.md) | Usuario final | Instalar con el `.exe`, usar sin instalar, desinstalar, problemas comunes |
| [GUIA-DEL-LENGUAJE.md](GUIA-DEL-LENGUAJE.md) | Quien programa en eco | Tutorial de cero a módulos, referencia de tipos, instrucciones, funciones, métodos, gramática y errores |
| [GUIA-DEL-IDE.md](GUIA-DEL-IDE.md) | Quien usa el IDE de escritorio | Interfaz, todos los atajos, buscar/reemplazar, depurador, guardado |
| [GUIA-DE-LA-CLI.md](GUIA-DE-LA-CLI.md) | Quien usa la terminal o integra eco | Comandos `eco`, códigos de salida, REPL, JSON de `--analyze`, protocolo `--server` |
| [GUIA-DEL-SERVIDOR-WEB.md](GUIA-DEL-SERVIDOR-WEB.md) | Quien levanta el IDE web | Endpoints, seguridad y limitaciones |
| [ARQUITECTURA.md](ARQUITECTURA.md) | Quien toca el código | Flujo lexer → parser → evaluador, módulos, contratos JSON, cómo ampliar el lenguaje |
| [DESARROLLO.md](DESARROLLO.md) | Quien desarrolla | Tests, compilación con PyInstaller e Inno Setup, checklist de versión |

El [README](../README.md) de la raíz es la vista corta: qué es, cómo se instala
y el resumen del lenguaje. Aquí está el detalle.

## Versión

**0.4.0** — el número vive en `runtime.py` (`VERSION`); el resto de sitios
(`instalador.iss`, `web/index.html`, `README.md`) se sincronizan siguiendo el
[checklist de DESARROLLO.md](DESARROLLO.md#checklist-de-versión).
