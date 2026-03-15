namespace OhioEdiParser.CodeSets;

public static class InsuranceLineCodes
{
    private static readonly Dictionary<string, string> Codes = new()
    {
        ["HMO"] = "Health Maintenance Organization",
        ["AG"] = "Preventative Care/Wellness (Special Conditions)",
        ["AH"] = "24 Hour Care (Waivers)",
        ["AJ"] = "Medicare Risk",
        ["AK"] = "Mental Health (SRSP, ACT, IHBT, BHCC)",
        ["EPO"] = "Exclusive Provider Organization (Restricted Medicaid)",
        ["HLT"] = "Health (Physician CSP, CARA)",
        ["MM"] = "Major Medical (Patient Liability)",
        ["PDG"] = "Prescription Drug (Pharmacy CSP)",
        ["POS"] = "Point of Service (Money Follows Person)",
        ["LTC"] = "Long-Term Care (Nursing Homes, Hospice)",
        ["LTD"] = "Long-Term Disability (Supplemental Income)"
    };

    public static string? GetDescription(string code) => Codes.GetValueOrDefault(code);
    public static bool IsKnown(string code) => Codes.ContainsKey(code);
}
