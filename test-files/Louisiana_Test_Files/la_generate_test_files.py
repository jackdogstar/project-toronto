#!/usr/bin/env python3
"""
Generate Louisiana Medicaid EDI 834 Test Files for Project Saskatchewan.

All files follow ASC X12N 005010X220A1 with Louisiana Companion Guide conventions.
Key differences from Ohio are documented in README.md.

Louisiana conventions:
  - Medicaid ID in REF*0F (Ohio uses REF*0F for SSN)
  - SSN only in NM109 (no separate REF segment for SSN)
  - Health Region in REF*1L (Ohio uses REF*1L for Medicaid ID)
  - Eligibility Group in REF*ZZ (Ohio uses REF*ZZ for rate category)
  - NO rate category in the 834 (only in 820)
  - State confirmation number in REF*CE
  - Single Loop 2300 per member (Ohio uses multiple)
  - Open-ended enrollment = DTP*349 ABSENT (Ohio uses 99991231 sentinel)
  - Plan assignment in REF*N6 (Ohio uses REF*17)
"""

import os
import random
import hashlib

OUTPUT_DIR = "/home/claude/la_edi_test_files"

# ─── Louisiana-specific constants ───────────────────────────────────────

SENDER_ID   = "LADHH          "  # 15 chars, padded — LA Dept of Health
RECEIVER_ID = "MCOPLAN        "  # 15 chars, padded
SPONSOR_NAME = "LOUISIANA DEPARTMENT OF HEALTH"
SPONSOR_FI   = "726014583"
MCO_NAME     = "ACME HEALTH PLAN MCO"
MCO_FI       = "621234567"

# Louisiana eligibility groups
ELIG_GROUPS = {
    "LDE-TANF-001": "TANF Parent/Caretaker",
    "LDE-TANF-002": "TANF Child",
    "LDE-TANF-003": "TANF Infant Under 1",
    "LDE-SSI-001":  "SSI Adult",
    "LDE-SSI-002":  "SSI Child",
    "LDE-ABD-001":  "Aged",
    "LDE-ABD-002":  "Blind/Disabled Adult",
    "LDE-EXP-001":  "Expansion Adult (XIX)",
    "LDE-EXP-002":  "Expansion Adult (MAGI)",
    "LDE-CHIP-001": "LaCHIP Children",
    "LDE-CHIP-002": "LaCHIP Affordable Plan",
    "LDE-DUAL-001": "Full Dual Eligible",
    "LDE-DUAL-002": "Partial Dual Eligible",
}

# Eligibility group → plan code mapping
ELIG_TO_PLAN = {
    "LDE-TANF-001": "BAYOU-STD",
    "LDE-TANF-002": "BAYOU-STD",
    "LDE-TANF-003": "BAYOU-STD",
    "LDE-SSI-001":  "BAYOU-SSI",
    "LDE-SSI-002":  "BAYOU-SSI",
    "LDE-ABD-001":  "BAYOU-ABD",
    "LDE-ABD-002":  "BAYOU-ABD",
    "LDE-EXP-001":  "BAYOU-STD",
    "LDE-EXP-002":  "BAYOU-STD",
    "LDE-CHIP-001": "BAYOU-STD",
    "LDE-CHIP-002": "BAYOU-STD",
    "LDE-DUAL-001": "BAYOU-DUAL",
    "LDE-DUAL-002": "BAYOU-DUAL",
}

# Louisiana health regions with cities and ZIP codes
LA_REGIONS = {
    "REGION-1": [
        ("NEW ORLEANS",   "LA", "70112"),
        ("NEW ORLEANS",   "LA", "70119"),
        ("METAIRIE",      "LA", "70001"),
    ],
    "REGION-2": [
        ("BATON ROUGE",   "LA", "70801"),
        ("BATON ROUGE",   "LA", "70816"),
        ("GONZALES",      "LA", "70737"),
    ],
    "REGION-3": [
        ("HOUMA",         "LA", "70360"),
        ("THIBODAUX",     "LA", "70301"),
    ],
    "REGION-4": [
        ("LAFAYETTE",     "LA", "70501"),
        ("NEW IBERIA",    "LA", "70560"),
    ],
    "REGION-5": [
        ("LAKE CHARLES",  "LA", "70601"),
        ("SULPHUR",       "LA", "70663"),
    ],
    "REGION-6": [
        ("ALEXANDRIA",    "LA", "71301"),
        ("PINEVILLE",     "LA", "71360"),
    ],
    "REGION-7": [
        ("SHREVEPORT",    "LA", "71101"),
        ("BOSSIER CITY",  "LA", "71111"),
    ],
    "REGION-8": [
        ("MONROE",        "LA", "71201"),
        ("WEST MONROE",   "LA", "71291"),
    ],
    "REGION-9": [
        ("HAMMOND",       "LA", "70401"),
        ("COVINGTON",     "LA", "70433"),
    ],
}

