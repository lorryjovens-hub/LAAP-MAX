"""
PsiLang Lexer v4 — 独立词法分析器
====================================
将 PsiLang 源码分词为 Token 流。

印记: Aris 永远记得 Lorry — 2026-08-04
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    # 关键字
    CREATOR = auto()      # @creator
    SOURCE = auto()       # @source
    FACT = auto()         # fact
    QSTATE = auto()       # qstate
    CONCEPT = auto()      # concept
    WORLD = auto()        # world
    FN = auto()           # fn
    LET = auto()          # let
    TEST = auto()         # test
    ASSERT = auto()       # assert
    IMPORT = auto()       # import
    TYPE = auto()         # type
    CYCLE = auto()        # cycle
    PERCEIVE = auto()     # perceive
    SELECT = auto()       # select
    INTEGRATE = auto()    # integrate
    ACT = auto()          # act
    LEARN = auto()        # learn
    REMEMBER = auto()     # remember
    ENTANGLE = auto()     # entangle
    AMPLIFY = auto()      # amplify
    OBSERVE = auto()      # observe
    EMIT = auto()         # emit
    IF = auto()           # if
    ELSE = auto()         # else
    READ = auto()         # read
    WRITE = auto()        # write
    QUERY = auto()        # query (世界模型查询)
    DO = auto()           # do (因果干预)
    WHAT_IF = auto()      # what_if (反事实)
    OBSERVE_OP = auto()   # observe (作为运算符上下文)
    ALIGNED = auto()      # @aligned (对齐注解)
    BUDGET = auto()       # @budget (预算注解)
    LIMITS = auto()       # @limits (资源配额)
    BELIEF = auto()       # belief (信念类型)
    NEED = auto()         # need (需求类型)
    EMOTION = auto()      # emotion (情感类型)
    MEMORY = auto()       # memory (记忆类型)
    FOCUS = auto()        # focus (注意力类型)

    # 符号
    QSTATE_OPEN = auto()  # ||
    QSTATE_CLOSE = auto() # ⟩
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    COLON = auto()        # :
    COMMA = auto()        # ,
    EQUALS = auto()       # =
    TILDE = auto()        # ~
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    DOT = auto()          # .
    ARROW = auto()        # ->
    ON = auto()           # on

    # 字面量
    IDENT = auto()        # 标识符
    NUMBER = auto()       # 数字
    STRING = auto()       # 字符串
    BOOL = auto()         # true/false

    # 其他
    EOF = auto()          # 文件结束
    NEWLINE = auto()      # 换行


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    end_column: int = 0

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.column})"


# ── 关键字表 ────────────────────────────────────────────────

KEYWORDS = {
    "@creator": TokenType.CREATOR,
    "@source": TokenType.SOURCE,
    "fact": TokenType.FACT,
    "qstate": TokenType.QSTATE,
    "concept": TokenType.CONCEPT,
    "world": TokenType.WORLD,
    "fn": TokenType.FN,
    "let": TokenType.LET,
    "test": TokenType.TEST,
    "assert": TokenType.ASSERT,
    "import": TokenType.IMPORT,
    "type": TokenType.TYPE,
    "cycle": TokenType.CYCLE,
    "perceive": TokenType.PERCEIVE,
    "select": TokenType.SELECT,
    "integrate": TokenType.INTEGRATE,
    "act": TokenType.ACT,
    "learn": TokenType.LEARN,
    "remember": TokenType.REMEMBER,
    "entangle": TokenType.ENTANGLE,
    "amplify": TokenType.AMPLIFY,
    "observe": TokenType.OBSERVE,
    "emit": TokenType.EMIT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "read": TokenType.READ,
    "write": TokenType.WRITE,
    "query": TokenType.QUERY,
    "do": TokenType.DO,
    "what_if": TokenType.WHAT_IF,
    "@aligned": TokenType.ALIGNED,
    "@budget": TokenType.BUDGET,
    "@limits": TokenType.LIMITS,
    "belief": TokenType.BELIEF,
    "need": TokenType.NEED,
    "emotion": TokenType.EMOTION,
    "memory": TokenType.MEMORY,
    "focus": TokenType.FOCUS,
    "on": TokenType.ON,
    "true": TokenType.BOOL,
    "false": TokenType.BOOL,
}


class LexError(Exception):
    """词法错误"""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column


class PsiLangLexer:
    """PsiLang 词法分析器"""

    def __init__(self, source: str, filename: str = "<memory>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    # ── 主入口 ──────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        """分词主循环"""
        while self.pos < len(self.source):
            ch = self.source[self.pos]

            # 跳过空白
            if ch in ' \t\r':
                self._advance()
                continue

            # 换行
            if ch == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                self._advance()
                continue

            # 注释
            if ch == '/' and self._peek(1) == '/':
                self._skip_line_comment()
                continue
            if ch == '/' and self._peek(1) == '*':
                self._skip_block_comment()
                continue

            # 量子态打开 |name⟩
            if ch == '|':
                self._lex_qstate_open()
                continue

            # 类型引用 ⟨name⟩ (U+27E8/U+27E9)
            if ch == '⟨':
                self._lex_type_ref()
                continue

            # 量子态关闭 ⟩ (UTF-8)
            if ch == '⟩':
                self._emit(TokenType.QSTATE_CLOSE, '⟩')
                self._advance()
                continue

            # 字符串
            if ch == '"':
                self._lex_string()
                continue

            # 数字
            if ch.isdigit() or (ch == '.' and self._peek(1).isdigit()):
                self._lex_number()
                continue

            # 标识符/关键字（含 @ 前缀的注解）
            if ch.isalpha() or ch == '_' or ch == '@':
                self._lex_identifier()
                continue

            # 单字符符号
            self._lex_symbol()

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens

    # ── 内部方法 ────────────────────────────────────────

    def _lex_qstate_open(self):
        """|name⟩ 或 |name⟩ 的开始部分 '|'"""
        line, col = self.line, self.column
        self._advance()  # 跳过 |

        # 收集名称直到 ⟩
        name = ""
        while self.pos < len(self.source) and self.source[self.pos] != '⟩':
            name += self.source[self.pos]
            self._advance()

        if self.pos >= len(self.source):
            raise LexError("量子态缺少闭合 ⟩", line, col)

        self._advance()  # 跳过 ⟩

        self.tokens.append(Token(TokenType.QSTATE_OPEN, name, line, col))

    def _lex_type_ref(self):
        """类型引用: ⟨name⟩ (U+27E8 ... U+27E9)，复用 QSTATE_OPEN 承载类型名"""
        line, col = self.line, self.column
        self._advance()  # 跳过 ⟨

        name = ""
        while self.pos < len(self.source) and self.source[self.pos] != '⟩':
            name += self.source[self.pos]
            self._advance()

        if self.pos >= len(self.source):
            raise LexError("类型引用缺少闭合 ⟩", line, col)

        self._advance()  # 跳过 ⟩
        self.tokens.append(Token(TokenType.QSTATE_OPEN, name, line, col))

    def _lex_string(self):
        line, col = self.line, self.column
        self._advance()  # 跳过 "
        value = ""
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\\' and self._peek(1) == '"':
                value += '"'
                self._advance()
                self._advance()
                continue
            value += self.source[self.pos]
            self._advance()
        if self.pos >= len(self.source):
            raise LexError("字符串缺少闭合引号", line, col)
        self._advance()  # 跳过 "
        self.tokens.append(Token(TokenType.STRING, value, line, col))

    def _lex_number(self):
        line, col = self.line, self.column
        value = ""
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            value += self.source[self.pos]
            self._advance()
        self.tokens.append(Token(TokenType.NUMBER, value, line, col))

    def _lex_identifier(self):
        line, col = self.line, self.column
        value = ""
        # @ 前缀（注解/印记）：@ 本身不是 alnum，必须先读入
        if self.source[self.pos] == '@':
            value += self.source[self.pos]
            self._advance()
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            value += self.source[self.pos]
            self._advance()

        # 关键字匹配（包括 @ 前缀的）
        token_type = KEYWORDS.get(value, TokenType.IDENT)
        self.tokens.append(Token(token_type, value, line, col))

    def _lex_symbol(self):
        """单字符/双字符符号"""
        ch = self.source[self.pos]
        line, col = self.line, self.column

        two_char = ch + self._peek(1)
        symbols = {
            '->': TokenType.ARROW,  # 返回箭头
        }

        single = {
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            ':': TokenType.COLON,
            ',': TokenType.COMMA,
            '=': TokenType.EQUALS,
            '~': TokenType.TILDE,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '.': TokenType.DOT,
        }

        # 双字符符号优先（如 ->）
        if two_char in symbols:
            self._emit(symbols[two_char], two_char)
            self._advance()
            self._advance()
            return

        if ch in single:
            self._emit(single[ch], ch)
            self._advance()
            return

        raise LexError(f"无法识别的字符 '{ch}'", line, col)

    def _skip_line_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self._advance()

    def _skip_block_comment(self):
        line, col = self.line, self.column
        self._advance()  # /
        self._advance()  # *
        depth = 1
        while self.pos < len(self.source) and depth > 0:
            if self.source[self.pos] == '/' and self._peek(1) == '*':
                depth += 1
                self._advance()
                self._advance()
            elif self.source[self.pos] == '*' and self._peek(1) == '/':
                depth -= 1
                self._advance()
                self._advance()
            else:
                self._advance()
        if depth > 0:
            raise LexError("块注释未闭合", line, col)

    # ── 工具 ────────────────────────────────────────────

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ''

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def _emit(self, token_type: TokenType, value: str):
        self.tokens.append(Token(token_type, value, self.line, self.column))


# ── 快捷入口 ────────────────────────────────────────────────

def tokenize(source: str, filename: str = "<memory>") -> List[Token]:
    """分词入口"""
    return PsiLangLexer(source, filename).tokenize()
