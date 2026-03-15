namespace OhioEdiParser.Models;

public class OhioCob
{
    public string PayerResponsibility { get; init; } = string.Empty;
    public string CobCode { get; init; } = string.Empty;
    public string? OtherInsuranceGroupNumber { get; init; }
    public string? OtherInsuranceSsn { get; init; }
    public string? InsurerName { get; init; }
}
