namespace OhioEdiParser.LoopParser.Models;

/// <summary>
/// A single EDI segment split into its component elements.
/// Elements[0] is the first data element (segment ID is separate).
/// </summary>
public record EdiSegment(string SegmentId, string[] Elements, int SegmentNumber)
{
    public string GetElement(int index) =>
        index >= 0 && index < Elements.Length ? Elements[index] : string.Empty;
}
