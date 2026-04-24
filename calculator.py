import ast
import operator


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def evaluate(expr):
    # Let '^' mean exponentiation the way most calculators do.
    expr = expr.replace("^", "**")
    try:
        return _eval(ast.parse(expr, mode="eval"))
    except (SyntaxError, ValueError, ZeroDivisionError, TypeError, OverflowError):
        return None


BANNER = r"""
==============================================================
                     Python Calculator
==============================================================
 Type a math expression and press Enter to see the result.
 Standard math rules apply: parentheses first, then powers,
 then multiplication/division, then addition/subtraction.

 Commands:
   help  (or ?)  show this guide again
   quit  (or q)  exit the calculator
==============================================================
"""

HELP = """
Available operations
--------------------
  +     addition              e.g.  2 + 3           -> 5
  -     subtraction / negate  e.g.  10 - 4          -> 6
                                    -7 + 2          -> -5
  *     multiplication        e.g.  6 * 7           -> 42
  /     division              e.g.  9 / 2           -> 4.5
  //    floor division        e.g.  9 // 2          -> 4
  %     modulo (remainder)    e.g.  9 % 2           -> 1
  **    exponent (power)      e.g.  2 ** 10         -> 1024
  ^     same as ** (power)    e.g.  3 ^ 4           -> 81

Grouping and precedence
-----------------------
  Use parentheses to control evaluation order:
      (2 + 3) * 4              -> 20
      2 + 3 * 4                -> 14

Number formats accepted
-----------------------
  Integers                     42,  -7
  Decimals                     3.14,  .5
  Scientific notation          1e3,  2.5e-2

Notes
-----
  * Division or modulo by zero returns an error.
  * Only numbers and the operators above are allowed --
    variables, functions and other code are rejected.
"""


def main():
    print(BANNER)
    print(HELP)
    while True:
        try:
            expr = input("calc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not expr:
            continue
        lowered = expr.lower()
        if lowered in {"q", "quit", "exit"}:
            print("Goodbye.")
            break
        if lowered in {"help", "?"}:
            print(HELP)
            continue
        result = evaluate(expr)
        if result is None:
            print("  Error: invalid expression. Type 'help' to see what's supported.")
        else:
            print(f"  = {result}")


if __name__ == "__main__":
    main()
