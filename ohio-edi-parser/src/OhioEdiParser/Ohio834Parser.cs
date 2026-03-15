using OhioEdiParser.Envelope;
using OhioEdiParser.Extraction;
using OhioEdiParser.LoopParser;
using OhioEdiParser.Models;
using OhioEdiParser.Tokenizer;
using OhioEdiParser.Validation;

namespace OhioEdiParser;

public class Ohio834Parser
{
    public OhioParseResult Parse(string rawEdiContent)
    {
        // 1. Detect delimiters from ISA
        var delimiters = DelimiterDetector.Detect(rawEdiContent);

        // 2. Tokenize into segments
        var segments = EdiTokenizer.Tokenize(rawEdiContent, delimiters);

        // 3. Parse envelope (ISA/IEA, GS/GE, ST/SE)
        var (interchange, transactionSets) = EnvelopeParser.Parse(segments);

        // 4. Process each transaction set
        var transactions = new List<OhioTransaction>();

        foreach (var txSet in transactionSets)
        {
            // 4a. Build loop hierarchy
            var root = Ohio834LoopParser.Parse(txSet.BodySegments);

            // 4b. Extract header
            var headerLoop = root.FindChild("HEADER");
            var loop1000A = root.FindChild("1000A");
            var loop1000B = root.FindChild("1000B");

            var txContext = OhioTransactionExtractor.ExtractHeader(
                headerLoop!, loop1000A, loop1000B);

            // 4c. Extract members
            var members = root.FindChildren("2000")
                .Select(loop2000 => OhioMemberExtractor.ExtractMember(
                    loop2000, txContext, delimiters.RepetitionSeparator))
                .ToList();

            transactions.Add(new OhioTransaction
            {
                Header = txContext,
                Members = members
            });
        }

        // 5. Build result and validate
        var result = new OhioParseResult
        {
            Transactions = transactions,
            Interchange = interchange,
            Validation = null!  // set below
        };

        var validation = OhioValidator.Validate(result);

        // Re-create with validation (since init-only)
        return new OhioParseResult
        {
            Transactions = transactions,
            Interchange = interchange,
            Validation = validation
        };
    }
}
