#!/usr/bin/env python3
"""Recount published Agensh replay metadata, without executing its JavaScript.

Usage: python3 agensh-replay-check.py replay.html
Source: https://agens-harness.github.io/project/replay.html
Reference input: 45,518,428 bytes, SHA-256 below.
The results describe retained replay bins and successful lifecycle events, not
independent execution of the experiment or simultaneous model inference.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

SOURCE_URL = "https://agens-harness.github.io/project/replay.html"
EXPECTED_SHA256 = "4543d032af90a885c0356f46c96005d1f7b394cc440fc9dac3e366deec1ddbd0"


def check(path):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Input differs from the reference replay; do not compare silently")
    text = raw.decode("utf-8")
    match = re.search(r"\bconst\s+DATA\s*=\s*", text)
    if match is None:
        raise ValueError("Missing literal const DATA assignment")
    data, consumed = json.JSONDecoder().raw_decode(text[match.end():])
    if data["schemaVersion"] != 4:
        raise ValueError("Only the inspected replay schema version 4 is supported")
    run = data["run"]
    frames = data["frames"]
    categories = data["categories"]
    idle_index = categories.index("idle")
    if len(categories) > 10:
        raise ValueError("Expected one decimal category digit per agent")
    active_by_states = []
    for frame in frames:
        states = frame["states"]
        if len(states) != run["agentCount"]:
            raise ValueError("State-vector width differs from configured population")
        if any(int(state) >= len(categories) for state in states):
            raise ValueError("Unrecognised activity category")
        active_by_states.append(sum(int(state) != idle_index for state in states))
    if active_by_states != [frame["activeAgents"] for frame in frames]:
        raise ValueError("Reported activity differs from non-idle state counts")
    git = data["production"]["gitea"]
    board = data["production"]["board"]
    git_kinds = Counter(event["kind"] for event in git["events"])
    board_types = Counter(record["type"] for record in board["records"])
    if len(board["records"]) != board["coverage"]["successfulWrites"]:
        raise ValueError("Board records disagree with replay coverage metadata")
    peak = max(active_by_states)
    result = {
        "source_url": SOURCE_URL,
        "input_bytes": len(raw),
        "input_sha256": digest,
        "data_json_start_character": match.end(),
        "data_json_characters": consumed,
        "schema_version": data["schemaVersion"],
        "configured_agent_identities": run["agentCount"],
        "recorded_agent_identities": len(data["agents"]),
        "gitea_event_kinds": dict(sorted(git_kinds.items())),
        "gitea_coverage": git["coverage"],
        "board_records": len(board["records"]),
        "board_record_types": dict(sorted(board_types.items())),
        "frames": len(frames),
        "replay_clock_bin_seconds": run["binSeconds"],
        "display_dilation_factor": run["dilationFactor"],
        "display_time_bin_seconds": run["binSeconds"] / run["dilationFactor"],
        "display_duration_seconds": len(frames) * run["binSeconds"] / run["dilationFactor"],
        "peak_non_idle_identities_per_bin": peak,
        "peak_frame_indices_zero_based": [i for i, n in enumerate(active_by_states) if n == peak],
        "activity_categories": categories,
        "non_idle_matches_reported_active_in_every_frame": True,
        "source_provenance": data["provenance"],
        "interpretation": {
            "activity": "A non-idle category in one retained replay bin; not proof of simultaneous LLM execution.",
            "board_fail": "A successful board write tagged FAIL, not a failed tool invocation or independent task failure.",
            "git": "Successful content-free Gitea lifecycle events retained by the replay, with its deduplication/coverage rules.",
            "time": "Follows the replay's subjectiveTime(wallSeconds) = elapsed(wallSeconds / DATA.run.dilationFactor)."
        }
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.replay), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
