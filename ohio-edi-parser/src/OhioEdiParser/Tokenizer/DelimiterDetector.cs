using OhioEdiParser.Envelope.Models;

namespace OhioEdiParser.Tokenizer;

public static class DelimiterDetector
{
    /// <summary>
    /// Reads the ISA segment (fixed-width 106 characters) to detect EDI delimiters.
    /// ISA is always exactly 106 characters: "ISA" + 103 data chars + segment terminator.
    /// Element separator is at position 3, sub-element separator at 104, segment terminator at 105.
    /// Repetition separator is ISA11 (element 11 of the ISA segment).
    /// </summary>
    public static DetectedDelimiters Detect(string rawEdi)
    {
        if (string.IsNullOrEmpty(rawEdi))
            throw new InvalidOperationException("EDI content is empty.");

        // Strip leading whitespace/BOM to find ISA
        var trimmed = rawEdi.TrimStart('\uFEFF', ' ', '\t', '\r', '\n');

        if (trimmed.Length < 106)
            throw new InvalidOperationException("EDI content is too short to contain a valid ISA segment.");

        if (!trimmed.StartsWith("ISA"))
            throw new InvalidOperationException("EDI content does not start with ISA segment.");

        char elementSeparator = trimmed[3];
        char segmentTerminator = trimmed[105];

        // Sub-element separator is at position 104 (the last element of ISA before the terminator)
        char subElementSeparator = trimmed[104];

        // Repetition separator is ISA11 — split ISA on element separator and take element 11
        var isaContent = trimmed[..106];
        var elements = isaContent.Split(elementSeparator);

        // ISA has 16 elements: ISA, 01, 02, ..., 16
        // Element 11 (0-based index 11) is the repetition separator
        char repetitionSeparator = '^'; // default
        if (elements.Length > 11 && elements[11].Length > 0)
        {
            repetitionSeparator = elements[11][0];
        }

        return new DetectedDelimiters(elementSeparator, subElementSeparator, segmentTerminator, repetitionSeparator);
    }
}
