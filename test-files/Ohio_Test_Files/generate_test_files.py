#!/usr/bin/env python3
"""
Generate Ohio Medicaid EDI 834 Test Files — ODM Companion Guide v13.1 conventions.

Key conventions per the real companion guide:
- REF*0F = Medicaid ID (12 chars, IE-origin starts with "9")
- SSN in NM1*IL element 09 (qualifier 34)
- Rate cell in Loop 2300 REF*1L (10 chars, XXXXXXXXXX = no rate cell)
- No REF*ZZ (not in ODM guide)
- No REF*1L at Loop 2000 level
- Plan codes from PlanCoverageDescCodes (CFC, ABD, OHR, BH-SUD, etc.)
- Insurance lines from InsuranceLineCodes (HMO, MM, HLT, AG, etc.)
- Full file: BGN08=4, all INS03=030, all HD01=030
- Changes file: BGN08=2, INS03=001/021/024, HD01=001/021/024/025
"""

import os
import random
import hashlib

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Ohio-specific constants ────────────────────────────────────────────

SENDER_ID   = "OHMMIS         "  # 15 chars, padded
RECEIVER_ID = "MCOPLAN        "  # 15 chars, padded
SPONSOR_NAME = "OHIO DEPARTMENT OF MEDICAID"
SPONSOR_FI   = "314589267"
MCO_NAME     = "ACME HEALTH PLAN MCO"
MCO_FI       = "621234567"

# Ohio cities with ZIP codes
OH_LOCATIONS = [
    ("COLUMBUS",    "OH", "43215"),
    ("COLUMBUS",    "OH", "43201"),
    ("CLEVELAND",   "OH", "44102"),
    ("CLEVELAND",   "OH", "44113"),
    ("CINCINNATI",  "OH", "45202"),
    ("CINCINNATI",  "OH", "45219"),
    ("DAYTON",      "OH", "45402"),
    ("TOLEDO",      "OH", "43604"),
    ("AKRON",       "OH", "44308"),
    ("YOUNGSTOWN",  "OH", "44503"),
    ("CANTON",      "OH", "44702"),
    ("SPRINGFIELD", "OH", "45502"),
    ("MANSFIELD",   "OH", "44902"),
    ("LIMA",        "OH", "45801"),
    ("ZANESVILLE",  "OH", "43701"),
]

STREETS = [
    "1234 MAPLE STREET", "5678 OAK AVENUE", "910 ELM BOULEVARD",
    "2345 PINE ROAD", "4567 CEDAR LANE", "7890 BIRCH DRIVE",
    "1122 WALNUT STREET", "3344 ASH AVENUE", "5566 CHERRY LANE",
    "7788 SPRUCE COURT", "2468 HICKORY WAY", "1357 POPLAR DRIVE",
    "9876 WILLOW STREET", "6543 MAGNOLIA AVENUE", "3210 SYCAMORE ROAD",
    "1598 CHESTNUT BOULEVARD", "7531 HEMLOCK LANE", "8642 LAUREL DRIVE",
    "4826 DOGWOOD COURT", "1739 HAWTHORN STREET",
]

APTS = [
    None, None, None, None, None,  # Most have no apt
    "APT 4B", "APT 12", "UNIT 3A", "SUITE 200", "APT 7",
    "UNIT 15C", "APT 2", "FL 3",
]

LAST_NAMES = [
    "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA",
    "MILLER", "DAVIS", "RODRIGUEZ", "MARTINEZ", "HERNANDEZ",
    "LOPEZ", "GONZALEZ", "WILSON", "ANDERSON", "THOMAS",
    "TAYLOR", "MOORE", "JACKSON", "MARTIN", "LEE",
    "PEREZ", "THOMPSON", "WHITE", "HARRIS", "SANCHEZ",
    "CLARK", "RAMIREZ", "LEWIS", "ROBINSON", "WALKER",
    "YOUNG", "ALLEN", "KING", "WRIGHT", "SCOTT",
    "TORRES", "NGUYEN", "HILL", "FLORES", "GREEN",
    "ADAMS", "NELSON", "BAKER", "HALL", "RIVERA",
    "CAMPBELL", "MITCHELL", "CARTER", "ROBERTS", "PHILLIPS",
]

