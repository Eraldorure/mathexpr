"""If you're looking for infos about this project, please check out the README file."""

import math
import types
import string

import _rules as r
import _tools as t


# ---------------------------------------------------- # TOOLS # ----------------------------------------------------- #


def convert_expr(expr):
    """This function is made to convert an expression (that can be made of ints, floats, complexes, or any
    Expression-like object) into the most corresponding object present inside the VALID_TYPES set.
    Note that it will "de-embed" the expression if it is an Expression object, and will return the expr attribute.
    Since there isn't any complex number type in the VALID_TYPES set, it will decompose it into a (a + b * i) sum."""

    if isinstance(expr, tuple(VALID_TYPES)):
        return expr
    # elif isinstance(expr, Expression):
    #     return expr.expr
    elif isinstance(expr, str):
        # return parse_expr(expr).expr
        return parse_expr(expr)
    elif isinstance(expr, (int, float, t.Fraction)):
        return Number(expr)
    elif isinstance(expr, complex):
        return expr.real + expr.imag * ImaginaryUnit()
    raise TypeError(f"invalid type '{type(expr)}' for expression '{expr}'")


def parse_expr(txt: str):
    """This function is made to parse a string into an Expression object.
    The txt argument must be a string that contains a valid Python expression. It is therefore important to note that
    it follows the same rules as Python in terms of operator signs. Furthermore, the multiplication operator is needed,
    and cannot be omitted."""

    aliases = {"sinh": "HyperbolicSine", "sh": "HyperbolicSine", "arcsin": "ArcSine", "asin": "ArcSine", "sin": "Sine",  # sin
               "cosh": "HyperbolicCosine", "ch": "HyperbolicCosine", "arccos": "ArcCosine", "acos": "ArcCosine", "cos": "Cosine",  # cos
               "tanh": "HyperbolicTangent", "th": "HyperbolicTangent", "arctan": "ArcTangent", "atan": "ArcTangent", "tan": "Tangent",  # tan
               "exp": "Exponential", "e": "EulerNumber()", "ln": "NaturalLogarithm",  # exp, ln
               "sqrt": "SquareRoot", "pi": "Pi()", "i": "ImaginaryUnit()", ",": ".", "^": "**"}  # other
    print("     Input |", repr(original := txt))
    i = 0
    txt = t.replace_seqs(t.remove_seqs(t.lower_except_single_letters(txt), " ", "\t", "\n"), aliases) + " "
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
        raise SyntaxError(f"{e.msg} in expression '{original}'")
    except NameError as e:
        raise NameError(f"'{e.name}' is not defined in expression '{original}'")


# ---------------------------------------------------- # BASICS # ---------------------------------------------------- #


class _Common:
    """All default magic methods for all the expression types. All of them inherit directly or indirectly from this class."""

    def __ne__(self, other):
        return not self == other

    def __add__(self, other):
        return Addition(self, other)

    def __radd__(self, other):
        return Addition(other, self)

    def __neg__(self):
        new = type(self)()
        new.neg = not new.neg
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
        return Multiplication(self, Exponentiation(other, -1))

    def __rtruediv__(self, other):
        return Multiplication(other, Exponentiation(self, -1))

    def __pow__(self, other):
        return Exponentiation(self, other)

    def __rpow__(self, other):
        return Exponentiation(other, self)

    def simplify(self):
        return self

    @staticmethod
    def size():
        return 1

    neg = False
    SIMP = False
    ORDER = 0


class Number(_Common):
    """This class is used to represent a number, which is stored as a <_tools.Fraction> type."""

    def __init__(self, value: int | float | t.Fraction, *, neg: bool = False):
        if neg:
            value = -value
        self.val = t.Fraction(value)

    def __call__(self, var: dict[str, any]):
        return self

    def __repr__(self):
        num = -self.val.numerator if self.neg else self.val.numerator
        den = self.val.denominator
        return ("-" if self.neg else "") + (str(num) if den == 1 else f"({num}/{den})")

    def __hash__(self):
        return hash(self.val)

    def __neg__(self):
        return Number(-self.val)

    def __eq__(self, other):
        return self.val == other.val if isinstance(other, Number) else self.val == other

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

    @property
    def neg(self):
        return self.val < 0


