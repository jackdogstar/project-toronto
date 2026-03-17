#!/usr/bin/env python3
"""
Generate realistic Louisiana 834 test files that exercise ALL features.

Louisiana-specific conventions (contrast with Ohio):
- REF*0F = Medicaid ID (LA + 9 digits) — NOT SSN
- SSN only in NM1*IL element 09 (qualifier 34)
- REF*1L = Health Region (REGION-1 through REGION-9) — Ohio uses for Medicaid ID
- REF*ZZ = Eligibility Group (LDE-xxx) — Ohio uses for rate category
- REF*CE = State confirmation number (LACONF...) — Ohio does not use
- Single Loop 2300 per member with HLT = full benefit package
- DTP*349 ABSENT for open-ended enrollment (Ohio uses 99991231 sentinel)
- REF*N6 in Loop 2300 for network assignment (Ohio uses REF*17)
- Parish codes in N4 (Louisiana uses parishes, not counties)
- Plan codes: BAYOU-STD, BAYOU-ABD, BAYOU-SSI, BAYOU-DUAL

Additional features exercised in realistic files:
- Race codes (DMG05) with ^ repetition separator
- PER contacts (phone, email)
- Responsible persons (NM1*S1/LR/QD) for children and elderly
- COB (Loop 2320/2330) for dual-eligible members with Medicare
- REF*F6 Medicare IDs
- REF*23 aid category
- DTP*300 redetermination dates
- DTP*473/474 Medicaid begin/end dates
- INS12 death date
- Multiple assignment reason codes
- Reporting categories (Loop 2700/2710) — living arrangements
- Multi-transaction (different MCEs per ST/SE block)
- Full file (BGN08=4) with audit records
- Parish-based geography
"""

import os
import hashlib

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Louisiana MCE receiver IDs (real Bayou Health plans)
MCES = {
    "LHCCONNECT": ("LOUISIANA HEALTHCARE CONNECTIONS", "720001234"),
    "HEALTHBLUE": ("HEALTHY BLUE", "720002345"),
    "AETNABH":    ("AETNA BETTER HEALTH OF LOUISIANA", "720003456"),
    "AMERIHLTH":  ("AMERIHEALTH CARITAS LOUISIANA", "720004567"),
    "UNITEDHC":   ("UNITEDEALTHCARE COMMUNITY PLAN OF LA", "720005678"),
}

# Louisiana parishes (FIPS codes)
PARISHES = {
    "071": "Orleans",
    "033": "East Baton Rouge",
    "109": "Terrebonne",
    "055": "Lafayette",
    "019": "Calcasieu",
    "079": "Rapides",
    "017": "Caddo",
    "073": "Ouachita",
    "105": "Tangipahoa",
    "051": "Jefferson",
}

_conf_counter = 0


def next_conf(date_str):
    global _conf_counter
    _conf_counter += 1
    return f"LACONF{date_str}{_conf_counter:04d}"


def isa(date_yymmdd, control_num, receiver="LHCCONNECT     "):
    return (
        f"ISA*00*          *00*          "
        f"*ZZ*LADHH          *ZZ*{receiver}"
        f"*{date_yymmdd}*0800*^*00501*{control_num:09d}*0*P*:~"
    )


def gs(date, receiver="LHCCONNECT"):
    return f"GS*BE*LADHH*{receiver}*{date}*0800*1*X*005010X220A1~"


def la_header(ref_id, date, bgn08, contract="LA-MCO-LHC-2025-001", mce_key="LHCCONNECT"):
    mce_name, mce_fi = MCES[mce_key]
    return [
        f"BGN*00*{ref_id}*{date}*0800****{bgn08}~",
        f"REF*38*{contract}~",
        f"DTP*007*D8*{date}~",
        f"N1*P5*LOUISIANA DEPARTMENT OF HEALTH*FI*726014583~",
        f"N1*IN*{mce_name}*FI*{mce_fi}~",
    ]


