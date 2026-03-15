namespace OhioEdiParser.Envelope.Models;

public class FunctionalGroupHeader
{
    public string FunctionalIdCode { get; init; } = string.Empty;  // GS01
    public string ApplicationSender { get; init; } = string.Empty; // GS02
    public string ApplicationReceiver { get; init; } = string.Empty; // GS03
    public string ControlNumber { get; init; } = string.Empty;    // GS06
}
