using OhioEdiParser.Models;
using OhioEdiParser.Tests.TestData.Builders;

namespace OhioEdiParser.Tests.Integration;

public class FullFileParsingTests
{
    private readonly Ohio834Parser _parser = new();

    [Fact]
    public void FullFile_MinimalMember_ParsesSuccessfully()
    {
        var edi = EdiBuilder.Create()
            .AsFullFile()
            .WithProviderId("1234567")
            .AddMember(m => m
                .WithMaintenanceType("030")
                .WithAssignmentReason("XN")
                .WithMedicaidId("123456789012")
                .WithName("DOE", "JOHN", "M")
                .WithSsn("123456789")
                .WithDob("19800115")
                .WithGender("M")
                .WithRace("C")
                .AddCoverage("030", "HMO", "CFC", "20250101", "20251231", "OHCFCM2580"))
            .Build();

        var result = _parser.Parse(edi);

        Assert.Single(result.Transactions);
        Assert.Single(result.Transactions[0].Members);

        var tx = result.Transactions[0];
        Assert.Equal(OhioFileType.Full, tx.Header.FileType);
        Assert.Equal("1234567", tx.Header.ProviderId);

        var member = tx.Members[0];
        Assert.Equal("123456789012", member.MedicaidId);
        Assert.Equal(MaintenanceAction.Audit, member.MaintenanceAction);
        Assert.Equal("DOE", member.Demographics.LastName);
        Assert.Equal("123456789", member.Demographics.Ssn);
        Assert.Equal("OHCFCM2580", member.Coverages[0].RateCellIndicator);
        Assert.False(member.HasCriticalErrors);
    }

    [Fact]
    public void FullFile_MultipleMembersWithDifferentCoverageTypes()
    {
        var edi = EdiBuilder.Create()
            .AsFullFile()
            .AddMember(m => m
                .WithMaintenanceType("030")
                .WithAssignmentReason("XN")
                .WithName("DOE", "JOHN")
                .AddCoverage("030", "HMO", "CFC", "20250101", "20251231", "OHCFCM2580")
                .AddCoverage("030", "AH", "WVR-A1", "20250101", "20251231"))
            .AddMember(m => m
                .WithMaintenanceType("030")
                .WithAssignmentReason("XN")
                .WithMedicaidId("987654321098")
                .WithName("SMITH", "JANE")
                .AddCoverage("030", "HMO", "ABD", "20250101", "20251231", "OHABDF4560"))
            .Build();

        var result = _parser.Parse(edi);
        Assert.Equal(2, result.Transactions[0].Members.Count);

        var member1 = result.Transactions[0].Members[0];
        Assert.Equal(2, member1.Coverages.Count);
        Assert.Equal("HMO", member1.Coverages[0].InsuranceLineCode);
        Assert.Equal("AH", member1.Coverages[1].InsuranceLineCode);

        var member2 = result.Transactions[0].Members[1];
        Assert.Equal("ABD", member2.Coverages[0].PlanCoverageDesc);
    }
}