class Variable(_Common):
    """A basic variable. It is represented by a single letter that isn't already used as a constant ("i" and "e" are
    disallowed). There is no way to specify whether a Variable object is a used as a constant or a true variable, as
    that depends solely on how the user uses it."""
    def __init__(self, name: str, *, neg: bool = False):
        ok, err = r.var_name_ok(name)
        if not ok:
            raise err
        self.name = name
        self.neg = neg

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
    """The base class for mathematical constants."""

    def __init__(self, value: int | float, name: str, *, neg: bool = False):
        self.name = name
        super().__init__(value, neg=neg)

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
    """The pi constant, used primarily for angles and circles."""

    def __init__(self, *, neg: bool = False):
        super().__init__(math.pi, "π", neg=neg)

    def __neg__(self):
        return Pi(neg=not self.neg)


class EulerNumber(_Constant):
    """Euler's number, which is involved in the definition of the exponential function."""

    def __init__(self, *, neg: bool = False):
        super().__init__(math.e, "e", neg=neg)

    def __neg__(self):
        return EulerNumber(neg=not self.neg)

    def __pow__(self, other):
        return Exponential(other, neg=self.neg)


class ImaginaryUnit(_Common):
    """This class is used to represent the imaginary unit, which is displayed as the letter "i" (and not "j", contrary
    to Python). It means that there is no complex number type, and that it will need to be made the good ol' way."""

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

    def __pow__(self, power):
        return Exponential(Number(0.5) * ImaginaryUnit() * Pi() * power)

    def __eq__(self, other):
        return isinstance(other, ImaginaryUnit) and self.neg == other.neg

    @staticmethod
    def derivative(_):
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


# -------------------------------------------------- # OPERATORS # --------------------------------------------------- #


class Addition(_Common):
    """A simple addition. It is also used for subtractions, as it is simply an addition with a negative object."""

    def __init__(self, *operands, neg: bool = False, simp: bool = True):
        self.num = 0
        self.oper = t.UnorderedTuple()
        for el in operands:
            el = convert_expr(el)
            if el.SIMP:
                el = el.simplify()
            if type(el) is Number:
                self.num += el.val
            elif isinstance(el, Addition):
                self.oper += el.oper
                self.num += el.num
            else:
                self.oper += t.UnorderedTuple((el,))
        self.neg = neg
        self.SIMP = simp

    def __repr__(self):
        res = ""
        oper = self.oper + ((Number(self.num),) if self.num else ())
        for el in oper:
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
        return isinstance(other, Addition) and self.oper == other.oper and self.num == other.num and self.neg == other.neg

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
                    smallest = el.get_smallest_size()
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
        elif len(res.oper) == 1 and not res.num:
            return -res.oper[0] if res.neg else res.oper[0]
        return res

    def size(self):
        return 1 + sum(el.size() for el in self.oper) + (self.num != 0)

    ORDER = 3