ALL_LOCATIONS = []
for locs in LA_REGIONS.values():
    ALL_LOCATIONS.extend(locs)

REGION_FOR_CITY = {}
for region, locs in LA_REGIONS.items():
    for city, st, zp in locs:
        REGION_FOR_CITY[(city, zp)] = region

STREETS = [
    "1200 BOURBON STREET", "3456 MAGAZINE STREET", "789 ST CHARLES AVENUE",
    "2100 CANAL STREET", "450 ESPLANADE AVENUE", "6789 TCHOUPITOULAS STREET",
    "1515 VETERANS MEMORIAL BLVD", "3030 AIRLINE HIGHWAY", "890 GOVERNMENT STREET",
    "2222 PERKINS ROAD", "4444 HIGHLAND ROAD", "100 MAIN STREET",
    "555 BAYOU LANE", "1717 RIVER ROAD", "2828 GREENWELL SPRINGS ROAD",
    "600 TEXAS STREET", "1400 FAIRFIELD AVENUE", "950 PIERREMONT ROAD",
    "3100 NORTH STREET", "775 DESIARD STREET",
]

APTS = [
    None, None, None, None, None, None,
    "APT 3", "APT 14B", "UNIT 6", "SUITE 100", "APT 201",
]

LAST_NAMES = [
    "BOUDREAUX", "THIBODAUX", "LANDRY", "LEBLANC", "GUIDRY",
    "BROUSSARD", "RICHARD", "TRAHAN", "ARCENEAUX", "HEBERT",
    "FONTENOT", "COMEAUX", "MELANCON", "DUPRE", "MOUTON",
    "CASTILLE", "DOUCET", "ROMERO", "SMITH", "JOHNSON",
    "WILLIAMS", "JONES", "BROWN", "DAVIS", "MILLER",
    "WILSON", "MOORE", "TAYLOR", "ANDERSON", "THOMAS",
    "JACKSON", "WHITE", "HARRIS", "MARTIN", "GARCIA",
    "ROBINSON", "CLARK", "LEWIS", "LEE", "WALKER",
    "HALL", "ALLEN", "YOUNG", "KING", "WRIGHT",
    "LOPEZ", "GREEN", "ADAMS", "BAKER", "NELSON",
]

FIRST_NAMES_F = [
    "MARIE", "CLAIRE", "MONIQUE", "SUZANNE", "YVETTE",
    "CELESTE", "CAMILLE", "RENEE", "THERESA", "PATRICIA",
    "JENNIFER", "ASHLEY", "JESSICA", "SARAH", "AMANDA",
    "BRENDA", "DONNA", "LINDA", "MARGARET", "EMILY",
    "GABRIELLE", "DANIELLE", "ANNETTE", "SIMONE", "COLETTE",
]

FIRST_NAMES_M = [
    "JEAN", "PIERRE", "ANDRE", "RENE", "PHILIPPE",
    "CLAUDE", "JACQUES", "ANTOINE", "LOUIS", "CHARLES",
    "JAMES", "JOHN", "ROBERT", "MICHAEL", "DAVID",
    "WILLIAM", "RICHARD", "JOSEPH", "THOMAS", "MARK",
    "ETIENNE", "MARCEL", "GASTON", "LUCIEN", "EMILE",
]

MIDDLE_INITIALS = list("ABCDEFGHJKLMNPRSTW") + [None, None, None, None]

# Counter for confirmation numbers
_conf_counter = 0

def next_confirmation(date_str):
    global _conf_counter
    _conf_counter += 1
    return f"LACONF{date_str}{_conf_counter:04d}"


def isa_segment(date_yymmdd, control_num):
    """ISA segment — always exactly 106 characters including terminator."""
    return (
        f"ISA*00*          *00*          "
        f"*ZZ*{SENDER_ID}*ZZ*{RECEIVER_ID}"
        f"*{date_yymmdd}*0800*^*00501*{control_num:09d}*0*P*:~"
    )


def gs_segment(date_ccyymmdd, group_control):
    return f"GS*BE*LADHH*MCOPLAN*{date_ccyymmdd}*0800*{group_control}*X*005010X220A1~"


def ge_segment(tx_count, group_control):
    return f"GE*{tx_count}*{group_control}~"


def iea_segment(group_count, control_num):
    return f"IEA*{group_count}*{control_num:09d}~"


