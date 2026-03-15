namespace OhioEdiParser.Envelope.Models;

public record DetectedDelimiters(
    char ElementSeparator,
    char SubElementSeparator,
    char SegmentTerminator,
    char RepetitionSeparator);
