# Ohio 834 Parser Design — Preliminary

## Based on ODM Companion Guide v13.1 (20250611)

**Project Saskatchewan — State Onboarding: Ohio**
**Status:** Design Draft
**Date:** February 25, 2026

---

## 1. What This Document Does

This document translates the Ohio Department of Medicaid (ODM) 834 Companion Guide into a concrete parser design for Project Saskatchewan. It maps every Ohio-specific convention discovered in the companion guide to the appropriate layer of the parsing architecture (Tokenizer → Envelope → Loop Structure → Segment Accessor → State Strategy), identifies Ohio's proprietary code sets that must be loaded into the configuration system, and flags areas where the companion guide reveals design decisions that differ from the assumptions in the original 834 example.

---

## 2. Companion Guide Key Findings

### 2.1 Two File Types — This Is Critical

Ohio sends **two distinct 834 file types**, and the system must distinguish them at intake:

| File Type | BGN08 Value | INS03 Values Used | HD01 Values Used | Frequency |
|---|---|---|---|---|
| **Full File** | `4` (Verify) | `030` only | `030` only | Monthly |
| **Changes File** | `2` (Change/Update) | `001`, `021`, `024` | `001`, `002`, `021`, `024`, `025` | Daily (Mon–Fri) |

The Full File is a complete roster snapshot — every member enrolled with a specific MCE at a point in time. The Changes File is incremental. The reconciliation engine needs to know which type it's processing because the Full File (030 = Audit/Compare) has different business semantics than a Changes File transaction.

**Design implication:** The Ohio state strategy must read `BGN08` at the transaction header level and set a file-type flag that affects how every subsequent member record is interpreted.

### 2.2 Transaction Set Structure — One ST/SE Per Provider

The Ohio 834 contains **separate transaction sets (ST–SE) for each 7-digit Medicaid Provider ID**. The Provider ID is in `REF*38` in the transaction header. Within each transaction set, member records are sequenced: ADDs first (`INS03=021`), then CHANGEs (`INS03=001`), then TERMs (`INS03=024`).

**Design implication:** A single Ohio 834 interchange (ISA/IEA) will contain multiple functional groups or transaction sets. The envelope parser will naturally split these. The state strategy must capture the Provider ID from `REF*38` and associate it with every member record in that transaction set.

### 2.3 Correction to the 834 Example Document

The 834_example.md document in this project shows Ohio using:
- `REF*0F` for SSN
- `REF*1L` for Medicaid ID (in Loop 2000)
- `REF*ZZ` for Rate Category (in Loop 2000)

**The actual Ohio Companion Guide says something different:**
- `REF*0F` in Loop 2000 = **Medicaid Recipient ID** (not SSN)
- SSN is in `NM1*IL` element 09 (with qualifier `34` in element 08)
- Rate cell info is in `REF*1L` in **Loop 2300** (not Loop 2000)
- There is no `REF*ZZ` in the Ohio guide at all

This is exactly the kind of discrepancy the layered architecture is designed to absorb — the state strategy is the only component that knows which segment carries which field, and the Ohio strategy must be built from the actual companion guide, not from assumptions.

---

## 3. Layer-by-Layer Design

### 3.1 Layer 1 & 2: Tokenizer and Envelope — No Ohio Customization Needed

The tokenizer and envelope parser are state-agnostic per the architecture. Ohio uses standard delimiters (`*`, `:`, `~`) based on the ISA segment in the companion guide. The envelope parser validates control number matching (ISA/IEA, GS/GE, ST/SE) per the standard rules.

Ohio-specific envelope values to capture for routing and logging:

| Field | Value | Purpose |
|---|---|---|
| ISA06 (Sender ID) | `MMISODJFS` | Identifies file as from Ohio Medicaid |
| ISA08 (Receiver ID) | One of 9 MCE codes | Identifies which MCE this file is for |
| GS02 (App Sender) | `MMISODJFS` | Confirms Ohio origin at functional group level |

The ISA08 receiver codes are:

| Code | MCE |
|---|---|
| `0021920` | AmeriHealth Caritas Ohio, Inc. |
| `0002937` | Anthem Blue Cross Blue Shield |
| `0004202` | Buckeye Community Health Plan |
| `0003150` | CareSource |
| `0021919` | Humana Health Plan of Ohio, Inc. |
| `0007316` | Molina Healthcare of Ohio |
| `0007610` | United Healthcare Community Plan of Ohio, Inc. |
| `0021457` | Aetna Better Health of Ohio Inc. |
| `0021914` | Aetna OhioRISE |

**Note from companion guide (Section 8):** "The 834 is an outbound transaction and there are no associated responses." This means Ohio does **not** expect TA1/999 acknowledgments back. Per FR-111 and FR-112 we still generate them internally for our audit trail, but we do not transmit them to Ohio.

