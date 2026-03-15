using OhioEdiParser.Tokenizer;

namespace OhioEdiParser.Tests.Tokenizer;

public class DelimiterDetectorTests
{
    // Standard Ohio ISA segment (106 chars): element sep *, sub-element sep :, terminator ~, repetition ^
    // ISA fields: 01(2) 02(10) 03(2) 04(10) 05(2) 06(15) 07(2) 08(15) 09(6) 10(4) 11(1) 12(5) 13(9) 14(1) 15(1) 16(1)
    private const string StandardIsa =
        "ISA*00*          *00*          *ZZ*MMISODJFS      *ZZ*0003150        *250611*0800*^*00501*000000001*0*P*:~";

    [Fact]
    public void Detect_StandardOhioIsa_ReturnsCorrectDelimiters()
    {
        var result = DelimiterDetector.Detect(StandardIsa);

        Assert.Equal('*', result.ElementSeparator);
        Assert.Equal(':', result.SubElementSeparator);
        Assert.Equal('~', result.SegmentTerminator);
        Assert.Equal('^', result.RepetitionSeparator);
    }

    [Fact]
    public void Detect_WithLeadingBom_StillWorks()
    {
        var withBom = "\uFEFF" + StandardIsa;
        var result = DelimiterDetector.Detect(withBom);
        Assert.Equal('*', result.ElementSeparator);
    }

    [Fact]
    public void Detect_WithLeadingWhitespace_StillWorks()
    {
        var withWhitespace = "  \r\n" + StandardIsa;
        var result = DelimiterDetector.Detect(withWhitespace);
        Assert.Equal('~', result.SegmentTerminator);
    }

    [Fact]
    public void Detect_EmptyInput_Throws()
    {
        Assert.Throws<InvalidOperationException>(() => DelimiterDetector.Detect(""));
    }

    [Fact]
    public void Detect_TooShort_Throws()
    {
        Assert.Throws<InvalidOperationException>(() => DelimiterDetector.Detect("ISA*00*short"));
    }

    [Fact]
    public void Detect_NotStartingWithIsa_Throws()
    {
        Assert.Throws<InvalidOperationException>(() => DelimiterDetector.Detect(new string('X', 106)));
    }
}
