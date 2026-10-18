r"""Evaluador: recorre el AST y ejecuta el programa.

Aquí vive lo que hace "propio" a este lenguaje:
  · ámbitos con `variable` y `const` (las constantes no se pueden modificar)
  · bucles `mientras` y `para` con `romper` / `continuar`
  · funciones con `devuelve` y llamadas nativas (longitud, rango, agregar...)
  · listas con índice y asignación por índice
  · diccionarios {"clave": valor} con índice, claves(), valores()
  · métodos encadenables:  persona.nombre.mayusculas(), lista.agregar(x)
  · importar "otro.eco" [como alias]  (el módulo llega como un diccionario)
  · textos con interpolación:  escribe "Hola ${nombre}";   y escapes \n \t \$
  · entrada("¿edad?") para leer del teclado (consola, diálogo o protocolo)
  · evaluación corta de `y` y `o`
  · depuración paso a paso: hook antes de cada instrucción (set_debug_hook)
"""

import math
import sys
from pathlib import Path

from lexer import tokenize, LexError, KEYWORDS
from parser import (
    parse, parse_expression, Program, Block, Let, Assign, IndexAssign,
    AttrAssign, Incremento, Importar, Print, If,
    While, For, ForIn, Function, Return, Break, Continue, ExprStatement,
    Number, Text, Boolean, Null, Var, Lista, Diccionario, Unary, Binary,
    Index, Attribute, Call, ParseError,
)


class RunError(Exception):
    """Error detectado durante la ejecución."""


class Detener(Exception):
    """El usuario ha detenido la depuración paso a paso."""

    def __init__(self, line):
        self.line = line
        super().__init__(f"detenido en la línea {line}")


# ------------------------------------------------- canal de entrada (stdin)
# `entrada()` no siempre puede leer la consola (IDE, servidor, protocolo).
# Quien use el intérprete puede instalar aquí su propio manejador:
#     interpreter.set_input_handler(lambda pregunta: "texto tecleado")
_handler_entrada = None


def set_input_handler(fn=None):
    """Instala (o quita, con None) el manejador de `entrada()`."""
    global _handler_entrada
    _handler_entrada = fn


def get_input_handler():
    """El manejador de `entrada()` instalado (o None)."""
    return _handler_entrada


# ------------------------------------------------- depuración paso a paso
# Antes de cada instrucción se llama a este hook (si alguien lo instaló con
# `set_debug_hook`). Devuelve "step" (para en la siguiente línea),
# "continue" (solo en puntos de ruptura) o "stop" (detiene el programa).
_hook_debug = None


def set_debug_hook(fn=None):
    """Instala (o quita, con None) el hook de depuración."""
    global _hook_debug
    _hook_debug = fn


def crear_hook_debug(enviar):
    """Convierte `enviar(linea, variables) -> acción` en un hook de depuración."""

    def hook(linea, variables):
        accion = enviar(linea, variables)
        if accion not in ("step", "continue"):       # "stop" o lo que sea
            raise Detener(linea)
        return accion

    return hook


# --------------------------------------------------------------- señales
class _Romper(Exception):
    def __init__(self, line):
        self.line = line


class _Continuar(Exception):
    def __init__(self, line):
        self.line = line


class _Devolver(Exception):
    def __init__(self, value, line):
        self.value = value
        self.line = line


# ---------------------------------------------------------------- valores
class Funcion:
    """Función definida por el usuario (con su entorno de cierre)."""

    def __init__(self, name, params, body, env):
        self.name, self.params, self.body, self.env = name, params, body, env

    def __repr__(self):
        return f"<funcion {self.name}({', '.join(self.params)})>"


class Nativa:
    """Función escrita en Python que el lenguaje expone como función."""

    def __init__(self, name, fn, min_args, max_args):
        self.name, self.fn = name, fn
        self.min_args, self.max_args = min_args, max_args

    def __repr__(self):
        return f"<funcion nativa {self.name}>"


class Metodo:
    """Método ligado a un valor:  "hola".mayusculas()  es  f("hola")."""

    def __init__(self, receptor, nombre, min_args, max_args, fn):
        self.receptor, self.nombre, self.fn = receptor, nombre, fn
        self.min_args, self.max_args = min_args, max_args

    def __repr__(self):
        return f"<metodo {type_name(self.receptor)}.{self.nombre}>"


