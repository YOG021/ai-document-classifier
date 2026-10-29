import re
from typing import List, Dict, Any
from ..models import IncomeCertData

def extract_income_data(lines: List[str], ocr_meta: Dict[str, Any]) -> Dict[str, Any]:
    full_text = "\n".join(lines)
    
    # 1. Application / Certificate Number
    app_number = None
    app_match = re.search(r"(?:Application\s*(?:No|Number)|Certificate\s*(?:No|Number)|Appl\.?\s*No|Application\s*ID)[:.\s]*([A-Z0-9/-]+)\b", full_text, re.IGNORECASE)
    if app_match:
        app_number = app_match.group(1).strip()
    else:
        id_match = re.search(r"\b([A-Z]{2,4}\d{8,14})\b", full_text)
        if id_match:
            app_number = id_match.group(1)

    # 2. G.O. Ms. No.
    go_ms_no = None
    go_match = re.search(r"(G\.?O\.?\s*(?:Ms|Rt)?\.?\s*No\.?[:.\s]*[A-Za-z0-9/,\s.-]+?)(?=\n|Date|Dated|$)", full_text, re.IGNORECASE)
    if go_match:
        go_ms_no = go_match.group(1).strip()

    # 3. Date of Application / Date of Issue
    date_of_issue = None
    date_match = re.search(r"(?:Date\s*of\s*Issue|Date\s*of\s*Application|Dated|Date)[:.\s]*(\d{2}[/-]\d{2}[/-]\d{4})", full_text, re.IGNORECASE)
    if not date_match:
        date_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b", full_text)
    if date_match:
        date_of_issue = date_match.group(1)

    # 4. Applicant Name
    applicant_name = None
    # Check explicit label first
    app_name_match = re.search(r"(?:Applicant\s*Name)[:.\s]*([A-Za-z\s.]+?)(?=\n|Father|S/o|D/o|W/o|Door|Address|$)", full_text, re.IGNORECASE)
    if app_name_match:
        applicant_name = app_name_match.group(1).strip()
    else:
        # Check 'Sri MANOJ KUMAR REDDY' or 'Certified that Sri MANOJ KUMAR REDDY'
        cert_match = re.search(r"(?:Certified\s*that\s*(?:Sri|Smt|Kumari)?|Sri|Smt|Kumari)[:.\s]*([A-Za-z\s.]+?)(?=\n|S/o|D/o|W/o|H/o|Son|Daughter|Resident|$)", full_text, re.IGNORECASE)
        if cert_match:
            cand = cert_match.group(1).strip()
            if len(cand.split()) >= 1 and cand.upper() not in ["MANOJ", "GOVERNMENT", "REVENUE"]:
                applicant_name = cand

    # 5. Father's / Guardian's Name
    father_or_guardian = None
    g_match = re.search(r"\b(?:Father's\s*Name|Husband's\s*Name|Guardian's\s*Name|S/o|D/o|W/o|H/o)[:.\s]*([A-Za-z\s.]+?)(?=\n|Resident|Village|Door|Address|Mandal|District|$)", full_text, re.IGNORECASE)
    if g_match:
        father_or_guardian = g_match.group(1).strip()

    # 6. Annual Income (in numbers and words)
    annual_income = None
    inc_match = re.search(r"(?:Annual\s*Income|Total\s*Income|Family\s*Income|Income)[:.\s]*([₹RsINR.\s0-9,/-]+(?:\([A-Za-z\s]+\))?)", full_text, re.IGNORECASE)
    if inc_match and inc_match.group(1).strip():
        annual_income = " ".join(inc_match.group(1).split())
    else:
        rs_match = re.search(r"(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\s*/-)?)", full_text, re.IGNORECASE)
        if rs_match:
            raw_amt = rs_match.group(0).strip()
            words_match = re.search(r"\((?:Rupees|in words)[:\s]*([A-Za-z\s]+?)\)", full_text, re.IGNORECASE)
            if words_match:
                annual_income = f"{raw_amt} ({words_match.group(1).strip()})"
            else:
                annual_income = raw_amt

    # 7. Financial Year / Validity Period
    financial_year = None
    fy_match = re.search(r"(?:Financial\s*Year|Validity\s*Period|Validity)[:.\s]*(\d{4}[-–]\d{2,4})", full_text, re.IGNORECASE)
    if fy_match:
        financial_year = fy_match.group(1)
    else:
        stand_fy = re.search(r"\b(20\d{2}[-–](?:20)?\d{2})\b", full_text)
        if stand_fy:
            financial_year = stand_fy.group(1)

    # 8. Address
    address = None
    addr_match = re.search(r"(?:Address|Door\s*No|House\s*No|H\.No|Resident\s*of)[:.\s]*([A-Za-z0-9\s.,/-]+?)(?=\n|Mandal|Taluk|District|Annual|$)", full_text, re.IGNORECASE)
    if addr_match:
        address = " ".join(addr_match.group(1).split()).strip(" ,")

    # 9. Mandal / Taluk & District
    mandal_district = None
    md_match = re.search(r"(?:Mandal|Taluk)[:.\s]*([A-Za-z\s]+?)[\s,]+(?:District)[:.\s]*([A-Za-z\s]+)", full_text, re.IGNORECASE)
    if md_match:
        mandal_district = f"Mandal: {md_match.group(1).strip()}, District: {md_match.group(2).strip()}"
    else:
        dist_match = re.search(r"(?:District)[:.\s]*([A-Za-z\s]+)", full_text, re.IGNORECASE)
        if dist_match:
            mandal_district = f"District: {dist_match.group(1).strip()}"

    # 10. Issuing Authority
    issuing_authority = None
    if re.search(r"\bTAHSILDAR\b", full_text, re.IGNORECASE):
        issuing_authority = "Tahsildar (Revenue Department)"
    elif re.search(r"\bREVENUE DIVISIONAL OFFICER|RDO\b", full_text, re.IGNORECASE):
        issuing_authority = "Revenue Divisional Officer"
    elif re.search(r"\bMRO\b", full_text, re.IGNORECASE):
        issuing_authority = "Mandal Revenue Officer"
    else:
        auth_match = re.search(r"(?:Issuing\s*Authority|Designation)[:.\s]*([A-Za-z\s]+)", full_text, re.IGNORECASE)
        if auth_match:
            issuing_authority = auth_match.group(1).strip()

    model = IncomeCertData(
        application_number=app_number,
        go_ms_no=go_ms_no,
        date_of_issue=date_of_issue,
        applicant_name=applicant_name,
        father_or_guardian_name=father_or_guardian,
        annual_income=annual_income,
        financial_year=financial_year,
        address=address,
        mandal_district=mandal_district,
        issuing_authority=issuing_authority,
    )
    return model.model_dump()
