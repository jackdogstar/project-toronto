using OhioEdiParser.Models;
using OhioEdiParser.Tests.TestData.Builders;

namespace OhioEdiParser.Tests.Extraction;

public class TransactionExtractorTests
{
    private readonly Ohio834Parser _parser = new();

    [Fact]
    public void ExtractHeader_ChangesFile_FileTypeIsChanges()
    {
        var edi = EdiBuilder.Create()
            .AsChangesFile()
            .AddMember(m => m.WithMaintenanceType("021"))
            .Build();

        var result = _parser.Parse(edi);
        Assert.Equal(OhioFileType.Changes, result.Transactions[0].Header.FileType);
    }

    [Fact]
    public void ExtractHeader_FullFile_FileTypeIsFull()
    {
        var edi = EdiBuilder.Create()
            .AsFullFile()
            .AddMember(m => m.WithMaintenanceType("030"))
            .Build();

        var result = _parser.Parse(edi);
        Assert.Equal(OhioFileType.Full, result.Transactions[0].Header.FileType);
    }

    [Fact]
    public void ExtractHeader_ProviderId_Extracted()
    {
        var edi = EdiBuilder.Create()
            .WithProviderId("9876543")
            .AddMember(m => { })
            .Build();

        var result = _parser.Parse(edi);
        Assert.Equal("9876543", result.Transactions[0].Header.ProviderId);
    }

    [Fact]
    public void ExtractHeader_SponsorAndMce_Extracted()
    {
        var edi = EdiBuilder.Create()
            .AddMember(m => { })
            .Build();

        var header = _parser.Parse(edi).Transactions[0].Header;
        Assert.Equal("OMES", header.SponsorName);
        Assert.Equal("311334825", header.SponsorTaxId);
        Assert.Equal("CareSource", header.MceName);
        Assert.Equal("311764600", header.MceTaxId);
    }

    [Fact]
    public void ExtractHeader_InterchangeInfo_Extracted()
    {
        var edi = EdiBuilder.Create()
            .WithReceiverId("0003150")
            .AddMember(m => { })
            .Build();

        var result = _parser.Parse(edi);
        Assert.Equal("MMISODJFS", result.Interchange.SenderId);
        Assert.Equal("0003150", result.Interchange.ReceiverId);
    }
}
