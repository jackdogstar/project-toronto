# Expected Parsing Outcomes — Louisiana 834 Test Files

This document defines the expected parsing output for each Louisiana test file.
It serves as the golden file reference per TDD Section 10.2.

**Critical: A parser configured for Ohio conventions will misinterpret these files.**
The expected outcomes below assume a Louisiana State Parsing Profile is loaded.

---

## Cross-State Parsing Trap Reference

Before reviewing individual file outcomes, here are the specific fields where an
Ohio-configured parser would produce WRONG results on Louisiana data:

| Segment | Ohio Interpretation | Louisiana Interpretation | Consequence of Wrong Profile |
|---|---|---|---|
| `REF*0F*LA100234567` | SSN = "LA100234567" | **Medicaid ID** = "LA100234567" | Member unidentifiable; SSN field corrupted |
| `REF*1L*REGION-1` | Medicaid ID = "REGION-1" | **Health Region** = Region 1 | Medicaid ID populated with garbage |
| `REF*ZZ*LDE-TANF-001` | Rate Category = "LDE-TANF-001" | **Eligibility Group** = TANF Parent | Rate category lookup fails on elig group code |
| `DTP*349` absent | Error: missing end date | **Open-ended enrollment** (correct) | False validation error on every member |
| Single `HD` loop | Missing dental coverage? | **Full benefit package** (med+dental+BH) | Coverage appears incomplete |
| `REF*N6*NET-1` | Unknown/unrecognized | **Network region** assignment | Data silently dropped or flagged |
| `REF*CE*LACONF...` | Unknown/unrecognized | **State confirmation number** | Audit trail data lost |

---

## File 1: LA_834_STANDARD_ENROLL_20260201.edi

### Envelope
| Field | Expected Value |
|---|---|
| Interchange Control | 000000001 |
| Sender ID | LADHH |
| Receiver ID | MCOPLAN |
| Interchange Date | 260201 (Feb 1, 2026) |
| Interchange Time | 0800 |
| Functional ID | BE (Benefit Enrollment) |
| Transaction Set ID | 834 |
| Version | 005010X220A1 |

### Summary
| Metric | Expected |
|---|---|
| Total member records | 8 |
| Successfully parsed | 8 |
| Parsing errors | 0 |
| Parsing warnings | 0 |
| HD segments (coverages) | 8 (one per member — Louisiana single-loop) |

### Member Records

**Member 1: BOUDREAUX, MARIE C**
| Field | Raw Value | Normalized Value | Notes |
|---|---|---|---|
| Maintenance Type | 021 | Addition | |
| Medicaid ID (REF\*0F) | LA100234567 | LA100234567 | Ohio puts SSN here |
| Health Region (REF\*1L) | REGION-1 | Region 1 (New Orleans) | Ohio puts Medicaid ID here |
| Elig Group (REF\*ZZ) | LDE-TANF-001 | ADULT_TANF (Parent/Caretaker) | Ohio puts rate category here |
| Confirmation (REF\*CE) | LACONF202602010001 | LACONF202602010001 | Ohio doesn't have this |
| SSN | 445112233 (in NM109) | 445112233 | Ohio has separate REF\*0F |
| DOB | 19870623 | 1987-06-23 | |
| Gender | F | F | |
| City/State/ZIP | NEW ORLEANS/LA/70112 | NEW ORLEANS/LA/70112 | |
| Coverage Count | 1 | 1 | Ohio would have 2 (med+dental) |
| Coverage | HLT / BAYOU-STD | Full Package / Bayou Standard | Ohio: HLT = medical only |
| Coverage Start | 20260201 | 2026-02-01 | |
| Coverage End | (DTP\*349 absent) | null (open-ended) | Ohio: 99991231 sentinel |
| Network (REF\*N6) | NET-1 | Network Region 1 | Ohio uses REF\*17 |

**Member 2: LANDRY, ANTOINE J** — Expansion (XIX), Baton Rouge, Region 2
| Field | Raw Value | Normalized |
|---|---|---|
| Medicaid ID | LA100345678 | LA100345678 |
| Elig Group | LDE-EXP-001 | ADULT_EXPANSION |
| Region | REGION-2 | Region 2 (Baton Rouge) |
| Plan | BAYOU-STD | Bayou Standard |

**Member 3: THIBODAUX, CAMILLE A** — TANF Child, Houma, Region 3
| Field | Raw Value | Normalized |
|---|---|---|
| Medicaid ID | LA100456789 | LA100456789 |
| Elig Group | LDE-TANF-002 | CHILD_TANF |
| DOB | 20180312 | 2018-03-12 |
| Region | REGION-3 | Region 3 (Houma/Thibodaux) |

**Member 4: GUIDRY, RENEE M** — SSI Adult, Lafayette, Region 4
| Field | Raw Value | Normalized |
|---|---|---|
| Elig Group | LDE-SSI-001 | ADULT_SSI |
| Plan | BAYOU-SSI | Bayou SSI Plan |

