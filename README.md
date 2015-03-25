Dharma
======

#### Requirements
---

None


#### Examples
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


#### Grammar Cheetsheet
---

##### comment
```
%%% comment
```

##### controls
```
%const% name := value
```

##### sections
```
%section% := value
%section% := variable
%section% := variance
```

##### extension methods
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

##### assigning values
```
digit :=
    %range%(0-9)

sign :=
    +
    -

value :=
    +sign+%repeat%(+digit+)
```

##### using values
```
+value+
```

##### assigning variables
```
variable :=
    @variable@ = new Foo();
```

##### using variables
```
value :=
    !variable!.bar();
```

##### referencing values from common.dg
```
value :=
    attribute=+common:number+
```

##### calling javascript library functions

```
foo :=
    Random.pick([0,1]);
```
