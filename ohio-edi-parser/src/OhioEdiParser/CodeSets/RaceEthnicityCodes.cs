namespace OhioEdiParser.CodeSets;

public static class RaceEthnicityCodes
{
    private static readonly Dictionary<string, string> Codes = new()
    {
        ["7"] = "Not provided",
        ["A"] = "Asian or Pacific Islander",
        ["B"] = "Black",
        ["C"] = "Caucasian",
        ["D"] = "Subcontinent Asian American",
        ["E"] = "Other Race or Ethnicity",
        ["F"] = "Asian Pacific American",
        ["G"] = "Native American",
        ["H"] = "Hispanic",
        ["I"] = "American Indian or Alaskan Native",
        ["J"] = "Native Hawaiian",
        ["N"] = "Black (Non-Hispanic)",
        ["O"] = "White (Non-Hispanic)",
        ["P"] = "Pacific Islander"
    };

    public static string? GetDescription(string code) => Codes.GetValueOrDefault(code);
    public static bool IsKnown(string code) => Codes.ContainsKey(code);
}
