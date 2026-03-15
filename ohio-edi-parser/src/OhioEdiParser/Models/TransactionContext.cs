namespace OhioEdiParser.Models;

public class TransactionContext
{
    public OhioFileType FileType { get; init; }
    public string FileReferenceId { get; init; } = string.Empty;
    public string FileEffectiveDate { get; init; } = string.Empty;
    public string ProviderId { get; init; } = string.Empty;
    public string SponsorName { get; init; } = string.Empty;
    public string SponsorTaxId { get; init; } = string.Empty;
    public string MceName { get; init; } = string.Empty;
    public string MceTaxId { get; init; } = string.Empty;
}
