namespace EdiTestHarness;

/// <summary>
/// Common interface for all state EDI 834 parsers.
/// Each state parser adapter implements this to plug into the harness.
/// </summary>
public interface IEdiParser
{
    /// <summary>Short identifier for the parser (e.g., "ohio", "louisiana").</summary>
    string ParserName { get; }

    /// <summary>Parse raw EDI content and return a common result.</summary>
    HarnessParseResult Parse(string rawEdiContent, string fileName);
}

/// <summary>
/// Common parse result that all parser adapters produce.
/// Abstracts away state-specific model differences.
/// </summary>
public class HarnessParseResult
{
    public string FileName { get; init; } = string.Empty;
    public bool Success { get; init; }
    public string? ErrorMessage { get; init; }
    public TimeSpan Duration { get; init; }

    // Envelope
    public string? SenderId { get; init; }
    public string? ReceiverId { get; init; }
    public string? ControlNumber { get; init; }

    // Transactions
    public List<HarnessTransaction> Transactions { get; init; } = new();

    // Validation
    public List<HarnessValidationIssue> ValidationIssues { get; init; } = new();
}

public class HarnessTransaction
{
    public string? FileType { get; init; }
    public string? ProviderId { get; init; }
    public string? EffectiveDate { get; init; }
    public List<HarnessMember> Members { get; init; } = new();
}

public class HarnessMember
{
    public string? MemberId { get; init; }
    public string? MaintenanceType { get; init; }
    public string? MaintenanceAction { get; init; }
    public string? LastName { get; init; }
    public string? FirstName { get; init; }
    public string? MiddleName { get; init; }
    public string? DateOfBirth { get; init; }
    public string? Gender { get; init; }
    public string? Ssn { get; init; }
    public string? City { get; init; }
    public string? State { get; init; }
    public string? Zip { get; init; }
    public int CoverageCount { get; init; }
    public List<HarnessCoverage> Coverages { get; init; } = new();
    public bool HasCriticalErrors { get; init; }

    /// <summary>State-specific fields stored as key-value pairs.</summary>
    public Dictionary<string, string?> ExtendedFields { get; init; } = new();
}

public class HarnessCoverage
{
    public string? MaintenanceType { get; init; }
    public string? InsuranceLine { get; init; }
    public string? PlanDescription { get; init; }
    public string? BeginDate { get; init; }
    public string? EndDate { get; init; }

    /// <summary>State-specific fields stored as key-value pairs.</summary>
    public Dictionary<string, string?> ExtendedFields { get; init; } = new();
}

public class HarnessValidationIssue
{
    public string RuleCode { get; init; } = string.Empty;
    public string Severity { get; init; } = string.Empty;   // Critical, Warning, Informational
    public string Message { get; init; } = string.Empty;
    public string? MemberId { get; init; }
}
