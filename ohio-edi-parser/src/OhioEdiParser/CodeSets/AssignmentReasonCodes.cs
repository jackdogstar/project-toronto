namespace OhioEdiParser.CodeSets;

public static class AssignmentReasonCodes
{
    private static readonly Dictionary<string, string> Codes = new()
    {
        // Add (Start) Reasons
        ["28"] = "Auto-enrollment: same MCE within previous 3 months, or newborn on mother's MCE",
        ["14"] = "Assigned by enrollment broker",
        ["15"] = "Enrollment addition by ODM managed care staff",
        ["16"] = "Member selected MCE through enrollment broker",
        ["17"] = "Retroactive re-enrollment for restored eligibility",
        ["AJ"] = "Assigned effective first day of current month per Day 1 rules",

        // Change & Delete (Stop) Reasons
        ["1"] = "Lost eligibility",
        ["2"] = "NF, IID, or HCBS Waiver Level of Care",
        ["3"] = "Date of death",
        ["5"] = "12-digit billing ID not active",
        ["6"] = "Disenrollment by ODM managed care staff",
        ["7"] = "No longer Medicaid eligible",
        ["9"] = "Incarcerated",
        ["10"] = "No longer in MCE service area",
        ["11"] = "Exempt by ODM Just Cause Determination",
        ["18"] = "Voluntary MCE change",
        ["29"] = "Enrolled in PACE or ODM staff action",
        ["37"] = "Invalid living arrangement code for managed care",
        ["38"] = "Special condition excluding from managed care",
        ["40"] = "Aid category not eligible for managed care program",
        ["43"] = "Lost Medicare A and/or B",
        ["AA"] = "Mutually exclusive benefit plan",
        ["AB"] = "OhioRISE disenrollment",
        ["AD"] = "Age invalid for aid category",
        ["EC"] = "Third Party Liability coverage",
        ["XT"] = "Enrolled in Medicare Part A and/or B",

        // System Reasons
        ["25"] = "System default for 001 Change transactions",
        ["AI"] = "System default (reason not in list)",
        ["XN"] = "System default — sent only on Full File"
    };

    public static string? GetDescription(string code) => Codes.GetValueOrDefault(code);
    public static bool IsKnown(string code) => Codes.ContainsKey(code);
}
