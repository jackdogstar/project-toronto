#!/usr/bin/env python3
"""
Generate realistic Ohio 834 test files that exercise EVERY feature of the parser.

These files populate all optional segments and fields:
- REF*23 (aid category), REF*3H (IE case number), REF*6O (alternate ID),
  REF*F6 (Medicare ID), REF*DX (county), REF*Q4 (linked secondary ID),
  REF*17 (newborn mother ID)
- DTP*300 (redetermination), DTP*473/474 (Medicaid begin/end)
- DMG05 race codes with ^ repetition separator
- N4 county code (CY qualifier)
- PER contacts (phone, email)
- Loop 2100G responsible person (parent, legal rep, org)
- Loop 2310 provider within coverage
- Loop 2320 COB with Loop 2330 insurer
- Loop 2700/2710 reporting categories (living arrangement, pregnancy, work req)
- AMT*D2 patient liability
- INS12 death date
- Multiple INS04 assignment reason codes
- All validation rules triggered
"""

import os
import hashlib

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def isa(date_yymmdd, control_num):
    return (
        f"ISA*00*          *00*          "
        f"*ZZ*OHMMIS         *ZZ*0003150        "
        f"*{date_yymmdd}*1230*^*00501*{control_num:09d}*0*P*:~"
    )


def gs(date, group_ctl="1"):
    return f"GS*BE*OHMMIS*0003150*{date}*1230*{group_ctl}*X*005010X220A1~"


def header(ref_id, date, bgn08, contract="OH-MCO-CARESOURCE-001"):
    return [
        f"BGN*00*{ref_id}*{date}*1230****{bgn08}~",
        f"REF*38*{contract}~",
        f"DTP*007*D8*{date}~",
        f"N1*P5*OHIO DEPARTMENT OF MEDICAID*FI*314589267~",
        f"N1*IN*CARESOURCE*FI*311234567~",
    ]


