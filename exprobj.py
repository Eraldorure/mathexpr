"""If you're looking for infos about this project, please check out the README file"""

import math
import types

import _rules as r
from _tools import *


# ---------------------------------------------------- # TOOLS # ----------------------------------------------------- #


def convert_expr(expr):
    """This function is made to convert an expression (that can be made of ints, floats, complexes, or any
    Expression-like object) into the most corresponding object present inside the VALID_TYPES set.
    Note that it will "de-embed" the expression if it is an Expression object, and will return the expr attribute.
    Since there isn't any complex number type in the VALID_TYPES set, it will decompose it into u sum."""

    if isinstance(expr, tuple(VALID_TYPES)):
        return expr
    # elif isinstance(expr, Expression):
    #     return expr.expr
    elif isinstance(expr, str):
        # return parse_expr(expr).expr
        return parse_expr(expr)
    elif isinstance(expr, (int, float)):
        return Number(expr)
    elif isinstance(expr, complex):
        return expr.real + expr.imag * ImaginaryUnit()
    raise TypeError(f"invalid type '{type(expr)}' for expression '{expr}'")


def parse_expr(txt: str):
    """This function is made to parse a string into an Expression object.
    The expr argument must a string that contains a valid Python expression. It is therefore important to note that it
    follows the same rules as Python in terms of operator signs, which means that for example ** is the power operator,
    and not ^. Furthermore, the multiplication operator is needed, and cannot be omitted."""

    aliases = {"sinh": "HyperbolicSine", "sh": "HyperbolicSine", "arcsin": "ArcSine", "asin": "ArcSine", "sin": "Sine",  # sin
               "cosh": "HyperbolicCosine", "ch": "HyperbolicCosine", "arccos": "ArcCosine", "acos": "ArcCosine", "cos": "Cosine",  # cos
               "tanh": "HyperbolicTangent", "th": "HyperbolicTangent", "arctan": "ArcTangent", "atan": "ArcTangent", "tan": "Tangent",  # tan
               "exp": "Exponential", "e": "EulerNumber()", "ln": "NaturalLogarithm",  # exp, log
               "sqrt": "SquareRoot", "pi": "Pi()", "i": "ImaginaryUnit()", ",": ".", "^": "**"}  # other
    print("     Input |", repr(original := txt))
    i = 0
    txt = replace_seqs(remove_seqs(lower_except_single_letters(txt), " ", "\t", "\n"), aliases) + " "
    print("Normalized |", repr(txt))
    while i < len(txt):
        char = txt[i]
        before = txt[i - 1] if i > 0 else "_"
        if char not in string.ascii_letters + string.digits + "+-*/(). ":
            raise ValueError(f"invalid character '{char}' in expression '{txt}'")
        if char in string.digits and before not in string.digits + ".":  # "_1"
            txt = txt[:i] + f"Number(" + txt[i:]
            i += 7
        elif char not in string.digits + "." and before in string.digits:  # "1_"
            txt = txt[:i] + ")" + txt[i:]
            i += 1
        elif before not in string.ascii_letters and char in string.ascii_letters and \
                txt[i + 1] not in string.ascii_letters:  # "_a_"
            txt = txt[:i] + "Variable('" + char + "')" + txt[i + 1:]
            i += 13
        i += 1
    print("  Evaluate |", repr(txt))
    try:
        # return Expression(eval(txt))
        return eval(txt)
    except SyntaxError as e:
        raise SyntaxError(f"invalid syntax in expression '{original}' "
                          f"(are you sure you are using a Python-compliant syntax?)") from e
    except NameError as e:
        raise NameError(f"invalid name in expression '{original}' "
                        f"(are you sure you are naming a mathematical constant or function?)") from e


# ---------------------------------------------------- # BASICS # ---------------------------------------------------- #


