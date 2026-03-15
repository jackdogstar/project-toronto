#!/usr/bin/env python3
"""Validate structural correctness of generated EDI 834 test files."""

import os
import sys

DIR = "/home/claude/edi_test_files"
PASS = "✓"
FAIL = "✗"

def validate_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    filename = os.path.basename(filepath)
    errors = []
    warnings = []

    # 1. Check ISA segment length (106 chars including terminator)
    isa_end = content.index("~") + 1
    isa_raw = content[:isa_end]
    if len(isa_raw) != 106:
        errors.append(f"ISA length is {len(isa_raw)}, expected 106")

    # 2. Detect delimiters
    elem_sep = content[3]  # character after "ISA"
    seg_term = "~"

    # 3. Split into segments
    segments = [s for s in content.split(seg_term) if s.strip()]

    # 4. Check ISA/IEA wrapper
    isa_elems = segments[0].split(elem_sep)
    iea_elems = segments[-1].split(elem_sep)

    if isa_elems[0] != "ISA":
        errors.append("File does not start with ISA")
    if iea_elems[0] != "IEA":
        errors.append("File does not end with IEA")

    isa_control = isa_elems[13].strip() if len(isa_elems) > 13 else "?"
    iea_control = iea_elems[2].strip() if len(iea_elems) > 2 else "?"
    if isa_control != iea_control:
        errors.append(f"ISA control ({isa_control}) != IEA control ({iea_control})")

    # 5. Check GS/GE
    gs_elems = segments[1].split(elem_sep)
    ge_seg = [s for s in segments if s.split(elem_sep)[0] == "GE"]
    if not ge_seg:
        errors.append("Missing GE segment")
    else:
        ge_elems = ge_seg[0].split(elem_sep)
        gs_control = gs_elems[6] if len(gs_elems) > 6 else "?"
        ge_control = ge_elems[2] if len(ge_elems) > 2 else "?"
        if gs_control != ge_control:
            errors.append(f"GS control ({gs_control}) != GE control ({ge_control})")

    # 6. Check ST/SE
    st_seg = [s for s in segments if s.split(elem_sep)[0] == "ST"]
    se_seg = [s for s in segments if s.split(elem_sep)[0] == "SE"]

    if len(st_seg) != 1:
        errors.append(f"Expected 1 ST segment, found {len(st_seg)}")
    if len(se_seg) != 1:
        errors.append(f"Expected 1 SE segment, found {len(se_seg)}")

    if st_seg and se_seg:
        st_elems = st_seg[0].split(elem_sep)
        se_elems = se_seg[0].split(elem_sep)

        st_control = st_elems[2] if len(st_elems) > 2 else "?"
        se_control = se_elems[2] if len(se_elems) > 2 else "?"
        if st_control != se_control:
            errors.append(f"ST control ({st_control}) != SE control ({se_control})")

        # Count segments between ST and SE (inclusive)
        st_idx = next(i for i, s in enumerate(segments) if s.split(elem_sep)[0] == "ST")
        se_idx = next(i for i, s in enumerate(segments) if s.split(elem_sep)[0] == "SE")
        actual_count = se_idx - st_idx + 1
        reported_count = int(se_elems[1])
        if actual_count != reported_count:
            errors.append(f"SE segment count ({reported_count}) != actual ({actual_count})")

    # 7. Count INS segments (members)
    ins_count = sum(1 for s in segments if s.split(elem_sep)[0] == "INS")

    # 8. Check that required segments exist per member
    nm1_count = sum(1 for s in segments if s.split(elem_sep)[0] == "NM1")
    hd_count = sum(1 for s in segments if s.split(elem_sep)[0] == "HD")

    # 9. Verify no line breaks in file content (proper single-line EDI)
    if "\n" in content or "\r" in content:
        warnings.append("File contains line breaks (not production-format single-line)")

    # Report
    status = PASS if not errors else FAIL
    print(f"\n{status} {filename}")
    print(f"  Segments: {len(segments)} | Members (INS): {ins_count} | "
          f"NM1: {nm1_count} | HD (coverages): {hd_count}")

    if errors:
        for e in errors:
            print(f"  {FAIL} ERROR: {e}")
    if warnings:
        for w in warnings:
            print(f"  ⚠ WARNING: {w}")
    if not errors and not warnings:
        print(f"  All structural checks passed")

    return len(errors) == 0


if __name__ == "__main__":
    files = sorted(f for f in os.listdir(DIR) if f.endswith(".edi"))
    all_pass = True
    for f in files:
        if not validate_file(os.path.join(DIR, f)):
            all_pass = False

    print(f"\n{'='*60}")
    if all_pass:
        print(f"{PASS} ALL FILES PASSED structural validation")
    else:
        print(f"{FAIL} Some files have structural errors")