FIRST_NAMES_F = [
    "MARIA", "JENNIFER", "LISA", "JESSICA", "SARAH",
    "PATRICIA", "LINDA", "ELIZABETH", "BARBARA", "SUSAN",
    "MARGARET", "DOROTHY", "RUTH", "HELEN", "ANNA",
    "ANGELA", "DEBORAH", "BRENDA", "ASHLEY", "EMILY",
    "DONNA", "CAROL", "AMANDA", "MELISSA", "STEPHANIE",
]

FIRST_NAMES_M = [
    "ROBERT", "JAMES", "JOHN", "MICHAEL", "DAVID",
    "WILLIAM", "RICHARD", "JOSEPH", "THOMAS", "CHARLES",
    "CHRISTOPHER", "DANIEL", "MATTHEW", "ANTHONY", "MARK",
    "DONALD", "STEVEN", "PAUL", "ANDREW", "JOSHUA",
    "KEVIN", "BRIAN", "GEORGE", "EDWARD", "RONALD",
]

MIDDLE_INITIALS = list("ABCDEFGHJKLMNPRSTW") + [None, None, None]


def isa_segment(date_yymmdd, control_num):
    """Build ISA segment — always exactly 106 characters including terminator."""
    return (
        f"ISA*00*          *00*          "
        f"*ZZ*{SENDER_ID}*ZZ*{RECEIVER_ID}"
        f"*{date_yymmdd}*1230*^*00501*{control_num:09d}*0*P*:~"
    )


def gs_segment(date_ccyymmdd, group_control):
    return f"GS*BE*OHMMIS*MCOPLAN*{date_ccyymmdd}*1230*{group_control}*X*005010X220A1~"


def ge_segment(tx_count, group_control):
    return f"GE*{tx_count}*{group_control}~"


def iea_segment(group_count, control_num):
    return f"IEA*{group_count}*{control_num:09d}~"


def build_header(bgn_ref, date_ccyymmdd, bgn08, contract_ref="OH-MCO-001"):
    """Build transaction header: BGN, REF, DTP, N1*P5, N1*IN."""
    segs = []
    segs.append(f"BGN*00*{bgn_ref}*{date_ccyymmdd}*1230****{bgn08}~")
    segs.append(f"REF*38*{contract_ref}~")
    segs.append(f"DTP*007*D8*{date_ccyymmdd}~")
    segs.append(f"N1*P5*{SPONSOR_NAME}*FI*{SPONSOR_FI}~")
    segs.append(f"N1*IN*{MCO_NAME}*FI*{MCO_FI}~")
    return segs


def build_member(*, ins03, ins04, medicaid_id, elig_date,
                 last_name, first_name, middle, ssn, dob, gender,
                 street, apt, city, state, zip_code,
                 coverages):
    """Build a complete member block per ODM Companion Guide conventions.

    Loop 2000: INS, REF*0F (Medicaid ID, 12 chars), DTP*336
    Loop 2100A: NM1*IL (SSN in element 09), DMG, N3, N4
    Loop 2300 (per coverage): HD, DTP*348, DTP*349, REF*1L (rate cell)
    """
    segs = []

    # ── Loop 2000: Member Level Detail ──
    segs.append(f"INS*Y*18*{ins03}*{ins04}*A***FT~")
    segs.append(f"REF*0F*{medicaid_id}~")
    segs.append(f"DTP*336*D8*{elig_date}~")

    # ── Loop 2100A: Member Name / Demographics ──
    if middle:
        segs.append(f"NM1*IL*1*{last_name}*{first_name}*{middle}***34*{ssn}~")
    else:
        segs.append(f"NM1*IL*1*{last_name}*{first_name}****34*{ssn}~")
    segs.append(f"DMG*D8*{dob}*{gender}~")
    if apt:
        segs.append(f"N3*{street}*{apt}~")
    else:
        segs.append(f"N3*{street}~")
    segs.append(f"N4*{city}*{state}*{zip_code}~")

    # ── Loop 2300: Health Coverage(s) ──
    for cov in coverages:
        hd01 = cov["hd01"]
        ins_line = cov["ins_line"]
        plan_code = cov["plan_code"]
        start = cov["start"]
        end = cov.get("end", "99991231")
        rate_cell = cov.get("rate_cell")

        segs.append(f"HD*{hd01}**{ins_line}*{plan_code}*EMP~")
        segs.append(f"DTP*348*D8*{start}~")
        segs.append(f"DTP*349*D8*{end}~")
        if rate_cell:
            segs.append(f"REF*1L*{rate_cell}~")

    return segs


