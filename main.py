# Firmware Diff Tool - main.py

import sys
import difflib
from pathlib import Path
import filecmp
import argparse


def read_text_file(path):
    with open(path, 'r', errors='ignore') as f:
        return f.readlines()


def diff_text_files(file1, file2):
    f1 = read_text_file(file1)
    f2 = read_text_file(file2)

    return difflib.unified_diff(
        f1, f2,
        fromfile=file1,
        tofile=file2,
        lineterm=''
    )


def read_binary_file(path):
    with open(path, 'rb') as f:
        return f.read()


def diff_binary_files(file1, file2, ignore_ff=False, ignore_00=False):
    b1 = read_binary_file(file1)
    b2 = read_binary_file(file2)

    len1 = len(b1)
    len2 = len(b2)
    min_len = min(len1, len2)

    all_diffs = []

    # Compare common length
    for i in range(min_len):
        if b1[i] != b2[i]:
            if ignore_ff and (b1[i] == 0xFF or b2[i] == 0xFF):
                continue
            if ignore_00 and (b1[i] == 0x00 or b2[i] == 0x00):
                continue
            all_diffs.append((i, b1[i], b2[i]))

    # Handle trailing differences
    if len1 > len2:
        for i in range(min_len, len1):
            if ignore_ff and b1[i] == 0xFF:
                continue
            if ignore_00 and b1[i] == 0x00:
                continue
            all_diffs.append((i, b1[i], None))

    elif len2 > len1:
        for i in range(min_len, len2):
            if ignore_ff and b2[i] == 0xFF:
                continue
            if ignore_00 and b2[i] == 0x00:
                continue
            all_diffs.append((i, None, b2[i]))

    extra_info = None
    if len1 != len2:
        extra_info = f"File sizes differ: {file1}={len1} bytes, {file2}={len2} bytes"

    return all_diffs, extra_info, len1, len2


def build_display_diffs(all_diffs, max_diffs):
    display_diffs = all_diffs[:max_diffs]
    truncated_display = len(all_diffs) > max_diffs
    return display_diffs, truncated_display


def build_changed_regions(all_diffs):
    if not all_diffs:
        return []

    offsets = sorted(offset for offset, _, _ in all_diffs)

    regions = []
    start = offsets[0]
    end = offsets[0]

    for offset in offsets[1:]:
        if offset == end + 1:
            end = offset
        else:
            regions.append((start, end))
            start = offset
            end = offset

    regions.append((start, end))
    return regions


def analyze_binary_diff(
    file1,
    file2,
    max_diffs=100
):
    all_diffs, extra_info, len1, len2 = diff_binary_files(
        file1,
        file2
    )

    display_diffs, truncated_display = build_display_diffs(all_diffs, max_diffs)

    regions = build_changed_regions(all_diffs)

    result = {
        "mode": "bin",
        "file1": file1,
        "file2": file2,
        "len1": len1,
        "len2": len2,
        "files_identical": (len(all_diffs) == 0 and len1 == len2),
        "size_mismatch": (len1 != len2),
        "all_diffs": all_diffs,
        "display_diffs": display_diffs,
        "diff_count_total": len(all_diffs),
        "display_diff_count": len(display_diffs),
        "truncated_display": truncated_display,
        "regions": regions,
        "extra_info": extra_info,
    }

    return result


def format_changed_regions(regions):
    lines = []
    lines.append("Changed regions:")

    if not regions:
        lines.append("  None")
        return lines

    for start, end in regions:
        size = end - start + 1
        lines.append(f"  0x{start:08X} - 0x{end:08X} ({size} bytes)")

    return lines