def member(ins03, ins04, medicaid_id, elig_group, region, elig_date,
           last, first, middle, ssn, dob, gender,
           street1, street2, city, state, zipcode,
           plan_code=None, coverage_end=None, network_region=None,
           conf_date="20260501",
           employment_status="FT",
           death_date=None,
           aid_category_ref=None,
           medicare_id=None,
           parish_code=None,
           redetermination_date=None,
           medicaid_begin=None,
           medicaid_end=None,
           race_codes=None,
           contacts=None,
           responsible_person=None,
           cob_records=None,
           reporting_categories=None):
    """Build a complete Louisiana member with all optional segments."""
    segs = []

    if plan_code is None:
        plan_map = {
            "LDE-TANF": "BAYOU-STD", "LDE-EXP": "BAYOU-STD", "LDE-CHIP": "BAYOU-STD",
            "LDE-SSI": "BAYOU-SSI", "LDE-ABD": "BAYOU-ABD", "LDE-DUAL": "BAYOU-DUAL",
        }
        prefix = "-".join(elig_group.split("-")[:2])
        plan_code = plan_map.get(prefix, "BAYOU-STD")

    if network_region is None:
        network_region = region.replace("REGION-", "NET-")

    conf_num = next_conf(conf_date)

    # ── Loop 2000: INS ──
    ins = f"INS*Y*18*{ins03}*{ins04}*A***{employment_status}"
    if death_date:
        ins += f"****{death_date}"
    segs.append(ins + "~")

    # ── Loop 2000: REF segments (Louisiana-specific!) ──
    segs.append(f"REF*0F*{medicaid_id}~")       # Medicaid ID (NOT SSN!)
    segs.append(f"REF*1L*{region}~")              # Health Region (NOT Medicaid ID!)
    segs.append(f"REF*ZZ*{elig_group}~")          # Eligibility Group (NOT rate cat!)
    segs.append(f"REF*CE*{conf_num}~")            # State confirmation (LA only)

    if aid_category_ref:
        segs.append(f"REF*23*{aid_category_ref}~")
    if medicare_id:
        segs.append(f"REF*F6*{medicare_id}~")

    # ── Loop 2000: DTP dates ──
    segs.append(f"DTP*336*D8*{elig_date}~")
    if redetermination_date:
        segs.append(f"DTP*300*D8*{redetermination_date}~")
    if medicaid_begin:
        segs.append(f"DTP*473*D8*{medicaid_begin}~")
    if medicaid_end:
        segs.append(f"DTP*474*D8*{medicaid_end}~")

    # ── Loop 2100A: NM1 (SSN only here, NOT in REF*0F) ──
    if middle:
        segs.append(f"NM1*IL*1*{last}*{first}*{middle}***34*{ssn}~")
    else:
        segs.append(f"NM1*IL*1*{last}*{first}****34*{ssn}~")

    dmg = f"DMG*D8*{dob}*{gender}"
    if race_codes:
        dmg += f"**{'^'.join(race_codes)}"
    segs.append(dmg + "~")

    if street2:
        segs.append(f"N3*{street1}*{street2}~")
    else:
        segs.append(f"N3*{street1}~")

    n4 = f"N4*{city}*{state}*{zipcode}"
    if parish_code:
        n4 += f"**CY*{parish_code}"
    segs.append(n4 + "~")

    if contacts:
        for c in contacts:
            per = f"PER*IP*{c.get('name', '')}"
            for qual, num in c.get("pairs", []):
                per += f"*{qual}*{num}"
            segs.append(per + "~")

    # ── Loop 2100G: Responsible Person ──
    if responsible_person:
        rp = responsible_person
        tc = rp["type_code"]
        if rp.get("is_org"):
            segs.append(f"NM1*{tc}*2*{rp['org_name']}~")
        else:
            rp_mid = f"*{rp['middle']}" if rp.get('middle') else ""
            segs.append(f"NM1*{tc}*1*{rp['last']}*{rp['first']}{rp_mid}~")
        if rp.get("street"):
            segs.append(f"N3*{rp['street']}~")
            segs.append(f"N4*{rp['city']}*{rp['state']}*{rp['zip']}~")

    # ── Loop 2300: SINGLE coverage (Louisiana convention!) ──
    segs.append(f"HD*{ins03}**HLT*{plan_code}*EMP~")
    segs.append(f"DTP*348*D8*{elig_date}~")
    # Louisiana: DTP*349 ABSENT for open-ended (no 99991231 sentinel!)
    if coverage_end:
        segs.append(f"DTP*349*D8*{coverage_end}~")
    # Louisiana: REF*N6 for network (NOT REF*17!)
    segs.append(f"REF*N6*{network_region}~")

    # ── Loop 2320: COB (after coverage) ──
    if cob_records:
        for cob in cob_records:
            segs.append(f"COB*{cob['payer_resp']}**{cob['cob_code']}~")
            if cob.get("group_number"):
                segs.append(f"REF*6P*{cob['group_number']}~")
            if cob.get("other_ssn"):
                segs.append(f"REF*SY*{cob['other_ssn']}~")
            if cob.get("insurer_name"):
                segs.append(f"NM1*IN*2*{cob['insurer_name']}~")

    # ── Loop 2700/2710: Reporting Categories ──
    if reporting_categories:
        for i, rc in enumerate(reporting_categories, 1):
            segs.append(f"LX*{i}~")
            segs.append(f"N1*75*{rc['category']}~")
            segs.append(f"REF*{rc['ref_qual']}*{rc['ref_value']}~")
            if rc.get("date"):
                segs.append(f"DTP*007*D8*{rc['date']}~")
            elif rc.get("date_range"):
                segs.append(f"DTP*007*RD8*{rc['date_range']}~")

    return segs