def wrap_transaction(header_segs, member_blocks, st_control="0001"):
    """Wrap header + members in ST/SE."""
    body = header_segs.copy()
    for block in member_blocks:
        body.extend(block)
    seg_count = len(body) + 2  # +2 for ST and SE themselves
    segs = [f"ST*834*{st_control}*005010X220A1~"]
    segs.extend(body)
    segs.append(f"SE*{seg_count}*{st_control}~")
    return segs


def build_file(isa_date, ccyy_date, control_num, bgn_ref, bgn08, member_blocks):
    """Build a complete EDI 834 file."""
    header = build_header(bgn_ref, ccyy_date, bgn08)
    tx_segs = wrap_transaction(header, member_blocks)
    all_segs = []
    all_segs.append(isa_segment(isa_date, control_num))
    all_segs.append(gs_segment(ccyy_date, "1"))
    all_segs.extend(tx_segs)
    all_segs.append(ge_segment(1, "1"))
    all_segs.append(iea_segment(1, control_num))
    return "".join(all_segs)


def cov(hd01, ins_line, plan_code, start, end="99991231", rate_cell=None):
    """Helper to build a coverage dict."""
    return {
        "hd01": hd01,
        "ins_line": ins_line,
        "plan_code": plan_code,
        "start": start,
        "end": end,
        "rate_cell": rate_cell,
    }


