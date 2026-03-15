namespace EdiTestHarness.Parsers;

/// <summary>
/// Registry of available EDI parsers. Add new state parsers here.
/// </summary>
public static class ParserRegistry
{
    private static readonly Dictionary<string, Func<IEdiParser>> Parsers = new(StringComparer.OrdinalIgnoreCase)
    {
        ["ohio"] = () => new OhioParserAdapter(),
        // Add future parsers here:
        // ["louisiana"] = () => new LouisianaParserAdapter(),
    };

    public static IEdiParser? GetParser(string name) =>
        Parsers.TryGetValue(name, out var factory) ? factory() : null;

    public static IEnumerable<string> AvailableParsers => Parsers.Keys;
}
