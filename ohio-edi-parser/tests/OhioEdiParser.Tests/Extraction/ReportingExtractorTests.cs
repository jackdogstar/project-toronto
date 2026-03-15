using OhioEdiParser.Tests.TestData.Builders;

namespace OhioEdiParser.Tests.Extraction;

public class ReportingExtractorTests
{
    private readonly Ohio834Parser _parser = new();

    [Fact]
    public void LivingArrangement_Extracted()
    {
        var edi = EdiBuilder.Create().AsChangesFile()
            .AddMember(m => m
                .AddCob("P", "1") // COB to break out of 2300 context
                .AddReportingCategory("LIVING ARRANGEMENT", "LU", "01"))
            .Build();

        var member = _parser.Parse(edi).Transactions[0].Members[0];
        Assert.Single(member.ReportingCategories);
        Assert.Equal("LIVING ARRANGEMENT", member.ReportingCategories[0].CategoryType);
        Assert.Equal("LU", member.ReportingCategories[0].RefQualifier);
        Assert.Equal("01", member.ReportingCategories[0].RefValue);
        Assert.Equal("Independent (Home/Apart/Trlr)", member.ReportingCategories[0].RefDescription);
    }

    [Fact]
    public void Pregnancy_Extracted()
    {
        var edi = EdiBuilder.Create().AsChangesFile()
            .AddMember(m => m
                .AddCob("P", "1")
                .AddReportingCategory("PREGNANT", "ZZ", "ESTIMATED DUE DATE"))
            .Build();

        var member = _parser.Parse(edi).Transactions[0].Members[0];
        Assert.Single(member.ReportingCategories);
        Assert.Equal("PREGNANT", member.ReportingCategories[0].CategoryType);
        Assert.Equal("ESTIMATED DUE DATE", member.ReportingCategories[0].RefValue);
    }

    [Fact]
    public void DateRange_Parsed()
    {
        var edi = EdiBuilder.Create().AsChangesFile()
            .AddMember(m => m
                .AddCob("P", "1")
                .AddReportingCategory("LIVING ARRANGEMENT", "LU", "01", "RD8", "20250101-20251231"))
            .Build();

        var member = _parser.Parse(edi).Transactions[0].Members[0];
        var rc = member.ReportingCategories[0];
        Assert.Null(rc.DateValue);
        Assert.Equal("20250101", rc.DateRangeStart);
        Assert.Equal("20251231", rc.DateRangeEnd);
    }
}
