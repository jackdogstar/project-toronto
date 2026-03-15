namespace OhioEdiParser.Models;

public enum OhioFileType
{
    Full,     // BGN08 = "4" (Verify) — monthly snapshot
    Changes   // BGN08 = "2" (Change/Update) — daily incremental
}
