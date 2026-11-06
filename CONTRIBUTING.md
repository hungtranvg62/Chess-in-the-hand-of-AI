# How we work

## Workflow (GitHub flow)

1. `main` must always work. Never push to `main` directly.
2. One branch per task, made from `main`, named as in [Branch names](#branch-names) below.
3. Run `pytest` on your computer, then push your branch and open a pull request.
4. GitHub runs the tests automatically (CI). Wait for the green check; if you see a red cross, click it, fix the failing test and push again.
5. One teammate reviews it. Merge only when the tests are green **and** the review is approved, then delete the branch.
6. Deliverables are GitHub Releases on `main`: `v0.1-proposal`, `v1.0-final`.

## Branch names

Format: `type/short-description`, in lowercase, with words joined by `-`.

| Type | Use it for | Example |
|---|---|---|
| `feature/` | New code: an engine, a game part, a UI screen | `feature/level3-alphabeta` |
| `fix/` | A normal bug fix | `fix/minimax-mate-score` |
| `hotfix/` | An urgent fix when `main` is broken | `hotfix/ci-failing-on-main` |
| `test/` | Adding or changing tests only | `test/greedy-mate-in-one` |
| `experiment/` | Benchmark scripts and experiment runs | `experiment/tournament-round-robin` |
| `docs/` | Plan, report, slides, README | `docs/proposal-slides` |
| `refactor/` | Cleaning code without changing what it does | `refactor/move-ordering` |
| `chore/` | Setup and config: requirements, CI, `.gitignore` | `chore/add-pytest-to-ci` |

- One task per branch. If you start something different, make a new branch.
- Delete the branch after it is merged.

## Project structure

- Work in **your own files** (see the owner in each file and in `.github/CODEOWNERS`).
- Need to change someone else's file? Ask them first, or let them review your pull request.
- Do not add new top-level folders without asking the leader.
- Inputs go in `data/`, outputs in `results/`.

## Code owners

[`.github/CODEOWNERS`](.github/CODEOWNERS) lists who is responsible for each file. When your pull request changes a file, GitHub automatically asks its owner to review it. The leader is on every line, so approval from either the owner or the leader is enough.

How to use it:
- **Before you edit a file**, check its owner in `CODEOWNERS` (or the first line of the file). If it isn't yours, tell the owner first.
- **When you open a pull request**, the right reviewers are added for you. You don't need to pick them.
- **When you are asked to review**, check the code within a day: approve it, or leave comments.
- **To change who owns a file**, edit `CODEOWNERS` in a pull request, and the leader approves it.

## Code rules

- Every engine uses the shared `search()` function from `game/interface.py`.
- Never change the board passed to `search()`; work on `board.copy()`.
- Add a test in `tests/` for the code you write.
- Your engine is tested automatically as soon as it defines `search()` (`tests/test_engine_contract.py`), and your evaluation as soon as it defines `evaluate(board)` (`tests/test_evaluation.py`). Make these pass.
- Keep CI fast: no long tournaments or UI windows in `tests/`; those go in `benchmark/`.
- Do not change `.github/workflows/` without asking the leader.
- No machine learning: classical search and hand-written evaluation only.