class Multiplication(_Common):
    """The multiplication operator. It is also used for divisions, since the denominator is stored as an object to a
    negative power."""

    def __init__(self, *operands, neg: bool = False, simp: bool = True):
        self.coef = t.Fraction(1)
        self.oper = t.UnorderedTuple()
        for el in operands:
            el = convert_expr(el)
            if el.SIMP:
                el = el.simplify()
            if el.neg:
                self.neg = not self.neg
                el = -el
            if type(el) is Number:
                self.coef *= el.val
            elif type(el) is Exponentiation and type(el.base) is Number and type(el.power) is Number and el.power.val.is_integer():
                self.coef *= el.base.val ** el.power.val
            elif isinstance(el, Multiplication):
                self.coef *= el.coef
                self.oper += el.oper
            else:
                self.oper += t.UnorderedTuple((el,))
        self.neg = neg
        self.SIMP = simp

    def __repr__(self):  # I am deeply ashamed of this method
        mul = {"add": "", "var": "", "fn": "", "other": "", "_count": 0}
        div = {"add": "", "var": "", "fn": "", "other": "", "_count": 0}
        for el in self.oper:
            if isinstance(el, Exponentiation) and el.power.neg:
                current = div
                el = el.base if el.power == -1 else (el.base ** (-el.power)).simplify()
            else:
                current = mul
            if isinstance(el, (Variable, ImaginaryUnit, _Constant)):
                current["var"] += f"{el}"
            elif isinstance(el, Addition):
                current["add"] += f"({el})"
            elif isinstance(el, tuple(FUNCTION_TYPES)):
                current["fn"] += f"{el}"
            else:
                current["other"] += f" * {el}" if current["_count"] else f"{el}"
            current["_count"] += 1
        res = "-" if self.neg else ""
        if mul["_count"]:
            res += ((str(self.coef.numerator) if self.coef.numerator != 1 else "")
                    + mul["add"] + mul["var"] + (" * " if mul["var"] and mul["fn"] else "") + mul["fn"] + mul["other"])
        else:
            res += str(self.coef.numerator)
        if div["_count"]:
            div_res = ((str(self.coef.denominator) if self.coef.denominator != 1 else "")
                       + div["add"] + div["var"] + (" * " if div["var"] and div["fn"] else "") + div["fn"] + div["other"])
            res += f" / ({div_res})" if div["_count"] > 1 or div["_count"] and self.coef.denominator != 1 else f" / {div_res}"
        elif self.coef.denominator != 1:
            res += f" / {self.coef.denominator}"
        return res

    def __hash__(self):
        return hash((Multiplication, self.coef, tuple(self.oper), self.neg))

    def __neg__(self):
        return Multiplication(*self.oper, self.coef, neg=not self.neg)

    def __eq__(self, other):
        return (isinstance(other, Multiplication) and self.oper == other.oper
                and self.coef == other.coef and self.neg == other.neg)

    def is_calculable(self) -> bool:
        return all(el.is_calculable() for el in self.oper)

    def get_variables(self) -> set[str]:
        res = set()
        for el in self.oper:
            res.update(el.get_variables())
        return res

    def remove_element(self, element):
        if type(element) is Number:
            return Multiplication(*self.oper, self.coef / element, neg=self.neg)
        for i in range(len(self.oper)):
            if self.oper[i] == element:
                return Multiplication(*self.oper[:i], *self.oper[i + 1:], self.coef, neg=self.neg)
        return self

    def get_smallest_size(self):
        size = self.oper[0].size()
        element = self.oper[0]
        for el in self.oper[1:]:
            if el.size() < size:
                size = el.size()
                element = el
        return element

    def derivative(self, var: str):
        res = Number(0)
        for i in range(len(self.oper)):
            res += Multiplication(*self.oper[:i], self.oper[i].derivative(var), *self.oper[i + 1:], self.coef, neg=self.neg)
        return res

    def simplify(self):
        powers = {Number(v): (False, p) for v, p in t.prime_factors(self.coef.numerator).items()}
        powers.update({Number(v): (False, -p) for v, p in t.prime_factors(self.coef.denominator).items()})
        for el in self.oper:
            if isinstance(el, Exponentiation):
                if el.base in powers:
                    powers[el.base] = (powers[el.base][0] != el.neg), powers[el.base][1] + el.power
                else:
                    powers[el.base] = el.neg, el.power
            else:
                powers[el] = ((powers[el][0] != el.neg), powers[el][1] + 1) if el in powers else (False, 1)
        new = Multiplication(neg=self.neg)
        for el, info in powers.items():
            if el == 0:
                return Number(0)
            if info[1] == 1:
                new *= -el if info[0] else el
            elif info[1] != 0:
                new *= Exponentiation(el, info[1], neg=info[0])
        if len(new.oper) == 1 and new.coef == 1:
            return -new.oper[0] if new.neg else new.oper[0]
        elif not new.oper:
            return Number(new.coef, neg=new.neg)
        return new

    def size(self):
        return 1 + sum(el.size() for el in self.oper) + (self.coef != 1)

    ORDER = 2