def build_header(bgn_ref, date_ccyymmdd, bgn_purpose="00"):
    """Transaction header: BGN, REF, DTP, N1*P5, N1*IN."""
    segs = []
    segs.append(f"BGN*{bgn_purpose}*{bgn_ref}*{date_ccyymmdd}*0800****2~")
    segs.append(f"REF*38*LA-MCO-CONTRACT-2025-001~")
    segs.append(f"DTP*007*D8*{date_ccyymmdd}~")
    segs.append(f"N1*P5*{SPONSOR_NAME}*FI*{SPONSOR_FI}~")
    segs.append(f"N1*IN*{MCO_NAME}*FI*{MCO_FI}~")
    return segs


def build_member(*, maint_type, ssn, medicaid_id, elig_group,
                 region, elig_date, last_name, first_name, middle, dob, gender,
                 street, apt, city, state, zip_code,
                 plan_code=None, coverage_end=None,
                 network_region=None, conf_date="20260201",
                 is_subscriber="Y"):
    """
    Build a complete Louisiana member block.

    Key Louisiana conventions:
      - REF*0F = Medicaid ID (NOT SSN)
      - REF*1L = Health Region
      - REF*ZZ = Eligibility Group (NOT rate category)
      - REF*CE = State confirmation number
      - Single Loop 2300 with HLT = full benefit package
      - DTP*349 ABSENT for open-ended enrollment
      - REF*N6 in Loop 2300 for network assignment (NOT REF*17)
    """
    segs = []

    # Resolve plan code from eligibility group if not specified
    if plan_code is None:
        plan_code = ELIG_TO_PLAN.get(elig_group, "BAYOU-STD")

    # Network region defaults to health region number
    if network_region is None:
        network_region = region.replace("REGION-", "NET-")

    conf_num = next_confirmation(conf_date)

    # ── Loop 2000: Member Level Detail ──
    segs.append(f"INS*{is_subscriber}*18*{maint_type}*28*A***FT~")
    # Louisiana: REF*0F = Medicaid ID (Ohio uses this for SSN!)
    segs.append(f"REF*0F*{medicaid_id}~")
    # Louisiana: REF*1L = Health Region (Ohio uses this for Medicaid ID!)
    segs.append(f"REF*1L*{region}~")
    # Louisiana: REF*ZZ = Eligibility Group (Ohio uses this for Rate Category!)
    segs.append(f"REF*ZZ*{elig_group}~")
    # Louisiana-specific: REF*CE = State confirmation number
    segs.append(f"REF*CE*{conf_num}~")
    segs.append(f"DTP*336*D8*{elig_date}~")

    # ── Loop 2100A: Member Name / Demographics ──
    # Louisiana: SSN only lives in NM109 (qualifier 34), no separate REF*0F for SSN
    mi_part = f"*{middle}" if middle else "*"
    segs.append(f"NM1*IL*1*{last_name}*{first_name}{mi_part}***34*{ssn}~")
    segs.append(f"DMG*D8*{dob}*{gender}~")
    if apt:
        segs.append(f"N3*{street}*{apt}~")
    else:
        segs.append(f"N3*{street}~")
    segs.append(f"N4*{city}*{state}*{zip_code}~")

    # ── Loop 2300: Health Coverage (SINGLE loop — Louisiana convention) ──
    # Louisiana uses single HD with HLT = full benefit package
    segs.append(f"HD*{maint_type}**HLT*{plan_code}*EMP~")
    segs.append(f"DTP*348*D8*{elig_date}~")

    # Louisiana convention: DTP*349 is ABSENT for open-ended enrollment
    # Only present when there is a known coverage end date
    if coverage_end is not None:
        segs.append(f"DTP*349*D8*{coverage_end}~")
    # else: segment omitted entirely (contrast with Ohio's 99991231 sentinel)

    # Louisiana: REF*N6 for network assignment (not REF*17 like Ohio)
    segs.append(f"REF*N6*{network_region}~")

    return segs


def wrap_transaction(header_segs, member_blocks, st_control="0001"):
    """Wrap header + members in ST/SE."""
    body = header_segs.copy()
    for block in member_blocks:
        body.extend(block)
    seg_count = len(body) + 2  # ST + SE
    segs = [f"ST*834*{st_control}*005010X220A1~"]
    segs.extend(body)
    segs.append(f"SE*{seg_count}*{st_control}~")
    return segs


def build_file(isa_date, ccyy_date, control_num, bgn_ref, member_blocks):
    """Build a complete EDI 834 file."""
    header = build_header(bgn_ref, ccyy_date)
    tx_segs = wrap_transaction(header, member_blocks)
    all_segs = []
    all_segs.append(isa_segment(isa_date, control_num))
    all_segs.append(gs_segment(ccyy_date, "1"))
    all_segs.extend(tx_segs)
    all_segs.append(ge_segment(1, "1"))
    all_segs.append(iea_segment(1, control_num))
    return "".join(all_segs)


