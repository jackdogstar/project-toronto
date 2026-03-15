namespace OhioEdiParser.CodeSets;

public static class PlanCoverageDescCodes
{
    private static readonly Dictionary<string, string> Codes = new()
    {
        // Managed Care
        ["ABD"] = "Aged/Blind/Disabled",
        ["CFC"] = "Covered Families and Children",
        ["OHR"] = "OhioRISE",

        // Behavioral Health / Treatment
        ["ACT"] = "Assertive Community Treatment",
        ["BH-SUD"] = "Behavioral Health - Substance Use Disorder",
        ["BH-SPMI"] = "Behavioral Health - Serious & Persistent Mental Illness",
        ["CARA"] = "Comprehensive Addiction and Recovery Act",
        ["IHBT"] = "Intensive Home-Based Treatment",
        ["SRSP"] = "State Residential Service Provider",

        // Medicare
        ["MEDICARE-A"] = "Medicare Part A",
        ["MEDICARE-B"] = "Medicare Part B",
        ["MEDICARE-C"] = "Medicare Part C",
        ["MEDICARE-D"] = "Medicare Part D",

        // Waivers
        ["WVR-A1"] = "Waiver A1",
        ["WVR-A4"] = "Waiver A4",
        ["WVR-A"] = "Waiver A",
        ["WVR-9"] = "Waiver 9",
        ["WVR-P3"] = "Waiver P3",
        ["WVR-ICDS"] = "Waiver ICDS",
        ["WVR-10"] = "Waiver 10",
        ["WVR-P"] = "Waiver P",
        ["WVR-B"] = "Waiver B",
        ["WVR-0"] = "Waiver 0",
        ["WVR-OR"] = "Waiver OhioRISE",

        // Nursing / Long-Term Care
        ["NH-CRISE"] = "Nursing Home - OhioRISE Crisis",
        ["NH-MCE"] = "Nursing Home - MCE",
        ["NH-MCADMIT"] = "Nursing Home - MCE Admission",
        ["HSBP"] = "Hospice",

        // Money Follows Person
        ["MFP-N"] = "Money Follows Person - No",
        ["MFP-Y"] = "Money Follows Person - Yes",

        // Patient Liability
        ["PL-F"] = "Patient Liability - F",
        ["PL-C"] = "Patient Liability - C",
        ["PL-G"] = "Patient Liability - G",
        ["PL-H"] = "Patient Liability - H",
        ["PL-I"] = "Patient Liability - I",
        ["PL-N"] = "Patient Liability - N",
        ["PL-R"] = "Patient Liability - R",
        ["PL-W"] = "Patient Liability - W",
        ["PL-P"] = "Patient Liability - P",

        // Supplemental Income
        ["SI-UNE"] = "Supplemental Income - Unemployment",

        // Special Conditions — Exclusionary
        ["951"] = "Exclude from Managed Care",
        ["AGE"] = "Age",
        ["BCM"] = "BCM",
        ["CIC"] = "Children in Custody",
        ["DDR"] = "DDR",
        ["DDW"] = "DDW",
        ["DEF"] = "Deferral",
        ["DOD"] = "Date of Death",
        ["DVS"] = "DVS",
        ["E01"] = "E01",
        ["ELG"] = "Eligibility",
        ["GHO"] = "GHO",
        ["IAH"] = "IAH",
        ["IDD"] = "IDD",
        ["INC"] = "Incarcerated",
        ["IVE"] = "IVE",
        ["JC"] = "Just Cause",
        ["LIS"] = "LIS",
        ["MUL"] = "Multiple",
        ["N4E"] = "N4E",
        ["NUR"] = "Nursing",
        ["OAC"] = "OAC",
        ["PBP"] = "PBP",
        ["RDS"] = "RDS",

        // Special Conditions — Informational
        ["CC1"] = "Care Coordination 1",
        ["CC2"] = "Care Coordination 2",
        ["I01"] = "I01",
        ["IMD"] = "IMD",
        ["O42"] = "O42",
        ["O51"] = "O51",
        ["O54"] = "O54",
        ["OOD"] = "Out of District",
        ["OOH"] = "Out of Home",
        ["OOM"] = "Out of Market",
        ["OOR"] = "Out of Region",
        ["OOV"] = "Out of Visit",
        ["ORW"] = "ORW",
        ["PRE"] = "Pregnancy"
    };

    public static string? GetDescription(string code) => Codes.GetValueOrDefault(code);
    public static bool IsKnown(string code) => Codes.ContainsKey(code);
}
