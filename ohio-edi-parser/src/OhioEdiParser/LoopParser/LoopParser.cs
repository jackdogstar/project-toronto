using OhioEdiParser.LoopParser.Models;

namespace OhioEdiParser.LoopParser;

/// <summary>
/// Builds the Ohio 834 loop hierarchy from a flat list of body segments (between ST and SE).
/// Uses a hardcoded state machine based on the 834 TR3 loop triggers.
/// </summary>
public static class Ohio834LoopParser
{
    private static readonly HashSet<string> ResponsiblePersonQualifiers = new() { "S1", "LR", "E1", "QD" };

    public static EdiLoop Parse(IReadOnlyList<EdiSegment> bodySegments)
    {
        var root = new EdiLoop { LoopId = "ROOT" };
        var header = new EdiLoop { LoopId = "HEADER" };
        root.Children.Add(header);

        EdiLoop? current1000A = null;
        EdiLoop? current1000B = null;
        EdiLoop? current2000 = null;
        EdiLoop? current2100 = null; // 2100A, 2100B, or 2100G
        EdiLoop? current2300 = null;
        EdiLoop? current2310 = null;
        EdiLoop? current2320 = null;
        EdiLoop? current2330 = null;
        EdiLoop? current2700 = null;
        EdiLoop? current2710 = null;

        bool in2300 = false;
        bool pastAllCoverages = false; // tracks whether we've seen reporting loops

        foreach (var segment in bodySegments)
        {
            switch (segment.SegmentId)
            {
                case "N1" when current2000 == null:
                {
                    // 1000A or 1000B
                    var qualifier = segment.GetElement(0);
                    if (qualifier == "P5")
                    {
                        current1000A = new EdiLoop { LoopId = "1000A" };
                        current1000A.Segments.Add(segment);
                        root.Children.Add(current1000A);
                    }
                    else if (qualifier == "IN")
                    {
                        current1000B = new EdiLoop { LoopId = "1000B" };
                        current1000B.Segments.Add(segment);
                        root.Children.Add(current1000B);
                    }
                    else
                    {
                        AddToCurrentContext(header, segment);
                    }
                    break;
                }

                case "INS":
                {
                    // Start new Loop 2000 (member)
                    CloseCurrentMember(ref current2300, ref current2310, ref current2320,
                        ref current2330, ref current2100, ref current2700, ref current2710);
                    in2300 = false;
                    pastAllCoverages = false;

                    current2000 = new EdiLoop { LoopId = "2000" };
                    current2000.Segments.Add(segment);
                    root.Children.Add(current2000);
                    break;
                }

                case "NM1" when current2000 != null:
                {
                    var qualifier = segment.GetElement(0);

                    if (qualifier == "IL")
                    {
                        // Loop 2100A — Member Name
                        CloseSubLoops(ref current2300, ref current2310, ref current2320,
                            ref current2330, ref current2100, ref current2700, ref current2710);
                        in2300 = false;

                        current2100 = new EdiLoop { LoopId = "2100A" };
                        current2100.Segments.Add(segment);
                        current2000.Children.Add(current2100);
                    }
                    else if (qualifier == "70")
                    {
                        // Loop 2100B — Incorrect Member Name
                        current2100 = new EdiLoop { LoopId = "2100B" };
                        current2100.Segments.Add(segment);
                        current2000.Children.Add(current2100);
                    }
                    else if (ResponsiblePersonQualifiers.Contains(qualifier))
                    {
                        // Loop 2100G — Responsible Person
                        current2100 = new EdiLoop { LoopId = "2100G" };
                        current2100.Segments.Add(segment);
                        current2000.Children.Add(current2100);
                    }
                    else if (qualifier == "IN" && current2320 != null)
                    {
                        // Loop 2330 — COB Related Entity (within 2320)
                        current2330 = new EdiLoop { LoopId = "2330" };
                        current2330.Segments.Add(segment);
                        current2320.Children.Add(current2330);
                    }
                    else if (current2310 != null)
                    {
                        current2310.Segments.Add(segment);
                    }
                    else if (current2100 != null)
                    {
                        current2100.Segments.Add(segment);
                    }
                    else
                    {
                        current2000.Segments.Add(segment);
                    }
                    break;
                }

                case "HD" when current2000 != null:
                {
                    // Loop 2300 — Health Coverage
                    current2310 = null;
                    current2100 = null;
                    in2300 = true;

                    current2300 = new EdiLoop { LoopId = "2300" };
                    current2300.Segments.Add(segment);
                    current2000.Children.Add(current2300);
                    break;
                }

                case "LX" when current2000 != null:
                {
                    if (in2300 && current2300 != null && !pastAllCoverages)
                    {
                        // Loop 2310 — Provider Info (within 2300)
                        current2310 = new EdiLoop { LoopId = "2310" };
                        current2310.Segments.Add(segment);
                        current2300.Children.Add(current2310);
                    }
                    else
                    {
                        // Loop 2700 — Reporting Category
                        in2300 = false;
                        current2300 = null;
                        current2310 = null;
                        pastAllCoverages = true;

                        current2700 = new EdiLoop { LoopId = "2700" };
                        current2700.Segments.Add(segment);
                        current2000.Children.Add(current2700);
                    }
                    break;
                }

                case "COB" when current2000 != null:
                {
                    // Loop 2320 — Coordination of Benefits
                    in2300 = false;
                    current2300 = null;
                    current2310 = null;
                    current2330 = null;

                    current2320 = new EdiLoop { LoopId = "2320" };
                    current2320.Segments.Add(segment);
                    current2000.Children.Add(current2320);
                    break;
                }

                case "N1" when current2000 != null && current2700 != null:
                {
                    // Loop 2710 within 2700
                    current2710 = new EdiLoop { LoopId = "2710" };
                    current2710.Segments.Add(segment);
                    current2700.Children.Add(current2710);
                    break;
                }

                default:
                {
                    // Add segment to the most specific open context
                    if (current2710 != null)
                        current2710.Segments.Add(segment);
                    else if (current2700 != null)
                        current2700.Segments.Add(segment);
                    else if (current2330 != null)
                        current2330.Segments.Add(segment);
                    else if (current2320 != null)
                        current2320.Segments.Add(segment);
                    else if (current2310 != null)
                        current2310.Segments.Add(segment);
                    else if (current2300 != null)
                        current2300.Segments.Add(segment);
                    else if (current2100 != null)
                        current2100.Segments.Add(segment);
                    else if (current2000 != null)
                        current2000.Segments.Add(segment);
                    else if (current1000B != null && segment.SegmentId is "N3" or "N4" or "PER")
                        current1000B.Segments.Add(segment);
                    else if (current1000A != null && segment.SegmentId is "N3" or "N4" or "PER")
                        current1000A.Segments.Add(segment);
                    else
                        header.Segments.Add(segment);
                    break;
                }
            }
        }

        return root;
    }

    private static void CloseCurrentMember(
        ref EdiLoop? current2300, ref EdiLoop? current2310,
        ref EdiLoop? current2320, ref EdiLoop? current2330,
        ref EdiLoop? current2100, ref EdiLoop? current2700, ref EdiLoop? current2710)
    {
        current2300 = null;
        current2310 = null;
        current2320 = null;
        current2330 = null;
        current2100 = null;
        current2700 = null;
        current2710 = null;
    }

    private static void CloseSubLoops(
        ref EdiLoop? current2300, ref EdiLoop? current2310,
        ref EdiLoop? current2320, ref EdiLoop? current2330,
        ref EdiLoop? current2100, ref EdiLoop? current2700, ref EdiLoop? current2710)
    {
        current2300 = null;
        current2310 = null;
        current2320 = null;
        current2330 = null;
        current2100 = null;
        current2700 = null;
        current2710 = null;
    }

    private static void AddToCurrentContext(EdiLoop fallback, EdiSegment segment)
    {
        fallback.Segments.Add(segment);
    }
}