def format_binary_diff(result, max_diffs=100, regions_only=False):
    lines = []

    file1 = result["file1"]
    file2 = result["file2"]
    len1 = result["len1"]
    len2 = result["len2"]
    extra_info = result["extra_info"]
    display_diffs = result["display_diffs"]
    regions = result["regions"]

    lines.append("Binary diff result")
    lines.append(f"File 1: {file1} ({len1} bytes)")
    lines.append(f"File 2: {file2} ({len2} bytes)")
    lines.append("")

    if result["files_identical"]:
        lines.append("Files are identical.")
        return lines

    def format_byte(b):
        if b is None:
            return "<none>"
        return f"0x{b:02X}"

    if display_diffs and not regions_only:
        if result["truncated_display"]:
            lines.append(
                f"Showing first {result['display_diff_count']} of {result['diff_count_total']} byte differences:"
            )
        else:
            lines.append(f"Total differences: {result['diff_count_total']}")

        for offset, v1, v2 in display_diffs:
            lines.append(
                f"offset 0x{offset:08X} : {format_byte(v1)} -> {format_byte(v2)}"
            )
        lines.append("")

    if extra_info:
        lines.append(extra_info)

    if regions or extra_info:
        lines.append("")
        lines.extend(format_changed_regions(regions))

    return lines


def compare_directories(dir1, dir2):
    dcmp = filecmp.dircmp(dir1, dir2)
    lines = []
    lines.append("Directory diff result")
    lines.append(f"Directory 1: {dir1}")
    lines.append(f"Directory 2: {dir2}")
    lines.append("")

    summary = {
        "left_only": 0,
        "right_only": 0,
        "diff_files": 0,
        "same_files": 0,
    }

    def walk_diff(dcmp_obj, rel_path=""):
        current = rel_path if rel_path else "."

        lines.append(f"[{current}]")

        if dcmp_obj.left_only:
            lines.append("  Only in directory 1:")
            for name in dcmp_obj.left_only:
                lines.append(f"    {name}")
            summary["left_only"] += len(dcmp_obj.left_only)

        if dcmp_obj.right_only:
            lines.append("  Only in directory 2:")
            for name in dcmp_obj.right_only:
                lines.append(f"    {name}")
            summary["right_only"] += len(dcmp_obj.right_only)

        if dcmp_obj.diff_files:
            lines.append("  Changed files:")
            for name in dcmp_obj.diff_files:
                lines.append(f"    {name}")
            summary["diff_files"] += len(dcmp_obj.diff_files)

        if dcmp_obj.same_files:
            lines.append("  Identical files:")
            for name in dcmp_obj.same_files:
                lines.append(f"    {name}")
            summary["same_files"] += len(dcmp_obj.same_files)

        if (not dcmp_obj.left_only and not dcmp_obj.right_only and
                not dcmp_obj.diff_files and not dcmp_obj.same_files):
            lines.append("  No file differences found.")

        lines.append("")

        for subdir_name, sub_dcmp in dcmp_obj.subdirs.items():
            sub_rel_path = f"{rel_path}/{subdir_name}" if rel_path else subdir_name
            walk_diff(sub_dcmp, sub_rel_path)

    walk_diff(dcmp)

    lines.append("Summary:")
    lines.append(f"  only in directory 1 : {summary['left_only']}")
    lines.append(f"  only in directory 2 : {summary['right_only']}")
    lines.append(f"  changed files       : {summary['diff_files']}")
    lines.append(f"  identical files     : {summary['same_files']}")

    return lines


def save_or_print(lines, output_file=None, saved_message="Result saved to"):
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        print(f"{saved_message}: {output_file}")
    else:
        for line in lines:
            print(line)