class _Common:
    """All default magic methods for all the expression types. Almost all of them inherit from this class."""

    def __ne__(self, other):
        return not self == other

    def __add__(self, other):
        return Addition(self, other)

    def __radd__(self, other):
        return Addition(other, self)

    def __neg__(self):
        new = type(self)()
        new.neg = not self.neg
        return new

    def __sub__(self, other):
        return Addition(self, -other)

    def __rsub__(self, other):
        return Addition(other, -self)

    def __mul__(self, other):
        if other == 0:
            return Number(0)
        elif other == 1:
            return self
        return Multiplication(self, other)

    def __rmul__(self, other):
        if other == 0:
            return Number(0)
        elif other == 1:
            return self
        return Multiplication(other, self)

    def __truediv__(self, other):
        return Division(self, other)

    def __rtruediv__(self, other):
        return Division(other, self)

    def __pow__(self, other):
        return Exponentiation(self, other)

    def __rpow__(self, other):
        return Exponentiation(other, self)

    def simplify(self):
        return self

    @staticmethod
    def score():
        return 1

    neg = False
    ORDER = 0


class Number(_Common):
    """This class is used to represent a number, which is stored as either an integer or a float.
    SoonTM it will be a whole new type that will work on its own without having to rely on built-in types, thus removing
    the imprecision brought by floats."""
    # TODO: Recreate Python's whole number system (good luck future me)

    def __init__(self, value: int | float):
        if (typ := type(value)) not in {int, float}:
            raise TypeError(f"value must be either an int or a float, not {typ}")
        self.val = value

    def __call__(self, var: dict[str, any]):
        return self

    def __repr__(self):
        return str(self.val)

    def __hash__(self):
        return hash(-self.val if self.neg else self.val)

    def __neg__(self):
        return Number(-self.val)

    def __eq__(self, other):
        val_self = -self.val if self.neg else self.val
        if isinstance(other, Number):
            other = -other.val if other.neg else other.val
        return val_self == other

    def __lt__(self, other):
        val_self = -self.val if self.neg else self.val
        if isinstance(other, Number):
            other = -other.val if other.neg else other.val
        return val_self < other

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    @staticmethod
    def derivative(_):
        return Number(0)

    @staticmethod
    def is_complex() -> bool:
        return False

    @staticmethod
    def is_calculable() -> bool:
        return True

    @staticmethod
    def get_variables() -> set[str]:
        return set()

    def simplify(self):
        return Number(int(self.val)) if isinstance(self.val, float) and math.trunc(self.val) == self.val else self

    @property
    def neg(self):
        return self.val < 0


class Variable(_Common):
    def __init__(self, name: str, *, neg: bool = False):
        ok, err = r.var_name_ok(name)
        if not ok:
            raise err
        self.neg = neg
        self.name = name

    def __call__(self, var: dict[str, any]):
        return convert_expr(var[self.name]) if self.name in var else self

    def __repr__(self):
        return ("-" if self.neg else "") + self.name

    def __hash__(self):
        return hash((Variable, self.name, self.neg))

    def __neg__(self):
        return Variable(self.name, neg=not self.neg)

    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name and self.neg == other.neg

    def derivative(self, var: str):
        return Number(1 - 2 * self.neg if var == self.name else 0)

    @staticmethod
    def is_complex() -> bool:
        return False

    @staticmethod
    def is_calculable() -> bool:
        return False

    def get_variables(self) -> set[str]:
        return {self.name}


# -------------------------------------------------- # CONSTANTS # --------------------------------------------------- #


class _Constant(Number):
    def __init__(self, value: int | float, name: str, *, neg: bool = False):
        self.name = name
        super().__init__(value if not neg else -value)

    def __repr__(self):
        return ("-" if self.neg else "") + self.name

    def __hash__(self):
        return hash((_Constant, self.name, self.neg))

    def __eq__(self, other):
        return isinstance(other, _Constant) and self.name == other.name and self.neg == other.neg

    def __ne__(self, other):
        return not isinstance(other, _Constant) or self.name != other.name or self.neg != other.neg

    @staticmethod
    def is_calculable() -> bool:
        return False


