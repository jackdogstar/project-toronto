using OhioEdiParser.CodeSets;
using OhioEdiParser.LoopParser.Models;
using OhioEdiParser.Models;

namespace OhioEdiParser.Extraction;

public static class OhioCoverageExtractor
{
    public static OhioCoverage ExtractCoverage(EdiLoop loop2300)
    {
        var hd = loop2300.FindSegment("HD")
            ?? throw new InvalidOperationException("HD segment not found in Loop 2300.");

        var maintenanceTypeCode = hd.GetElement(0);
        var insuranceLine = hd.GetElement(2);
        var planCoverageDesc = hd.GetElement(3);

        var rateCellRaw = loop2300.GetElementValue("REF", 0, "1L", 1);
        var rateCellMissing = rateCellRaw == "XXXXXXXXXX";

        decimal? patientLiability = null;
        if (insuranceLine == "MM")
        {
            var amtValue = loop2300.GetElementValue("AMT", 0, "D2", 1);
            if (amtValue != null && decimal.TryParse(amtValue, out var amt))
                patientLiability = amt;
        }

        OhioProvider? provider = null;
        var loop2310 = loop2300.FindChild("2310");
        if (loop2310 != null)
        {
            provider = ExtractProvider(loop2310);
        }

        return new OhioCoverage
        {
            MaintenanceTypeCode = maintenanceTypeCode,
            MaintenanceAction = ResolveMaintenanceAction(maintenanceTypeCode),
            InsuranceLineCode = insuranceLine,
            InsuranceLineDescription = InsuranceLineCodes.GetDescription(insuranceLine),
            PlanCoverageDesc = planCoverageDesc,
            PlanCoverageDescription = PlanCoverageDescCodes.GetDescription(planCoverageDesc),
            BenefitBeginDate = loop2300.GetElementValue("DTP", 0, "348", 2),
            BenefitEndDate = loop2300.GetElementValue("DTP", 0, "349", 2),
            RateCellIndicator = rateCellMissing ? null : rateCellRaw,
            RateCellMissing = rateCellMissing,
            PatientLiabilityAmount = patientLiability,
            Provider = provider
        };
    }

    private static OhioProvider ExtractProvider(EdiLoop loop2310)
    {
        var nm1 = loop2310.Segments.FirstOrDefault(s => s.SegmentId == "NM1");
        if (nm1 == null) return new OhioProvider();

        return new OhioProvider
        {
            EntityTypeQualifier = nm1.GetElement(0),
            Name = nm1.GetElement(2),
            IdQualifier = nm1.GetElement(7),
            Id = nm1.GetElement(8)
        };
    }

    internal static MaintenanceAction ResolveMaintenanceAction(string code) => code switch
    {
        "001" => MaintenanceAction.Change,
        "002" => MaintenanceAction.Delete,
        "021" => MaintenanceAction.Add,
        "024" => MaintenanceAction.Termination,
        "025" => MaintenanceAction.Reinstate,
        "030" => MaintenanceAction.Audit,
        _ => MaintenanceAction.Change // default fallback
    };
}
