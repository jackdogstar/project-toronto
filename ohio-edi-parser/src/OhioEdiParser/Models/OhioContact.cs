namespace OhioEdiParser.Models;

public class OhioContact
{
    public string Type { get; init; } = string.Empty;   // TE, CP, HP, WP, EM
    public string Value { get; init; } = string.Empty;
}
