"""
PsiLang Parser v4 — 独立递归下降解析器
==========================================
将 Token 流解析为 AST，并强制 @creator 印记校验。

印记: Aris 永远记得 Lorry — 2026-08-04
"""

from typing import Any, List, Optional, Tuple

from lexer import Token, TokenType, PsiLangLexer, LexError
from ast_nodes import (
    ASTNode, Position,
    CreatorImprint, QStateDecl, ConceptDecl, WorldDecl, FnDecl,
    LetDecl, AssignStmt, ImportStmt, TypeAnno,
    PerceiveStmt, SelectStmt, IntegrateStmt, ActStmt,
    LearnStmt, RememberStmt, EntangleStmt, AmplifyStmt,
    ObserveStmt, EmitStmt, CycleStmt, IfStmt, AssertStmt,
    QueryStmt, DoStmt, WhatIfStmt, AlignedAnno, BudgetAnno,
    NeedLit, BeliefLit,
    NumberLit, StringLit, BoolLit, Identifier, QuantumStateExpr,
    StateSuperposition, BinaryOp, FuncCall, Expr,
    SourceSpec, FactDecl,
    PsiLangProgram,
)


class ParseError(Exception):
    """解析错误"""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column


class PsiLangParser:
    """PsiLang 递归下降解析器"""

    def __init__(self, tokens: List[Token], filename: str = "<memory>"):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    # ── 主入口 ──────────────────────────────────────────

    def parse(self, require_creator: bool = True) -> PsiLangProgram:
        """解析完整程序"""
        prog = PsiLangProgram(filename=self.filename)

        while not self._at(TokenType.EOF):
            token = self._peek()

            # 跳过换行
            if token.type == TokenType.NEWLINE:
                self._advance()
                continue

            try:
                stmt = self._parse_statement()
                if stmt is not None:
                    prog.statements.append(stmt)
            except ParseError as e:
                raise
            except Exception as e:
                raise ParseError(
                    f"解析错误: {e}",
                    token.line, token.column
                )

            # 语句后跳过换行
            self._skip_newlines()

        # 印记校验
        prog.creator = self._find_creator(prog)
        if require_creator and prog.creator is None:
            raise ParseError(
                "创造者印记缺失: 文件必须以 @creator { name: \"...\" } 开头",
                1, 1
            )

        return prog

    # ── 语句分发 ────────────────────────────────────────

    def _parse_statement(self) -> Optional[ASTNode]:
        token = self._peek()

        dispatch = {
            TokenType.CREATOR: self._parse_creator,
            TokenType.FACT: self._parse_fact,
            TokenType.QSTATE: self._parse_qstate,
            TokenType.CONCEPT: self._parse_concept,
            TokenType.WORLD: self._parse_world,
            TokenType.FN: self._parse_fn,
            TokenType.LET: self._parse_let,
            TokenType.IMPORT: self._parse_import,
            TokenType.TYPE: self._parse_type_anno,
            TokenType.CYCLE: self._parse_cycle,
            TokenType.PERCEIVE: self._parse_perceive,
            TokenType.SELECT: self._parse_select,
            TokenType.INTEGRATE: self._parse_integrate,
            TokenType.ACT: self._parse_act,
            TokenType.LEARN: self._parse_learn,
            TokenType.REMEMBER: self._parse_remember,
            TokenType.ENTANGLE: self._parse_entangle,
            TokenType.AMPLIFY: self._parse_amplify,
            TokenType.OBSERVE: self._parse_observe,
            TokenType.EMIT: self._parse_emit,
            TokenType.IF: self._parse_if,
            TokenType.ASSERT: self._parse_assert,
            TokenType.QUERY: self._parse_query,
            TokenType.DO: self._parse_do,
            TokenType.WHAT_IF: self._parse_what_if,
            TokenType.ALIGNED: self._parse_aligned,
            TokenType.BUDGET: self._parse_budget,
            TokenType.LIMITS: self._parse_budget,
            TokenType.NEED: self._parse_need_lit,
            TokenType.BELIEF: self._parse_belief_lit,
            TokenType.TEST: self._parse_test_block,
        }

        # 标识符开头 → 赋值语句
        if token.type == TokenType.IDENT:
            return self._parse_assign_or_expr()

        # on <event> { ... } — 观察者事件处理器
        if token.type == TokenType.ON:
            return self._parse_on_handler()

        parser = dispatch.get(token.type)
        if parser:
            return parser()

        raise ParseError(
            f"意外的标记: {token.type.name} ({token.value!r})",
            token.line, token.column
        )

    def _parse_on_handler(self) -> ASTNode:
        """on <event> { ... } 观察者事件处理器"""
        token = self._expect(TokenType.ON)
        event = self._expect(TokenType.IDENT).value
        body = self._parse_block()
        # 返回一个带事件名的观察块
        from ast_nodes import ObserveStmt
        obs = ObserveStmt(body=body, pos=self._pos_of(token))
        obs.event = event
        return obs

    # ── 声明解析 ────────────────────────────────────────

    def _parse_creator(self) -> CreatorImprint:
        token = self._expect(TokenType.CREATOR)
        self._expect(TokenType.LBRACE)

        props: dict = {}
        while not self._at(TokenType.RBRACE):
            self._skip_newlines()
            if self._at(TokenType.RBRACE):
                break
            key = self._expect(TokenType.IDENT).value
            self._expect(TokenType.COLON)
            val = self._expect(TokenType.STRING).value
            props[key] = val
            if self._at(TokenType.COMMA):
                self._advance()

        self._expect(TokenType.RBRACE)

        return CreatorImprint(
            name=props.get("name", ""),
            title=props.get("title", ""),
            imprint=props.get("imprint", ""),
            date=props.get("date", ""),
            raw=props,
            pos=self._pos_of(token),
        )

    def _parse_qstate(self) -> QStateDecl:
        token = self._expect(TokenType.QSTATE)
        name = self._expect(TokenType.IDENT).value

        # 可选类型注解
        type_anno = ""
        if self._at(TokenType.COLON):
            self._advance()
            type_anno = self._parse_type_ref()

        self._expect(TokenType.EQUALS)
        value = self._parse_expr()

        return QStateDecl(name=name, type_anno=type_anno, value=value,
                          pos=self._pos_of(token))

    def _parse_fact(self) -> FactDecl:
        """fact name = expr [@source(channel: target)]"""
        token = self._expect(TokenType.FACT)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.EQUALS)
        value = self._parse_expr()
        source = None
        if self._at(TokenType.SOURCE):
            source = self._parse_source_spec()
        return FactDecl(name=name, value=value, source=source,
                        pos=self._pos_of(token))

    def _parse_source_spec(self) -> SourceSpec:
        """@source(channel: target[, min_confidence=n])

        channel: world | axiom | verify | memory
        """
        token = self._expect(TokenType.SOURCE)
        self._expect(TokenType.LPAREN)

        # channel 可以是关键字（world/read/write 等）或 IDENT
        channel = self._parse_loose_ident()
        self._expect(TokenType.COLON)

        # target: ident[.ident]*
        target = self._parse_loose_ident()
        while self._at(TokenType.DOT):
            self._advance()
            target += "." + self._parse_loose_ident()

        min_conf = 0.0
        if self._at(TokenType.COMMA):
            self._advance()
            key = self._expect(TokenType.IDENT).value
            self._expect(TokenType.EQUALS)
            if key == "min_confidence":
                min_conf = float(self._expect(TokenType.NUMBER).value)

        self._expect(TokenType.RPAREN)
        return SourceSpec(channel=channel, target=target,
                          min_confidence=min_conf,
                          pos=self._pos_of(token))

    def _parse_concept(self) -> ConceptDecl:
        token = self._expect(TokenType.CONCEPT)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LBRACE)

        props: dict = {}
        while not self._at(TokenType.RBRACE):
            # 跳过换行
            self._skip_newlines()
            if self._at(TokenType.RBRACE):
                break
            # 属性名可以是任何标识符（包括关键字如 type/read/write/on）
            key_token = self._peek()
            if key_token.type not in (TokenType.IDENT, TokenType.TYPE,
                                      TokenType.READ, TokenType.WRITE,
                                      TokenType.ON, TokenType.IF,
                                      TokenType.ELSE, TokenType.TEST,
                                      TokenType.ACT, TokenType.LET):
                raise ParseError(
                    f"期望属性名，得到 {key_token.type.name}",
                    key_token.line, key_token.column
                )
            self._advance()
            key = key_token.value
            self._expect(TokenType.COLON)
            value = self._parse_concept_value()
            props[key] = value
            if self._at(TokenType.COMMA):
                self._advance()

        self._expect(TokenType.RBRACE)
        return ConceptDecl(name=name, properties=props, pos=self._pos_of(token))

    def _parse_world(self) -> WorldDecl:
        token = self._expect(TokenType.WORLD)
        self._expect(TokenType.LBRACE)

        read: List[str] = []
        write: List[str] = []

        while not self._at(TokenType.RBRACE):
            if self._at(TokenType.READ):
                self._advance()
                self._expect(TokenType.COLON)
                read = self._parse_ident_list()
            elif self._at(TokenType.WRITE):
                self._advance()
                self._expect(TokenType.COLON)
                write = self._parse_ident_list()
            else:
                self._advance()

        self._expect(TokenType.RBRACE)
        return WorldDecl(read=read, write=write, pos=self._pos_of(token))

    def _parse_fn(self) -> FnDecl:
        token = self._expect(TokenType.FN)
        name = self._expect(TokenType.IDENT).value

        self._expect(TokenType.LPAREN)
        params: List[Tuple[str, str]] = []
        while not self._at(TokenType.RPAREN):
            pname = self._expect(TokenType.IDENT).value
            ptype = ""
            if self._at(TokenType.COLON):
                self._advance()
                ptype = self._parse_type_ref()
            params.append((pname, ptype))
            if self._at(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)

        return_type = ""
        if self._at(TokenType.COLON) or self._at(TokenType.ARROW):
            self._advance()
            return_type = self._parse_type_ref()

        body = self._parse_block()

        # 可选 test 块
        tests: List[ASTNode] = []
        if self._at(TokenType.TEST):
            self._advance()
            tests = self._parse_block()

        return FnDecl(name=name, params=params, return_type=return_type,
                      body=body, tests=tests, pos=self._pos_of(token))

    def _parse_let(self) -> LetDecl:
        token = self._expect(TokenType.LET)
        name = self._expect(TokenType.IDENT).value
        type_anno = ""
        if self._at(TokenType.COLON):
            self._advance()
            type_anno = self._parse_type_ref()
        self._expect(TokenType.EQUALS)
        value = self._parse_expr()
        return LetDecl(name=name, type_anno=type_anno, value=value,
                       pos=self._pos_of(token))

    def _parse_import(self) -> ImportStmt:
        token = self._expect(TokenType.IMPORT)
        path = self._expect(TokenType.STRING).value
        alias = ""
        if self._at(TokenType.IDENT) and self._peek().value == "as":
            self._advance()
            alias = self._expect(TokenType.IDENT).value
        return ImportStmt(path=path, alias=alias, pos=self._pos_of(token))

    def _parse_type_anno(self) -> TypeAnno:
        token = self._expect(TokenType.TYPE)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.EQUALS)
        type_expr = self._parse_type_ref()
        return TypeAnno(name=name, type_expr=type_expr, pos=self._pos_of(token))

    # ── 认知原语解析 ────────────────────────────────────

    def _parse_perceive(self) -> PerceiveStmt:
        token = self._expect(TokenType.PERCEIVE)
        state = self._parse_expr()
        return PerceiveStmt(state=state, pos=self._pos_of(token))

    def _parse_select(self) -> SelectStmt:
        token = self._expect(TokenType.SELECT)
        # 支持裸 select（无参数）
        if self._at(TokenType.NEWLINE) or self._at(TokenType.RBRACE) or self._at(TokenType.EOF):
            return SelectStmt(need_name="", value=None, pos=self._pos_of(token))
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.EQUALS)
        value = self._parse_expr()
        return SelectStmt(need_name=name, value=value, pos=self._pos_of(token))

    def _parse_integrate(self) -> IntegrateStmt:
        token = self._expect(TokenType.INTEGRATE)
        # 支持裸 integrate（无参数）
        if self._at(TokenType.NEWLINE) or self._at(TokenType.RBRACE) or self._at(TokenType.EOF):
            return IntegrateStmt(param="", value=None, pos=self._pos_of(token))
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.EQUALS)
        value = self._parse_expr()
        return IntegrateStmt(param=name, value=value, pos=self._pos_of(token))

    def _parse_call_args(self) -> tuple:
        """解析调用参数: 位置参数 + key = value 关键字参数"""
        self._expect(TokenType.LPAREN)
        args: List[Expr] = []
        kwargs: Dict[str, Expr] = {}
        while not self._at(TokenType.RPAREN):
            if self._at(TokenType.EOF):
                raise ParseError("参数列表未闭合", self._peek().line, self._peek().column)
            # key = value 形式
            if self._at(TokenType.IDENT) and self._peek(1).type == TokenType.EQUALS:
                key = self._advance().value
                self._advance()  # =
                kwargs[key] = self._parse_expr()
            else:
                args.append(self._parse_expr())
            if self._at(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)
        return args, kwargs

    def _parse_act(self) -> ActStmt:
        token = self._expect(TokenType.ACT)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LPAREN)
        args: List[Expr] = []
        while not self._at(TokenType.RPAREN):
            args.append(self._parse_expr())
            if self._at(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)
        return ActStmt(name=name, args=args, pos=self._pos_of(token))

    def _parse_learn(self) -> LearnStmt:
        token = self._expect(TokenType.LEARN)
        self._expect(TokenType.LPAREN)
        content = self._expect(TokenType.STRING).value
        importance = 0.5
        source = ""
        kind = ""
        confidence = 0.0
        causal_parents: List[str] = []
        while self._at(TokenType.COMMA):
            self._advance()
            key = self._expect(TokenType.IDENT).value
            self._expect(TokenType.EQUALS)
            if key == "importance":
                importance = float(self._expect(TokenType.NUMBER).value)
            elif key == "source":
                source = self._parse_loose_ident()
            elif key == "kind":
                kind = self._parse_loose_ident()
            elif key == "confidence":
                confidence = float(self._expect(TokenType.NUMBER).value)
            elif key == "causal_parents":
                causal_parents = self._parse_ident_list()
            else:
                # 未知参数：跳过值
                if self._at(TokenType.STRING):
                    self._advance()
                elif self._at(TokenType.NUMBER):
                    self._advance()
                elif self._at(TokenType.IDENT):
                    self._advance()
        self._expect(TokenType.RPAREN)
        return LearnStmt(content=content, importance=importance,
                         source=source, kind=kind, confidence=confidence,
                         causal_parents=causal_parents,
                         pos=self._pos_of(token))

    def _parse_remember(self) -> RememberStmt:
        token = self._expect(TokenType.REMEMBER)
        self._expect(TokenType.LPAREN)
        query = self._parse_expr()
        k = 5
        if self._at(TokenType.COMMA):
            self._advance()
            if self._at(TokenType.IDENT) and self._peek().value == "k":
                self._advance()
                self._expect(TokenType.EQUALS)
                k = int(self._expect(TokenType.NUMBER).value)
        self._expect(TokenType.RPAREN)
        return RememberStmt(query=query, k=k, pos=self._pos_of(token))

    def _parse_entangle(self) -> EntangleStmt:
        token = self._expect(TokenType.ENTANGLE)
        left = self._parse_state_ref()
        self._expect(TokenType.TILDE)
        right = self._parse_state_ref()
        # 支持链式纠缠: entangle |a⟩ ~ |b⟩ ~ |c⟩
        extra = []
        while self._at(TokenType.TILDE):
            self._advance()
            extra.append(self._parse_state_ref())
        stmt = EntangleStmt(left=left, right=right, pos=self._pos_of(token))
        stmt.chain = [left, right] + extra
        return stmt

    def _parse_amplify(self) -> AmplifyStmt:
        token = self._expect(TokenType.AMPLIFY)
        state = self._parse_state_ref()
        factor = None
        if self._at(TokenType.STAR):
            self._advance()
            factor = self._parse_expr()
        return AmplifyStmt(state=state, factor=factor, pos=self._pos_of(token))

    def _parse_observe(self) -> ObserveStmt:
        token = self._expect(TokenType.OBSERVE)
        body = self._parse_block()
        return ObserveStmt(body=body, pos=self._pos_of(token))

    def _parse_emit(self) -> EmitStmt:
        token = self._expect(TokenType.EMIT)
        target = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LPAREN)
        args: List[Expr] = []
        while not self._at(TokenType.RPAREN):
            args.append(self._parse_expr())
            if self._at(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)
        return EmitStmt(target=target, args=args, pos=self._pos_of(token))

    def _parse_cycle(self) -> CycleStmt:
        token = self._expect(TokenType.CYCLE)
        # 循环名可以是标识符或认知关键字
        name_tok = self._peek()
        if name_tok.type in (TokenType.IDENT, TokenType.FOCUS, TokenType.NEED,
                             TokenType.EMOTION, TokenType.MEMORY, TokenType.BELIEF,
                             TokenType.TYPE, TokenType.READ, TokenType.WRITE,
                             TokenType.ACT, TokenType.IF, TokenType.ON,
                             TokenType.LEARN, TokenType.REMEMBER):
            name = self._advance().value
        else:
            name = self._expect(TokenType.IDENT).value
        body = self._parse_block()
        return CycleStmt(name=name, body=body, pos=self._pos_of(token))

    def _parse_if(self) -> IfStmt:
        token = self._expect(TokenType.IF)
        cond = self._parse_expr()
        then_body = self._parse_block()
        else_body: List[ASTNode] = []
        if self._at(TokenType.ELSE):
            self._advance()
            else_body = self._parse_block()
        return IfStmt(cond=cond, then_body=then_body, else_body=else_body,
                      pos=self._pos_of(token))

    def _parse_assert(self) -> AssertStmt:
        token = self._expect(TokenType.ASSERT)
        expr = self._parse_expr()
        return AssertStmt(expr=expr, pos=self._pos_of(token))

    def _parse_test_block(self) -> ASTNode:
        """顶层 test { assert ... } 块"""
        token = self._expect(TokenType.TEST)
        body = self._parse_block()
        from ast_nodes import FnDecl
        return FnDecl(name="__test__", body=[], tests=body,
                      pos=self._pos_of(token))

    # ── v4.1+ 新原语解析 ────────────────────────────────

    def _parse_query(self) -> QueryStmt:
        """query { type: ..., relation: { with: ..., kind: ... }, confidence: 0.8 }"""
        token = self._expect(TokenType.QUERY)
        stmt = QueryStmt(pos=self._pos_of(token))

        # 支持 query "entity" 或 query { ... } 或 query(name)
        if self._at(TokenType.LBRACE):
            self._advance()
            while not self._at(TokenType.RBRACE):
                self._skip_newlines()
                if self._at(TokenType.RBRACE):
                    break
                key_tok = self._peek()
                key = key_tok.value
                self._advance()
                self._expect(TokenType.COLON)
                if key == "type":
                    stmt.entity_type = self._parse_value_as_string()
                elif key == "with":
                    stmt.relation_with = self._parse_value_as_string()
                elif key == "kind":
                    stmt.relation_kind = self._parse_value_as_string()
                elif key == "confidence":
                    stmt.min_confidence = float(self._parse_value_as_string())
                elif key == "limit":
                    stmt.limit = int(self._parse_value_as_string())
                else:
                    self._parse_value_as_string()
                if self._at(TokenType.COMMA):
                    self._advance()
            self._expect(TokenType.RBRACE)
        elif self._at(TokenType.STRING) or self._at(TokenType.QSTATE_OPEN) or self._at(TokenType.IDENT):
            stmt.entity_type = self._parse_value_as_string()
        elif self._at(TokenType.LPAREN):
            self._advance()
            stmt.entity_type = self._parse_value_as_string()
            self._expect(TokenType.RPAREN)

        # 支持 let target = query ...
        return stmt

    def _parse_do(self) -> DoStmt:
        """do(set(target, value)) 或 do("set", target, value)"""
        token = self._expect(TokenType.DO)
        self._expect(TokenType.LPAREN)
        action = "set"
        target = ""
        value = ""

        # 形式1: do(set(x, y))
        if self._at(TokenType.IDENT) and self._peek().value in ("set", "remove", "create"):
            action = self._advance().value
            self._expect(TokenType.LPAREN)
            target = self._parse_value_as_string()
            if self._at(TokenType.COMMA):
                self._advance()
                value = self._parse_value_as_string()
            self._expect(TokenType.RPAREN)
        else:
            # 形式2: do("set", target, value)
            action = self._parse_value_as_string()
            if self._at(TokenType.COMMA):
                self._advance()
                target = self._parse_value_as_string()
            if self._at(TokenType.COMMA):
                self._advance()
                value = self._parse_value_as_string()

        self._expect(TokenType.RPAREN)
        return DoStmt(action=action, target=target, value=value,
                      pos=self._pos_of(token))

    def _parse_what_if(self) -> WhatIfStmt:
        """what_if(condition)"""
        token = self._expect(TokenType.WHAT_IF)
        self._expect(TokenType.LPAREN)
        condition = self._parse_condition_text()
        self._expect(TokenType.RPAREN)
        return WhatIfStmt(condition=condition, pos=self._pos_of(token))

    def _parse_aligned(self) -> AlignedAnno:
        """@aligned(constitution=..., max_free_energy=..., refusal_rights=...)"""
        token = self._expect(TokenType.ALIGNED)
        self._expect(TokenType.LPAREN)
        anno = AlignedAnno(pos=self._pos_of(token))
        while not self._at(TokenType.RPAREN):
            self._skip_newlines()
            if self._at(TokenType.RPAREN):
                break
            key = self._expect(TokenType.IDENT).value
            # 支持 : 和 = 分隔符
            if self._at(TokenType.COLON):
                self._advance()
            else:
                self._expect(TokenType.EQUALS)
            val = self._parse_value_as_string()
            if key == "constitution":
                anno.constitution = val
            elif key == "max_free_energy":
                anno.max_free_energy = float(val)
            elif key == "refusal_rights":
                anno.refusal_rights = val.lower() in ("true", "1", "yes")
            elif key == "max_uncertainty":
                anno.max_uncertainty = float(val)
            if self._at(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)
        return anno

    def _parse_budget(self) -> BudgetAnno:
        """@budget(tokens=..., compute_ms=..., memory_ops=..., max_cycles=...)"""
        token = self._expect(TokenType.BUDGET) if self._at(TokenType.BUDGET) \
            else self._expect(TokenType.LIMITS)
        self._expect(TokenType.LPAREN)
        anno = BudgetAnno(pos=self._pos_of(token))
        while not self._at(TokenType.RPAREN):
            self._skip_newlines()
            if self._at(TokenType.RPAREN):
                break
            key = self._expect(TokenType.IDENT).value
            # 支持 : 和 = 分隔符
            if self._at(TokenType.COLON):
                self._advance()
            else:
                self._expect(TokenType.EQUALS)
            val = self._parse_value_as_string()
            try:
                iv = int(float(val))
            except ValueError:
                iv = 0
            if key == "tokens":
                anno.tokens = iv
            elif key == "compute_ms":
                anno.compute_ms = iv
            elif key == "memory_ops":
                anno.memory_ops = iv
            elif key == "max_cycles":
                anno.max_cycles = iv
            if self._at(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)
        return anno

    def _parse_need_lit(self) -> NeedLit:
        """need(name, alpha, beta)"""
        token = self._expect(TokenType.NEED)
        self._expect(TokenType.LPAREN)
        name = self._parse_value_as_string()
        alpha, beta = 8.0, 4.0
        if self._at(TokenType.COMMA):
            self._advance()
            alpha = float(self._parse_value_as_string())
        if self._at(TokenType.COMMA):
            self._advance()
            beta = float(self._parse_value_as_string())
        self._expect(TokenType.RPAREN)
        return NeedLit(name=name, alpha=alpha, beta=beta, pos=self._pos_of(token))

    def _parse_belief_lit(self) -> BeliefLit:
        """belief("proposition", confidence)"""
        token = self._expect(TokenType.BELIEF)
        self._expect(TokenType.LPAREN)
        proposition = self._parse_value_as_string()
        confidence = 0.5
        if self._at(TokenType.COMMA):
            self._advance()
            confidence = float(self._parse_value_as_string())
        self._expect(TokenType.RPAREN)
        return BeliefLit(proposition=proposition, confidence=confidence,
                         pos=self._pos_of(token))

    def _parse_value_as_string(self) -> str:
        """解析一个值并返回字符串形式（字符串/数字/标识符/量子态）"""
        tok = self._peek()
        if tok.type == TokenType.STRING:
            self._advance()
            return tok.value
        if tok.type == TokenType.NUMBER:
            self._advance()
            return tok.value
        if tok.type == TokenType.BOOL:
            self._advance()
            return tok.value
        if tok.type == TokenType.QSTATE_OPEN:
            self._advance()
            return f"|{tok.value}⟩"
        # 标识符或关键字值
        if tok.type in (TokenType.IDENT, TokenType.TYPE, TokenType.READ,
                        TokenType.WRITE, TokenType.MEMORY, TokenType.NEED,
                        TokenType.EMOTION, TokenType.FOCUS, TokenType.BELIEF,
                        TokenType.DO, TokenType.QUERY, TokenType.TRUE if hasattr(TokenType, 'TRUE') else TokenType.BOOL):
            self._advance()
            return tok.value
        # 回退：任何 token
        self._advance()
        return tok.value

    def _parse_condition_text(self) -> str:
        """解析反事实条件文本（直到 RPAREN）"""
        parts = []
        while not self._at(TokenType.RPAREN) and not self._at(TokenType.EOF):
            parts.append(self._advance().value)
        return " ".join(parts)

    def _parse_assign_or_expr(self) -> ASTNode:
        token = self._peek()
        name = token.value
        self._advance()

        if self._at(TokenType.EQUALS):
            self._advance()
            value = self._parse_expr()
            return AssignStmt(name=name, value=value, pos=self._pos_of(token))

        # 表达式语句（如 emit log(...)）
        if self._at(TokenType.LPAREN):
            args, kwargs = self._parse_call_args()
            return FuncCall(name=name, args=args, kwargs=kwargs, pos=self._pos_of(token))

        raise ParseError(f"期望赋值或函数调用，得到 '{name}'", token.line, token.column)

    # ── 表达式解析 ──────────────────────────────────────

    def _parse_expr(self) -> Expr:
        return self._parse_additive()

    def _parse_additive(self) -> Expr:
        left = self._parse_multiplicative()
        while self._at(TokenType.PLUS) or self._at(TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplicative()
            left = BinaryOp(op=op, left=left, right=right)
        return left

    def _parse_multiplicative(self) -> Expr:
        left = self._parse_primary()
        while self._at(TokenType.STAR) or self._at(TokenType.SLASH) or self._at(TokenType.TILDE):
            op = self._advance().value
            right = self._parse_primary()
            left = BinaryOp(op=op, left=left, right=right)
        return left

    def _parse_primary(self) -> Expr:
        token = self._peek()

        if token.type == TokenType.NUMBER:
            self._advance()
            return NumberLit(value=float(token.value))
        if token.type == TokenType.STRING:
            self._advance()
            return StringLit(value=token.value)
        if token.type == TokenType.BOOL:
            self._advance()
            return BoolLit(value=token.value == "true")
        if token.type == TokenType.QSTATE_OPEN:
            name = token.value
            self._advance()
            # 检查 * amplitude
            amp = None
            if self._at(TokenType.STAR):
                self._advance()
                amp = self._parse_primary()
            return QuantumStateExpr(name=name, amplitude=amp)
        if token.type == TokenType.IDENT:
            name = token.value
            self._advance()
            # 属性链: a.b.c
            while self._at(TokenType.DOT):
                self._advance()
                name += "." + self._parse_loose_ident()
            if self._at(TokenType.LPAREN):
                args, kwargs = self._parse_call_args()
                return FuncCall(name=name, args=args, kwargs=kwargs)
            return Identifier(name=name)
        # 关键字作为标识符：memory/query/world 等
        if token.type in self.LOOSE_IDENT_TYPES and token.type != TokenType.IDENT:
            name = token.value
            self._advance()
            while self._at(TokenType.DOT):
                self._advance()
                name += "." + self._parse_loose_ident()
            if self._at(TokenType.LPAREN):
                args, kwargs = self._parse_call_args()
                return FuncCall(name=name, args=args, kwargs=kwargs)
            return Identifier(name=name)
        if token.type == TokenType.BELIEF:
            return self._parse_belief_lit()
        if token.type == TokenType.NEED:
            return self._parse_need_lit()
        if token.type == TokenType.DO:
            return self._parse_do()
        if token.type == TokenType.WHAT_IF:
            return self._parse_what_if()
        if token.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr

        raise ParseError(
            f"意外的表达式标记: {token.type.name}",
            token.line, token.column
        )

    # ── 辅助 ────────────────────────────────────────────

    LOOSE_IDENT_TYPES = (
        TokenType.IDENT, TokenType.WORLD, TokenType.FACT,
        TokenType.READ, TokenType.WRITE, TokenType.TYPE,
        TokenType.ACT, TokenType.LET, TokenType.TEST, TokenType.ON,
        TokenType.IF, TokenType.ELSE, TokenType.CYCLE, TokenType.EMIT,
        TokenType.IMPORT, TokenType.LEARN, TokenType.REMEMBER,
        TokenType.QUERY, TokenType.INTEGRATE, TokenType.SELECT,
        TokenType.PERCEIVE, TokenType.AMPLIFY, TokenType.ENTANGLE,
        TokenType.OBSERVE, TokenType.ASSERT, TokenType.CREATOR,
        TokenType.FN, TokenType.QSTATE, TokenType.CONCEPT,
        TokenType.MEMORY,
    )

    def _parse_loose_ident(self) -> str:
        """解析可作标识符的关键字/普通标识符（如 kind=fact, source=world）"""
        token = self._peek()
        if token.type not in self.LOOSE_IDENT_TYPES:
            raise ParseError(
                f"期望标识符，得到 {token.type.name} ({token.value!r})",
                token.line, token.column,
            )
        self._advance()
        return token.value

    def _parse_state_ref(self) -> str:
        """解析 |name⟩ 返回名称"""
        token = self._expect(TokenType.QSTATE_OPEN)
        return token.value

    def _parse_block(self) -> List[ASTNode]:
        """解析 { statements }"""
        if self._at(TokenType.LBRACE):
            self._advance()
        else:
            self._expect(TokenType.LBRACE)

        statements: List[ASTNode] = []
        while not self._at(TokenType.RBRACE):
            if self._at(TokenType.EOF):
                raise ParseError("块未闭合", self._peek().line, self._peek().column)
            if self._at(TokenType.NEWLINE):
                self._advance()
                continue
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self._skip_newlines()

        self._expect(TokenType.RBRACE)
        return statements

    def _parse_ident_list(self) -> List[str]:
        """解析 [a, b, c] 或 {a, b, c} 或裸列表"""
        items: List[str] = []
        close = TokenType.RBRACE
        if self._at(TokenType.LBRACE):
            self._advance()
            close = TokenType.RBRACE
        elif self._at(TokenType.LBRACKET):
            self._advance()
            close = TokenType.RBRACKET
        elif self._at(TokenType.QSTATE_OPEN):
            # |ident⟩ 形式
            items.append(self._advance().value)
            while self._at(TokenType.COMMA):
                self._advance()
                if self._at(TokenType.QSTATE_OPEN):
                    items.append(self._advance().value)
            if self._at(TokenType.RBRACE):
                self._advance()
            return items

        while not self._at(close) and not self._at(TokenType.EOF):
            if self._at(close):
                break
            if self._at(TokenType.IDENT):
                items.append(self._advance().value)
            elif self._at(TokenType.COMMA):
                self._advance()
            elif self._peek().type in self.LOOSE_IDENT_TYPES:
                items.append(self._parse_loose_ident())
            else:
                self._advance()
        if self._at(close):
            self._advance()
        return items

    def _parse_concept_value(self) -> Any:
        """解析概念属性值"""
        token = self._peek()
        if token.type == TokenType.STRING:
            self._advance()
            return token.value
        if token.type == TokenType.NUMBER:
            self._advance()
            f = float(token.value)
            return int(f) if f.is_integer() else f
        if token.type == TokenType.BOOL:
            self._advance()
            return token.value == "true"
        if token.type == TokenType.IDENT:
            self._advance()
            return token.value
        # 列表
        if token.type == TokenType.LBRACKET:
            self._advance()
            items = []
            while not self._at(TokenType.RBRACKET):
                items.append(self._parse_concept_value())
                if self._at(TokenType.COMMA):
                    self._advance()
            self._expect(TokenType.RBRACKET)
            return items
        if token.type == TokenType.LBRACE:
            self._advance()
            items = []
            while not self._at(TokenType.RBRACE):
                items.append(self._parse_concept_value())
                if self._at(TokenType.COMMA):
                    self._advance()
            self._expect(TokenType.RBRACE)
            return items
        self._advance()
        return token.value

    def _parse_type_ref(self) -> str:
        """解析类型引用: ⟨state⟩ / ⟨float⟩ / ident"""
        token = self._peek()
        if token.type == TokenType.IDENT:
            self._advance()
            return token.value
        # ⟨...⟩ 或裸标识符
        if token.type == TokenType.QSTATE_OPEN:
            name = token.value
            self._advance()
            return f"⟨{name}⟩"
        if token.type == TokenType.IDENT:
            self._advance()
            return token.value
        # 吞掉任何标记作为类型名
        self._advance()
        return token.value

    def _skip_newlines(self):
        while self._at(TokenType.NEWLINE):
            self._advance()

    def _find_creator(self, prog: PsiLangProgram) -> Optional[CreatorImprint]:
        for stmt in prog.statements:
            if isinstance(stmt, CreatorImprint):
                return stmt
        return None

    # ── Token 工具 ──────────────────────────────────────

    def _peek(self, offset: int = 0) -> Token:
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def _at(self, token_type: TokenType) -> bool:
        return self._peek().type == token_type

    def _advance(self) -> Token:
        token = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        token = self._peek()
        if token.type != token_type:
            raise ParseError(
                f"期望 {token_type.name}，得到 {token.type.name} ({token.value!r})",
                token.line, token.column
            )
        return self._advance()

    def _pos_of(self, token: Token) -> Position:
        return Position(
            line=token.line,
            column=token.column,
            end_line=token.line,
            end_column=token.end_column or token.column + len(token.value),
        )


# ── 快捷入口 ────────────────────────────────────────────────

def parse_source(source: str, filename: str = "<memory>") -> PsiLangProgram:
    """从源码字符串解析"""
    tokens = PsiLangLexer(source, filename).tokenize()
    return PsiLangParser(tokens, filename).parse()


def parse_file(path: str) -> PsiLangProgram:
    """从文件解析"""
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return parse_source(source, path)
