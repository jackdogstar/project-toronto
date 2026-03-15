namespace OhioEdiParser.Models;

public class OhioCoverage
{
    public string MaintenanceTypeCode { get; init; } = string.Empty;
    public MaintenanceAction MaintenanceAction { get; init; }
    public string InsuranceLineCode { get; init; } = string.Empty;
    public string? InsuranceLineDescription { get; init; }
    public string PlanCoverageDesc { get; init; } = string.Empty;
    public string? PlanCoverageDescription { get; init; }
    public string? BenefitBeginDate { get; init; }
    public string? BenefitEndDate { get; init; }
    public string? RateCellIndicator { get; init; }
    public bool RateCellMissing { get; init; }
    public decimal? PatientLiabilityAmount { get; init; }
    public OhioProvider? Provider { get; init; }
}
