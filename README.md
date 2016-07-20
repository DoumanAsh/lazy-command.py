command.py
==============

The Rust-like wrapper over `subprocess.PIPE`

The idea behind this wrapper is to customize command by means of method chaining.

Examples
-------

#### Collect all output of command
```python
from command import Command

output = Command('make').arg(target).arg('-n').all_pipe().output()

print("return code={} | stdout={} | stderr={}".format(output.status,
                                                      output.stdout,
                                                      output.stderr))
```

#### Just check status code
```python
from command import Command

return_code = (Command('grep').arg('something')
                              .arg('-r')
                              .arg('.')
                              .stdout_null()
                              .status())

print("grep returns {}".format(return_code))
```

#### Set command in one go

Under hood `Command` uses `shlex.split` so you can set the whole command in one go.

```python
from command import Command

return_code = Command('grep something -r .').stdout_null().status()

print("grep returns {}".format(return_code))
```
