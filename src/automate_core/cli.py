from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from automate_core.engine import scan_repository

def main() -> int:
    parser = argparse.ArgumentParser(description="Automate Core CLI - Headless repository analysis")
    parser.add_argument("repository", type=str, help="Path to the repository to scan")
    parser.add_argument("--output", "-o", type=str, help="Output JSON file path")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit with code 1 if critical findings exist")

    args = parser.parse_args()

    repo_path = Path(args.repository).expanduser().resolve()
    if not repo_path.is_dir():
        print(f"Error: Repository path '{repo_path}' is not a directory.", file=sys.stderr)
        return 1

    try:
        report = scan_repository(repo_path)
    except Exception as e:
        print(f"Scan failed: {e}", file=sys.stderr)
        return 1

    report_dict = report.to_dict()

    if args.output:
        try:
            Path(args.output).write_text(json.dumps(report_dict, indent=2, sort_keys=True), encoding="utf-8")
            print(f"Report written to {args.output}")
        except Exception as e:
            print(f"Failed to write output: {e}", file=sys.stderr)
            return 1
    else:
        print(json.dumps(report_dict, indent=2, sort_keys=True))

    if args.fail_on_critical:
        critical_findings = [f for f in report.findings if f.severity == "critical"]
        if critical_findings:
            print(f"\\nError: Found {len(critical_findings)} critical findings.", file=sys.stderr)
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
