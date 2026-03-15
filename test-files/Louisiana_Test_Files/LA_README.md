# Louisiana Medicaid EDI 834 Test Files

## Overview

These test files simulate EDI 834 Benefit Enrollment and Maintenance transactions
as they would arrive from the Louisiana Department of Health (LADHH) to a Managed
Care Organization (MCO). All files follow the ASC X12N 005010X220A1 standard with
Louisiana-specific Companion Guide conventions.

**These files are designed to contrast with the Ohio test files** to exercise the
system's state-variation handling. Nearly every convention differs between the two
states, even though both use the same X12 834 national standard.

---

## Louisiana vs. Ohio Companion Guide Comparison

This table highlights the key differences that the State Parsing Profile must handle.
The same REF qualifier, the same segment ID, and the same element position can mean
entirely different things depending on which state sent the file.

| Convention | Louisiana | Ohio |
|---|---|---|
| **Sender ID** | `LADHH` | `OHMMIS` |
| **Medicaid ID location** | `REF*0F` in Loop 2000 (format: `LA` + 9 digits) | `REF*1L` in Loop 2000 (format: `OH83XXXXXXX`) |
| **SSN location** | NM109 only (not in a separate REF segment) | `REF*0F` in Loop 2000 AND NM109 |
| **REF\*0F meaning** | **Medicaid ID** | **SSN** |
| **REF\*1L meaning** | **Health Region code** (regions 1–9) | **Medicaid ID** |
| **REF\*ZZ meaning** | **Eligibility Group** code | **Rate Category** code |
| **Rate Category in 834** | **NOT PRESENT** — only in the 820 | Present in `REF*ZZ` |
| **Open-ended enrollment** | `DTP*349` segment is **ABSENT** | `DTP*349*D8*99991231` (sentinel date) |
| **Coverage loops** | **Single** Loop 2300 per member (combined benefit package) | **Multiple** Loop 2300s (one per coverage type) |
| **Plan code format** | Network-based: `BAYOU-STD`, `BAYOU-ABD`, etc. | Product-based: `OH-MED-01`, `OH-DEN-01`, etc. |
| **Plan assignment** | `REF*N6` in Loop 2300 (network region) | `REF*17` in Loop 2300 |
| **State confirmation #** | `REF*CE` in Loop 2000 (must be stored) | Not used |
| **Insurance line code** | `HLT` = full benefit package (med+dental+BH) | `HLT` = medical only, `DEN` = dental, `BHT` = BH |

### Why This Matters

These differences demonstrate why the parsing layer cannot use hardcoded field
mappings. A parser that assumes `REF*0F` is always an SSN (as it is in Ohio) would
incorrectly interpret Louisiana's Medicaid ID as an SSN. A parser that expects
`DTP*349*D8*99991231` for open-ended enrollment would flag every Louisiana member
as missing an end date. A parser that expects multiple Loop 2300s would see
Louisiana's single-loop structure as incomplete.

The State Parsing Profile for each state must define WHERE each field lives, WHAT
each code means, and HOW structural conventions should be interpreted.

---

## Louisiana Companion Guide Conventions

### Identifiers
| Field | Segment/Element | Format | Example |
|---|---|---|---|
| Medicaid ID | REF\*0F, Loop 2000 | `LA` + 9 digits | `LA100234567` |
| SSN | NM109 (qualifier 34) | 9 digits | `445112233` |
| Health Region | REF\*1L, Loop 2000 | `REGION-` + 1-2 digits | `REGION-1` |
| Eligibility Group | REF\*ZZ, Loop 2000 | `LDE-` prefix | `LDE-TANF-001` |
| State Confirmation | REF\*CE, Loop 2000 | `LACONF` + 8 digits | `LACONF20260101` |

### Eligibility Group Codes
| Code | Description | Internal Mapping |
|---|---|---|
| LDE-TANF-001 | TANF Parent/Caretaker | ADULT_TANF |
| LDE-TANF-002 | TANF Child | CHILD_TANF |
| LDE-TANF-003 | TANF Infant (under 1) | CHILD_INFANT_TANF |
| LDE-SSI-001 | SSI Adult | ADULT_SSI |
| LDE-SSI-002 | SSI Child | CHILD_SSI |
| LDE-ABD-001 | Aged | ADULT_AGED |
| LDE-ABD-002 | Blind/Disabled Adult | ADULT_BLIND_DISABLED |
| LDE-EXP-001 | Expansion Adult (XIX) | ADULT_EXPANSION |
| LDE-EXP-002 | Expansion Adult (MAGI) | ADULT_EXPANSION_MAGI |
| LDE-CHIP-001 | LaCHIP (Children) | CHILD_CHIP |
| LDE-CHIP-002 | LaCHIP Affordable Plan | CHILD_CHIP_AFFORD |
| LDE-DUAL-001 | Full Dual Eligible | ADULT_DUAL_FULL |
| LDE-DUAL-002 | Partial Dual Eligible | ADULT_DUAL_PARTIAL |