def build_file(isa_seg, gs_seg, tx_blocks, isa_control):
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


# ═══════════════════════════════════════════════════════════════════════
# FILE 1: Realistic Full Roster — exercises ALL Louisiana features
# BGN08=4 (Full file), 15 members, all INS03=030
# ═══════════════════════════════════════════════════════════════════════

def generate_full_roster():
    global _conf_counter
    _conf_counter = 0
    hdr = la_header("LAFULL20260501", "20260501", "4")
    members = []

    # M1: TANF adult, New Orleans, parish code, race, contacts, redetermination
    members.append(member(
        "030", "XN", "LA600100001", "LDE-TANF-001", "REGION-1", "20260501",
        "BOUDREAUX", "MARIE", "C", "445112233", "19870623", "F",
        "1200 BOURBON STREET", "APT 3", "NEW ORLEANS", "LA", "70112",
        conf_date="20260501",
        aid_category_ref="TANF 20250801",
        parish_code="071",
        race_codes=["B"],
        medicaid_begin="20250801",
        redetermination_date="20260801",
        contacts=[{"name": "MARIE BOUDREAUX", "pairs": [("TE", "5045551234")]}],
        cob_records=[{"payer_resp": "S", "cob_code": "5"}],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "01", "date": "20250801"},
        ],
    ))

    # M2: Full dual-eligible elderly, Monroe — Medicare COB, institutional
    members.append(member(
        "030", "XN", "LA600100002", "LDE-DUAL-001", "REGION-8", "20260501",
        "HEBERT", "CLAIRE", "D", "212889900", "19420712", "F",
        "775 DESIARD STREET", None, "MONROE", "LA", "71201",
        conf_date="20260501",
        medicare_id="1LA4TE5MK72",
        aid_category_ref="DUAL 20230601",
        parish_code="073",
        race_codes=["C"],
        medicaid_begin="20230601",
        redetermination_date="20260601",
        cob_records=[{
            "payer_resp": "P", "cob_code": "1",
            "group_number": "GRP-MEDICARE-AB",
            "other_ssn": "212889900",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "10", "date": "20240101"},
        ],
    ))

    # M3: TANF child with responsible person (parent), multi-race
    members.append(member(
        "030", "XN", "LA600100003", "LDE-TANF-002", "REGION-2", "20260501",
        "LANDRY", "CAMILLE", "A", "667334455", "20190515", "F",
        "890 GOVERNMENT STREET", None, "BATON ROUGE", "LA", "70801",
        conf_date="20260501",
        aid_category_ref="TANF 20190601",
        parish_code="033",
        race_codes=["B", "C"],
        medicaid_begin="20190601",
        responsible_person={
            "type_code": "S1", "last": "LANDRY", "first": "ANTOINE", "middle": "J",
            "street": "890 GOVERNMENT STREET", "city": "BATON ROUGE", "state": "LA", "zip": "70801",
        },
    ))

    # M4: Newborn infant with mother ID
    members.append(member(
        "030", "28", "LA600100004", "LDE-TANF-003", "REGION-4", "20260501",
        "GUIDRY", "BEBE", None, "778445500", "20260418", "F",
        "3456 MAGAZINE STREET", None, "LAFAYETTE", "LA", "70501",
        conf_date="20260501",
        aid_category_ref="TANF 20260418",
        parish_code="055",
        medicaid_begin="20260418",
        responsible_person={
            "type_code": "S1", "last": "GUIDRY", "first": "RENEE",
            "street": "3456 MAGAZINE STREET", "city": "LAFAYETTE", "state": "LA", "zip": "70501",
        },
    ))

    # M5: LaCHIP child, Covington, Region 9
    members.append(member(
        "030", "XN", "LA600100005", "LDE-CHIP-001", "REGION-9", "20260501",
        "BROUSSARD", "ETIENNE", "P", "889556677", "20140907", "M",
        "555 BAYOU LANE", None, "COVINGTON", "LA", "70433",
        conf_date="20260501",
        aid_category_ref="CHIP 20200901",
        parish_code="105",
        race_codes=["C", "H"],
        medicaid_begin="20200901",
        responsible_person={
            "type_code": "S1", "last": "BROUSSARD", "first": "JACQUES",
            "street": "555 BAYOU LANE", "city": "COVINGTON", "state": "LA", "zip": "70433",
        },
    ))

    # M6: Deceased member — death date in INS12
    members.append(member(
        "030", "3", "LA600100006", "LDE-ABD-002", "REGION-5", "20260501",
        "FONTENOT", "THERESA", "L", "990667788", "19680301", "F",
        "100 MAIN STREET", "SUITE 100", "LAKE CHARLES", "LA", "70601",
        death_date="20260420",
        coverage_end="20260420",
        conf_date="20260501",
        aid_category_ref="ABD 20240101",
        parish_code="019",
        race_codes=["C"],
        medicaid_begin="20240101",
        medicaid_end="20260420",
    ))

    # M7: Expansion adult (MAGI), Shreveport, contacts + race
    members.append(member(
        "030", "XN", "LA600100007", "LDE-EXP-002", "REGION-7", "20260501",
        "RICHARD", "JEAN", "B", "101778899", "19800110", "M",
        "950 PIERREMONT ROAD", None, "SHREVEPORT", "LA", "71101",
        conf_date="20260501",
        aid_category_ref="EXP 20250301",
        parish_code="017",
        race_codes=["B", "I"],
        medicaid_begin="20250301",
        redetermination_date="20260301",
        contacts=[
            {"name": "JEAN RICHARD", "pairs": [("TE", "3185559876")]},
        ],
    ))

    # M8: SSI adult with redetermination, Alexandria
    members.append(member(
        "030", "XN", "LA600100008", "LDE-SSI-001", "REGION-6", "20260501",
        "TRAHAN", "ANNETTE", "P", "410001001", "19650818", "F",
        "600 TEXAS STREET", None, "ALEXANDRIA", "LA", "71301",
        conf_date="20260501",
        aid_category_ref="SSI 20220301",
        parish_code="079",
        race_codes=["C"],
        medicaid_begin="20220301",
        redetermination_date="20260901",
    ))

    # M9: ABD Aged, 90+, Houma
    members.append(member(
        "030", "XN", "LA600100009", "LDE-ABD-001", "REGION-3", "20260501",
        "COMEAUX", "RUTH", "E", "550505050", "19350611", "F",
        "100 MAIN STREET", "UNIT 6", "HOUMA", "LA", "70360",
        conf_date="20260501",
        medicare_id="2FK8RR4JL91",
        aid_category_ref="ABD 20200101",
        parish_code="109",
        medicaid_begin="20200101",
        cob_records=[{
            "payer_resp": "P", "cob_code": "1",
            "group_number": "GRP-MCARE-AB",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "09", "date": "20230101"},
        ],
    ))

    # M10: Partial dual, Region 7
    members.append(member(
        "030", "XN", "LA600100010", "LDE-DUAL-002", "REGION-7", "20260501",
        "FONTENOT", "EMILE", "G", "560606060", "19500924", "M",
        "600 TEXAS STREET", None, "SHREVEPORT", "LA", "71101",
        conf_date="20260501",
        medicare_id="3HJ9KK2LP44",
        aid_category_ref="DUAL 20240601",
        parish_code="017",
        medicaid_begin="20240601",
        cob_records=[{
            "payer_resp": "P", "cob_code": "1",
            "group_number": "GRP-MCARE-B",
            "other_ssn": "560606060",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
    ))

    # M11: SSI child with org responsible person (DCFS)
    members.append(member(
        "030", "XN", "LA600100011", "LDE-SSI-002", "REGION-2", "20260501",
        "MELANCON", "SIMONE", "R", "321002002", "20120803", "F",
        "2222 PERKINS ROAD", None, "BATON ROUGE", "LA", "70816",
        conf_date="20260501",
        aid_category_ref="SSI 20210601",
        parish_code="033",
        race_codes=["B"],
        medicaid_begin="20210601",
        responsible_person={
            "type_code": "QD", "is_org": True,
            "org_name": "LOUISIANA DCFS REGION 2",
            "street": "627 N 4TH STREET", "city": "BATON ROUGE", "state": "LA", "zip": "70802",
        },
    ))

    # M12: Expansion adult XIX, Gonzales
    members.append(member(
        "030", "XN", "LA600100012", "LDE-EXP-001", "REGION-2", "20260501",
        "ROMERO", "JAMES", "K", "410003003", "19880320", "M",
        "4444 HIGHLAND ROAD", None, "GONZALES", "LA", "70737",
        conf_date="20260501",
        aid_category_ref="EXP 20250701",
        parish_code="033",
        race_codes=["H"],
        medicaid_begin="20250701",
        redetermination_date="20260701",
    ))

    # M13: LaCHIP Affordable Plan child
    members.append(member(
        "030", "XN", "LA600100013", "LDE-CHIP-002", "REGION-5", "20260501",
        "CASTILLE", "GABRIELLE", "T", "530303030", "20120218", "F",
        "1717 RIVER ROAD", None, "SULPHUR", "LA", "70663",
        conf_date="20260501",
        aid_category_ref="CHIP 20220301",
        parish_code="019",
        medicaid_begin="20220301",
        responsible_person={
            "type_code": "S1", "last": "CASTILLE", "first": "DANIELLE",
            "street": "1717 RIVER ROAD", "city": "SULPHUR", "state": "LA", "zip": "70663",
        },
    ))

    # M14: TANF parent with legal representative, multiple contacts
    members.append(member(
        "030", "XN", "LA600100014", "LDE-TANF-001", "REGION-1", "20260501",
        "DE LA CROIX", "PIERRE", "A", "520202020", "19760830", "M",
        "450 ESPLANADE AVENUE", None, "NEW ORLEANS", "LA", "70112",
        conf_date="20260501",
        aid_category_ref="TANF 20250101",
        parish_code="071",
        race_codes=["C", "E"],
        medicaid_begin="20250101",
        redetermination_date="20260101",
        contacts=[
            {"name": "PIERRE DE LA CROIX", "pairs": [("TE", "5045557890")]},
            {"name": "MARIE DE LA CROIX", "pairs": [("TE", "5045557891"), ("EM", "MDELACROIX@EMAIL.COM")]},
        ],
    ))

    # M15: Complex — dual with 2 COB, reporting, legal rep
    members.append(member(
        "030", "XN", "LA600100015", "LDE-DUAL-001", "REGION-1", "20260501",
        "ARCENEAUX", "GASTON", "W", "410002002", "19440615", "M",
        "2100 CANAL STREET", None, "NEW ORLEANS", "LA", "70119",
        conf_date="20260501",
        medicare_id="4PQ2RR8NT66",
        aid_category_ref="DUAL 20210101",
        parish_code="071",
        race_codes=["B"],
        medicaid_begin="20210101",
        redetermination_date="20260101",
        responsible_person={
            "type_code": "LR", "last": "ARCENEAUX", "first": "MARIE", "middle": "T",
            "street": "2100 CANAL STREET", "city": "NEW ORLEANS", "state": "LA", "zip": "70119",
        },
        cob_records=[
            {
                "payer_resp": "P", "cob_code": "1",
                "group_number": "GRP-MCARE-AB",
                "other_ssn": "410002002",
                "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
            },
            {
                "payer_resp": "T", "cob_code": "4",
                "group_number": "GRP-AARP-SUPP",
                "insurer_name": "AARP SUPPLEMENTAL INSURANCE",
            },
        ],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "01", "date": "20210101"},
        ],
    ))

    return build_file(isa("260501", 201), gs("20260501"), [(hdr, members)], 201)


