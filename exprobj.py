"""If you're looking for infos about this project, please check out the README file."""

import math
import types
import string
import typing

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


class _MathObject:
    """All default methods and attributes for the expression types. This class is made for inheritance purposes only,
    and mustn't be instantiated."""

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
        return Multiplication(self, Exponentiation(-other if other.neg else other, -1, neg=other.neg))

    def __rtruediv__(self, other):
        return Multiplication(other, Exponentiation(-self if self.neg else self, -1, neg=self.neg))

    def __pow__(self, other):
        return Exponentiation(self, other)

    def __rpow__(self, other):
        return Exponentiation(other, self)

    def expand(self):
        return self

    def simplify(self):
        return self

    neg = False
    simp = False
    ORDER = 0


class Number(_MathObject):
    """This class is used to represent a number, which is stored as a <_tools.Fraction> type."""

    def __init__(self, value: int | float | t.Fraction, *, neg: bool = False):
        if neg:
            value = -value
        self.val = t.Fraction(value)

    def __call__(self, var: dict[str, typing.Any]):
        return self

    def __repr__(self):
        num = -self.val.numerator if self.neg else self.val.numerator
        den = self.val.denominator
        return ("-" if self.neg else "") + (str(num) if den == 1 else f"{num}/{den}")

    def __hash__(self):
        return hash(self.val)

    def __neg__(self):
        return Number(-self.val)

    def __eq__(self, other):
        return self.val == (other.val if isinstance(other, Number) else other)

    def __lt__(self, other):
        return self.val < (other.val if isinstance(other, Number) else other)

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    @staticmethod
    def derivative(_):
        return Number(0)

    def get_factors(self) -> dict:
        return {Number(v): Number(p) for v, p in t.fraction_prime_factors(self.val).items()}

    @staticmethod
    def get_variables() -> set[str]:
        return set()

    def is_integer(self):
        return self.val.is_integer()

    @property
    def neg(self):
        return self.val < 0


class Variable(_MathObject):
    """A basic variable. It is represented by a single letter that isn't already used as a constant ("i" and "e" are
    disallowed). There is no way to specify whether a Variable object is a used as a constant or a true variable, as
    that depends solely on how the user uses it."""
    def __init__(self, name: str, *, neg: bool = False):
        ok, err = r.var_name_ok(name)
        if not ok and not isinstance(self, _Constant):
            raise err
        self.name = name
        self.neg = neg

    def __call__(self, var: dict[str, typing.Any]):
        if self.name in var:
            return -convert_expr(var[self.name]) if self.neg else convert_expr(var[self.name])
        return self

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

    def get_factors(self) -> dict:
        return {-self: Number(1), Number(-1): Number(1)} if self.neg else {self: Number(1)}

    def get_variables(self) -> set[str]:
        return {self.name}


# -------------------------------------------------- # CONSTANTS # --------------------------------------------------- #


class _Constant(Variable):
    """The base class for mathematical constants."""

    def __hash__(self):
        return hash((_Constant, self.name, self.neg))

    def __eq__(self, other):
        return isinstance(other, _Constant) and self.name == other.name and self.neg == other.neg

    def __ne__(self, other):
        return not isinstance(other, _Constant) or self.name != other.name or self.neg != other.neg

    def derivative(self, var: str):
        return Number(0)

    def get_variables(self) -> set[str]:
        return set()


class Pi(_Constant):
    """The pi constant, used primarily for angles and circles."""

    def __init__(self, *, neg: bool = False):
        super().__init__("π", neg=neg)

    def __neg__(self):
        return Pi(neg=not self.neg)


class EulerNumber(_Constant):
    """Euler's number, which is involved in the definition of the exponential function."""

    def __init__(self, *, neg: bool = False):
        super().__init__("e", neg=neg)

    def __neg__(self):
        return EulerNumber(neg=not self.neg)

    def __pow__(self, other):
        return Exponential(other, neg=self.neg).simplify()


