namespace OhioEdiParser.Models;

public enum MaintenanceAction
{
    Add,         // 021
    Change,      // 001
    Termination, // 024
    Audit,       // 030
    Delete,      // 002 (HD01 only)
    Reinstate    // 025 (HD01 only)
}
