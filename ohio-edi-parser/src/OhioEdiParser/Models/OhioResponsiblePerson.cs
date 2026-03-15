namespace OhioEdiParser.Models;

public class OhioResponsiblePerson
{
    public string TypeCode { get; init; } = string.Empty;
    public string? LastName { get; init; }
    public string? FirstName { get; init; }
    public string? OrganizationName { get; init; }
    public OhioAddress? Address { get; init; }
    public List<OhioContact> Contacts { get; init; } = new();
}
