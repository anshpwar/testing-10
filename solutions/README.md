# Solutions

Reference resolutions for the CONFLICT scenarios in this repository. `VERIFIED` means the resolved tree passes all real test suites. Each scenario has `S###.md` (explanation) and, when verified, `S###.patch`.

| Scenario | Title | Status |
|---|---|---|
| [S031](S031.md) | Test record without execution times beside a concurrent edit | VERIFIED |
| [S039](S039.md) | Concurrent policy edits with mixed deployment and test records | VERIFIED |
| [S049](S049.md) | Second history with timestamp-less test records | VERIFIED |
| [S051](S051.md) | Second history with a hand-resolved revert | VERIFIED |
| [S052](S052.md) | Composite history across several policy and helper changes | VERIFIED |
| [S059](S059.md) | Commits rebased onto a new base while the other side keeps tuning | VERIFIED |
| [S060](S060.md) | Long history with several overlapping edits and mixed provenance | VERIFIED |
| [S066](S066.md) | Revert of a tuned rule collides with a later edit to the same tier | VERIFIED |
| [S086](S086.md) | Concurrent edits to a policy table beside a shared helper | VERIFIED |
