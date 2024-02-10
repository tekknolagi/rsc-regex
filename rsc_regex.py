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


@dataclass
class Thread:
    pc: int
    textp: int


MAX_THREADS = 10


def run_thread(ops: list[Opcode], text: str, threads: list[Thread]) -> bool:
    thread = threads.pop()
    pc = thread.pc
    textp = thread.textp
    while pc < len(ops):
        op = ops[pc]
        pc += 1
        if isinstance(op, Char):
            if textp >= len(text) or text[textp] != op.value:
                return False
            textp += 1
        elif isinstance(op, Jump):
            pc += op.target
        elif isinstance(op, Match):
            return True
        elif isinstance(op, Split):
            if len(threads) >= MAX_THREADS:
                raise RuntimeError("Too many threads")
            threads.append(Thread(pc + op.target2, textp))
            pc += op.target1
        else:
            raise NotImplementedError(f"Unsupported opcode: {op}")
    return True


def match(ops: list[Opcode], text: str) -> bool:
    threads = [Thread(pc=0, textp=0)]
    while threads:
        result = run_thread(ops, text, threads)
        if result:
            return True
    return False


def native_compile(ops: list[Opcode]) -> str:
    result: list[str] = []
    for op in ops:
        if isinstance(op, Char):
            result += [
                # Strings are nul-terminated; we assume the regex has no
                # nul so we can check for out-of-bounds and non-matching in
                # one comparison
                f"cmpb [rdi], 0x{ord(op.value)}",
                "jne .Lno_match",
                "inc rdi",
            ]
        else:
            raise NotImplementedError(f"Unsupported opcode: {op}")
    return "\n".join(result)


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
        self.assertTrue(match([Char("a")], "a"))
        self.assertTrue(match([], "a"))

    def test_match_char_does_not_match(self) -> None:
        self.assertFalse(match([Char("a")], "b"))

    def test_match_chars_matches(self) -> None:
        self.assertTrue(match([Char("a"), Char("b")], "ab"))
        self.assertTrue(match([Char("a"), Char("b")], "abc"))

    def test_match_chars_does_not_match(self) -> None:
        self.assertFalse(match([Char("a"), Char("b")], "ac"))
        self.assertFalse(match([Char("a"), Char("b")], "a"))

    def test_match_returns_true(self) -> None:
        self.assertTrue(match([Match()], "ac"))
        self.assertTrue(match([Match(), Char("x")], "ac"))

    def test_jump_is_relative_displacement(self) -> None:
        self.assertTrue(match([Char("a"), Jump(1), Char("x"), Char("b")], "ab"))

    def test_split_is_relative_displacements(self) -> None:
        self.assertTrue(match([Split(0, 2), Char("a"), Jump(1), Char("b")], "ab"))
        self.assertTrue(match([Split(0, 2), Char("a"), Jump(1), Char("b")], "ba"))
        prog = [Split(0, 2), Char("a"), Jump(2), Char("b"), Char("c")]
        self.assertTrue(match(prog, "a"))
        self.assertFalse(match(prog, "b"))
        self.assertFalse(match(prog, "c"))
        self.assertTrue(match(prog, "bc"))


class EndToEndTests(unittest.TestCase):
    def test_match_lit(self) -> None:
        self.assertTrue(match(compile(Lit("a")), "a"))
        self.assertFalse(match(compile(Lit("a")), "b"))

    def test_match_seq(self) -> None:
        self.assertTrue(match(compile(Seq(Lit("a"), Lit("b"))), "ab"))
        self.assertFalse(match(compile(Seq(Lit("a"), Lit("b"))), "ac"))

    def test_match_alt(self) -> None:
        self.assertTrue(match(compile(Alt(Lit("a"), Lit("b"))), "a"))
        self.assertTrue(match(compile(Alt(Lit("a"), Lit("b"))), "b"))
        self.assertFalse(match(compile(Alt(Lit("a"), Lit("b"))), "c"))

    def test_match_alt_seq(self) -> None:
        ab_or_cd = compile(Alt(Seq(Lit("a"), Lit("b")), Seq(Lit("c"), Lit("d"))))
        self.assertFalse(match(ab_or_cd, "a"))
        self.assertFalse(match(ab_or_cd, "b"))
        self.assertFalse(match(ab_or_cd, "c"))
        self.assertFalse(match(ab_or_cd, "d"))
        self.assertFalse(match(ab_or_cd, "ac"))
        self.assertFalse(match(ab_or_cd, "bd"))
        self.assertTrue(match(ab_or_cd, "ab"))
        self.assertTrue(match(ab_or_cd, "cd"))


class NativeCompileTests(unittest.TestCase):
    def test_native_compile_lit(self) -> None:
        self.assertEqual(
            native_compile([Char("a")]), "cmpb [rdi], 0x97\njne .Lno_match\ninc rdi"
        )

    def test_native_compile_seq(self) -> None:
        self.assertEqual(
            native_compile([Char("a"), Char("b")]),
            "\n".join(
                [
                    "cmpb [rdi], 0x97",
                    "jne .Lno_match",
                    "inc rdi",
                    "cmpb [rdi], 0x98",
                    "jne .Lno_match",
                    "inc rdi",
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
