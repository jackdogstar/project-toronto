using System.Diagnostics;
using OhioEdiParser;
using OhioEdiParser.Models;

namespace EdiTestHarness.Parsers;

public class OhioParserAdapter : IEdiParser
{
    public string ParserName => "ohio";

    private readonly Ohio834Parser _parser = new();

    public HarnessParseResult Parse(string rawEdiContent, string fileName)
    {
        var sw = Stopwatch.StartNew();

        try
        {
            var result = _parser.Parse(rawEdiContent);
            sw.Stop();

            var transactions = result.Transactions.Select(tx => new HarnessTransaction
            {
                FileType = tx.Header.FileType.ToString(),
                ProviderId = tx.Header.ProviderId,
                EffectiveDate = tx.Header.FileEffectiveDate,
                Members = tx.Members.Select(MapMember).ToList()
            }).ToList();

            var issues = result.Validation.Issues.Select(i => new HarnessValidationIssue
            {
                RuleCode = i.RuleCode,
                Severity = i.Severity.ToString(),
                Message = i.Message,
                MemberId = i.MemberMedicaidId
            }).ToList();

            return new HarnessParseResult
            {
                FileName = fileName,
                Success = true,
                Duration = sw.Elapsed,
                SenderId = result.Interchange.SenderId,
                ReceiverId = result.Interchange.ReceiverId,
                ControlNumber = result.Interchange.ControlNumber,
                Transactions = transactions,
                ValidationIssues = issues
            };
        }
        catch (Exception ex)
        {
            sw.Stop();
            return new HarnessParseResult
            {
                FileName = fileName,
                Success = false,
                ErrorMessage = ex.Message,
                Duration = sw.Elapsed
            };
        }
    }

    private static HarnessMember MapMember(OhioMember m) => new()
    {
        MemberId = m.MedicaidId,
        MaintenanceType = m.MaintenanceTypeCode,
        MaintenanceAction = m.MaintenanceAction.ToString(),
        LastName = m.Demographics?.LastName,
        FirstName = m.Demographics?.FirstName,
        MiddleName = m.Demographics?.MiddleName,
        DateOfBirth = m.Demographics?.DateOfBirth,
        Gender = m.Demographics?.Gender,
        Ssn = m.Demographics?.Ssn,
        City = m.Demographics?.Address?.City,
        State = m.Demographics?.Address?.State,
        Zip = m.Demographics?.Address?.Zip,
        CoverageCount = m.Coverages.Count,
        HasCriticalErrors = m.HasCriticalErrors,
        Coverages = m.Coverages.Select(c => new HarnessCoverage
        {
            MaintenanceType = c.MaintenanceTypeCode,
            InsuranceLine = c.InsuranceLineCode,
            PlanDescription = c.PlanCoverageDesc,
            BeginDate = c.BenefitBeginDate,
            EndDate = c.BenefitEndDate,
            ExtendedFields = new Dictionary<string, string?>
            {
                ["RateCellIndicator"] = c.RateCellIndicator,
                ["RateCellMissing"] = c.RateCellMissing.ToString(),
                ["PatientLiability"] = c.PatientLiabilityAmount?.ToString(),
                ["InsuranceLineDesc"] = c.InsuranceLineDescription,
                ["PlanCoverageDescFull"] = c.PlanCoverageDescription
            }
        }).ToList(),
        ExtendedFields = new Dictionary<string, string?>
        {
            ["AssignmentReason"] = m.AssignmentReasonCode,
            ["AssignmentReasonDesc"] = m.AssignmentReasonDescription,
            ["EmploymentStatus"] = m.EmploymentStatus,
            ["IsIeOrigin"] = m.IsIeOrigin.ToString(),
            ["MedicareId"] = m.MedicareId,
            ["AlternateId"] = m.AlternateId,
            ["CountyOfEligibility"] = m.CountyOfEligibility,
            ["AidCategory"] = m.AidCategory,
            ["RedeterminationDate"] = m.RedeterminationDate,
            ["MedicaidBeginDate"] = m.MedicaidBeginDate,
            ["MedicaidEndDate"] = m.MedicaidEndDate,
            ["DateOfDeath"] = m.DateOfDeath,
            ["ResponsiblePersonType"] = m.ResponsiblePerson?.TypeCode,
            ["CobCount"] = m.CoordinationOfBenefits.Count.ToString(),
            ["ReportingCategoryCount"] = m.ReportingCategories.Count.ToString()
        }
    };
}
