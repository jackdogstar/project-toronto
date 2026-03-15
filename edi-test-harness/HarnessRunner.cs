using EdiTestHarness.Reporting;

namespace EdiTestHarness;

public class HarnessRunner
{
    private readonly IEdiParser _parser;
    private readonly bool _verbose;

    public HarnessRunner(IEdiParser parser, bool verbose)
    {
        _parser = parser;
        _verbose = verbose;
    }

    public int Run(string directory)
    {
        var ediFiles = Directory.GetFiles(directory, "*.edi")
            .OrderBy(f => f)
            .ToList();

        if (ediFiles.Count == 0)
        {
            Console.WriteLine($"No .edi files found in: {directory}");
            return 1;
        }

        ConsoleReporter.PrintHeader(_parser.ParserName, directory, ediFiles.Count);

        var results = new List<HarnessParseResult>();

        foreach (var filePath in ediFiles)
        {
            var fileName = Path.GetFileName(filePath);
            var content = File.ReadAllText(filePath);

            var result = _parser.Parse(content, fileName);
            results.Add(result);

            ConsoleReporter.PrintFileResult(result, _verbose);
        }

        ConsoleReporter.PrintSummary(results);

        // Write JSON result files
        var resultsDir = JsonReporter.WriteResults(directory, _parser.ParserName, results);
        Console.WriteLine($"  Results written to: {resultsDir}");
        Console.WriteLine();

        // Return non-zero if any files failed to parse
        return results.Any(r => !r.Success) ? 1 : 0;
    }
}
