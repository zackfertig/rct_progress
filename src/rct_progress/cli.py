"""Tiny CLI wrapper around :mod:`rct_progress.core`.

This module is deliberately minimal: it parses command-line
arguments, configures logging and calls the pure functions in
``core``. Keeping CLI code separate from core logic makes testing
and reuse easier.
"""
from pathlib import Path
import argparse
import logging
from typing import Optional

from . import core


def main(argv: Optional[list] = None) -> int:
    """Entry point for the console script.

    Args:
        argv: Optional list of arguments (defaults to ``sys.argv``).

    Returns:
        An exit code (0 for success).
    """
    parser = argparse.ArgumentParser(description='Decompress and decrypt a CSS0.DAT file and parse it to CSV.')
    parser.add_argument('--input', '-i', default='CSS0.DAT', help='Path to input CSS0.DAT file (default: CSS0.DAT)')
    parser.add_argument('--out', '-o', default='css0_parsed.csv', help='Output CSV filename (default: css0_parsed.csv)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Write intermediate decompressed/decrypted binary files and print extra info')
    args = parser.parse_args(argv)

    # If a relative input path is provided, assume it's relative to the
    # current working directory (pwd).
    inp_path = Path(args.input)
    if not inp_path.is_absolute():
        inp_path = Path.cwd() / args.input

    # For the output CSV, if a relative path is provided, write it into the
    # current working directory (so `-o foo.csv` uses pwd), unless an absolute
    # path is given.
    out_csv = Path(args.out) if Path(args.out).is_absolute() else Path.cwd() / args.out

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format='%(levelname)s: %(message)s')
    core.process_file(inp_path, out_csv, verbose=args.verbose)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