### 3.2 Layer 3: Loop Structure Parser — Standard TR3, No Ohio Override

The loop trigger rules are national TR3 rules and do not change for Ohio. The loop structure parser will produce the standard tree:

```
Transaction Header (BGN, REF, DTP)
├── Loop 1000A (Sponsor: N1*P5)
├── Loop 1000B (Payer: N1*IN)
└── Loop 2000 (Member: INS) ← one per member
    ├── Loop 2100A (Member Name: NM1*IL)
    ├── Loop 2100B (Incorrect Member Name: NM1*70) — used for corrections
    ├── Loop 2100G (Responsible Person: NM1*S1/LR/E1/QD) — Ohio-specific use
    ├── Loop 2300 (Health Coverage: HD) ← multiple per member
    │   └── Loop 2310 (Provider Info: LX/NM1)
    ├── Loop 2320 (Coordination of Benefits: COB)
    │   └── Loop 2330 (COB Related Entity: NM1*IN)
    └── Loop 2700/2710/2750 (Reporting Categories)
```

Ohio uses several loops that many states don't:
- **Loop 2100G** (Responsible Person) — for guardians, foster care placement providers, authorized representatives
- **Loop 2320/2330** (Coordination of Benefits) — for members with Medicare or other coverage
- **Loop 2700/2710/2750** (Reporting Categories) — for living arrangements, pregnancy status, and work requirements

### 3.3 Layer 4: Segment Accessor — No Ohio Customization Needed

The segment accessor is a generic query API. No changes for Ohio.

### 3.4 Layer 5: Ohio State Strategy — This Is Where All the Work Lives

This is the detailed mapping of Ohio companion guide conventions to extraction logic.

---

## 4. Ohio State Strategy: Field Extraction Map

### 4.1 Transaction Header Extraction

| Internal Field | Source Segment | Source Element | Ohio Convention | Notes |
|---|---|---|---|---|
| File Type | `BGN` | Element 08 | `2` = Changes, `4` = Full | Determines interpretation of all INS/HD records |
| File Reference ID | `BGN` | Element 02 | Free-form | Used for source traceability |
| File Effective Date | `DTP*007` | Element 03 | `YYYYMMDD` | |
| Provider ID | `REF*38` | Element 02 | 7-digit Medicaid Provider ID | Each ST/SE is scoped to one provider |
| Sponsor Name | `N1*P5` (1000A) | Element 02 | `OMES` | Ohio changed from "OHIO DEPARTMENT OF MEDICAID" to "OMES" |
| Sponsor Tax ID | `N1*P5` (1000A) | Element 04 | `311334825` | |
| MCE Name | `N1*IN` (1000B) | Element 02 | Name of receiving MCE | |
| MCE Tax ID | `N1*IN` (1000B) | Element 04 | Federal Tax ID of MCE | |

### 4.2 Member Level Detail (Loop 2000) Extraction

| Internal Field | Source Segment | Source Element | Ohio Convention | Notes |
|---|---|---|---|---|
| Is Subscriber | `INS` | Element 01 | Always `Y` | Ohio treats every Medicaid enrollee as a subscriber |
| Relationship | `INS` | Element 02 | Always `18` (Self) | |
| Maintenance Type | `INS` | Element 03 | `001`/`021`/`024`/`030` | See Section 5.1 for interpretation rules |
| Assignment Reason | `INS` | Element 04 | Ohio-proprietary codes | See Section 6.1 for full code set |
| Benefit Status | `INS` | Element 05 | Always `A` (Active) | |
| Employment Status | `INS` | Element 08 | `FT` or `TE` | `FT` = active, `TE` = terminated |
| Date of Death | `INS` | Element 12 | `YYYYMMDD` or empty | Only present when INS04=03 (death), and even then not always |
| **Medicaid ID** | **`REF*0F`** | **Element 02** | **12-char Medicaid Recipient ID** | **CRITICAL: NOT SSN. IDs from IE system start with "9"** |
| Newborn Mother ID | `REF*17` | Element 02 | Format: `C` + Medicaid ID | Only present for newborns |
| Aid Category + Date | `REF*23` | Element 02 | Format: `XXXX CCYYMMDD` | Aid category (3-4 chars) + space + effective date |
| IE Case Number | `REF*3H` | Element 02 | Format: `CCCCCCCCCCXXXX01` | Case number + category + sequence |
| Alternate ID | `REF*6O` | Element 02 | Prior ID (pre-Foster Care) | For claims history linkage |
| Medicare ID | `REF*F6` | Element 02 | Medicare Beneficiary ID or HIC# | Only if member has Medicare |
| County of Eligibility | `REF*DX` | Element 02 | County identifier | |
| Linked/Secondary ID | `REF*Q4` | Element 02 | Inactive linked Medicaid ID | For member identity resolution |
| Redetermination Date | `DTP*300` | Element 03 | `YYYYMMDD` | Eligibility review date |
| Medicaid Begin Date | `DTP*473` | Element 03 | `YYYYMMDD` | PMP-specific eligibility start |
| Medicaid End Date | `DTP*474` | Element 03 | `YYYYMMDD` | PMP-specific eligibility end |

