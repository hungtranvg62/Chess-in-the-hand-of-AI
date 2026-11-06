# Chess in the Hand of AI

A chess app with four AI levels (Easy, Medium, Hard, Master), built only with classical search. No machine learning.
Course project for IT3160E – Introduction to Artificial Intelligence (HUST).

## Team

| Member | Student ID | Role |
|---|---|---|
| Trần Vương Hưng (leader) | 20225496 | Game logic + Level 4 (Master) |
| Trần Ngọc Tuấn | 20235568 | Level 2 (Medium) |
| LEBON-BARRÉ Dominique, Hubert Harry | 20260088S | Level 3 (Hard) |
| PLICHON Matthias Eskandar Jacques | 20260096S | Level 1 (Easy) |
| BEN SIMON Joseph Yves Yanis | 20260090S | App & integration |

## Read these first

1. **README.md** (this file): what the project is and how to set it up.
2. **[CONTRIBUTING.md](CONTRIBUTING.md)**: the rules: branches, pull requests, who owns which files.
3. **[docs/plan.md](docs/plan.md)**: the full plan: the four levels, the algorithms, the experiments.
4. **[.github/CODEOWNERS](.github/CODEOWNERS)**: who reviews changes to each file.

## Set up

We use a **virtual environment**: a private Python folder for this project. Everyone gets the same package versions, and nothing clashes with other projects on your computer. The `.venv/` folder is in `.gitignore`, so it is never committed.

```
python -m venv .venv
```

Activate it every time you open a new terminal:

```
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
```

Then install the packages (once, and again when `requirements.txt` changes):

```
pip install -r requirements.txt
```

## Run the tests

```
pytest
```

Run this before you push. GitHub also runs the same tests automatically on every push to `main` and on every pull request (see [.github/workflows/ci.yml](.github/workflows/ci.yml)). A green check means all tests passed; a red cross means a test failed. Click it to see which one.

## Project structure

| Folder | What goes in it |
|---|---|
| `game/` | Game logic on python-chess and the shared `search()` function |
| `engine/` | One file per AI level; `evaluation/` for scoring functions |
| `ui/` | Pygame app |
| `benchmark/` | Test runner: games and puzzles without a screen |
| `data/` | Input files: openings, WAC puzzles |
| `results/` | Output files: CSV, PGN, charts |
| `tests/` | Automatic tests |
| `docs/` | Project plan, proposal, report, final presentation |
| `.github/` | `CODEOWNERS` (who reviews what) and `workflows/ci.yml` (automatic tests) |

See [CONTRIBUTING.md](CONTRIBUTING.md) for the rules and [docs/plan.md](docs/plan.md) for the full plan.
