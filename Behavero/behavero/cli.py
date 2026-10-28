import argparse
import json
import sys
from . import __version__
from .core import compare_snapshots, run_command, snapshot_tree
from .storage import load_json, save_json

def _summary(report):
    s = report.get("summary", {})
    print("Behavero investigation summary")
    for key in ("created", "deleted", "modified", "unchanged"):
        print(f"  {key.capitalize():10} {s.get(key, 0)}")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="behavero",
        description="Local-first, evidence-based software behavior investigations.",
        epilog="Not a sandbox. Never use this tool to execute unknown or suspected malware.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="action", required=True)
    snap = sub.add_parser("snapshot", help="Create a filesystem snapshot")
    snap.add_argument("directory")
    snap.add_argument("-o", "--output", required=True)
    comp = sub.add_parser("compare", help="Compare a baseline with the current directory")
    comp.add_argument("baseline")
    comp.add_argument("directory")
    comp.add_argument("-o", "--output", required=True)
    run = sub.add_parser("run", help="Snapshot, run a command, compare; not a sandbox")
    run.add_argument("directory")
    run.add_argument("--output", required=True)
    run.add_argument("--timeout", type=float, default=60.0)
    run.add_argument("command", nargs=argparse.REMAINDER)
    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.action == "snapshot":
            data = snapshot_tree(args.directory)
            save_json(data, args.output)
            print(f"Snapshot saved: {args.output} ({len(data['entries'])} paths)")
            return 0
        if args.action == "compare":
            report = compare_snapshots(load_json(args.baseline), snapshot_tree(args.directory))
            save_json(report, args.output)
            _summary(report)
            print(f"Report saved: {args.output}")
            return 0
        if args.action == "run":
            command = list(args.command)
            if command and command[0] == "--":
                command = command[1:]
            if not command:
                parser.error("run requires a command after '--'")
            if args.timeout <= 0:
                parser.error("--timeout must be greater than zero")
            before = snapshot_tree(args.directory)
            execution = run_command(command, args.directory, args.timeout)
            after = snapshot_tree(args.directory)
            report = compare_snapshots(before, after)
            report["execution"] = execution
            report["tool_version"] = __version__
            save_json(report, args.output)
            _summary(report)
            print(f"Command exit code: {execution.get('exit_code')}")
            print(f"Report saved: {args.output}")
            return 1 if execution.get("exit_code") not in (0, None) or execution.get("timed_out") else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"behavero: error: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
