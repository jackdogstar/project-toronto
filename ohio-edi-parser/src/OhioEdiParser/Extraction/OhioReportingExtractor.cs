using OhioEdiParser.CodeSets;
using OhioEdiParser.LoopParser.Models;
using OhioEdiParser.Models;

namespace OhioEdiParser.Extraction;

public static class OhioReportingExtractor
{
    public static List<OhioReportingCategory> ExtractReportingCategories(IEnumerable<EdiLoop> loop2700s)
    {
        var categories = new List<OhioReportingCategory>();

        foreach (var loop2700 in loop2700s)
        {
            foreach (var loop2710 in loop2700.FindChildren("2710"))
            {
                var n1 = loop2710.Segments.FirstOrDefault(s => s.SegmentId == "N1");
                var refSeg = loop2710.Segments.FirstOrDefault(s => s.SegmentId == "REF");
                var dtpSeg = loop2710.Segments.FirstOrDefault(s => s.SegmentId == "DTP");

                if (n1 == null || refSeg == null) continue;

                var categoryType = n1.GetElement(1);
                var refQualifier = refSeg.GetElement(0);
                var refValue = refSeg.GetElement(1);

                string? dateValue = null;
                string? dateRangeStart = null;
                string? dateRangeEnd = null;

                if (dtpSeg != null)
                {
                    var dateFormat = dtpSeg.GetElement(1); // DTP02
                    var dateData = dtpSeg.GetElement(2);   // DTP03

                    if (dateFormat == "D8")
                    {
                        dateValue = dateData;
                    }
                    else if (dateFormat == "RD8" && dateData.Contains('-'))
                    {
                        var parts = dateData.Split('-');
                        dateRangeStart = parts[0];
                        dateRangeEnd = parts.Length > 1 ? parts[1] : null;
                    }
                }

                string? refDescription = null;
                if (refQualifier == "LU")
                    refDescription = LivingArrangementCodes.GetDescription(refValue);

                categories.Add(new OhioReportingCategory
                {
                    CategoryType = categoryType,
                    RefQualifier = refQualifier,
                    RefValue = refValue,
                    RefDescription = refDescription,
                    DateValue = dateValue,
                    DateRangeStart = dateRangeStart,
                    DateRangeEnd = dateRangeEnd
                });
            }
        }

        return categories;
    }
}
