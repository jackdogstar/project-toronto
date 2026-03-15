using OhioEdiParser.CodeSets;
using OhioEdiParser.LoopParser.Models;
using OhioEdiParser.Models;

namespace OhioEdiParser.Extraction;

public static class OhioMemberExtractor
{
    private const string OdmPlaceholderLine1 = "50 W. TOWN ST";
    private const string OdmPlaceholderCity = "COLUMBUS";
    private const string OdmPlaceholderZip = "43215";

    public static OhioMember ExtractMember(EdiLoop loop2000, TransactionContext txContext, char repetitionSeparator)
    {
        var ins = loop2000.FindSegment("INS")
            ?? throw new InvalidOperationException("INS segment not found in Loop 2000.");

        var maintenanceTypeCode = ins.GetElement(2); // INS03
        var assignmentReasonCode = ins.GetElement(3); // INS04
        var employmentStatus = ins.GetElement(7);     // INS08
        var dateOfDeath = ins.GetElement(11);          // INS12

        // Medicaid ID — REF*0F (NOT SSN)
        var medicaidId = loop2000.GetElementValue("REF", 0, "0F", 1) ?? string.Empty;

        // Parse REF*23 (aid category + date)
        var aidCategoryRef = loop2000.GetElementValue("REF", 0, "23", 1);
        string? aidCategory = null;
        string? aidCategoryEffDate = null;
        if (aidCategoryRef != null)
        {
            var spaceIdx = aidCategoryRef.IndexOf(' ');
            if (spaceIdx > 0)
            {
                aidCategory = aidCategoryRef[..spaceIdx];
                aidCategoryEffDate = aidCategoryRef[(spaceIdx + 1)..];
            }
            else
            {
                aidCategory = aidCategoryRef;
            }
        }

        // Demographics (Loop 2100A)
        var demographics = ExtractDemographics(loop2000.FindChild("2100A"), repetitionSeparator);

        // Coverages (Loop 2300 — multiple)
        var coverages = loop2000.FindChildren("2300")
            .Select(OhioCoverageExtractor.ExtractCoverage)
            .ToList();

        // Responsible Person (Loop 2100G — optional)
        OhioResponsiblePerson? responsiblePerson = null;
        var loop2100G = loop2000.FindChild("2100G");
        if (loop2100G != null)
            responsiblePerson = ExtractResponsiblePerson(loop2100G);

        // COB (Loop 2320 — optional, multiple)
        var cobRecords = loop2000.FindChildren("2320")
            .Select(ExtractCob)
            .ToList();

        // Reporting Categories (Loop 2700/2710/2750)
        var reportingCategories = OhioReportingExtractor.ExtractReportingCategories(
            loop2000.FindChildren("2700"));

        return new OhioMember
        {
            MaintenanceTypeCode = maintenanceTypeCode,
            MaintenanceAction = OhioCoverageExtractor.ResolveMaintenanceAction(maintenanceTypeCode),
            AssignmentReasonCode = assignmentReasonCode,
            AssignmentReasonDescription = AssignmentReasonCodes.GetDescription(assignmentReasonCode),
            EmploymentStatus = employmentStatus,
            DateOfDeath = string.IsNullOrEmpty(dateOfDeath) ? null : dateOfDeath,
            MedicaidId = medicaidId,
            IsIeOrigin = medicaidId.Length > 0 && medicaidId[0] == '9',
            NewbornMotherId = loop2000.GetElementValue("REF", 0, "17", 1),
            AidCategory = aidCategory,
            AidCategoryEffectiveDate = aidCategoryEffDate,
            IeCaseNumber = loop2000.GetElementValue("REF", 0, "3H", 1),
            AlternateId = loop2000.GetElementValue("REF", 0, "6O", 1),
            MedicareId = loop2000.GetElementValue("REF", 0, "F6", 1),
            CountyOfEligibility = loop2000.GetElementValue("REF", 0, "DX", 1),
            LinkedSecondaryId = loop2000.GetElementValue("REF", 0, "Q4", 1),
            RedeterminationDate = loop2000.GetElementValue("DTP", 0, "300", 2),
            MedicaidBeginDate = loop2000.GetElementValue("DTP", 0, "473", 2),
            MedicaidEndDate = loop2000.GetElementValue("DTP", 0, "474", 2),
            Demographics = demographics,
            Coverages = coverages,
            ResponsiblePerson = responsiblePerson,
            CoordinationOfBenefits = cobRecords,
            ReportingCategories = reportingCategories
        };
    }

