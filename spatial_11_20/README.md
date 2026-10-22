# Spatial 11–20 game

This is an optional, standalone oTree app. It is not imported by the repository's
`settings.py` or added to the existing session sequence; removing this directory
does not affect the current experiment.

The app runs 10 rounds with two participants per group. Each round independently
randomizes the pairings and assigns one player the `opponent number - 1` target
and the other the `opponent number - 10` target. The number board is 10 × 10 and
covers 1–100, following the clarified board specification. The selectable bonus
amount is set in `C.BONUS` in `__init__.py`.

To run it as a separate oTree session, add `spatial_11_20` to the app sequence
of a dedicated session configuration; no changes to the existing session
configuration are needed.
