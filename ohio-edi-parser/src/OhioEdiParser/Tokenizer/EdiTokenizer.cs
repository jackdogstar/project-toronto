using OhioEdiParser.Envelope.Models;
using OhioEdiParser.LoopParser.Models;

namespace OhioEdiParser.Tokenizer;

public static class EdiTokenizer
{
    public static IReadOnlyList<EdiSegment> Tokenize(string rawEdi, DetectedDelimiters delimiters)
    {
        var trimmed = rawEdi.TrimStart('\uFEFF', ' ', '\t', '\r', '\n');
        var segmentStrings = trimmed.Split(delimiters.SegmentTerminator);
        var segments = new List<EdiSegment>();
        int segmentNumber = 0;

        foreach (var raw in segmentStrings)
        {
            // Clean up whitespace/newlines between segments
            var cleaned = raw.Trim(' ', '\t', '\r', '\n');
            if (string.IsNullOrEmpty(cleaned))
                continue;

            var parts = cleaned.Split(delimiters.ElementSeparator);
            var segmentId = parts[0];
            var elements = parts.Length > 1 ? parts[1..] : Array.Empty<string>();

            segments.Add(new EdiSegment(segmentId, elements, segmentNumber));
            segmentNumber++;
        }

        return segments;
    }
}