def member(ins03, ins04, medicaid_id, elig_date,
           last, first, middle, ssn, dob, gender,
           street1, street2, city, state, zipcode,
           coverages,
           employment_status="FT",
           death_date=None,
           aid_category_ref=None,
           ie_case_number=None,
           alternate_id=None,
           medicare_id=None,
           county_of_elig=None,
           linked_secondary_id=None,
           newborn_mother_id=None,
           redetermination_date=None,
           medicaid_begin=None,
           medicaid_end=None,
           race_codes=None,
           county_code=None,
           contacts=None,
           responsible_person=None,
           cob_records=None,
           reporting_categories=None):
    """Build a complete member block with all optional segments."""
    segs = []

    # ── Loop 2000: INS ──
    ins = f"INS*Y*18*{ins03}*{ins04}*A***{employment_status}"
    if death_date:
        ins += f"****{death_date}"
    segs.append(ins + "~")

    # ── Loop 2000: REF segments ──
    segs.append(f"REF*0F*{medicaid_id}~")
    if newborn_mother_id:
        segs.append(f"REF*17*{newborn_mother_id}~")
    if aid_category_ref:
        segs.append(f"REF*23*{aid_category_ref}~")
    if ie_case_number:
        segs.append(f"REF*3H*{ie_case_number}~")
    if alternate_id:
        segs.append(f"REF*6O*{alternate_id}~")
    if medicare_id:
        segs.append(f"REF*F6*{medicare_id}~")
    if county_of_elig:
        segs.append(f"REF*DX*{county_of_elig}~")
    if linked_secondary_id:
        segs.append(f"REF*Q4*{linked_secondary_id}~")

    # ── Loop 2000: DTP dates ──
    segs.append(f"DTP*336*D8*{elig_date}~")
    if redetermination_date:
        segs.append(f"DTP*300*D8*{redetermination_date}~")
    if medicaid_begin:
        segs.append(f"DTP*473*D8*{medicaid_begin}~")
    if medicaid_end:
        segs.append(f"DTP*474*D8*{medicaid_end}~")

    # ── Loop 2100A: NM1 ──
    if middle:
        segs.append(f"NM1*IL*1*{last}*{first}*{middle}***34*{ssn}~")
    else:
        segs.append(f"NM1*IL*1*{last}*{first}****34*{ssn}~")

    # ── Loop 2100A: DMG with optional race codes ──
    dmg = f"DMG*D8*{dob}*{gender}"
    if race_codes:
        dmg += f"**{'^'.join(race_codes)}"
    segs.append(dmg + "~")

    # ── Loop 2100A: Address ──
    if street2:
        segs.append(f"N3*{street1}*{street2}~")
    else:
        segs.append(f"N3*{street1}~")

    n4 = f"N4*{city}*{state}*{zipcode}"
    if county_code:
        n4 += f"**CY*{county_code}"
    segs.append(n4 + "~")

    # ── Loop 2100A: PER contacts ──
    if contacts:
        for contact in contacts:
            per_parts = ["PER*IP*"]
            # Format: PER*IP*name*qual1*num1*qual2*num2
            name = contact.get("name", "")
            pairs = contact.get("pairs", [])
            per = f"PER*IP*{name}"
            for qual, num in pairs:
                per += f"*{qual}*{num}"
            segs.append(per + "~")

    # ── Loop 2100G: Responsible Person (optional) ──
    if responsible_person:
        rp = responsible_person
        tc = rp["type_code"]
        if rp.get("is_org"):
            segs.append(f"NM1*{tc}*2*{rp['org_name']}~")
        else:
            rp_mid = f"*{rp['middle']}" if rp.get('middle') else ""
            segs.append(f"NM1*{tc}*1*{rp['last']}*{rp['first']}{rp_mid}~")
        if rp.get("street"):
            if rp.get("street2"):
                segs.append(f"N3*{rp['street']}*{rp['street2']}~")
            else:
                segs.append(f"N3*{rp['street']}~")
            segs.append(f"N4*{rp['city']}*{rp['state']}*{rp['zip']}~")
        if rp.get("phone"):
            segs.append(f"PER*IP**TE*{rp['phone']}~")

    # ── Loop 2300: Coverages ──
    for cov in coverages:
        segs.append(f"HD*{cov['hd01']}**{cov['ins_line']}*{cov['plan']}*EMP~")
        segs.append(f"DTP*348*D8*{cov['start']}~")
        if cov.get("end"):
            segs.append(f"DTP*349*D8*{cov['end']}~")
        if cov.get("rate_cell"):
            segs.append(f"REF*1L*{cov['rate_cell']}~")
        if cov.get("patient_liability") is not None:
            segs.append(f"AMT*D2*{cov['patient_liability']}~")
        # Loop 2310: Provider (optional)
        if cov.get("provider"):
            p = cov["provider"]
            segs.append(f"LX*{p.get('seq', '1')}~")
            segs.append(f"NM1*{p['qual']}*{p['entity_type']}*{p['name']}****{p['id_qual']}*{p['id']}~")

    # ── Loop 2320: COB (optional, must come after all coverages) ──
    if cob_records:
        for cob in cob_records:
            segs.append(f"COB*{cob['payer_resp']}**{cob['cob_code']}~")
            if cob.get("group_number"):
                segs.append(f"REF*6P*{cob['group_number']}~")
            if cob.get("other_ssn"):
                segs.append(f"REF*SY*{cob['other_ssn']}~")
            if cob.get("insurer_name"):
                # Loop 2330
                segs.append(f"NM1*IN*2*{cob['insurer_name']}~")

    # ── Loop 2700/2710: Reporting Categories (optional, must come after COB) ──
    if reporting_categories:
        for i, rc in enumerate(reporting_categories, 1):
            segs.append(f"LX*{i}~")  # Loop 2700
            segs.append(f"N1*75*{rc['category']}~")  # Loop 2710
            segs.append(f"REF*{rc['ref_qual']}*{rc['ref_value']}~")
            if rc.get("date"):
                segs.append(f"DTP*007*D8*{rc['date']}~")
            elif rc.get("date_range"):
                segs.append(f"DTP*007*RD8*{rc['date_range']}~")

    return segs


def build_file(isa_seg, gs_seg, tx_blocks, isa_control):
    """Build complete file. tx_blocks = list of (header_segs, member_blocks) tuples."""
    all_segs = [isa_seg, gs_seg]

    for tx_idx, (hdr_segs, mbr_blocks) in enumerate(tx_blocks, 1):
        st_ctl = f"{tx_idx:04d}"
        body = list(hdr_segs)
        for block in mbr_blocks:
            body.extend(block)
        seg_count = len(body) + 2
        all_segs.append(f"ST*834*{st_ctl}*005010X220A1~")
        all_segs.extend(body)
        all_segs.append(f"SE*{seg_count}*{st_ctl}~")

    all_segs.append(f"GE*{len(tx_blocks)}*1~")
    all_segs.append(f"IEA*1*{isa_control:09d}~")
    return "".join(all_segs)


