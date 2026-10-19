# RoboReplay

**Predict → run → reflect → change one thing.** An offline robotics practice notebook for coaches, curious builders, and family experiments.

Compare code or attachment variants within each custom mission. See success counts, median duration for all attempts, median duration for successful attempts, and students' predictions and observations together. A fast failed attempt should not look like a successful speed improvement.

## Try it

Python 3.9+; no packages, accounts, network calls, or installation needed.

```sh
python3 robo_replay.py example.json
python3 robo_replay.py example.json > practice-review.md
python3 robo_replay.py example.json --json
python3 -m unittest -v
```

Copy `example.json` to a private folder outside this repository. Replace its fictional runs with your experiments. Every run needs a unique `id`, `mission`, `variant`, `prediction`, `observation`, positive finite `seconds`, and boolean `success`. Keep `schema_version` at 1. Set a consistent success criterion before testing. Record duration manually with your own stopwatch. Empty notebooks, duplicate IDs, invalid times, and missing fields produce an explanatory error and exit code 2.

The tool only reads the notebook; it never rewrites it. Shell `>` overwrites an existing report, so choose a new filename when retaining history. Reports and JSON exports include your notes: review them before sharing. No real student information is included in the sample.

## A 15-minute coaching activity

1. Choose a small custom mission, such as delivering a foam cube.
2. Predict what one attachment or code change will do.
3. Run several trials of each version under comparable conditions.
4. Record unsuccessful attempts too, including what happened.
5. Compare counts and timing; explain tradeoffs and pick the next experiment.

The sample has only two trials per version. Its 50% versus 100% success rates are observations of that tiny sample, not evidence that one design is reliably better. Mission and variant labels are grouped exactly as entered. Different start conditions, batteries, operators, and difficulty can make comparisons misleading. There is no automatic winner ranking or statistical significance claim.

## Scope and next steps

This first release is a command-line comparison tool. A visual run-entry notebook, built-in timer, route sketching, and side-by-side replay are planned; they are not implemented. It does not connect to or control a robot. It uses generic practice missions, has no official season scoring, and is not affiliated with or endorsed by FIRST or LEGO.

Original project; MIT licensed. Keep improvements dependency-free and add regression tests for validation and comparison changes.
