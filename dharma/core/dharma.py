# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import re
import sys
import logging
from string import Template
from itertools import chain
from collections import OrderedDict

if sys.version_info[0] == 2:
    from extensions import *  # pylint: disable=E0401,W0401
else:
    from dharma.core.extensions import *  # pylint: disable=W0401,W0614


class GenState:
    def __init__(self):
        self.leaf_mode = False
        self.leaf_trigger = 0


class String:
    """Generator class basic strings which need no further evaluation."""

    def __init__(self, value, parent):
        self.parent = parent
        self.value = value

    def generate(self, state):
        return self.value


class ValueXRef:
    """Generator class for +value+ cross references."""

    def __init__(self, value, parent):
        self.value = ("%s:%s" % (parent.namespace, value)) if ":" not in value else value
        self.parent = parent
        self.parent.value_xref[self.value] = None

    def generate(self, state):
        try:
            ref = self.parent.value_xref[self.value]
        except KeyError:
            logging.error("Value xref inconsistency in %s looking for %s", self.parent.ident, self.value)
            sys.exit(-1)
        return ref.generate(state)


class VariableXRef:
    """Generator class for !variable! cross references."""

    def __init__(self, value, parent):
        self.value = ("%s:%s" % (parent.namespace, value)) if ":" not in value else value
        self.parent = parent
        self.parent.variable_xref[self.value] = None

    def generate(self, state):
        try:
            ref = self.parent.variable_xref[self.value]
        except KeyError:
            logging.error("Variable xref inconsistency in %s looking for %s", self.parent.ident, self.value)
            sys.exit(-1)
        return ref.generate(state)


class ElementXRef:
    """Generator class for @value@ cross references."""

    def __init__(self, value, parent):
        self.value = ("%s:%s" % (parent.namespace, value)) if ":" not in value else value
        self.parent = parent
        self.parent.element_xref[self.value] = None

    def generate(self, state):
        try:
            ref = self.parent.element_xref[self.value]
        except KeyError:
            logging.error("Element xref inconsistency in %s looking for %s", self.parent.ident, self.value)
            sys.exit(-1)
        return ref.generate(state)


class DharmaObject(list):
    """Base object of which Dharma section classes inherit from."""

    def __init__(self, ident, machine):
        list.__init__(self)
        self.ident = "%s:%s" % (machine.namespace, ident)
        self.machine = machine
        self.value_xref = {}
        self.variable_xref = {}
        self.element_xref = {}
        self.namespace = machine.namespace
        self.lineno = machine.lineno

    def id(self):  # pylint: disable=invalid-name
        return "Line %d [%s]" % (self.lineno, self.namespace)

    def __hash__(self):
        return hash(self.ident)

    @staticmethod
    def eval(tokens, state):
        return "".join(token.generate(state) for token in tokens)


class DharmaValue(DharmaObject):
    """Dharma class which manages the |value| section of a grammar."""

    def __init__(self, ident, machine):
        DharmaObject.__init__(self, ident, machine)
        self.leaf = []
        self.leaf_path = []
        self.path_idents = set()
        self.minimized = None

    def n_xrefs(self, value):
        repeats, n = False, 0
        for t in value:
            if isinstance(t, ValueXRef):
                n += 1
                if t.value not in self.path_idents:
                    return False, None, None
            elif isinstance(t, MetaRepeat):
                repeats = True
                n += self.n_xrefs(t.repeat)[2]
        return True, repeats, max(1, min(n, 8))  # constrain within [1, 8]

    def append(self, value):
        list.append(self, value)
        for t in value:
            if isinstance(t, (MetaRepeat, ValueXRef)):
                return
        self.leaf.append(value)

    def generate(self, state):  # pylint: disable=too-many-branches
        if not state.leaf_mode:
            state.leaf_trigger += 1
            if state.leaf_trigger > DharmaConst.LEAF_TRIGGER:
                state.leaf_mode = True
        if not self:
            return ""
        if state.leaf_mode and self.leaf:
            value = random.choice(self.leaf)
        elif state.leaf_mode:  # favour non-repeating
            if self.minimized is None:
                n_refs_groups = {}
                have_non_repeats = False
                for v in self:
                    is_leaf_path, repeats, n_xrefs = self.n_xrefs(v)
                    if not is_leaf_path:
                        continue
                    if not repeats:
                        if not have_non_repeats:
                            n_refs_groups = {}
                            have_non_repeats = True
                    if not repeats or not have_non_repeats:
                        n_refs_groups.setdefault(n_xrefs, []).append(v)
                for _, v in sorted(n_refs_groups.items()):
                    self.minimized = v
                    break
                if not self.minimized:
                    logging.error("No path to leaf in force-leaf mode in value %s", self.ident)
                    sys.exit(-1)
            value = random.choice(self.minimized)
        else:
            value = random.choice(self)
        return self.eval(value, state)