class ImaginaryUnit(_Constant):
    """This class is used to represent the imaginary unit, which is displayed as the letter "i" (and not "j", contrary
    to Python). It means that there is no complex number type, and that it will need to be made the good ol' way."""

    def __init__(self, *, neg: bool = False):
        super().__init__("i", neg=neg)

    def __neg__(self):
        return ImaginaryUnit(neg=not self.neg)

    def __pow__(self, power):
        # i ** n = exp(i * n * pi / 2)
        return Exponential(Multiplication(ImaginaryUnit(), Pi(), t.Fraction(1, 2), power)).simplify()

    def get_factors(self) -> dict:
        return {Number(-1): Number(0.5 + self.neg)}


# -------------------------------------------------- # OPERATORS # --------------------------------------------------- #


class Addition(_MathObject):
    """A simple addition. It is also used for subtractions, as those are simply additions with a negative object."""

    def __init__(self, *operands, neg: bool = False, simp: bool = True):
        self.num = t.Fraction(0)
        self.oper = t.UnorderedTuple()
        for el in operands:
            el = convert_expr(-el if neg else el)
            if el.simp:
                el = el.simplify()
            if isinstance(el, Number):
                self.num += el.val
            elif isinstance(el, Addition):
                self.oper += el.oper
                self.num += el.num
            else:
                self.oper += t.UnorderedTuple((el,))
        self.simp = simp

    def __call__(self, var: dict[str, typing.Any]):
        return Addition(*(el(var) for el in self.oper), self.num).simplify()

    def __repr__(self):
        res = ""
        oper = self.oper + ((Number(self.num),) if self.num or not self.oper else ())
        for el in oper:
            if res:
                res += f" - {repr(el)[1:]}" if el.neg else f" + {el}"
            else:
                res += f"-{repr(el)[1:]}" if el.neg else f"{el}"
        return res

    def __hash__(self):
        return hash((Addition, self.num, self.oper))

    def __neg__(self):
        return Addition(*(-el for el in self.oper), -self.num, simp=self.simp)

    def __eq__(self, other):
        return isinstance(other, Addition) and self.oper == other.oper and self.num == other.num

    def get_variables(self) -> set[str]:
        res = set()
        for el in self.oper:
            res.update(el.get_variables())
        return res

    def get_factors(self) -> dict:
        return {self: Number(1)}

    def derivative(self, var: str):
        return Addition(*(el.derivative(var) for el in self.oper), neg=self.neg)

    # def expand(self):  # Useless because an Addition object is by definition already expanded
    #     return Addition(*(el.expand() for el in self.oper), self.num, neg=self.neg)

    def simplify(self):
        obj = self
        working = True
        while working:  # loop because in some cases factorization requires multiple passes
            # step 1: decomposing the addition into a dict containing bases and a decomposition of the powers
            decompositions: dict[_MathObject, dict[_MathObject, dict[int, int | float | t.Fraction]]] = {}  # {base: {mul: {index: coef, ...}, ...}, ...}
            # i.e.  e**(3+x) + 3*e**x  --->  {e: {1: {0: 3}, x: {0: 1, 1: 1}}, 3: {1: {1: 1}}}
            if obj.num != 0:
                factors = Number(obj.num).get_factors()
                for base, power in factors.items():
                    decompositions[base] = {Number(1): {-1: power}}  # special index -1 for num
            for i in range(len(obj.oper)):
                if isinstance(obj.oper[i], (Exponentiation, Multiplication)):
                    factors = obj.oper[i].get_factors()
                else:
                    factors = {obj.oper[i]: Number(1)}
                for base, power in factors.items():
                    if isinstance(power, Addition):
                        mul = {}
                        if power.num != 0:
                            mul[Number(1)] = {i: power.num}
                        for el in power.oper:
                            if isinstance(el, Multiplication):
                                mul[Multiplication(*el.oper, neg=el.neg)] = {i: el.coef}
                            else:
                                mul[el] = {i: 1}
                    elif isinstance(power, Multiplication):
                        mul = {Multiplication(*power.oper, neg=power.neg): {i: power.coef}}
                    elif isinstance(power, Number):
                        mul = {Number(1, neg=power.neg): {i: abs(power.val)}}
                    else:
                        mul = {power: {i: 1}}
                    if base.neg:
                        base = -base
                    if base in decompositions:
                        for m in mul:
                            if m in decompositions[base]:
                                decompositions[base][m].update(mul[m])
                            else:
                                decompositions[base][m] = mul[m]
                    else:
                        decompositions[base] = mul
            # step 2: creating groups indicating which terms can be factorized by what
            groups: dict[_MathObject, set[int]] = {}  # {term: {index, ...}, ...}
            for base, power in decompositions.items():
                for mul, pos in power.items():
                    indexes = set(pos.keys())
                    if len(pos) < 2 or any(indexes & set(saved_indexes) not in (set(), indexes) for saved_indexes in groups.values()):
                        continue  # need at least 2 elements to factorize + factorizations cannot overlap
                    new_key = Exponentiation(base, mul * min(pos.values()))
                    if related_keys := t.find_value_in_dict(indexes, groups):
                        prev_key = related_keys.pop()
                        groups[Multiplication(prev_key, new_key)] = groups.pop(prev_key)
                    else:
                        groups[new_key] = indexes
            # step 3: constructing the new and simplified addition
            if groups:
                result = Addition()
                remaining = list(range(-1, len(obj.oper)))
                for factor, indexes in groups.items():
                    tmp = Addition()
                    for ind in indexes:
                        if ind == -1:
                            tmp += Number(obj.num) / factor
                        else:
                            tmp += obj.oper[ind] / factor
                        remaining.remove(ind)
                    result += factor * tmp
                for ind in remaining:
                    if ind == -1:
                        result += obj.num
                    else:
                        result += obj.oper[ind]
                obj = result
            else:
                working = False  # no simplification available, terminate loop and return current obj
            # step 4: checking whether the current addition is just a superfluous container
            if len(obj.oper) == 1 and obj.num == 0:
                return obj.oper[0]
            elif not obj.oper:
                return Number(obj.num)
        return obj

    neg = False
    ORDER = 3


