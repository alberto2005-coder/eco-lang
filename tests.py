"""Tests del intérprete — se ejecutan con:  py tests.py"""

import io
from contextlib import redirect_stdout

from main import compile_and_run
from interpreter import Interpreter, RunError
from lexer import tokenize, LexError
from parser import ParseError


def run(source: str) -> str:
    out = io.StringIO()
    with redirect_stdout(out):
        compile_and_run(source, Interpreter())
    return out.getvalue()


def expect_output(source: str, expected: str):
    got = run(source)
    assert got == expected, f"\nENTRADA:\n{source}\nESPERADO: {expected!r}\nOBTENIDO: {got!r}"


def expect_error(source: str, exc, contiene: str = ""):
    try:
        run(source)
    except exc as e:
        if contiene:
            assert contiene in str(e), f"el error no contiene {contiene!r}: {e}"
        return str(e)
    raise AssertionError(f"debía lanzar {exc.__name__} y no lo hizo:\n{source}")


# ---------------------------------------------------------------- léxico
tipos = [t.type for t in tokenize("variable x = 10;")]
assert tipos == ["VARIABLE", "IDENT", "ASSIGN", "NUMBER", "SEMI", "EOF"], tipos
tipos = [t.type for t in tokenize("si sino mientras para funcion devuelve romper continuar")]
assert tipos == ["SI", "SINO", "MIENTRAS", "PARA", "FUNCION", "DEVUELVE", "ROMPER",
                 "CONTINUAR", "EOF"], tipos
assert [t.type for t in tokenize("1 ^ 2 [ ] , y o no")] == \
    ["NUMBER", "POW", "NUMBER", "LBRACKET", "RBRACKET", "COMMA", "Y", "O", "NO", "EOF"]
expect_error('variable x = "sin cerrar', LexError)
expect_error("variable x = @;", LexError)

# ---------------------------------------------------------------- sintaxis
expect_error("escribe 1 +;", ParseError)
expect_error("variable 2 = 3;", ParseError)
expect_error("si (verdadero) { escribe 1;", ParseError)
expect_error("mientras { }", ParseError)                  # falta la condición
expect_error("mientras 1 < 2 {", ParseError)              # falta la llave que cierra
expect_output("variable i = 0; mientras i < 3 { i++; } escribe i;", "3\n")   # sin paréntesis
expect_error("funcion f( { }", ParseError)
expect_error("escribe [1, 2;", ParseError)

# ------------------------------------------------------------ expresiones
expect_output("escribe 2 + 3 * 4;", "14\n")
expect_output("escribe (2 + 3) * 4;", "20\n")
expect_output("escribe 10 / 4;", "2.5\n")
expect_output("escribe 10 % 3;", "1\n")
expect_output("escribe -3 + 5;", "2\n")
expect_output("escribe 2 ^ 10;", "1024\n")
expect_output("escribe 2 ^ 3 ^ 2;", "512\n")            # asociativo por la derecha
expect_output('escribe "hola " + "mundo";', "hola mundo\n")
expect_output("escribe [1, 2] + [3];", "[1, 2, 3]\n")
expect_output("escribe 1 == 1; escribe 1 != 2; escribe no verdadero;",
              "verdadero\nverdadero\nfalso\n")
expect_output("escribe 2 < 3 y 3 < 4;", "verdadero\n")
expect_output("escribe no (1 == 2) o falso;", "verdadero\n")

# ---------------------------------------------------------------- variables
expect_output("variable x = 5; x = x + 1; escribe x;", "6\n")
expect_output("const P = 3; escribe P * 2;", "6\n")
expect_error("const P = 3; P = 4;", RunError, "constante")
expect_error("escribe no_existe;", RunError, "no está declarada")
expect_error("zarpa = 3;", RunError, "no está declarada")   # 'y'/'o'/'no' son reservadas
expect_error("variable a = 1; variable a = 2;", RunError, "ya está declarada")

