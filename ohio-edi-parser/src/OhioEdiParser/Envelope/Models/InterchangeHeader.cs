namespace OhioEdiParser.Envelope.Models;

public class InterchangeHeader
{
    public string SenderId { get; init; } = string.Empty;       // ISA06
    public string ReceiverId { get; init; } = string.Empty;     // ISA08
    public string ControlNumber { get; init; } = string.Empty;  // ISA13
    public string Date { get; init; } = string.Empty;           // ISA09
    public string Time { get; init; } = string.Empty;           // ISA10
}