# ═══════════════════════════════════════════════════════════════════════
# FILE 1: Standard New Enrollments (Changes file, 8 members, all 021)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_1():
    members = []

    # Member 1: Adult female, TANF, medical(HMO/CFC) + dental(MM/CFC), Columbus
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000001", elig_date="20260201",
        last_name="JOHNSON", first_name="MARIA", middle="A",
        ssn="123456789", dob="19840315", gender="F",
        street="1234 MAPLE STREET", apt="APT 4B",
        city="COLUMBUS", state="OH", zip_code="43215",
        coverages=[
            cov("021", "HMO", "CFC", "20260201", rate_cell="0260201001"),
            cov("021", "MM", "CFC", "20260201", rate_cell="0260201001"),
        ],
    ))

    # Member 2: SSI adult male, medical only (HMO/ABD), Cleveland
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000002", elig_date="20260201",
        last_name="WILLIAMS", first_name="ROBERT", middle="T",
        ssn="234567891", dob="19560722", gender="M",
        street="5678 OAK AVENUE", apt=None,
        city="CLEVELAND", state="OH", zip_code="44102",
        coverages=[
            cov("021", "HMO", "ABD", "20260201", rate_cell="0260201002"),
        ],
    ))

    # Member 3: Child age 3, TANF, medical + dental, Cincinnati
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000003", elig_date="20260201",
        last_name="GARCIA", first_name="ISABELLA", middle="M",
        ssn="345678912", dob="20221108", gender="F",
        street="910 ELM BOULEVARD", apt="UNIT 3A",
        city="CINCINNATI", state="OH", zip_code="45202",
        coverages=[
            cov("021", "HMO", "CFC", "20260201", rate_cell="0260201003"),
            cov("021", "MM", "CFC", "20260201", rate_cell="0260201003"),
        ],
    ))

    # Member 4: Expansion adult male, medical only, Dayton
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000004", elig_date="20260201",
        last_name="MARTINEZ", first_name="CARLOS", middle=None,
        ssn="456789123", dob="19910603", gender="M",
        street="2345 PINE ROAD", apt=None,
        city="DAYTON", state="OH", zip_code="45402",
        coverages=[
            cov("021", "HMO", "CFC", "20260201", rate_cell="0260201004"),
        ],
    ))

    # Member 5: TANF child age 10, medical + dental, Toledo
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000005", elig_date="20260201",
        last_name="BROWN", first_name="JAYDEN", middle="R",
        ssn="567891234", dob="20151215", gender="M",
        street="4567 CEDAR LANE", apt=None,
        city="TOLEDO", state="OH", zip_code="43604",
        coverages=[
            cov("021", "HMO", "CFC", "20260201", rate_cell="0260201005"),
            cov("021", "MM", "CFC", "20260201", rate_cell="0260201005"),
        ],
    ))

    # Member 6: SSI adult female, medical only, Akron
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000006", elig_date="20260201",
        last_name="DAVIS", first_name="PATRICIA", middle="L",
        ssn="678912345", dob="19720418", gender="F",
        street="7890 BIRCH DRIVE", apt="APT 12",
        city="AKRON", state="OH", zip_code="44308",
        coverages=[
            cov("021", "HMO", "ABD", "20260201", rate_cell="0260201006"),
        ],
    ))

    # Member 7: SSI child, medical + dental (ABD plan), Youngstown
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000007", elig_date="20260201",
        last_name="THOMPSON", first_name="EMILY", middle="K",
        ssn="789123456", dob="20180909", gender="F",
        street="1122 WALNUT STREET", apt=None,
        city="YOUNGSTOWN", state="OH", zip_code="44503",
        coverages=[
            cov("021", "HMO", "ABD", "20260201", rate_cell="0260201007"),
            cov("021", "MM", "ABD", "20260201", rate_cell="0260201007"),
        ],
    ))

    # Member 8: Expansion adult, medical + dental + behavioral health (3 coverages), Canton
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0100000008", elig_date="20260201",
        last_name="WILSON", first_name="JAMES", middle="D",
        ssn="891234567", dob="19880127", gender="M",
        street="3344 ASH AVENUE", apt="SUITE 200",
        city="CANTON", state="OH", zip_code="44702",
        coverages=[
            cov("021", "HMO", "CFC", "20260201", rate_cell="0260201008"),
            cov("021", "MM", "CFC", "20260201", rate_cell="0260201008"),
            cov("021", "HLT", "BH-SUD", "20260201", rate_cell="0260201008"),
        ],
    ))

    return build_file("260201", "20260201", 1, "OHENRL20260201", "2", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 2: Mixed Maintenance Types (Changes file, 6 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_2():
    members = []

    # Addition 1: New enrollment
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0200000001", elig_date="20260215",
        last_name="PEREZ", first_name="ROSA", middle="E",
        ssn="111223344", dob="19950812", gender="F",
        street="9876 WILLOW STREET", apt=None,
        city="COLUMBUS", state="OH", zip_code="43201",
        coverages=[
            cov("021", "HMO", "CFC", "20260215", rate_cell="0260215001"),
            cov("021", "MM", "CFC", "20260215", rate_cell="0260215001"),
        ],
    ))

    # Addition 2: Medical only
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0200000002", elig_date="20260215",
        last_name="NGUYEN", first_name="DAVID", middle="H",
        ssn="222334455", dob="19870304", gender="M",
        street="6543 MAGNOLIA AVENUE", apt="APT 7",
        city="CLEVELAND", state="OH", zip_code="44113",
        coverages=[
            cov("021", "HMO", "CFC", "20260215", rate_cell="0260215002"),
        ],
    ))

    # Termination 1: Losing coverage end of Feb (INS03=024, HD01=024)
    members.append(build_member(
        ins03="024", ins04="1", medicaid_id="9A0200000003", elig_date="20250801",
        last_name="TAYLOR", first_name="MICHELLE", middle="N",
        ssn="333445566", dob="19890629", gender="F",
        street="3210 SYCAMORE ROAD", apt=None,
        city="DAYTON", state="OH", zip_code="45402",
        coverages=[
            cov("024", "HMO", "CFC", "20250801", "20260228", "0250801003"),
            cov("024", "MM", "CFC", "20250801", "20260228", "0250801003"),
        ],
    ))

    # Termination 2: SSI member termed mid-month
    members.append(build_member(
        ins03="024", ins04="1", medicaid_id="9A0200000004", elig_date="20240301",
        last_name="CLARK", first_name="STEVEN", middle="W",
        ssn="444556677", dob="19650114", gender="M",
        street="1598 CHESTNUT BOULEVARD", apt=None,
        city="TOLEDO", state="OH", zip_code="43604",
        coverages=[
            cov("024", "HMO", "ABD", "20240301", "20260215", "0240301004"),
        ],
    ))

    # Change: Address update (INS03=001, HD01=001)
    members.append(build_member(
        ins03="001", ins04="EC", medicaid_id="9A0200000005", elig_date="20250601",
        last_name="MOORE", first_name="AIDEN", middle="J",
        ssn="555667788", dob="20130422", gender="M",
        street="7531 HEMLOCK LANE", apt="UNIT 15C",
        city="AKRON", state="OH", zip_code="44308",
        coverages=[
            cov("001", "HMO", "CFC", "20250601", rate_cell="0250601005"),
            cov("001", "MM", "CFC", "20250601", rate_cell="0250601005"),
        ],
    ))

    # Reinstatement: INS03=021 (addition back), HD01=025 (reinstatement at coverage level)
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0200000006", elig_date="20260201",
        last_name="HARRIS", first_name="KEVIN", middle="B",
        ssn="666778899", dob="19930817", gender="M",
        street="8642 LAUREL DRIVE", apt=None,
        city="CINCINNATI", state="OH", zip_code="45219",
        coverages=[
            cov("025", "HMO", "CFC", "20260201", rate_cell="0260201006"),
        ],
    ))

    return build_file("260215", "20260215", 2, "OHMIXED20260215", "2", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 3: Retroactive Changes (Changes file, 5 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_3():
    members = []

    # Retroactive addition: elig date 2 months prior
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0300000001", elig_date="20260101",
        last_name="ROBINSON", first_name="ANGELA", middle="P",
        ssn="111111111", dob="19970210", gender="F",
        street="4826 DOGWOOD COURT", apt=None,
        city="SPRINGFIELD", state="OH", zip_code="45502",
        coverages=[
            cov("021", "HMO", "CFC", "20260101", rate_cell="0260101001"),
            cov("021", "MM", "CFC", "20260101", rate_cell="0260101001"),
        ],
    ))

    # Retroactive termination: termed effective last month
    members.append(build_member(
        ins03="024", ins04="1", medicaid_id="9A0300000002", elig_date="20230601",
        last_name="LEWIS", first_name="DONALD", middle="G",
        ssn="222222222", dob="19580930", gender="M",
        street="1739 HAWTHORN STREET", apt=None,
        city="MANSFIELD", state="OH", zip_code="44902",
        coverages=[
            cov("024", "HMO", "ABD", "20230601", "20260201", "0230601002"),
        ],
    ))

    # Change: Rate category change retroactive (INS03=001)
    members.append(build_member(
        ins03="001", ins04="EC", medicaid_id="9A0300000003", elig_date="20250901",
        last_name="WALKER", first_name="ASHLEY", middle="R",
        ssn="333333333", dob="20140515", gender="F",
        street="2468 HICKORY WAY", apt=None,
        city="LIMA", state="OH", zip_code="45801",
        coverages=[
            cov("001", "HMO", "CFC", "20250901", rate_cell="0250901003"),
            cov("001", "MM", "CFC", "20250901", rate_cell="0250901003"),
        ],
    ))

    # Data correction (INS03=001 for Changes file — was 030 in old file)
    members.append(build_member(
        ins03="001", ins04="EC", medicaid_id="9A0300000004", elig_date="20260101",
        last_name="YOUNG", first_name="STEPHANIE", middle="L",
        ssn="444444444", dob="19860712", gender="F",
        street="1357 POPLAR DRIVE", apt="APT 2",
        city="ZANESVILLE", state="OH", zip_code="43701",
        coverages=[
            cov("001", "HMO", "CFC", "20260101", rate_cell="0260101004"),
        ],
    ))

    # Dual-eligible new enrollment
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0300000005", elig_date="20260301",
        last_name="ALLEN", first_name="GEORGE", middle="F",
        ssn="555555555", dob="19430825", gender="M",
        street="5566 CHERRY LANE", apt=None,
        city="COLUMBUS", state="OH", zip_code="43215",
        coverages=[
            cov("021", "HMO", "ABD", "20260301", rate_cell="0260301005"),
        ],
    ))

    return build_file("260301", "20260301", 3, "OHRETRO20260301", "2", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 4: Edge Cases (Changes file, 6 members)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_4():
    members = []

    # Hyphenated last name
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0400000001", elig_date="20260301",
        last_name="GARCIA-LOPEZ", first_name="MARIA", middle="C",
        ssn="101010101", dob="19910215", gender="F",
        street="1234 MAPLE STREET", apt=None,
        city="COLUMBUS", state="OH", zip_code="43215",
        coverages=[
            cov("021", "HMO", "CFC", "20260301", rate_cell="0260301001"),
            cov("021", "MM", "CFC", "20260301", rate_cell="0260301001"),
        ],
    ))

    # Name with suffix embedded in last name (THOMPSON JR)
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0400000002", elig_date="20260301",
        last_name="THOMPSON JR", first_name="MARCUS", middle="D",
        ssn="202020202", dob="19880614", gender="M",
        street="5678 OAK AVENUE", apt=None,
        city="CLEVELAND", state="OH", zip_code="44102",
        coverages=[
            cov("021", "HMO", "CFC", "20260301", rate_cell="0260301002"),
        ],
    ))

    # Very long address
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0400000003", elig_date="20260301",
        last_name="WASHINGTON", first_name="DEBORAH", middle="A",
        ssn="303030303", dob="19700823", gender="F",
        street="12345 NORTH SPRINGFIELD BOULEVARD", apt="APARTMENT 4B BUILDING C",
        city="CINCINNATI", state="OH", zip_code="45202",
        coverages=[
            cov("021", "HMO", "ABD", "20260301", rate_cell="0260301003"),
        ],
    ))

    # Infant (DOB within 30 days of eligibility) — TANF child under 1
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0400000004", elig_date="20260120",
        last_name="HERNANDEZ", first_name="SOFIA", middle=None,
        ssn="404040404", dob="20260118", gender="F",
        street="2345 PINE ROAD", apt=None,
        city="DAYTON", state="OH", zip_code="45402",
        coverages=[
            cov("021", "HMO", "CFC", "20260120", rate_cell="0260120004"),
            cov("021", "MM", "CFC", "20260120", rate_cell="0260120004"),
        ],
    ))

    # Elderly member (85+), ODM placeholder address → triggers OH-VAL-105,
    # XXXXXXXXXX rate cell → triggers OH-VAL-103
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0400000005", elig_date="20260301",
        last_name="BAKER", first_name="HELEN", middle="M",
        ssn="505050505", dob="19400305", gender="F",
        street="50 W. TOWN ST", apt="SUITE 400",
        city="COLUMBUS", state="OH", zip_code="43215",
        coverages=[
            cov("021", "HMO", "ABD", "20260301", rate_cell="XXXXXXXXXX"),
        ],
    ))

    # Member with 3 coverages: medical + dental + behavioral health
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0400000006", elig_date="20260301",
        last_name="OBRIEN", first_name="SEAN", middle="P",
        ssn="606060606", dob="19850519", gender="M",
        street="4567 CEDAR LANE", apt=None,
        city="AKRON", state="OH", zip_code="44308",
        coverages=[
            cov("021", "HMO", "CFC", "20260301", rate_cell="0260301006"),
            cov("021", "MM", "CFC", "20260301", rate_cell="0260301006"),
            cov("021", "HLT", "BH-SUD", "20260301", rate_cell="0260301006"),
        ],
    ))

    return build_file("260315", "20260315", 4, "OHEDGE20260315", "2", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 5: Error File (Changes file, 5 members — intentional errors)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_5():
    members = []

    # ERROR 1: Missing NM1 segment — structural error
    segs = []
    segs.append("INS*Y*18*021*28*A***FT~")
    segs.append("REF*0F*9A0500000001~")
    segs.append("DTP*336*D8*20260301~")
    # NM1 intentionally omitted
    segs.append("DMG*D8*19900101*F~")
    segs.append("N3*1234 ERROR STREET~")
    segs.append("N4*COLUMBUS*OH*43215~")
    segs.append("HD*021**HMO*CFC*EMP~")
    segs.append("DTP*348*D8*20260301~")
    segs.append("DTP*349*D8*99991231~")
    segs.append("REF*1L*0260301E01~")
    members.append(segs)

    # ERROR 2: Short Medicaid ID (8 chars, not 12) → OH-VAL-001 Critical
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A050002", elig_date="20260301",
        last_name="ERRORTEST", first_name="BADID", middle="B",
        ssn="999000002", dob="19850515", gender="M",
        street="5678 ERROR AVENUE", apt=None,
        city="CLEVELAND", state="OH", zip_code="44102",
        coverages=[
            cov("021", "HMO", "CFC", "20260301", rate_cell="0260301E02"),
        ],
    ))

    # ERROR 3: Invalid DOB (19901332 — month 13, day 32)
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0500000003", elig_date="20260301",
        last_name="ERRORTEST", first_name="BADDATE", middle="C",
        ssn="999000003", dob="19901332", gender="F",
        street="910 ERROR BOULEVARD", apt=None,
        city="DAYTON", state="OH", zip_code="45402",
        coverages=[
            cov("021", "HMO", "CFC", "20260301", rate_cell="0260301E03"),
        ],
    ))

    # ERROR 4: No coverages (missing HD segment) → OH-VAL-005 Critical
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0500000004", elig_date="20260301",
        last_name="ERRORTEST", first_name="NOCOV", middle="D",
        ssn="999000004", dob="19880101", gender="M",
        street="2345 ERROR ROAD", apt=None,
        city="TOLEDO", state="OH", zip_code="43604",
        coverages=[],  # No coverages
    ))

    # VALID: Normal member — verifies partial file processing
    members.append(build_member(
        ins03="021", ins04="28", medicaid_id="9A0500000005", elig_date="20260301",
        last_name="GOODRECORD", first_name="VALID", middle="A",
        ssn="999000005", dob="19920715", gender="F",
        street="1234 SUCCESS STREET", apt=None,
        city="COLUMBUS", state="OH", zip_code="43215",
        coverages=[
            cov("021", "HMO", "CFC", "20260301", rate_cell="0260301005"),
            cov("021", "MM", "CFC", "20260301", rate_cell="0260301005"),
        ],
    ))

    return build_file("260320", "20260320", 5, "OHERROR20260320", "2", members)


