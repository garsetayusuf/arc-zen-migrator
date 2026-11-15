# Migration support

Arc → Zen: inherited upstream implementation; needs regression validation against real browser versions.

Zen → Arc: **read-only session preview only** at this stage. Arc sidebar writes, pinned tabs, Essentials, folders, profiles, passwords, cookies and CloudKit changes are blocked until isolated profile and synchronization tests demonstrate safety. No reverse migration is advertised as verified.

The application must never silently substitute an export for a successful import. Browser data may contain private information; do not include URLs, titles, credentials, or local profile paths in diagnostic logs.

Before using this project with real data, test on disposable browser profiles and keep independent backups.
