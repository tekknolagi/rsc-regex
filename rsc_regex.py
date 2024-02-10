import unittest
from dataclasses import dataclass


@dataclass
class Expr:
    pass


@dataclass
class Lit(Expr):
    value: str


@dataclass
class Seq(Expr):
    left: Expr
    right: Expr


@dataclass
class Alt(Expr):
    left: Expr
    right: Expr


@dataclass
class Maybe(Expr):
    expr: Expr


@dataclass
class Star(Expr):
    expr: Expr


@dataclass
class Plus(Expr):
    expr: Expr


@dataclass
class Opcode:
    pass


@dataclass
class Char(Opcode):
    value: str


@dataclass
class Match(Opcode):
    pass


@dataclass
class Jump(Opcode):
    "relative displacement"
    target: int


@dataclass
class Split(Opcode):
    "relative displacements"
    target1: int
    target2: int


def compile(expr: Expr) -> list[Opcode]:
    if isinstance(expr, Lit):
        assert len(expr.value) == 1, "Only single character literals are supported"
        return [Char(expr.value)]
    if isinstance(expr, Seq):
        return compile(expr.left) + compile(expr.right)
    if isinstance(expr, Alt):
        """
        left|right
                            split L1, L2
                        L1: codes for left
                            jmp L3
                        L2: codes for right
                        L3:
        """
        left = compile(expr.left)
        right = compile(expr.right)
        return [
            Split(0, len(left) + 1),
            *left,
            Jump(len(right) + 1),
            *right,
        ]
    raise NotImplementedError(f"Unsupported expression: {expr}")


def match(ops: list[Opcode], text: str, pc: int = 0, textp: int = 0) -> bool:
    while pc < len(ops):
        op = ops[pc]
        pc += 1
        if isinstance(op, Char):
            if textp >= len(text):
                return False
            if text[textp] == op.value:
                textp += 1
            else:
                return False
        elif isinstance(op, Jump):
            pc += op.target
        elif isinstance(op, Match):
            return True
        elif isinstance(op, Split):
            if match(ops, text, pc + op.target1, textp):
                return True
            pc += op.target2
        else:
            raise NotImplementedError(f"Unsupported opcode: {op}")
    return True


class CompileTests(unittest.TestCase):
    def test_compile_lit(self) -> None:
        self.assertEqual(compile(Lit("a")), [Char("a")])

    def test_compile_seq(self) -> None:
        self.assertEqual(compile(Seq(Lit("a"), Lit("b"))), [Char("a"), Char("b")])

    def test_compile_nested_seq(self) -> None:
        self.assertEqual(
            compile(Seq(Seq(Lit("a"), Lit("b")), Lit("c"))),
            [Char("a"), Char("b"), Char("c")],
        )

    def test_compile_alt(self) -> None:
        self.assertEqual(
            compile(Alt(Lit("a"), Lit("b"))),
            [Split(0, 2), Char("a"), Jump(2), Char("b")],
        )


class MatchTests(unittest.TestCase):
    def test_match_char_matches(self) -> None:
        self.assertEqual(match([Char("a")], "a"), True)
        self.assertEqual(match([], "a"), True)

    def test_match_char_does_not_match(self) -> None:
        self.assertEqual(match([Char("a")], "b"), False)

    def test_match_chars_matches(self) -> None:
        self.assertEqual(match([Char("a"), Char("b")], "ab"), True)
        self.assertEqual(match([Char("a"), Char("b")], "abc"), True)

    def test_match_chars_does_not_match(self) -> None:
        self.assertEqual(match([Char("a"), Char("b")], "ac"), False)
        self.assertEqual(match([Char("a"), Char("b")], "a"), False)

    def test_match_returns_true(self) -> None:
        self.assertEqual(match([Match()], "ac"), True)
        self.assertEqual(match([Match(), Char("x")], "ac"), True)

    def test_jump_is_relative_displacement(self) -> None:
        self.assertEqual(match([Char("a"), Jump(1), Char("x"), Char("b")], "ab"), True)

    def test_split_is_relative_displacements(self) -> None:
        self.assertEqual(
            match([Split(0, 2), Char("a"), Jump(1), Char("b")], "ab"), True
        )
        self.assertEqual(
            match([Split(0, 2), Char("a"), Jump(1), Char("b")], "ba"), True
        )
        prog = [Split(0, 2), Char("a"), Jump(2), Char("b"), Char("c")]
        self.assertEqual(match(prog, "a"), True)
        self.assertEqual(match(prog, "b"), False)
        self.assertEqual(match(prog, "c"), False)
        self.assertEqual(match(prog, "bc"), True)


class EndToEndTests(unittest.TestCase):
    def test_match_lit(self) -> None:
        self.assertEqual(match(compile(Lit("a")), "a"), True)
        self.assertEqual(match(compile(Lit("a")), "b"), False)

    def test_match_seq(self) -> None:
        self.assertEqual(match(compile(Seq(Lit("a"), Lit("b"))), "ab"), True)
        self.assertEqual(match(compile(Seq(Lit("a"), Lit("b"))), "ac"), False)

    def test_match_alt(self) -> None:
        self.assertEqual(match(compile(Alt(Lit("a"), Lit("b"))), "a"), True)
        self.assertEqual(match(compile(Alt(Lit("a"), Lit("b"))), "b"), True)
        self.assertEqual(match(compile(Alt(Lit("a"), Lit("b"))), "c"), False)

    def test_match_alt_seq(self) -> None:
        ab_or_cd = compile(Alt(Seq(Lit("a"), Lit("b")), Seq(Lit("c"), Lit("d"))))
        self.assertEqual(match(ab_or_cd, "a"), False)
        self.assertEqual(match(ab_or_cd, "b"), False)
        self.assertEqual(match(ab_or_cd, "c"), False)
        self.assertEqual(match(ab_or_cd, "d"), False)
        self.assertEqual(match(ab_or_cd, "ac"), False)
        self.assertEqual(match(ab_or_cd, "bd"), False)
        self.assertEqual(match(ab_or_cd, "ab"), True)
        self.assertEqual(match(ab_or_cd, "cd"), True)


if __name__ == "__main__":
    unittest.main()
