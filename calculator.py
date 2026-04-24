import ast
import math
import operator
import re
import sys

import plotext as plt


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


def _eval(node, env):
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError(f"unknown name: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval(node.left, env), _eval(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand, env))
    raise ValueError("unsupported expression")


def evaluate(expr):
    # Let '^' mean exponentiation the way most calculators do.
    expr = expr.replace("^", "**")
    try:
        return _eval(ast.parse(expr, mode="eval"), {})
    except (SyntaxError, ValueError, ZeroDivisionError, TypeError, OverflowError):
        return None


def _compile_expr(expr, allowed_names):
    """Parse `expr` once and return a callable that evaluates it given a var binding.

    Returns None if the expression is invalid or references a name outside
    `allowed_names`. The returned callable accepts keyword args for each
    allowed name and returns the numeric result, or None on runtime errors
    (division by zero, overflow, etc.).
    """
    expr = expr.replace("^", "**")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in allowed_names:
            return None

    def fn(**env):
        try:
            return _eval(tree, env)
        except (ValueError, ZeroDivisionError, TypeError, OverflowError):
            return None

    return fn


_PLOT_CMD_RE = re.compile(r"^\s*plot\s+(.+)$", re.IGNORECASE)
_PLOT_RANGE_RE = re.compile(r"^(.+?)\s+from\s+(.+?)\s+to\s+(.+?)\s*$", re.IGNORECASE)


def _plot(line):
    m = _PLOT_CMD_RE.match(line)
    if not m:
        print("  Error: usage 'plot <expr>' or 'plot <expr> from <a> to <b>'.")
        return
    rest = m.group(1).strip()

    m2 = _PLOT_RANGE_RE.match(rest)
    if m2:
        expr_part = m2.group(1).strip()
        lo = evaluate(m2.group(2).strip())
        hi = evaluate(m2.group(3).strip())
    else:
        expr_part = rest
        lo, hi = -10.0, 10.0

    if lo is None or hi is None:
        print("  Error: invalid range.")
        return
    if hi <= lo:
        print("  Error: range end must be greater than range start.")
        return

    fn = _compile_expr(expr_part, allowed_names={"x"})
    if fn is None:
        print("  Error: invalid plot expression (use 'x' as the variable).")
        return

    samples = 200
    xs, ys = [], []
    for i in range(samples + 1):
        x = lo + (hi - lo) * i / samples
        y = fn(x=x)
        if y is None or isinstance(y, bool) or not isinstance(y, (int, float)):
            continue
        if math.isinf(y) or math.isnan(y):
            continue
        xs.append(x)
        ys.append(y)

    if not xs:
        print("  Error: expression could not be plotted over that range.")
        return

    plt.clear_figure()
    plt.plot(xs, ys)
    plt.title(f"y = {expr_part}")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.plotsize(70, 20)
    plt.show()


BANNER = r"""
==============================================================
                     Python Calculator
==============================================================
 Type a math expression and press Enter to see the result,
 or use the 'plot' command to graph a function in the terminal.
 Standard math rules apply: parentheses first, then powers,
 then multiplication/division, then addition/subtraction.

 Commands:
   plot <expr> [from <a> to <b>]   graph y = <expr> over x
   help  (or ?)                    show this guide again
   quit  (or q)                    exit the calculator
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

Plotting (terminal graph)
-------------------------
  Use 'x' as the variable. The plot renders as ASCII in the terminal.

      plot x                         straight line,  x in [-10, 10]
      plot x^2                       parabola,       x in [-10, 10]
      plot x**3 - 4*x                cubic,          x in [-10, 10]
      plot 1/x from 0.1 to 5         custom range
      plot (x - 2) * (x + 3) from -5 to 5

  The range is optional; it defaults to -10 to 10 when omitted.
  Points where the expression errors (e.g. divide-by-zero) are skipped.

Notes
-----
  * Division or modulo by zero in a plain calculation returns an error.
  * Outside of 'plot', only numbers and the operators above are allowed
    -- variables, functions and other code are rejected.
  * Inside 'plot', only the variable 'x' is recognised.
"""


def main():
    # plotext draws with Unicode braille/box chars; Windows' default cp1252
    # stdout can't encode those. Switch to UTF-8 where supported.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
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
        if lowered == "plot" or lowered.startswith("plot "):
            _plot(expr)
            continue
        result = evaluate(expr)
        if result is None:
            print("  Error: invalid expression. Type 'help' to see what's supported.")
        else:
            print(f"  = {result}")


if __name__ == "__main__":
    main()
