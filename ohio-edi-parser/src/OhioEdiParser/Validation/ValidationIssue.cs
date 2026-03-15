namespace OhioEdiParser.Validation;

public class ValidationIssue
{
    public string RuleCode { get; init; } = string.Empty;
    public ValidationSeverity Severity { get; init; }
    public string Message { get; init; } = string.Empty;
    public string? MemberMedicaidId { get; init; }
    public int? CoverageIndex { get; init; }
}
