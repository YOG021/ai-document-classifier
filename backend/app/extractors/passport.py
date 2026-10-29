import re
from typing import List, Dict, Any
from ..models import PassportData

def parse_mrz_dates(date_str: str) -> str:
    """Converts YYMMDD into DD/MM/YYYY"""
    if len(date_str) == 6 and date_str.isdigit():
        yy = int(date_str[:2])
        mm = date_str[2:4]
        dd = date_str[4:6]
        # Assume 19xx for yy > 40, else 20xx
        year = 1900 + yy if yy > 40 else 2000 + yy
        return f"{dd}/{mm}/{year}"
    return date_str

def extract_passport_data(lines: List[str], ocr_meta: Dict[str, Any]) -> Dict[str, Any]:
    full_text = "\n".join(lines)
    
    # 1. MRZ Lines
    mrz_lines: List[str] = []
    for line in lines:
        cleaned_line = line.replace(" ", "").upper()
        if "P<IND" in cleaned_line or (len(cleaned_line) >= 25 and "<" in cleaned_line):
            mrz_lines.append(cleaned_line)

    # 2. Passport Number (1 letter + 7 digits)
    passport_number = None
    pno_match = re.search(r"(?:Passport\s*No|Passport\s*Number)[:.\s]*([A-Z][0-9]{7})\b", full_text, re.IGNORECASE)
    if pno_match:
        passport_number = pno_match.group(1).upper()
    else:
        p_matches = re.findall(r"\b([A-Z][0-9]{7})\b", full_text)
        if p_matches:
            passport_number = p_matches[0]

    # 3. Surname & Given Names
    surname = None
    given_name = None
    full_name = None

    sur_match = re.search(r"(?:Surname)[:.\s]*([A-Za-z\s]+?)(?=\n|Given|Name|$)", full_text, re.IGNORECASE)
    if sur_match:
        surname = sur_match.group(1).strip()

    given_match = re.search(r"(?:Given\s*Name|Given\s*Names)[:.\s]*([A-Za-z\s]+?)(?=\n|Nationality|Sex|DOB|$)", full_text, re.IGNORECASE)
    if given_match:
        given_name = given_match.group(1).strip()

    # Parse MRZ Line 1: P<INDSURNAME<<GIVEN<NAME
    if mrz_lines:
        line1 = mrz_lines[0]
        if "P<IND" in line1:
            name_part = line1.split("P<IND", 1)[1]
            parts = name_part.split("<<")
            if len(parts) >= 2:
                if not surname:
                    surname = parts[0].replace("<", " ").strip()
                if not given_name:
                    given_name = parts[1].replace("<", " ").strip()
            elif len(parts) == 1:
                if not surname:
                    surname = parts[0].replace("<", " ").strip()

    if surname and given_name:
        full_name = f"{given_name} {surname}"
    elif given_name:
        full_name = given_name
    elif surname:
        full_name = surname

    # 4. Nationality
    nationality = "INDIAN"
    nat_match = re.search(r"(?:Nationality)[:.\s]*([A-Za-z]+)", full_text, re.IGNORECASE)
    if nat_match:
        cand_nat = nat_match.group(1).strip().upper()
        if cand_nat not in ["SEX", "M", "F", "DOB"]:
            nationality = cand_nat

    # 5. Sex / Gender
    gender = None
    sex_match = re.search(r"(?:Sex|Gender)[:.\s]*([MF])\b", full_text, re.IGNORECASE)
    if sex_match:
        gender = sex_match.group(1).upper()
    elif re.search(r"\b(?:MALE)\b", full_text, re.IGNORECASE):
        gender = "M"
    elif re.search(r"\b(?:FEMALE)\b", full_text, re.IGNORECASE):
        gender = "F"

    # 6. Dates: DOB, Date of Issue, Date of Expiry
    dob = None
    date_of_issue = None
    date_of_expiry = None

    dob_match = re.search(r"(?:Date\s*of\s*Birth|DOB)[:.\s]*(\d{2}[/-]\d{2}[/-]\d{4})", full_text, re.IGNORECASE)
    if dob_match:
        dob = dob_match.group(1)

    doi_match = re.search(r"(?:Date\s*of\s*Issue)[:.\s]*(\d{2}[/-]\d{2}[/-]\d{4})", full_text, re.IGNORECASE)
    if doi_match:
        date_of_issue = doi_match.group(1)

    doe_match = re.search(r"(?:Date\s*of\s*Expiry)[:.\s]*(\d{2}[/-]\d{2}[/-]\d{4})", full_text, re.IGNORECASE)
    if doe_match:
        date_of_expiry = doe_match.group(1)

    # Decode MRZ Line 2 if available
    # Line 2 format: [Passport(9)][Chk(1)][Nat(3)][DOB(6)][Chk(1)][Sex(1)][Exp(6)][Chk(1)]...
    if len(mrz_lines) >= 2:
        l2 = mrz_lines[1]
        if len(l2) >= 28:
            if not passport_number:
                passport_number = l2[:9].replace("<", "").strip()
            if not gender and l2[20] in ["M", "F"]:
                gender = l2[20]
            if not dob and l2[13:19].isdigit():
                dob = parse_mrz_dates(l2[13:19])
            if not date_of_expiry and l2[21:27].isdigit():
                date_of_expiry = parse_mrz_dates(l2[21:27])

    # 7. Places of Birth & Issue
    place_of_birth = None
    place_of_issue = None

    pob_match = re.search(r"(?:Place\s*of\s*Birth)[:.\s]*([A-Za-z\s,]+?)(?=\n|Place\s*of\s*Issue|Date|$)", full_text, re.IGNORECASE)
    if pob_match:
        place_of_birth = pob_match.group(1).strip()

    poi_match = re.search(r"(?:Place\s*of\s*Issue)[:.\s]*([A-Za-z\s,]+?)(?=\n|Date\s*of\s*Issue|Date\s*of\s*Expiry|$)", full_text, re.IGNORECASE)
    if poi_match:
        place_of_issue = poi_match.group(1).strip()

    # Fallback to standalone dates
    all_dates = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", full_text)
    if len(all_dates) >= 3:
        if not dob:
            dob = all_dates[0]
        if not date_of_issue:
            date_of_issue = all_dates[1]
        if not date_of_expiry:
            date_of_expiry = all_dates[2]

    photo_detected = ocr_meta.get("has_photo", False)

    model = PassportData(
        passport_number=passport_number,
        full_name=full_name,
        given_name=given_name,
        surname=surname,
        nationality=nationality,
        dob=dob,
        gender=gender,
        place_of_birth=place_of_birth,
        place_of_issue=place_of_issue,
        date_of_issue=date_of_issue,
        date_of_expiry=date_of_expiry,
        mrz_lines=mrz_lines[:2],
        photo_detected=photo_detected,
    )
    return model.model_dump()