class Multiplication(_MathObject):
    """The multiplication operator. It is also used for divisions, since the denominator is stored as an object to a
    negative power."""

    def __init__(self, *operands, neg: bool = False, simp: bool = True):
        self.coef = t.Fraction(1)
        self.oper = t.UnorderedTuple()
        for el in operands:
            el = convert_expr(el)
            if el.simp:
                el = el.simplify()
            if el.neg:
                neg = not neg
                el = -el
            if isinstance(el, Number):
                self.coef *= el.val
            elif isinstance(el, Multiplication):
                self.coef *= el.coef
                self.oper += el.oper
            else:
                self.oper += t.UnorderedTuple((el,))
        self.neg = neg
        self.simp = simp

    def __call__(self, var: dict[str, typing.Any]):
        return Multiplication(*(el(var) for el in self.oper), self.coef, neg=self.neg).simplify()

    def __repr__(self):
        def repr_single(mul: Multiplication, is_div: bool = False) -> str:
            res = add = var = fn = other = ""
            if mul.coef != 1:
                res += str(mul.coef.numerator)
            for el in mul.oper:
                if isinstance(el, Addition):
                    add += f"({el})"
                elif isinstance(el, Variable):
                    var += repr(el)
                elif isinstance(el, tuple(FUNCTION_TYPES)):
                    if fn:
                        fn += " * "
                    fn += repr(el)
                else:
                    if other:
                        other += " * "
                    other += repr(el)
            res += add + var
            if fn:
                if var:
                    res += " * "
                res += fn
            if other:
                if res:
                    res += " * "
                res += other
            elif not res:
                res = "1"
            if mul.neg:
                res = "-" + res
            return f"({res})" if is_div and (mul.coef == 1 and len(mul.oper) > 1 or mul.coef != 1 and len(mul.oper) > 0) else res

        num, den = self.get_fraction()
        if den.coef == 1 and len(den.oper) == 0:
            return repr_single(num)
        return repr_single(num) + " / " + repr_single(den, True)

    def __hash__(self):
        return hash((Multiplication, self.coef, tuple(self.oper), self.neg))

    def __neg__(self):
        return Multiplication(*self.oper, self.coef, neg=not self.neg, simp=self.simp)

    def __eq__(self, other):
        other = convert_expr(other)
        return (isinstance(other, Multiplication) and self.oper == other.oper
                and self.coef == other.coef and self.neg == other.neg)

    def get_fraction(self):
        num = [Number(self.coef.numerator)]
        den = [Number(-1), Number(self.coef.denominator)] if self.coef < 0 else [Number(self.coef.denominator)]
        for el in self.oper:
            if isinstance(el, Exponentiation) and el.power.neg:
                den.append(Exponentiation(el.base, -el.power, neg=el.neg))
            else:
                num.append(el)
        return Multiplication(*num, neg=self.neg), Multiplication(*den)

    def get_variables(self) -> set[str]:
        res = set()
        for el in self.oper:
            res.update(el.get_variables())
        return res

    def get_factors(self) -> dict:
        factors = {Number(v): Number(p) for v, p in t.fraction_prime_factors(self.coef).items()}
        for el in self.oper:
            for v, p in el.get_factors().items():
                factors[v] = (factors.get(v, Number(0)) + p).simplify()
        if self.neg:
            factors[Number(-1)] = (factors.get(Number(-1), Number(0)) + 1).simplify()
        return factors

    def remove_element(self, element):
        if isinstance(element, Number):
            return Multiplication(*self.oper, self.coef / element, neg=self.neg)
        for i in range(len(self.oper)):
            if self.oper[i] == element:
                return Multiplication(*self.oper[:i], *self.oper[i + 1:], self.coef, neg=self.neg)
        return self

    def derivative(self, var: str):
        res = Number(0)
        for i in range(len(self.oper)):
            res += Multiplication(*self.oper[:i], self.oper[i].derivative(var), *self.oper[i + 1:], self.coef, neg=self.neg)
        return res

    def expand(self):
        add = []
        others = [Number(self.coef).expand()]
        for el in self.oper:
            if isinstance(el, Addition):
                add.append(el)  # .expand() not necessary because Addition.expand(self) -> self
            else:
                others.append(el.expand())
        res = Multiplication(*others, neg=self.neg)
        for el in add:
            res = Addition(*(res * el_el for el_el in el.oper), res * el.num, neg=res.neg)
        return res

    def simplify(self):
        powers = {Number(v): (False, p) for v, p in t.fraction_prime_factors(self.coef).items()}
        for el in self.oper:
            if isinstance(el, Exponentiation):
                if el.base in powers:
                    powers[el.base] = (powers[el.base][0] != el.neg), powers[el.base][1] + el.power
                else:
                    powers[el.base] = el.neg, el.power
            else:
                powers[el] = ((powers[el][0] != el.neg), powers[el][1] + 1) if el in powers else (False, 1)
        tmp_oper = []
        for el, info in powers.items():
            if el == 0:
                return Number(0)
            if info[1] == 1:
                tmp_oper.append(-el if info[0] else el)
            elif info[1] != 0:
                tmp_oper.append(Exponentiation(el, info[1], neg=info[0]))
        new = Multiplication(*tmp_oper, neg=self.neg)
        if len(new.oper) == 1 and new.coef == 1:
            return -new.oper[0] if new.neg else new.oper[0]
        elif not new.oper:
            return Number(new.coef, neg=new.neg)
        return new

    ORDER = 2


