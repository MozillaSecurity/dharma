![Logo](https://github.com/posidron/posidron.github.io/raw/master/static/images/dharma.png)


[![Build Status](https://api.travis-ci.org/MozillaSecurity/dharma.svg)](https://travis-ci.org/MozillaSecurity/dharma)



## Requirements
None


## Examples
Generate a single test-case.

```bash
% ./dharma.py -grammars grammars/webcrypto.dg
```

Generate a single test case with multiple grammars.

```bash
% ./dharma.py -grammars grammars/canvas2d.dg grammars/mediarecorder.dg
```

Generating test-cases as files.

```bash
% ./dharma.py -grammars grammars/webcrypto.dg -storage . -count 5
```

Generate test-cases, send each over WebSocket to Firefox, observe the process for crashes and bucket them.

```bash
% ./dharma.py -server -grammars grammars/canvas2d.dg -template grammars/var/templates/html5/default.html
% ./framboise.py -setup inbound64-release -debug -worker 4 -testcase ~/dev/projects/fuzzers/dharma/grammars/var/index.html
```

Benchmark the generator.

```bash
% time ./dharma.py -grammars grammars/webcrypto.dg -count 10000 > /dev/null
```

## Screenshots

![Dharma Demo](https://github.com/posidron/posidron.github.io/blob/master/static/images/dharma/dharma_demo.png "")
![Dharma Menu](https://github.com/posidron/posidron.github.io/blob/master/static/images/dharma/dharma_menu.png "")



## Grammar Cheatsheet

### comment
```
%%% comment
```

### controls
```
%const% name := value
```

### sections
```
%section% := value
%section% := variable
%section% := variance
```

### extension methods
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

### assigning values
```
digit :=
    %range%(0-9)

sign :=
    +
    -

value :=
    +sign+%repeat%(+digit+)
```

### using values
```
+value+
```

### assigning variables
```
variable :=
    @variable@ = new Foo();
```

### using variables
```
value :=
    !variable!.bar();
```

### referencing values from common.dg
```
value :=
    attribute=+common:number+
```

### calling javascript library functions
```
foo :=
    Random.pick([0,1]);
```
