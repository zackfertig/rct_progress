"""Highscores builder CLI for OpenRCT2.

This module provides a console entry point to build or merge
OpenRCT2 highscores.dat (v2) from either a CSV (parsed from RCT1
CSS0.DAT) or directly from a CSS0.DAT file.

Usage examples (after installation):
  rct-highscores --css0 ".../DATA/CSS0.DAT" -o ./outdir/highscores.dat --merge
  rct-highscores -i ./outdir/css0_parsed_split.csv -o ./outdir/highscores.dat

You can also run in-place without installation:
  python -m rct_progress.highscores --css0 ".../CSS0.DAT" -o ./outdir/highscores.dat
"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import struct
import sys
import tempfile
from pathlib import Path
from typing import BinaryIO, Dict, Tuple, Optional

from .core import process_file


VERSION = 2
INT64_MIN = -9223372036854775808


def write_cstring(fh, s: str, encoding: str = "utf-8") -> None:
    data = (s or "").encode(encoding, errors="replace")
    fh.write(data)
    fh.write(b"\x00")


def to_money64(company_value_field: str | int | float | None) -> int:
    if company_value_field is None:
        return 0
    s = str(company_value_field).strip()
    if s == "":
        return 0
    try:
        v = int(float(s))
    except ValueError:
        return 0
    return int(v)


def build_from_rows(rows: list[dict], out_path: Path) -> None:
    filtered = [r for r in rows if (r.get("filename") or "").strip() and (r.get("winner") or "").strip()]

    with open(out_path, "wb") as f:
        # header
        f.write(struct.pack("<I", VERSION))
        f.write(struct.pack("<I", len(filtered)))

        for r in filtered:
            file_name_only = Path((r.get("filename") or "").strip()).name
            winner = r.get("winner", "").strip()
            money64 = to_money64(r.get("company_value"))

            write_cstring(f, file_name_only)
            write_cstring(f, winner)
            f.write(struct.pack("<q", money64))  # int64 little-endian
            f.write(struct.pack("<q", INT64_MIN))  # timestamp

    print(f"highscores.dat written: {out_path}")
    print(f"Entries: {len(filtered)}")


def build(csv_path: Path, out_path: Path) -> None:
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    build_from_rows(rows, out_path)


def rows_from_css0(css0_path: Path) -> list[dict]:
    """Parse CSS0.DAT and return rows compatible with build_from_rows."""
    with tempfile.TemporaryDirectory() as td:
        tmp_csv = Path(td) / "css0_parsed.csv"
        rows = process_file(css0_path, tmp_csv, verbose=False, keep_intermediate=False)
    # Normalize keys
    normalized = []
    for r in rows:
        normalized.append(
            {
                "filename": r.get("filename", ""),
                "name": r.get("name", ""),
                "company_value": r.get("company_value", 0),
                "winner": r.get("winner", ""),
            }
        )
    return normalized


def _read_cstring(fh: BinaryIO) -> str:
    bs = bytearray()
    while True:
        b = fh.read(1)
        if not b or b == b"\x00":
            break
        bs += b
    return bs.decode("utf-8", errors="replace")


def load_highscores(path: Path) -> Dict[str, Tuple[str, str, int, int]]:
    """Load highscores.dat into a dict keyed by lowercase filename.

    Value tuple: (filename_original, winner_name, company_value, timestamp)
    """
    result: Dict[str, Tuple[str, str, int, int]] = {}
    if not path.exists():
        return result
    with open(path, "rb") as f:
        _ = int.from_bytes(f.read(4), "little")  # version (unused)
        cnt = int.from_bytes(f.read(4), "little")
        for _ in range(cnt):
            fn = _read_cstring(f)
            name = _read_cstring(f)
            val = int.from_bytes(f.read(8), "little", signed=True)
            ts = int.from_bytes(f.read(8), "little", signed=True)
            result[fn.lower()] = (fn, name, val, ts)
    return result


def best_map_from_rows(rows: list[dict]) -> Dict[str, Tuple[str, str, int, int]]:
    """Reduce rows to best-by-filename map in internal units, timestamp=INT64_MIN.

    For duplicates in rows, keep the entry with the higher company_value.
    """
    best: Dict[str, Tuple[str, str, int, int]] = {}
    for r in rows:
        fn = Path((r.get("filename") or "").strip()).name
        if not fn:
            continue
        winner = (r.get("winner") or "").strip()
        if not winner:
            continue
        val = to_money64(r.get("company_value"))
        key = fn.lower()
        prev = best.get(key)
        if prev is None or val > prev[2]:
            best[key] = (fn, winner, val, INT64_MIN)
    return best


def write_from_map(entries: Dict[str, Tuple[str, str, int, int]], out_path: Path) -> None:
    items = list(entries.values())
    # Deterministic order by filename
    items.sort(key=lambda t: t[0].lower())
    with open(out_path, "wb") as f:
        f.write(struct.pack("<I", VERSION))
        f.write(struct.pack("<I", len(items)))
        for fn, name, val, ts in items:
            write_cstring(f, fn)
            write_cstring(f, name)
            f.write(struct.pack("<q", int(val)))
            f.write(struct.pack("<q", int(ts)))


def _default_openrct2_dir() -> Path:
    sysname = platform.system()
    home = Path.home()
    if sysname == "Windows":
        docs = os.environ.get("USERPROFILE")
        if docs:
            return Path(docs) / "Documents" / "OpenRCT2"
        return home / "Documents" / "OpenRCT2"
    if sysname == "Darwin":
        return home / "Library" / "Application Support" / "OpenRCT2"
    # Linux and others
    return home / ".config" / "OpenRCT2"


def _binary_adjacent_dir() -> Path:
    """Return a sensible directory "next to the binary" for packaged runs.

    - Linux AppImage: use the directory of the .AppImage file (APPIMAGE env).
    - macOS .app (frozen): use the directory containing the .app bundle.
    - Other frozen (Windows/Linux onefile): directory containing sys.executable.
    - Fallback (non-frozen): current working directory.
    """
    # AppImage: environment variable points to the actual .AppImage on disk
    appimage = os.environ.get("APPIMAGE")
    if appimage:
        p = Path(appimage)
        try:
            return p.resolve().parent
        except Exception:
            return p.parent

    # macOS .app bundles
    if getattr(sys, "frozen", False) and platform.system() == "Darwin":
        exe = Path(sys.executable).resolve()
        # Find the ".app" in parents, if present
        for parent in exe.parents:
            if parent.suffix == ".app":
                return parent.parent  # folder containing the .app
        return exe.parent

    # General frozen case (Windows/Linux onefile)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    # Fallback for dev runs
    return Path.cwd()


def _pause_on_exit_windows() -> None:
    """Keep the console window open on Windows when launched by double-click.

    Intended for drag-and-drop UX. No-op on other platforms.
    """
    if platform.system() != "Windows":
        return
    try:
        # input() works when stdin is a console
        input("Press Enter to exit...")
    except Exception:
        try:
            import msvcrt  # type: ignore
            print("Press any key to exit...")
            msvcrt.getch()
        except Exception:
            pass


def _run_build(css0: Optional[Path], csv_in: Optional[Path], out: Path, merge: bool) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    existing_map: Dict[str, Tuple[str, str, int, int]] = {}
    if merge and out.exists():
        existing_map = load_highscores(out)

    if css0 is not None:
        rows = rows_from_css0(css0)
    else:
        assert csv_in is not None
        with open(csv_in, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))

    new_map = best_map_from_rows(rows)
    if merge:
        merged = dict(existing_map)
        for k, v in new_map.items():
            prev = merged.get(k)
            if prev is None or v[2] > prev[2]:
                merged[k] = v
        write_from_map(merged, out)
        print(f"highscores.dat merged and written: {out}")
        print(f"Entries: {len(merged)}")
    else:
        write_from_map(new_map, out)
        print(f"highscores.dat written: {out}")
        print(f"Entries: {len(new_map)}")


def main(argv: Optional[list[str]] = None) -> int:
    """Console entry point for highscores builder.

    Supports drag-and-drop style positional usage when frozen/packaged
    or executed directly, and argparse-based flags otherwise.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Drag-and-drop friendly handling:
    #  - If invoked with one positional arg: treat it as CSS0.DAT and write highscores.dat next to the binary (no merge).
    #  - If invoked with two positional args: if one looks like CSS0.DAT and the other looks like highscores.dat, perform a merge. If no explicit highscores path was provided, write next to the binary.
    dnd_args = [a for a in argv if not a.startswith("-")]

    def looks_like_css0(p: Path) -> bool:
        return p.name.lower() == "css0.dat"

    def looks_like_highscores(p: Path) -> bool:
        return p.name.lower() == "highscores.dat"

    if len(dnd_args) == 1 and all(a.startswith("-") is False for a in dnd_args):
        # Single file dropped: assume CSS0.DAT -> write next to the binary
        css0p = Path(dnd_args[0]).resolve()
        outp = _binary_adjacent_dir() / "highscores.dat"
        _run_build(css0=css0p, csv_in=None, out=outp, merge=False)
        _pause_on_exit_windows()
        return 0

    if len(dnd_args) == 2:
        p1 = Path(dnd_args[0]).resolve()
        p2 = Path(dnd_args[1]).resolve()
        css0p: Optional[Path] = None
        highp: Optional[Path] = None
        if looks_like_css0(p1):
            css0p = p1
        if looks_like_css0(p2):
            css0p = css0p or p2
            highp = p1 if highp is None and p1 != css0p else highp
        if looks_like_highscores(p1):
            highp = p1
        if looks_like_highscores(p2):
            highp = highp or p2
        # If highscores wasn't explicitly provided, default to binary-adjacent dir
        if css0p is not None:
            if highp is None:
                highp = _binary_adjacent_dir() / "highscores.dat"
            _run_build(css0=css0p, csv_in=None, out=highp, merge=True)
            _pause_on_exit_windows()
            return 0

    # No drag-and-drop positional case; use standard argparse
    parser = argparse.ArgumentParser(
        description="Build OpenRCT2 highscores.dat (v2) from RCT1 CSV or CSS0.DAT"
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "-i", "--input", help="Path to input CSV (filename, name, company_value, winner)"
    )
    src.add_argument("--css0", help="Path to CSS0.DAT to parse directly")
    parser.add_argument("-o", "--output", required=True, help="Path to output highscores.dat")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge into existing highscores.dat (keep higher company value per scenario)",
    )
    args = parser.parse_args(argv)

    out = Path(args.output)
    css0p = Path(args.css0).resolve() if args.css0 else None
    csv_in = Path(args.input).resolve() if args.input else None
    _run_build(css0=css0p, csv_in=csv_in, out=out, merge=args.merge)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
