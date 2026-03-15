namespace OhioEdiParser.Models;

public class OhioReportingCategory
{
    public string CategoryType { get; init; } = string.Empty;   // "LIVING ARRANGEMENT", "PREGNANT", "WORK REQUIREMENT - MANDATORY"
    public string RefQualifier { get; init; } = string.Empty;   // LU, ZZ, XX1
    public string RefValue { get; init; } = string.Empty;       // code or text
    public string? RefDescription { get; init; }                // lookup for living arrangement
    public string? DateValue { get; init; }                     // single date (D8)
    public string? DateRangeStart { get; init; }                // range start (RD8)
    public string? DateRangeEnd { get; init; }                  // range end (RD8)
}
