# Unified reverse migration milestones

This PR brings the reverse-migration components into one reviewable branch.

## Supported today

| Capability | Status |
| --- | --- |
| Arc → Zen upstream GUI | Inherited; regression testing required |
| Zen session inventory | Read-only preview |
| Space selection | Planner API and CLI |
| Tab/pin/Essential/folder metadata | Read-only discovery |
| Duplicate handling | Stable in-run fingerprints |
| Chromium bookmark import | **Isolated test profile only** |
| Portable bookmark HTML export | Available for manual import; Space labels become bookmark folders |
| Backup and restore | Explicit checksum-verified primitives |
| Native Arc sidebar and CloudKit writes | **Blocked** |
| Live Arc profile migration | **Blocked** |
| Passwords, cookies, extensions | **Blocked** |
| macOS signed/notarized app | Not yet validated |

## Test-only bookmark import

Create a disposable copy of an Arc profile, with a Chromium `Bookmarks` file.
Never point this command at the live profile. The test copy must contain
`.arc-zen-isolated-test-profile` and the browser must be closed.

```bash
arc-zen-reverse --zen-profile "/path/to/zen-profile" --preview
arc-zen-reverse --zen-profile "/path/to/zen-profile" --space "space-id" \
  --test-bookmarks-profile "/path/to/disposable-profile" \
  --backup-dir "/path/to/independent-backups" --confirm-isolated
```

The import adds HTTP(S) links to a dedicated Chromium bookmarks folder. It does
**not** create Arc Spaces, Essentials, pinned sidebar tabs, or CloudKit records.
Do not label it as a complete Zen → Arc migration.

## Release gates remaining

1. Validate Zen session schemas using sanitized real-world fixtures.
2. Establish Arc sidebar and CloudKit behavior on disposable profiles, including
   browser restart and sync, before enabling native writes.
3. Integrate transactional recovery with all supported migration operations.
4. Validate signed/notarized macOS app on Apple Silicon.
5. Verify password/cookie handling separately and only with explicit opt-in.

## Practical Zen → Arc fallback: portable bookmark HTML

In the desktop GUI, preview Zen, choose Spaces, and select **Export bookmarks for Arc…**.
Alternatively:

```bash
arc-zen-reverse --zen-profile "/path/to/zen-profile" \\
  --export-bookmarks "/private/location/zen-bookmarks.html"
```

The exported Netscape-format HTML groups HTTP(S) tabs by source Space, status
(Essentials/Pinned/Regular), and folder. Import it manually using a compatible
bookmark importer. **This does not recreate Arc sidebar Spaces or pinned tabs**;
the hierarchy is merely preserved as ordinary bookmark folders. The file
contains private URLs and titles; store it privately and remove it after use.