# ------------------------------------------------------------ condicionales
expect_output("si (verdadero) { escribe 1; } sino { escribe 2; }", "1\n")
expect_output("si (falso) { escribe 1; } sino si (verdadero) { escribe 2; } sino { escribe 3; }",
              "2\n")
expect_output("si (falso) { escribe 1; }", "")
expect_error("si (1) { escribe 2; }", RunError, "verdadero o falso")

# ------------------------------------------------------------------ bucles
expect_output("variable i = 0; mientras (i < 3) { escribe i; i = i + 1; }", "0\n1\n2\n")
expect_output("variable t = 0; para (variable i = 0; i < 10; i = i + 1) { "
              "si (i == 3) { romper; } si (i % 2 == 0) { continuar; } t = t + i; } "
              "escribe t;", "1\n")     # solo suma los impares 1 (rompe en 3)
expect_output("variable s = 0; para (x en [10, 20, 30]) { s = s + x; } escribe s;", "60\n")
expect_output("variable c = 0; para (variable i = 0; ; i = i + 1) { "
              "si (i >= 4) { romper; } c = c + 1; } escribe c;", "4\n")
expect_error("romper;", RunError, "dentro de un bucle")
expect_error("continuar;", RunError, "dentro de un bucle")
expect_error("variable n = 0; para (x en 5) { n = n + 1; }", RunError, "necesita una lista")

# --------------------------------------------------------------- funciones
expect_output("funcion doble(n) { devuelve n * 2; } escribe doble(21);", "42\n")
expect_output("funcion saludo() { devuelve \"hola\"; } escribe saludo();", "hola\n")
expect_output("funcion f() { } escribe f();", "nulo\n")   # sin devuelve -> nulo
expect_output("funcion suma(a, b) { devuelve a + b; } escribe suma(2, 3) + suma(1, 1);", "7\n")
expect_output(
    "funcion fib(n) { si (n < 2) { devuelve n; } devuelve fib(n - 1) + fib(n - 2); } "
    "escribe fib(10);", "55\n")
expect_error("funcion f(a) { devuelve a; } escribe f();", RunError, "1 parámetro")
expect_error("funcion f(a) { devuelve a; } escribe f(1, 2);", RunError, "recibe 2")
expect_error("escribe 3();", RunError, "Solo se pueden llamar funciones")
expect_error("devuelve 1;", RunError, "dentro de una función")
expect_error("funcion mala() { romper; } mala();", RunError, "dentro de un bucle")

# ------------------------------------------------------------------ listas
expect_output("variable l = [1, 2, 3]; escribe l[0]; escribe l[2];", "1\n3\n")
expect_output("variable l = [1, 2, 3]; l[1] = 99; escribe l;", "[1, 99, 3]\n")
expect_output("variable l = [\"a\"]; escribe longitud(l);", "1\n")
expect_output("escribe longitud(\"abcd\");", "4\n")
expect_output("escribe rango(4);", "[0, 1, 2, 3]\n")
expect_output("escribe rango(2, 5);", "[2, 3, 4]\n")
expect_output("escribe rango(0, 10, 3);", "[0, 3, 6, 9]\n")
expect_output("escribe rango(5, 0, -2);", "[5, 3, 1]\n")
expect_output("variable l = []; agregar(l, 7); escribe l;", "[7]\n")
expect_output("variable l = [\"a\"]; escribe l[0][0];", "a\n")
expect_error("escribe [1, 2][5];", RunError, "fuera de rango")
expect_error("escribe 42[0];", RunError, "Solo se puede indexar")
expect_error("escribe [1][\"x\"];", RunError, "índice debe ser un número")