# ═══════════════════════════════════════════════════════════════════════
# FILE 2: Realistic Changes — mixed maintenance, 10 members
# BGN08=2 (Changes file)
# ═══════════════════════════════════════════════════════════════════════

def generate_changes():
    global _conf_counter
    _conf_counter = 100
    hdr = la_header("LACHG20260515", "20260515", "2")
    members = []

    # M1: New enrollment — expansion adult, assigned by enrollment broker
    members.append(member(
        "021", "14", "LA600200001", "LDE-EXP-001", "REGION-1", "20260515",
        "DUPRE", "DANIELLE", "N", "321003003", "19910117", "F",
        "1515 VETERANS MEMORIAL BLVD", "APT 14B", "METAIRIE", "LA", "70001",
        conf_date="20260515",
        aid_category_ref="EXP 20260515",
        parish_code="051",
        race_codes=["C"],
        medicaid_begin="20260515",
        redetermination_date="20270515",
    ))

    # M2: New enrollment — TANF child with responsible person
    members.append(member(
        "021", "16", "LA600200002", "LDE-TANF-002", "REGION-4", "20260515",
        "MOUTON", "JACQUES", None, "321004004", "20180430", "M",
        "789 ST CHARLES AVENUE", None, "NEW IBERIA", "LA", "70560",
        conf_date="20260515",
        aid_category_ref="TANF 20260515",
        parish_code="055",
        race_codes=["C", "H"],
        medicaid_begin="20260515",
        responsible_person={
            "type_code": "S1", "last": "MOUTON", "first": "PHILIPPE",
            "street": "789 ST CHARLES AVENUE", "city": "NEW IBERIA", "state": "LA", "zip": "70560",
        },
    ))

    # M3: Termination — lost eligibility
    members.append(member(
        "024", "7", "LA600200003", "LDE-TANF-001", "REGION-2", "20260515",
        "DOUCET", "LUCIEN", "H", "321006006", "19850929", "M",
        "2828 GREENWELL SPRINGS ROAD", None, "BATON ROUGE", "LA", "70816",
        coverage_end="20260531",
        conf_date="20260515",
        aid_category_ref="TANF 20240901",
        parish_code="033",
        medicaid_begin="20240901",
        medicaid_end="20260531",
    ))

    # M4: Termination — death
    members.append(member(
        "024", "3", "LA600200004", "LDE-ABD-001", "REGION-6", "20260515",
        "LEBLANC", "COLETTE", "S", "410004004", "19500827", "F",
        "3100 NORTH STREET", None, "PINEVILLE", "LA", "71360",
        death_date="20260508",
        coverage_end="20260508",
        conf_date="20260515",
        aid_category_ref="ABD 20220101",
        parish_code="079",
        medicaid_begin="20220101",
        medicaid_end="20260508",
    ))

    # M5: Change — address update, new parish
    members.append(member(
        "001", "EC", "LA600200005", "LDE-EXP-002", "REGION-7", "20260515",
        "COMEAUX", "MARCEL", "E", "321001001", "19890522", "M",
        "950 PIERREMONT ROAD", None, "SHREVEPORT", "LA", "71101",
        conf_date="20260515",
        aid_category_ref="EXP 20250301",
        parish_code="017",
        medicaid_begin="20250301",
    ))

    # M6: Reinstatement — INS03=021, different plan code
    members.append(member(
        "021", "17", "LA600200006", "LDE-SSI-001", "REGION-5", "20260515",
        "GUIDRY", "RENEE", "M", "778445566", "19650818", "F",
        "555 BAYOU LANE", None, "LAKE CHARLES", "LA", "70601",
        conf_date="20260515",
        aid_category_ref="SSI 20240101",
        parish_code="019",
        medicaid_begin="20240101",
    ))

    # M7: New dual-eligible with Medicare COB
    members.append(member(
        "021", "AJ", "LA600200007", "LDE-DUAL-001", "REGION-3", "20260515",
        "THIBODAUX", "CAMILLE", "A", "667334400", "19480312", "F",
        "100 MAIN STREET", None, "THIBODAUX", "LA", "70301",
        conf_date="20260515",
        medicare_id="5ST3UU9OV88",
        aid_category_ref="DUAL 20260515",
        parish_code="109",
        race_codes=["C"],
        medicaid_begin="20260515",
        cob_records=[{
            "payer_resp": "P", "cob_code": "1",
            "group_number": "GRP-MCARE-AB",
            "other_ssn": "667334400",
            "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
        }],
        reporting_categories=[
            {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "19", "date": "20260401"},
        ],
    ))

    # M8: Change — eligibility group update (TANF child to CHIP)
    members.append(member(
        "001", "25", "LA600200008", "LDE-CHIP-001", "REGION-9", "20260515",
        "BROUSSARD", "GABRIELLE", "T", "530303030", "20070615", "F",
        "1717 RIVER ROAD", None, "COVINGTON", "LA", "70433",
        conf_date="20260515",
        aid_category_ref="CHIP 20260501",
        parish_code="105",
        medicaid_begin="20250301",
    ))

    # M9: Disenrollment by LADHH staff
    members.append(member(
        "024", "6", "LA600200009", "LDE-EXP-001", "REGION-8", "20260515",
        "JOHNSON", "DOROTHY", "F", "410005005", "19710220", "F",
        "775 DESIARD STREET", "APT 201", "WEST MONROE", "LA", "71291",
        coverage_end="20260531",
        conf_date="20260515",
        aid_category_ref="EXP 20250101",
        parish_code="073",
        medicaid_begin="20250101",
        medicaid_end="20260531",
    ))

    # M10: Voluntary MCE change
    members.append(member(
        "001", "18", "LA600200010", "LDE-TANF-001", "REGION-1", "20260515",
        "BOUDREAUX-THIBODAUX", "CELESTE", "M", "510101010", "19930407", "F",
        "3456 MAGAZINE STREET", None, "NEW ORLEANS", "LA", "70112",
        conf_date="20260515",
        aid_category_ref="TANF 20250601",
        parish_code="071",
        race_codes=["C"],
        medicaid_begin="20250601",
    ))

    return build_file(isa("260515", 202), gs("20260515"), [(hdr, members)], 202)