**Member 5: BROUSSARD, ETIENNE P** — LaCHIP Child, Lake Charles, Region 5
| Field | Raw Value | Normalized |
|---|---|---|
| Elig Group | LDE-CHIP-001 | CHILD_CHIP |
| Plan | BAYOU-STD | Bayou Standard |
| DOB | 20140907 | 2014-09-07 |

**Member 6: FONTENOT, THERESA L** — ABD Aged, Alexandria, Region 6
| Field | Raw Value | Normalized |
|---|---|---|
| Elig Group | LDE-ABD-001 | ADULT_AGED |
| Plan | BAYOU-ABD | Bayou ABD Plan |
| DOB | 19420301 | 1942-03-01 |

**Member 7: RICHARD, JEAN B** — Expansion MAGI, Shreveport, Region 7
| Field | Raw Value | Normalized |
|---|---|---|
| Elig Group | LDE-EXP-002 | ADULT_EXPANSION_MAGI |
| Plan | BAYOU-STD | Bayou Standard |

**Member 8: HEBERT, CLAIRE D** — Full Dual Eligible, Monroe, Region 8
| Field | Raw Value | Normalized |
|---|---|---|
| Elig Group | LDE-DUAL-001 | ADULT_DUAL_FULL |
| Plan | BAYOU-DUAL | Bayou Dual Plan |
| DOB | 19480712 | 1948-07-12 |

---

## File 2: LA_834_MIXED_MAINT_20260215.edi

### Summary
| Metric | Expected |
|---|---|
| Total member records | 6 |
| Successfully parsed | 6 |
| Parsing errors | 0 |
| Maintenance type 021 (Addition) | 2 |
| Maintenance type 024 (Termination) | 2 |
| Maintenance type 025 (Change) | 1 |
| Maintenance type 026 (Reinstatement) | 1 |

### Key Parsing Verification Points

**COMEAUX, MARCEL E** — Addition (021)
- Region 9 (Hammond) — tests coverage of all 9 regions across files
- Expansion adult, BAYOU-STD plan

**MELANCON, SIMONE R** — Addition (021)
- Region 1, Metairie (not New Orleans — same region, different city)

**DUPRE, DANIELLE N** — Termination (024)
- **DTP\*349 IS present**: `DTP*349*D8*20260228`
- Normalized end date: 2026-02-28
- This is the KEY test: Louisiana sends DTP\*349 ONLY for terminations
- Contrast: open-ended members have NO DTP\*349 at all

**MOUTON, PHILIPPE G** — Termination (024)
- Coverage end: 20260215 (mid-month)
- Original eligibility: 20240101 (2+ years enrolled)
- SSI plan (BAYOU-SSI)

**CASTILLE, GABRIELLE T** — Change (025)
- Eligibility group change: aged from TANF child into CHIP
- New elig group: LDE-CHIP-001
- Plan changes accordingly: BAYOU-STD (same plan, different elig group)
- Tests that elig group changes are tracked even when plan doesn't change

**DOUCET, LUCIEN H** — Reinstatement (026)
- EXP-002 (MAGI), reinstated to Region 7
- New confirmation code issued (different from original enrollment)
- Open-ended (no DTP\*349)

---

## File 3: LA_834_RETRO_CHANGES_20260301.edi

### Summary
| Metric | Expected |
|---|---|
| Total member records | 5 |
| Successfully parsed | 5 |
| Parsing errors | 0 |

### Key Verification Points

**TRAHAN, ANNETTE P** — Retroactive Addition
- File date: 20260301, Eligibility date: 20260101 (2 months retro)
- Should trigger retroactive payment adjustment detection

**ARCENEAUX, GASTON W** — Retroactive Termination
- Coverage end: 20260201 (prior month)
- DTP\*349 present (terminated member)
- Long enrollment: 20230801 to 20260201

**ROMERO, JAMES K** — Eligibility Group Change (025)
- Changed from EXP-001 to EXP-002
- Same plan (BAYOU-STD) but different eligibility basis
- Important for rate reconciliation since rate may differ

**LEBLANC, COLETTE S** — Audit/Compare (030)
- TANF child, Region 3
- 030 = roster comparison, not an enrollment action
- Should be stored but not create enrollment state changes

**JOHNSON, DOROTHY F** — Partial Dual Eligible (new)
- LDE-DUAL-002 (partial, not full)
- BAYOU-DUAL plan
- Age 81 — appropriate for dual eligibility
- Region 8 (Monroe area)

---

## File 4: LA_834_EDGE_CASES_20260315.edi

### Summary
| Metric | Expected |
|---|---|
| Total member records | 6 |
| Successfully parsed | 6 |
| Parsing errors | 0 |
| HD segments (coverages) | 6 (one per member) |

### Key Verification Points

**BOUDREAUX-THIBODAUX, CELESTE M** — Hyphenated Cajun Name
- Two hyphenated Cajun surnames
- Parser must preserve full hyphenated name: "BOUDREAUX-THIBODAUX"
- Tests longest realistic Louisiana last name

**DE LA CROIX, PIERRE A** — Multi-Word Creole Name
- NM1 last name field: "DE LA CROIX" (spaces within last name)
- Parser must preserve multi-word last name as-is
- NM103 = "DE LA CROIX", NM104 = "PIERRE"
- This is structurally valid X12 — spaces are allowed within elements

