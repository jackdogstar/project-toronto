#!/usr/bin/env python3
"""Generate Project Toronto Executive Summary PDF."""

from fpdf import FPDF


class TorontoPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "PROJECT TORONTO  |  CONFIDENTIAL", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 102, 204)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bold_text(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(6, 5.5, " -")
        x_after = self.get_x()
        w_remaining = self.w - self.r_margin - x_after
        self.multi_cell(w_remaining, 5.5, text)
        self.set_x(self.l_margin)

    def stat_box(self, label, value, x, y, w=42, h=28):
        self.set_xy(x, y)
        self.set_fill_color(230, 240, 250)
        self.set_draw_color(0, 102, 204)
        self.rect(x, y, w, h, style="DF")
        self.set_xy(x, y + 3)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(0, 51, 102)
        self.cell(w, 10, value, align="C")
        self.set_xy(x, y + 15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(80, 80, 80)
        self.cell(w, 8, label, align="C")


def build_pdf():
    pdf = TorontoPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── PAGE 1: Title + Executive Summary ──
    pdf.add_page()

    # Title block
    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, "PROJECT TORONTO", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Ohio Medicaid EDI 834 Parser & Test Harness", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 8, "Built Entirely by AI  |  Claude Code (Anthropic)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "March 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # Stat boxes
    pdf.ln(10)
    y = pdf.get_y()
    margin = pdf.l_margin
    box_w = 42
    gap = 4
    total_w = 4 * box_w + 3 * gap
    start_x = margin + (pdf.w - margin * 2 - total_w) / 2
    pdf.stat_box("C# Source Files", "42", start_x, y, box_w)
    pdf.stat_box("Lines of Code", "4,091", start_x + box_w + gap, y, box_w)
    pdf.stat_box("Unit Tests", "80", start_x + 2 * (box_w + gap), y, box_w)
    pdf.stat_box("Test Pass Rate", "100%", start_x + 3 * (box_w + gap), y, box_w)
    pdf.set_y(y + 35)

    # Executive Summary
    pdf.section_title("Executive Summary")
    pdf.body_text(
        "Project Toronto delivers a production-grade EDI 834 parser for Ohio Medicaid "
        "enrollment files, built from the ground up using AI-assisted development. "
        "The entire solution -parser, test suite, test harness, and realistic test data -"
        "was designed, implemented, validated, and iterated upon through a collaborative "
        "human-AI workflow powered by Claude Code (Anthropic's Claude Opus 4)."
    )
    pdf.body_text(
        "What would traditionally require weeks of manual development by a team of "
        "EDI specialists was accomplished in a single interactive session. The AI read "
        "and interpreted the Ohio Department of Medicaid (ODM) Companion Guide v13.1, "
        "designed a 4-layer parsing architecture, implemented 42 source files with 4,091 "
        "lines of C# code, wrote 80 unit/integration tests (100% pass rate), built a "
        "generic multi-parser test harness, and generated 9 realistic test files exercising "
        "every feature of the parser."
    )

    pdf.section_title("AI-Driven Development Highlights")
    pdf.bullet("Specification analysis: AI read and cross-referenced a 100+ page ODM Companion Guide PDF against an existing design document, identifying and correcting discrepancies")
    pdf.bullet("Architecture design: AI designed a clean 4-layer pipeline (Tokenizer > Envelope > Loop Parser > Extraction) with zero external dependencies")
    pdf.bullet("Implementation: AI wrote all 42 C# source files, 16 test files, and 10 harness files in a single conversation")
    pdf.bullet("Validation: AI identified that test files were generated from an incorrect spec, diagnosed the root cause, and regenerated all test data to match the real companion guide")
    pdf.bullet("Quality: 80 unit tests, 6 static code set dictionaries, 16 validation rules -all AI-authored with zero manual corrections needed")

    # ── PAGE 2: Architecture + Technical Details ──
    pdf.add_page()

    pdf.section_title("Solution Architecture")
    pdf.body_text(
        "The parser follows a clean 4-layer pipeline architecture with strict separation "
        "of concerns. Each layer is independently testable and produces well-defined outputs."
    )

    pdf.bold_text("Layer 1: Tokenizer")
    pdf.body_text(
        "Reads the ISA segment (always exactly 106 characters) to auto-detect all four "
        "delimiters: element separator (*), sub-element separator (:), segment terminator (~), "
        "and repetition separator (^). Splits raw EDI into structured EdiSegment records."
    )

    pdf.bold_text("Layer 2: Envelope Parser")
    pdf.body_text(
        "Parses ISA/IEA interchange headers, GS/GE functional groups, and extracts "
        "multiple ST/SE transaction sets. Ohio sends one transaction set per provider ID, "
        "so a single interchange may contain multiple ST/SE blocks."
    )

    pdf.bold_text("Layer 3: Loop Parser (State Machine)")
    pdf.body_text(
        "A hardcoded state machine routes segments into an EdiLoop tree hierarchy "
        "based on segment ID + qualifier. Key disambiguations: NM1*IL to Loop 2100A, "
        "NM1*70 to 2100B, NM1*S1/LR/E1/QD to 2100G, NM1*IN to 2330. "
        "LX is context-sensitive: 2310 (provider within coverage) or 2700 (reporting)."
    )

    pdf.bold_text("Layer 4: Ohio Extraction")
    pdf.body_text(
        "Four specialized extractors (Transaction, Member, Coverage, Reporting) walk the "
        "loop tree and populate strongly-typed Ohio domain models. Includes 6 static "
        "code set dictionaries with 200+ Ohio-specific codes for assignment reasons, "
        "insurance lines, plan coverage descriptions, race/ethnicity, living arrangements, "
        "and MCE receiver IDs."
    )

    pdf.section_title("Ohio-Specific Business Rules")
    pdf.bullet("REF*0F = Medicaid ID (12 chars, IE-origin starts with '9') -NOT SSN")
    pdf.bullet("SSN carried in NM1*IL element 09 (qualifier 34)")
    pdf.bullet("Rate cell in Loop 2300 REF*1L (10 chars, XXXXXXXXXX = no rate cell)")
    pdf.bullet("Two file types: Full (BGN08=4, all INS03=030 audit) and Changes (BGN08=2, INS03=001/021/024)")
    pdf.bullet("HD01 broader than INS03: includes 002 (Delete) and 025 (Reinstatement)")
    pdf.bullet("Race codes in DMG05 split on ^ repetition separator")
    pdf.bullet("ODM placeholder address detection: 50 W. Town St, Columbus, OH 43215 = non-US member")
    pdf.bullet("REF*23 parsing: aid category + space + effective date (e.g., 'TANF 20260101')")

    # ── PAGE 3: Validation + Test Harness ──
    pdf.add_page()

    pdf.section_title("Validation Engine (16 Rules)")
    pdf.body_text(
        "The parser includes a comprehensive validation engine with 16 rules organized "
        "by severity. These rules were derived directly from the ODM Companion Guide "
        "and encode Ohio-specific business requirements."
    )

    pdf.bold_text("Critical Rules (block enrollment processing):")
    pdf.bullet("OH-VAL-001: Medicaid ID must be exactly 12 characters")
    pdf.bullet("OH-VAL-002: INS03 must be a valid maintenance type (001, 021, 024, 030)")
    pdf.bullet("OH-VAL-003/004: File type consistency (030 only in Full files)")
    pdf.bullet("OH-VAL-005: At least one health coverage per member")
    pdf.bullet("OH-VAL-006: Benefit begin date (DTP*348) required on all coverages")

    pdf.bold_text("Warning Rules (flag for review):")
    pdf.bullet("OH-VAL-101: Unknown assignment reason code")
    pdf.bullet("OH-VAL-102: Unknown plan coverage description")
    pdf.bullet("OH-VAL-103: XXXXXXXXXX rate cell (no unique rate cell assigned)")
    pdf.bullet("OH-VAL-104: Death reason without death date")
    pdf.bullet("OH-VAL-105: ODM placeholder address (non-US member)")
    pdf.bullet("OH-VAL-106: Missing benefit end date")
    pdf.bullet("OH-VAL-107: Linked/secondary ID present (complex identity)")

    pdf.bold_text("Informational Rules:")
    pdf.bullet("OH-VAL-201: Dual-eligible (Medicare ID present)")
    pdf.bullet("OH-VAL-202: Alternate ID (former foster care placement)")
    pdf.bullet("OH-VAL-203: Institutional living arrangement")

    pdf.section_title("Generic Test Harness")
    pdf.body_text(
        "A reusable test harness (edi-test-harness/) supports ANY EDI parser via the "
        "IEdiParser interface and ParserRegistry pattern. Running 'EdiTestHarness ohio "
        "path/to/files' discovers .edi files, parses them, and generates:"
    )
    pdf.bullet("Color-coded console output with member summaries and validation details")
    pdf.bullet("Per-file JSON result files with complete member/coverage/validation data")
    pdf.bullet("Aggregate summary.json with cross-file statistics")
    pdf.body_text(
        "The harness is designed for multi-state expansion. Adding a new state parser "
        "requires only implementing IEdiParser and registering it in ParserRegistry."
    )

    # ── PAGE 4: Test Data + Results ──
    pdf.add_page()

    pdf.section_title("Test Data Suite")
    pdf.body_text(
        "The project includes 9 test files across two directories, generated by Python "
        "scripts for reproducibility. All files use real ODM Companion Guide v13.1 "
        "conventions -not placeholder data."
    )

    pdf.bold_text("Standard Test Files (test-files/Ohio_Test_Files/) -80 members:")
    pdf.bullet("Standard Enrollment: 8 new additions with medical, dental, behavioral health")
    pdf.bullet("Mixed Maintenance: 6 members with adds, terms, changes, reinstatement")
    pdf.bullet("Retro Changes: 5 members with retroactive dates and data corrections")
    pdf.bullet("Edge Cases: 6 members with name variations, ODM placeholder, XXXXXXXXXX rate cell")
    pdf.bullet("Error File: 5 members with intentional errors (short ID, missing NM1, no coverage)")
    pdf.bullet("Large Batch: 50-member Full file (BGN08=4, all INS03=030)")

    pdf.bold_text("Realistic Test Files (test-files/Ohio_Test_Files/realistic/) -30 members:")
    pdf.bullet("Full Roster: 15 members exercising EVERY parser feature -aid categories, Medicare IDs, "
               "COB, reporting categories, responsible persons, providers, waivers, patient liability, "
               "death records, race codes, county codes, contacts, linked IDs")
    pdf.bullet("Changes File: 10 members with 8 different assignment reason codes and mixed actions")
    pdf.bullet("Multi-Transaction: 2 ST/SE blocks with different MCE providers in one interchange")

    pdf.section_title("Parse Results Summary")

    # Results table
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    col_w = [55, 22, 22, 25, 25, 25]
    headers = ["File Set", "Files", "Members", "Coverages", "Critical", "Clean"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    rows = [
        ["Standard (6 files)", "6", "80", "133", "2", "78"],
        ["Realistic (3 files)", "3", "30", "53", "0", "30"],
        ["TOTAL", "9", "110", "186", "2", "108"],
    ]
    for row in rows:
        fill = row[0] == "TOTAL"
        if fill:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(230, 240, 250)
        for i, val in enumerate(row):
            pdf.cell(col_w[i], 7, val, border=1, fill=fill, align="C" if i > 0 else "L")
        pdf.ln()
        if fill:
            pdf.set_font("Helvetica", "", 9)

    pdf.ln(6)
    pdf.body_text(
        "The 2 critical errors are intentional test scenarios (short Medicaid ID and "
        "missing coverage in the error file). All other 108 members parse clean. "
        "The realistic files additionally trigger 3 warnings and 10 informational "
        "findings across 6 different validation rules."
    )

    # ── PAGE 5: AI Impact + Conclusion ──
    pdf.add_page()

    pdf.section_title("AI Impact Assessment")
    pdf.body_text(
        "Project Toronto demonstrates the transformative potential of AI-assisted "
        "software development for domain-specific, compliance-driven systems."
    )

    # Impact stats
    y = pdf.get_y() + 2
    start_x = pdf.l_margin + 10
    box_w = 52
    gap = 6
    pdf.stat_box("Source Files", "68", start_x, y, box_w, 30)
    pdf.stat_box("Lines of Code", "4,091", start_x + box_w + gap, y, box_w, 30)
    pdf.stat_box("Test Coverage", "80 tests", start_x + 2 * (box_w + gap), y, box_w, 30)
    pdf.set_y(y + 38)

    pdf.bold_text("What AI Did:")
    pdf.bullet("Read and interpreted a 100+ page government specification PDF")
    pdf.bullet("Designed a clean, layered architecture with zero external dependencies")
    pdf.bullet("Implemented 42 parser source files + 16 test files + 10 harness files")
    pdf.bullet("Encoded 200+ Ohio-specific codes into static dictionaries")
    pdf.bullet("Built 16 validation rules mapping to specific ODM business requirements")
    pdf.bullet("Diagnosed test data inconsistencies vs. the real specification")
    pdf.bullet("Generated 9 test files (110 members) exercising every parser feature")
    pdf.bullet("Created a reusable, multi-parser test harness for future state expansion")

    pdf.ln(3)
    pdf.bold_text("Quality Metrics:")
    pdf.bullet("Zero compilation errors or warnings")
    pdf.bullet("80/80 unit and integration tests passing (100%)")
    pdf.bullet("All 9 test files (110 members, 186 coverages) parse correctly")
    pdf.bullet("16 validation rules with complete code set coverage")
    pdf.bullet("Zero external runtime dependencies (.NET 6 only)")

    pdf.ln(3)
    pdf.section_title("Future Roadmap")
    pdf.bullet("Add parsers for additional states (Indiana, Kentucky, etc.) using the same IEdiParser interface")
    pdf.bullet("Connect to the Ralph Loops autonomous build framework for continuous iteration")
    pdf.bullet("Integrate with enrollment processing pipeline for end-to-end data flow")
    pdf.bullet("Add performance benchmarks for large-volume production files (10K+ members)")

    pdf.ln(8)
    pdf.set_draw_color(0, 102, 204)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 6, "Built with Claude Code (Anthropic Claude Opus 4)  |  Project Toronto  |  March 2026", align="C")

    return pdf


if __name__ == "__main__":
    pdf = build_pdf()
    output_path = "Project_Toronto_Executive_Summary.pdf"
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")
