namespace EdiTestHarness.Reporting;

/// <summary>
/// Writes parse results to the console with color-coded output.
/// </summary>
public static class ConsoleReporter
{
    public static void PrintHeader(string parserName, string directory, int fileCount)
    {
        Console.WriteLine();
        Console.WriteLine(new string('=', 80));
        Console.WriteLine($"  EDI Test Harness — Parser: {parserName.ToUpperInvariant()}");
        Console.WriteLine($"  Directory: {directory}");
        Console.WriteLine($"  Files: {fileCount}");
        Console.WriteLine(new string('=', 80));
        Console.WriteLine();
    }

    public static void PrintFileResult(HarnessParseResult result, bool verbose)
    {
        Console.WriteLine(new string('-', 80));
        Console.Write($"  File: {result.FileName}  ");

        if (result.Success)
        {
            WriteColored("[PARSED]", ConsoleColor.Green);
            Console.WriteLine($"  ({result.Duration.TotalMilliseconds:F1}ms)");
        }
        else
        {
            WriteColored("[ERROR]", ConsoleColor.Red);
            Console.WriteLine($"  ({result.Duration.TotalMilliseconds:F1}ms)");
            Console.WriteLine($"    Error: {result.ErrorMessage}");
            Console.WriteLine();
            return;
        }

        // Envelope
        Console.WriteLine($"    Sender: {result.SenderId}  |  Receiver: {result.ReceiverId}  |  Control#: {result.ControlNumber}");

        // Transactions
        foreach (var tx in result.Transactions)
        {
            Console.WriteLine($"    Transaction: FileType={tx.FileType}  Provider={tx.ProviderId}  EffDate={tx.EffectiveDate}");
            Console.WriteLine($"    Members: {tx.Members.Count}");

            if (verbose)
            {
                foreach (var member in tx.Members)
                {
                    PrintMember(member);
                }
            }
            else
            {
                // Summary view
                var withErrors = tx.Members.Count(m => m.HasCriticalErrors);
                var clean = tx.Members.Count - withErrors;
                Console.Write($"      Clean: ");
                WriteColored(clean.ToString(), ConsoleColor.Green);
                if (withErrors > 0)
                {
                    Console.Write("  |  Critical errors: ");
                    WriteColored(withErrors.ToString(), ConsoleColor.Red);
                }
                Console.WriteLine();

                // Maintenance type breakdown
                var maintGroups = tx.Members
                    .GroupBy(m => m.MaintenanceAction)
                    .OrderBy(g => g.Key);
                Console.Write("      Actions: ");
                Console.WriteLine(string.Join(", ", maintGroups.Select(g => $"{g.Key}={g.Count()}")));

                // Coverage summary
                var totalCoverages = tx.Members.Sum(m => m.CoverageCount);
                Console.WriteLine($"      Total coverages: {totalCoverages}");
            }
        }

        // Validation summary
        if (result.ValidationIssues.Count > 0)
        {
            Console.WriteLine();
            var critical = result.ValidationIssues.Count(i => i.Severity == "Critical");
            var warnings = result.ValidationIssues.Count(i => i.Severity == "Warning");
            var info = result.ValidationIssues.Count(i => i.Severity == "Informational");

            Console.Write("    Validation: ");
            if (critical > 0) { WriteColored($"{critical} critical", ConsoleColor.Red); Console.Write("  "); }
            if (warnings > 0) { WriteColored($"{warnings} warnings", ConsoleColor.Yellow); Console.Write("  "); }
            if (info > 0) { WriteColored($"{info} info", ConsoleColor.Cyan); }
            Console.WriteLine();

            if (verbose)
            {
                foreach (var issue in result.ValidationIssues)
                {
                    var color = issue.Severity switch
                    {
                        "Critical" => ConsoleColor.Red,
                        "Warning" => ConsoleColor.Yellow,
                        _ => ConsoleColor.Cyan
                    };
                    Console.Write($"      [{issue.RuleCode}] ");
                    WriteColored(issue.Severity, color);
                    Console.Write($": {issue.Message}");
                    if (issue.MemberId != null) Console.Write($"  (ID: {issue.MemberId})");
                    Console.WriteLine();
                }
            }
        }
        else
        {
            Console.Write("    Validation: ");
            WriteColored("No issues", ConsoleColor.Green);
            Console.WriteLine();
        }

        Console.WriteLine();
    }

