using System.Text;

namespace OhioEdiParser.Tests.TestData.Builders;

/// <summary>
/// Fluent builder for constructing valid Ohio 834 EDI strings for testing.
/// </summary>
public class EdiBuilder
{
    private readonly StringBuilder _body = new();
    private string _bgn08 = "2"; // default to Changes file
    private string _refId = "REF001";
    private string _providerId = "1234567";
    private string _sponsorName = "OMES";
    private string _sponsorTaxId = "311334825";
    private string _mceName = "CareSource";
    private string _mceTaxId = "311764600";
    private string _receiverId = "0003150";

    public static EdiBuilder Create() => new();

    public EdiBuilder AsFullFile()
    {
        _bgn08 = "4";
        return this;
    }

    public EdiBuilder AsChangesFile()
    {
        _bgn08 = "2";
        return this;
    }

    public EdiBuilder WithProviderId(string id)
    {
        _providerId = id;
        return this;
    }

    public EdiBuilder WithReceiverId(string id)
    {
        _receiverId = id;
        return this;
    }

    public EdiBuilder AddMember(Action<MemberBuilder> configure)
    {
        var mb = new MemberBuilder();
        configure(mb);
        _body.Append(mb.Build());
        return this;
    }

    public string Build()
    {
        var sb = new StringBuilder();

        // ISA (exactly 106 chars including terminator)
        sb.Append($"ISA*00*          *00*          *ZZ*MMISODJFS      *ZZ*{_receiverId.PadRight(15)}*250611*0800*^*00501*000000001*0*P*:~");

        // GS
        sb.Append($"GS*HP*MMISODJFS*{_receiverId}*20250611*0800*1*X*005010X220A1~");

        // ST
        sb.Append("ST*834*0001~");

        // BGN
        sb.Append($"BGN*00*{_refId}*20250611*****{_bgn08}~");

        // REF*38 (Provider ID)
        sb.Append($"REF*38*{_providerId}~");

        // DTP*007 (Effective Date)
        sb.Append("DTP*007*D8*20250611~");

        // 1000A — Sponsor
        sb.Append($"N1*P5*{_sponsorName}*FI*{_sponsorTaxId}~");

        // 1000B — Payer/MCE
        sb.Append($"N1*IN*{_mceName}*FI*{_mceTaxId}~");

        // Members
        sb.Append(_body);

        // SE
        sb.Append("SE*999*0001~");

        // GE
        sb.Append("GE*1*1~");

        // IEA
        sb.Append("IEA*1*000000001~");

        return sb.ToString();
    }
}

public class MemberBuilder
{
    private readonly StringBuilder _segments = new();
    private string _ins03 = "021";
    private string _ins04 = "28";
    private string _ins08 = "FT";
    private string _ins12 = "";
    private string _medicaidId = "123456789012";
    private string _lastName = "DOE";
    private string _firstName = "JOHN";
    private string _middleName = "M";
    private string _ssn = "123456789";
    private string _dob = "19800115";
    private string _gender = "M";
    private string _race = "C";
    private string _addressLine1 = "123 MAIN ST";
    private string _city = "COLUMBUS";
    private string _state = "OH";
    private string _zip = "43215";
    private string _countyCode = "25";
    private readonly List<Action<StringBuilder>> _coverageActions = new();
    private readonly List<Action<StringBuilder>> _memberLevelActions = new(); // REF/DTP at Loop 2000 level
    private readonly List<Action<StringBuilder>> _postDemoActions = new();    // responsible person, COB, reporting

    public MemberBuilder WithMaintenanceType(string code)
    {
        _ins03 = code;
        return this;
    }

    public MemberBuilder WithAssignmentReason(string code)
    {
        _ins04 = code;
        return this;
    }

    public MemberBuilder WithEmploymentStatus(string status)
    {
        _ins08 = status;
        return this;
    }

    public MemberBuilder WithDateOfDeath(string date)
    {
        _ins12 = date;
        return this;
    }

    public MemberBuilder WithMedicaidId(string id)
    {
        _medicaidId = id;
        return this;
    }

    public MemberBuilder WithName(string last, string first, string? middle = null)
    {
        _lastName = last;
        _firstName = first;
        _middleName = middle ?? "";
        return this;
    }

    public MemberBuilder WithSsn(string ssn)
    {
        _ssn = ssn;
        return this;
    }

    public MemberBuilder WithDob(string dob)
    {
        _dob = dob;
        return this;
    }

    public MemberBuilder WithGender(string gender)
    {
        _gender = gender;
        return this;
    }

    public MemberBuilder WithRace(string race)
    {
        _race = race;
        return this;
    }

    public MemberBuilder WithAddress(string line1, string city, string state, string zip)
    {
        _addressLine1 = line1;
        _city = city;
        _state = state;
        _zip = zip;
        return this;
    }

