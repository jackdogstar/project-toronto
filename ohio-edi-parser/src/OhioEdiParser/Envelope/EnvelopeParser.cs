using OhioEdiParser.Envelope.Models;
using OhioEdiParser.LoopParser.Models;

namespace OhioEdiParser.Envelope;

public static class EnvelopeParser
{
    public static (InterchangeHeader Interchange, List<TransactionSetEnvelope> TransactionSets) Parse(
        IReadOnlyList<EdiSegment> segments)
    {
        var interchange = ParseInterchangeHeader(segments);
        var transactionSets = new List<TransactionSetEnvelope>();

        int i = 0;
        // Skip to first GS
        while (i < segments.Count && segments[i].SegmentId != "GS")
            i++;

        while (i < segments.Count && segments[i].SegmentId == "GS")
        {
            var group = ParseFunctionalGroupHeader(segments[i]);
            i++;

            // Parse all ST/SE within this GS/GE
            while (i < segments.Count && segments[i].SegmentId == "ST")
            {
                var stSegment = segments[i];
                var controlNumber = stSegment.GetElement(1); // ST02
                i++;

                var bodySegments = new List<EdiSegment>();
                while (i < segments.Count && segments[i].SegmentId != "SE")
                {
                    bodySegments.Add(segments[i]);
                    i++;
                }

                // Skip SE
                if (i < segments.Count && segments[i].SegmentId == "SE")
                    i++;

                transactionSets.Add(new TransactionSetEnvelope
                {
                    Interchange = interchange,
                    FunctionalGroup = group,
                    TransactionSetControlNumber = controlNumber,
                    BodySegments = bodySegments
                });
            }

            // Skip GE
            if (i < segments.Count && segments[i].SegmentId == "GE")
                i++;
        }

        return (interchange, transactionSets);
    }

    private static InterchangeHeader ParseInterchangeHeader(IReadOnlyList<EdiSegment> segments)
    {
        var isa = segments.FirstOrDefault(s => s.SegmentId == "ISA");
        if (isa == null)
            throw new InvalidOperationException("ISA segment not found.");

        return new InterchangeHeader
        {
            SenderId = isa.GetElement(5).Trim(),     // ISA06
            ReceiverId = isa.GetElement(7).Trim(),   // ISA08
            ControlNumber = isa.GetElement(12).Trim(), // ISA13
            Date = isa.GetElement(8).Trim(),          // ISA09
            Time = isa.GetElement(9).Trim()           // ISA10
        };
    }

    private static FunctionalGroupHeader ParseFunctionalGroupHeader(EdiSegment gs)
    {
        return new FunctionalGroupHeader
        {
            FunctionalIdCode = gs.GetElement(0),      // GS01
            ApplicationSender = gs.GetElement(1),     // GS02
            ApplicationReceiver = gs.GetElement(2),   // GS03
            ControlNumber = gs.GetElement(5)          // GS06
        };
    }
}
