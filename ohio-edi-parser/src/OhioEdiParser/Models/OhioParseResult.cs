using OhioEdiParser.Envelope.Models;
using OhioEdiParser.Validation;

namespace OhioEdiParser.Models;

public class OhioParseResult
{
    public List<OhioTransaction> Transactions { get; init; } = new();
    public ValidationResult Validation { get; init; } = null!;
    public InterchangeHeader Interchange { get; init; } = null!;
}
