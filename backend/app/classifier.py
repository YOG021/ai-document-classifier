import re
from typing import List, Dict, Any, Tuple
from .models import ClassificationResult, DocumentType

ANCHOR_DEFINITIONS: Dict[DocumentType, Dict[str, Any]] = {
    "aadhaar": {
        "title": "Aadhaar Card",
        "primary_keywords": [
            "UNIQUE IDENTIFICATION AUTHORITY OF INDIA",
            "GOVERNMENT OF INDIA",
            "UIDAI",
            "MERA AADHAAR, MERI PEHCHAN",
            "MERA AADHAAR",
            "MERI PEHCHAN",
            "BHARAT SARKAR",
        ],
        "secondary_keywords": [
            "AADHAAR",
            "ENROLMENT NO",
            "HELP@UIDAI.GOV.IN",
            "WWW.UIDAI.GOV.IN",
            "1947",
            "YEAR OF BIRTH",
            "DOB",
            "MALE",
            "FEMALE",
        ],
        "regex_patterns": [
            re.compile(r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b"),  # 12-digit spaced Aadhaar
        ],
        "min_score_threshold": 25,
    },
    "pan": {
        "title": "Permanent Account Number (PAN) Card",
        "primary_keywords": [
            "INCOME TAX DEPARTMENT",
            "GOVT. OF INDIA",
            "GOVERNMENT OF INDIA",
            "PERMANENT ACCOUNT NUMBER CARD",
            "PERMANENT ACCOUNT NUMBER",
            "INAYAKAR VIBHAG",
        ],
        "secondary_keywords": [
            "FATHER'S NAME",
            "DATE OF BIRTH",
            "SIGNATURE",
            "CARDHOLDER",
        ],
        "regex_patterns": [
            re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),  # 10-char PAN regex
        ],
        "min_score_threshold": 30,
    },
    "ssc": {
        "title": "SSC Marks Card (10th Standard)",
        "primary_keywords": [
            "BOARD OF SECONDARY EDUCATION",
            "SECONDARY SCHOOL CERTIFICATE",
            "MEMORANDUM OF MARKS",
            "SSC",
            "CENTRAL BOARD OF SECONDARY EDUCATION",
            "CBSE",
            "HIGH SCHOOL CERTIFICATE",
            "MATRICULATION",
        ],
        "secondary_keywords": [
            "HALL TICKET NO",
            "ROLL NO",
            "ROLL NUMBER",
            "MEDIUM OF INSTRUCTION",
            "IDENTIFICATION MARKS",
            "GRAND TOTAL",
            "GRADE POINT",
            "GPA",
            "CGPA",
            "MAX MARKS",
            "MARKS OBTAINED",
            "RESULT",
            "DIVISION",
            "PASSED",
            "MOTHER'S NAME",
        ],
        "regex_patterns": [
            re.compile(r"\b(?:ROLL|HALL\s*TICKET)\s*(?:NO|NUMBER)?[:.\s]*[A-Z0-9-]+\b", re.IGNORECASE),
            re.compile(r"\b(?:PASSED|FAILED|DISTINCTION|FIRST\s+CLASS)\b", re.IGNORECASE),
        ],
        "min_score_threshold": 25,
    },
    "passport": {
        "title": "Republic of India Passport",
        "primary_keywords": [
            "REPUBLIC OF INDIA",
            "PASSPORT",
            "PASSPORT NO",
            "PASSAM",
            "INDIAN UNION",
            "MINISTRY OF EXTERNAL AFFAIRS",
        ],
        "secondary_keywords": [
            "SURNAME",
            "GIVEN NAME",
            "NATIONALITY",
            "PLACE OF BIRTH",
            "PLACE OF ISSUE",
            "DATE OF ISSUE",
            "DATE OF EXPIRY",
            "TYPE P",
            "CODE IND",
        ],
        "regex_patterns": [
            re.compile(r"P<IND[A-Z<]+"),  # MRZ Line 1 pattern
            re.compile(r"\b[A-Z][0-9]{7}\b"),  # Indian Passport Number format
        ],
        "min_score_threshold": 30,
    },
    "income_cert": {
        "title": "Income Certificate",
        "primary_keywords": [
            "REVENUE DEPARTMENT",
            "INCOME CERTIFICATE",
            "ANNUAL INCOME",
            "TAHSILDAR",
            "MEESEVA",
            "GOVERNMENT OF",
            "DISTRICT ADMINISTRATION",
        ],
        "secondary_keywords": [
            "G.O. MS",
            "G.O.MS.NO",
            "PER ANNUM",
            "FINANCIAL YEAR",
            "MANDAL",
            "TALUK",
            "VILLAGE",
            "DOOR NO",
            "CERTIFIED THAT",
            "FAMILY INCOME",
            "APPLICATION NO",
            "CERTIFICATE NO",
        ],
        "regex_patterns": [
            re.compile(r"G\.?O\.?\s*(?:MS|RT)?\.?\s*NO[:.\s]*[0-9/]+", re.IGNORECASE),
            re.compile(r"(?:RS\.?|INR|₹)\s*[0-9,]+(?:\s*/-)?", re.IGNORECASE),
            re.compile(r"\b(?:APPLICATION|CERTIFICATE)\s*(?:NO|NUMBER)[:.\s]*[A-Z0-9/-]+", re.IGNORECASE),
        ],
        "min_score_threshold": 25,
    },
}

