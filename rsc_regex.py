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
    raise NotImplementedError(f"Unsupported expression: {expr}")


def match(ops: list[Opcode], text: str) -> bool:
    pc = 0
    textp = 0
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
        else:
            raise NotImplementedError(f"Unsupported opcode: {op}")
    return True


class CompileTests(unittest.TestCase):
    def test_compile_lit(self) -> None:
        self.assertEqual(compile(Lit("a")), [Char("a")])

    def test_compile_seq(self) -> None:
        self.assertEqual(compile(Seq(Lit("a"), Lit("b"))), [Char("a"), Char("b")])

    def test_compile_nested_seq(self) -> None:
        self.assertEqual(compile(Seq(Seq(Lit("a"), Lit("b")), Lit("c"))), [Char("a"), Char("b"), Char("c")])



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

if __name__ == "__main__":
    unittest.main()