# ═══════════════════════════════════════════════════════════════════════
# FILE 6: Large Batch — Full File (BGN08=4, 50 members, all INS03=030)
# ═══════════════════════════════════════════════════════════════════════

def generate_file_6():
    random.seed(42)  # deterministic for reproducibility
    members = []

    # Plan code based on category:
    # ABD/DUAL/SSI → ABD plan code, others → CFC
    def plan_for_cat(rate_cat):
        if rate_cat in ("ABD", "DUAL", "SSI-A"):
            return "ABD"
        return "CFC"

    # Rate category distribution (weighted pool)
    rate_cat_weights = [
        ("CFC",  18),  # TANF + Expansion children/families
        ("ABD",  12),  # Aged/Blind/Disabled + SSI + Dual
        ("OHR",   5),  # Other managed care
        ("CFC",  15),  # More CFC for variety
    ]
    rate_pool = []
    for code, weight in rate_cat_weights:
        rate_pool.extend([code] * weight)

    for i in range(50):
        idx = i + 1
        ssn = f"7{idx:08d}"
        medicaid_id = f"9A06{idx:08d}"
        plan_code = random.choice(rate_pool)

        # Generate appropriate DOB
        if plan_code == "ABD":
            year = random.randint(1935, 1960)
        elif plan_code == "OHR":
            year = random.randint(1970, 2000)
        else:
            # CFC: mix of children and adults
            if random.random() < 0.4:
                year = random.randint(2008, 2024)
            else:
                year = random.randint(1970, 2000)
        dob = f"{year}{random.randint(1,12):02d}{random.randint(1,28):02d}"

        gender = random.choice(["M", "F"])
        first_name = random.choice(FIRST_NAMES_F if gender == "F" else FIRST_NAMES_M)
        last_name = random.choice(LAST_NAMES)
        middle = random.choice(MIDDLE_INITIALS)
        loc = random.choice(OH_LOCATIONS)
        street = random.choice(STREETS)
        apt = random.choice(APTS)
        rate_cell = f"04010{idx:05d}"

        # Full file: all 030
        covs = [cov("030", "HMO", plan_code, "20260401", rate_cell=rate_cell)]
        # ~70% get dental too
        if random.random() < 0.7:
            covs.append(cov("030", "MM", plan_code, "20260401", rate_cell=rate_cell))

        members.append(build_member(
            ins03="030", ins04="28", medicaid_id=medicaid_id, elig_date="20260401",
            last_name=last_name, first_name=first_name, middle=middle,
            ssn=ssn, dob=dob, gender=gender,
            street=street, apt=apt,
            city=loc[0], state=loc[1], zip_code=loc[2],
            coverages=covs,
        ))

    return build_file("260401", "20260401", 6, "OHBATCH20260401", "4", members)


