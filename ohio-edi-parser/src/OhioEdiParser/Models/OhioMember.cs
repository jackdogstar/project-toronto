namespace OhioEdiParser.Models;

public class OhioMember
{
    // INS fields
    public string MaintenanceTypeCode { get; init; } = string.Empty;
    public MaintenanceAction MaintenanceAction { get; init; }
    public string AssignmentReasonCode { get; init; } = string.Empty;
    public string? AssignmentReasonDescription { get; init; }
    public string EmploymentStatus { get; init; } = string.Empty;
    public string? DateOfDeath { get; init; }

    // Identifiers
    public string MedicaidId { get; init; } = string.Empty;
    public bool IsIeOrigin { get; init; }
    public string? NewbornMotherId { get; init; }
    public string? AidCategory { get; init; }
    public string? AidCategoryEffectiveDate { get; init; }
    public string? IeCaseNumber { get; init; }
    public string? AlternateId { get; init; }
    public string? MedicareId { get; init; }
    public string? CountyOfEligibility { get; init; }
    public string? LinkedSecondaryId { get; init; }

    // Dates
    public string? RedeterminationDate { get; init; }
    public string? MedicaidBeginDate { get; init; }
    public string? MedicaidEndDate { get; init; }

    // Nested
    public OhioDemographics Demographics { get; init; } = null!;
    public List<OhioCoverage> Coverages { get; init; } = new();
    public OhioResponsiblePerson? ResponsiblePerson { get; init; }
    public List<OhioCob> CoordinationOfBenefits { get; init; } = new();
    public List<OhioReportingCategory> ReportingCategories { get; init; } = new();

    // Validation flags
    public bool HasCriticalErrors { get; set; }
}