# --------------------------------------------------- textos e interpolación
expect_output('variable nombre = "Ana"; escribe "Hola, ${nombre}!";', "Hola, Ana!\n")
expect_output('escribe "suma: ${1 + 2}";', "suma: 3\n")
expect_output('escribe "largo: ${longitud([1,2,3])}";', "largo: 3\n")
expect_output('escribe "escapado: \\${1 + 1}";', "escapado: ${1 + 1}\n")
expect_output('escribe "tab:\\tfin";', "tab:\tfin\n")
expect_error('escribe "${1 +}";', RunError, "dentro de ${")
expect_error('escribe "${1";', RunError, "sin cerrar")

# ---------------------------------------------------------- tipos y errores
expect_output("escribe tipo(1); escribe tipo(\"a\"); escribe tipo(verdadero); "
              "escribe tipo([1]); escribe tipo(nulo);",
              "número\ntexto\nbooleano\nlista\nnulo\n")
expect_output("escribe texto(12); escribe numero(\"3,5\");", "12\n3.5\n")
expect_output("escribe 1 == verdadero;", "falso\n")       # tipos estrictos
expect_error("escribe 1 / 0;", RunError, "División entre cero")
expect_error('escribe 1 + "a";', RunError, "no puede combinar")
expect_error('escribe "a" < 1;', RunError, "No se puede comparar")
expect_error('escribe 1 - "x";', RunError, "necesita números")
expect_error("escribe (no 1);", RunError, "booleanos")
expect_output("escribe falso y (1 / 0 == 0);", "falso\n")   # cortocircuito
expect_output("escribe verdadero o (1 / 0 == 0);", "verdadero\n")

# --------------------------------------------------------- ámbitos
# lo declarado dentro de un bloque no se ve fuera
expect_output("variable total = 0; si (verdadero) { variable dentro = 1; "
              "total = total + dentro; } escribe total;", "1\n")
expect_error("si (verdadero) { variable dentro = 1; } escribe dentro;",
             RunError, "no está declarada")

# ---------------------------------------------------------- diccionarios
expect_output('escribe {"nombre": "Ana"};', '{"nombre": "Ana"}\n')
expect_output('variable d = {nombre: "Ana", edad: 30}; escribe d["nombre"];', "Ana\n")
expect_output('variable d = {a: 1, b: [2, 3]}; escribe d; escribe d["b"][1];',
              '{"a": 1, "b": [2, 3]}\n3\n')
expect_output('variable d = {a: 1}; d["b"] = 2; escribe d; escribe longitud(d);',
              '{"a": 1, "b": 2}\n2\n')              # crear la clave al asignar
expect_output('variable d = {a: 1, b: 2}; escribe claves(d); escribe valores(d);',
              '["a", "b"]\n[1, 2]\n')
expect_output('variable d = {nombre: "Ana"}; escribe tipo(d);', "diccionario\n")
expect_output('variable d = {a: 1, b: 2}; variable s = 0; para (k en d) { s = s + d[k]; } '
              'escribe s;', "3\n")
expect_output('variable d = {hijo: {nombre: "Lía"}}; escribe d["hijo"]["nombre"];', "Lía\n")
expect_output('escribe {"a": 1} == {"a": 1}; escribe {"a": 1} == {"a": 2};',
              "verdadero\nfalso\n")
expect_output('escribe {"x": 1} != {"x": 1, "y": 2};', "verdadero\n")
expect_output('variable d = {"a": 1, "b": 2}; escribe d; escribe d == {"b": 2, "a": 1};',
              '{"a": 1, "b": 2}\nverdadero\n')       # el orden no importa
expect_error('escribe {"a": 1}["b"];', RunError, "no existe en el diccionario")
expect_error('variable d = {a: 1}; escribe d[1];', RunError, "Las claves")   # claves son textos
expect_error('variable d = {}; d[verdadero] = 1;', RunError, "Las claves")
expect_error('escribe {1: "x"};', ParseError, "clave")                      # 1 no es clave
expect_error('escribe {"a" 1};', ParseError)
expect_error('escribe {"a": 1} + 1;', RunError, "no puede combinar")
expect_error('agregar({a: 1}, 2);', RunError, "necesita una lista")

