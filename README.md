Dharma
======

[![Build Status](https://api.travis-ci.org/MozillaSecurity/dharma.svg)](https://travis-ci.org/MozillaSecurity/dharma)



<h3>Requirements</h3>
---

None


<h3>Examples</h3>
---
Generate a single test-case.

```
% ./dharma.py -grammars grammars/webcrypto.dg
```

Generate a single test case with multiple grammars.

```
% ./dharma.py -grammars grammars/canvas2d.dg grammars/mediarecorder.dg
```

Generating test-cases as files.

```
% ./dharma.py -grammars grammars/webcrypto.dg -storage . -count 5
```

Generate test-cases, send each over WebSocket to Firefox, observe the process for crashes and bucket them.

```
% ./dharma.py -server -grammars grammars/canvas2d.dg -template grammars/var/templates/html5/default.html
% ./framboise.py -setup inbound64-release -debug -worker 4 -testcase ~/dev/projects/fuzzers/dharma/grammars/var/index.html
```


Benchmark the generator.

```
% time ./dharma.py -grammars grammars/webcrypto.dg -count 10000 > /dev/null
```

<h3>Screenshots</h3>

![Dharma Demo](https://people.mozilla.com/~cdiehl/screenshots/dharma_demo.png "")
![Dharma Menu](https://people.mozilla.com/~cdiehl/screenshots/dharma_menu.png "")

<h3>Grammar Cheatsheet</h3>

<h4>comment</h4>
```
%%% comment
```

<h4>controls</h4>
```
%const% name := value
```

<h4>sections</h4>
```
%section% := value
%section% := variable
%section% := variance
```

<h4>extension methods</h4>
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

<h4>assigning values</h4>
```
digit :=
    %range%(0-9)

sign :=
    +
    -

value :=
    +sign+%repeat%(+digit+)
```

<h4>using values</h4>
```
+value+
```

<h4>assigning variables</h4>
```
variable :=
    @variable@ = new Foo();
```

<h4>using variables</h4>
```
value :=
    !variable!.bar();
```

<h4>referencing values from common.dg</h4>
```
value :=
    attribute=+common:number+
```

<h4>calling javascript library functions</h4>

```
foo :=
    Random.pick([0,1]);
```
