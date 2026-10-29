from typing import List, Dict, Any, Tuple
from .aadhaar import extract_aadhaar_data
from .pan import extract_pan_data
from .ssc import extract_ssc_data
from .passport import extract_passport_data
from .income_cert import extract_income_data

def extract_and_validate(doc_type: str, lines: List[str], ocr_meta: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], str]:
    validation_issues: List[str] = []
    status = "valid"

    if doc_type == "aadhaar":
        data = extract_aadhaar_data(lines, ocr_meta)
        if not data.get("aadhaar_number"):
            validation_issues.append("Missing or unreadable 12-digit Aadhaar UID.")
        if not data.get("name"):
            validation_issues.append("Candidate Full Name could not be confirmed with high confidence.")
        if not data.get("dob_or_yob"):
            validation_issues.append("Date of Birth or Year of Birth not detected.")
            
    elif doc_type == "pan":
        data = extract_pan_data(lines, ocr_meta)
        pan = data.get("pan_number")
        if not pan:
            validation_issues.append("Valid 10-character PAN number not found.")
        elif len(pan) == 10 and pan[3] not in ["P", "C", "H", "F", "A", "T", "B", "L", "J", "G"]:
            validation_issues.append(f"PAN 4th character '{pan[3]}' is not a standard PAN holder entity code.")
        if not data.get("dob"):
            validation_issues.append("Date of Birth not clearly identified on card.")
        if not data.get("name"):
            validation_issues.append("Cardholder name not confirmed.")

    elif doc_type == "ssc":
        data = extract_ssc_data(lines, ocr_meta)
        if not data.get("roll_number"):
            validation_issues.append("Hall Ticket / Roll Number missing or unreadable.")
        if not data.get("candidate_name"):
            validation_issues.append("Candidate Name not identified.")
        if not data.get("subject_marks"):
            validation_issues.append("Subject marks table structure could not be parsed.")

    elif doc_type == "passport":
        data = extract_passport_data(lines, ocr_meta)
        if not data.get("passport_number"):
            validation_issues.append("Passport Number (1 letter + 7 digits) not found.")
        if not data.get("mrz_lines"):
            validation_issues.append("Machine Readable Zone (MRZ) lines not detected at document bottom.")
        if not data.get("date_of_expiry"):
            validation_issues.append("Date of Expiry not identified.")

    elif doc_type == "income_cert":
        data = extract_income_data(lines, ocr_meta)
        if not data.get("annual_income"):
            validation_issues.append("Annual income amount not parsed.")
        if not data.get("applicant_name"):
            validation_issues.append("Applicant name missing.")
        if not data.get("issuing_authority"):
            validation_issues.append("Issuing Authority designation (e.g. Tahsildar) not detected.")

    else:
        data = {}
        validation_issues.append("Unknown or unclassified document type.")
        status = "invalid"

    if validation_issues and status != "invalid":
        status = "warning" if len(validation_issues) <= 2 else "invalid"

    return data, validation_issues, status