# --------------------------------------------------------------- entrada
import interpreter
interpreter.set_input_handler(lambda pregunta: "21")
expect_output('variable edad = numero(entrada("¿edad? ")); escribe edad * 2;',
              "¿edad? 42\n")
expect_output('escribe entrada();', "21\n")          # sin mensaje también funciona
interpreter.set_input_handler(lambda pregunta: "hola " + pregunta.strip())
expect_output('escribe entrada("p: ");', "p: hola p:\n")
interpreter.set_input_handler(None)
# sin canal de entrada (ventana sin consola) -> error claro, no bloqueo
_real_stdin = interpreter.sys.stdin
interpreter.sys.stdin = None
expect_error('escribe numero(entrada());', RunError, "necesita datos")
# entrada agotada (EOF) -> error claro
import io as _io
interpreter.sys.stdin = _io.StringIO("")
expect_error('escribe numero(entrada());', RunError, "fin de stdin")
interpreter.sys.stdin = _real_stdin
expect_error('entrada(5);', RunError, "espera un texto")               # tipo de argumento
expect_error('entrada("a", "b");', RunError, "espera 0-1 argumento")

# ----------------------------------------------------- comillas simples
expect_output("escribe 'hola';", "hola\n")
expect_output("escribe 'comillas \"dentro\"';", 'comillas "dentro"\n')
expect_output("escribe \"comillas 'dentro'\";", "comillas 'dentro'\n")
expect_output("escribe 'no\\' cierra';", "no' cierra\n")
expect_output("variable d = {k: 7}; escribe \"${d['k']}\";", "7\n")     # simples en ${}
expect_output("variable d = {k: 7}; escribe \"${d[\\\"k\\\"]}\";", "7\n")  # escapadas en ${}
expect_error("escribe 'sin cerrar;", LexError)


# --------------------------------------------------------------- módulos
import tempfile
from pathlib import Path

def run_en(source: str, filename) -> str:
    """Ejecuta `source` como si viniera del archivo `filename`."""
    out = io.StringIO()
    with redirect_stdout(out):
        compile_and_run(source, Interpreter(filename=str(filename)))
    return out.getvalue()

_mod = Path(tempfile.mkdtemp(prefix="eco_test_mod_"))
(_mod / "util.eco").write_text(
    'const K = 6;\n'
    'funcion doble(n) { devuelve n * 2; }\n'
    'escribe "cargando util";\n', encoding="utf-8")
_principal = _mod / "principal.eco"        # no hace falta que exista

# la ruta es relativa al archivo que importa; se puede ir con y sin .eco
expect_error('escribe util.K;', RunError)  # sin importar, no existe 'util'
assert run_en('importar "util"; escribe util.K;', _principal) == "cargando util\n6\n"
assert run_en('importar "util.eco"; escribe util.K;', _principal) == "cargando util\n6\n"
# alias y funciones exportadas
assert run_en('importar "util" como u; escribe u.doble(21);', _principal) == \
    "cargando util\n42\n"
# el módulo se ejecuta UNA sola vez aunque se importe dos veces
assert run_en('importar "util"; importar "util.eco" como u2; '
              'escribe util.K; escribe u2.K;', _principal) == \
    "cargando util\n6\n6\n"
# el error dice qué módulo y dónde lo buscó
try:
    run_en('importar "no_existe_ninguna";', _principal)
    raise AssertionError("debía fallar el módulo inexistente")
except RunError as e:
    assert "No se encontró el módulo" in str(e), e
    assert str(_mod) in str(e), e
# el ejemplo de módulos tiene que seguir funcionando
_ejemplo = Path(__file__).resolve().parent / "ejemplos" / "importar.eco"
if _ejemplo.is_file():
    assert "doble(21):   42" in run_en(_ejemplo.read_text(encoding="utf-8"), _ejemplo)


print("OK — todos los tests pasaron")
