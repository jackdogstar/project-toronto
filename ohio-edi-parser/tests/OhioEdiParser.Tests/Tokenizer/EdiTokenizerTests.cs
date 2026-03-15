using OhioEdiParser.Envelope.Models;
using OhioEdiParser.Tokenizer;

namespace OhioEdiParser.Tests.Tokenizer;

public class EdiTokenizerTests
{
    private static readonly DetectedDelimiters StandardDelimiters =
        new('*', ':', '~', '^');

    [Fact]
    public void Tokenize_SimpleSegments_ParsesCorrectly()
    {
        var edi = "ISA*00*test~GS*HP*sender~";
        var segments = EdiTokenizer.Tokenize(edi, StandardDelimiters);

        Assert.Equal(2, segments.Count);
        Assert.Equal("ISA", segments[0].SegmentId);
        Assert.Equal("00", segments[0].GetElement(0));
        Assert.Equal("test", segments[0].GetElement(1));
        Assert.Equal("GS", segments[1].SegmentId);
    }

    [Fact]
    public void Tokenize_SegmentNumbersAreSequential()
    {
        var edi = "SEG1*a~SEG2*b~SEG3*c~";
        var segments = EdiTokenizer.Tokenize(edi, StandardDelimiters);

        Assert.Equal(0, segments[0].SegmentNumber);
        Assert.Equal(1, segments[1].SegmentNumber);
        Assert.Equal(2, segments[2].SegmentNumber);
    }

    [Fact]
    public void Tokenize_EmptyElements_PreservedAsEmptyStrings()
    {
        var edi = "REF*0F**value~";
        var segments = EdiTokenizer.Tokenize(edi, StandardDelimiters);

        Assert.Equal("0F", segments[0].GetElement(0));
        Assert.Equal("", segments[0].GetElement(1));
        Assert.Equal("value", segments[0].GetElement(2));
    }

    [Fact]
    public void Tokenize_HandlesNewlinesBetweenSegments()
    {
        var edi = "SEG1*a~\r\nSEG2*b~\nSEG3*c~";
        var segments = EdiTokenizer.Tokenize(edi, StandardDelimiters);

        Assert.Equal(3, segments.Count);
        Assert.Equal("SEG2", segments[1].SegmentId);
    }

    [Fact]
    public void Tokenize_TrailingTerminator_NoExtraSegment()
    {
        var edi = "SEG1*a~SEG2*b~";
        var segments = EdiTokenizer.Tokenize(edi, StandardDelimiters);
        Assert.Equal(2, segments.Count);
    }

    [Fact]
    public void Tokenize_SegmentWithNoElements_HasEmptyArray()
    {
        var edi = "SE~";
        var segments = EdiTokenizer.Tokenize(edi, StandardDelimiters);

        Assert.Single(segments);
        Assert.Equal("SE", segments[0].SegmentId);
        Assert.Empty(segments[0].Elements);
    }

    [Fact]
    public void GetElement_OutOfRange_ReturnsEmpty()
    {
        var edi = "REF*0F~";
        var segments = EdiTokenizer.Tokenize(edi, StandardDelimiters);

        Assert.Equal("0F", segments[0].GetElement(0));
        Assert.Equal("", segments[0].GetElement(1)); // out of range
        Assert.Equal("", segments[0].GetElement(99)); // way out of range
    }
}