def parse_args():
    description = """Firmware Diff Tool

Primary use:
  Compare firmware / binary files with region-based change analysis.

Additional modes:
  text  Compare two text files and output unified diff
  dir   Compare two directories and list changed / added / removed files

Use 'python main.py <mode> -h' for detailed help of each mode.
"""

    epilog = """Examples:
  python main.py --version
  python main.py -h

  python main.py bin old.bin new.bin
  python main.py bin old.bin new.bin --regions-only
  python main.py bin old.bin new.bin --max-diffs 10

  python main.py text file1.txt file2.txt
  python main.py text file1.txt file2.txt result.diff

  python main.py dir dirA dirB
  python main.py dir dirA dirB dir_result.txt

Tip:
  Use 'python main.py <mode> -h' for mode-specific help.
"""

    parser = argparse.ArgumentParser(
        prog="main.py",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="fw_diff_tool free v0.4"
    )

    subparsers = parser.add_subparsers(
        dest="mode",
        required=True,
        title="modes",
        metavar="{text,bin,dir}",
        help="Available comparison modes. Use '<mode> -h' for more details.",
    )

    parser_text = subparsers.add_parser(
        "text",
        help="Compare two text files",
        description="Text mode\n\nCompare two text files and output unified diff.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser_text.add_argument("file1", help="Path to first text file")
    parser_text.add_argument("file2", help="Path to second text file")
    parser_text.add_argument("output_file", nargs="?", help="Optional output file")

    parser_bin = subparsers.add_parser(
        "bin",
        help="Compare two binary / firmware files",
        description="Binary mode\n\nCompare two binary / firmware files and show byte differences and changed regions.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser_bin.add_argument("file1", help="Path to first binary file")
    parser_bin.add_argument("file2", help="Path to second binary file")
    parser_bin.add_argument("output_file", nargs="?", help="Optional output file")

    parser_bin.add_argument(
        "--max-diffs",
        type=int,
        default=100,
        help="Maximum number of byte differences to display (default: 100)"
    )
    parser_bin.add_argument(
        "--regions-only",
        action="store_true",
        help="Show changed regions only"
    )

    parser_dir = subparsers.add_parser(
        "dir",
        help="Compare two directories",
        description="Directory mode\n\nCompare two directories and list differences.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser_dir.add_argument("dir1", help="Path to first directory")
    parser_dir.add_argument("dir2", help="Path to second directory")
    parser_dir.add_argument("output_file", nargs="?", help="Optional output file")

    return parser.parse_args()


def check_file_exists(path):
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)
    if not p.is_file():
        print(f"Error: not a file: {path}")
        sys.exit(1)


def check_dir_exists(path):
    p = Path(path)
    if not p.exists():
        print(f"Error: directory not found: {path}")
        sys.exit(1)
    if not p.is_dir():
        print(f"Error: not a directory: {path}")
        sys.exit(1)


def check_parent_dir_for_output(path):
    p = Path(path)
    parent = p.parent
    if str(parent) and str(parent) != "." and not parent.exists():
        print(f"Error: output directory not found: {parent}")
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()

    if args.mode == "text":
        check_file_exists(args.file1)
        check_file_exists(args.file2)

        if args.output_file:
            check_parent_dir_for_output(args.output_file)

        diff = list(diff_text_files(args.file1, args.file2))

        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                for line in diff:
                    f.write(line + '\n')
            print(f"Text diff result saved to: {args.output_file}")
        else:
            print("Text diff result")
            print("")
            for line in diff:
                print(line)

    elif args.mode == "bin":
        check_file_exists(args.file1)
        check_file_exists(args.file2)

        if args.output_file:
            check_parent_dir_for_output(args.output_file)

        max_diffs = args.max_diffs
        if max_diffs <= 0:
            print("Error: --max-diffs must be greater than 0")
            sys.exit(1)

        result = analyze_binary_diff(
            args.file1,
            args.file2,
            max_diffs=args.max_diffs
        )

        lines = format_binary_diff(
            result,
            max_diffs=args.max_diffs,
            regions_only=args.regions_only
        )

        save_or_print(lines, args.output_file, "Binary diff result saved to")

    elif args.mode == "dir":
        check_dir_exists(args.dir1)
        check_dir_exists(args.dir2)

        if args.output_file:
            check_parent_dir_for_output(args.output_file)

        lines = compare_directories(args.dir1, args.dir2)
        save_or_print(lines, args.output_file, "Directory diff result saved to")
