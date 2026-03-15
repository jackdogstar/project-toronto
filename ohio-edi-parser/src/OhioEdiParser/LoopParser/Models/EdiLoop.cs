namespace OhioEdiParser.LoopParser.Models;

public class EdiLoop
{
    public string LoopId { get; init; } = string.Empty;
    public List<EdiSegment> Segments { get; } = new();
    public List<EdiLoop> Children { get; } = new();

    public EdiLoop? FindChild(string loopId) =>
        Children.FirstOrDefault(c => c.LoopId == loopId);

    public IEnumerable<EdiLoop> FindChildren(string loopId) =>
        Children.Where(c => c.LoopId == loopId);

    /// <summary>
    /// Finds a segment by ID and optional qualifier (element at qualifierIndex == qualifierValue).
    /// </summary>
    public EdiSegment? FindSegment(string segmentId, int qualifierIndex = -1, string? qualifierValue = null)
    {
        foreach (var seg in Segments)
        {
            if (seg.SegmentId != segmentId) continue;
            if (qualifierIndex >= 0 && qualifierValue != null)
            {
                if (seg.GetElement(qualifierIndex) != qualifierValue) continue;
            }
            return seg;
        }
        return null;
    }

    /// <summary>
    /// Gets element value from a qualified segment within this loop.
    /// </summary>
    public string? GetElementValue(string segmentId, int qualifierIndex, string qualifierValue, int elementIndex)
    {
        var seg = FindSegment(segmentId, qualifierIndex, qualifierValue);
        if (seg == null) return null;
        var val = seg.GetElement(elementIndex);
        return string.IsNullOrEmpty(val) ? null : val;
    }
}
