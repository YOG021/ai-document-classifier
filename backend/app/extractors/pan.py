import re
from typing import List, Dict, Any
from ..models import PANData

def extract_pan_data(lines: List[str], ocr_meta: Dict[str, Any]) -> Dict[str, Any]:
    full_text = "\n".join(lines)
    
    # 1. PAN Number (10 characters: 5 letters, 4 digits, 1 letter)
    pan_number = None
    pan_matches = re.findall(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", full_text)
    if pan_matches:
        pan_number = pan_matches[0]

    # 2. Date of Birth (DD/MM/YYYY)
    dob = None
    dob_match = re.search(r"(?:DOB|Date of Birth|जन्म तारीख)[:\s]*(\d{2}/\d{2}/\d{4})", full_text, re.IGNORECASE)
    if not dob_match:
        dob_match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", full_text)
    if dob_match:
        dob = dob_match.group(1)

    # 3. Cardholder Name and Father's Name
    name = None
    fathers_name = None

    # Filter out known header lines
    ignore_headers = [
        "INCOME TAX DEPARTMENT", "GOVT. OF INDIA", "GOVERNMENT OF INDIA",
        "PERMANENT ACCOUNT NUMBER CARD", "PERMANENT ACCOUNT NUMBER",
        "INAYAKAR VIBHAG", "SIGNATURE", "CARDHOLDER'S SIGNATURE"
    ]
    candidate_lines = []
    for line in lines:
        clean = line.strip()
        clean_upper = clean.upper()
        if any(h in clean_upper for h in ignore_headers):
            continue
        if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", clean):
            continue
        if re.search(r"\b\d{2}/\d{2}/\d{4}\b", clean):
            continue
        # Names on PAN card are uppercase letters and spaces
        if re.match(r"^[A-Z][A-Z\s.]{2,40}$", clean) and len(clean.split()) >= 1:
            candidate_lines.append(clean)

    # Contextual labeling if labels exist
    for i, line in enumerate(lines):
        clean_upper = line.upper()
        if "FATHER'S NAME" in clean_upper or "FATHER NAME" in clean_upper:
            parts = line.split(":", 1) if ":" in line else []
            if len(parts) > 1 and parts[1].strip():
                fathers_name = parts[1].strip()
            elif i + 1 < len(lines):
                fathers_name = lines[i + 1].strip()
        elif "NAME" in clean_upper and "FATHER" not in clean_upper and "DEPARTMENT" not in clean_upper:
            parts = line.split(":", 1) if ":" in line else []
            if len(parts) > 1 and parts[1].strip():
                name = parts[1].strip()

    # Fallback to positional candidates (Cardholder Name comes first, Father's Name comes second)
    if not name and len(candidate_lines) >= 1:
        name = candidate_lines[0]
    if not fathers_name and len(candidate_lines) >= 2:
        fathers_name = candidate_lines[1]

    # 4. Photo, Signature, QR Code
    photo_detected = ocr_meta.get("has_photo", False)
    signature_detected = ocr_meta.get("has_signature", False)
    qr_detected = ocr_meta.get("has_qr", False) or bool(ocr_meta.get("qr_payloads"))

    model = PANData(
        pan_number=pan_number,
        name=name,
        fathers_name=fathers_name,
        dob=dob,
        photo_detected=photo_detected,
        signature_detected=signature_detected,
        qr_detected=qr_detected,
    )
    return model.model_dump()
