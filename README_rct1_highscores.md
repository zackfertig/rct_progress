# Generate OpenRCT2 highscores.dat from RCT1 CSV

This script converts an RCT1 progress CSV into OpenRCT2's highscores.dat (v2) so your RCT1 scenario completions (e.g., SC0.SC4 "Forest Frontiers") show as completed in OpenRCT2.

## Input CSV
- Path: `c:\Users\Krabs\repos\rct_progress\outdir\css0_parsed_split.csv`
- Expected columns:
  - `filename` — Scenario filename (e.g., `sc0.sc4`). Case is preserved.
  - `name` — Scenario display name (optional; not used for matching).
  - `company_value` — Integer currency units (e.g., `80000` for $80,000). Scaled ×10 for internal storage.
  - `winner` — Player name. If empty, the row is skipped.

## What gets written
- File format matches `ScenarioRepository.cpp` (v0.4.27):
  1. `uint32` version = 2
  2. `uint32` count = number of entries
  3. For each entry:
     - `cstring` fileName (scenario file name only, e.g., `sc0.sc4`)
     - `cstring` name (player name)
     - `int64` company_value (money64, value ×10)
     - `int64` timestamp (`INT64_MIN` = legacy/unknown)
- Strings are UTF-8 with a trailing 0 byte. Integers are little-endian.

## Generate highscores.dat
Run in PowerShell (VS Code terminal is fine):

```powershell
cd c:\Users\Krabs\repos\rct_progress
py .\build_highscores.py
```

Output: `c:\Users\Krabs\repos\rct_progress\outdir\highscores.dat`

## Install into OpenRCT2
Copy highscores.dat to your OpenRCT2 user folder:

```powershell
Copy-Item .\outdir\highscores.dat "$env:USERPROFILE\Documents\OpenRCT2\highscores.dat" -Force
```

Restart OpenRCT2. Your RCT1 scenarios (like Forest Frontiers) should now appear as completed, with the stored company value and winner name.

## Notes
- Matching uses only the scenario file name (e.g., `sc0.sc4`), which is how OpenRCT2 links highscores to installed scenarios.
- If you also have legacy RCT2 `scores.dat`, it will still be imported, but highscores.dat takes precedence.
- If an entry has the same company value as an existing highscore but no name recorded, OpenRCT2 may update the timestamp on next record; using `INT64_MIN` keeps these imports clearly marked as legacy.

### Troubleshooting: AA scenarios completed but not available, or duplicates (e.g., Funtopia appears twice)
Symptoms
- Added Attractions (AA) scenarios are marked “completed” but don’t appear as available/selectable.
- A scenario like “Funtopia” shows up twice in the list.

Cause
- Duplicate scenario files in your RCT1 install or user scenario folders (e.g., `Old_SC40.SC4` … `Old_SC69.SC4`) cause the repository to index multiple variants or hide the canonical one.

Fix
1) Close OpenRCT2.
2) In your RCT1 scenarios directories (and/or Documents/OpenRCT2/scenarios), move/remove duplicate AA files so only the canonical filenames remain (typically `sc40.sc4` … `sc69.sc4`).
  - If you see files prefixed with `Old_` (e.g., `Old_SC40.SC4`), zip them for backup and remove them from the scanned folders.
3) Force a scenario re-index by deleting the cache file:
  - `%USERPROFILE%\Documents\OpenRCT2\scenarios.idx`
4) Restart OpenRCT2.

Tips
- Highscores only attach to scenarios that are actually installed and indexed; cleanup ensures the repository finds the correct SC4 file.
- Matching is by filename only, so keeping the canonical `scXX.sc4` names avoids mismatches.