# ----------------------------------------------------------------- entorno
class Env:
    """Ámbito de variables: cadena de entornos padre (alcance léxico)."""

    def __init__(self, parent: "Env" = None):
        self.vars = {}          # nombre -> (valor, es_constante)
        self.parent = parent

    def declare(self, name, value, const, line):
        if name in self.vars:
            raise RunError(f"[línea {line}] La variable '{name}' ya está declarada en este ámbito")
        self.vars[name] = (value, const)

    def lookup(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env, env.vars[name]
            env = env.parent
        return None, None

    def get(self, name, line):
        _, slot = self.lookup(name)
        if slot is None:
            raise RunError(f"[línea {line}] '{name}' no está declarada")
        return slot[0]

    def set(self, name, value, line):
        env, slot = self.lookup(name)
        if slot is None:
            raise RunError(f"[línea {line}] No se puede asignar a '{name}': no está declarada "
                           f"(declárala antes con: variable {name} = ...)")
        if slot[1]:
            raise RunError(f"[línea {line}] '{name}' es una constante y no se puede modificar")
        env.vars[name] = (value, slot[1])


# ------------------------------------------------------------- utilidades
def fmt_number(v: float) -> str:
    """Los enteros se muestran sin '.0' y se evitan errores de coma flotante."""
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return f"{v:.10g}"


def type_name(v) -> str:
    if v is None:
        return "nulo"
    if isinstance(v, bool):
        return "booleano"
    if isinstance(v, float):
        return "número"
    if isinstance(v, str):
        return "texto"
    if isinstance(v, list):
        return "lista"
    if isinstance(v, dict):
        return "diccionario"
    if isinstance(v, (Funcion, Nativa)):
        return "función"
    return type(v).__name__


def render(v) -> str:
    """Representación con comillas en los textos (para listas y errores)."""
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, list):
        return "[" + ", ".join(render(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{render(k)}: {render(x)}" for k, x in v.items()) + "}"
    if isinstance(v, bool):
        return "verdadero" if v else "falso"
    if v is None:
        return "nulo"
    if isinstance(v, float):
        return fmt_number(v)
    if isinstance(v, (Funcion, Nativa)):
        return f"<funcion {v.name}>"
    return str(v)


def display(v) -> str:
    """Lo que imprime `escribe`: los textos sin comillas."""
    if isinstance(v, str):
        return v
    return render(v)


def equal(a, b) -> bool:
    """Igualdad estricta de tipos: verdadero != 1, y listas/diccionarios por dentro."""
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    return a == b


ESCAPES = {"n": "\n", "t": "\t", '"': '"', "'": "'", "\\": "\\", "$": "$"}


# ----------------------------------------------------------------- métodos
# Métodos encadenables:  persona.nombre.mayusculas(), lista.agregar(x), ...
# Cada tipo de valor tiene su diccionario de métodos; la firma de cada
# función es  fn(intérprete, receptor, argumentos, línea).

def _arg_texto(interp, metodo, valor, line):
    if not isinstance(valor, str):
        interp.fail(line, f"'{metodo}' espera un texto (recibió: {type_name(valor)})")
    return valor


def _arg_numero(interp, metodo, valor, line):
    if not isinstance(valor, float) or isinstance(valor, bool):
        interp.fail(line, f"'{metodo}' espera un número (recibió: {type_name(valor)})")
    return valor


def _arg_indice(interp, metodo, valor, n, line):
    _arg_numero(interp, metodo, valor, line)
    if valor != int(valor):
        interp.fail(line, f"'{metodo}' espera un índice entero (recibió: {fmt_number(valor)})")
    i = int(valor)
    if i < 0:
        i += n
    if i < 0 or i >= n:
        interp.fail(line, f"'{metodo}': índice fuera de rango ({fmt_number(valor)}) "
                          f"con una lista de {n} elemento(s)")
    return i


# --- texto ---
def _texto_longitud(interp, r, a, line):
    return float(len(r))


def _texto_mayusculas(interp, r, a, line):
    return r.upper()


def _texto_minusculas(interp, r, a, line):
    return r.lower()


def _texto_recortar(interp, r, a, line):
    return r.strip()


def _texto_contiene(interp, r, a, line):
    return _arg_texto(interp, "contiene", a[0], line) in r


def _texto_empieza(interp, r, a, line):
    return r.startswith(_arg_texto(interp, "empiezaPor", a[0], line))


def _texto_termina(interp, r, a, line):
    return r.endswith(_arg_texto(interp, "terminaPor", a[0], line))


def _texto_reemplazar(interp, r, a, line):
    viejo = _arg_texto(interp, "reemplazar", a[0], line)
    nuevo = _arg_texto(interp, "reemplazar", a[1], line)
    return r.replace(viejo, nuevo)


def _texto_partir(interp, r, a, line):
    return r.split(_arg_texto(interp, "partir", a[0], line))


def _texto_indice(interp, r, a, line):
    return float(r.find(_arg_texto(interp, "indice", a[0], line)))


# --- lista ---
def _lista_longitud(interp, r, a, line):
    return float(len(r))


def _lista_agregar(interp, r, a, line):
    r.append(a[0])
    return r


def _lista_invertir(interp, r, a, line):
    r.reverse()                            # in situ, como 'agregar'
    return r


def _lista_ordenar(interp, r, a, line):
    try:
        r.sort()                           # in situ:  l.ordenar();
    except TypeError:
        interp.fail(line, "'ordenar' no sabe comparar esos elementos "
                          "(usa todos números o todos textos)")
    return r


def _lista_contiene(interp, r, a, line):
    return any(equal(x, a[0]) for x in r)


def _lista_indice(interp, r, a, line):
    for i, x in enumerate(r):
        if equal(x, a[0]):
            return float(i)
    return -1.0


def _lista_primero(interp, r, a, line):
    if not r:
        interp.fail(line, "'primero': la lista está vacía")
    return r[0]


def _lista_ultimo(interp, r, a, line):
    if not r:
        interp.fail(line, "'ultimo': la lista está vacía")
    return r[-1]


def _lista_borrar(interp, r, a, line):
    return r.pop(_arg_indice(interp, "borrar", a[0], len(r), line))


def _lista_vaciar(interp, r, a, line):
    r.clear()
    return r


# --- diccionario ---
def _dic_longitud(interp, r, a, line):
    return float(len(r))


def _dic_claves(interp, r, a, line):
    return list(r.keys())


def _dic_valores(interp, r, a, line):
    return list(r.values())


def _dic_tiene(interp, r, a, line):
    return _arg_texto(interp, "tiene", a[0], line) in r


def _dic_borrar(interp, r, a, line):
    clave = _arg_texto(interp, "borrar", a[0], line)
    if clave not in r:
        interp.fail(line, f"'borrar': la clave '{clave}' no existe en el diccionario "
                          f"(tiene: {', '.join(render(k) for k in r) or 'ninguna'})")
    return r.pop(clave)


def _dic_fusionar(interp, r, a, line):
    otro = a[0]
    if not isinstance(otro, dict):
        interp.fail(line, f"'fusionar' necesita un diccionario (recibió: {type_name(otro)})")
    nuevo = dict(r)
    nuevo.update(otro)
    return nuevo


# --- número ---
def _num_redondear(interp, r, a, line):
    if not a:
        return float(round(r))
    dec = _arg_numero(interp, "redondear", a[0], line)
    if dec < 0 or dec != int(dec):
        interp.fail(line, f"'redondear' espera decimales enteros >= 0 "
                          f"(recibió: {fmt_number(dec)})")
    return float(round(r, int(dec)))


def _num_absoluto(interp, r, a, line):
    return abs(r)


def _num_piso(interp, r, a, line):
    return float(math.floor(r))


def _num_techo(interp, r, a, line):
    return float(math.ceil(r))


METODOS = {
    "texto": {
        "longitud": (0, 0, _texto_longitud),
        "mayusculas": (0, 0, _texto_mayusculas),
        "minusculas": (0, 0, _texto_minusculas),
        "recortar": (0, 0, _texto_recortar),
        "contiene": (1, 1, _texto_contiene),
        "empiezaPor": (1, 1, _texto_empieza),
        "terminaPor": (1, 1, _texto_termina),
        "reemplazar": (2, 2, _texto_reemplazar),
        "partir": (1, 1, _texto_partir),
        "indice": (1, 1, _texto_indice),
    },
    "lista": {
        "longitud": (0, 0, _lista_longitud),
        "agregar": (1, 1, _lista_agregar),
        "invertir": (0, 0, _lista_invertir),
        "ordenar": (0, 0, _lista_ordenar),
        "contiene": (1, 1, _lista_contiene),
        "indice": (1, 1, _lista_indice),
        "primero": (0, 0, _lista_primero),
        "ultimo": (0, 0, _lista_ultimo),
        "borrar": (1, 1, _lista_borrar),
        "vaciar": (0, 0, _lista_vaciar),
    },
    "diccionario": {
        "longitud": (0, 0, _dic_longitud),
        "claves": (0, 0, _dic_claves),
        "valores": (0, 0, _dic_valores),
        "tiene": (1, 1, _dic_tiene),
        "borrar": (1, 1, _dic_borrar),
        "fusionar": (1, 1, _dic_fusionar),
    },
    "número": {
        "redondear": (0, 1, _num_redondear),
        "absoluto": (0, 0, _num_absoluto),
        "piso": (0, 0, _num_piso),
        "techo": (0, 0, _num_techo),
    },
}


def metodos_de(v):
    """El diccionario de métodos que acepta un valor, o None si no tiene."""
    if isinstance(v, str):
        return "texto"
    if isinstance(v, list):
        return "lista"
    if isinstance(v, dict):
        return "diccionario"
    if isinstance(v, float) and not isinstance(v, bool):
        return "número"
    return None


# --------------------------------------------------------------- intérprete
class Interpreter:
    def __init__(self, filename=None):
        self.env = Env()
        self.filename = filename          # archivo en curso (para 'importar')
        self.modulos = {}                 # ruta -> diccionario del módulo
        self._declare_natives()

    # ---------------------------------------------------------- natives
    def _declare_natives(self):
        def _longitud(interp, a, line):
            v = a[0]
            if isinstance(v, (str, list, dict)):
                return float(len(v))
            interp.fail(line, f"'longitud' necesita un texto, una lista o un diccionario "
                              f"(recibió: {type_name(v)})")

        def _claves(interp, a, line):
            d = a[0]
            if not isinstance(d, dict):
                interp.fail(line, f"'claves' necesita un diccionario (recibió: {type_name(d)})")
            return list(d.keys())

        def _valores(interp, a, line):
            d = a[0]
            if not isinstance(d, dict):
                interp.fail(line, f"'valores' necesita un diccionario (recibió: {type_name(d)})")
            return list(d.values())

        def _entrada(interp, a, line):
            prompt = a[0] if a else ""
            if not isinstance(prompt, str):
                interp.fail(line, f"'entrada' espera un texto como mensaje "
                                  f"(recibió: {type_name(prompt)})")
            return interp.leer_entrada(prompt, line)

        def _rango(interp, a, line):
            nums = []
            for i, x in enumerate(a):
                if not isinstance(x, float) or isinstance(x, bool):
                    interp.fail(line, f"'rango' necesita números (argumento {i + 1}: {type_name(x)})")
                nums.append(x)
            if len(nums) == 1:
                inicio, fin, paso = 0.0, nums[0], 1.0
            elif len(nums) == 2:
                inicio, fin, paso = nums[0], nums[1], 1.0
            else:
                inicio, fin, paso = nums
            if paso == 0:
                interp.fail(line, "'rango' no puede tener paso 0")
            delta = (fin - inicio) / paso
            if delta <= 0:
                return []
            # techo con tolerancia: 0.1+0.1+... y los pasos negativos
            total = int(math.ceil(delta - 1e-9))
            return [float(inicio + paso * i) for i in range(total)]

        def _agregar(interp, a, line):
            lista, valor = a
            if not isinstance(lista, list):
                interp.fail(line, f"'agregar' necesita una lista (recibió: {type_name(lista)})")
            lista.append(valor)
            return lista

        def _texto(interp, a, line):
            return display(a[0])

        def _numero(interp, a, line):
            v = a[0]
            if isinstance(v, bool):
                return 1.0 if v else 0.0
            if isinstance(v, float):
                return v
            if isinstance(v, str):
                t = v.strip().replace(",", ".")
                try:
                    return float(t)
                except ValueError:
                    interp.fail(line, f"'numero' no puede convertir {v!r} a número")
            interp.fail(line, f"'numero' no sabe convertir un {type_name(v)}")

        def _tipo(interp, a, line):
            return type_name(a[0])

        for name, fn, lo, hi in (
            ("longitud", _longitud, 1, 1),
            ("rango", _rango, 1, 3),
            ("agregar", _agregar, 2, 2),
            ("claves", _claves, 1, 1),
            ("valores", _valores, 1, 1),
            ("entrada", _entrada, 0, 1),
            ("texto", _texto, 1, 1),
            ("numero", _numero, 1, 1),
            ("tipo", _tipo, 1, 1),
        ):
            self.env.declare(name, Nativa(name, fn, lo, hi), True, 0)

    # ---------------------------------------------------------- entrada
    def leer_entrada(self, prompt: str, line: int) -> str:
        """`entrada("¿edad?")`: primero el manejador instalado, si no la consola."""
        if prompt:
            try:
                sys.stdout.write(prompt)              # se ve en la salida aunque haya diálogo
                sys.stdout.flush()
            except Exception:
                pass                                  # salida capturada (StringIO)

        if _handler_entrada is not None:
            try:
                valor = _handler_entrada(prompt)
            except RunError:
                raise
            except Exception as e:
                self.fail(line, f"entrada(): {e}")
            return "" if valor is None else str(valor)

        lectura = getattr(sys.stdin, "readline", None)
        if lectura is None:
            self.fail(line, "entrada() necesita datos: ejecuta el programa con "
                            "eco.exe en una terminal o en el IDE de escritorio")
        try:
            linea = lectura()
        except Exception:
            linea = ""
        if not linea:
            self.fail(line, "entrada(): se acabó la entrada (fin de stdin)")
        return linea.rstrip("\r\n")

    # ---------------------------------------------------------- errores
    @staticmethod
    def fail(line, msg):
        raise RunError(f"[línea {line}] {msg}")

    # ------------------------------------------------------ programa
    def run(self, program: Program):
        try:
            for stmt in program.body:
                self.exec(stmt, self.env)
        except _Romper as e:
            self.fail(e.line, "'romper' solo puede usarse dentro de un bucle")
        except _Continuar as e:
            self.fail(e.line, "'continuar' solo puede usarse dentro de un bucle")
        except _Devolver as e:
            self.fail(e.line, "'devuelve' solo puede usarse dentro de una función")

    # -------------------------------------------------- instrucciones
    def exec(self, node, env: Env):
        hook = _hook_debug
        if hook is not None and getattr(node, "line", None):
            hook(node.line, self.snapshot(env))      # puede lanzar Detener
        kind = type(node)

        if kind is Let:
            value = self.eval(node.value, env)
            env.declare(node.name, value, node.const, node.line)
            return None

        if kind is Assign:
            env.set(node.name, self.eval(node.value, env), node.line)
            return None

        if kind is IndexAssign:
            target = self.eval(node.target, env)
            index = self.eval(node.index, env)
            value = self.eval(node.value, env)
            if isinstance(target, dict):            # crea la clave si no existe
                target[self._clave(index, node.line)] = value
                return None
            if not isinstance(target, list):
                self.fail(node.line, f"Solo se puede asignar dentro de una lista "
                                     f"o de un diccionario (recibió: {type_name(target)})")
            i = self._index(target, index, node.line, asignable=True)
            target[i] = value
            return None

        if kind is AttrAssign:
            # persona.nombre = "Ana";   (siempre sobre un diccionario)
            target = self.eval(node.target, env)
            if not isinstance(target, dict):
                self.fail(node.line, f"Solo se puede escribir '.{node.name}' dentro de "
                                     f"un diccionario (recibió: {type_name(target)})")
            target[node.name] = self.eval(node.value, env)
            return None

        if kind is Incremento:
            # i++;  i--;
            valor = env.get(node.name, node.line)
            if not isinstance(valor, float) or isinstance(valor, bool):
                self.fail(node.line, f"'{node.name}{'++' if node.delta > 0 else '--'}' "
                                     f"necesita un número (recibió: {type_name(valor)})")
            env.set(node.name, valor + node.delta, node.line)
            return None

        if kind is Importar:
            self._importar(node, env)
            return None

        if kind is Print:
            print(" ".join(display(self.eval(a, env)) for a in node.args))
            return None

        if kind is If:
            cond = self._condition(node.cond, env, node.line, "si")
            branch = node.then_body if cond else node.else_body
            if branch is not None:
                self.exec(branch, env)
            return None

        if kind is While:
            while self._condition(node.cond, env, node.line, "mientras"):
                try:
                    self.exec(node.body, env)
                except _Romper:
                    break
                except _Continuar:
                    continue
            return None

        if kind is For:
            loop = Env(env)
            if node.init is not None:
                self.exec(node.init, loop)
            while node.cond is None or self._condition(node.cond, loop, node.line, "para"):
                try:
                    self.exec(node.body, loop)
                except _Romper:
                    break
                except _Continuar:
                    pass
                if node.step is not None:
                    self.exec(node.step, loop)
            return None

        if kind is ForIn:
            items = self.eval(node.iterable, env)
            if isinstance(items, dict):
                items = list(items.keys())          # recorre las claves
            elif not isinstance(items, list):
                self.fail(node.line, f"'para x en ...' necesita una lista o un diccionario "
                                     f"(recibió: {type_name(items)})")
            loop = Env(env)
            for item in items:
                if node.name in loop.vars:
                    loop.vars[node.name] = (item, False)
                else:
                    loop.declare(node.name, item, False, node.line)
                try:
                    self.exec(node.body, loop)
                except _Romper:
                    break
                except _Continuar:
                    continue
            return None

        if kind is Block:
            inner = Env(env)
            for stmt in node.body:
                self.exec(stmt, inner)
            return None

        if kind is Function:
            f = Funcion(node.name, node.params, node.body, env)
            env.declare(node.name, f, False, node.line)
            return None

        if kind is Return:
            value = self.eval(node.value, env) if node.value is not None else None
            raise _Devolver(value, node.line)

        if kind is Break:
            raise _Romper(node.line)

        if kind is Continue:
            raise _Continuar(node.line)

        if kind is ExprStatement:
            self.eval(node.value, env)
            return None

        return self.eval(node, env)

    def _condition(self, node, env, line, donde: str) -> bool:
        v = self.eval(node, env)
        if not isinstance(v, bool):
            self.fail(line, f"La condición de '{donde}' debe ser verdadero o falso "
                            f"(recibió: {type_name(v)})")
        return v

    # ----------------------------------------------------- expresiones
    def eval(self, node, env: Env):
        kind = type(node)

        if kind is Number:
            return node.value
        if kind is Boolean:
            return node.value
        if kind is Null:
            return None
        if kind is Text:
            return self.render_text(node.value, env, node.line)
        if kind is Lista:
            return [self.eval(x, env) for x in node.items]
        if kind is Diccionario:
            d = {}
            for k, v in node.pairs:
                key = k if isinstance(k, str) else self.eval(k, env)
                if isinstance(key, float) and not isinstance(key, bool):
                    key = fmt_number(key)
                if not isinstance(key, str):
                    self.fail(node.line, f"Las claves de un diccionario deben ser textos "
                                         f"(recibió: {type_name(key)})")
                d[key] = self.eval(v, env)
            return d
        if kind is Var:
            return env.get(node.name, node.line)
        if kind is Unary:
            return self._unary(node, env)
        if kind is Binary:
            return self._binary(node, env)
        if kind is Index:
            return self._index_get(node, env)
        if kind is Attribute:
            return self._atributo_de(self.eval(node.target, env), node.name, node.line)
        if kind is Call:
            return self._call(node, env)

        raise RunError(f"Nodo desconocido en el AST: {kind.__name__}")

    def _unary(self, node, env):
        v = self.eval(node.operand, env)
        if node.op == "no":
            if not isinstance(v, bool):
                self.fail(node.line, f"'no' solo funciona con booleanos (recibió: {type_name(v)})")
            return not v
        if not isinstance(v, float) or isinstance(v, bool):
            self.fail(node.line, f"El signo '-' necesita un número (recibió: {type_name(v)})")
        return -v

    def _binary(self, node, env):
        op, line = node.op, node.line

        # --- evaluación corta ---
        if op == "y":
            left = self.eval(node.left, env)
            self._require_bool(left, line, "y")
            if not left:
                return False
            right = self.eval(node.right, env)
            self._require_bool(right, line, "y")
            return right
        if op == "o":
            left = self.eval(node.left, env)
            self._require_bool(left, line, "o")
            if left:
                return True
            right = self.eval(node.right, env)
            self._require_bool(right, line, "o")
            return right

        left = self.eval(node.left, env)
        right = self.eval(node.right, env)

        if op == "==":
            return equal(left, right)
        if op == "!=":
            return not equal(left, right)

        if op == "+":
            if isinstance(left, float) and isinstance(right, float) \
                    and not isinstance(left, bool) and not isinstance(right, bool):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            self.fail(line, f"'+' no puede combinar {type_name(left)} y {type_name(right)} "
                            "(usa dos números, dos textos o dos listas)")

        if op in ("<", "<=", ">", ">="):
            if type(left) is not type(right) or not isinstance(left, (float, str)):
                self.fail(line, f"No se puede comparar {type_name(left)} con {type_name(right)}")
            return {"<": left < right, "<=": left <= right,
                    ">": left > right, ">=": left >= right}[op]

        # --- aritmética ---
        for v, quién in ((left, "izquierdo"), (right, "derecho")):
            if not isinstance(v, float) or isinstance(v, bool):
                self.fail(line, f"El operador '{op}' necesita números "
                                f"(valor {quién}: {type_name(v)})")

        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                self.fail(line, "División entre cero")
            return left / right
        if op == "%":
            if right == 0:
                self.fail(line, "Módulo entre cero")
            return left % right
        if op == "^":
            try:
                r = left ** right
            except OverflowError:
                self.fail(line, "Desbordamiento al elevar a potencia")
            if isinstance(r, complex):
                self.fail(line, "Potencia inválida con números negativos y exponente decimal")
            return float(r)

        raise RunError(f"[línea {line}] Operador desconocido: {op}")

    @staticmethod
    def _require_bool(v, line, op):
        if not isinstance(v, bool):
            raise RunError(f"[línea {line}] '{op}' necesita booleanos (recibió: {type_name(v)})")

    # --------------------------------------------------------- listas
    def _index(self, target, index, line, asignable=False):
        if not isinstance(index, float) or isinstance(index, bool):
            self.fail(line, f"El índice debe ser un número (recibió: {type_name(index)})")
        if index != int(index):
            self.fail(line, f"El índice debe ser un número entero (recibió: {fmt_number(index)})")
        i = int(index)
        if i < 0:
            i += len(target)
        if i < 0 or i >= len(target):
            accion = "asignar" if asignable else "acceder"
            self.fail(line, f"Índice fuera de rango ({fmt_number(index)}) al {accion}: "
                            f"la lista tiene {len(target)} elemento(s)")
        return i

    def _clave(self, index, line) -> str:
        """La clave de un diccionario: siempre texto (nada de índices numéricos)."""
        if not isinstance(index, str):
            self.fail(line, f"Las claves de un diccionario son textos "
                            f"(recibió: {type_name(index)}); usa d[\"clave\"]")
        return index

    def _index_get(self, node, env):
        target = self.eval(node.target, env)
        index = self.eval(node.index, env)
        if isinstance(target, dict):
            key = self._clave(index, node.line)
            if key not in target:
                self.fail(node.line, f"La clave '{key}' no existe en el diccionario "
                                     f"(tiene: {', '.join(render(k) for k in target) or 'ninguna'})")
            return target[key]
        if isinstance(target, list):
            return target[self._index(target, index, node.line)]
        if isinstance(target, str):
            return target[self._index(target, index, node.line)]
        self.fail(node.line, f"Solo se puede indexar listas, textos y diccionarios "
                             f"(recibió: {type_name(target)})")

    # ------------------------------------------------------ atributos
    def _atributo_de(self, obj, name: str, line: int):
        """persona.nombre -> la clave del diccionario, o su método si no existe."""
        if isinstance(obj, dict):
            if name in obj:                       # la clave gana sobre el método
                return obj[name]
            metodo = METODOS["diccionario"].get(name)
            if metodo:
                return Metodo(obj, name, *metodo)
            self.fail(line, f"El diccionario no tiene la clave '{name}' "
                            f"(tiene: {', '.join(render(k) for k in obj) or 'ninguna'})")
        tipo = metodos_de(obj)
        if tipo:
            metodo = METODOS[tipo].get(name)
            if metodo:
                return Metodo(obj, name, *metodo)
            self.fail(line, f"{type_name(obj)} no tiene el método '{name}' "
                            f"(disponibles: {', '.join(sorted(METODOS[tipo]))})")
        self.fail(line, f"Los {type_name(obj)} no tienen atributos: solo los textos, "
                        f"listas, diccionarios y números admiten '.'")

    # ------------------------------------------------------- módulos
    def _importar(self, node, env: Env):
        """importar "otro.eco" [como alias];  ->  alias es un diccionario."""
        base = Path(self.filename).resolve().parent if self.filename else Path.cwd()
        candidatos = [base / node.nombre]
        if not str(node.nombre).lower().endswith(".eco"):
            candidatos.append(base / (node.nombre + ".eco"))
        ruta = next((c for c in candidatos if c.is_file()), None)
        if ruta is None:
            self.fail(node.line, f"No se encontró el módulo '{node.nombre}' "
                                 f"(buscado en: {base})")

        clave = str(ruta.resolve())
        modulo = self.modulos.get(clave)
        if modulo is None:
            modulo = {}
            self.modulos[clave] = modulo          # ya está en curso: corta los ciclos
            try:
                texto = ruta.read_text(encoding="utf-8")
            except OSError as e:
                self.fail(node.line, f"No se pudo leer '{ruta.name}': {e}")
            try:
                arbol = parse(tokenize(texto))
            except (LexError, ParseError) as e:
                self.fail(node.line, f"Error en el módulo '{ruta.name}': {e}")

            entorno = Env(self.env)               # ve las nativas, no las locales
            anterior = self.filename
            self.filename = clave                 # las rutas relativas salen de aquí
            try:
                for stmt in arbol.body:
                    self.exec(stmt, entorno)
            except _Romper:
                self.fail(node.line, "'romper' fuera de un bucle en el módulo "
                                     f"'{ruta.name}'")
            except _Continuar:
                self.fail(node.line, "'continuar' fuera de un bucle en el módulo "
                                     f"'{ruta.name}'")
            except _Devolver:
                self.fail(node.line, "'devuelve' fuera de una función en el módulo "
                                     f"'{ruta.name}'")
            finally:
                self.filename = anterior
            for k, (v, _c) in entorno.vars.items():
                modulo[k] = v

        alias = node.alias or Path(node.nombre).stem
        if not alias.isidentifier() or alias in KEYWORDS:
            self.fail(node.line, f"'{alias}' no sirve como nombre de módulo; usa: "
                                 f'importar "{node.nombre}" como nombre')
        _, slot = env.lookup(alias)
        if slot is not None:
            if slot[0] is modulo:
                return                            # ya estaba importado
            self.fail(node.line, f"'{alias}' ya está declarada en este ámbito")
        env.declare(alias, modulo, True, node.line)   # el módulo no se reasigna

    # ------------------------------------------------------ depuración
    @staticmethod
    def snapshot(env: Env) -> dict:
        """Variables visibles en este punto (para el depurador), de fuera adentro."""
        cadena, e = [], env
        while e is not None:
            cadena.append(e)
            e = e.parent
        valores, orden = {}, []
        for e in reversed(cadena):
            for k, (v, c) in e.vars.items():
                if isinstance(v, Nativa):
                    continue                     # longitus, rango... no interesan
                if k not in valores:
                    orden.append(k)
                txt = render(v)
                valores[k] = (txt[:97] + "…" if len(txt) > 100 else txt) + \
                             (" (const)" if c else "")
        return {k: valores[k] for k in orden}

    # ------------------------------------------------------ llamadas
    def _call(self, node, env):
        callee = self.eval(node.callee, env)
        args = [self.eval(a, env) for a in node.args]
        line = node.line

        if isinstance(callee, Metodo):
            n = len(args)
            if n < callee.min_args or n > callee.max_args:
                self.fail(line, f"'{callee.nombre}' espera {callee.min_args}"
                                f"{'-' + str(callee.max_args) if callee.max_args != callee.min_args else ''}"
                                f" argumento(s) y recibe {n}")
            return callee.fn(self, callee.receptor, args, line)

        if isinstance(callee, Nativa):
            n = len(args)
            if n < callee.min_args or n > callee.max_args:
                self.fail(line, f"'{callee.name}' espera {callee.min_args}"
                                f"{'-' + str(callee.max_args) if callee.max_args != callee.min_args else ''}"
                                f" argumento(s) y recibe {n}")
            return callee.fn(self, args, line)

        if isinstance(callee, Funcion):
            if len(args) != len(callee.params):
                self.fail(line, f"'{callee.name}' espera {len(callee.params)} parámetro(s) "
                                f"y recibe {len(args)}")
            local = Env(callee.env)
            for p, a in zip(callee.params, args):
                local.declare(p, a, False, line)
            try:
                self.exec(callee.body, local)
            except _Devolver as r:
                return r.value
            except _Romper as e:
                self.fail(e.line, "'romper' solo puede usarse dentro de un bucle")
            except _Continuar as e:
                self.fail(e.line, "'continuar' solo puede usarse dentro de un bucle")
            return None

        self.fail(line, f"Solo se pueden llamar funciones (recibió: {type_name(callee)})")

    # -------------------------------------------------- textos con ${...}
    def render_text(self, raw: str, env: Env, line: int) -> str:
        """Escapa \\n, \\t, \\"...  y sustituye ${expresión} por su valor."""
        if "${" not in raw and "\\" not in raw:
            return raw

        out = []
        i, n = 0, len(raw)
        while i < n:
            ch = raw[i]

            if ch == "\\" and i + 1 < n:
                nx = raw[i + 1]
                if nx == "$":                 # \$ -> dólar literal, sin interpolar
                    out.append("$")
                else:
                    out.append(ESCAPES.get(nx, "\\" + nx))
                i += 2
                continue

            if ch == "$" and i + 1 < n and raw[i + 1] == "{":
                end = self._find_close(raw, i + 2, line)
                src = raw[i + 2:end]
                out.append(display(self._eval_snippet(src, env, line)))
                i = end + 1
                continue

            out.append(ch)
            i += 1
        return "".join(out)

    @staticmethod
    def _find_close(raw: str, start: int, line: int) -> int:
        """Busca el '}' de cierre respetando llaves y comillas anidadas."""
        depth, i, n, quote = 1, start, len(raw), None
        while i < n:
            ch = raw[i]
            if ch == "\\":                       # \" dentro de la interpolación
                i += 2
                continue
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        raise RunError(f"[línea {line}] Interpolación sin cerrar: falta '}}' en ${{...}}")

    @staticmethod
    def _eval_snippet(src: str, env: Env, line: int):
        """Analiza y evalúa la expresión de dentro de ${...}.

        Si el texto exterior iba entre comillas dobles, los `\"` de dentro
        (p. ej.  ${d[\"clave\"]}) se convierten en comillas normales.
        """
        try:
            expr = parse_expression(tokenize(src.replace('\\"', '"')))
        except (LexError, ParseError) as e:
            raise RunError(f"[línea {line}] Error dentro de ${{{src.strip()}}}: {e}") from None
        return _Snippet().eval(expr, env)


class _Snippet(Interpreter):
    """Intérprete mínimo para evaluar las expresiones de la interpolación."""

    def __init__(self):
        self.filename = None        # no necesita nativas: usa el mismo entorno
        self.modulos = {}

    def _declare_natives(self):
        pass
