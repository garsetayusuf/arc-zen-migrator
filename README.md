# Arc ↔ Zen Migrator

Independent Python/PySide6 desktop project based on [NosefU/arc-to-zen](https://github.com/NosefU/arc-to-zen).

**Development build — not a completed bidirectional migrator.** Arc → Zen functionality is preserved from upstream. Zen → Arc currently provides a read-only preview and explicitly blocks unverified writes to Arc's sidebar and CloudKit-synchronized state.

See [support matrix](MIGRATION_SUPPORT.md) and [upstream attribution](UPSTREAM_ATTRIBUTION.md).

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[desktop]"
python desktop.py
```

## Build macOS app

```bash
pip install -e ".[build]"
python scripts/build_desktop.py --version dev
```

Do not use real profiles to validate experimental browser writes. Never upload real browser databases, cookies, passwords, or local session files to GitHub.