    public static void PrintMember(HarnessMember member)
    {
        var errorFlag = member.HasCriticalErrors ? " [CRITICAL ERRORS]" : "";
        Console.Write($"      {member.LastName}, {member.FirstName}");
        if (member.MiddleName != null) Console.Write($" {member.MiddleName}");
        Console.Write($"  |  ID: {member.MemberId}  |  {member.MaintenanceAction}");
        if (member.HasCriticalErrors) WriteColored(errorFlag, ConsoleColor.Red);
        Console.WriteLine();

        Console.WriteLine($"        DOB: {member.DateOfBirth}  Gender: {member.Gender}  SSN: {MaskSsn(member.Ssn)}");
        Console.WriteLine($"        Location: {member.City}, {member.State} {member.Zip}");
        Console.WriteLine($"        Coverages: {member.CoverageCount}");

        foreach (var cov in member.Coverages)
        {
            Console.WriteLine($"          {cov.InsuranceLine} / {cov.PlanDescription}  |  {cov.BeginDate} - {cov.EndDate ?? "(open)"}");
        }

        // Extended fields (non-null only)
        var extras = member.ExtendedFields
            .Where(kv => kv.Value != null && kv.Value != "0" && kv.Value != "False" && kv.Value != "")
            .ToList();
        if (extras.Count > 0)
        {
            Console.WriteLine($"        Extended: {string.Join(", ", extras.Select(kv => $"{kv.Key}={kv.Value}"))}");
        }
    }

    public static void PrintSummary(List<HarnessParseResult> results)
    {
        Console.WriteLine(new string('=', 80));
        Console.WriteLine("  SUMMARY");
        Console.WriteLine(new string('=', 80));

        var totalFiles = results.Count;
        var parsed = results.Count(r => r.Success);
        var failed = totalFiles - parsed;
        var totalMembers = results.Where(r => r.Success).SelectMany(r => r.Transactions).Sum(t => t.Members.Count);
        var totalCoverages = results.Where(r => r.Success)
            .SelectMany(r => r.Transactions)
            .SelectMany(t => t.Members)
            .Sum(m => m.CoverageCount);
        var totalCritical = results.Sum(r => r.ValidationIssues.Count(i => i.Severity == "Critical"));
        var totalWarnings = results.Sum(r => r.ValidationIssues.Count(i => i.Severity == "Warning"));
        var totalInfo = results.Sum(r => r.ValidationIssues.Count(i => i.Severity == "Informational"));
        var totalDuration = results.Aggregate(TimeSpan.Zero, (sum, r) => sum + r.Duration);

        Console.Write($"  Files parsed: ");
        WriteColored(parsed.ToString(), ConsoleColor.Green);
        if (failed > 0)
        {
            Console.Write($"  |  Files failed: ");
            WriteColored(failed.ToString(), ConsoleColor.Red);
        }
        Console.WriteLine($"  |  Total: {totalFiles}");

        Console.WriteLine($"  Members: {totalMembers}  |  Coverages: {totalCoverages}");
        Console.Write($"  Validation: ");
        WriteColored($"{totalCritical} critical", totalCritical > 0 ? ConsoleColor.Red : ConsoleColor.Green);
        Console.Write("  ");
        WriteColored($"{totalWarnings} warnings", totalWarnings > 0 ? ConsoleColor.Yellow : ConsoleColor.Green);
        Console.Write("  ");
        WriteColored($"{totalInfo} info", ConsoleColor.Cyan);
        Console.WriteLine();
        Console.WriteLine($"  Total parse time: {totalDuration.TotalMilliseconds:F1}ms");
        Console.WriteLine();
    }

    private static string MaskSsn(string? ssn)
    {
        if (string.IsNullOrEmpty(ssn) || ssn.Length < 4) return ssn ?? "(none)";
        return "***-**-" + ssn[^4..];
    }

    private static void WriteColored(string text, ConsoleColor color)
    {
        var prev = Console.ForegroundColor;
        Console.ForegroundColor = color;
        Console.Write(text);
        Console.ForegroundColor = prev;
    }
}