# ═══════════════════════════════════════════════════════════════════════
# FILE 3: Multi-Transaction — 2 ST/SE blocks, different MCEs
# Tests envelope parsing with Louisiana MCE variations
# ═══════════════════════════════════════════════════════════════════════

def generate_multi_tx():
    global _conf_counter
    _conf_counter = 200

    # TX1: Louisiana Healthcare Connections
    hdr1 = la_header("LAMULTI1-20260601", "20260601", "2",
                     "LA-MCO-LHC-2025-001", "LHCCONNECT")
    tx1_members = [
        member(
            "021", "14", "LA600300001", "LDE-EXP-001", "REGION-1", "20260601",
            "LANDRY", "MONIQUE", "C", "601010101", "19880315", "F",
            "1200 BOURBON STREET", None, "NEW ORLEANS", "LA", "70112",
            conf_date="20260601",
            aid_category_ref="EXP 20260601",
            parish_code="071",
            race_codes=["B"],
            medicaid_begin="20260601",
        ),
        member(
            "021", "16", "LA600300002", "LDE-DUAL-001", "REGION-8", "20260601",
            "HEBERT", "CHARLES", "R", "602020202", "19450920", "M",
            "775 DESIARD STREET", None, "MONROE", "LA", "71201",
            conf_date="20260601",
            medicare_id="6WX4YY1QZ33",
            aid_category_ref="DUAL 20260601",
            parish_code="073",
            medicaid_begin="20260601",
            cob_records=[{
                "payer_resp": "P", "cob_code": "1",
                "group_number": "GRP-MCARE-A",
                "insurer_name": "CENTERS FOR MEDICARE AND MEDICAID SERVICES",
            }],
            reporting_categories=[
                {"category": "LIVING ARRANGEMENT", "ref_qual": "LU", "ref_value": "01", "date": "20260601"},
            ],
        ),
    ]

    # TX2: Healthy Blue (different MCE)
    hdr2 = la_header("LAMULTI2-20260601", "20260601", "2",
                     "LA-MCO-HB-2025-002", "HEALTHBLUE")
    tx2_members = [
        member(
            "021", "28", "LA600300003", "LDE-TANF-003", "REGION-4", "20260601",
            "GUIDRY", "BEAU", None, "603030303", "20260520", "M",
            "3456 MAGAZINE STREET", None, "LAFAYETTE", "LA", "70501",
            conf_date="20260601",
            aid_category_ref="TANF 20260520",
            parish_code="055",
            medicaid_begin="20260520",
            responsible_person={
                "type_code": "S1", "last": "GUIDRY", "first": "SUZANNE",
                "street": "3456 MAGAZINE STREET", "city": "LAFAYETTE", "state": "LA", "zip": "70501",
            },
        ),
        member(
            "024", "10", "LA600300004", "LDE-EXP-002", "REGION-7", "20260601",
            "RICHARD", "PHILIPPE", "A", "604040404", "19820111", "M",
            "1400 FAIRFIELD AVENUE", None, "BOSSIER CITY", "LA", "71111",
            coverage_end="20260615",
            conf_date="20260601",
            aid_category_ref="EXP 20240101",
            parish_code="017",
            medicaid_begin="20240101",
            medicaid_end="20260615",
        ),
        member(
            "001", "EC", "LA600300005", "LDE-CHIP-001", "REGION-9", "20260601",
            "BROUSSARD", "DANIELLE", "D", "605050505", "20100630", "F",
            "3100 NORTH STREET", None, "HAMMOND", "LA", "70401",
            conf_date="20260601",
            aid_category_ref="CHIP 20250301",
            parish_code="105",
            race_codes=["C", "G"],
            medicaid_begin="20250301",
            responsible_person={
                "type_code": "S1", "last": "BROUSSARD", "first": "ANTOINE",
                "street": "3100 NORTH STREET", "city": "HAMMOND", "state": "LA", "zip": "70401",
            },
        ),
    ]

    return build_file(
        isa("260601", 203), gs("20260601"),
        [(hdr1, tx1_members), (hdr2, tx2_members)], 203)


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
    print("Generating Realistic Louisiana 834 Test Files...\n")

    print("File 1: Full Roster - 15 members, all features")
    write_file("LA_834_REALISTIC_FULL_20260501.edi", generate_full_roster())

    print("File 2: Changes - 10 members, mixed maintenance")
    write_file("LA_834_REALISTIC_CHANGES_20260515.edi", generate_changes())

    print("File 3: Multi-Transaction - 2 ST/SE blocks, different MCEs")
    write_file("LA_834_REALISTIC_MULTI_TX_20260601.edi", generate_multi_tx())

    print("\nDone. Files written to:", OUTPUT_DIR)
