# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import sys
import math
import random
import logging


class DharmaConst(object):
    """Configuration settings for the Dharma generator."""
    pass


class MetaBlock(object):
    """Grammar extension which loads code fragments from a file into the grammar."""

    def __init__(self, path, parent):
        self.parent = parent
        path = os.path.expanduser(path)
        if os.path.exists(path):
            with open(path) as fo:
                self.content = fo.read()
        else:
            logging.warning('%s: Unable to load resource for block() "%s"', parent.id(), path)
            self.content = path

    def generate(self, state):
        return self.content


class MetaURI(object):
    """Grammar extension which loads a random file URI into the generated code."""

    def __init__(self, path, parent):
        self.parent = parent
        if path in DharmaConst.URI_TABLE:
            path = DharmaConst.URI_TABLE[path]
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            self.path = [p for p in (os.path.join(path, f) for f in os.listdir(path)) if os.path.isfile(p)]
        elif os.path.exists(path):
            self.path = [path]
        else:
            logging.warning('%s: Unable to identify argument of uri() "%s"', parent.id(), path)
            self.path = [path]

    def generate(self, state):
        return random.choice(self.path)


class MetaRepeat(object):
    """Grammar extension method which repeats an arbitrary expression."""

    def __init__(self, repeat, separator, nodups, parent):
        self.parent = parent
        self.repeat, self.separator, self.nodups = repeat, separator, nodups

    def generate(self, state):
        count = random.randint(1, math.pow(2, random.randint(1, DharmaConst.MAX_REPEAT_POWER)))
        strings = [self.parent.eval(self.repeat, state) for _ in range(count)]
        if self.nodups:
            strings = list(set(strings))
        return self.separator.join(strings)


class MetaChoice(object):
    """Grammar extension method which chooses an item out of a list randomly."""

    def __init__(self, choices, parent):
        self.parent = parent
        self.choices = choices
        self.choices = [x.strip() for x in self.choices.split(",")]

    def generate(self, state):
        return random.choice(self.choices)


class MetaRange(object):
    """Grammar extension method which generates a random value between a range of values |a| and |b|."""

    def __init__(self, a, b, parent):
        self.parent = parent
        self.base = None
        # Type identification
        if a is None or b is None:
            logging.error("%s: Malformed 'range' meta", parent.id())
            sys.exit(-1)
        if self._is_char(a) and self._is_char(b):
            self.a, self.b = ord(a), ord(b)
            self.fmt = "c"
            return
        if self._is_float(a) and self._is_float(b):
            type_a, type_b = float, float
            self.fmt = "f"
        else:
            type_a, type_b = int, int
            self.fmt = "i"
            if self._is_hex(a) and self._is_hex(b):
                self.base = 16
            else:
                self.base = 0
        # Type verification
        if type_a != type_b:
            logging.error("%s: Mismatch in 'range' meta %s/%s in %s",
                          parent.id(), type_a.__name__, type_b.__name__, parent.ident)
            sys.exit(-1)
        # Type construction
        try:
            if self.base:
                self.a, self.b = type_a(a, self.base), type_b(b, self.base)
            else:
                self.a, self.b = type_a(a), type_b(b)
        except ValueError:
            logging.error("%d: Conversion error %s in 'range' meta", parent.id(), type_b.__name__)
            sys.exit(-1)

    def _is_char(self, x):
        return len(x) == 1

    def _is_float(self, x):
        return "." in x

    def _is_hex(self, x):
        return "0x" in x

    def generate(self, state):
        if self.fmt == "c":
            return "%c" % random.randint(self.a, self.b)
        elif self.fmt == "f":
            return "%g" % random.uniform(self.a, self.b)
        elif self.fmt == "i":
            if self.base == 16:
                return "%x" % random.randint(self.a, self.b)
            return "%d" % random.randint(self.a, self.b)
