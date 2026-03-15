# Expected Parsing Outcomes — Ohio 834 Test Files

These test files use **ODM Companion Guide v13.1** conventions.

---

## File 1: OH_834_STANDARD_ENROLL_20260201.edi

### Envelope
| Field | Expected Value |
|---|---|
| Interchange Control | 000000001 |
| Sender ID | OHMMIS |
| Receiver ID | MCOPLAN |
| File Type (BGN08) | 2 (Changes) |
| Version | 005010X220A1 |

### Summary
| Metric | Expected |
|---|---|
| Total members | 8 |
| Clean members | 8 |
| Critical errors | 0 |
| Warnings | 0 |

### Member Records

| # | Name | INS03 | Medicaid ID (REF*0F) | SSN (NM1-09) | Plan (HD04) | Coverages |
|---|---|---|---|---|---|---|
| 1 | JOHNSON, MARIA A | 021 | 9A0100000001 | 123456789 | CFC | HMO+MM |
| 2 | WILLIAMS, ROBERT T | 021 | 9A0100000002 | 234567891 | ABD | HMO |
| 3 | GARCIA, ISABELLA M | 021 | 9A0100000003 | 345678912 | CFC | HMO+MM |
| 4 | MARTINEZ, CARLOS | 021 | 9A0100000004 | 456789123 | CFC | HMO |
| 5 | BROWN, JAYDEN R | 021 | 9A0100000005 | 567891234 | CFC | HMO+MM |
| 6 | DAVIS, PATRICIA L | 021 | 9A0100000006 | 678912345 | ABD | HMO |
| 7 | THOMPSON, EMILY K | 021 | 9A0100000007 | 789123456 | ABD | HMO+MM |
| 8 | WILSON, JAMES D | 021 | 9A0100000008 | 891234567 | CFC | HMO+MM+HLT(BH-SUD) |

**Key verification points:**
- All Medicaid IDs are 12 chars starting with `9` (IE-origin)
- SSN is in NM1*IL element 09 (not REF*0F)
- Rate cells in Loop 2300 REF*1L (format: `0260201NNN`)
- Member 8 has 3 coverages: medical (HMO/CFC), dental (MM/CFC), behavioral (HLT/BH-SUD)
- All coverage end dates are 99991231 (open-ended)

---

## File 2: OH_834_MIXED_MAINT_20260215.edi

### Summary
| Metric | Expected |
|---|---|
| Total members | 6 |
| Clean members | 6 |
| INS03=021 (Addition) | 3 |
| INS03=001 (Change) | 1 |
| INS03=024 (Termination) | 2 |

### Key Verification Points

| Name | INS03 | HD01 | Action | Key Detail |
|---|---|---|---|---|
| PEREZ, ROSA E | 021 | 021 | Addition | Medical + dental |
| NGUYEN, DAVID H | 021 | 021 | Addition | Medical only |
| TAYLOR, MICHELLE N | 024 | 024 | Termination | End date: 20260228 (not 99991231) |
| CLARK, STEVEN W | 024 | 024 | Termination | End date: 20260215, ABD plan |
| MOORE, AIDEN J | 001 | 001 | Change | Address update, INS04=EC |
| HARRIS, KEVIN B | 021 | 025 | Reinstatement | INS03=021 (addition back), HD01=025 (reinstate at coverage level) |

---

## File 3: OH_834_RETRO_CHANGES_20260301.edi

### Summary
| Metric | Expected |
|---|---|
| Total members | 5 |
| Clean members | 5 |
| Critical errors | 0 |

### Key Verification Points

| Name | INS03 | Key Detail |
|---|---|---|
| ROBINSON, ANGELA P | 021 | Retro addition: elig 20260101, file date 20260301 |
| LEWIS, DONALD G | 024 | Retro termination: end 20260201, elig since 20230601 |
| WALKER, ASHLEY R | 001 | Change: rate category, INS04=EC |
| YOUNG, STEPHANIE L | 001 | Data correction, INS04=EC |
| ALLEN, GEORGE F | 021 | Dual-eligible, DOB 19430825, ABD plan |

---

## File 4: OH_834_EDGE_CASES_20260315.edi

### Summary
| Metric | Expected |
|---|---|
| Total members | 6 |
| Clean members | 6 |
| Warnings | 2 |

### Key Verification Points

| Name | Edge Case | Expected Validation |
|---|---|---|
| GARCIA-LOPEZ, MARIA C | Hyphenated last name | Clean |
| THOMPSON JR, MARCUS D | Suffix in last name field | Clean |
| WASHINGTON, DEBORAH A | Long address (N3*long street*long apt) | Clean |
| HERNANDEZ, SOFIA | Infant, DOB 20260118, no middle name | Clean |
| BAKER, HELEN M | 85+, ODM placeholder addr, XXXXXXXXXX rate cell | OH-VAL-103 + OH-VAL-105 |
| OBRIEN, SEAN P | 3 coverages (HMO+MM+HLT/BH-SUD) | Clean |

---

## File 5: OH_834_ERROR_FILE_20260320.edi

### Summary
| Metric | Expected |
|---|---|
| Total members | 5 |
| Members with critical errors | 2 |
| Clean members | 3 |

### Error Details

| Name/ID | Error | Rule | Severity |
|---|---|---|---|
| 9A0500000001 | Missing NM1 segment | (structural) | No validation rule — demographics empty |
| ERRORTEST, BADID | Medicaid ID `9A050002` is 8 chars | OH-VAL-001 | Critical |
| ERRORTEST, BADDATE | DOB `19901332` (invalid date) | (no specific rule) | Parsed as-is |
| ERRORTEST, NOCOV | No HD segment / no coverages | OH-VAL-005 | Critical |
| GOODRECORD, VALID A | Valid member | — | Clean |

---

## File 6: OH_834_LARGE_BATCH_20260401.edi

### Summary
| Metric | Expected |
|---|---|
| File Type | Full (BGN08=4) |
| Total members | 50 |
| Clean members | 50 |
| All INS03 | 030 (Audit) |
| All HD01 | 030 (Audit) |
| Total coverages | ~88 (70% dual coverage) |
| Validation issues | 0 |

### Verification Points
- All 50 members are audit/compare records (INS03=030, HD01=030)
- All ISA/IEA, GS/GE, ST/SE control numbers match
- SE segment count equals actual segment count
- Mix of CFC, ABD, OHR plan codes
- All Medicaid IDs are 12 chars (format: `9A06NNNNNNNN`)
- All rate cells populated (no XXXXXXXXXX)
- Deterministic: regenerate with `python3 generate_test_files.py` (seed 42)