    private static OhioDemographics ExtractDemographics(EdiLoop? loop2100A, char repetitionSeparator)
    {
        if (loop2100A == null)
            return new OhioDemographics();

        var nm1 = loop2100A.FindSegment("NM1");
        var dmg = loop2100A.FindSegment("DMG");
        var n3 = loop2100A.FindSegment("N3");
        var n4 = loop2100A.FindSegment("N4");

        // SSN is in NM1*IL element 09 (index 8), with qualifier 34 in element 08 (index 7)
        string? ssn = null;
        if (nm1 != null && nm1.GetElement(7) == "34")
            ssn = nm1.GetElement(8);

        // Race codes — split on repetition separator
        var raceCodes = new List<string>();
        var raceDescriptions = new List<string?>();
        if (dmg != null)
        {
            var raceRaw = dmg.GetElement(4); // DMG05 (0-indexed: 4)
            if (!string.IsNullOrEmpty(raceRaw))
            {
                foreach (var code in raceRaw.Split(repetitionSeparator))
                {
                    if (!string.IsNullOrEmpty(code))
                    {
                        raceCodes.Add(code);
                        raceDescriptions.Add(RaceEthnicityCodes.GetDescription(code));
                    }
                }
            }
        }

        // Address
        OhioAddress? address = null;
        if (n3 != null && n4 != null)
        {
            var line1 = n3.GetElement(0);
            var city = n4.GetElement(0);
            var zip = n4.GetElement(2);

            var isPlaceholder = line1.ToUpperInvariant().Contains("50 W. TOWN ST")
                && city.ToUpperInvariant() == "COLUMBUS"
                && zip.StartsWith("43215");

            address = new OhioAddress
            {
                Line1 = line1,
                Line2 = string.IsNullOrEmpty(n3.GetElement(1)) ? null : n3.GetElement(1),
                City = city,
                State = n4.GetElement(1),
                Zip = zip,
                IsOdmPlaceholder = isPlaceholder
            };
        }

        // County code
        string? countyCode = null;
        if (n4 != null && n4.GetElement(4) == "CY")
            countyCode = n4.GetElement(5);

        // Contacts
        var contacts = ExtractContacts(loop2100A);

        return new OhioDemographics
        {
            LastName = nm1?.GetElement(2) ?? string.Empty,
            FirstName = nm1?.GetElement(3) ?? string.Empty,
            MiddleName = string.IsNullOrEmpty(nm1?.GetElement(4)) ? null : nm1!.GetElement(4),
            Ssn = ssn,
            DateOfBirth = dmg?.GetElement(1) ?? string.Empty,
            Gender = dmg?.GetElement(2) ?? string.Empty,
            RaceCodes = raceCodes,
            RaceDescriptions = raceDescriptions,
            Address = address,
            Contacts = contacts,
            CountyCode = countyCode
        };
    }

    private static List<OhioContact> ExtractContacts(EdiLoop loop)
    {
        var contacts = new List<OhioContact>();
        foreach (var per in loop.Segments.Where(s => s.SegmentId == "PER"))
        {
            // PER has up to 3 contact pairs: elements 02/03, 04/05, 06/07
            // (0-indexed: 1/2, 3/4, 5/6)
            for (int i = 1; i < 7; i += 2)
            {
                var type = per.GetElement(i);
                var value = per.GetElement(i + 1);
                if (!string.IsNullOrEmpty(type) && !string.IsNullOrEmpty(value))
                {
                    contacts.Add(new OhioContact { Type = type, Value = value });
                }
            }
        }
        return contacts;
    }

    private static OhioResponsiblePerson ExtractResponsiblePerson(EdiLoop loop2100G)
    {
        var nm1 = loop2100G.Segments.FirstOrDefault(s => s.SegmentId == "NM1");
        var n3 = loop2100G.Segments.FirstOrDefault(s => s.SegmentId == "N3");
        var n4 = loop2100G.Segments.FirstOrDefault(s => s.SegmentId == "N4");

        OhioAddress? address = null;
        if (n3 != null && n4 != null)
        {
            address = new OhioAddress
            {
                Line1 = n3.GetElement(0),
                Line2 = string.IsNullOrEmpty(n3.GetElement(1)) ? null : n3.GetElement(1),
                City = n4.GetElement(0),
                State = n4.GetElement(1),
                Zip = n4.GetElement(2)
            };
        }

        var isOrg = nm1?.GetElement(1) == "2";

        return new OhioResponsiblePerson
        {
            TypeCode = nm1?.GetElement(0) ?? string.Empty,
            LastName = isOrg ? null : nm1?.GetElement(2),
            FirstName = isOrg ? null : nm1?.GetElement(3),
            OrganizationName = isOrg ? nm1?.GetElement(2) : null,
            Address = address,
            Contacts = ExtractContacts(loop2100G)
        };
    }

    private static OhioCob ExtractCob(EdiLoop loop2320)
    {
        var cob = loop2320.FindSegment("COB");
        var loop2330 = loop2320.FindChild("2330");
        var insurerNm1 = loop2330?.Segments.FirstOrDefault(s => s.SegmentId == "NM1");

        return new OhioCob
        {
            PayerResponsibility = cob?.GetElement(0) ?? string.Empty,
            CobCode = cob?.GetElement(2) ?? string.Empty,
            OtherInsuranceGroupNumber = loop2320.GetElementValue("REF", 0, "6P", 1),
            OtherInsuranceSsn = loop2320.GetElementValue("REF", 0, "SY", 1),
            InsurerName = insurerNm1?.GetElement(2)
        };
    }
}