class Pi(_Constant):
    def __init__(self, *, neg: bool = False):
        super().__init__(math.pi, "π", neg=neg)

    def __neg__(self):
        return Pi(neg=not self.neg)


class EulerNumber(_Constant):
    def __init__(self, *, neg: bool = False):
        super().__init__(math.e, "e", neg=neg)

    def __neg__(self):
        return EulerNumber(neg=not self.neg)

    def __pow__(self, other):
        return Exponential(other)


class ImaginaryUnit(_Common):
    """This class is used to represent the imaginary unit, which is stored as the letter i (and not j).
    It means that there is no complex number type, and that it will need to be made the good ol' way."""

    def __init__(self, *, neg: bool = False):
        self.neg = neg

    def __call__(self, var: dict[str, any]):
        return self

    def __repr__(self):
        return "-i" if self.neg else "i"

    def __hash__(self):
        return hash((ImaginaryUnit, self.neg))

    def __neg__(self):
        return ImaginaryUnit(neg=not self.neg)

    def __eq__(self, other):
        return isinstance(other, ImaginaryUnit) and self.neg == other.neg

    @staticmethod
    def derivative(_: str):
        return Number(0)

    @staticmethod
    def is_complex() -> bool:
        return True

    @staticmethod
    def is_calculable() -> bool:
        return False

    @staticmethod
    def get_variables() -> set[str]:
        return set()

    def simplify(self):
        return self


# -------------------------------------------------- # OPERATORS # --------------------------------------------------- #


class Addition(_Common):
    def __init__(self, *args, neg: bool = False):
        self.num = 0
        self.oper = UnorderedTuple()
        self.neg = neg
        for el in args:
            el = convert_expr(el).simplify()
            if type(el) is Number:
                self.num += el.val
            elif isinstance(el, Addition):
                self.oper += el.oper
                self.num += el.num
            else:
                self.oper += UnorderedTuple((el,))

    def __repr__(self):
        res = f"{self.num}" if self.num else ""
        for el in self.oper:
            if not res:
                res += f"-{repr(el)[1:]}" if el.neg else f"{el}"
            else:
                res += f" - {repr(el)[1:]}" if el.neg else f" + {el}"
        return res

    def __hash__(self):
        return hash((Addition, self.num, self.oper, self.neg))

    def __neg__(self):
        return Addition(*[-el for el in self.oper], -self.num, neg=not self.neg)

    def __eq__(self, other):
        return (type(self) is type(other) and set(self.oper) == set(other.oper)
                and self.num == other.num and self.neg == other.neg)

    def is_calculable(self) -> bool:
        return all(el.is_calculable() for el in self.oper)

    def get_variables(self) -> set[str]:
        res = set()
        for el in self.oper:
            res.update(el.get_variables())
        return res

    def derivative(self, var: str):
        return Addition(*[el.derivative(var) for el in self.oper], neg=self.neg)

    def simplify(self):
        amount = {}
        for el in self.oper:
            neg = el.neg
            el = -el if neg else el
            if isinstance(el, Multiplication):
                if join := el.oper & amount.keys():
                    key = join.pop()
                    amount[key] += -el.remove_element(key) if neg else el.remove_element(key)
                else:
                    smallest = el.get_lowest_score()
                    amount[smallest] = el.remove_element(smallest)
            elif el in amount:
                amount[el] += 1 - 2 * neg
            else:
                amount[el] = 1 - 2 * neg
        new = []
        for el, am in amount.items():
            new.append(am * el)
        res = Addition(*new, self.num, neg=self.neg)
        if not res.oper:
            return Number(self.num)
        return res

    def score(self):
        return sum(el.score() for el in self.oper) + (self.num != 0)

    ORDER = 3