class Exponentiation(_MathObject):
    """The class that represents the exponentiation operator, which is used to raise something to a power."""

    def __init__(self, base, power, *, neg: bool = False, simp: bool = True):
        self.base = convert_expr(base)
        if self.base.simp:
            self.base = self.base.simplify()
        self.power = convert_expr(power)
        if self.power.simp:
            self.power = self.power.simplify()
        if isinstance(self.base, Exponentiation):
            self.power = (self.power * self.base.power).simplify()
            self.base = self.base.base
        self.neg = neg
        self.simp = simp

    def __call__(self, var: dict[str, typing.Any]):
        return Exponentiation(self.base(var), self.power(var), neg=self.neg).simplify()

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
        return Exponentiation(self.base, self.power, neg=not self.neg, simp=self.simp)

    def get_variables(self) -> set[str]:
        return self.base.get_variables() | self.power.get_variables()

    def get_factors(self) -> dict:
        fact = {v: (p * self.power).simplify() for v, p in self.base.get_factors().items()}
        if self.neg:
            fact[Number(-1)] = (fact.get(Number(-1), Number(0)) + 1).simplify()
        return fact

    def derivative(self, var: str):
        return self.base.derivative(var) * self.power * self.base ** (self.power - 1) + \
            self.power.derivative(var) * NaturalLogarithm(self.base) * self.base ** self.power

    def expand(self):
        if isinstance(self.base, Multiplication):
            return Multiplication(*(Exponentiation(el, self.power, simp=False).expand() for el in self.base.oper), neg=self.neg)
        elif isinstance(self.power, Number) and self.power.is_integer() and self.power > 1:
            return Multiplication(*(self.base for _ in range(int(self.power.val))), neg=self.neg)
        return Exponentiation(self.base.expand(), self.power.expand(), neg=self.neg)

    def simplify(self):
        if self.power == 0:
            return Number(1, neg=self.neg)
        elif self.power == 1:
            return -self.base if self.neg else self.base
        elif self.base == 1:
            return Number(1, neg=self.neg)
        elif isinstance(self.base, (EulerNumber, ImaginaryUnit)):
            return -(self.base ** self.power) if self.neg else self.base ** self.power
        elif self.power == 0.5:
            return SquareRoot(self.base, neg=self.neg).simplify()
        elif isinstance(self.base, Multiplication):
            if self.base.coef != 1 and self.power != -0.5:
                return Exponentiation(Multiplication(*self.base.oper), self.power, neg=self.neg) * Number(self.base.coef) ** self.power
            elif self.power == -1:
                return Multiplication(*(Exponentiation(el, -1, simp=False) for el in self.base.oper), neg=self.neg)
        elif isinstance(self.base, Number) and isinstance(self.power, Number) and self.power.val.is_integer():
            return Number(self.base.val ** self.power.val, neg=self.neg)
        return self

    ORDER = 1


