# speaker_stats

## Dependency management

This project uses pipenv for dependency management.

Ideally, therefore, make sure pipenv is installed and run all python commands from the pipenv shell.

```bash
pip install pipenv
pipenv shell
```

That said, we try to keep the requirements.txt file up to date with the pipfile,
so `pip install -r requirements.txt` should also work.

To make sure the requirements.txt file is up to date, run:

```bash
pipenv requirements > requirements.txt
```
and then you can safely `pip install -r requirements.txt`
