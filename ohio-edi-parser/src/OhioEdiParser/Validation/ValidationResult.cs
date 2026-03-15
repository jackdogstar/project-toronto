namespace OhioEdiParser.Validation;

public class ValidationResult
{
    public List<ValidationIssue> Issues { get; }
    public bool HasCriticalErrors => Issues.Any(i => i.Severity == ValidationSeverity.Critical);

    public ValidationResult(List<ValidationIssue> issues)
    {
        Issues = issues;
    }
}
