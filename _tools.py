import string
import math
from typing import Self


class UnorderedTuple(tuple):
    """A quick little class that is made to be used as a tuple (unmodifiable list), but with the difference that it
    doesn't have any order, which has an effect on equality tests."""

    def __repr__(self):
        return "UnorderedTuple(" + ", ".join(map(str, self)) + ")"

    def __hash__(self):
        return hash((UnorderedTuple, tuple(sorted(map(str, self)))))

    def __eq__(self, other: tuple):
        if isinstance(other, UnorderedTuple) and len(self) != len(other):
            return False
        other = list(other)
        for el in self:
            if el not in other:
                return False
            other.remove(el)
        return True

    def __ne__(self, other):
        return not self == other

    __lt__ = __le__ = __gt__ = __ge__ = NotImplemented


class Fraction:
    """The simple implementation of a mathematical fraction."""

    # Miscellaneous
    def __init__(self, numerator: int | float | Self, denominator: int | float = 1):
        if not isinstance(numerator, (float, int, Fraction)):
            raise TypeError(f"the numerator must be an int, a float or a Fraction (not {type(numerator).__name__})")
        elif not isinstance(denominator, (float, int)):
            raise TypeError(f"the denominator must be an int or a float (not {type(denominator).__name__})")
        elif denominator == 0:
            raise ValueError("the denominator cannot be 0")

        if isinstance(numerator, Fraction) and denominator == 1:
            self.numerator, self.denominator = numerator.numerator, numerator.denominator
            return
        elif isinstance(numerator, float) or isinstance(denominator, float):  # If one is a float, we convert both to int
            while numerator - math.trunc(numerator) != 0.0 or denominator - math.trunc(denominator) != 0.0:
                numerator *= 10
                denominator *= 10
            numerator, denominator = int(numerator), int(denominator)

        if denominator < 0:  # The negation is always contained in the numerator
            numerator = -numerator
            denominator = -denominator

        gcd = math.gcd(numerator, denominator)  # Here we reduce the fraction
        self.numerator = numerator // gcd
        self.denominator = denominator // gcd

    def __copy__(self):
        return Fraction(self.numerator, self.denominator)

    def __repr__(self):
        return f"({self.numerator}/{self.denominator})"

    def __hash__(self):
        return hash(float(self))

    # Types
    def __float__(self):
        return self.numerator / self.denominator

    def __int__(self):
        return self.numerator // self.denominator

    def __bool__(self):
        return self.numerator != 0

    # Comparison operators
    def __eq__(self, other):
        if isinstance(other, Fraction):
            return self.numerator == other.numerator and self.denominator == other.denominator
        elif isinstance(other, int):
            return self.denominator == 1 and self.numerator == other
        elif isinstance(other, float):
            return math.isclose(self, other)
        return False

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if isinstance(other, (Fraction, float, int)):
            return float(self) < float(other)
        return False

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return self > other or self == other

    # Math operators
    def __add__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)
        return Fraction(self.numerator * other.denominator + other.numerator * self.denominator,
                        self.denominator * other.denominator)

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)
        return Fraction(self.numerator * other.denominator - other.numerator * self.denominator,
                        self.denominator * other.denominator)

    def __rsub__(self, other):
        return self - other

    def __neg__(self):
        return Fraction(-self.numerator, self.denominator)

    def __mul__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)
        return Fraction(self.numerator * other.numerator,
                        self.denominator * other.denominator)

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)
        return Fraction(self.numerator * other.denominator,
                        self.denominator * other.numerator)

    def __rtruediv__(self, other):
        return Fraction(other) / self

    def __floordiv__(self, other):
        if other < 0:
            raise ValueError("impossible to divide by a negative number yet")  # TODO: Implement it
        new = Fraction(self.numerator, self.denominator)
        times = Fraction(0)
        while new < 0:
            new += other
            times -= 1
        while new > other:
            new -= other
            times += 1
        return times

    def __rfloordiv__(self, other):
        return Fraction(other) // self

    def __mod__(self, other):
        new = Fraction(self.numerator, self.denominator)
        if other < 0:
            raise ValueError("the modulo must be positive")  # TODO: Implement it too
        while new < 0:
            new += other
        while new > other:
            new -= other
        return new

    def __rmod__(self, other):
        return Fraction(other) % self

    def __pow__(self, power, modulo=None):
        if power < 0:
            return pow(self.invert(), -power, modulo)
        return Fraction(self.numerator ** power, self.denominator ** power) % modulo if modulo is not None \
            else Fraction(self.numerator ** power, self.denominator ** power)

    def __rpow__(self, other, modulo=None):
        return pow(other, float(self), modulo)

    # Math functions
    def __abs__(self):
        return -self if self < 0 else self

    def __trunc__(self):
        return math.trunc(float(self))

    # Other methods
    def invert(self):
        """Returns the invert of the fraction (a/b becomes b/a)."""
        return Fraction(self.denominator, self.numerator)

    def is_integer(self):
        """Returns whether the fraction is an integer."""
        return self.denominator == 1


def replace_seqs(txt: str, new: dict[str, str]) -> str:
    """This function is made to replace all the occurrences of multiple sequences of characters by other sequences of
    characters.
    Warning: the order of the sequences in the dict is important since once a sequence is replaced, it will not be
    modified again. In short, no replacement will be made on characters that have already been replaced."""

    no_rep = []
    result = [txt]
    for before, after in new.items():
        if before == "":
            continue
        for i, el in enumerate(result):
            if i not in no_rep:
                j = el.find(before)
                if j != -1:
                    result[i] = el[:j]
                    result.insert(i + 1, after)
                    result.insert(i + 2, el[j + len(before):])
                no_rep.append(i + 1)
    print(" Replacing |", result)
    return "".join(result)


def remove_seqs(txt: str, *seqs: str) -> str:
    """This simple function removes each occurrence of every single given sequences from the given text.
    Warning: in some extreme cases, the order of the sequences can be important. You'll have to check yourself what does
    or doesn't work."""

    for seq in seqs:
        txt = txt.replace(seq, "")
    return txt


def lower_except_single_letters(txt: str) -> str:
    """Even though the name is already pretty explicit, this function is made to lower all the letters in a given text
    except for the ones that are surrounded by non-letter characters."""

    txt = " " + txt + " "
    res = ""
    for i in range(1, len(txt) - 1):
        if txt[i - 1] not in string.ascii_letters and txt[i + 1] not in string.ascii_letters:
            res += txt[i]
        else:
            res += txt[i].lower()
    return res


def prime_factors(n: int) -> dict[int, int]:
    """This function returns a dict containing all the prime factors and their power of a given number."""
    if n == 0:
        return {0: 1}
    factors = {}
    i = 2
    while i * i <= n:
        if n % i:
            i += 1
        else:
            n //= i
            factors[i] = factors.get(i, 0) + 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


if __name__ == '__main__':
    test = prime_factors(28)
    res = 1
    for v, p in test.items():
        res *= v ** -p
    print(test, res == 1/28)
