using OhioEdiParser.CodeSets;
using OhioEdiParser.Models;

namespace OhioEdiParser.Validation;

public static class OhioValidator
{
    private static readonly HashSet<string> ValidInsMaintenanceCodes = new() { "001", "021", "024", "030" };

    public static ValidationResult Validate(OhioParseResult result)
    {
        var issues = new List<ValidationIssue>();

        foreach (var tx in result.Transactions)
        {
            foreach (var member in tx.Members)
            {
                ValidateMedicaidId(member, issues);
                ValidateMaintenanceType(member, issues);
                ValidateFileTypeConsistency(member, tx.Header, issues);
                ValidateCoveragePresent(member, issues);
                ValidateBenefitBeginDate(member, issues);
                ValidateAssignmentReason(member, issues);
                ValidatePlanCoverageDesc(member, issues);
                ValidateRateCell(member, issues);
                ValidateDeathRecord(member, issues);
                ValidateAddress(member, issues);
                ValidateBenefitEndDate(member, tx.Header, issues);
                ValidateLinkedIds(member, issues);
                CheckDualEligible(member, issues);
                CheckAlternateId(member, issues);
                CheckInstitutional(member, issues);
            }
        }

        return new ValidationResult(issues);
    }

    // OH-VAL-001: Medicaid ID must be present and exactly 12 characters
    private static void ValidateMedicaidId(OhioMember member, List<ValidationIssue> issues)
    {
        if (string.IsNullOrEmpty(member.MedicaidId) || member.MedicaidId.Length != 12)
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-001",
                Severity = ValidationSeverity.Critical,
                Message = $"Medicaid ID must be exactly 12 characters. Got: '{member.MedicaidId}' ({member.MedicaidId?.Length ?? 0} chars)",
                MemberMedicaidId = member.MedicaidId
            });
            member.HasCriticalErrors = true;
        }
    }

    // OH-VAL-002: INS03 must be a valid code
    private static void ValidateMaintenanceType(OhioMember member, List<ValidationIssue> issues)
    {
        if (!ValidInsMaintenanceCodes.Contains(member.MaintenanceTypeCode))
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-002",
                Severity = ValidationSeverity.Critical,
                Message = $"Invalid INS03 maintenance type: '{member.MaintenanceTypeCode}'",
                MemberMedicaidId = member.MedicaidId
            });
            member.HasCriticalErrors = true;
        }
    }

    // OH-VAL-003 & OH-VAL-004: File type consistency
    private static void ValidateFileTypeConsistency(OhioMember member, TransactionContext header, List<ValidationIssue> issues)
    {
        if (header.FileType == OhioFileType.Full && member.MaintenanceTypeCode != "030")
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-003",
                Severity = ValidationSeverity.Critical,
                Message = $"Full File (BGN08=4) but INS03='{member.MaintenanceTypeCode}', expected '030'",
                MemberMedicaidId = member.MedicaidId
            });
            member.HasCriticalErrors = true;
        }

        if (header.FileType == OhioFileType.Changes && member.MaintenanceTypeCode == "030")
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-004",
                Severity = ValidationSeverity.Critical,
                Message = "Changes File (BGN08=2) but INS03='030' (Audit) — not valid in Changes File",
                MemberMedicaidId = member.MedicaidId
            });
            member.HasCriticalErrors = true;
        }
    }

    // OH-VAL-005: At least one coverage per member
    private static void ValidateCoveragePresent(OhioMember member, List<ValidationIssue> issues)
    {
        if (member.Coverages.Count == 0)
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-005",
                Severity = ValidationSeverity.Critical,
                Message = "No health coverage (Loop 2300/HD) found for member",
                MemberMedicaidId = member.MedicaidId
            });
            member.HasCriticalErrors = true;
        }
    }

    // OH-VAL-006: Benefit begin date required
    private static void ValidateBenefitBeginDate(OhioMember member, List<ValidationIssue> issues)
    {
        for (int i = 0; i < member.Coverages.Count; i++)
        {
            if (string.IsNullOrEmpty(member.Coverages[i].BenefitBeginDate))
            {
                issues.Add(new ValidationIssue
                {
                    RuleCode = "OH-VAL-006",
                    Severity = ValidationSeverity.Critical,
                    Message = $"DTP*348 (Benefit Begin Date) missing for coverage {i}",
                    MemberMedicaidId = member.MedicaidId,
                    CoverageIndex = i
                });
                member.HasCriticalErrors = true;
            }
        }
    }

    // OH-VAL-101: Unknown assignment reason
    private static void ValidateAssignmentReason(OhioMember member, List<ValidationIssue> issues)
    {
        if (!string.IsNullOrEmpty(member.AssignmentReasonCode) &&
            !AssignmentReasonCodes.IsKnown(member.AssignmentReasonCode))
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-101",
                Severity = ValidationSeverity.Warning,
                Message = $"Unknown assignment reason code: '{member.AssignmentReasonCode}'",
                MemberMedicaidId = member.MedicaidId
            });
        }
    }

    // OH-VAL-102: Unknown plan coverage description
    private static void ValidatePlanCoverageDesc(OhioMember member, List<ValidationIssue> issues)
    {
        for (int i = 0; i < member.Coverages.Count; i++)
        {
            var desc = member.Coverages[i].PlanCoverageDesc;
            if (!string.IsNullOrEmpty(desc) && !PlanCoverageDescCodes.IsKnown(desc))
            {
                issues.Add(new ValidationIssue
                {
                    RuleCode = "OH-VAL-102",
                    Severity = ValidationSeverity.Warning,
                    Message = $"Unknown plan coverage description: '{desc}'",
                    MemberMedicaidId = member.MedicaidId,
                    CoverageIndex = i
                });
            }
        }
    }

    // OH-VAL-103: Rate cell is XXXXXXXXXX
    private static void ValidateRateCell(OhioMember member, List<ValidationIssue> issues)
    {
        for (int i = 0; i < member.Coverages.Count; i++)
        {
            if (member.Coverages[i].RateCellMissing)
            {
                issues.Add(new ValidationIssue
                {
                    RuleCode = "OH-VAL-103",
                    Severity = ValidationSeverity.Warning,
                    Message = "Rate cell indicator is XXXXXXXXXX — no unique rate cell exists",
                    MemberMedicaidId = member.MedicaidId,
                    CoverageIndex = i
                });
            }
        }
    }

    // OH-VAL-104: Death without date
    private static void ValidateDeathRecord(OhioMember member, List<ValidationIssue> issues)
    {
        if (member.AssignmentReasonCode == "3" && string.IsNullOrEmpty(member.DateOfDeath))
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-104",
                Severity = ValidationSeverity.Warning,
                Message = "INS04=03 (death) but INS12 (death date) is empty — incomplete death record",
                MemberMedicaidId = member.MedicaidId
            });
        }
    }

    // OH-VAL-105: ODM placeholder address
    private static void ValidateAddress(OhioMember member, List<ValidationIssue> issues)
    {
        if (member.Demographics?.Address?.IsOdmPlaceholder == true)
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-105",
                Severity = ValidationSeverity.Warning,
                Message = "Address matches ODM HQ placeholder — member has non-US address",
                MemberMedicaidId = member.MedicaidId
            });
        }
    }

    // OH-VAL-106: Missing benefit end date
    private static void ValidateBenefitEndDate(OhioMember member, TransactionContext header, List<ValidationIssue> issues)
    {
        for (int i = 0; i < member.Coverages.Count; i++)
        {
            if (string.IsNullOrEmpty(member.Coverages[i].BenefitEndDate))
            {
                issues.Add(new ValidationIssue
                {
                    RuleCode = "OH-VAL-106",
                    Severity = ValidationSeverity.Warning,
                    Message = "DTP*349 (Benefit End Date) absent — open-ended coverage",
                    MemberMedicaidId = member.MedicaidId,
                    CoverageIndex = i
                });
            }
        }
    }

    // OH-VAL-107: Multiple linked IDs
    private static void ValidateLinkedIds(OhioMember member, List<ValidationIssue> issues)
    {
        // This checks if the member has a linked ID — complex cases might have multiple
        if (!string.IsNullOrEmpty(member.LinkedSecondaryId))
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-107",
                Severity = ValidationSeverity.Warning,
                Message = "Member has linked/secondary ID (REF*Q4) — complex member identity case",
                MemberMedicaidId = member.MedicaidId
            });
        }
    }

    // OH-VAL-201: Dual-eligible
    private static void CheckDualEligible(OhioMember member, List<ValidationIssue> issues)
    {
        if (!string.IsNullOrEmpty(member.MedicareId))
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-201",
                Severity = ValidationSeverity.Informational,
                Message = "Member has Medicare ID (REF*F6) — dual-eligible member",
                MemberMedicaidId = member.MedicaidId
            });
        }
    }

    // OH-VAL-202: Alternate ID
    private static void CheckAlternateId(OhioMember member, List<ValidationIssue> issues)
    {
        if (!string.IsNullOrEmpty(member.AlternateId))
        {
            issues.Add(new ValidationIssue
            {
                RuleCode = "OH-VAL-202",
                Severity = ValidationSeverity.Informational,
                Message = "Member has Alternate ID (REF*6O) — former foster care placement",
                MemberMedicaidId = member.MedicaidId
            });
        }
    }

    // OH-VAL-203: Institutional living arrangement
    private static void CheckInstitutional(OhioMember member, List<ValidationIssue> issues)
    {
        foreach (var rc in member.ReportingCategories)
        {
            if (rc.RefQualifier == "LU" && LivingArrangementCodes.InstitutionalCodes.Contains(rc.RefValue))
            {
                issues.Add(new ValidationIssue
                {
                    RuleCode = "OH-VAL-203",
                    Severity = ValidationSeverity.Informational,
                    Message = $"Living arrangement indicates institutional setting: code '{rc.RefValue}'",
                    MemberMedicaidId = member.MedicaidId
                });
            }
        }
    }
}