class Exponentiation(_Common):
    """The class that represents the exponentiation operator, which is used to raise a something to a power."""

    def __init__(self, base, power, *, neg: bool = False, simp: bool = True):
        self.power = convert_expr(power)
        if self.power.SIMP:
            self.power = self.power.simplify()
        self.base = convert_expr(base).simplify()
        if self.power.SIMP:
            self.power = self.power.simplify()
        if isinstance(self.base, Exponentiation):
            self.power = (self.power * self.base.power).simplify()
            self.base = self.base.base
        self.neg = neg
        self.SIMP = simp

    def __call__(self, var: dict[str, any]):
        return Exponentiation(self.base(var), self.power(var), neg=self.neg)

    def __repr__(self):
        base = repr(self.base)
        power = repr(self.power)
        if self.base.neg or self.base.ORDER > self.ORDER:
            base = f"({base})"
        if self.power.neg or self.power.ORDER >= self.ORDER:
            power = f"({power})"
        return f"{'-' if self.neg else ''}{base} ** {power}"

    def __hash__(self):
        return hash((Exponentiation, self.base, self.power, self.neg))

    def __neg__(self):
        return Exponentiation(self.base, self.power, neg=not self.neg)

    def derivative(self, var: str):
        return self.base.derivative(var) * self.power * self.base ** (self.power - 1) + \
            self.power.derivative(var) * NaturalLogarithm(self.base) * self.base ** self.power

    def simplify(self):
        if self.power == 0:
            return Number(1, neg=self.neg)
        elif self.power == 1:
            return -self.base if self.neg else self.base
        elif self.power == 0.5:
            return SquareRoot(self.base, neg=self.neg).simplify()
        elif isinstance(self.base, Multiplication):
            if self.base.coef != 1 and self.power != -0.5:
                return Exponentiation(Multiplication(*self.base.oper), self.power, neg=self.neg) * Number(self.base.coef) ** self.power
            elif self.power == -1:
                return Multiplication(*[Exponentiation(el, -1, simp=False) for el in self.base.oper], neg=self.neg)
        elif type(self.base) is Number and type(self.power) is Number and (res := self.base.val ** self.power.val).is_integer():
            return Number(res, neg=self.neg)
        return self

    def size(self):
        return 1 + self.base.size() + self.power.size()

    ORDER = 1


# -------------------------------------------------- # FUNCTIONS # --------------------------------------------------- #


class Exponential(Exponentiation):
    """The class that represents the exponential function, which is equivalent to (e ** x)."""

    def __init__(self, expression, *, neg: bool = False, simp: bool = True):
        super().__init__(EulerNumber(), expression, neg=neg, simp=simp)

    def __repr__(self):
        return f"{'-' if self.neg else ''}exp({self.power})"

    def __neg__(self):
        return Exponential(self.power, neg=not self.neg)

    def derivative(self, var: str):
        return self.power.derivative(var) * Exponential(self.power)

    def simplify(self):
        if self.power == 0:
            return Number(1, neg=self.neg)
        elif self.power == 1:
            return EulerNumber(neg=self.neg)
        elif isinstance(self.power, NaturalLogarithm):
            return self.power.expr
        elif isinstance(self.power, Multiplication) and self.power.oper == t.UnorderedTuple((Pi(), ImaginaryUnit())):
            num = (-self.power.coef if self.power.neg else self.power.coef) % 2
            answers = {0: Number(1), 0.5: ImaginaryUnit(), 1: Number(-1), 1.5: -ImaginaryUnit()}
            if num in answers:
                return -answers[num] if self.neg else answers[num]
        return self

    def size(self):
        return 1 + self.power.size()

    ORDER = 0