    public MemberBuilder WithOdmPlaceholderAddress()
    {
        _addressLine1 = "50 W. TOWN ST SUITE 400";
        _city = "COLUMBUS";
        _state = "OH";
        _zip = "43215";
        return this;
    }

    public MemberBuilder AddCoverage(string hd01, string hd03, string hd04,
        string beginDate, string? endDate = null, string? rateCell = null)
    {
        _coverageActions.Add(sb =>
        {
            sb.Append($"HD*{hd01}**{hd03}*{hd04}~");
            sb.Append($"DTP*348*D8*{beginDate}~");
            if (endDate != null)
                sb.Append($"DTP*349*D8*{endDate}~");
            if (rateCell != null)
                sb.Append($"REF*1L*{rateCell}~");
        });
        return this;
    }

    public MemberBuilder AddCoverageWithProvider(string hd01, string hd03, string hd04,
        string beginDate, string providerType, string providerName, string providerId)
    {
        _coverageActions.Add(sb =>
        {
            sb.Append($"HD*{hd01}**{hd03}*{hd04}~");
            sb.Append($"DTP*348*D8*{beginDate}~");
            sb.Append("LX*1~");
            sb.Append($"NM1*{providerType}*2*{providerName}*****SV*{providerId}~");
        });
        return this;
    }

    public MemberBuilder AddCoverageWithPatientLiability(string amount)
    {
        _coverageActions.Add(sb =>
        {
            sb.Append("HD*021**MM*PL-F~");
            sb.Append("DTP*348*D8*20250101~");
            sb.Append($"AMT*D2*{amount}~");
        });
        return this;
    }

    public MemberBuilder AddRef(string qualifier, string value)
    {
        _memberLevelActions.Add(sb => sb.Append($"REF*{qualifier}*{value}~"));
        return this;
    }

    public MemberBuilder AddDtp(string qualifier, string date)
    {
        _memberLevelActions.Add(sb => sb.Append($"DTP*{qualifier}*D8*{date}~"));
        return this;
    }

    public MemberBuilder AddResponsiblePerson(string typeCode, string lastName, string firstName)
    {
        _postDemoActions.Add(sb =>
        {
            sb.Append($"NM1*{typeCode}*1*{lastName}*{firstName}~");
            sb.Append("N3*789 ELM ST~");
            sb.Append("N4*CLEVELAND*OH*44101~");
        });
        return this;
    }

    public MemberBuilder AddCob(string payerResp, string cobCode, string? insurerName = null)
    {
        _postDemoActions.Add(sb =>
        {
            sb.Append($"COB*{payerResp}**{cobCode}~");
            if (insurerName != null)
                sb.Append($"NM1*IN*2*{insurerName}~");
        });
        return this;
    }

    public MemberBuilder AddReportingCategory(string categoryName, string refQualifier,
        string refValue, string dateFormat = "D8", string dateValue = "20250101")
    {
        _postDemoActions.Add(sb =>
        {
            sb.Append("LX*99~");
            sb.Append($"N1*75*{categoryName}~");
            sb.Append($"REF*{refQualifier}*{refValue}~");
            sb.Append($"DTP*007*{dateFormat}*{dateValue}~");
        });
        return this;
    }

    internal string Build()
    {
        var sb = new StringBuilder();

        // INS segment — pad to 12 elements
        sb.Append($"INS*Y*18*{_ins03}*{_ins04}*A***{_ins08}****{_ins12}~");

        // REF*0F (Medicaid ID)
        sb.Append($"REF*0F*{_medicaidId}~");

        // Member-level REF/DTP segments (Loop 2000, before NM1)
        foreach (var action in _memberLevelActions)
        {
            action(sb);
        }

        // NM1*IL (Member Name + SSN)
        sb.Append($"NM1*IL*1*{_lastName}*{_firstName}*{_middleName}***34*{_ssn}~");

        // N3 (Address)
        sb.Append($"N3*{_addressLine1}~");

        // N4 (City/State/Zip/County)
        sb.Append($"N4*{_city}*{_state}*{_zip}**CY*{_countyCode}~");

        // DMG (Demographics)
        sb.Append($"DMG*D8*{_dob}*{_gender}**{_race}~");

        // PER (Contact) — optional, add a phone
        sb.Append("PER*IP**TE*6145551234~");

        // Post-demographic segments (responsible person, COB, reporting)
        foreach (var action in _postDemoActions)
        {
            action(sb);
        }

        // Coverages
        if (_coverageActions.Count == 0)
        {
            // Default coverage
            sb.Append($"HD*{_ins03}**HMO*CFC~");
            sb.Append("DTP*348*D8*20250101~");
            sb.Append("DTP*349*D8*20251231~");
            sb.Append("REF*1L*OHCFCM2580~");
        }
        else
        {
            foreach (var action in _coverageActions)
            {
                action(sb);
            }
        }

        return sb.ToString();
    }
}
