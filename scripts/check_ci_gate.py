#!/usr/bin/env python3
"""Fail closed when a required CI job did not actually succeed."""
import json
import os
import sys


def failures(event_name, results):
    required = {"lint", "tests"}
    if event_name == "pull_request":
        required.add("dependency_review")
    elif event_name not in {"push", "workflow_dispatch"}:
        return [f"Unsupported event: {event_name}"]
    errors = []
    for name in sorted(required):
        result = results.get(name, {}).get("result")
        if result != "success":
            errors.append(f"{name}: expected success, got {result or 'missing'}")
    # Dependency review compares PR base/head. Non-PR runs have no such pair.
    if event_name != "pull_request":
        result = results.get("dependency_review", {}).get("result")
        if result not in {"success", "skipped"}:
            errors.append(f"dependency_review: unexpected result {result or 'missing'}")
    return errors


def main():
    try:
        results = json.loads(os.environ["NEEDS_JSON"])
        if not isinstance(results, dict):
            raise ValueError("NEEDS_JSON must be an object")
        errors = failures(os.environ["GITHUB_EVENT_NAME"], results)
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        print(f"Invalid CI evidence: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("All applicable required jobs actually succeeded.")
    if os.environ["GITHUB_EVENT_NAME"] != "pull_request":
        print("Dependency diff: not applicable outside pull_request events.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