def cov(hd01, ins_line, plan, start, end="99991231", rate_cell=None,
        patient_liability=None, provider=None):
    d = {"hd01": hd01, "ins_line": ins_line, "plan": plan,
         "start": start, "end": end, "rate_cell": rate_cell}
    if patient_liability is not None:
        d["patient_liability"] = patient_liability
    if provider:
        d["provider"] = provider
    return d


# ═══════════════════════════════════════════════════════════════════════
# FILE 1: Realistic Full Roster — exercises ALL features
# BGN08=4, 15 members, all INS03=030
# ═══════════════════════════════════════════════════════════════════════

def generate_full_roster():
    hdr = header("OHFULL20260501", "20260501", "4")
    members = []

    # ── Member 1: Standard TANF adult with aid category, race, contacts ──
    members.append(member(
        "030", "XN", "9A0600100001", "20260501",
        "JOHNSON", "MARIA", "A", "123456789", "19840315", "F",
        "1234 MAPLE STREET", "APT 4B", "COLUMBUS", "OH", "43215",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101001"),
         cov("030", "MM", "CFC", "20260101", rate_cell="0260101001")],
        aid_category_ref="TANF 20250801",
        county_of_elig="039",
        race_codes=["C"],
        county_code="039",
        contacts=[{"name": "MARIA JOHNSON", "pairs": [("TE", "6145551234"), ("EM", "MJOHNSON@EMAIL.COM")]}],
        medicaid_begin="20250801",
        redetermination_date="20260801",
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "01", "date": "20250801"},
        ],
        # Need COB before reporting for loop parser — use minimal COB
        cob_records=[{"payer_resp": "S", "cob_code": "5"}],
    ))

    # ── Member 2: Dual-eligible elderly ABD with Medicare, COB, institutional ──
    # Triggers: OH-VAL-201 (Medicare), OH-VAL-203 (institutional living)
    members.append(member(
        "030", "XN", "9A0600100002", "20260501",
        "WILLIAMS", "ROBERT", "T", "234567891", "19420722", "M",
        "1739 HAWTHORN STREET", None, "CLEVELAND", "OH", "44102",
        [cov("030", "HMO", "ABD", "20230601", rate_cell="0230601002"),
         cov("030", "MM", "ABD", "20230601", rate_cell="0230601002",
             patient_liability="125.50")],
        aid_category_ref="ABD 20230601",
        medicare_id="1EG4TE5MK72",
        county_of_elig="035",
        race_codes=["B"],
        county_code="035",
        medicaid_begin="20230601",
        redetermination_date="20260601",
        cob_records=[{
            "payer_resp": "P",
            "cob_code": "1",
            "group_number": "GRP-MEDICARE-A",
            "other_ssn": "234567891",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "10",
             "date": "20240101"},
        ],
    ))

    # ── Member 3: Child with responsible person (parent) ──
    members.append(member(
        "030", "XN", "9A0600100003", "20260501",
        "GARCIA", "ISABELLA", "M", "345678912", "20200515", "F",
        "910 ELM BOULEVARD", "UNIT 3A", "CINCINNATI", "OH", "45202",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101003"),
         cov("030", "MM", "CFC", "20260101", rate_cell="0260101003")],
        aid_category_ref="TANF 20200601",
        county_of_elig="061",
        race_codes=["H", "C"],
        county_code="061",
        medicaid_begin="20200601",
        responsible_person={
            "type_code": "S1",
            "last": "GARCIA",
            "first": "CARLOS",
            "middle": "R",
            "street": "910 ELM BOULEVARD",
            "street2": "UNIT 3A",
            "city": "CINCINNATI",
            "state": "OH",
            "zip": "45202",
            "phone": "5135559876",
        },
    ))

    # ── Member 4: Newborn with mother ID, auto-enrollment ──
    members.append(member(
        "030", "28", "9A0600100004", "20260501",
        "MARTINEZ", "BABY", None, "456789123", "20260410", "M",
        "2345 PINE ROAD", None, "DAYTON", "OH", "45402",
        [cov("030", "HMO", "CFC", "20260410", rate_cell="0260410004")],
        newborn_mother_id="9A0600100099",
        aid_category_ref="TANF 20260410",
        county_of_elig="057",
        medicaid_begin="20260410",
        responsible_person={
            "type_code": "S1",
            "last": "MARTINEZ",
            "first": "LUCIA",
            "street": "2345 PINE ROAD",
            "city": "DAYTON",
            "state": "OH",
            "zip": "45402",
        },
    ))

    # ── Member 5: Former foster youth with alternate ID ──
    # Triggers: OH-VAL-202 (alternate ID)
    members.append(member(
        "030", "XN", "9A0600100005", "20260501",
        "BROWN", "JAYDEN", "R", "567891234", "20040315", "M",
        "4567 CEDAR LANE", None, "TOLEDO", "OH", "43604",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101005"),
         cov("030", "MM", "CFC", "20260101", rate_cell="0260101005"),
         cov("030", "HLT", "BH-SUD", "20260101", rate_cell="0260101005")],
        alternate_id="FC2019004521",
        aid_category_ref="CFC 20200401",
        county_of_elig="095",
        race_codes=["B", "E"],
        county_code="095",
        medicaid_begin="20200401",
    ))

    # ── Member 6: Deceased member with death date ──
    # Death reason code 3, with death date in INS12
    members.append(member(
        "030", "3", "9A0600100006", "20260501",
        "DAVIS", "PATRICIA", "L", "678912345", "19680418", "F",
        "7890 BIRCH DRIVE", "APT 12", "AKRON", "OH", "44308",
        [cov("030", "HMO", "ABD", "20240101", "20260415", "0240101006")],
        death_date="20260415",
        aid_category_ref="ABD 20240101",
        county_of_elig="153",
        race_codes=["C"],
        medicaid_begin="20240101",
        medicaid_end="20260415",
    ))

    # ── Member 7: Pregnant woman with reporting categories ──
    members.append(member(
        "030", "XN", "9A0600100007", "20260501",
        "THOMPSON", "EMILY", "K", "789123456", "19950909", "F",
        "1122 WALNUT STREET", None, "YOUNGSTOWN", "OH", "44503",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101007"),
         cov("030", "MM", "CFC", "20260101", rate_cell="0260101007")],
        aid_category_ref="TANF 20250901",
        county_of_elig="099",
        race_codes=["O"],
        medicaid_begin="20250901",
        redetermination_date="20261201",
        cob_records=[{"payer_resp": "S", "cob_code": "5"}],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "01", "date": "20250901"},
            {"category": "PREGNANT", "ref_qual": "ZZ", "ref_value": "Y",
             "date_range": "20260201-20261001"},
        ],
    ))

    # ── Member 8: Incarcerated member ──
    # Assignment reason 9 (incarcerated), living arrangement 14 or 15
    members.append(member(
        "030", "9", "9A0600100008", "20260501",
        "WILSON", "JAMES", "D", "891234567", "19880127", "M",
        "50 W. TOWN ST", "SUITE 400", "COLUMBUS", "OH", "43215",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="XXXXXXXXXX")],
        aid_category_ref="EXP 20240101",
        county_of_elig="049",
        medicaid_begin="20240101",
        cob_records=[{"payer_resp": "S", "cob_code": "5"}],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "14", "date": "20260301"},
        ],
    ))
    # Note: ODM placeholder address → OH-VAL-105, XXXXXXXXXX → OH-VAL-103

    # ── Member 9: Member with patient liability on MM coverage ──
    members.append(member(
        "030", "XN", "9A0600100009", "20260501",
        "PEREZ", "ROSA", "E", "111223344", "19500812", "F",
        "9876 WILLOW STREET", None, "COLUMBUS", "OH", "43201",
        [cov("030", "HMO", "ABD", "20250301", rate_cell="0250301009"),
         cov("030", "MM", "ABD", "20250301", rate_cell="0250301009",
             patient_liability="350.00")],
        aid_category_ref="ABD 20250301",
        county_of_elig="049",
        race_codes=["H"],
        county_code="049",
        medicaid_begin="20250301",
        redetermination_date="20260301",
    ))

    # ── Member 10: Linked secondary ID member ──
    # Triggers: OH-VAL-107 (linked ID)
    members.append(member(
        "030", "XN", "9A0600100010", "20260501",
        "NGUYEN", "DAVID", "H", "222334455", "19870304", "M",
        "6543 MAGNOLIA AVENUE", "APT 7", "CLEVELAND", "OH", "44113",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101010")],
        linked_secondary_id="9A0600199999",
        aid_category_ref="EXP 20250601",
        county_of_elig="035",
        medicaid_begin="20250601",
    ))

    # ── Member 11: Provider in coverage (Loop 2310) ──
    members.append(member(
        "030", "XN", "9A0600100011", "20260501",
        "TAYLOR", "MICHELLE", "N", "333445566", "19890629", "F",
        "3210 SYCAMORE ROAD", None, "DAYTON", "OH", "45402",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101011",
             provider={"seq": "1", "qual": "P3", "entity_type": "2",
                       "name": "PREMIER HEALTH NETWORK", "id_qual": "FI",
                       "id": "311234567"})],
        aid_category_ref="TANF 20250101",
        county_of_elig="057",
        medicaid_begin="20250101",
    ))

    # ── Member 12: Waiver coverage ──
    members.append(member(
        "030", "XN", "9A0600100012", "20260501",
        "CLARK", "STEVEN", "W", "444556677", "19650114", "M",
        "1598 CHESTNUT BOULEVARD", None, "TOLEDO", "OH", "43604",
        [cov("030", "HMO", "ABD", "20240601", rate_cell="0240601012"),
         cov("030", "AH", "WVR-A1", "20240601", rate_cell="0240601012")],
        aid_category_ref="ABD 20240601",
        medicare_id="2FK8RR4JL91",
        county_of_elig="095",
        race_codes=["C"],
        medicaid_begin="20240601",
        redetermination_date="20260601",
        cob_records=[{
            "payer_resp": "P",
            "cob_code": "1",
            "group_number": "GRP-MEDICARE-AB",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "16", "date": "20240601"},
        ],
    ))

    # ── Member 13: Responsible person = organization ──
    members.append(member(
        "030", "XN", "9A0600100013", "20260501",
        "MOORE", "AIDEN", "J", "555667788", "20130422", "M",
        "7531 HEMLOCK LANE", "UNIT 15C", "AKRON", "OH", "44308",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101013"),
         cov("030", "MM", "CFC", "20260101", rate_cell="0260101013")],
        aid_category_ref="CFC 20210601",
        county_of_elig="153",
        race_codes=["A", "C"],
        medicaid_begin="20210601",
        responsible_person={
            "type_code": "QD",
            "is_org": True,
            "org_name": "SUMMIT COUNTY CHILDREN SERVICES",
            "street": "264 S ARLINGTON ST",
            "city": "AKRON",
            "state": "OH",
            "zip": "44306",
            "phone": "3303791234",
        },
    ))

    # ── Member 14: Multiple race codes, IE case number ──
    members.append(member(
        "030", "XN", "9A0600100014", "20260501",
        "HARRIS", "KEVIN", "B", "666778899", "19930817", "M",
        "8642 LAUREL DRIVE", None, "CINCINNATI", "OH", "45219",
        [cov("030", "HMO", "CFC", "20260101", rate_cell="0260101014"),
         cov("030", "MM", "CFC", "20260101", rate_cell="0260101014")],
        ie_case_number="IE2024-039-00458",
        aid_category_ref="EXP 20240901",
        county_of_elig="061",
        race_codes=["B", "I", "H"],
        county_code="061",
        medicaid_begin="20240901",
        contacts=[{"name": "KEVIN HARRIS", "pairs": [("TE", "5135557890")]}],
    ))

    # ── Member 15: Complex — multiple reporting, COB, contacts ──
    members.append(member(
        "030", "XN", "9A0600100015", "20260501",
        "WRIGHT", "ANNA", "R", "777889900", "19440722", "F",
        "3344 ASH AVENUE", None, "COLUMBUS", "OH", "43201",
        [cov("030", "HMO", "ABD", "20220101", rate_cell="0220101015"),
         cov("030", "MM", "ABD", "20220101", rate_cell="0220101015",
             patient_liability="275.00"),
         cov("030", "AJ", "MEDICARE-B", "20220101", rate_cell="0220101015")],
        medicare_id="3HJ9KK2LP44",
        aid_category_ref="ABD 20220101",
        county_of_elig="049",
        race_codes=["O"],
        county_code="049",
        medicaid_begin="20220101",
        redetermination_date="20260101",
        contacts=[
            {"name": "ANNA WRIGHT", "pairs": [("TE", "6145554321")]},
            {"name": "SARAH WRIGHT", "pairs": [("TE", "6145559876"), ("EM", "SWRIGHT@FAMILY.COM")]},
        ],
        responsible_person={
            "type_code": "LR",
            "last": "WRIGHT",
            "first": "SARAH",
            "middle": "E",
            "street": "3344 ASH AVENUE",
            "city": "COLUMBUS",
            "state": "OH",
            "zip": "43201",
            "phone": "6145559876",
        },
        cob_records=[
            {
                "payer_resp": "P",
                "cob_code": "1",
                "group_number": "GRP-MCARE-AB",
                "other_ssn": "777889900",
                "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
            },
            {
                "payer_resp": "T",
                "cob_code": "4",
                "group_number": "GRP-AETNA-2024",
                "insurer_name": "AETNA HEALTH INSURANCE",
            },
        ],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "09",
             "date": "20230601"},
            {"category": "WORK REQUIREMENT - MANDATORY", "ref_qual": "ZZ", "ref_value": "EXEMPT-AGE",
             "date": "20220101"},
        ],
    ))

    return build_file(isa("260501", 101), gs("20260501"), [(hdr, members)], 101)


