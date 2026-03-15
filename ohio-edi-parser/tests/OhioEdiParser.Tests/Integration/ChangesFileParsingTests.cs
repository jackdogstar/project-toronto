using OhioEdiParser.Models;
using OhioEdiParser.Tests.TestData.Builders;

namespace OhioEdiParser.Tests.Integration;

public class ChangesFileParsingTests
{
    private readonly Ohio834Parser _parser = new();

    [Fact]
    public void ChangesFile_Addition_ParsesCorrectly()
    {
        var edi = EdiBuilder.Create()
            .AsChangesFile()
            .AddMember(m => m
                .WithMaintenanceType("021")
                .WithAssignmentReason("16")
                .WithMedicaidId("123456789012")
                .WithName("JONES", "ALICE")
                .AddCoverage("021", "HMO", "CFC", "20250101", "20251231", "OHCFCF1825"))
            .Build();

        var result = _parser.Parse(edi);
        var member = result.Transactions[0].Members[0];

        Assert.Equal(OhioFileType.Changes, result.Transactions[0].Header.FileType);
        Assert.Equal(MaintenanceAction.Add, member.MaintenanceAction);
        Assert.Equal("Member selected MCE through enrollment broker", member.AssignmentReasonDescription);
        Assert.False(member.HasCriticalErrors);
    }

    [Fact]
    public void ChangesFile_Termination_WithDeathDate()
    {
        var edi = EdiBuilder.Create()
            .AsChangesFile()
            .AddMember(m => m
                .WithMaintenanceType("024")
                .WithAssignmentReason("3")
                .WithDateOfDeath("20250301")
                .WithMedicaidId("123456789012")
                .AddCoverage("024", "HMO", "CFC", "20250101", "20250301"))
            .Build();

        var result = _parser.Parse(edi);
        var member = result.Transactions[0].Members[0];

        Assert.Equal(MaintenanceAction.Termination, member.MaintenanceAction);
        Assert.Equal("20250301", member.DateOfDeath);
        Assert.Equal("Date of death", member.AssignmentReasonDescription);
    }

    [Fact]
    public void ChangesFile_Change_DemographicUpdate()
    {
        var edi = EdiBuilder.Create()
            .AsChangesFile()
            .AddMember(m => m
                .WithMaintenanceType("001")
                .WithAssignmentReason("25")
                .WithMedicaidId("123456789012")
                .WithName("NEWNAME", "MARY")
                .WithAddress("789 NEW ST", "AKRON", "OH", "44301")
                .AddCoverage("001", "HMO", "CFC", "20250101", "20251231"))
            .Build();

        var result = _parser.Parse(edi);
        var member = result.Transactions[0].Members[0];

        Assert.Equal(MaintenanceAction.Change, member.MaintenanceAction);
        Assert.Equal("NEWNAME", member.Demographics.LastName);
        Assert.Equal("AKRON", member.Demographics.Address!.City);
    }

    [Fact]
    public void ChangesFile_MemberWithAllOptionalLoops()
    {
        var edi = EdiBuilder.Create()
            .AsChangesFile()
            .AddMember(m => m
                .WithMaintenanceType("021")
                .WithAssignmentReason("28")
                .WithMedicaidId("912345678901") // IE origin
                .AddRef("F6", "1EG4TE5MK73")   // Medicare ID
                .AddRef("6O", "ALT987654321")   // Alternate ID
                .AddRef("Q4", "LNK123456789")   // Linked ID
                .AddRef("DX", "25")             // County
                .AddDtp("300", "20260101")       // Redetermination
                .AddDtp("473", "20250101")       // Medicaid Begin
                .AddDtp("474", "20251231")       // Medicaid End
                .AddResponsiblePerson("S1", "PARENT", "MARY")
                .AddCoverage("021", "HMO", "CFC", "20250101", "20251231", "OHCFCF1825")
                .AddCob("P", "1", "MEDICARE")
                .AddReportingCategory("LIVING ARRANGEMENT", "LU", "01"))
            .Build();

        var result = _parser.Parse(edi);
        var member = result.Transactions[0].Members[0];

        Assert.True(member.IsIeOrigin);
        Assert.Equal("1EG4TE5MK73", member.MedicareId);
        Assert.Equal("ALT987654321", member.AlternateId);
        Assert.Equal("LNK123456789", member.LinkedSecondaryId);
        Assert.Equal("25", member.CountyOfEligibility);
        Assert.Equal("20260101", member.RedeterminationDate);
        Assert.Equal("20250101", member.MedicaidBeginDate);
        Assert.Equal("20251231", member.MedicaidEndDate);

        // Responsible person
        Assert.NotNull(member.ResponsiblePerson);
        Assert.Equal("S1", member.ResponsiblePerson!.TypeCode);
        Assert.Equal("PARENT", member.ResponsiblePerson.LastName);

        // COB
        Assert.Single(member.CoordinationOfBenefits);
        Assert.Equal("P", member.CoordinationOfBenefits[0].PayerResponsibility);
        Assert.Equal("MEDICARE", member.CoordinationOfBenefits[0].InsurerName);

        // Reporting categories
        Assert.Single(member.ReportingCategories);
        Assert.Equal("01", member.ReportingCategories[0].RefValue);

        // Validation informational issues
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-201"); // dual-eligible
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-202"); // alternate ID
        Assert.Contains(result.Validation.Issues, i => i.RuleCode == "OH-VAL-107"); // linked ID
    }
}
