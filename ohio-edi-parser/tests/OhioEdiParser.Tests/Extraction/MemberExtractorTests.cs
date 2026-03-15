using OhioEdiParser.Models;
using OhioEdiParser.Tests.TestData.Builders;

namespace OhioEdiParser.Tests.Extraction;

public class MemberExtractorTests
{
    private readonly Ohio834Parser _parser = new();

    private OhioMember ParseSingleMember(Action<EdiBuilder>? configureBuilder = null, Action<MemberBuilder>? configureMember = null)
    {
        var builder = EdiBuilder.Create().AsChangesFile();
        configureBuilder?.Invoke(builder);
        builder.AddMember(m =>
        {
            configureMember?.Invoke(m);
        });
        var result = _parser.Parse(builder.Build());
        return result.Transactions[0].Members[0];
    }

    [Fact]
    public void MedicaidId_ExtractedFromRefOF()
    {
        var member = ParseSingleMember(configureMember: m => m.WithMedicaidId("123456789012"));
        Assert.Equal("123456789012", member.MedicaidId);
    }

    [Fact]
    public void IsIeOrigin_TrueWhenStartsWith9()
    {
        var member = ParseSingleMember(configureMember: m => m.WithMedicaidId("912345678901"));
        Assert.True(member.IsIeOrigin);
    }

    [Fact]
    public void IsIeOrigin_FalseWhenDoesNotStartWith9()
    {
        var member = ParseSingleMember(configureMember: m => m.WithMedicaidId("123456789012"));
        Assert.False(member.IsIeOrigin);
    }

    [Fact]
    public void Ssn_ExtractedFromNM1IL_NotFromRefOF()
    {
        var member = ParseSingleMember(configureMember: m => m.WithSsn("987654321"));
        Assert.Equal("987654321", member.Demographics.Ssn);
    }

    [Fact]
    public void Name_Extracted()
    {
        var member = ParseSingleMember(configureMember: m => m.WithName("SMITH", "JANE", "A"));
        Assert.Equal("SMITH", member.Demographics.LastName);
        Assert.Equal("JANE", member.Demographics.FirstName);
        Assert.Equal("A", member.Demographics.MiddleName);
    }

    [Fact]
    public void Demographics_DobGenderRace_Extracted()
    {
        var member = ParseSingleMember(configureMember: m =>
            m.WithDob("19900301").WithGender("F").WithRace("B"));
        Assert.Equal("19900301", member.Demographics.DateOfBirth);
        Assert.Equal("F", member.Demographics.Gender);
        Assert.Contains("B", member.Demographics.RaceCodes);
    }

    [Fact]
    public void MultipleRaceCodes_SplitOnRepetitionSeparator()
    {
        var member = ParseSingleMember(configureMember: m => m.WithRace("B^H"));
        Assert.Equal(2, member.Demographics.RaceCodes.Count);
        Assert.Equal("B", member.Demographics.RaceCodes[0]);
        Assert.Equal("H", member.Demographics.RaceCodes[1]);
    }

    [Fact]
    public void Address_Extracted()
    {
        var member = ParseSingleMember(configureMember: m =>
            m.WithAddress("456 OAK AVE", "CLEVELAND", "OH", "44101"));
        Assert.Equal("456 OAK AVE", member.Demographics.Address!.Line1);
        Assert.Equal("CLEVELAND", member.Demographics.Address.City);
        Assert.Equal("OH", member.Demographics.Address.State);
        Assert.Equal("44101", member.Demographics.Address.Zip);
        Assert.False(member.Demographics.Address.IsOdmPlaceholder);
    }

    [Fact]
    public void OdmPlaceholderAddress_Detected()
    {
        var member = ParseSingleMember(configureMember: m => m.WithOdmPlaceholderAddress());
        Assert.True(member.Demographics.Address!.IsOdmPlaceholder);
    }

    [Fact]
    public void MaintenanceAction_Add_Resolved()
    {
        var member = ParseSingleMember(configureMember: m => m.WithMaintenanceType("021"));
        Assert.Equal(MaintenanceAction.Add, member.MaintenanceAction);
    }

    [Fact]
    public void MaintenanceAction_Term_Resolved()
    {
        var member = ParseSingleMember(configureMember: m => m.WithMaintenanceType("024").WithAssignmentReason("1"));
        Assert.Equal(MaintenanceAction.Termination, member.MaintenanceAction);
    }

    [Fact]
    public void AssignmentReason_Description_Looked_Up()
    {
        var member = ParseSingleMember(configureMember: m => m.WithAssignmentReason("28"));
        Assert.NotNull(member.AssignmentReasonDescription);
        Assert.Contains("Auto-enrollment", member.AssignmentReasonDescription!);
    }

    [Fact]
    public void DateOfDeath_ExtractedFromINS12()
    {
        var member = ParseSingleMember(configureMember: m =>
            m.WithAssignmentReason("3").WithDateOfDeath("20250301").WithMaintenanceType("024"));
        Assert.Equal("20250301", member.DateOfDeath);
    }

    [Fact]
    public void CountyCode_Extracted()
    {
        var member = ParseSingleMember();
        Assert.Equal("25", member.Demographics.CountyCode);
    }
}