# ═══════════════════════════════════════════════════════════════════════
# Generate all files
# ═══════════════════════════════════════════════════════════════════════

def write_file(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    size = os.path.getsize(path)
    sha = hashlib.sha256(content.encode()).hexdigest()
    ins_count = content.count("INS*Y*18*")
    print(f"  {filename}: {ins_count} members, {size:,} bytes | SHA-256: {sha[:16]}...")


if __name__ == "__main__":
    print("Generating Ohio Medicaid EDI 834 Test Files (ODM v13.1 conventions)...\n")

    print("File 1: Standard Enrollments — Changes file, 8 members")
    write_file("OH_834_STANDARD_ENROLL_20260201.edi", generate_file_1())

    print("File 2: Mixed Maintenance — Changes file, 6 members")
    write_file("OH_834_MIXED_MAINT_20260215.edi", generate_file_2())

    print("File 3: Retro Changes — Changes file, 5 members")
    write_file("OH_834_RETRO_CHANGES_20260301.edi", generate_file_3())

    print("File 4: Edge Cases — Changes file, 6 members")
    write_file("OH_834_EDGE_CASES_20260315.edi", generate_file_4())

    print("File 5: Error File — Changes file, 5 members (3 with errors)")
    write_file("OH_834_ERROR_FILE_20260320.edi", generate_file_5())

    print("File 6: Large Batch — Full file (BGN08=4), 50 members")
    write_file("OH_834_LARGE_BATCH_20260401.edi", generate_file_6())

    print("\nDone. All files written to:", OUTPUT_DIR)
