using OhioEdiParser.LoopParser.Models;
using OhioEdiParser.Models;

namespace OhioEdiParser.Extraction;

public static class OhioTransactionExtractor
{
    public static TransactionContext ExtractHeader(EdiLoop headerLoop, EdiLoop? loop1000A, EdiLoop? loop1000B)
    {
        var bgn = headerLoop.FindSegment("BGN")
            ?? throw new InvalidOperationException("BGN segment not found in transaction header.");

        var fileTypeCode = bgn.GetElement(7); // BGN08 (0-indexed: element 7)
        var fileType = fileTypeCode switch
        {
            "4" => OhioFileType.Full,
            "2" => OhioFileType.Changes,
            _ => throw new InvalidOperationException($"Unknown BGN08 file type: '{fileTypeCode}'")
        };

        var providerIdRef = headerLoop.FindSegment("REF", 0, "38");
        var effectiveDateDtp = headerLoop.FindSegment("DTP", 0, "007");

        var sponsorN1 = loop1000A?.FindSegment("N1");
        var payerN1 = loop1000B?.FindSegment("N1");

        return new TransactionContext
        {
            FileType = fileType,
            FileReferenceId = bgn.GetElement(1),           // BGN02
            FileEffectiveDate = effectiveDateDtp?.GetElement(2) ?? string.Empty, // DTP03
            ProviderId = providerIdRef?.GetElement(1) ?? string.Empty,           // REF*38 element 02
            SponsorName = sponsorN1?.GetElement(1) ?? string.Empty,              // N1*P5 element 02
            SponsorTaxId = sponsorN1?.GetElement(3) ?? string.Empty,             // N1*P5 element 04
            MceName = payerN1?.GetElement(1) ?? string.Empty,                    // N1*IN element 02
            MceTaxId = payerN1?.GetElement(3) ?? string.Empty                    // N1*IN element 04
        };
    }
}
