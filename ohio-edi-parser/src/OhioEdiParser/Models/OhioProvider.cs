namespace OhioEdiParser.Models;

public class OhioProvider
{
    public string EntityTypeQualifier { get; init; } = string.Empty; // FA, QA, Y2
    public string Name { get; init; } = string.Empty;
    public string IdQualifier { get; init; } = string.Empty;        // XX=NPI, SV=Medicaid
    public string Id { get; init; } = string.Empty;
}
