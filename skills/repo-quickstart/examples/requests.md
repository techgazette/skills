# Example: psf/requests

A real run, read on 2026-10-01 at commit `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`.

## Request

> How do I start using https://github.com/psf/requests? Give me a "use it today" box.

## Step 2: helper output

```bash
python3 scripts/readme_blocks.py https://raw.githubusercontent.com/psf/requests/611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60/README.md --format md
```

`````text
Source: https://raw.githubusercontent.com/psf/requests/611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60/README.md
Blocks: 4

### Block 1: lines 11-24, lang=python, under "Requests" [prompts]
```python
>>> import requests
>>> r = requests.get('https://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
'{"authenticated": true, ...'
>>> r.json()
{'authenticated': True, ...}
```

### Block 2: lines 34-36, lang=console, under "Installing Requests and Supported Versions" [install, shell, prompts]
```console
$ python -m pip install requests
```

### Block 3: lines 64-66, lang=shell, under "Cloning the repository" [shell]
```shell
git clone -c fetch.fsck.badTimezone=ignore https://github.com/psf/requests.git
```

### Block 4: lines 70-72, lang=shell, under "Cloning the repository" [shell]
```shell
git config --global fetch.fsck.badTimezone ignore
```
`````

## Steps 3 and 4: choosing

- Install: block 2 sits under "Installing Requests and Supported Versions" and is
  tagged `install`. It is the only install command in the README.
- First run: block 1 is the README's own example, a REPL session. It is complete on its
  own after the install. Blocks 3 and 4 are about cloning the repository, not using
  the library, so they are skipped.
- Requires: the README states "Requests officially supports Python 3.10+."

## Final output

`````markdown
### Use it today: Requests
Install (README lines 34-36):
```console
$ python -m pip install requests
```

First run (README lines 11-24, under "Requests"):
```python
>>> import requests
>>> r = requests.get('https://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
'{"authenticated": true, ...'
>>> r.json()
{'authenticated': True, ...}
```
This is an interactive session: type the lines after `>>>` into `python`; the other lines are the expected output.

Requires: "Requests officially supports Python 3.10+."
Source: https://github.com/psf/requests/blob/611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60/README.md, read on 2026-10-01
`````

What the skill does not do here: it does not rewrite the REPL session as a script, drop
the `$` prompt, or swap `httpbin.org` for another URL, even though any of those would be
convenient.
