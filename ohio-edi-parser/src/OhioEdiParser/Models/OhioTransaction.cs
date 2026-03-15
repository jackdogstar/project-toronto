namespace OhioEdiParser.Models;

public class OhioTransaction
{
    public TransactionContext Header { get; init; } = null!;
    public List<OhioMember> Members { get; init; } = new();
}
