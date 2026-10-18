"""Analizador léxico (lexer): el texto fuente -> lista de tokens.

Las palabras clave de ESTE lenguaje son en español:

    variable edad = 30;
    si (edad >= 18) { escribe "mayor"; } sino { escribe "menor"; }
"""

from dataclasses import dataclass


class LexError(Exception):
    """Error detectado durante el análisis léxico."""


@dataclass
class Token:
    type: str       # VARIABLE, NUMBER, PLUS...
    value: object   # valor literal (número, texto) o el texto del token
    line: int
    col: int

    def __repr__(self) -> str:
        return f"{self.type}({self.value!r})@{self.line}:{self.col}"


KEYWORDS = {
    "variable": "VARIABLE",
    "const": "CONST",
    "escribe": "ESCRIBE",
    "si": "SI",
    "sino": "SINO",
    "mientras": "MIENTRAS",
    "para": "PARA",
    "en": "EN",
    "funcion": "FUNCION",
    "devuelve": "DEVUELVE",
    "romper": "ROMPER",
    "continuar": "CONTINUAR",
    "verdadero": "VERDADERO",
    "falso": "FALSO",
    "nulo": "NULO",
    "y": "Y",
    "o": "O",
    "no": "NO",
    "importar": "IMPORTAR",
    "como": "COMO",
}

# Símbolos de un solo carácter.
SINGLE = {
    "(": "LPAREN", ")": "RPAREN", "{": "LBRACE", "}": "RBRACE",
    "[": "LBRACKET", "]": "RBRACKET",
    "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
    "^": "POW",
    "=": "ASSIGN", "<": "LT", ">": "GT", "!": "NOT",
    ".": "DOT",
    ",": "COMMA", ";": "SEMI", ":": "DOSPUNTOS",
}

# Operadores de dos caracteres (se miran antes que los de uno).
DOUBLE = {"==": "EQ", "!=": "NE", "<=": "LE", ">=": "GE"}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    # ---- utilidades de posición ----
    def error(self, msg: str):
        raise LexError(f"[línea {self.line}, columna {self.col}] {msg}")

    def peek(self, offset: int = 0):
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    # ---- bucle principal ----
    def run(self) -> list[Token]:
        # se ignora el BOM de UTF-8 que añaden algunos editores de Windows
        if self.source.startswith("\ufeff"):
            self.advance()

        while self.pos < len(self.source):
            ch = self.peek()

            if ch in " \t\r\n":
                self.advance()
                continue

            if ch == "/" and self.peek(1) == "/":          # comentario
                while self.pos < len(self.source) and self.peek() != "\n":
                    self.advance()
                continue

            if ch.isdigit() or (ch == "." and (self.peek(1) or "").isdigit()):
                self.number()
                continue

            if ch.isalpha() or ch == "_":
                self.identifier()
                continue

            if ch in "\"'":
                self.string()
                continue

            two = ch + (self.peek(1) or "")

            # i++ / i--  (solo tras un identificador o ')' o ']': así
            # 1 - -1 sigue siendo una resta, no un decremento)
            if two in ("++", "--") and self.tokens and \
                    self.tokens[-1].type in ("IDENT", "RPAREN", "RBRACKET"):
                line, col = self.line, self.col
                self.advance()
                self.advance()
                self.tokens.append(Token("INC" if two == "++" else "DEC", two, line, col))
                continue

            if two in DOUBLE:
                line, col = self.line, self.col
                self.advance()
                self.advance()
                self.tokens.append(Token(DOUBLE[two], two, line, col))
                continue

            if ch in SINGLE:
                line, col = self.line, self.col
                self.advance()
                self.tokens.append(Token(SINGLE[ch], ch, line, col))
                continue

            self.error(f"Carácter inesperado {ch!r}")

        self.tokens.append(Token("EOF", None, self.line, self.col))
        return self.tokens

    # ---- lectores especializados ----
    def number(self):
        line, col = self.line, self.col
        start = self.pos
        while self.peek() and (self.peek().isdigit() or self.peek() == "."):
            if self.peek() == "." and not (self.peek(1) or "").isdigit():
                break
            self.advance()
        text = self.source[start:self.pos]
        try:
            value = float(text)
        except ValueError:
            raise LexError(f"[línea {line}, columna {col}] Número inválido {text!r}") from None
        self.tokens.append(Token("NUMBER", value, line, col))

    def identifier(self):
        line, col = self.line, self.col
        start = self.pos
        while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        text = self.source[start:self.pos]
        self.tokens.append(Token(KEYWORDS.get(text, "IDENT"), text, line, col))

    def string(self):
        r"""Guarda el texto CRUDO (sin procesar escapes ni ${}).

        Admite comillas dobles y simples: las simples sirven dentro de la
        interpolación,  escribe "${d['clave']}";
        La conversión de escapes y de ${} la hace el evaluador, para poder
        distinguir \$ de $.
        """
        line, col = self.line, self.col
        comilla = self.advance()  # comilla inicial
        chars = []
        while True:
            if self.pos >= len(self.source):
                raise LexError(f"[línea {line}, columna {col}] Cadena sin cerrar (falta {comilla})")
            ch = self.advance()
            if ch == comilla:
                break
            if ch == "\n":
                raise LexError(f"[línea {line}, columna {col}] Salto de línea dentro de una cadena")
            if ch == "\\":                      # se conserva el par \\ + siguiente
                chars.append(ch)
                if self.pos < len(self.source):
                    chars.append(self.advance())
                continue
            chars.append(ch)
        self.tokens.append(Token("STRING", "".join(chars), line, col))


def tokenize(source: str) -> list[Token]:
    """Función de puerta: fuente -> lista de tokens."""
    return Lexer(source).run()
