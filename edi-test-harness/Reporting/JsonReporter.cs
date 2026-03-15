using System.Text.Json;
using System.Text.Json.Serialization;

namespace EdiTestHarness.Reporting;

public static class JsonReporter
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters = { new TimeSpanConverter() }
    };

    /// <summary>
    /// Writes a JSON result file for each parsed EDI file, plus a summary file.
    /// Files are written to a results/ folder inside the test file directory.
    /// </summary>
    public static string WriteResults(string testFileDirectory, string parserName, List<HarnessParseResult> results)
    {
        var resultsDir = Path.Combine(testFileDirectory, "results");
        Directory.CreateDirectory(resultsDir);

        // Write individual result files
        foreach (var result in results)
        {
            var baseName = Path.GetFileNameWithoutExtension(result.FileName);
            var resultPath = Path.Combine(resultsDir, $"{baseName}_result.json");
            var json = JsonSerializer.Serialize(result, JsonOptions);
            File.WriteAllText(resultPath, json);
        }

        // Write summary file
        var summary = BuildSummary(parserName, results);
        var summaryPath = Path.Combine(resultsDir, "summary.json");
        var summaryJson = JsonSerializer.Serialize(summary, JsonOptions);
        File.WriteAllText(summaryPath, summaryJson);

        return resultsDir;
    }

    private static object BuildSummary(string parserName, List<HarnessParseResult> results)
    {
        var totalMembers = results
            .Where(r => r.Success)
            .SelectMany(r => r.Transactions)
            .Sum(t => t.Members.Count);

        var totalCoverages = results
            .Where(r => r.Success)
            .SelectMany(r => r.Transactions)
            .SelectMany(t => t.Members)
            .Sum(m => m.CoverageCount);

        var membersWithErrors = results
            .Where(r => r.Success)
            .SelectMany(r => r.Transactions)
            .SelectMany(t => t.Members)
            .Count(m => m.HasCriticalErrors);

        return new
        {
            Parser = parserName,
            RunTimestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
            TotalFiles = results.Count,
            FilesParsed = results.Count(r => r.Success),
            FilesFailed = results.Count(r => !r.Success),
            TotalMembers = totalMembers,
            MembersWithCriticalErrors = membersWithErrors,
            MembersClean = totalMembers - membersWithErrors,
            TotalCoverages = totalCoverages,
            Validation = new
            {
                Critical = results.Sum(r => r.ValidationIssues.Count(i => i.Severity == "Critical")),
                Warning = results.Sum(r => r.ValidationIssues.Count(i => i.Severity == "Warning")),
                Informational = results.Sum(r => r.ValidationIssues.Count(i => i.Severity == "Informational"))
            },
            TotalParseTimeMs = results.Aggregate(TimeSpan.Zero, (sum, r) => sum + r.Duration).TotalMilliseconds,
            Files = results.Select(r => new
            {
                r.FileName,
                r.Success,
                r.ErrorMessage,
                ParseTimeMs = r.Duration.TotalMilliseconds,
                MemberCount = r.Success
                    ? r.Transactions.Sum(t => t.Members.Count)
                    : 0,
                CoverageCount = r.Success
                    ? r.Transactions.SelectMany(t => t.Members).Sum(m => m.CoverageCount)
                    : 0,
                CriticalIssues = r.ValidationIssues.Count(i => i.Severity == "Critical"),
                WarningIssues = r.ValidationIssues.Count(i => i.Severity == "Warning"),
                InfoIssues = r.ValidationIssues.Count(i => i.Severity == "Informational")
            })
        };
    }

    private class TimeSpanConverter : JsonConverter<TimeSpan>
    {
        public override TimeSpan Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            return TimeSpan.FromMilliseconds(reader.GetDouble());
        }

        public override void Write(Utf8JsonWriter writer, TimeSpan value, JsonSerializerOptions options)
        {
            writer.WriteNumberValue(Math.Round(value.TotalMilliseconds, 1));
        }
    }
}
