namespace OhioEdiParser.Models;

public class OhioDemographics
{
    public string LastName { get; init; } = string.Empty;
    public string FirstName { get; init; } = string.Empty;
    public string? MiddleName { get; init; }
    public string? Ssn { get; init; }
    public string DateOfBirth { get; init; } = string.Empty;
    public string Gender { get; init; } = string.Empty;
    public List<string> RaceCodes { get; init; } = new();
    public List<string?> RaceDescriptions { get; init; } = new();
    public OhioAddress? Address { get; init; }
    public List<OhioContact> Contacts { get; init; } = new();
    public string? CountyCode { get; init; }
}
