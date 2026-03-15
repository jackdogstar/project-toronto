using OhioEdiParser.Models;
using OhioEdiParser.Tests.TestData.Builders;

namespace OhioEdiParser.Tests.Extraction;

public class CoverageExtractorTests
{
    private readonly Ohio834Parser _parser = new();

    private List<OhioCoverage> ParseCoverages(Action<MemberBuilder> configure)
    {
        var edi = EdiBuilder.Create().AsChangesFile()
            .AddMember(configure)
            .Build();
        return _parser.Parse(edi).Transactions[0].Members[0].Coverages;
    }

    [Fact]
    public void Coverage_BasicFields_Extracted()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("021", "HMO", "CFC", "20250101", "20251231", "OHCFCM2580"));

        Assert.Single(coverages);
        Assert.Equal("021", coverages[0].MaintenanceTypeCode);
        Assert.Equal(MaintenanceAction.Add, coverages[0].MaintenanceAction);
        Assert.Equal("HMO", coverages[0].InsuranceLineCode);
        Assert.Equal("CFC", coverages[0].PlanCoverageDesc);
        Assert.Equal("20250101", coverages[0].BenefitBeginDate);
        Assert.Equal("20251231", coverages[0].BenefitEndDate);
    }

    [Fact]
    public void RateCell_Extracted_FromLoop2300()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("021", "HMO", "CFC", "20250101", "20251231", "OHCFCM2580"));

        Assert.Equal("OHCFCM2580", coverages[0].RateCellIndicator);
        Assert.False(coverages[0].RateCellMissing);
    }

    [Fact]
    public void RateCell_XXXXXXXXXX_MarkedAsMissing()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("021", "HMO", "CFC", "20250101", "20251231", "XXXXXXXXXX"));

        Assert.Null(coverages[0].RateCellIndicator);
        Assert.True(coverages[0].RateCellMissing);
    }

    [Fact]
    public void InsuranceLine_Description_LookedUp()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("021", "HMO", "CFC", "20250101"));

        Assert.NotNull(coverages[0].InsuranceLineDescription);
        Assert.Contains("Health Maintenance Organization", coverages[0].InsuranceLineDescription!);
    }

    [Fact]
    public void PlanCoverageDesc_Description_LookedUp()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("021", "HMO", "ABD", "20250101"));

        Assert.Equal("Aged/Blind/Disabled", coverages[0].PlanCoverageDescription);
    }

    [Fact]
    public void MultipleCoverages_AllExtracted()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("021", "HMO", "CFC", "20250101")
             .AddCoverage("021", "AH", "WVR-A1", "20250101"));

        Assert.Equal(2, coverages.Count);
        Assert.Equal("HMO", coverages[0].InsuranceLineCode);
        Assert.Equal("AH", coverages[1].InsuranceLineCode);
    }

    [Fact]
    public void PatientLiability_ExtractedForMM()
    {
        var coverages = ParseCoverages(m => m.AddCoverageWithPatientLiability("150.00"));

        Assert.Equal(150.00m, coverages[0].PatientLiabilityAmount);
    }

    [Fact]
    public void Provider_ExtractedFromLoop2310()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverageWithProvider("021", "HMO", "CFC", "20250101", "Y2", "CARESOURCE", "1234567"));

        Assert.NotNull(coverages[0].Provider);
        Assert.Equal("Y2", coverages[0].Provider!.EntityTypeQualifier);
        Assert.Equal("CARESOURCE", coverages[0].Provider.Name);
        Assert.Equal("1234567", coverages[0].Provider.Id);
    }

    [Fact]
    public void HD01_Delete_MappedCorrectly()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("002", "AG", "951", "20250101"));

        Assert.Equal(MaintenanceAction.Delete, coverages[0].MaintenanceAction);
    }

    [Fact]
    public void HD01_Reinstate_MappedCorrectly()
    {
        var coverages = ParseCoverages(m =>
            m.AddCoverage("025", "HMO", "CFC", "20250101"));

        Assert.Equal(MaintenanceAction.Reinstate, coverages[0].MaintenanceAction);
    }
}
