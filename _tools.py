import string


class UnorderedList(list):
    """A quick little class that is made to be used as a list, but with the difference that it doesn't have any order."""

    def __init__(self, *args):
        super().__init__(args)

    def __repr__(self):
        return "UnorderedList(" + ", ".join(map(str, self)) + ")"

    def __hash__(self):
        return hash((UnorderedList, tuple(sorted(map(str, self)))))

    def __eq__(self, other: list):
        if isinstance(other, UnorderedList) and len(self) != len(other):
            return False
        other = other.copy()
        for el in self:
            if el not in other:
                return False
            other.remove(el)
        return True

    def __ne__(self, other):
        return not self == other


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
    print("Replacing.:", result)
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


if __name__ == '__main__':
    lst1 = UnorderedList(1, 2, 3, 4, 5)
    lst2 = UnorderedList(5, 4, 3, 2, 1)
    print(lst1, lst2, lst1 == lst2)
    print(hash(lst1), hash(lst2), hash(lst1) == hash(lst2))
