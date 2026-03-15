using OhioEdiParser.Envelope;
using OhioEdiParser.Envelope.Models;
using OhioEdiParser.LoopParser.Models;
using OhioEdiParser.Tokenizer;

namespace OhioEdiParser.Tests.Envelope;

public class EnvelopeParserTests
{
    private static readonly DetectedDelimiters Delimiters = new('*', ':', '~', '^');

    private static IReadOnlyList<EdiSegment> Tokenize(string edi) =>
        EdiTokenizer.Tokenize(edi, Delimiters);

    [Fact]
    public void Parse_SingleTransaction_ExtractsInterchangeHeader()
    {
        var edi = BuildSingleTransactionEdi("BGN*00*REF001~INS*Y*18*021*28~");
        var segments = Tokenize(edi);
        var (interchange, _) = EnvelopeParser.Parse(segments);

        Assert.Equal("MMISODJFS", interchange.SenderId);
        Assert.Equal("0003150", interchange.ReceiverId);
        Assert.Equal("000000001", interchange.ControlNumber);
    }

    [Fact]
    public void Parse_SingleTransaction_ExtractsBodySegments()
    {
        var edi = BuildSingleTransactionEdi("BGN*00*REF001~INS*Y*18*021*28~");
        var segments = Tokenize(edi);
        var (_, txSets) = EnvelopeParser.Parse(segments);

        Assert.Single(txSets);
        Assert.Equal("0001", txSets[0].TransactionSetControlNumber);
        Assert.Equal(2, txSets[0].BodySegments.Count);
        Assert.Equal("BGN", txSets[0].BodySegments[0].SegmentId);
        Assert.Equal("INS", txSets[0].BodySegments[1].SegmentId);
    }

    [Fact]
    public void Parse_MultipleTransactionSets_ReturnsAll()
    {
        var edi =
            "ISA*00*          *00*          *ZZ*MMISODJFS      *ZZ*0003150        *250611*0800*^*00501*000000001*0*P*:~" +
            "GS*HP*MMISODJFS*0003150*20250611*0800*1*X*005010X220A1~" +
            "ST*834*0001~BGN*00*REF001~SE*2*0001~" +
            "ST*834*0002~BGN*00*REF002~SE*2*0002~" +
            "GE*2*1~" +
            "IEA*1*000000001~";

        var segments = Tokenize(edi);
        var (_, txSets) = EnvelopeParser.Parse(segments);

        Assert.Equal(2, txSets.Count);
        Assert.Equal("0001", txSets[0].TransactionSetControlNumber);
        Assert.Equal("0002", txSets[1].TransactionSetControlNumber);
    }

    [Fact]
    public void Parse_FunctionalGroupHeader_Extracted()
    {
        var edi = BuildSingleTransactionEdi("BGN*00*REF001~");
        var segments = Tokenize(edi);
        var (_, txSets) = EnvelopeParser.Parse(segments);

        Assert.Equal("HP", txSets[0].FunctionalGroup.FunctionalIdCode);
        Assert.Equal("MMISODJFS", txSets[0].FunctionalGroup.ApplicationSender);
        Assert.Equal("0003150", txSets[0].FunctionalGroup.ApplicationReceiver);
    }

    [Fact]
    public void Parse_NoIsaSegment_Throws()
    {
        var segments = new List<EdiSegment>
        {
            new("GS", new[] { "HP" }, 0)
        };

        Assert.Throws<InvalidOperationException>(() => EnvelopeParser.Parse(segments));
    }

    private static string BuildSingleTransactionEdi(string body)
    {
        return
            "ISA*00*          *00*          *ZZ*MMISODJFS      *ZZ*0003150        *250611*0800*^*00501*000000001*0*P*:~" +
            "GS*HP*MMISODJFS*0003150*20250611*0800*1*X*005010X220A1~" +
            "ST*834*0001~" +
            body +
            "SE*2*0001~" +
            "GE*1*1~" +
            "IEA*1*000000001~";
    }
}
