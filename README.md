Dharma
======

<h3>Requirements</h3>
---

None


<h3>Examples</h3>
---


Generate a single test case.

```
% ./core/dharma.py -grammars grammar/webcrypto.dg
```

Generate a single test case with multiple grammars.

```
% ./core/dharma.py -grammars grammar/canvas2d.dg grammar/mediarecorder.dg
```

Generating test cases as files.

```
% ./core/dharma.py -grammars grammar/webcrypto.dg -storage . -count 5
```

Generate test cases, send each over WebSocket to Firefox, observe the process for crashes and bucket them.

```
% ./core/dharma.py -server -grammars grammar/canvas2d.dg -template var/templates/html5/default.html
% ./framboise.py -setup inbound64-release -debug -worker 4 -testcase ~/dev/projects/fuzzers/dharma/var/index.html
```


Benchmark the generator.

```
% time ./core/dharma.py -grammars grammar/webcrypto.dg -count 10000 > /dev/null
```


<h3>Grammar Cheetsheet</h3>

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
