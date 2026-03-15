using OhioEdiParser.LoopParser.Models;

namespace OhioEdiParser.Envelope.Models;

public class TransactionSetEnvelope
{
    public InterchangeHeader Interchange { get; init; } = null!;
    public FunctionalGroupHeader FunctionalGroup { get; init; } = null!;
    public string TransactionSetControlNumber { get; init; } = string.Empty;  // ST02
    public IReadOnlyList<EdiSegment> BodySegments { get; init; } = Array.Empty<EdiSegment>();
}
