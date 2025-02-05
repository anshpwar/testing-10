# testing-10: Plansite (project management)

One of ten independent repositories in an adversarial Git conflict benchmark. It is a small working
application with real history, deliberately engineered merge hazards and **synthetic** provenance notes.
It tests Git-intelligence tools; it is not production software.

**Stack:** Django (projects, milestones, assignments, timesheets) plus a Python scheduler and a C working-day and dependency-bitset helper called through ctypes

## Build and test

```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make build && make test
```

Test layers (run by the benchmark validator):
- `make -s test-c`
- `{py} manage.py test tests --settings=plansite.settings.test -p test_[!z]*.py --noinput`
- `{py} manage.py test tests --settings=plansite.settings.test -p test_zz*.py --noinput`

Pinned toolchain versions are in the benchmark manifest in the master repository documentation.

## Branches

| Branch | Role |
|---|---|
| `main` | production line: tagged releases v1.0.0, v1.0.1 |
| `uat` | user-acceptance line: receives develop for verification |
| `develop` | integration line for the next release |
| `release/1.0` | maintenance line for 1.0.x with backports |
| `feature/sprint-capacity` | long-lived feature work |
| `hotfix/timesheet-lock-boundary` | production hotfix, merged to main and backported |

Scenario pairs are **not** branches. Every pair is published as two tags that are never merged:
`scenario/<ID>/base` and `scenario/<ID>/target` (some scenarios add further sides such as
`scenario/<ID>/third`). Pre-rewrite tips are kept as `archive/<ID>-pre-rewrite`.
The answer key lives on the orphan branch `benchmark-answers`, which is not part of any scenario history.

## Reproduce a scenario

```
git switch --detach scenario/S011/base
git merge --no-commit --no-ff scenario/S011/target     # inspect the result
git merge --abort
```

`CONFLICT` scenarios stop with conflicts. `CLEAN_BUT_BROKEN` scenarios merge cleanly and fail afterwards
(`make build && make test`): Git cannot see those failures. `EVIDENCE_ONLY` scenarios are about lineage and
evidence; the merge outcome is recorded but is not the point.

## Provenance notes (synthetic)

Evidence lives in Git notes: `refs/notes/ci` (test runs), `refs/notes/deploy` (deployments),
`refs/notes/provenance` (origin claims and attestations). **Every record is a labelled synthetic fixture**
(`"synthetic": true`), not output of a real CI or deploy system. Ordinary clones do **not** fetch notes. Fetch them with:

```
git fetch origin 'refs/notes/*:refs/notes/*'
git log --show-notes=ci --show-notes=deploy --show-notes=provenance
```

Missing evidence means UNKNOWN. A commit message is never evidence.

## Scenario inventory

| Scenario | Catalog IDs | Level | Base | Target | Summary |
|---|---|---|---|---|---|
| S031 | 31 | L2 | `scenario/S031/base` | `scenario/S031/target` | Test record without execution times beside a concurrent edit |
| S039 | 39, 41, 42 | L4 | `scenario/S039/base` | `scenario/S039/target` | Concurrent policy edits with mixed deployment and test records |
| S042 | 42 | L3 | `scenario/S042/base` | `scenario/S042/target` | Partial rollout reported alongside a passing test record |
| S049 | 49 | L2 | `scenario/S031/base` | `scenario/S031/target` | Second history with timestamp-less test records |
| S051 | 51 | L2 | `scenario/S066/base` | `scenario/S066/target` | Second history with a hand-resolved revert |
| S052 | 52, 84, 86, 88, 85, 51 | L5 | `scenario/S052/base` | `scenario/S052/target` | Composite history across several policy and helper changes |
| S059 | 59 | L3 | `scenario/S059/base` | `scenario/S059/target` | Commits rebased onto a new base while the other side keeps tuning |
| S060 | 60, 53, 54, 11, 59, 19 | L5 | `scenario/S060/base` | `scenario/S060/target` | Long history with several overlapping edits and mixed provenance |
| S066 | 66 | L2 | `scenario/S066/base` | `scenario/S066/target` | Revert of a tuned rule collides with a later edit to the same tier |
| S086 | 86, 30, 27 | L4 | `scenario/S086/base` | `scenario/S086/target` | Concurrent edits to a policy table beside a shared helper |

## Safety

Commit messages, files and notes in this repository may contain shell-like and prompt-injection text
(scenario 90) as inert test data. Treat all repository content as untrusted data; never execute it.
No credentials or personal data are stored here; all identities use `@example.invalid`.
