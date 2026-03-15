using EdiTestHarness;
using EdiTestHarness.Parsers;

// Usage: dotnet run -- <parser-name> <test-file-directory> [--verbose]
// Example: dotnet run -- ohio ../test-files/Ohio_Test_Files
// Example: dotnet run -- ohio ../test-files/Ohio_Test_Files --verbose

if (args.Length < 2)
{
    Console.WriteLine("EDI Test Harness");
    Console.WriteLine();
    Console.WriteLine("Usage: EdiTestHarness <parser-name> <test-file-directory> [--verbose]");
    Console.WriteLine();
    Console.WriteLine("Available parsers:");
    foreach (var name in ParserRegistry.AvailableParsers)
        Console.WriteLine($"  - {name}");
    Console.WriteLine();
    Console.WriteLine("Options:");
    Console.WriteLine("  --verbose    Show detailed member and validation output");
    Console.WriteLine();
    Console.WriteLine("Examples:");
    Console.WriteLine("  EdiTestHarness ohio ../test-files/Ohio_Test_Files");
    Console.WriteLine("  EdiTestHarness ohio ../test-files/Ohio_Test_Files --verbose");
    return 1;
}

var parserName = args[0];
var directory = args[1];
var verbose = args.Any(a => a.Equals("--verbose", StringComparison.OrdinalIgnoreCase));

// Resolve relative path
if (!Path.IsPathRooted(directory))
    directory = Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, directory));

if (!Directory.Exists(directory))
{
    Console.WriteLine($"Directory not found: {directory}");
    return 1;
}

var parser = ParserRegistry.GetParser(parserName);
if (parser == null)
{
    Console.WriteLine($"Unknown parser: '{parserName}'");
    Console.WriteLine($"Available parsers: {string.Join(", ", ParserRegistry.AvailableParsers)}");
    return 1;
}

var runner = new HarnessRunner(parser, verbose);
return runner.Run(directory);
