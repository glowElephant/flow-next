# prospect: manual smoke (maintainer checklist)

Moved out of the shipped skill in 7.0; never loaded at runtime.

On a repo with git history and a CHANGELOG: `prospect DX` should produce a readable snapshot listing recently-modified files, open specs, CHANGELOG entries from the last few releases, memory hits if memory is initialised, and `scanned: none (...)` lines for any absent source. The snapshot must fit in roughly 30-50 lines of output and must not contain raw file bodies.
