import re
from typing import List, Dict, Any, Optional
from ..models import AadhaarData

def extract_aadhaar_data(lines: List[str], ocr_meta: Dict[str, Any]) -> Dict[str, Any]:
    full_text = "\n".join(lines)
    
    # 1. Aadhaar Number (12 digits, XXXX XXXX XXXX or XXXXXXXXXXXX)
    aadhaar_num = None
    uid_match = re.search(r"\b([2-9]\d{3}\s\d{4}\s\d{4})\b", full_text)
    if uid_match:
        aadhaar_num = uid_match.group(1)
    else:
        # Check without spaces
        raw_uid = re.search(r"\b([2-9]\d{11})\b", full_text)
        if raw_uid:
            raw = raw_uid.group(1)
            aadhaar_num = f"{raw[:4]} {raw[4:8]} {raw[8:]}"

    # 2. VID (Virtual ID) - Omitted as per user requirement
    vid = None

    # 3. DOB or YOB
    dob_or_yob = None
    dob_match = re.search(r"(?:DOB|Date of Birth|जन्म तारीख)[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})", full_text, re.IGNORECASE)
    if dob_match:
        dob_or_yob = dob_match.group(1)
    else:
        # Check Year of Birth
        yob_match = re.search(r"(?:Year of Birth|जन्म वर्ष|YOB)[:\s]*(\d{4})", full_text, re.IGNORECASE)
        if yob_match:
            dob_or_yob = yob_match.group(1)
        else:
            # Standalone date format
            stand_date = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", full_text)
            if stand_date:
                dob_or_yob = stand_date.group(1)

    # 4. Gender (Male / Female / Transgender)
    gender = None
    if re.search(r"\b(?:MALE|PURUSH|पुरुष)\b", full_text, re.IGNORECASE):
        gender = "Male"
    elif re.search(r"\b(?:FEMALE|STREE|महिला)\b", full_text, re.IGNORECASE):
        gender = "Female"
    elif re.search(r"\b(?:TRANSGENDER)\b", full_text, re.IGNORECASE):
        gender = "Transgender"

    # 5. Care of / Relationship & Guardian Name
    relation_type = None
    guardian_name = None
    rel_match = re.search(r"\b(C/O|S/O|D/O|W/O)[:\s]+([A-Za-z\s.]+?)(?:,|\n|Door|House|H\.No|Ward)", full_text, re.IGNORECASE)
    if rel_match:
        relation_type = rel_match.group(1).upper()
        guardian_name = rel_match.group(2).strip()
    else:
        # Check line by line
        for i, line in enumerate(lines):
            for prefix in ["C/O", "S/O", "D/O", "W/O"]:
                if prefix in line.upper():
                    relation_type = prefix
                    parts = line.split(":", 1) if ":" in line else line.split(prefix, 1)
                    if len(parts) > 1 and parts[1].strip():
                        guardian_name = parts[1].strip()
                    elif i + 1 < len(lines):
                        guardian_name = lines[i + 1].strip()
                    break
            if relation_type:
                break

    # 6. Full Name
    BLOCKED_NAME_SUBSTRINGS = [
        "GOVERN", "GOVT", "INDIA", "BHARAT", "SARKAR",
        "UIDAI", "AUTHORITY", "IDENTIFICATION", "UNIQUE",
        "AADHAAR", "ADHAAR", "ADHAR", "PEHCHAN", "ENROL",
        "HELP@", "WWW.", "HTTP", ".GOV", "1947",
        "DOWNLOAD", "ISSUE DATE", "VALIDITY", "DIGITAL",
        "ADDRESS", "PINCODE", "PIN CODE",
        "C/O", "S/O", "D/O", "W/O",
        "MALE", "FEMALE", "TRANSGENDER", "GENDER",
        "DOB", "YOB", "DATE OF BIRTH", "YEAR OF BIRTH",
        "VID", "CARD NUMBER"
    ]

    BLOCKED_NAME_TOKENS = {
        "INDIA", "GOVERNMENT", "GOVERMENT", "GOVT", "AUTHORITY", "UNIQUE",
        "IDENTIFICATION", "AADHAAR", "UIDAI", "PURUSH", "STREE", "MAHILA"
    }

    def is_valid_name_candidate(cand: str) -> bool:
        clean = cand.strip()
        if not clean or len(clean) < 3 or len(clean) > 50:
            return False
        if any(c.isdigit() for c in clean):
            return False
        # Only allow Latin letters, spaces, dots, hyphens, and apostrophes
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .'-")
        if not all(c in allowed_chars for c in clean):
            return False
        letters_only = [c for c in clean if c.isalpha()]
        if len(letters_only) < 3:
            return False
        clean_upper = clean.upper()
        for b in BLOCKED_NAME_SUBSTRINGS:
            if b in clean_upper:
                return False
        tokens = set(re.findall(r"[A-Za-z]+", clean_upper))
        if tokens & BLOCKED_NAME_TOKENS:
            return False
        words = [w for w in clean.split() if any(c.isalpha() for c in w)]
        if len(words) < 1 or len(words) > 6:
            return False
        return True

    name = None

    # Priority 1: Explicit label (e.g. "Name / नाम : John Doe" or "Name: John Doe")
    label_match = re.search(r"(?:Name|नाम|Cardholder\s*Name)[:\s]+([A-Za-z\s.]{3,40})", full_text, re.IGNORECASE)
    if label_match and is_valid_name_candidate(label_match.group(1)):
        name = label_match.group(1).strip()

    # Priority 2: Look backwards from DOB / YOB line (most reliable for Aadhaar cards)
    if not name:
        dob_idx = -1
        for i, line in enumerate(lines):
            if re.search(r"(?:DOB|Date of Birth|Year of Birth|YOB|जन्म तारीख|जन्म वर्ष|\b\d{2}[/-]\d{2}[/-]\d{4}\b)", line, re.IGNORECASE):
                dob_idx = i
                break
        if dob_idx > 0:
            for i in range(dob_idx - 1, max(-1, dob_idx - 5), -1):
                if is_valid_name_candidate(lines[i]):
                    cand = lines[i].strip()
                    if not guardian_name or cand.upper() != guardian_name.upper():
                        name = cand
                        break
            if not name:
                for i in range(dob_idx - 1, max(-1, dob_idx - 5), -1):
                    if is_valid_name_candidate(lines[i]):
                        name = lines[i].strip()
                        break

    # Priority 3: Look backwards from Gender line
    if not name:
        gender_idx = -1
        for i, line in enumerate(lines):
            if re.search(r"\b(?:MALE|FEMALE|TRANSGENDER|PURUSH|STREE|महिला|पुरुष)\b", line, re.IGNORECASE):
                gender_idx = i
                break
        if gender_idx > 0:
            for i in range(gender_idx - 1, max(-1, gender_idx - 5), -1):
                if is_valid_name_candidate(lines[i]):
                    name = lines[i].strip()
                    break

    # Priority 4: Look backwards from Aadhaar number line
    if not name:
        uid_idx = -1
        for i, line in enumerate(lines):
            if re.search(r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b", line):
                uid_idx = i
                break
        if uid_idx > 0:
            for i in range(uid_idx - 1, max(-1, uid_idx - 6), -1):
                if is_valid_name_candidate(lines[i]):
                    name = lines[i].strip()
                    break

    # Priority 5: Scan all lines
    if not name:
        for line in lines:
            if is_valid_name_candidate(line):
                cand = line.strip()
                if not guardian_name or cand.upper() != guardian_name.upper():
                    name = cand
                    break
        if not name:
            for line in lines:
                if is_valid_name_candidate(line):
                    name = line.strip()
                    break

    # 7. Address & PIN Code
    pin_code = None
    pin_match = re.search(r"\b([1-9][0-9]{5})\b", full_text)
    if pin_match:
        pin_code = pin_match.group(1)

    address = None
    addr_match = re.search(r"(?:Address|पता)[:\s]*([\s\S]+?)(?:\d{6}|$)", full_text, re.IGNORECASE)
    if addr_match:
        raw_addr = addr_match.group(1).strip()
        address = " ".join(raw_addr.split())
        address = re.sub(r"[\s,-]+$", "", address)
        if pin_code and pin_code not in address:
            address += f" - {pin_code}"
    elif "Address" in full_text:
        # Fallback to lines below 'Address'
        addr_lines = []
        capture = False
        for line in lines:
            if "Address" in line:
                capture = True
                continue
            if capture:
                if re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", line) or "UIDAI" in line:
                    break
                addr_lines.append(line)
        if addr_lines:
            address = ", ".join(addr_lines)
            address = re.sub(r"[\s,-]+$", "", address)
            if pin_code and pin_code not in address:
                address += f" - {pin_code}"

    # 8. Photo & QR Code
    photo_detected = ocr_meta.get("has_photo", False)
    qr_detected = ocr_meta.get("has_qr", False) or bool(ocr_meta.get("qr_payloads"))

    model = AadhaarData(
        aadhaar_number=aadhaar_num,
        vid=vid,
        name=name,
        dob_or_yob=dob_or_yob,
        gender=gender,
        relation_type=relation_type,
        guardian_name=guardian_name,
        address=address,
        pin_code=pin_code,
        photo_detected=photo_detected,
        qr_detected=qr_detected,
    )
    return model.model_dump()