# ═══════════════════════════════════════════════════════════════════════
# FILE 2: Realistic Changes — mixed maintenance with all features
# BGN08=2, 10 members
# ═══════════════════════════════════════════════════════════════════════

def generate_changes():
    hdr = header("OHCHG20260515", "20260515", "2")
    members = []

    # ── M1: New enrollment (021) — adult with full details ──
    members.append(member(
        "021", "14", "9A0600200001", "20260515",
        "ROBINSON", "ANGELA", "P", "111111111", "19970210", "F",
        "4826 DOGWOOD COURT", None, "SPRINGFIELD", "OH", "45502",
        [cov("021", "HMO", "CFC", "20260515", rate_cell="0260515001"),
         cov("021", "MM", "CFC", "20260515", rate_cell="0260515001")],
        aid_category_ref="EXP 20260515",
        county_of_elig="023",
        race_codes=["B"],
        county_code="023",
        medicaid_begin="20260515",
        redetermination_date="20270515",
        contacts=[{"name": "ANGELA ROBINSON", "pairs": [("TE", "9375551234")]}],
    ))

    # ── M2: New enrollment (021) — child with responsible person ──
    members.append(member(
        "021", "16", "9A0600200002", "20260515",
        "LEWIS", "SOPHIA", None, "222222222", "20190815", "F",
        "1739 HAWTHORN STREET", None, "MANSFIELD", "OH", "44902",
        [cov("021", "HMO", "CFC", "20260515", rate_cell="0260515002"),
         cov("021", "MM", "CFC", "20260515", rate_cell="0260515002")],
        aid_category_ref="TANF 20260515",
        county_of_elig="139",
        race_codes=["C", "H"],
        medicaid_begin="20260515",
        responsible_person={
            "type_code": "S1",
            "last": "LEWIS",
            "first": "JENNIFER",
            "street": "1739 HAWTHORN STREET",
            "city": "MANSFIELD",
            "state": "OH",
            "zip": "44902",
        },
    ))

    # ── M3: Termination (024) — lost eligibility ──
    members.append(member(
        "024", "7", "9A0600200003", "20260515",
        "WALKER", "ASHLEY", "R", "333333333", "19850515", "F",
        "2468 HICKORY WAY", None, "LIMA", "OH", "45801",
        [cov("024", "HMO", "CFC", "20240901", "20260531", "0240901003"),
         cov("024", "MM", "CFC", "20240901", "20260531", "0240901003")],
        aid_category_ref="TANF 20240901",
        county_of_elig="003",
        medicaid_begin="20240901",
        medicaid_end="20260531",
    ))

    # ── M4: Termination (024) — death with date ──
    members.append(member(
        "024", "3", "9A0600200004", "20260515",
        "YOUNG", "STEPHANIE", "L", "444444444", "19520712", "F",
        "1357 POPLAR DRIVE", "APT 2", "ZANESVILLE", "OH", "43701",
        [cov("024", "HMO", "ABD", "20220601", "20260502", "0220601004")],
        death_date="20260502",
        aid_category_ref="ABD 20220601",
        county_of_elig="119",
        race_codes=["C"],
        medicaid_begin="20220601",
        medicaid_end="20260502",
    ))

    # ── M5: Change (001) — address update, new county ──
    members.append(member(
        "001", "EC", "9A0600200005", "20260515",
        "ALLEN", "GEORGE", "F", "555555555", "19430825", "M",
        "5566 CHERRY LANE", None, "COLUMBUS", "OH", "43215",
        [cov("001", "HMO", "ABD", "20230101", rate_cell="0230101005"),
         cov("001", "MM", "ABD", "20230101", rate_cell="0230101005",
             patient_liability="200.00")],
        medicare_id="4PQ2RR8NT66",
        aid_category_ref="ABD 20230101",
        county_of_elig="049",
        county_code="049",
        medicaid_begin="20230101",
        cob_records=[{
            "payer_resp": "P",
            "cob_code": "1",
            "group_number": "GRP-MCARE-B",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "01", "date": "20260501"},
        ],
    ))

    # ── M6: Reinstatement — INS03=021, HD01=025 ──
    members.append(member(
        "021", "17", "9A0600200006", "20260515",
        "KING", "DAVID", "S", "666666666", "19991104", "M",
        "8642 LAUREL DRIVE", None, "SPRINGFIELD", "OH", "45502",
        [cov("025", "HMO", "CFC", "20260515", rate_cell="0260515006"),
         cov("025", "MM", "CFC", "20260515", rate_cell="0260515006")],
        aid_category_ref="EXP 20250601",
        county_of_elig="023",
        medicaid_begin="20250601",
    ))

    # ── M7: New dual-eligible with COB and reporting ──
    members.append(member(
        "021", "AJ", "9A0600200007", "20260515",
        "FLORES", "RUTH", "R", "777777777", "19481003", "F",
        "5566 CHERRY LANE", "SUITE 200", "AKRON", "OH", "44308",
        [cov("021", "HMO", "ABD", "20260515", rate_cell="0260515007"),
         cov("021", "MM", "ABD", "20260515", rate_cell="0260515007",
             patient_liability="450.00"),
         cov("021", "AH", "WVR-9", "20260515", rate_cell="0260515007")],
        medicare_id="5ST3UU9OV88",
        aid_category_ref="ABD 20260515",
        county_of_elig="153",
        race_codes=["O"],
        county_code="153",
        medicaid_begin="20260515",
        redetermination_date="20270515",
        cob_records=[{
            "payer_resp": "P",
            "cob_code": "1",
            "group_number": "GRP-MCARE-AB",
            "other_ssn": "777777777",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "19",
             "date": "20260401"},
        ],
    ))

    # ── M8: Change (001) — rate category adjustment ──
    members.append(member(
        "001", "25", "9A0600200008", "20260515",
        "SCOTT", "CAROL", "L", "888888888", "19811117", "F",
        "2345 PINE ROAD", None, "COLUMBUS", "OH", "43215",
        [cov("001", "HMO", "CFC", "20250601", rate_cell="0250601008"),
         cov("001", "MM", "CFC", "20250601", rate_cell="0250601008")],
        aid_category_ref="TANF 20250601",
        county_of_elig="049",
        race_codes=["B", "C"],
        medicaid_begin="20250601",
    ))

    # ── M9: Disenrollment by ODM staff ──
    members.append(member(
        "024", "6", "9A0600200009", "20260515",
        "MITCHELL", "DOROTHY", "L", "999999999", "19710220", "F",
        "1739 HAWTHORN STREET", "SUITE 200", "DAYTON", "OH", "45402",
        [cov("024", "HMO", "CFC", "20250101", "20260531", "0250101009")],
        aid_category_ref="TANF 20250101",
        county_of_elig="057",
        medicaid_begin="20250101",
        medicaid_end="20260531",
    ))

    # ── M10: Voluntary MCE change ──
    members.append(member(
        "001", "18", "9A0600200010", "20260515",
        "CARTER", "PATRICIA", "S", "101010101", "19790727", "F",
        "5566 CHERRY LANE", "FL 3", "TOLEDO", "OH", "43604",
        [cov("001", "HMO", "OHR", "20250801", rate_cell="0250801010")],
        aid_category_ref="CFC 20250801",
        county_of_elig="095",
        race_codes=["C"],
        medicaid_begin="20250801",
    ))

    return build_file(isa("260515", 102), gs("20260515"), [(hdr, members)], 102)


