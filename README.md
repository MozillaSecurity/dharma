<p align="center">
  <img src="https://github.com/posidron/posidron.github.io/raw/master/static/images/dharma.png" alt="Logo" />
</p>

<p align="center">
Generation-based, context-free grammar fuzzer.
</p>

<p align="center">
<a href="https://travis-ci.org/MozillaSecurity/dharma"><img src="https://api.travis-ci.org/MozillaSecurity/dharma.svg?branch=master" alt="Build Status"></a>
<a href="https://www.irccloud.com/invite?channel=%23fuzzing&amp;hostname=irc.mozilla.org&amp;port=6697&amp;ssl=1"><img src="https://img.shields.io/badge/IRC-%23fuzzing-1e72ff.svg?style=flat" alt="IRC"></a>
</p>

<p align="center">
<img src="https://raw.githubusercontent.com/posidron/posidron.github.io/master/static/images/dharma.gif">
</p>

<h2>Table of Contents</h2>

- [Run](#Run)
  - [pip](#pip)
  - [pipenv](#pipenv)
  - [package](#package)
  - [Docker](#Docker)
- [Examples](#Examples)
- [Development](#Development)
- [Dharma Grammar Cheatsheet](#Dharma-Grammar-Cheatsheet)
- [API Documentation](#API-Documentation)
- [Dharma in the Public](#Dharma-in-the-Public)

## Run

All roads lead to Rome but Python 3.x is the prefered vehicle.

### pip

```bash
pip install dharma
dharma --help
```

### pipenv

```bash
pipenv install --dev
pipenv run dharma --help
```

### package

```bash
python -m dharma --help
```

### Docker

```bash
docker build -t dharma .
docker run --rm -it dharma -grammars dharma/grammars/canvas2d.dg
```

## Examples

Generate a single test-case and print it to `stdout`. Multiple grammars can be appended to the `-grammars` argument.

```bash
dharma -grammars dharma/grammars/canvas2d.dg
```

Generating multiple test-cases and save the result to disk.

```bash
dharma -grammars dharma/grammars/canvas2d.dg -storage . -count 5
```

Generate test-cases and serve them in a template via WebSocket.
Launch `dharma/grammars/var/index.html` in the browser after Dharma launched.

```bash
dharma -grammars dharma/grammars/canvas2d.dg -server -template grammars/var/templates/html5/default.html
```

Benchmark the generator.

```bash
time dharma -grammars dharma/grammars/canvas2d.dg -count 10000 > /dev/null
```

## Development

### PyLint

In case you run PyLint 1.9.2 and Python 3.7 you need to upgrade PyLint.

```bash
pip3 install pylint astroid --pre -U
```

## Dharma Grammar Cheatsheet

### Comments

```
%%% comment
```

### Controls

```
%const% name := value
```

### Sections

```
%section% := value
%section% := variable
%section% := variance
```

### Extension Methods

Refer to `extensions.py` in `dharma/core/` and to the `xref_registry` in the `DharmaMachine` class to add further extensions.

```
%range%(0-9)
%range%(0.0-9.0)
%range%(a-z)
%range%(!-~)
%range%(0x100-0x200)

%repeat%(+variable+)
%repeat%(+variable+, ", ")

%uri%(path)
%uri%(lookup_key)

%block%(path)

%choice%(foo, "bar", 1)
```

### Assigning Values

```
digit :=
    %range%(0-9)

sign :=
    +
    -

value :=
    +sign+%repeat%(+digit+)
```

### Using Values

```
+value+
```

### Assigning Variables

```
variable :=
    @variable@ = new Foo();
```

### Using Variables

```
value :=
    !variable!.bar();
```

### Referencing values from `common.dg`

```
value :=
    attribute=+common:number+
```

### Calling JavaScript library methods

```
foo :=
    Random.pick([0,1]);
```

## API Documentation

- https://mozillasecurity.github.io/dharma

## Dharma in the Public

Dharma mentionings in the news.

- https://www.zerodayinitiative.com/blog/2019/1/31/implementing-fuzz-logics-with-dharma
- http://blog.ret2.io/2018/06/13/pwn2own-2018-vulnerability-discovery/
- https://blog.mozilla.org/security/2015/06/29/dharma/
- https://www.redpacketsecurity.com/dharma-generation-based-context-free-grammar-fuzzing-tool/
