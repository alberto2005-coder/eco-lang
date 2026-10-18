"""Analizador sintáctico (parser) + definición del AST.

Descenso recursivo: cada producción de la gramática es una función.

    programa    := instrucción*
    instrucción := escribe expresión ("," expresión)* ";"
                 | ("variable" | "const") IDENT "=" expresión ";"
                 | IDENT "=" expresión ";"
                 | IDENT ("[" expresión "]" | "." IDENT)* "=" expresión ";"
                 | IDENT ("++" | "--") ";"
                 | importar CADENA (como IDENT)? ";"
                 | si [ (] exp [) ] instrucción (sino instrucción)?
                 | mientras [ (] exp [) ] instrucción
                 | para ( ... ) instrucción
                 | funcion IDENT "(" (IDENT ("," IDENT)*)? ")" bloque
                 | devuelve [expresión] ";"
                 | romper ";" | continuar ";"
                 | bloque
                 | expresión ";"

    expresión   := ... | expresión "." IDENT | expresión "." IDENT "(" args ")"
"""

from dataclasses import dataclass


class ParseError(Exception):
    """Error detectado durante el análisis sintáctico."""


# ------------------------------------------------------------ AST: expresiones
@dataclass
class Number:
    value: float


@dataclass
class Text:
    value: str          # crudo: puede contener \n y ${expresión}
    line: int = 0


@dataclass
class Boolean:
    value: bool


@dataclass
class Null:
    line: int


@dataclass
class Var:
    name: str
    line: int


@dataclass
class Lista:
    items: list
    line: int


@dataclass
class Diccionario:
    """{"nombre": "Ana", edad: 30}  — pares de (clave, valor)."""
    pairs: list            # [(clave_texto_o_nodo, valor_nodo)]
    line: int


@dataclass
class Unary:
    op: str             # "-" o "no"
    operand: object
    line: int


@dataclass
class Binary:
    op: str             # + - * / % ^ == != < <= > >= y o
    left: object
    right: object
    line: int


@dataclass
class Index:
    target: object
    index: object
    line: int


@dataclass
class Attribute:
    """persona.nombre  ->  acceso a una clave de diccionario o a un método."""
    target: object
    name: str
    line: int


@dataclass
class Call:
    callee: object
    args: list
    line: int


# ---------------------------------------------------------- AST: instrucciones
@dataclass
class Let:
    name: str
    value: object
    line: int
    const: bool = False


@dataclass
class Assign:
    name: str
    value: object
    line: int


@dataclass
class IndexAssign:
    target: object
    index: object
    value: object
    line: int


@dataclass
class AttrAssign:
    """persona.nombre = "Ana";"""
    target: object
    name: str
    value: object
    line: int


@dataclass
class Incremento:
    """i++;  i--;  (también como paso de 'para')"""
    name: str
    delta: int            # +1 o -1
    line: int


@dataclass
class Importar:
    """importar "otro.eco" [como alias];"""
    nombre: str
    alias: object          # nombre del módulo o None
    line: int


@dataclass
class Print:
    args: list
    line: int


@dataclass
class If:
    cond: object
    then_body: object
    else_body: object       # puede ser None
    line: int


@dataclass
class While:
    cond: object
    body: object
    line: int


@dataclass
class For:
    init: object            # Let | ExprStatement | None
    cond: object            # puede ser None (bucle infinito)
    step: object            # puede ser None
    body: object
    line: int


@dataclass
class ForIn:
    name: str
    iterable: object
    body: object
    line: int


@dataclass
class Block:
    body: list


@dataclass
class Function:
    name: str
    params: list
    body: object
    line: int


@dataclass
class Return:
    value: object
    line: int


@dataclass
class Break:
    line: int


@dataclass
class Continue:
    line: int


@dataclass
class ExprStatement:
    value: object
    line: int


@dataclass
class Program:
    body: list


