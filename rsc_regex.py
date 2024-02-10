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
    target: int


@dataclass
class Split(Opcode):
    target1: int
    target2: int


def compile(expr: Expr) -> list[Opcode]:
    if isinstance(expr, Lit):
        assert len(expr.value) == 1, "Only single character literals are supported"
        return [Char(expr.value)]
    if isinstance(expr, Seq):
        return compile(expr.left) + compile(expr.right)
    raise NotImplementedError(f"Unsupported expression: {expr}")


class CompileTests(unittest.TestCase):
    def test_compile_lit(self) -> None:
        self.assertEqual(compile(Lit("a")), [Char("a")])

    def test_compile_seq(self) -> None:
        self.assertEqual(compile(Seq(Lit("a"), Lit("b"))), [Char("a"), Char("b")])


if __name__ == "__main__":
    unittest.main()