def classify_document(raw_text: str, lines: List[str]) -> ClassificationResult:
    """Classifies document based on anchor keywords, regex patterns, and context signals."""
    normalized_text = raw_text.upper()
    
    scores: Dict[DocumentType, float] = {"aadhaar": 0, "pan": 0, "ssc": 0, "passport": 0, "income_cert": 0}
    matched_anchors_map: Dict[DocumentType, List[str]] = {k: [] for k in scores}
    secondary_signals_map: Dict[DocumentType, List[str]] = {k: [] for k in scores}

    for doc_type, config in ANCHOR_DEFINITIONS.items():
        # 1. Primary Keywords (Weight: 25 points each)
        for pk in config["primary_keywords"]:
            if pk in normalized_text:
                scores[doc_type] += 25
                matched_anchors_map[doc_type].append(f"Header/Keyword: '{pk}'")

        # 2. Secondary Keywords (Weight: 8 points each)
        for sk in config["secondary_keywords"]:
            if sk in normalized_text:
                scores[doc_type] += 8
                secondary_signals_map[doc_type].append(sk)

        # 3. Regex Patterns (Weight: 35 points each)
        for pattern in config["regex_patterns"]:
            matches = pattern.findall(raw_text)
            if matches:
                scores[doc_type] += 35
                matched_str = str(matches[0]) if len(str(matches[0])) < 30 else str(matches[0])[:30] + "..."
                matched_anchors_map[doc_type].append(f"Format Pattern: '{matched_str}'")

    # Document-specific discriminator bonuses/penalties
    # Check Aadhaar vs PAN
    pan_matches = re.findall(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", raw_text)
    if pan_matches and ("INCOME TAX" in normalized_text or "PERMANENT ACCOUNT NUMBER" in normalized_text):
        scores["pan"] += 40

    aadhaar_matches = re.findall(r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b", raw_text)
    if aadhaar_matches and ("UIDAI" in normalized_text or "AADHAAR" in normalized_text or "MERA AADHAAR" in normalized_text):
        scores["aadhaar"] += 40

    mrz_matches = re.findall(r"P<IND[A-Z0-9<]+", raw_text.replace(" ", ""))
    if mrz_matches or "PASSPORT" in normalized_text:
        if mrz_matches:
            scores["passport"] += 50

    if "TAHSILDAR" in normalized_text and ("ANNUAL INCOME" in normalized_text or "INCOME CERTIFICATE" in normalized_text):
        scores["income_cert"] += 45

    if "BOARD OF SECONDARY EDUCATION" in normalized_text or "SECONDARY SCHOOL CERTIFICATE" in normalized_text:
        scores["ssc"] += 45

    # Determine highest scoring document
    best_type: DocumentType = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]
    threshold = ANCHOR_DEFINITIONS[best_type]["min_score_threshold"]

    if best_score < threshold:
        return ClassificationResult(
            doc_type="unknown",
            document_title="Unrecognized Document",
            confidence=0.0,
            matched_anchors=[],
            secondary_signals=[],
            reasoning="Document did not match primary anchor keywords or format patterns for Aadhaar, PAN, SSC, Passport, or Income Certificate.",
        )

    # Calculate normalized confidence percentage (0.0 to 1.0)
    confidence = min(0.99, max(0.50, best_score / 120.0))

    reasoning = (
        f"Classified as {ANCHOR_DEFINITIONS[best_type]['title']} with score {best_score:.1f}. "
        f"Matched {len(matched_anchors_map[best_type])} classification anchors: "
        f"{', '.join(matched_anchors_map[best_type][:3])}."
    )

    return ClassificationResult(
        doc_type=best_type,
        document_title=ANCHOR_DEFINITIONS[best_type]["title"],
        confidence=round(confidence, 2),
        matched_anchors=matched_anchors_map[best_type],
        secondary_signals=list(set(secondary_signals_map[best_type]))[:8],
        reasoning=reasoning,
    )
