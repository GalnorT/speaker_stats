# speaker_stats

This project is a data analysis and visualization project of the [Czech Debate dataset](https://statistiky.debatovani.cz).

This project was also submitted for the Data Processing in Python course at IES CUNI. If you are reviewing this project for the purposes of this course, please also read [this document](IES_PYTHON_README.md) after finishing this README.

## Dependency management

This project uses pipenv for dependency management.

Ideally, therefore, please install pipenv and run all python commands from the pipenv shell.

```bash
pip install pipenv
pipenv shell
```

That said, we the requirements.txt file should be up to date with the pipfile,
so `pip install -r requirements.txt` should also work.

To make sure the requirements.txt file is up to date, run:

```bash
pipenv requirements > requirements.txt
```

and then you can safely `pip install -r requirements.txt`

## Running the project

To run various backend scripts, you can typically run them with python (ideally in the pipenv shell) with the `--help` flag, for example:

```bash
python -m data.preprocessing.estimate_gender --help
```

since most scripts are written as mini CLI tools, the `help` flag tells you more about how to use/run each script.

Additionally, the frontend of the project can be run on a local development server with

```bash
npm run serve
```

_Note: The front end code is written in raw Typescript, so if you make changes to it , don't forget to compile it with:_

```bash
npm run build
```