# -------------------------------------------------- # FUNCTIONS # --------------------------------------------------- #


class Exponential(Exponentiation):
    """The class that represents the exponential function (exp(x)), which is equivalent to (e ** x)."""

    def __init__(self, expression, *, neg: bool = False, simp: bool = True):
        super().__init__(EulerNumber(), expression, neg=neg, simp=simp)

    def __repr__(self):
        return f"{'-' if self.neg else ''}exp({self.power})"

    def __neg__(self):
        return Exponential(self.power, neg=not self.neg, simp=self.simp)

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
            answers = {
                t.Fraction(0): Number(1),
                t.Fraction(1, 2): ImaginaryUnit(),
                t.Fraction(1): Number(-1),
                t.Fraction(3, 2): -ImaginaryUnit()
            }
            if num in answers:
                return -answers[num] if self.neg else answers[num]
        return self

    ORDER = 0


class NaturalLogarithm(_MathObject):
    """The class that represents the natural logarithm function (ln(x)). It is the opposite of the exponential function,
    which means that (exp(ln(x)) = ln(exp(x)) = x)."""

    def __init__(self, expression, *, neg: bool = False, simp: bool = True):
        self.expr = convert_expr(expression)
        if self.expr.simp:
            self.expr = self.expr.simplify()
        self.neg = neg
        self.simp = simp

    def __call__(self, var: dict[str, typing.Any]):
        return NaturalLogarithm(self.expr(var), neg=self.neg).simplify()

    def __repr__(self):
        return f"{'-' if self.neg else ''}ln({self.expr})"

    def __hash__(self):
        return hash((NaturalLogarithm, self.expr, self.neg))

    def __neg__(self):
        return NaturalLogarithm(self.expr, neg=not self.neg, simp=self.simp)

    def get_variables(self) -> set[str]:
        return self.expr.get_variables()

    def get_factors(self) -> dict:
        return {self: Number(1)} if self.neg else {-self: Number(1), Number(-1): Number(1)}

    def derivative(self, var: str):
        return (-1 if self.neg else 1) * self.expr.derivative(var) / self.expr

    def expand(self):
        return NaturalLogarithm(self.expr.expand(), neg=self.neg)

    def simplify(self):
        if self.expr == 1:
            return Number(0)
        elif self.expr == EulerNumber():
            return Number(1)
        elif isinstance(self.expr, Exponential):
            return self.expr.power
        # elif isinstance(self.expr, Multiplication):  # Keep? Because it's true only in certain cases (when all elements are positive)
        #     return Addition(*(NaturalLogarithm(el) for el in self.expr.oper + (self.expr.coef,)), neg=self.neg)
        # elif isinstance(self.expr, Exponentiation):  # Keep? Because it's true only in certain cases (when the base is positive)
        #     return self.expr.power * NaturalLogarithm(self.expr.base, neg=self.neg)
        return self