class DharmaVariable(DharmaObject):
    """Dharma class which manages the |variable| section of a grammar."""

    def __init__(self, ident, machine):
        DharmaObject.__init__(self, ident, machine)
        self.var = ident
        self.count = 0
        self.default = ""

    def clear(self):
        self.count = 0
        self.default = ""

    def generate(self, state):
        """Return a random variable if any, otherwise create a new default variable."""
        if self.count >= random.randint(DharmaConst.VARIABLE_MIN, DharmaConst.VARIABLE_MAX):
            return "%s%d" % (self.var, random.randint(1, self.count))
        var = random.choice(self)
        prefix = self.eval(var[0], state)
        suffix = self.eval(var[1], state)
        self.count += 1
        element_name = "%s%d" % (self.var, self.count)
        self.default += "%s%s%s\n" % (prefix, element_name, suffix)
        return element_name


class DharmaVariance(DharmaObject):
    """Dharma class which manages the |variance| section of a grammar."""

    def generate(self, state):
        return self.eval(random.choice(self), state)


class DharmaMachine:  # pylint: disable=too-many-instance-attributes
    def __init__(self, prefix="", suffix="", template=""):
        self.section = None
        self.level = "top"
        self.namespace = ""
        self.lineno = 0
        self.current_obj = None
        self.value = {}
        self.variable = OrderedDict()
        self.variance = {}
        self.prefix = prefix
        self.suffix = suffix
        self.template = template
        self.consts_set = {}
        self.default_grammars = ["../grammars/common.dg"]
        self.grammar_level_registry = r"""^(
            (?P<comment>%%%).*|
            %const%\s*(?P<const>[A-Z_]+)\s*:=\s*(?P<value>.*)|
            %section%\s*:=\s*(?P<section>value|variable|variance)|
            (?P<ident>[a-zA-Z0-9_]+)\s*:=\s*|
            (?P<empty>\s*)|
            (\t|[ ]+)(?P<assign>.*)
        )$"""
        self.xref_registry = r"""(
            (?P<type>\+|!|@)(?P<xref>[a-zA-Z0-9:_]+)(?P=type)|
            %uri%\(\s*(?P<uri>.*?)\s*\)|
            %repeat%\(\s*(?P<repeat>.+?)\s*(,\s*"(?P<separator>.*?)")?\s*(,\s*(?P<nodups>nodups))?\s*\)|
            %block%\(\s*(?P<block>.*?)\s*\)|
            %range%\((?P<start>.+?)-(?P<end>.+?)\)|
            %choice%\(\s*(?P<choices>.+?)\s*\)
        )"""

    def process_settings(self, settings):
        """A lazy way of feeding Dharma with configuration settings."""
        logging.debug("Using configuration from: %s", settings.name)
        exec(compile(settings.read(), settings.name, 'exec'), globals(), locals())  # pylint: disable=exec-used

    def set_namespace(self, name):
        self.namespace = name
        self.lineno = 0

    def id(self):  # pylint: disable=invalid-name
        return "Line %d [%s]" % (self.lineno, self.namespace)

    def parse_line(self, line):
        self.lineno += 1
        m = re.match(self.grammar_level_registry, line, re.VERBOSE | re.IGNORECASE)
        if m is None:
            pass
        elif m.group("comment"):
            return
        elif m.group("const"):
            self.handle_const(*m.group("const", "value"))
            return
        elif m.group("section"):
            self.handle_empty_line()
            self.section = m.group("section").lower()
            return
        elif m.group("empty") is not None:
            self.handle_empty_line()
            return
        elif self.section is None:
            logging.error("%s: Non-empty line in void section", self.id())
            sys.exit(-1)
        elif self.level == "top":
            self.handle_top_level(m.group("ident"))
            return
        elif self.level == "assign":
            self.handle_assign_level(m.group("assign"))
            return
        logging.error("%s: Unhandled line", self.id())
        sys.exit(-1)

    def handle_const(self, const, value):
        if not hasattr(DharmaConst, const):
            logging.error("%s: Trying to set non-existent constant", self.id())
            sys.exit(-1)
        orig = self.consts_set.get(const)
        if value[0] == '"':
            assert value[-1] == '"'
            value = value[1:-1]
            setattr(DharmaConst, const, value)
        else:
            setattr(DharmaConst, const, float(value) if "." in value else int(value))
        if orig is not None and getattr(DharmaConst, const) != orig:
            logging.warning("%s: Overriding constant %s defined by previous grammar", self.id(), const)
        self.consts_set[const] = getattr(DharmaConst, const)

    def handle_empty_line(self):
        if self.current_obj is None:
            pass
        elif not self.current_obj:
            logging.error("%s: Empty assignment", self.id())
            sys.exit(-1)
        else:
            self.add_section_object()
        self.level = "top"
        self.current_obj = None

    def handle_top_level(self, ident):
        if ident is None:
            logging.error("%s: Top level syntax error", self.id())
            sys.exit(-1)
        try:
            assign_type = {"value": DharmaValue,
                           "variable": DharmaVariable,
                           "variance": DharmaVariance}[self.section]
        except KeyError:
            logging.error("%s: Invalid state for top-level", self.id())
            sys.exit(-1)
        self.current_obj = assign_type(ident, self)
        self.level = "assign"

    def handle_assign_level(self, assign):
        if assign is None:
            logging.error("%s: Assign level syntax error", self.id())
            sys.exit(-1)
        try:
            parse_assign = {"value": self.parse_assign_value,
                            "variable": self.parse_assign_variable,
                            "variance": self.parse_assign_variance}[self.section]
        except KeyError:
            logging.error("%s: Invalid state for assignment", self.id())
            sys.exit(-1)
        parse_assign(self.parse_xrefs(assign))

    def parse_xrefs(self, token):
        """Search token for +value+ and !variable! style references. Be careful to not xref a new variable.
        """
        out, end = [], 0
        token = token.replace("\\n", "\n")
        for m in re.finditer(self.xref_registry, token, re.VERBOSE | re.DOTALL):
            if m.start(0) > end:
                out.append(String(token[end:m.start(0)], self.current_obj))
            end = m.end(0)
            if m.group("type"):
                xref_type = {"+": ValueXRef,
                             "!": VariableXRef,
                             "@": ElementXRef}[m.group("type")]
                out.append(xref_type(m.group("xref"), self.current_obj))
            elif m.group("uri") is not None:
                path = m.group("uri")
                out.append(MetaURI(path, self.current_obj))
            elif m.group("repeat") is not None:
                repeat, separator, nodups = m.group("repeat", "separator", "nodups")
                if separator is None:
                    separator = ""
                if nodups is None:
                    nodups = ""
                out.append(MetaRepeat(self.parse_xrefs(repeat), separator, nodups, self.current_obj))
            elif m.group("block") is not None:
                path = m.group("block")
                out.append(MetaBlock(path, self.current_obj))
            elif m.group("choices") is not None:
                choices = m.group("choices")
                out.append(MetaChoice(choices, self.current_obj))
            else:
                startval, endval = m.group("start", "end")
                out.append(MetaRange(startval, endval, self.current_obj))
        if end < len(token):
            out.append(String(token[end:], self.current_obj))
        return out

    def parse_assign_value(self, tokens):
        if not isinstance(self.current_obj, DharmaValue):
            logging.error("%s: Normal value found in non-normal assignment", self.id())
            sys.exit(-1)
        self.current_obj.append(tokens)

    def parse_assign_variable(self, tokens):
        """
        Example:
            tokens
                dharma.String:      'let ',
                dharma.ElementXRef: 'GrammarNS:<VarName>',
                dharma.String:      '= new ',
                dharma.ValueXRef:   'GrammarNS:<ValueName>'
        """
        for i, token in enumerate(tokens):
            if isinstance(token, ElementXRef):
                variable = token.value
                break
        else:
            logging.error("%s: Variable assignment syntax error", self.id())
            sys.exit(-1)
        if variable != self.current_obj.ident:
            logging.error("%s: Variable name mismatch", self.id())
            sys.exit(-1)
        if not isinstance(self.current_obj, DharmaVariable):
            logging.error("%s: Inconsistent object for variable assignment", self.id())
            sys.exit(-1)
        prefix, suffix = tokens[:i], tokens[i + 1:]  # pylint: disable=undefined-loop-variable
        self.current_obj.append((prefix, suffix))

    def parse_assign_variance(self, tokens):
        if not isinstance(self.current_obj, DharmaVariance):
            logging.error("%s: Inconsistent object for variance assignment", self.id())
            sys.exit(-1)
        self.current_obj.append(tokens)

    def add_section_object(self):
        try:
            section_dict = getattr(self, self.section)
        except AttributeError:
            logging.error("%s: Inconsistent section value, fatal", self.id())
            sys.exit(-1)
        if self.current_obj.ident in section_dict:
            logging.error("%s(%s): '%s' gets redefined", self.id(), self.section, self.current_obj.ident)
            sys.exit(-1)
        section_dict[self.current_obj.ident] = self.current_obj

    def resolve_xref(self):
        for obj in chain(self.value.values(),
                         self.variable.values(),
                         self.variance.values()):
            try:
                msg = "%s: Undefined value reference from %s to %s"
                obj.value_xref.update((x, self.value[x]) for x in obj.value_xref)
                msg = "%s: Undefined variable reference from %s to %s"
                obj.variable_xref.update((x, self.variable[x]) for x in obj.variable_xref)
                msg = "%s: Element reference without a default variable from %s to %s"
                obj.element_xref.update((x, self.variable[x]) for x in obj.element_xref)
            except KeyError as error:
                logging.error(msg, self.id(), obj.ident, error.args[0])
                sys.exit(-1)

    def calculate_leaf_paths(self):
        """Build map of reverse xrefs then traverse backwards marking path to leaf for all leaves.
        """
        reverse_xref = {}
        leaves = set()
        for v in self.value.values():
            if v.leaf:
                leaves.add(v)
            for xref in v.value_xref:
                reverse_xref.setdefault(xref, []).append(v.ident)
        for leaf in leaves:
            self.calculate_leaf_path(leaf, reverse_xref)

    def calculate_leaf_path(self, leaf, reverse_xref):
        if leaf.ident not in reverse_xref:
            return
        for name in reverse_xref[leaf.ident]:
            xref = self.value[name]
            xref.leaf_path.append((leaf.ident, leaf.ident, 0))
            xref.path_idents.add(leaf.ident)
            self.propagate_leaf(leaf.ident, xref, {xref}, 1, reverse_xref)

    def propagate_leaf(self, leaf, obj, node_seen, depth, reverse_xref):
        if obj.ident not in reverse_xref:
            return
        for name in reverse_xref[obj.ident]:
            xref = self.value[name]
            xref.leaf_path.append((leaf, obj.ident, depth))
            xref.path_idents.add(obj.ident)
            if xref in node_seen:
                continue
            node_seen.add(xref)
            self.propagate_leaf(leaf, xref, node_seen, depth + 1, reverse_xref)

    def generate_content(self):
        """Generates a test case as a string."""
        # Setup pre-conditions.
        if not self.variance:
            logging.error("%s: No variance information %s", self.id(), self.variance)
            sys.exit(-1)

        for var in self.variable.values():
            var.clear()

        # Handle variances
        variances = []
        for _ in range(random.randint(DharmaConst.VARIANCE_MIN, DharmaConst.VARIANCE_MAX)):
            var = random.choice(list(self.variance.values()))
            variances.append(DharmaConst.VARIANCE_TEMPLATE % var.generate(GenState()))
            variances.append("\n")

        # Handle variables
        variables = []
        for var in self.variable.values():
            if var.default:
                variables.append(DharmaConst.VARIANCE_TEMPLATE % var.default)
                variables.append("\n")

        # Build content
        content = "".join(chain([self.prefix], variables, variances, [self.suffix]))
        if self.template:
            return Template(self.template).safe_substitute(testcase_content=content)
        return content

    def generate_testcases(self, path, filetype, count):
        """Writes out generated test cases to the provided path."""
        path = path.rstrip("/")
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as error:
            logging.error("Unable to create folder for test cases: %s", error)
            sys.exit(-1)
        for n in range(count):
            filename = os.path.join(path, "%d.%s" % (n + 1, filetype))
            try:
                with open(filename, "w") as fo:
                    fo.write(self.generate_content())
            except IOError:
                logging.error("Failed in writing test case %s", filename)
                sys.exit(-1)

    def process_grammars(self, grammars):
        """Process provided grammars by parsing them into Python objects."""
        for path in self.default_grammars:
            grammars.insert(0, open(os.path.relpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                 os.path.normcase(path)))))
        for fo in grammars:
            logging.debug("Processing grammar content of %s", fo.name)
            self.set_namespace(os.path.splitext(os.path.basename(fo.name))[0])
            for line in fo:
                self.parse_line(line)
            self.handle_empty_line()
        self.resolve_xref()
        self.calculate_leaf_paths()
