# Building legacy scores.dat for OpenRCT2 (historical)

Note: For importing RCT1 (SC4) progress into OpenRCT2, use highscores.dat as described in `README.md`. The legacy RCT2 scores.dat format below is retained for reference.

This creates a legacy RCT2-style scores.dat from your CSV so OpenRCT2 can import legacy highscores.

Input CSV
- Path: c:\Users\Krabs\repos\rct_progress\outdir\css0_parsed_split.csv
- Columns used: filename, name, company_value, winner
- Rows with empty filename are skipped.
- company_value >= 2,147,483,648 is treated as “no score”.

What gets written
- Path: SCENARIOS\<FILENAME> (uppercased).
- Flags: Visible+Completed if winner is present and company_value is valid; else 0.
- CompanyValue: company_value × 10 (money32 internal units).
- Other fields are filled with safe dummy values and zero padding to match ScoresEntry.

Generate scores.dat
- PowerShell:
  - py c:\Users\Krabs\repos\rct_progress\build_scores.py
- Output: c:\Users\Krabs\repos\rct_progress\outdir\scores.dat

Import into OpenRCT2
- Copy scores.dat to one of:
  - %USERPROFILE%\Documents\OpenRCT2\legacy\scores.dat
  - Your original RCT2 install folder (next to its scores.dat)
- Restart OpenRCT2 or trigger a content rescan.

Notes
- Encoding is Windows-1252/Latin-1 for legacy strings.
- The binary layout matches RCT2.h ScoresEntry (0x02B0 bytes per entry).
- You can adjust the path prefix in normalize_path() if needed.