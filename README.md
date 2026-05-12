# Firmware Region Diff (Free Version)

A lightweight CLI tool for comparing firmware / binary files.

---

## What it does

This tool helps you quickly inspect differences between binary / firmware files.

Features:

* Byte-level diff
* Basic region grouping
* Human-readable output
* Text and directory comparison modes

It is designed for quick inspection, debugging, and understanding binary changes.

---

## Example

```
Binary diff result
File 1: a.bin (5 bytes)
File 2: b.bin (6 bytes)

Total differences: 3
offset 0x00000001 : 0x02 -> 0xFF
offset 0x00000003 : 0x04 -> 0x99
offset 0x00000005 : <none> -> 0x06

File sizes differ: a.bin=5 bytes, b.bin=6 bytes

Changed regions:
  0x00000001 - 0x00000001 (1 bytes)
  0x00000003 - 0x00000003 (1 bytes)
  0x00000005 - 0x00000005 (1 bytes)
```

---

## Installation

Requires Python 3.x

```
git clone <your-repo-url>
cd fw_diff_tool
python main.py -h
```

---

## Usage

Compare two binary files:

```
python main.py bin old.bin new.bin
```

Show changed regions only:

```
python main.py bin old.bin new.bin --regions-only
```

Limit displayed differences:

```
python main.py bin old.bin new.bin --max-diffs 10
```

---

## Additional Modes

Text comparison:

```
python main.py text file1.txt file2.txt
```

Directory comparison:

```
python main.py dir dirA dirB
```

---

## Limitations (Free Version)

This free version is designed for basic inspection and debugging.

It does not include:

* Region summary statistics
* JSON output
* Filtering options (ignore patterns, region size)
* Workflow / CI integration

---

## Pro Version

The Pro version adds advanced analysis and automation capabilities:

* Region summary (total bytes, region count, largest region)
* JSON output for scripting and CI pipelines
* Filtering options (ignore patterns, region size)
* Workflow integration (fail conditions, quiet mode)

Designed for engineers who need to integrate binary comparison into real workflows.

👉 Get the Pro version: <https://mtlabs.gumroad.com/l/firmware-region-diff>

---

## Notes

* This tool focuses on clarity and practical usage.
* Output is designed to be readable and script-friendly.
* No GUI — CLI only.

---

## License

This project is licensed under the MIT License. 