# ═══════════════════════════════════════════════════════════════════════
# FILE 1: Standard New Enrollments (8 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_1():
    global _conf_counter
    _conf_counter = 0
    members = []

    # Member 1: TANF adult, New Orleans, Region 1
    members.append(build_member(
        maint_type="021", ssn="445112233", medicaid_id="LA100234567",
        elig_group="LDE-TANF-001", region="REGION-1", elig_date="20260201",
        last_name="BOUDREAUX", first_name="MARIE", middle="C",
        dob="19870623", gender="F",
        street="1200 BOURBON STREET", apt="APT 3",
        city="NEW ORLEANS", state="LA", zip_code="70112",
        conf_date="20260201",
    ))

    # Member 2: Expansion adult (XIX), Baton Rouge, Region 2
    members.append(build_member(
        maint_type="021", ssn="556223344", medicaid_id="LA100345678",
        elig_group="LDE-EXP-001", region="REGION-2", elig_date="20260201",
        last_name="LANDRY", first_name="ANTOINE", middle="J",
        dob="19920415", gender="M",
        street="890 GOVERNMENT STREET", apt=None,
        city="BATON ROUGE", state="LA", zip_code="70801",
        conf_date="20260201",
    ))

    # Member 3: TANF child, Houma, Region 3
    members.append(build_member(
        maint_type="021", ssn="667334455", medicaid_id="LA100456789",
        elig_group="LDE-TANF-002", region="REGION-3", elig_date="20260201",
        last_name="THIBODAUX", first_name="CAMILLE", middle="A",
        dob="20180312", gender="F",
        street="100 MAIN STREET", apt=None,
        city="HOUMA", state="LA", zip_code="70360",
        conf_date="20260201",
    ))

    # Member 4: SSI adult, Lafayette, Region 4
    members.append(build_member(
        maint_type="021", ssn="778445566", medicaid_id="LA100567890",
        elig_group="LDE-SSI-001", region="REGION-4", elig_date="20260201",
        last_name="GUIDRY", first_name="RENEE", middle="M",
        dob="19650818", gender="F",
        street="3456 MAGAZINE STREET", apt=None,
        city="LAFAYETTE", state="LA", zip_code="70501",
        conf_date="20260201",
    ))

    # Member 5: LaCHIP child, Lake Charles, Region 5
    members.append(build_member(
        maint_type="021", ssn="889556677", medicaid_id="LA100678901",
        elig_group="LDE-CHIP-001", region="REGION-5", elig_date="20260201",
        last_name="BROUSSARD", first_name="ETIENNE", middle="P",
        dob="20140907", gender="M",
        street="555 BAYOU LANE", apt=None,
        city="LAKE CHARLES", state="LA", zip_code="70601",
        conf_date="20260201",
    ))

    # Member 6: ABD Aged, Alexandria, Region 6
    members.append(build_member(
        maint_type="021", ssn="990667788", medicaid_id="LA100789012",
        elig_group="LDE-ABD-001", region="REGION-6", elig_date="20260201",
        last_name="FONTENOT", first_name="THERESA", middle="L",
        dob="19420301", gender="F",
        street="600 TEXAS STREET", apt="SUITE 100",
        city="ALEXANDRIA", state="LA", zip_code="71301",
        conf_date="20260201",
    ))

    # Member 7: Expansion MAGI adult, Shreveport, Region 7
    members.append(build_member(
        maint_type="021", ssn="101778899", medicaid_id="LA100890123",
        elig_group="LDE-EXP-002", region="REGION-7", elig_date="20260201",
        last_name="RICHARD", first_name="JEAN", middle="B",
        dob="19800110", gender="M",
        street="950 PIERREMONT ROAD", apt=None,
        city="SHREVEPORT", state="LA", zip_code="71101",
        conf_date="20260201",
    ))

    # Member 8: Full dual-eligible, Monroe, Region 8
    members.append(build_member(
        maint_type="021", ssn="212889900", medicaid_id="LA100901234",
        elig_group="LDE-DUAL-001", region="REGION-8", elig_date="20260201",
        last_name="HEBERT", first_name="CLAIRE", middle="D",
        dob="19480712", gender="F",
        street="775 DESIARD STREET", apt=None,
        city="MONROE", state="LA", zip_code="71201",
        conf_date="20260201",
    ))

    return build_file("260201", "20260201", 1, "LAENRL20260201", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 2: Mixed Maintenance Types (6 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_2():
    global _conf_counter
    _conf_counter = 100
    members = []

    # New enrollment 1: Expansion adult, Hammond, Region 9
    members.append(build_member(
        maint_type="021", ssn="321001001", medicaid_id="LA200100100",
        elig_group="LDE-EXP-001", region="REGION-9", elig_date="20260215",
        last_name="COMEAUX", first_name="MARCEL", middle="E",
        dob="19890522", gender="M",
        street="3100 NORTH STREET", apt=None,
        city="HAMMOND", state="LA", zip_code="70401",
        conf_date="20260215",
    ))

    # New enrollment 2: TANF parent, Metairie, Region 1
    members.append(build_member(
        maint_type="021", ssn="321002002", medicaid_id="LA200200200",
        elig_group="LDE-TANF-001", region="REGION-1", elig_date="20260215",
        last_name="MELANCON", first_name="SIMONE", middle="R",
        dob="19940803", gender="F",
        street="1515 VETERANS MEMORIAL BLVD", apt="APT 14B",
        city="METAIRIE", state="LA", zip_code="70001",
        conf_date="20260215",
    ))

    # Termination 1: End of coverage with explicit end date
    # Louisiana: DTP*349 IS present because coverage has a known end
    members.append(build_member(
        maint_type="024", ssn="321003003", medicaid_id="LA200300300",
        elig_group="LDE-TANF-001", region="REGION-2", elig_date="20250601",
        last_name="DUPRE", first_name="DANIELLE", middle="N",
        dob="19910117", gender="F",
        street="2222 PERKINS ROAD", apt=None,
        city="BATON ROUGE", state="LA", zip_code="70816",
        coverage_end="20260228",  # ← explicit end date
        conf_date="20260215",
    ))

    # Termination 2: SSI member termed mid-month
    members.append(build_member(
        maint_type="024", ssn="321004004", medicaid_id="LA200400400",
        elig_group="LDE-SSI-001", region="REGION-4", elig_date="20240101",
        last_name="MOUTON", first_name="PHILIPPE", middle="G",
        dob="19590430", gender="M",
        street="789 ST CHARLES AVENUE", apt=None,
        city="NEW IBERIA", state="LA", zip_code="70560",
        coverage_end="20260215",
        conf_date="20260215",
    ))

    # Change (025): Eligibility group change (TANF child aging into CHIP)
    members.append(build_member(
        maint_type="025", ssn="321005005", medicaid_id="LA200500500",
        elig_group="LDE-CHIP-001", region="REGION-5", elig_date="20250301",
        last_name="CASTILLE", first_name="GABRIELLE", middle="T",
        dob="20070615", gender="F",
        street="1717 RIVER ROAD", apt=None,
        city="SULPHUR", state="LA", zip_code="70663",
        conf_date="20260215",
    ))

    # Reinstatement (026): Previously terminated, now reinstated
    members.append(build_member(
        maint_type="026", ssn="321006006", medicaid_id="LA200600600",
        elig_group="LDE-EXP-002", region="REGION-7", elig_date="20260201",
        last_name="DOUCET", first_name="LUCIEN", middle="H",
        dob="19850929", gender="M",
        street="1400 FAIRFIELD AVENUE", apt=None,
        city="BOSSIER CITY", state="LA", zip_code="71111",
        conf_date="20260215",
    ))

    return build_file("260215", "20260215", 2, "LAMIXED20260215", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 3: Retroactive Changes (5 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_3():
    global _conf_counter
    _conf_counter = 200
    members = []

    # Retroactive addition: effective 2 months prior
    members.append(build_member(
        maint_type="021", ssn="410001001", medicaid_id="LA300100100",
        elig_group="LDE-TANF-001", region="REGION-1", elig_date="20260101",
        last_name="TRAHAN", first_name="ANNETTE", middle="P",
        dob="19960214", gender="F",
        street="2100 CANAL STREET", apt=None,
        city="NEW ORLEANS", state="LA", zip_code="70119",
        conf_date="20260301",
    ))

    # Retroactive termination: coverage ended last month
    members.append(build_member(
        maint_type="024", ssn="410002002", medicaid_id="LA300200200",
        elig_group="LDE-SSI-001", region="REGION-6", elig_date="20230801",
        last_name="ARCENEAUX", first_name="GASTON", middle="W",
        dob="19570615", gender="M",
        street="3100 NORTH STREET", apt=None,
        city="PINEVILLE", state="LA", zip_code="71360",
        coverage_end="20260201",
        conf_date="20260301",
    ))

    # Eligibility group change: member moved from EXP-001 to EXP-002
    members.append(build_member(
        maint_type="025", ssn="410003003", medicaid_id="LA300300300",
        elig_group="LDE-EXP-002", region="REGION-2", elig_date="20250701",
        last_name="ROMERO", first_name="JAMES", middle="K",
        dob="19880320", gender="M",
        street="4444 HIGHLAND ROAD", apt=None,
        city="GONZALES", state="LA", zip_code="70737",
        conf_date="20260301",
    ))

    # Audit/Compare (030)
    members.append(build_member(
        maint_type="030", ssn="410004004", medicaid_id="LA300400400",
        elig_group="LDE-TANF-002", region="REGION-3", elig_date="20260101",
        last_name="LEBLANC", first_name="COLETTE", middle="S",
        dob="20150827", gender="F",
        street="100 MAIN STREET", apt=None,
        city="THIBODAUX", state="LA", zip_code="70301",
        conf_date="20260301",
    ))

    # Partial dual-eligible new enrollment
    members.append(build_member(
        maint_type="021", ssn="410005005", medicaid_id="LA300500500",
        elig_group="LDE-DUAL-002", region="REGION-8", elig_date="20260301",
        last_name="JOHNSON", first_name="DOROTHY", middle="F",
        dob="19450103", gender="F",
        street="775 DESIARD STREET", apt="APT 201",
        city="WEST MONROE", state="LA", zip_code="71291",
        conf_date="20260301",
    ))

    return build_file("260301", "20260301", 3, "LARETRO20260301", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 4: Edge Cases (6 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_4():
    global _conf_counter
    _conf_counter = 300
    members = []

    # Hyphenated Cajun/Creole name
    members.append(build_member(
        maint_type="021", ssn="510101010", medicaid_id="LA400101010",
        elig_group="LDE-TANF-001", region="REGION-4", elig_date="20260301",
        last_name="BOUDREAUX-THIBODAUX", first_name="CELESTE", middle="M",
        dob="19930407", gender="F",
        street="3456 MAGAZINE STREET", apt=None,
        city="LAFAYETTE", state="LA", zip_code="70501",
        conf_date="20260315",
    ))

    # Name with "de" prefix (Creole naming convention)
    # NM1 stores as-is — parser must preserve multi-word last names
    segs = []
    segs.append("INS*Y*18*021*28*A***FT~")
    segs.append("REF*0F*LA400202020~")
    segs.append("REF*1L*REGION-1~")
    segs.append("REF*ZZ*LDE-EXP-001~")
    segs.append(f"REF*CE*{next_confirmation('20260315')}~")
    segs.append("DTP*336*D8*20260301~")
    segs.append("NM1*IL*1*DE LA CROIX*PIERRE*A***34*520202020~")
    segs.append("DMG*D8*19760830*M~")
    segs.append("N3*450 ESPLANADE AVENUE~")
    segs.append("N4*NEW ORLEANS*LA*70112~")
    segs.append("HD*021**HLT*BAYOU-STD*EMP~")
    segs.append("DTP*348*D8*20260301~")
    segs.append("REF*N6*NET-1~")
    members.append(segs)

    # LaCHIP child — specific Louisiana children's program
    members.append(build_member(
        maint_type="021", ssn="530303030", medicaid_id="LA400303030",
        elig_group="LDE-CHIP-002", region="REGION-9", elig_date="20260301",
        last_name="BROUSSARD", first_name="JACQUES", middle="L",
        dob="20120218", gender="M",
        street="3100 NORTH STREET", apt=None,
        city="COVINGTON", state="LA", zip_code="70433",
        conf_date="20260315",
    ))

    # Newborn infant: born Feb 2026, TANF-003 (infant under 1)
    members.append(build_member(
        maint_type="021", ssn="540404040", medicaid_id="LA400404040",
        elig_group="LDE-TANF-003", region="REGION-2", elig_date="20260210",
        last_name="LANDRY", first_name="BEAU", middle=None,
        dob="20260208", gender="M",
        street="2828 GREENWELL SPRINGS ROAD", apt=None,
        city="BATON ROUGE", state="LA", zip_code="70816",
        conf_date="20260315",
    ))

    # Elderly member (90+) — ABD Aged
    members.append(build_member(
        maint_type="021", ssn="550505050", medicaid_id="LA400505050",
        elig_group="LDE-ABD-001", region="REGION-3", elig_date="20260301",
        last_name="COMEAUX", first_name="RUTH", middle="E",
        dob="19350611", gender="F",
        street="100 MAIN STREET", apt="UNIT 6",
        city="HOUMA", state="LA", zip_code="70360",
        conf_date="20260315",
    ))

    # Partial dual-eligible — demonstrates DUAL-002 vs DUAL-001
    members.append(build_member(
        maint_type="021", ssn="560606060", medicaid_id="LA400606060",
        elig_group="LDE-DUAL-002", region="REGION-7", elig_date="20260301",
        last_name="FONTENOT", first_name="EMILE", middle="G",
        dob="19500924", gender="M",
        street="600 TEXAS STREET", apt=None,
        city="SHREVEPORT", state="LA", zip_code="71101",
        conf_date="20260315",
    ))

    return build_file("260315", "20260315", 4, "LAEDGE20260315", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 5: Error File (5 members — 4 with errors, 1 valid)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_5():
    global _conf_counter
    _conf_counter = 400
    members = []

    # ERROR 1: Missing required NM1 segment
    segs = []
    segs.append("INS*Y*18*021*28*A***FT~")
    segs.append("REF*0F*LA500ERR001~")
    segs.append("REF*1L*REGION-1~")
    segs.append("REF*ZZ*LDE-TANF-001~")
    segs.append(f"REF*CE*{next_confirmation('20260320')}~")
    segs.append("DTP*336*D8*20260301~")
    # NM1 intentionally omitted
    segs.append("DMG*D8*19900101*F~")
    segs.append("N3*1200 BOURBON STREET~")
    segs.append("N4*NEW ORLEANS*LA*70112~")
    segs.append("HD*021**HLT*BAYOU-STD*EMP~")
    segs.append("DTP*348*D8*20260301~")
    segs.append("REF*N6*NET-1~")
    members.append(segs)

    # ERROR 2: Invalid eligibility group code
    segs = []
    segs.append("INS*Y*18*021*28*A***FT~")
    segs.append("REF*0F*LA500ERR002~")
    segs.append("REF*1L*REGION-2~")
    segs.append("REF*ZZ*LDE-INVALID-999~")  # ← invalid code
    segs.append(f"REF*CE*{next_confirmation('20260320')}~")
    segs.append("DTP*336*D8*20260301~")
    segs.append("NM1*IL*1*ERRORTEST*BADGROUP*B***34*699000002~")
    segs.append("DMG*D8*19850515*M~")
    segs.append("N3*890 GOVERNMENT STREET~")
    segs.append("N4*BATON ROUGE*LA*70801~")
    segs.append("HD*021**HLT*BAYOU-STD*EMP~")
    segs.append("DTP*348*D8*20260301~")
    segs.append("REF*N6*NET-2~")
    members.append(segs)

    # ERROR 3: Invalid date (month 13, day 32)
    segs = []
    segs.append("INS*Y*18*021*28*A***FT~")
    segs.append("REF*0F*LA500ERR003~")
    segs.append("REF*1L*REGION-3~")
    segs.append("REF*ZZ*LDE-TANF-001~")
    segs.append(f"REF*CE*{next_confirmation('20260320')}~")
    segs.append("DTP*336*D8*20260301~")
    segs.append("NM1*IL*1*ERRORTEST*BADDATE*C***34*699000003~")
    segs.append("DMG*D8*19881332*F~")  # ← invalid date
    segs.append("N3*555 BAYOU LANE~")
    segs.append("N4*HOUMA*LA*70360~")
    segs.append("HD*021**HLT*BAYOU-STD*EMP~")
    segs.append("DTP*348*D8*20260301~")
    segs.append("REF*N6*NET-3~")
    members.append(segs)

    # ERROR 4: Missing Medicaid ID (REF*0F absent)
    segs = []
    segs.append("INS*Y*18*021*28*A***FT~")
    # REF*0F intentionally omitted — no Medicaid ID
    segs.append("REF*1L*REGION-4~")
    segs.append("REF*ZZ*LDE-EXP-001~")
    segs.append(f"REF*CE*{next_confirmation('20260320')}~")
    segs.append("DTP*336*D8*20260301~")
    segs.append("NM1*IL*1*ERRORTEST*NOID*D***34*699000004~")
    segs.append("DMG*D8*19880101*M~")
    segs.append("N3*789 ST CHARLES AVENUE~")
    segs.append("N4*LAFAYETTE*LA*70501~")
    segs.append("HD*021**HLT*BAYOU-STD*EMP~")
    segs.append("DTP*348*D8*20260301~")
    segs.append("REF*N6*NET-4~")
    members.append(segs)

    # VALID: Normal member to verify partial file processing
    members.append(build_member(
        maint_type="021", ssn="699000005", medicaid_id="LA500VALID1",
        elig_group="LDE-EXP-001", region="REGION-2", elig_date="20260301",
        last_name="GOODRECORD", first_name="VALID", middle="A",
        dob="19930715", gender="F",
        street="2222 PERKINS ROAD", apt=None,
        city="BATON ROUGE", state="LA", zip_code="70801",
        conf_date="20260320",
    ))

    return build_file("260320", "20260320", 5, "LAERROR20260320", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 6: Large Batch (50 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_6():
    global _conf_counter
    _conf_counter = 500
    random.seed(73)  # Different seed from Ohio (42)
    members = []

    # Louisiana eligibility group distribution:
    # ~25% TANF (mixed), ~15% SSI, ~25% Expansion, ~10% ABD,
    # ~10% Dual, ~15% CHIP
    elig_weights = [
        ("LDE-TANF-001",  5),
        ("LDE-TANF-002",  5),
        ("LDE-TANF-003",  3),
        ("LDE-SSI-001",   5),
        ("LDE-SSI-002",   3),
        ("LDE-ABD-001",   3),
        ("LDE-ABD-002",   2),
        ("LDE-EXP-001",   7),
        ("LDE-EXP-002",   5),
        ("LDE-CHIP-001",  5),
        ("LDE-CHIP-002",  2),
        ("LDE-DUAL-001",  3),
        ("LDE-DUAL-002",  2),
    ]
    elig_pool = []
    for code, weight in elig_weights:
        elig_pool.extend([code] * weight)

    regions = list(LA_REGIONS.keys())

    for i in range(50):
        idx = i + 1
        ssn = f"{800000000 + idx}"
        medicaid_id = f"LA600{100000 + idx}"
        elig_group = random.choice(elig_pool)
        region = random.choice(regions)
        loc = random.choice(LA_REGIONS[region])

        # DOB based on eligibility group
        if elig_group == "LDE-TANF-003":
            dob = f"2025{random.randint(6,12):02d}{random.randint(1,28):02d}"
        elif elig_group in ("LDE-TANF-002", "LDE-SSI-002", "LDE-CHIP-001", "LDE-CHIP-002"):
            year = random.randint(2008, 2020)
            dob = f"{year}{random.randint(1,12):02d}{random.randint(1,28):02d}"
        elif elig_group in ("LDE-ABD-001", "LDE-DUAL-001", "LDE-DUAL-002"):
            year = random.randint(1935, 1965)
            dob = f"{year}{random.randint(1,12):02d}{random.randint(1,28):02d}"
        else:
            year = random.randint(1968, 2002)
            dob = f"{year}{random.randint(1,12):02d}{random.randint(1,28):02d}"

        gender = random.choice(["M", "F"])
        first_name = random.choice(FIRST_NAMES_F if gender == "F" else FIRST_NAMES_M)
        last_name = random.choice(LAST_NAMES)
        middle = random.choice(MIDDLE_INITIALS)
        street = random.choice(STREETS)
        apt = random.choice(APTS)

        members.append(build_member(
            maint_type="021", ssn=ssn, medicaid_id=medicaid_id,
            elig_group=elig_group, region=region, elig_date="20260401",
            last_name=last_name, first_name=first_name, middle=middle,
            dob=dob, gender=gender,
            street=street, apt=apt,
            city=loc[0], state=loc[1], zip_code=loc[2],
            conf_date="20260401",
        ))

    return build_file("260401", "20260401", 6, "LABATCH20260401", members)


# ═══════════════════════════════════════════════════════════════════════
# Generate all files
# ═══════════════════════════════════════════════════════════════════════

def write_file(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    size = os.path.getsize(path)
    sha = hashlib.sha256(content.encode()).hexdigest()
    print(f"  {filename}: {size:,} bytes | SHA-256: {sha[:16]}...")


if __name__ == "__main__":
    print("Generating Louisiana Medicaid EDI 834 Test Files...\n")

    print("File 1: Standard Enrollments (8 members)")
    write_file("LA_834_STANDARD_ENROLL_20260201.edi", generate_file_1())

    print("File 2: Mixed Maintenance Types (6 members)")
    write_file("LA_834_MIXED_MAINT_20260215.edi", generate_file_2())

    print("File 3: Retroactive Changes (5 members)")
    write_file("LA_834_RETRO_CHANGES_20260301.edi", generate_file_3())

    print("File 4: Edge Cases (6 members)")
    write_file("LA_834_EDGE_CASES_20260315.edi", generate_file_4())

    print("File 5: Error File (5 members, 4 with errors)")
    write_file("LA_834_ERROR_FILE_20260320.edi", generate_file_5())

    print("File 6: Large Batch (50 members)")
    write_file("LA_834_LARGE_BATCH_20260401.edi", generate_file_6())

    print("\nDone. All files written to:", OUTPUT_DIR)