class SquareRoot(Exponentiation):
    """The class that represents the square root function, which is equivalent to a 0.5 power."""

    def __init__(self, base, *, neg: bool = False, simp: bool = True):
        super().__init__(base, Number(0.5), neg=neg, simp=simp)

    def __repr__(self):
        return f"{'-' if self.neg else ''}sqrt({self.base})"

    def derivative(self, var: str):
        return self.base.derivative(var) / (2 * SquareRoot(self.base, neg=self.neg))

    def simplify(self):
        if self.power != 0.5:
            return Exponentiation(self.base, self.power, neg=self.neg).simplify()
        elif self.base == 0:
            return Number(0)
        elif isinstance(self.base, Number):
            if self.base.neg:
                value = -self.base.val
                mul = ImaginaryUnit()
            else:
                value = self.base.val
                mul = 1
            if (res := math.sqrt(value)).is_integer():
                return Multiplication(mul, res, neg=self.neg)
            return Multiplication(mul, SquareRoot(value, simp=False), neg=self.neg)
        elif isinstance(self.base, Multiplication):
            inside = []
            outside = []
            for el in self.base.oper:
                if isinstance(el, Exponentiation):
                    outside.append(SquareRoot(el))
                else:
                    inside.append(el)
            if (res := math.sqrt(self.base.coef)).is_integer():
                outside.append(res)
            else:
                outside.append(self.base.coef)
            tmp = SquareRoot(Multiplication(*inside), simp=False)
            return Multiplication(*outside, (1 if tmp.base == 1 else tmp), neg=self.neg)
        return self

    ORDER = 0


# ----------------------------------------------------- # SETS # ----------------------------------------------------- #


VALID_TYPES = {eval(el) for el in dir()
               if el[0] != "_" and type(eval(el)) not in {types.ModuleType, types.FunctionType}}

FUNCTION_TYPES = {Exponential, NaturalLogarithm, SquareRoot}


if __name__ == '__main__':
    val = 1 + (2 * Variable("x") ** 2 + 6 * Variable("x") - 2 * Variable("x")) / Variable("x")
    # val = parse_expr("3*x + 3*y + 3*z - 3")
    # val = ImaginaryUnit() ** 2
    print("     Value |", val)
    print("   Factors |", val.get_factors())
    val_simp = val.simplify()
    print("Simplified |", val_simp)
    print("Simplif. 2 |", val_simp.simplify())
    val_exp = val.expand()
    print("  Expanded |", val_exp)
    print("Exp + simp |", val_exp.simplify())
    # der = val_simp.derivative("x")
    # print("Derivative |", der)
    # print(" Der. exp. |", der.expand())
    # print("Der. simp. |", der.simplify())