class NaturalLogarithm(_Common):
    """The class that represents the natural logarithm function. It is the opposite of the exponential function."""

    def __init__(self, expression, *, neg: bool = False, simp: bool = True):
        self.expr = convert_expr(expression)
        if self.expr.SIMP:
            self.expr = self.expr.simplify()
        self.neg = neg
        self.SIMP = simp

    def __repr__(self):
        return f"{'-' if self.neg else ''}ln({self.expr})"

    def __hash__(self):
        return hash((NaturalLogarithm, self.expr, self.neg))

    def __neg__(self):
        return NaturalLogarithm(self.expr, neg=not self.neg)

    def derivative(self, var: str):
        return (-1 if self.neg else 1) * self.expr.derivative(var) / self.expr

    def simplify(self):
        if self.expr == 1:
            return Number(0)
        elif self.expr == EulerNumber():
            return Number(1)
        elif isinstance(self.expr, Exponential):
            return self.expr.power
        elif isinstance(self.expr, Multiplication):  # Keep? Because it's true only in certain cases (when all elements are positive)
            return Addition(*[NaturalLogarithm(el) for el in self.expr.oper + (self.expr.coef,)], neg=self.neg)
        elif isinstance(self.expr, Exponentiation):  # Keep? Because it's true only in certain cases (when the base is positive)
            return self.expr.power * NaturalLogarithm(self.expr.base, neg=self.neg)
        return self

    def size(self):
        return 1 + self.expr.size()


class SquareRoot(Exponentiation):
    """The class that represents the square root function, which is equivalent to a 0.5 power."""

    def __init__(self, base, *, neg: bool = False, simp: bool = True):
        super().__init__(base, Number(0.5), neg=neg, simp=simp)

    def __repr__(self):
        return f"{'-' if self.neg else ''}sqrt({self.base})"

    def derivative(self, var: str):
        return self.base.derivative(var) / (2 * SquareRoot(self.base))

    def simplify(self):
        if self.power != 0.5:
            return Exponentiation(self.base, self.power, neg=self.neg).simplify()
        elif self.base == 0:
            return Number(0)
        elif self.base == 1:
            return Number(-1 if self.neg else 1)
        elif type(self.base) is Number and (res := math.sqrt(self.base.val)).is_integer():
            return Number(res, neg=self.neg)
        elif isinstance(self.base, Multiplication):
            keep = []
            remove = []
            for el in self.base.oper:
                if isinstance(el, Exponentiation):
                    remove.append(SquareRoot(el))
                else:
                    keep.append(el)
            if (res := math.sqrt(self.base.coef)).is_integer():
                return Multiplication(*remove, Number(res), SquareRoot(Multiplication(*keep), simp=False), neg=self.neg)
            return Multiplication(*remove, SquareRoot(Multiplication(*keep, self.base.coef), simp=False), neg=self.neg)
        return self

    def size(self):
        return 1 + self.base.size()

    ORDER = 0


class Factorial(_Common):
    pass  # TODO


# ----------------------------------------------------- # SETS # ----------------------------------------------------- #


VALID_TYPES = {eval(el) for el in dir()
               if el[0] != "_" and type(eval(el)) not in {types.ModuleType, types.FunctionType}}  # - {Expression}

FUNCTION_TYPES = {Exponential, NaturalLogarithm, SquareRoot}  # Complete as more functions are added


if __name__ == '__main__':
    val = (2 * Variable("x") ** 2 + 4 * Variable("x")) / Variable("x") + 1  # TODO: Find a way to better factorize additions
    print("     Value |", val)
    val_simp = val.simplify()
    print("Simplified |", val_simp)
    der = val_simp.derivative("x")
    print("Derivative |", der)
    der_simp = der.simplify()
    print("Simp. der. |", der_simp)