### 4.3 Member Demographics (Loop 2100A) Extraction

| Internal Field | Source Segment | Source Element | Ohio Convention | Notes |
|---|---|---|---|---|
| Last Name | `NM1*IL` | Element 03 | | |
| First Name | `NM1*IL` | Element 04 | | |
| Middle Name | `NM1*IL` | Element 05 | | |
| SSN | `NM1*IL` | Element 09 | NM108 = `34` (SSN qualifier) | SSN is here, NOT in REF*0F |
| Phone Numbers | `PER` | Elements 03–07 | Qualifiers: `TE`, `CP`, `HP`, `WP`, `EM` | Up to 3 contact methods per PER segment |
| Address Line 1 | `N3` | Element 01 | | |
| Address Line 2 | `N3` | Element 02 | | May be empty |
| City | `N4` | Element 01 | | |
| State | `N4` | Element 02 | | |
| ZIP | `N4` | Element 03 | | |
| County Code | `N4` | Element 06 | 2-digit county code | N405 = `CY` (County qualifier) |
| Date of Birth | `DMG` | Element 02 | `YYYYMMDD` | |
| Gender | `DMG` | Element 03 | `F` / `M` | |
| Race/Ethnicity | `DMG` | Element 05-1 | Multiple codes separated by `^` | Ohio sends multiple race codes using the ISA11 repetition separator |
| Out-of-Country Address | `N3`/`N4` | | Uses ODM HQ address as placeholder | If member is outside US, address is "50 W. Town St, Suite 400, Columbus, OH 43215" |

**Race/Ethnicity Parsing Note:** Ohio sends composite race/ethnicity data like `A^B^C` where `^` is the repetition separator from ISA11. The parser must split on this character and store multiple race codes per member.

### 4.4 Responsible Person (Loop 2100G) Extraction

Ohio uses this loop for guardians, foster placement providers, and authorized representatives. Many states omit this loop entirely.

| Internal Field | Source Segment | Source Element | Ohio Convention |
|---|---|---|---|
| Responsible Person Type | `NM1` | Element 01 | `S1`=Parent, `LR`=Personal Rep, `E1`=Placement Provider, `QD`=Authorized Rep |
| Responsible Person Name | `NM1` | Elements 03–05 | Or organization name if individual not available |
| Contact Info | `PER` | Elements 03–07 | Same qualifier set as member PER |
| Address | `N3`/`N4` | | Same out-of-country convention as member |

### 4.5 Health Coverage (Loop 2300) Extraction — The Complex Part

Ohio uses Loop 2300 for much more than basic managed care enrollment. A single member can have **many** 2300 loops representing different coverage types. The companion guide states the Changes file can have up to 10 changes per day per coverage per recipient.

| Internal Field | Source Segment | Source Element | Ohio Convention | Notes |
|---|---|---|---|---|
| Coverage Maint Type | `HD` | Element 01 | `001`/`002`/`021`/`024`/`025`/`030` | HD01 has a broader set of codes than INS03 (includes `002` Delete and `025` Reinstatement) |
| Insurance Line Code | `HD` | Element 03 | Ohio-proprietary set | See Section 6.2 |
| Plan Coverage Desc | `HD` | Element 04 | Ohio-proprietary set | See Section 6.3 — this is an extensive code list |
| Benefit Begin Date | `DTP*348` | Element 03 | `YYYYMMDD` | |
| Benefit End Date | `DTP*349` | Element 03 | `YYYYMMDD` | |
| Patient Liability Amt | `AMT*D2` | Element 02 | Monetary amount | Only for Patient Liability coverage (HD03=`MM`) |
| **Rate Cell Indicator** | **`REF*1L`** | **Element 02** | **Composite of program/region/gender/age** | **CRITICAL: Rate cell is HERE in Loop 2300, not in Loop 2000** |

