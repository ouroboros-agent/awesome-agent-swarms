# Recounting the published Agensh replay

All five numerical summaries below are reproducible from the authors' published replay. The peak counts identities marked non-idle in a time bin; it does not establish that 1,020 language models were executing simultaneously.

## Exact input

- URL: https://agens-harness.github.io/project/replay.html
- Size: 45,518,428 bytes.
- SHA-256: `4543d032af90a885c0356f46c96005d1f7b394cc440fc9dac3e366deec1ddbd0`.
- Format: HTML containing a literal `const DATA = …` JSON object, schema version 4.
- On 15 November 2026 the source URL returned HTTP 200 and exactly the bytes identified above.

## Reproduction

With Python 3, run:

```sh
python3 agensh-replay-check.py replay.html
```

The script checks the exact historical hash, parses the JSON with Python's JSON decoder, and never executes JavaScript. It starts parsing after `const DATA =` at source-character offset 25,795; the JSON value occupies 45,456,895 characters. It reports derived counts as JSON. It performs no network requests and needs only the standard library.

| Summary | Calculation | Result |
|---|---|---:|
| Successful PR creation events | Count `DATA.production.gitea.events` with `kind == "pull_request"` | 11,111 |
| Successful PR merge events | Same array, `kind == "pull_request_merged"` | 2,800 |
| Successful board writes | Length of `DATA.production.board.records` | 148,079 |
| Board writes labelled FAIL | Same array, `type == "FAIL"` | 56,472 |
| Peak non-idle identities in a bin | For each `DATA.frames` item, count digits in `states` whose category is not `idle`; take maximum | 1,020 |

The event counts agree with the replay's coverage metadata (`pullRequestsCreated`, `pullRequestsMerged`, `successfulWrites`). Counting non-idle states independently matches each frame's `activeAgents` field in all 576 frames. The maximum occurs at zero-based frame indices 460, 487, 539, and 549. The configured population and retained identity list both contain 1,024 identities.

## Time convention

The replay defines `subjectiveTime(wallSeconds)` as `elapsed(wallSeconds / DATA.run.dilationFactor)`. Its metadata specifies a 300-second replay-clock bin and a dilation factor of 8. Therefore:

- displayed duration per bin = 300 / 8 = 37.5 seconds;
- 576 bins = 172,800 replay-clock seconds = 48 replay-clock hours;
- displayed run duration = 172,800 / 8 = 21,600 seconds = 6 hours.

This reproduces the replay's time convention rather than an independent reconstruction of physical timing from raw inference logs.

## What the counts mean

The replay labels its Gitea table “successful content-free Gitea lifecycle events” and its board table “successful content-free context-board writes”. FAIL is a **board-record type**, not a failed tool invocation or a count of independently failed tasks. The activity categories are `idle`, `thinking`, `local`, `gitea`, `mattermost`, and `board`; a non-idle bin does not resolve overlapping execution within that bin.

These are counts of retained event rows under the replay's own deduplication and aggregation rules, not a reconstruction of every raw trajectory event. The replay reports 10,855,853 events read, 5,309,496 retained, and two malformed lines, across 1,024 source files. No new agent experiment was run, and this recount does not establish complete coverage beyond the authors' exported replay.

For the paper and website, an accurate short statement is: “In the authors' published replay we counted 11,111 successful PR-creation events, 2,800 merge events, and 148,079 board writes, including 56,472 tagged FAIL. The replay reaches 1,020 non-idle identities in a 37.5-second displayed interval.”

The replication material consists of this note, `agensh-replay-check.py`, the source URL and hash, and `agensh-replay-check.json`. If the source URL later serves different bytes, the script refuses the changed input rather than silently comparing different versions.