# -------------------------------------------------------------------- Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---- utilidades ----
    def peek(self):
        return self.tokens[self.pos]

    def previous(self):
        return self.tokens[self.pos - 1]

    def check(self, ttype: str) -> bool:
        return self.peek().type == ttype

    def advance(self):
        tok = self.peek()
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def match(self, *types):
        for ttype in types:
            if self.check(ttype):
                return self.advance()
        return None

    def expect(self, ttype: str, msg: str):
        if self.check(ttype):
            return self.advance()
        tok = self.peek()
        raise ParseError(f"[línea {tok.line}, columna {tok.col}] {msg} (encontrado: {tok.type})")

    def error(self, msg: str):
        tok = self.peek()
        raise ParseError(f"[línea {tok.line}, columna {tok.col}] {msg}")

    # ---- programa e instrucciones ----
    def parse(self) -> Program:
        body = []
        while not self.check("EOF"):
            body.append(self.statement())
        return Program(body)

    def statement(self):
        if self.match("ESCRIBE"):
            line = self.previous().line
            args = [self.expression()]
            while self.match("COMMA"):
                args.append(self.expression())
            self.expect("SEMI", "Falta ';' al final de 'escribe'")
            return Print(args, line)

        if self.match("VARIABLE", "CONST"):
            return self.declaration(const=self.previous().type == "CONST")

        if self.match("SI"):
            return self.if_statement()

        if self.match("MIENTRAS"):
            line = self.previous().line
            cond = self.condicion("mientras")
            return While(cond, self.statement(), line)

        if self.match("IMPORTAR"):
            line = self.previous().line
            nombre = self.expect("STRING", "Después de 'importar' falta el archivo "
                                           "entre comillas")
            alias = None
            if self.match("COMO"):
                alias = self.expect("IDENT", "Después de 'como' falta el nombre del "
                                             "módulo").value
            self.expect("SEMI", "Falta ';' después de 'importar'")
            return Importar(nombre.value, alias, line)

        if self.match("PARA"):
            return self.for_statement()

        if self.match("FUNCION"):
            return self.function_statement()

        if self.match("DEVUELVE"):
            line = self.previous().line
            value = None if self.check("SEMI") else self.expression()
            self.expect("SEMI", "Falta ';' después de 'devuelve'")
            return Return(value, line)

        if self.match("ROMPER"):
            line = self.previous().line
            self.expect("SEMI", "Falta ';' después de 'romper'")
            return Break(line)

        if self.match("CONTINUAR"):
            line = self.previous().line
            self.expect("SEMI", "Falta ';' después de 'continuar'")
            return Continue(line)

        if self.match("LBRACE"):
            return self.block()

        # asignación simple:  x = expresión;
        if self.check("IDENT") and self._next_type() == "ASSIGN":
            name = self.advance()
            self.advance()
            value = self.expression()
            self.expect("SEMI", "Falta ';' al final de la asignación")
            return Assign(name.value, value, name.line)

        # i++ / i--  (instrucción independiente)
        if self.check("IDENT") and self._next_type() in ("INC", "DEC"):
            tok = self.advance()
            op = self.advance()
            self.expect("SEMI", "Falta ';' después del incremento")
            return Incremento(tok.value, 1 if op.type == "INC" else -1, tok.line)

        # asignación por índice o por atributo:  lista[0] = ...;  persona.nombre = ...;
        # (si tras la cadena no hay '=', no era una asignación: se retrocede y
        # se analiza como expresión, p. ej.  lista.ordenar();)
        if self.check("IDENT") and self._next_type() in ("LBRACKET", "DOT"):
            inicio = self.pos
            target = self._lvalue_chain()
            if self.check("ASSIGN"):
                self.advance()
                value = self.expression()
                self.expect("SEMI", "Falta ';' al final de la asignación")
                if isinstance(target, Index):
                    return IndexAssign(target.target, target.index, value, target.line)
                if isinstance(target, Attribute):
                    return AttrAssign(target.target, target.name, value, target.line)
                self.error("Solo se puede asignar a un índice o a un atributo")
            self.pos = inicio

        # expresión usada como instrucción (el resultado se descarta)
        line = self.peek().line
        value = self.expression()
        self.expect("SEMI", "Falta ';' al final de la instrucción")
        return ExprStatement(value, line)

    def _next_type(self) -> str:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].type
        return "EOF"

    def condicion(self, quien: str):
        """La condición de 'si'/'mientras': admite  si cond { }  y  si (cond) { }.

        Los paréntesis de la segunda forma no hacen falta: `primary` ya los
        trata como agrupación, así que se parsea una expresión y ya.
        """
        if self.check("EOF"):
            self.error(f"Después de '{quien}' falta la condición")
        return self.expression()

    def _lvalue_chain(self):
        """lista[0][1]  ->  Index(Index(lista, 0), 1)
        persona.nombre  ->  Attribute(Var(persona), nombre)"""
        tok = self.advance()                      # IDENT
        target = Var(tok.value, tok.line)
        while True:
            if self.match("LBRACKET"):
                idx = self.expression()
                self.expect("RBRACKET", "Falta ']' que cierra el índice")
                target = Index(target, idx, tok.line)
            elif self.match("DOT"):
                nombre = self.expect("IDENT", "Después de '.' falta un nombre")
                target = Attribute(target, nombre.value, tok.line)
            else:
                return target

    def declaration(self, const: bool, con_semi: bool = True):
        line = self.previous().line
        name = self.expect("IDENT", "Después de 'variable' falta el nombre")
        self.expect("ASSIGN", "Falta '=' en la declaración")
        value = self.expression()
        if con_semi:
            self.expect("SEMI", "Falta ';' al final de la declaración")
        return Let(name.value, value, line, const)

    def if_statement(self):
        line = self.previous().line
        cond = self.condicion("si")
        then_body = self.statement()
        else_body = None
        if self.match("SINO"):
            else_body = self.statement()          # también admite "sino si"
        return If(cond, then_body, else_body, line)

    def for_statement(self):
        line = self.previous().line
        self.expect("LPAREN", "Después de 'para' falta '('")

        # para (x en lista)
        if self.check("IDENT") and self._next_type() == "EN":
            name = self.advance()
            self.advance()                        # 'en'
            iterable = self.expression()
            self.expect("RPAREN", "Falta ')' que cierra 'para'")
            return ForIn(name.value, iterable, self.statement(), line)

        # para (variable i = 0; i < 10; i = i + 1)   /   para (; cond; paso)
        init = None
        if self.match("VARIABLE", "CONST"):
            init = self.declaration(const=self.previous().type == "CONST", con_semi=False)
        elif not self.check("SEMI"):
            self.error("Se esperaba 'variable i = 0', 'x en lista' o ';'")

        self.expect("SEMI", "Falta ';' tras la inicialización de 'para'")
        cond = None if self.check("SEMI") else self.expression()
        self.expect("SEMI", "Falta ';' tras la condición de 'para'")

        # el paso es una instrucción sin ';'  (p. ej.  i = i + 1  o  i++)
        step = None
        if not self.check("RPAREN"):
            if self.check("IDENT") and self._next_type() in ("INC", "DEC"):
                tok = self.advance()
                op = self.advance()
                step = Incremento(tok.value, 1 if op.type == "INC" else -1, tok.line)
            elif self.check("IDENT") and self._next_type() == "ASSIGN":
                tok = self.advance()
                self.advance()                       # '='
                step = Assign(tok.value, self.expression(), tok.line)
            else:
                step = self.expression()

        self.expect("RPAREN", "Falta ')' que cierra 'para'")
        return For(init, cond, step, self.statement(), line)

    def function_statement(self):
        line = self.previous().line
        name = self.expect("IDENT", "Después de 'funcion' falta el nombre")
        self.expect("LPAREN", "Falta '(' después del nombre de la función")
        params = []
        if not self.check("RPAREN"):
            params.append(self.expect("IDENT", "Se esperaba un parámetro").value)
            while self.match("COMMA"):
                params.append(self.expect("IDENT", "Se esperaba un parámetro").value)
        self.expect("RPAREN", "Falta ')' que cierra los parámetros")
        if self.match("LBRACE"):
            body = self.block()
        else:
            body = Block([self._function_body_expr()])
        return Function(name.value, params, body, line)

    def _function_body_expr(self):
        """Admite 'funcion f() = expresión;' como azúcar de una devolución."""
        self.expect("ASSIGN", "Falta '{' o '= expresión;' tras la cabecera")
        value = self.expression()
        self.expect("SEMI", "Falta ';' al final de la función")
        return Return(value, self.previous().line)

    def block(self) -> Block:
        body = []
        while not self.check("RBRACE") and not self.check("EOF"):
            body.append(self.statement())
        self.expect("RBRACE", "Falta '}' que cierra el bloque")
        return Block(body)

    # ---- expresiones por niveles de precedencia ----
    def expression(self):
        return self.logic_or()

    def logic_or(self):
        expr = self.logic_and()
        while True:
            op = self.match("O")
            if not op:
                break
            expr = Binary("o", expr, self.logic_and(), op.line)
        return expr

    def logic_and(self):
        expr = self.comparison()
        while True:
            op = self.match("Y")
            if not op:
                break
            expr = Binary("y", expr, self.comparison(), op.line)
        return expr

    def comparison(self):
        expr = self.term()
        while True:
            op = self.match("EQ", "NE", "LT", "LE", "GT", "GE")
            if not op:
                break
            expr = Binary(op.value, expr, self.term(), op.line)
        return expr

    def term(self):
        expr = self.factor()
        while True:
            op = self.match("PLUS", "MINUS")
            if not op:
                break
            expr = Binary(op.value, expr, self.factor(), op.line)
        return expr

    def factor(self):
        expr = self.unary()
        while True:
            op = self.match("STAR", "SLASH", "PERCENT")
            if not op:
                break
            expr = Binary(op.value, expr, self.unary(), op.line)
        return expr

    def unary(self):
        op = self.match("MINUS", "NO")
        if op:
            return Unary(op.value, self.unary(), op.line)
        return self.power()

    def power(self):
        """^ es asociativo por la derecha: 2 ^ 3 ^ 2 = 2 ^ (3 ^ 2)"""
        base = self.postfix()
        if self.match("POW"):
            return Binary("^", base, self.unary(), self.previous().line)
        return base

    def postfix(self):
        expr = self.primary()
        while True:
            if self.match("LBRACKET"):
                idx = self.expression()
                self.expect("RBRACKET", "Falta ']' que cierra el índice")
                expr = Index(expr, idx, getattr(expr, "line", self.previous().line))
            elif self.match("DOT"):
                nombre = self.expect("IDENT", "Después de '.' falta un nombre")
                expr = Attribute(expr, nombre.value, getattr(expr, "line", nombre.line))
            elif self.match("LPAREN"):
                args = []
                if not self.check("RPAREN"):
                    args.append(self.expression())
                    while self.match("COMMA"):
                        args.append(self.expression())
                self.expect("RPAREN", "Falta ')' que cierra la llamada")
                expr = Call(expr, args, getattr(expr, "line", self.previous().line))
            else:
                return expr

    def _dict_pair(self):
        """Clave: "texto" (o identificador sin comillas) y después ':'"""
        tok = self.peek()
        if self._next_type() != "DOSPUNTOS":
            self.error('Las claves de un diccionario van entre comillas: {"clave": valor}')
        if tok.type == "STRING":
            self.advance()
            self.advance()
            key = Text(tok.value, tok.line)      # se evalúa al ejecutar (admite ${})
        elif tok.type == "IDENT":
            self.advance()
            self.advance()
            key = tok.value                      # {edad: 30} equivale a {"edad": 30}
        else:
            self.error('La clave debe ser un texto o un identificador: {"clave": valor}')
        return (key, self.expression())

    def primary(self):
        if self.match("NUMBER"):
            return Number(self.previous().value)
        if self.match("STRING"):
            tok = self.previous()
            return Text(tok.value, tok.line)
        if self.match("VERDADERO"):
            return Boolean(True)
        if self.match("FALSO"):
            return Boolean(False)
        if self.match("NULO"):
            return Null(self.previous().line)
        if self.match("LBRACKET"):
            line = self.previous().line
            items = []
            if not self.check("RBRACKET"):
                items.append(self.expression())
                while self.match("COMMA"):
                    items.append(self.expression())
            self.expect("RBRACKET", "Falta ']' que cierra la lista")
            return Lista(items, line)
        if self.match("LBRACE"):
            line = self.previous().line
            pairs = []
            if not self.check("RBRACE"):
                pairs.append(self._dict_pair())
                while self.match("COMMA"):
                    pairs.append(self._dict_pair())
            self.expect("RBRACE", "Falta '}' que cierra el diccionario")
            return Diccionario(pairs, line)
        if self.match("IDENT"):
            tok = self.previous()
            return Var(tok.value, tok.line)
        if self.match("LPAREN"):
            expr = self.expression()
            self.expect("RPAREN", "Falta ')' que cierra el grupo")
            return expr
        self.error("Se esperaba una expresión")


def parse(tokens) -> Program:
    """Función de puerta: tokens -> AST."""
    return Parser(tokens).parse()


def parse_expression(tokens):
    """Analiza una sola expresión (lo usa la interpolación ${...})."""
    p = Parser(tokens)
    expr = p.expression()
    if not p.check("EOF"):
        p.error("Sobra contenido después de la expresión")
    return expr
