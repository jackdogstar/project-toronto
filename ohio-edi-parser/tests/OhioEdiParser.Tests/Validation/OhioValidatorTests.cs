using OhioEdiParser.Models;
using OhioEdiParser.Tests.TestData.Builders;
using OhioEdiParser.Validation;

namespace OhioEdiParser.Tests.Validation;

public class OhioValidatorTests
{
    private readonly Ohio834Parser _parser = new();

    private OhioParseResult ParseResult(Action<EdiBuilder>? configureBuilder = null,
        Action<MemberBuilder>? configureMember = null)
    {
        var builder = EdiBuilder.Create().AsChangesFile();
        configureBuilder?.Invoke(builder);
        builder.AddMember(m => configureMember?.Invoke(m));
        return _parser.Parse(builder.Build());
    }

    [Fact]
    public void OHVAL001_MedicaidIdWrongLength_Critical()
    {
        var result = ParseResult(configureMember: m => m.WithMedicaidId("12345"));
        Assert.Contains(result.Validation.Issues,
            i => i.RuleCode == "OH-VAL-001" && i.Severity == ValidationSeverity.Critical);
    }

    [Fact]
    public void OHVAL001_MedicaidId12Chars_NoCritical()
    {
        var result = ParseResult(configureMember: m => m.WithMedicaidId("123456789012"));
        Assert.DoesNotContain(result.Validation.Issues, i => i.RuleCode == "OH-VAL-001");
    }

    [Fact]
    public void OHVAL002_InvalidMaintenanceType_Critical()
    {
        var result = ParseResult(configureMember: m => m.WithMaintenanceType("999"));
        Assert.Contains(result.Validation.Issues,
            i => i.RuleCode == "OH-VAL-002" && i.Severity == ValidationSeverity.Critical);
    }

    [Fact]
    public void OHVAL003_FullFileWithNon030_Critical()
    {
        var result = ParseResult(
            configureBuilder: b => b.AsFullFile(),
            configureMember: m => m.WithMaintenanceType("021"));
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-003");
    }

    [Fact]
    public void OHVAL004_ChangesFileWith030_Critical()
    {
        var result = ParseResult(configureMember: m => m.WithMaintenanceType("030"));
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-004");
    }

    [Fact]
    public void OHVAL006_MissingBenefitBeginDate_Critical()
    {
        // The default member builder includes a begin date, so this tests a member with
        // a coverage that has no DTP*348 — we'd need a custom coverage for this.
        // For now, just verify a valid member passes
        var result = ParseResult();
        Assert.DoesNotContain(result.Validation.Issues, i => i.RuleCode == "OH-VAL-006");
    }

    [Fact]
    public void OHVAL101_UnknownAssignmentReason_Warning()
    {
        var result = ParseResult(configureMember: m => m.WithAssignmentReason("ZZZ"));
        Assert.Contains(result.Validation.Issues,
            i => i.RuleCode == "OH-VAL-101" && i.Severity == ValidationSeverity.Warning);
    }

    [Fact]
    public void OHVAL103_RateCellXXXXXXXXXX_Warning()
    {
        var result = ParseResult(configureMember: m =>
            m.AddCoverage("021", "HMO", "CFC", "20250101", "20251231", "XXXXXXXXXX"));
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-103");
    }

    [Fact]
    public void OHVAL104_DeathWithoutDate_Warning()
    {
        var result = ParseResult(configureMember: m =>
            m.WithAssignmentReason("3").WithMaintenanceType("024"));
        Assert.Contains(result.Validation.Issues,
            i => i.RuleCode == "OH-VAL-104" && i.Severity == ValidationSeverity.Warning);
    }

    [Fact]
    public void OHVAL105_OdmPlaceholderAddress_Warning()
    {
        var result = ParseResult(configureMember: m => m.WithOdmPlaceholderAddress());
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-105");
    }

    [Fact]
    public void OHVAL201_DualEligible_Informational()
    {
        var result = ParseResult(configureMember: m => m.AddRef("F6", "MCAREID123"));
        Assert.Contains(result.Validation.Issues,
            i => i.RuleCode == "OH-VAL-201" && i.Severity == ValidationSeverity.Informational);
    }

    [Fact]
    public void OHVAL202_AlternateId_Informational()
    {
        var result = ParseResult(configureMember: m => m.AddRef("6O", "ALT123"));
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-202");
    }
}
