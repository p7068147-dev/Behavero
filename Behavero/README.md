# Behavero

**Local-first, evidence-based software behavior investigations.**

Behavero snapshots a directory, compares filesystem state, and can run an explicitly supplied command between snapshots to report observed changes and basic execution metadata.

> **Safety:** Behavero is not a sandbox, malware detector, or containment tool. Do not use `behavero run` to execute unknown or suspected malware. A command may access the network, modify files outside the monitored directory, or launch other processes.

## v0.1.0 features

- SHA-256 hashes for regular files
- File and directory metadata snapshots
- Created, deleted, and modified path reporting
- Symlinks recorded without being followed
- JSON snapshots and reports
- Optional command execution with timeout, duration, and exit code
- Standard-library-only runtime
- Automated tests and GitHub Actions

## Requirements

Python 3.10+. Developed for macOS and Linux.

## Install

```bash
git clone https://github.com/p7068147-dev/Behavero.git
cd Behavero
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Or run from the source folder using `python -m behavero --help`.

## Quick start

```bash
mkdir -p ~/behavero-lab
printf 'initial content\n' > ~/behavero-lab/example.txt
behavero snapshot ~/behavero-lab --output baseline.snapshot.json

printf 'second line\n' >> ~/behavero-lab/example.txt
printf 'new file\n' > ~/behavero-lab/created.txt
behavero compare baseline.snapshot.json ~/behavero-lab --output changes.report.json
```

Try a trusted, harmless command in the lab:

```bash
behavero run --output run.report.json ~/behavero-lab -- \
  python3 -c "from pathlib import Path; Path('demo-created.txt').write_text('hello', encoding='utf-8')"
```

The command after `--` is passed as an argument list with no shell. Standard output and error remain attached to the terminal and are not stored in the report.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Limitations

- The monitored directory is not a security boundary; changes outside it are not observed.
- v0.1.0 does not trace child processes, system calls, network connections, or system-wide changes.
- A timeout does not guarantee that descendant processes are terminated.
- Concurrent writes and unreadable files can affect results.
- Timestamp-only changes are not counted as modifications in this version.
- A changed file is an observation, not proof of malicious behavior.
- Reports can expose local paths and command arguments; review before sharing.

## Roadmap

- [ ] Ignore patterns and richer unreadable-file reporting
- [ ] macOS/Linux process event collectors
- [ ] Human-readable HTML timeline
- [ ] Reproducible demo dataset and release artifacts

## License

MIT; see [LICENSE](LICENSE).