### Health Regions
Louisiana organizes Medicaid administration into 9 health regions:
| Code | Region Name | Major Cities |
|---|---|---|
| REGION-1 | New Orleans | New Orleans, Metairie |
| REGION-2 | Baton Rouge | Baton Rouge, Gonzales |
| REGION-3 | Houma/Thibodaux | Houma, Thibodaux |
| REGION-4 | Lafayette | Lafayette, New Iberia |
| REGION-5 | Lake Charles | Lake Charles, Sulphur |
| REGION-6 | Alexandria | Alexandria, Pineville |
| REGION-7 | Shreveport | Shreveport, Bossier City |
| REGION-8 | Monroe | Monroe, West Monroe |
| REGION-9 | Hammond | Hammond, Covington |

### Plan Codes (Network-Based)
| Code | Description | Eligible Populations |
|---|---|---|
| BAYOU-STD | Bayou Health Standard Plan | TANF, Expansion, CHIP |
| BAYOU-ABD | Bayou Health ABD Plan | Aged, Blind, Disabled |
| BAYOU-SSI | Bayou Health SSI Plan | SSI recipients |
| BAYOU-DUAL | Bayou Health Dual Plan | Dual-eligible |

### Coverage Structure
Louisiana uses a **single Loop 2300** per member. The insurance line code `HLT`
represents the full benefit package (medical, dental, and behavioral health
combined). This contrasts with Ohio, which sends separate Loop 2300s for each
coverage type.

### Open-Ended Enrollment
Louisiana signals open-ended enrollment by **omitting the DTP\*349 (coverage end
date) segment entirely**. If DTP\*349 is present, the member has a known coverage
end date. This contrasts with Ohio, which always sends DTP\*349 and uses the
sentinel value `99991231` for open-ended enrollment.

---

## Test Files

### File 1: `LA_834_STANDARD_ENROLL_20260201.edi`
**Purpose:** Standard monthly enrollment file — new additions.
- **Members:** 8 new enrollments (maintenance type 021)
- **Scenarios covered:**
  - Multiple eligibility groups (TANF, SSI, Expansion, CHIP, ABD)
  - All 9 health regions represented
  - Single Loop 2300 per member (Louisiana convention)
  - Open-ended enrollment via absent DTP*349
  - REF*CE confirmation codes on every member
  - Medicaid ID in REF*0F (not REF*1L like Ohio)
- **Expected parsing outcome:** All 8 records parse successfully, zero errors

### File 2: `LA_834_MIXED_MAINT_20260215.edi`
**Purpose:** Mid-month update with mixed maintenance types.
- **Members:** 6 transactions
  - 2 additions (021), 2 terminations (024), 1 change (025), 1 reinstatement (026)
- **Scenarios covered:**
  - Termination with explicit DTP*349 end date (vs. absent for open-ended)
  - Change transaction with eligibility group change
  - Reinstatement with new confirmation code
- **Expected parsing outcome:** All 6 records parse successfully, zero errors

### File 3: `LA_834_RETRO_CHANGES_20260301.edi`
**Purpose:** Retroactive enrollment changes.
- **Members:** 5 transactions
  - Retroactive addition, retroactive termination, eligibility group change,
    audit/compare (030), partial dual-eligible enrollment
- **Expected parsing outcome:** All 5 records parse successfully, zero errors

### File 4: `LA_834_EDGE_CASES_20260315.edi`
**Purpose:** Louisiana-specific edge cases.
- **Members:** 6 transactions
  - Hyphenated Cajun/Creole name (BOUDREAUX-THIBODAUX)
  - Name with "de" prefix (DE LA CROIX)
  - Louisiana CHIP child with LaCHIP plan
  - Newborn infant with TANF-003 eligibility
  - Elderly member (90+) with ABD eligibility
  - Partial dual-eligible member
- **Expected parsing outcome:** All 6 records parse successfully, zero errors

### File 5: `LA_834_ERROR_FILE_20260320.edi`
**Purpose:** Deliberate errors for error handling testing.
- **Members:** 5 transactions with various issues
  - Missing required NM1 segment
  - Invalid eligibility group code (not in Louisiana code set)
  - Invalid date format
  - Missing Medicaid ID (REF*0F absent)
  - Valid member (verifies partial file processing)
- **Expected parsing outcome:** 1 successful record, 4 error records

### File 6: `LA_834_LARGE_BATCH_20260401.edi`
**Purpose:** Larger batch for volume testing.
- **Members:** 50 new enrollments
- **Scenarios covered:**
  - Realistic eligibility group distribution
  - All Louisiana health regions
  - Deterministic via random seed 73
- **Expected parsing outcome:** All 50 records parse successfully, zero errors

## File Format Notes
- All `.edi` files are single continuous strings (production format, no line breaks)
- Element separator: `*` | Sub-element separator: `:` | Segment terminator: `~`
- ISA segment is always exactly 106 characters
- All files use X12 version 005010X220A1