# ═══════════════════════════════════════════════════════════════════════
# FILE 3: Multi-Transaction — 2 ST/SE blocks, different providers
# Tests envelope parsing with multiple transaction sets
# ═══════════════════════════════════════════════════════════════════════

def generate_multi_tx():
    # Transaction 1: CareSource members
    hdr1 = [
        f"BGN*00*OHMULTI1-20260601*20260601*1230****2~",
        f"REF*38*OH-MCO-CARESOURCE-001~",
        f"DTP*007*D8*20260601~",
        f"N1*P5*OHIO DEPARTMENT OF MEDICAID*FI*314589267~",
        f"N1*IN*CARESOURCE*FI*311234567~",
    ]

    tx1_members = [
        member(
            "021", "14", "9A0600300001", "20260601",
            "ADAMS", "JENNIFER", "L", "201020102", "19880315", "F",
            "1234 MAPLE STREET", None, "COLUMBUS", "OH", "43215",
            [cov("021", "HMO", "CFC", "20260601", rate_cell="0260601001"),
             cov("021", "MM", "CFC", "20260601", rate_cell="0260601001")],
            aid_category_ref="EXP 20260601",
            county_of_elig="049",
            race_codes=["C"],
            medicaid_begin="20260601",
        ),
        member(
            "021", "16", "9A0600300002", "20260601",
            "NELSON", "WILLIAM", "R", "302030302", "19750920", "M",
            "5678 OAK AVENUE", "APT 4B", "CLEVELAND", "OH", "44102",
            [cov("021", "HMO", "ABD", "20260601", rate_cell="0260601002")],
            medicare_id="6WX4YY1QZ33",
            aid_category_ref="ABD 20260601",
            county_of_elig="035",
            medicaid_begin="20260601",
            cob_records=[{
                "payer_resp": "P",
                "cob_code": "1",
                "group_number": "GRP-MCARE-A",
                "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
            }],
            reporting_categories=[
                {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "01",
                 "date": "20260601"},
            ],
        ),
    ]

    # Transaction 2: Buckeye members (different MCE)
    hdr2 = [
        f"BGN*00*OHMULTI2-20260601*20260601*1230****2~",
        f"REF*38*OH-MCO-BUCKEYE-002~",
        f"DTP*007*D8*20260601~",
        f"N1*P5*OHIO DEPARTMENT OF MEDICAID*FI*314589267~",
        f"N1*IN*BUCKEYE COMMUNITY HEALTH PLAN*FI*314567890~",
    ]

    tx2_members = [
        member(
            "021", "28", "9A0600300003", "20260601",
            "PHILLIPS", "DANIEL", "K", "403050403", "20260520", "M",
            "910 ELM BOULEVARD", None, "CINCINNATI", "OH", "45202",
            [cov("021", "HMO", "CFC", "20260520", rate_cell="0260520003")],
            newborn_mother_id="9A0600300099",
            aid_category_ref="TANF 20260520",
            county_of_elig="061",
            medicaid_begin="20260520",
            responsible_person={
                "type_code": "S1",
                "last": "PHILLIPS",
                "first": "SARAH",
                "street": "910 ELM BOULEVARD",
                "city": "CINCINNATI",
                "state": "OH",
                "zip": "45202",
            },
        ),
        member(
            "024", "10", "9A0600300004", "20260601",
            "ROBERTS", "THOMAS", "A", "504060504", "19820111", "M",
            "2345 PINE ROAD", None, "DAYTON", "OH", "45402",
            [cov("024", "HMO", "CFC", "20240101", "20260615", "0240101004")],
            aid_category_ref="EXP 20240101",
            county_of_elig="057",
            medicaid_begin="20240101",
            medicaid_end="20260615",
        ),
        member(
            "001", "EC", "9A0600300005", "20260601",
            "GREEN", "MELISSA", "D", "605070605", "19910630", "F",
            "4567 CEDAR LANE", "UNIT 3A", "TOLEDO", "OH", "43604",
            [cov("001", "HMO", "CFC", "20250301", rate_cell="0250301005"),
             cov("001", "MM", "CFC", "20250301", rate_cell="0250301005"),
             cov("001", "HLT", "BH-SUD", "20250301", rate_cell="0250301005")],
            aid_category_ref="EXP 20250301",
            county_of_elig="095",
            race_codes=["C", "G"],
            medicaid_begin="20250301",
        ),
    ]

    return build_file(
        isa("260601", 103), gs("20260601"),
        [(hdr1, tx1_members), (hdr2, tx2_members)],
        103)


# ═══════════════════════════════════════════════════════════════════════
# Write all files
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
    print("Generating Realistic Ohio 834 Test Files...\n")

    print("File 1: Full Roster — 15 members, all features")
    write_file("OH_834_REALISTIC_FULL_20260501.edi", generate_full_roster())

    print("File 2: Changes — 10 members, mixed maintenance")
    write_file("OH_834_REALISTIC_CHANGES_20260515.edi", generate_changes())

    print("File 3: Multi-Transaction — 2 ST/SE blocks, different MCEs")
    write_file("OH_834_REALISTIC_MULTI_TX_20260601.edi", generate_multi_tx())

    print("\nDone. Files written to:", OUTPUT_DIR)