**BROUSSARD, JACQUES L** — LaCHIP Affordable Plan
- LDE-CHIP-002 (LaCHIP Affordable Plan, vs standard CHIP-001)
- Tests Louisiana-specific CHIP sub-classification
- Region 9 (Covington)

**LANDRY, BEAU** — Newborn Infant
- DOB: 20260208 (2 days before eligibility start)
- Elig Group: LDE-TANF-003 (TANF Infant Under 1)
- No middle name (absent)
- Tests youngest possible member scenario

**COMEAUX, RUTH E** — Elderly (90+)
- DOB: 19350611 (age 90)
- LDE-ABD-001 (Aged)
- BAYOU-ABD plan

**FONTENOT, EMILE G** — Partial Dual Eligible
- LDE-DUAL-002 (partial dual)
- BAYOU-DUAL plan
- Tests dual eligibility sub-classification

---

## File 5: LA_834_ERROR_FILE_20260320.edi

### Summary
| Metric | Expected |
|---|---|
| Total member records | 5 |
| Successfully parsed | 1 |
| Parsing errors | 4 |

### Expected Errors

**Record 1 (Medicaid ID: LA500ERR001)** — Missing NM1 Segment
- Error Type: LOOP_STRUCTURE_ERROR
- Detail: Required NM1\*IL segment missing in Loop 2100A
- Severity: Critical
- Note: Medicaid ID is in REF\*0F (Louisiana convention)

**Record 2 (Medicaid ID: LA500ERR002)** — Invalid Eligibility Group
- Error Type: UNRESOLVED_CODE
- Detail: Eligibility group "LDE-INVALID-999" not in Louisiana code set
- Severity: Warning or Critical (depending on profile config)
- Note: In Ohio, REF\*ZZ contains rate category; here it's eligibility group.
  The same UNRESOLVED_CODE error has different business meaning per state.

**Record 3 (Medicaid ID: LA500ERR003)** — Invalid Date
- Error Type: FORMAT_CORRECTION failure
- Detail: DOB "19881332" — month 13, day 32
- Severity: Critical

**Record 4 (no Medicaid ID)** — Missing REF\*0F (Medicaid ID)
- Error Type: Missing required element
- Detail: REF\*0F absent — no Louisiana Medicaid ID
- Severity: Critical or Warning
- Note: In Ohio, missing REF\*0F means missing SSN. In Louisiana, missing
  REF\*0F means missing Medicaid ID — a much more critical identifier.

**Record 5: GOODRECORD, VALID A** — Valid Record
- Parses successfully
- Medicaid ID: LA500VALID1
- Elig Group: LDE-EXP-001 → ADULT_EXPANSION
- Verifies partial file processing (NF-302)

---

## File 6: LA_834_LARGE_BATCH_20260401.edi

### Summary
| Metric | Expected |
|---|---|
| Total member records | 50 |
| Successfully parsed | 50 |
| Parsing errors | 0 |
| HD segments | 50 (exactly 1 per member — Louisiana single-loop) |
| Unique eligibility groups | up to 13 |
| Health regions | all 9 represented |

### Eligibility Group Distribution (approximate, seed 73)
| Group | Expected Count (approx) |
|---|---|
| LDE-EXP-001 | ~7 |
| LDE-TANF-001 | ~5 |
| LDE-TANF-002 | ~5 |
| LDE-CHIP-001 | ~5 |
| LDE-SSI-001 | ~5 |
| LDE-EXP-002 | ~5 |
| LDE-TANF-003 | ~3 |
| LDE-SSI-002 | ~3 |
| LDE-ABD-001 | ~3 |
| LDE-DUAL-001 | ~3 |
| LDE-ABD-002 | ~2 |
| LDE-CHIP-002 | ~2 |
| LDE-DUAL-002 | ~2 |

### Structural Verification
- All 50 ISA/IEA, GS/GE, ST/SE control numbers match
- SE segment count equals actual segment count
- Exactly 50 HD segments (one per member — single-loop convention)
- Zero DTP\*349 segments (all open-ended enrollments)
- All 50 REF\*CE confirmation codes present and unique
- Random seed 73 ensures reproducible results (different from Ohio's seed 42)
- File suitable for cross-state concurrent processing tests (with Ohio file 6)

---

## Cross-State Test Scenario

Files 6 from both Ohio and Louisiana are designed to be processed concurrently
to test state isolation (FR-602, FR-613). When both files are processed:

| Check | Expected Result |
|---|---|
| Ohio member count | 50 |
| Louisiana member count | 50 |
| Ohio HD count | ~83 (multiple per member) |
| Louisiana HD count | 50 (exactly one per member) |
| Ohio DTP\*349 count | ~83 (one per HD, all 99991231) |
| Louisiana DTP\*349 count | 0 (all open-ended = absent) |
| Ohio REF\*CE count | 0 (not used) |
| Louisiana REF\*CE count | 50 (all present) |
| Cross-contamination | ZERO — no Ohio data in Louisiana results or vice versa |
