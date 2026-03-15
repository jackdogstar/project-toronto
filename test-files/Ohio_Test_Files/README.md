# Ohio Medicaid EDI 834 Test Files

## Overview

These test files simulate EDI 834 Benefit Enrollment and Maintenance transactions
as they would arrive from the Ohio Department of Medicaid (OHMMIS) to a Managed
Care Organization (MCO). All files follow the ASC X12N 005010X220A1 standard with
Ohio-specific conventions per the **ODM Companion Guide v13.1**.

## ODM Companion Guide Conventions Used

| Convention | Detail |
|---|---|
| **Sender ID** | `OHMMIS` (Ohio MMIS) |
| **Receiver ID** | `MCOPLAN` (MCO identifier) |
| **Medicaid ID** | `REF*0F` in Loop 2000, 12 chars, IE-origin starts with `9` |
| **SSN** | `NM1*IL` element 09 (qualifier 34) |
| **Rate Cell** | `REF*1L` in Loop 2300 (10 chars, `XXXXXXXXXX` = no rate cell) |
| **Full File** | `BGN08=4`, all `INS03=030` (audit/compare monthly roster) |
| **Changes File** | `BGN08=2`, `INS03=001/021/024` (daily updates) |
| **HD01 Codes** | `001`=Change, `002`=Delete, `021`=Add, `024`=Term, `025`=Reinstate, `030`=Audit |
| **Open-Ended Enrollment** | `DTP*349*D8*99991231` (sentinel date) |
| **Coverage Loops** | Multiple Loop 2300 per member (medical + dental + BH) |
| **Element Separator** | `*` |
| **Sub-Element Separator** | `:` |
| **Segment Terminator** | `~` |
| **Repetition Separator** | `^` (ISA11) |

## Insurance Line Codes (HD03)

| Code | Description |
|---|---|
| HMO | Health Maintenance Organization (standard medical) |
| MM | Dental |
| HLT | Health (used for behavioral health) |
| AG | Dental Waiver |

## Plan Coverage Description Codes (HD04)

| Code | Description | Used For |
|---|---|---|
| CFC | Covered Families and Children | TANF, Expansion, children |
| ABD | Aged/Blind/Disabled | SSI, Dual-eligible, elderly |
| OHR | Ohio Managed Care (other) | General managed care |
| BH-SUD | Behavioral Health / Substance Use | Behavioral health coverage |

## Test Files

### File 1: `OH_834_STANDARD_ENROLL_20260201.edi`
**Type:** Changes file (BGN08=2)
**Purpose:** Standard enrollment file — new additions only.
- **Members:** 8 new enrollments (INS03=021, HD01=021)
- **Scenarios covered:**
  - Multiple age groups (infant to elderly)
  - Male and female members
  - Medical-only (HMO/CFC or HMO/ABD) and medical+dental
  - Various Ohio regions (Columbus, Cleveland, Cincinnati, Dayton, Toledo, Akron)
  - CFC and ABD plan codes
  - One member with medical+dental+behavioral health (3 Loop 2300s)
  - Rate cells in all Loop 2300 coverages
- **Expected parsing outcome:** All 8 records parse clean, zero validation issues

### File 2: `OH_834_MIXED_MAINT_20260215.edi`
**Type:** Changes file (BGN08=2)
**Purpose:** Mid-month update with mixed maintenance types.
- **Members:** 6 transactions
  - 3 additions (INS03=021, HD01=021 or HD01=025 for reinstatement)
  - 1 change (INS03=001, HD01=001 — address update)
  - 2 terminations (INS03=024, HD01=024 — with specific end dates)
- **Scenarios covered:**
  - All valid Changes-file maintenance types (001, 021, 024)
  - HD01=025 (reinstatement at coverage level) with INS03=021
  - Termination with specific end dates (not 99991231)
  - INS04 reason codes: 28 (add), 1 (term), EC (change)
- **Expected parsing outcome:** All 6 records parse clean, zero validation issues

### File 3: `OH_834_RETRO_CHANGES_20260301.edi`
**Type:** Changes file (BGN08=2)
**Purpose:** Retroactive enrollment changes affecting prior periods.
- **Members:** 5 transactions
  - 1 retroactive addition (elig date 2 months prior)
  - 1 retroactive termination (termed effective last month)
  - 2 changes (INS03=001 — rate category change + data correction)
  - 1 dual-eligible new enrollment
- **Scenarios covered:**
  - Retroactive effective dates
  - Multiple INS03=001 change scenarios
  - Dual-eligible member (ABD plan)
- **Expected parsing outcome:** All 5 records parse clean, zero validation issues

### File 4: `OH_834_EDGE_CASES_20260315.edi`
**Type:** Changes file (BGN08=2)
**Purpose:** Edge cases and unusual-but-valid scenarios.
- **Members:** 6 transactions
  - Hyphenated last name (GARCIA-LOPEZ)
  - Suffix in last name field (THOMPSON JR)
  - Very long address (N3 with long street + apartment)
  - Infant member (DOB 2 days before eligibility)
  - Elderly member (85+) with ODM placeholder address and XXXXXXXXXX rate cell
  - Member with 3 coverages (medical + dental + behavioral health)
- **Expected warnings:**
  - OH-VAL-103: XXXXXXXXXX rate cell (BAKER, HELEN M)
  - OH-VAL-105: ODM placeholder address (BAKER, HELEN M)
- **Expected parsing outcome:** All 6 parse successfully, 2 warnings (intentional)

### File 5: `OH_834_ERROR_FILE_20260320.edi`
**Type:** Changes file (BGN08=2)
**Purpose:** Deliberate errors for testing error handling and validation.
- **Members:** 5 transactions
  - Member 1: Missing NM1 segment (demographics empty)
  - Member 2: Short Medicaid ID (8 chars) → OH-VAL-001 Critical
  - Member 3: Invalid DOB (19901332 — month 13, day 32)
  - Member 4: No coverages (no HD segment) → OH-VAL-005 Critical
  - Member 5: Valid member (verifies partial file processing)
- **Expected critical errors:**
  - OH-VAL-001: Medicaid ID not 12 chars (ERRORTEST, BADID)
  - OH-VAL-005: No coverage found (ERRORTEST, NOCOV)
- **Expected parsing outcome:** All 5 parse, 2 critical errors, 3 clean members

### File 6: `OH_834_LARGE_BATCH_20260401.edi`
**Type:** Full file (BGN08=4)
**Purpose:** Full monthly roster file for volume testing.
- **Members:** 50 audit/compare records (INS03=030, HD01=030)
- **Scenarios covered:**
  - Full file type (BGN08=4) with audit maintenance
  - Mix of CFC, ABD, OHR plan codes
  - ~70% medical+dental, ~30% medical-only
  - Various Ohio cities and demographics
  - All rate cells populated (no XXXXXXXXXX)
  - Deterministic generation (random seed 42)
- **Expected parsing outcome:** All 50 records parse clean, zero validation issues

## File Format Notes

- All `.edi` files are single continuous strings with no line breaks (production format)
- Segment terminator is `~` (tilde)
- Element separator is `*` (asterisk)
- Sub-element separator is `:` (colon)
- Repetition separator is `^` (caret, ISA11)
- ISA segment is always exactly 106 characters
- All files use X12 version 005010X220A1
- Generated by `generate_test_files.py` (run to regenerate)
