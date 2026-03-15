namespace OhioEdiParser.CodeSets;

public static class MceReceiverIds
{
    private static readonly Dictionary<string, string> Codes = new()
    {
        ["0021920"] = "AmeriHealth Caritas Ohio, Inc.",
        ["0002937"] = "Anthem Blue Cross Blue Shield",
        ["0004202"] = "Buckeye Community Health Plan",
        ["0003150"] = "CareSource",
        ["0021919"] = "Humana Health Plan of Ohio, Inc.",
        ["0007316"] = "Molina Healthcare of Ohio",
        ["0007610"] = "United Healthcare Community Plan of Ohio, Inc.",
        ["0021457"] = "Aetna Better Health of Ohio Inc.",
        ["0021914"] = "Aetna OhioRISE"
    };

    public static string? GetDescription(string code) => Codes.GetValueOrDefault(code);
    public static bool IsKnown(string code) => Codes.ContainsKey(code);
}