class Multiplication(_Common):
    def __init__(self, *args, neg: bool = False):
        self.num = 1
        self.oper = UnorderedTuple()
        self.neg = neg
        for el in args:
            el = convert_expr(el).simplify()
            if el.neg:
                self.neg = not self.neg
                el = -el
            if type(el) is Number:
                self.num *= el.val
            elif isinstance(el, Multiplication):
                self.num *= el.num
                self.oper += el.oper
            else:
                self.oper += UnorderedTuple((el,))

    def __repr__(self):
        var = ""
        add = ""
        fn = ""
        other = ""
        for el in self.oper:
            if isinstance(el, (Variable, ImaginaryUnit, _Constant)):
                var += f"{el}"
            elif isinstance(el, Addition):
                add += f"({el})"
            elif el in FUNCTION_TYPES:
                fn += f"{el}"
            else:
                other += f" * {el}"
        if var and fn:
            var += " * "
        return f"{'-' if self.neg else ''}{self.num if self.num != 1 else ''}{add}{var}{fn}{other}"

    def __hash__(self):
        return hash((Multiplication, self.num, tuple(self.oper), self.neg))

    def __neg__(self):
        return Multiplication(*self.oper, self.num, neg=not self.neg)

    def __eq__(self, other):
        return (isinstance(other, Multiplication) and self.oper == other.oper
                and self.num == other.num and self.neg == other.neg)

    def is_calculable(self) -> bool:
        return all(el.is_calculable() for el in self.oper)

    def get_variables(self) -> set[str]:
        res = set()
        for el in self.oper:
            res.update(el.get_variables())
        return res

    def remove_element(self, element):
        if type(element) is Number:
            return Multiplication(*self.oper, self.num / element, neg=self.neg)
        for i in range(len(self.oper)):
            if self.oper[i] == element:
                return Multiplication(*self.oper[:i], *self.oper[i + 1:], self.num, neg=self.neg)
        return self

    def get_lowest_score(self):
        score = self.oper[0].score()
        element = self.oper[0]
        for el in self.oper[1:]:
            if el.score() < score:
                score = el.score()
                element = el
        return element

    def derivative(self, var: str):
        res = Number(0)
        for i in range(len(self.oper)):
            res += Multiplication(*self.oper[:i], self.oper[i].derivative(var), *self.oper[i + 1:], self.num, neg=self.neg)
        return res

    def simplify(self):
        if not self.num:
            return Number(0)
        elif len(self.oper) == 1 and self.num == 1:
            return -self.oper[0] if self.neg else self.oper[0]
        elif not self.oper:
            return Number(-self.num if self.neg else self.num)
        return self  # TODO: Complete once divisions and powers are implemented

    def score(self):
        res = 1
        for el in self.oper:
            res *= el.score()
        return res

    ORDER = 2


class Division(_Common):
    pass  # TODO


class Exponentiation(_Common):
    pass  # TODO


# -------------------------------------------------- # FUNCTIONS # --------------------------------------------------- #


class Exponential(Exponentiation):
    pass  # TODO


class NaturalLogarithm(_Common):
    pass  # TODO


class SquareRoot(Exponentiation):
    pass  # TODO


class Factorial(_Common):
    pass  # TODO


# ----------------------------------------------------- # SETS # ----------------------------------------------------- #


VALID_TYPES = {eval(el) for el in dir() if el[0] != "_" and
               type(eval(el)) not in {types.ModuleType, types.FunctionType}} - {-1}  # - {Expression}

FUNCTION_TYPES = {Exponential, NaturalLogarithm, SquareRoot}  # TODO : Complete as more functions are added


if __name__ == '__main__':
    val = 2 * Variable("x") * Pi() - 3 * EulerNumber() - Variable("x") * EulerNumber() + 2 + Pi()
    print("     Value |", val)
    print("Simplified |", val.simplify())
    print("Derivative |", val.derivative("x"))
    print("Simp. der. |", val.derivative("x").simplify())