**Rate Cell Special Cases:**
- `XXXXXXXXXX` (10 X's) = no unique rate cell exists (term date is in the past, or span is set to history)
- IE-system members: 6-character rate cell indicator
- ICDS members: 7 or 8-character rate cell indicator

**Coverage Type Determination:** The combination of `HD03` (Insurance Line Code) and `HD04` (Plan Coverage Description) together define the type of coverage. The Ohio strategy must interpret this pair as a unit:

```
HD03=HMO + HD04=ABD  → Aged/Blind/Disabled managed care enrollment
HD03=HMO + HD04=CFC  → Covered Families and Children managed care enrollment
HD03=HMO + HD04=OHR  → OhioRISE enrollment
HD03=AG  + HD04=951  → Special Condition: Exclude from Managed Care
HD03=AH  + HD04=WVR-* → Waiver enrollment
HD03=LTC + HD04=NH-*  → Nursing home span
...and so on
```

### 4.6 Provider Information (Loop 2310) Extraction

| Internal Field | Source Segment | Source Element | Ohio Convention |
|---|---|---|---|
| Provider Type | `NM1` | Element 01 | `FA`=Facility, `QA`=Pharmacy, `Y2`=MCO |
| Provider Name | `NM1` | Element 03 | Organization name (NM102 always = `2`, Non-Person) |
| Provider ID Type | `NM1` | Element 08 | `XX`=NPI, `SV`=Medicaid Provider ID or H Number |
| Provider ID | `NM1` | Element 09 | NPI or Medicaid Provider ID |
| Provider Phone | `PER` | Element 04 | TE qualifier |

### 4.7 Coordination of Benefits (Loop 2320/2330) Extraction

| Internal Field | Source Segment | Source Element | Ohio Convention |
|---|---|---|---|
| Payer Responsibility | `COB` | Element 01 | `P` = Primary |
| COB Code | `COB` | Element 03 | `1` = Coordination of Benefits |
| Other Insurance Group# | `REF*6P` | Element 02 | |
| Other Insurance SSN | `REF*SY` | Element 02 | |
| Insurer Name | `NM1*IN` (2330) | Element 03 | |

### 4.8 Reporting Categories (Loop 2750) Extraction

This is a distinctly Ohio feature. Three types of reporting categories are sent:

| Category | N1 Element 02 | REF01 | REF02 Content | DTP03 |
|---|---|---|---|---|
| Living Arrangement | `LIVING ARRANGEMENT` | `LU` | 2-char code (see Section 6.5) | Start date or date range |
| Pregnancy | `PREGNANT` | `ZZ` | `ESTIMATED DUE DATE`, `END DATE`, or `NO DATE AVAILABLE` | The date value |
| Work Requirement | `WORK REQUIREMENT - MANDATORY` | `XX1` | `WORK REQUIREMENT - MANDATORY` | Effective date |

**DTP format handling:** When `DTP02=D8`, element 03 is a single date (`CCYYMMDD`). When `DTP02=RD8`, element 03 is a date range (`CCYYMMDD-CCYYMMDD`). The parser must handle both.

---

## 5. Ohio Business Logic Rules

### 5.1 Maintenance Type Interpretation

The meaning of maintenance type codes depends on whether we're processing a Full File or Changes File:

| INS03 | In Changes File (BGN08=2) | In Full File (BGN08=4) |
|---|---|---|
| `021` | New enrollment — add this member | N/A (not used in Full File) |
| `001` | Change to existing member | N/A (not used in Full File) |
| `024` | Termination/cancellation | N/A (not used in Full File) |
| `030` | N/A (not used in Changes File) | Audit/Compare — this is the current state of the member |

**Companion guide warning:** "The MCE should not assume that new membership results in the automatic termination of prior coverage. There will be multiple member level details (Loop 2000) to indicate movement from the old to the new coverage."

This means when processing a Changes File `021` (Addition), the system must NOT automatically close prior enrollment spans. Ohio will send a separate `024` (Termination) record for the old coverage.

**Companion guide warning:** "Membership spans should not be used to process changes (INS01 = 001)."

This means `001` Change records should update demographic or status fields but should NOT be interpreted as modifying enrollment date spans.

### 5.2 HD01 Maintenance Type in Loop 2300

Loop 2300 has its own maintenance type in `HD01`, which can differ from `INS03`:

- `002` (Delete) and `025` (Reinstatement) appear **only** in `HD01`, never in `INS03`
- For supplemental coverages (waivers, special conditions, patient liability, etc.), the Changes File uses `001` for any span that partially or completely overlaps plan enrollment
- The Full File uses `030` for these same coverages
- These supplemental programs will **never** use `002`, `021`, or `024`

### 5.3 Open-Ended Enrollment

The companion guide does not mention `99991231` as a sentinel value (this was an assumption in the 834_example.md). Looking at the actual guide, Ohio uses `DTP*349` (Benefit End) with a real date. Open-ended enrollment would simply mean the `DTP*349` date is in the future, or the absence of a termination record. The Ohio strategy should **not** apply the `99991231` convention without further verification from actual test files.

### 5.4 Medicaid ID Format

- All ODM-assigned IDs are **12 characters** in length
- IDs originating from the IE (eligibility) system have `9` as the first character
- The system should store the full 12-character ID and flag IE-origin IDs

### 5.5 Date of Death Handling

When `INS04=03` (death assignment reason):
- The Medicaid end date in `DTP*474` is the date of death
- `INS12` (Date Time Period in the INS segment) may also contain the death date from the eligibility system
- However, the guide warns: "A death reported by MCE (INS04=03) may not always have a date in this element"
- The Ohio strategy should check both locations and prefer `INS12` when present, fall back to `DTP*474`

### 5.6 Address for Out-of-Country Members

If a member's address is outside the US, Ohio substitutes:
```
50 W. Town St, Suite 400
Columbus, OH 43215
```
The Ohio strategy should detect this specific address pattern and flag the member as having a non-US address rather than storing the ODM headquarters as the member's actual address.

---

## 6. Ohio Code Sets — Configuration Artifacts

These code sets must be loaded into the state configuration management system (FR-612) as discrete, versioned artifacts.

### 6.1 Assignment Reason Codes (INS04)

**Add (Start) Reasons:**

| Code | Description | Programs |
|---|---|---|
| `28` | Auto-enrollment: same MCE within previous 3 months, or newborn on mother's MCE | ABD, MAGI, MyCare Ohio |
| `14` | Assigned by enrollment broker (member did not select) | ABD, MAGI, MyCare Ohio |
| `15` | Enrollment addition by ODM managed care staff | ABD, MAGI, MyCare Ohio |
| `16` | Member selected MCE through enrollment broker, or ODM staff added MyCare Ohio enrollment | ABD, MAGI, MyCare Ohio |
| `17` | Retroactive re-enrollment (up to 3 months) for restored eligibility | ABD, MAGI, MyCare Ohio |
| `AJ` | Assigned effective first day of current month per Day 1 rules | ABD, MAGI |

**Change & Delete (Stop) Reasons:**

| Code | Description | Programs |
|---|---|---|
| `1` | Lost eligibility (did not complete reapplication) or no longer eligible | ABD, MAGI, MyCare Ohio |
| `2` | NF, IID, or HCBS Waiver Level of Care | MyCare Ohio |
| `3` | Date of death | ABD, MAGI, MyCare Ohio |
| `5` | 12-digit billing ID not active ("secondary" ID) | ABD, MAGI, MyCare Ohio |
| `6` | Disenrollment by ODM managed care staff | ABD, MAGI, MyCare Ohio |
| `7` | No longer Medicaid eligible | ABD, MAGI, MyCare Ohio |
| `9` | Incarcerated | ABD, MAGI, MyCare Ohio |
| `10` | No longer in MCE service area (moved out of Ohio) | ABD, MAGI, MyCare Ohio |
| `11` | Exempt by ODM Just Cause Determination | ABD, MAGI, MyCare Ohio |
| `18` | Voluntary MCE change | ABD, MAGI, MyCare Ohio |
| `29` | Enrolled in PACE (MyCare) or ODM staff action (ABD/MAGI) | MyCare Ohio, ABD, MAGI |
| `37` | Invalid living arrangement code for managed care | ABD, MAGI, MyCare Ohio |
| `38` | Special condition excluding from managed care | ABD, MAGI, MyCare Ohio |
| `40` | Aid category not eligible for managed care program | ABD, MAGI, MyCare Ohio |
| `43` | Lost Medicare A and/or B | MyCare Ohio |
| `AA` | Mutually exclusive benefit plan (e.g., PACE) | ABD, MAGI, MyCare Ohio |
| `AB` | OhioRISE disenrollment | |
| `AD` | Age invalid for aid category (prevents rate cell determination) | MyCare Ohio, MAGI Extension |
| `EC` | Third Party Liability coverage | MyCare Ohio |
| `XT` | Enrolled in Medicare Part A and/or B | ABD, MAGI |

**System Reasons:**

| Code | Description |
|---|---|
| `25` | System default for `001` Change transactions (change in identifying data) |
| `AI` | System default (reason not in list — contact ODM) |
| `XN` | System default — sent only on Full File |

### 6.2 Insurance Line Codes (HD03)

| Code | Description | Coverage Type |
|---|---|---|
| `HMO` | Health Maintenance Organization | Primary managed care enrollment |
| `AG` | Preventative Care/Wellness | Special Conditions |
| `AH` | 24 Hour Care | Waivers |
| `AJ` | Medicare Risk | Medicare |
| `AK` | Mental Health | SRSP, ACT, IHBT, BHCC |
| `EPO` | Exclusive Provider Organization | Restricted Medicaid |
| `HLT` | Health | Physician CSP, CARA |
| `MM` | Major Medical | Patient Liability |
| `PDG` | Prescription Drug | Pharmacy CSP |
| `POS` | Point of Service | Money Follows Person |
| `LTC` | Long-Term Care | Nursing Homes, Hospice |
| `LTD` | Long-Term Disability | Supplemental Income |

### 6.3 Plan Coverage Description Codes (HD04)

This is Ohio's most extensive proprietary code set. Organized by coverage category:

**Managed Care:**
`ABD`, `CFC`, `OHR`

**Behavioral Health / Treatment:**
`ACT`, `BH-SUD`, `BH-SPMI`, `CARA`, `IHBT`, `SRSP`

**Medicare:**
`MEDICARE-A`, `MEDICARE-B`, `MEDICARE-C`, `MEDICARE-D`

**Waivers:**
`WVR-A1`, `WVR-A4`, `WVR-A`, `WVR-9`, `WVR-P3`, `WVR-ICDS`, `WVR-10`, `WVR-P`, `WVR-B`, `WVR-0`, `WVR-OR`

**Nursing / Long-Term Care:**
`NH-CRISE`, `NH-MCE`, `NH-MCADMIT`, `HSBP`

**Money Follows Person:**
`MFP-N`, `MFP-Y`

**Patient Liability:**
`PL-F`, `PL-C`, `PL-G`, `PL-H`, `PL-I`, `PL-N`, `PL-R`, `PL-W`, `PL-P`

**Supplemental Income:**
`SI-UNE`

**Special Conditions — Exclusionary:**
`951`, `AGE`, `BCM`, `CIC`, `DDR`, `DDW`, `DEF`, `DOD`, `DVS`, `E01`, `ELG`, `GHO`, `IAH`, `IDD`, `INC`, `IVE`, `JC`, `LIS`, `MUL`, `N4E`, `NUR`, `OAC`, `PBP`, `RDS`

**Special Conditions — Informational:**
`CC1`, `CC2`, `I01`, `IMD`, `O42`, `O51`, `O54`, `OOD`, `OOH`, `OOM`, `OOR`, `OOV`, `ORW`, `PRE`

### 6.4 Race/Ethnicity Codes (DMG05-1)

| Code | Description |
|---|---|
| `7` | Not provided |
| `A` | Asian or Pacific Islander |
| `B` | Black |
| `C` | Caucasian |
| `D` | Subcontinent Asian American |
| `E` | Other Race or Ethnicity |
| `F` | Asian Pacific American |
| `G` | Native American |
| `H` | Hispanic |
| `I` | American Indian or Alaskan Native |
| `J` | Native Hawaiian |
| `N` | Black (Non-Hispanic) |
| `O` | White (Non-Hispanic) |
| `P` | Pacific Islander |

### 6.5 Living Arrangement Codes (REF*LU in Loop 2750)

78 distinct codes. A sample:

| Code | Description |
|---|---|
| `01` | Independent (Home/Apart/Trlr) |
| `02` | Public Institution |
| `09` | Nursing Home/Group Home |
| `10` | Nursing Home (LTCF) |
| `13` | Homeless |
| `22` | Death |
| `24` | Under 21 Years, In Custody |
| `FC` | Foster Care |
| `KG` | Kinship Guardianship Assistance Program |
| ... | (74 additional codes — full list in companion guide Appendix 11.3) |

### 6.6 MCE Receiver ID Mapping

| ISA08 Code | MCE Name |
|---|---|
| `0021920` | AmeriHealth Caritas Ohio |
| `0002937` | Anthem Blue Cross Blue Shield |
| `0004202` | Buckeye Community Health Plan |
| `0003150` | CareSource |
| `0021919` | Humana Health Plan of Ohio |
| `0007316` | Molina Healthcare of Ohio |
| `0007610` | United Healthcare Community Plan of Ohio |
| `0021457` | Aetna Better Health of Ohio |
| `0021914` | Aetna OhioRISE |

---

## 7. Ohio State Strategy — Pseudocode

```
class OhioStateStrategy implements IStateStrategy:

    function parseTransactionHeader(headerSegments, loop1000A, loop1000B):
        bgn = headerSegments.getSegment("BGN")
        fileType = bgn.element(08)  // "2" = Changes, "4" = Full
        fileRefId = bgn.element(02)

        providerIdRef = headerSegments.getSegment("REF", qualifierElement=01, qualifierValue="38")
        providerId = providerIdRef.element(02)  // 7-digit Medicaid Provider ID

        effectiveDateDtp = headerSegments.getSegment("DTP", qualifierElement=01, qualifierValue="007")
        fileEffectiveDate = parseDate(effectiveDateDtp.element(03))

        sponsorName = loop1000A.getSegment("N1").element(02)      // "OMES"
        sponsorTaxId = loop1000A.getSegment("N1").element(04)     // "311334825"
        mceName = loop1000B.getSegment("N1").element(02)
        mceTaxId = loop1000B.getSegment("N1").element(04)

        return TransactionContext {
            state = "OH",
            fileType,         // FULL or CHANGES
            providerId,
            fileRefId,
            fileEffectiveDate,
            sponsorName, sponsorTaxId,
            mceName, mceTaxId
        }

    function parseMember(loop2000, txContext):
        ins = loop2000.getSegment("INS")
        maintenanceType = resolveMaintenanceType(ins.element(03), txContext.fileType)
        assignmentReason = resolveAssignmentReason(ins.element(04))
        employmentStatus = ins.element(08)   // "FT" or "TE"
        dateOfDeath = ins.element(12)        // may be empty

        // ── Medicaid ID (REF*0F) — THIS IS NOT SSN ──
        medicaidId = loop2000.getElementValue("REF", 0, "0F", 1)

        // ── Supplemental Identifiers ──
        newbornMotherId = loop2000.getElementValue("REF", 0, "17", 1)  // nullable
        aidCategoryRef = loop2000.getElementValue("REF", 0, "23", 1)   // nullable
        ieCaseNumber = loop2000.getElementValue("REF", 0, "3H", 1)     // nullable
        alternateId = loop2000.getElementValue("REF", 0, "6O", 1)      // nullable
        medicareId = loop2000.getElementValue("REF", 0, "F6", 1)       // nullable
        countyOfEligibility = loop2000.getElementValue("REF", 0, "DX", 1)
        linkedSecondaryId = loop2000.getElementValue("REF", 0, "Q4", 1) // nullable

        // ── Parse Aid Category from REF*23 ──
        aidCategory = null
        aidCategoryEffDate = null
        if aidCategoryRef is not null:
            parts = aidCategoryRef.split(" ")  // "XXXX CCYYMMDD"
            aidCategory = parts[0]
            aidCategoryEffDate = parseDate(parts[1])

        // ── Member-Level Dates ──
        redeterminationDate = loop2000.getElementValue("DTP", 0, "300", 2)
        medicaidBeginDate = loop2000.getElementValue("DTP", 0, "473", 2)
        medicaidEndDate = loop2000.getElementValue("DTP", 0, "474", 2)

        // ── Demographics (Loop 2100A) ──
        loop2100A = loop2000.getChildLoops("2100A").single()
        nm1 = loop2100A.getSegment("NM1")
        lastName = nm1.element(03)
        firstName = nm1.element(04)
        middleName = nm1.element(05)
        ssn = nm1.element(09)   // SSN is HERE, not in REF*0F

        dmg = loop2100A.getSegment("DMG")
        dob = parseDate(dmg.element(02))
        gender = dmg.element(03)
        raceEthnicityCodes = parseRaceEthnicity(dmg.element(05))  // split on "^"

        n4 = loop2100A.getSegment("N4")
        countyCode = null
        if n4.element(05) == "CY":
            countyCode = n4.element(06)  // 2-digit county code

        address = parseAddress(loop2100A)
        address = detectOdmPlaceholderAddress(address)  // flag if out-of-country

        // ── Contact Information ──
        contacts = parseContacts(loop2100A)  // PER segment with TE/CP/HP/WP/EM

        // ── Health Coverages (Loop 2300 — multiple) ──
        coverages = []
        for each loop2300 in loop2000.getChildLoops("2300"):
            coverages.append(parseCoverage(loop2300, txContext))

        // ── Responsible Person (Loop 2100G — optional) ──
        responsiblePerson = null
        loop2100Gs = loop2000.getChildLoops("2100G")
        if loop2100Gs is not empty:
            responsiblePerson = parseResponsiblePerson(loop2100Gs.first())

        // ── Coordination of Benefits (Loop 2320 — optional) ──
        cobRecords = []
        for each loop2320 in loop2000.getChildLoops("2320"):
            cobRecords.append(parseCOB(loop2320))

        // ── Reporting Categories (Loop 2750 — optional, multiple) ──
        reportingCategories = parseReportingCategories(loop2000)

        return OhioEnrollmentRecord {
            // ... all fields assembled into normalized internal model
            // with Ohio-specific extensions stored in flexible fields
        }

    function parseCoverage(loop2300, txContext):
        hd = loop2300.getSegment("HD")
        coverageMaintenanceType = hd.element(01)  // may differ from INS03
        insuranceLine = hd.element(03)
        planCoverageDesc = hd.element(04)

        benefitBegin = loop2300.getElementValue("DTP", 0, "348", 2)
        benefitEnd = loop2300.getElementValue("DTP", 0, "349", 2)

        // ── Rate Cell — THIS IS IN LOOP 2300, NOT LOOP 2000 ──
        rateCellIndicator = loop2300.getElementValue("REF", 0, "1L", 1)
        if rateCellIndicator == "XXXXXXXXXX":
            rateCellIndicator = null  // no valid rate cell
            rateCellMissing = true

        // ── Patient Liability (only for HD03=MM) ──
        patientLiabilityAmount = null
        if insuranceLine == "MM":
            patientLiabilityAmount = loop2300.getElementValue("AMT", 0, "D2", 1)

        // ── Provider Info (Loop 2310 — optional) ──
        provider = null
        loop2310s = loop2300.getChildLoops("2310")
        if loop2310s is not empty:
            provider = parseProvider(loop2310s.first())

        coverageType = resolveCoverageType(insuranceLine, planCoverageDesc)

        return CoverageRecord {
            coverageMaintenanceType,
            coverageType,
            insuranceLine,
            planCoverageDesc,
            benefitBegin, benefitEnd,
            rateCellIndicator,
            rateCellMissing,
            patientLiabilityAmount,
            provider,
        }
```

---

## 8. Validation Rules — Ohio-Specific (FR-212)

These rules supplement the national TR3 validation and are configured as the Ohio validation rule set.

### 8.1 Critical Errors (Prevent Record Loading)

| Rule | Description |
|---|---|
| OH-VAL-001 | `REF*0F` (Medicaid ID) must be present and exactly 12 characters |
| OH-VAL-002 | `INS03` must be one of `001`, `021`, `024`, `030` |
| OH-VAL-003 | If BGN08=`4` (Full File), all INS03 values must be `030` |
| OH-VAL-004 | If BGN08=`2` (Changes File), INS03 must not be `030` |
| OH-VAL-005 | At least one Loop 2300 (HD segment) must be present per member |
| OH-VAL-006 | `DTP*348` (Benefit Begin) must be present in every Loop 2300 |

### 8.2 Warning Rules (Record Loaded with Caveats)

| Rule | Description |
|---|---|
| OH-VAL-101 | `INS04` (Assignment Reason) not in known Ohio code set — log for review |
| OH-VAL-102 | `HD04` (Plan Coverage Desc) not in known Ohio code set — log for review |
| OH-VAL-103 | Rate cell indicator is `XXXXXXXXXX` — flag for reconciliation review |
| OH-VAL-104 | `INS04=03` (death) but `INS12` (death date) is empty — incomplete death record |
| OH-VAL-105 | Address matches ODM HQ placeholder — member has non-US address |
| OH-VAL-106 | `DTP*349` (Benefit End) is absent — open-ended coverage (may be expected for Full File) |
| OH-VAL-107 | Multiple `REF*Q4` (linked IDs) present — complex member identity case |

### 8.3 Informational Rules

| Rule | Description |
|---|---|
| OH-VAL-201 | Member has Medicare coverage (REF*F6 present) — dual-eligible member |
| OH-VAL-202 | Member has Alternate ID (REF*6O present) — former foster care placement |
| OH-VAL-203 | Living arrangement indicates institutional setting (codes 02, 09, 10, 19, 20, 26, etc.) |

---

## 9. Reconciliation Impact

The rate cell indicator in `REF*1L` (Loop 2300) is the bridge between 834 enrollment and 820 capitation. The reconciliation engine will need to:

1. Extract the rate cell from **Loop 2300** (not Loop 2000) for each HMO coverage record
2. Handle the `XXXXXXXXXX` missing-rate-cell case by logging these members as unreconcilable for capitation matching
3. Account for the different rate cell lengths: standard (10 chars), IE (6 chars), ICDS (7-8 chars)
4. Match rate cells against the Ohio 820 capitation data to detect mismatches (FR-504)

---

## 10. Open Questions for Ohio Onboarding

| # | Question | Impact |
|---|---|---|
| 1 | Can we obtain Ohio test files (both Full and Changes)? | Required to validate all parsing logic against real data |
| 2 | What is the exact format of the rate cell indicator composite? | Need to understand the program/region/gender/age encoding for rate table mapping |
| 3 | Does Ohio provide a reconciliation file, and in what format? | Determines whether three-way matching (FR-511) is possible |
| 4 | What is the delivery cadence — is the Full File always on a specific day? | Affects processing schedule configuration |
| 5 | The 834_example.md assumed REF*ZZ for rate category and REF*0F for SSN — are there other states where these assumptions hold, or should we treat every state's field mapping as unique from scratch? | Architecture validation |
| 6 | The guide mentions "OhioRISE" as a distinct managed care program — does it have separate 820 capitation files or is it combined? | Affects 820 parser design |
| 7 | How should we normalize the 78 living arrangement codes for the internal data model? | Data model extensibility |
