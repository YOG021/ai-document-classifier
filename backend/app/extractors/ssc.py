import re
from typing import List, Dict, Any
from ..models import SSCData, SubjectMark

COMMON_SUBJECTS = [
    "FIRST LANGUAGE", "SECOND LANGUAGE", "THIRD LANGUAGE", "ENGLISH", "HINDI",
    "TELUGU", "TAMIL", "KANNADA", "SANSKRIT", "MATHEMATICS", "MATHS",
    "GENERAL SCIENCE", "SCIENCE", "PHYSICAL SCIENCE", "NATURAL SCIENCE",
    "SOCIAL STUDIES", "SOCIAL SCIENCE"
]

def extract_ssc_data(lines: List[str], ocr_meta: Dict[str, Any]) -> Dict[str, Any]:
    full_text = "\n".join(lines)
    
    # 1. Roll Number / Hall Ticket Number
    roll_number = None
    roll_match = re.search(r"(?:Roll\s*(?:Number|No)|Hall\s*Ticket\s*(?:Number|No)|HT\s*NO)[:.\s-]*([A-Z0-9-]{5,30})\b", full_text, re.IGNORECASE)
    if roll_match:
        roll_number = roll_match.group(1).strip()
    else:
        for i, line in enumerate(lines):
            line_upper = line.upper()
            if any(k in line_upper for k in ["ROLL NO", "ROLL NUMBER", "HALL TICKET"]):
                parts = re.split(r"[:.-]", line, 1)
                if len(parts) > 1 and re.search(r"[A-Z0-9-]{5,20}", parts[1]):
                    roll_number = re.search(r"[A-Z0-9-]{5,20}", parts[1]).group(0).strip()
                    break
                elif i + 1 < len(lines) and re.match(r"^[A-Z0-9-]{5,20}$", lines[i + 1].strip()):
                    roll_number = lines[i + 1].strip()
                    break
        if not roll_number:
            r_gen = re.search(r"\b(\d{4}-SSC-\d{5,10}|\d{9,12})\b", full_text)
            if r_gen:
                roll_number = r_gen.group(1)

    # 2. Candidate Name
    BLOCKED_CANDIDATE_SUBSTRINGS = [
        "BOARD", "SECONDARY", "EDUCATION", "CERTIFICATE", "MEMORANDUM", "MARKS",
        "EXAMINATION", "PUBLIC", "GOVERNMENT", "DIRECTOR", "CONTROLLER", "SCHOOL",
        "HIGH SCHOOL", "HEADMASTER", "SECRETARY", "ROLL", "HALL TICKET", "FATHER",
        "MOTHER", "GUARDIAN", "DATE OF BIRTH", "DOB", "MEDIUM", "IDENTIFICATION",
        "SUBJECT", "GRADE", "DIVISION", "RESULT", "PASSED", "FAILED", "DISTINCTION",
        "TOTAL", "FIRST LANGUAGE", "SECOND LANGUAGE", "THIRD LANGUAGE", "MATHEMATICS",
        "SCIENCE", "SOCIAL", "YEAR", "MONTH"
    ]

    def is_valid_name_str(text: str) -> bool:
        if not text:
            return False
        clean = text.strip(" :.-,\t\n")
        if len(clean) < 3 or len(clean) > 45:
            return False
        if any(c.isdigit() for c in clean):
            return False
        if not all(c.isalpha() or c in " .'-" for c in clean):
            return False
        clean_upper = clean.upper()
        for b in BLOCKED_CANDIDATE_SUBSTRINGS:
            if b in clean_upper:
                return False
        words = [w for w in clean.split() if any(c.isalpha() for c in w)]
        if len(words) < 1 or len(words) > 6:
            return False
        return True

    candidate_name = None

    # Strategy 1: Certified that / This is to certify that pattern (standard on State Board SSC marks cards)
    cert_match = re.search(
        r"(?:THIS\s+IS\s+TO\s+CERTIFY\s+THAT|CERTIFIED\s+THAT|TO\s+CERTIFY\s+THAT)[:.\s]+([A-Za-z\s.]+?)(?=\s*(?:SON|DAUGHTER|BEARING|ROLL|FATHER|MOTHER|S/O|D/O|\n|$))",
        full_text,
        re.IGNORECASE
    )
    if cert_match and is_valid_name_str(cert_match.group(1)):
        candidate_name = cert_match.group(1).strip(" :.-")

    # Strategy 2: Explicit Candidate Name labels (regex on full_text)
    if not candidate_name:
        c_patterns = [
            r"(?:Candidate(?:'s)?\s*Name|Name\s*of\s*(?:the\s*)?Candidate|Student(?:'s)?\s*Name)[:.\s]+([A-Za-z\s.]+?)(?=\n|Father|Mother|Roll|DOB|School|$)",
            r"(?:^|\n)\s*(?:Name|Candidate)[:.\s]+([A-Za-z\s.]+?)(?=\n|Father|Mother|Roll|DOB|School|$)",
        ]
        for pat in c_patterns:
            m = re.search(pat, full_text, re.IGNORECASE)
            if m and is_valid_name_str(m.group(1)):
                candidate_name = m.group(1).strip(" :.-")
                break

    # Strategy 3: Line-by-line inspection (handles split labels where name is on the next line)
    if not candidate_name:
        label_keywords = [
            "CANDIDATE NAME", "CANDIDATE'S NAME", "CANDIDATES NAME",
            "NAME OF THE CANDIDATE", "NAME OF CANDIDATE",
            "STUDENT NAME", "STUDENT'S NAME", "STUDENTS NAME",
            "NAME OF THE STUDENT", "NAME OF STUDENT",
            "CERTIFIED THAT", "THIS IS TO CERTIFY THAT"
        ]
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_upper = line_clean.upper()
            for lk in label_keywords:
                if lk in line_upper:
                    idx = line_upper.find(lk) + len(lk)
                    orig_after = line_clean[idx:].strip(" :.-")
                    if is_valid_name_str(orig_after):
                        candidate_name = orig_after
                        break
                    if i + 1 < len(lines) and is_valid_name_str(lines[i + 1]):
                        candidate_name = lines[i + 1].strip(" :.-")
                        break
            if candidate_name:
                break

    # Strategy 4: Line starting with 'NAME :' or 'NAME:' or 'CANDIDATE :'
    if not candidate_name:
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_upper = line_clean.upper()
            if re.match(r"^(?:NAME|CANDIDATE)\s*[:.-]", line_upper):
                parts = re.split(r"[:.-]", line_clean, 1)
                if len(parts) > 1 and is_valid_name_str(parts[1]):
                    candidate_name = parts[1].strip(" :.-")
                    break
                if i + 1 < len(lines) and is_valid_name_str(lines[i + 1]):
                    candidate_name = lines[i + 1].strip(" :.-")
                    break

    # Strategy 5: Positional search right before Father's Name or Mother's Name
    if not candidate_name:
        parent_idx = -1
        for i, line in enumerate(lines):
            if re.search(r"(?:Father(?:'s)?\s*Name|Mother(?:'s)?\s*Name)", line, re.IGNORECASE):
                parent_idx = i
                break
        if parent_idx > 0:
            for i in range(parent_idx - 1, max(-1, parent_idx - 4), -1):
                if is_valid_name_str(lines[i]):
                    candidate_name = lines[i].strip(" :.-")
                    break

    # 3. Father's Name
    fathers_name = None
    f_match = re.search(r"(?:Father(?:'s)?\s*(?:/\s*Guardian(?:'s)?)?\s*Name|Father\s*Name)[:.\s]*([A-Za-z\s.]+?)(?=\n|Mother|Roll|DOB|School|$)", full_text, re.IGNORECASE)
    if f_match and is_valid_name_str(f_match.group(1)):
        fathers_name = f_match.group(1).strip(" :.-")
    else:
        for i, line in enumerate(lines):
            if "FATHER" in line.upper():
                parts = re.split(r"[:.-]", line, 1)
                if len(parts) > 1 and is_valid_name_str(parts[1]):
                    fathers_name = parts[1].strip(" :.-")
                    break
                elif i + 1 < len(lines) and is_valid_name_str(lines[i + 1]):
                    fathers_name = lines[i + 1].strip(" :.-")
                    break

    # 4. Mother's Name
    mothers_name = None
    m_match = re.search(r"(?:Mother(?:'s)?\s*Name|Mother\s*Name)[:.\s]*([A-Za-z\s.]+?)(?=\n|Father|Roll|DOB|School|$)", full_text, re.IGNORECASE)
    if m_match and is_valid_name_str(m_match.group(1)):
        mothers_name = m_match.group(1).strip(" :.-")
    else:
        for i, line in enumerate(lines):
            if "MOTHER" in line.upper():
                parts = re.split(r"[:.-]", line, 1)
                if len(parts) > 1 and is_valid_name_str(parts[1]):
                    mothers_name = parts[1].strip(" :.-")
                    break
                elif i + 1 < len(lines) and is_valid_name_str(lines[i + 1]):
                    mothers_name = lines[i + 1].strip(" :.-")
                    break

    # 5. Date of Birth
    dob = None
    dob_match = re.search(r"(?:DOB|Date\s*of\s*Birth)[:.\s]*(\d{2}[/-]\d{2}[/-]\d{4})", full_text, re.IGNORECASE)
    if not dob_match:
        dob_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b", full_text)
    if dob_match:
        dob = dob_match.group(1)

    # 6. School / Institution Name
    school_name = None
    school_match = re.search(r"(?:School\s*Name|Name\s*of\s*the\s*School|Institution\s*Name)[:.\s]*([A-Za-z0-9\s.,()-]+?)(?=\n|Month|Exam|Medium|$)", full_text, re.IGNORECASE)
    if school_match:
        school_name = school_match.group(1).strip()

    # 7. Month & Year of Examination / Passing
    passing_year_month = None
    pass_match = re.search(r"(?:Month\s*(?:&|and)\s*Year\s*(?:of\s*Exam)?|Exam\s*Month|Held\s*in|Passed\s*in)[:.\s]*([A-Za-z]+\s*[-–/]?\s*\d{4})", full_text, re.IGNORECASE)
    if pass_match:
        passing_year_month = pass_match.group(1).strip()
    else:
        # Check standard Month Year e.g. March 2022
        my_match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2}|19\d{2})\b", full_text, re.IGNORECASE)
        if my_match:
            passing_year_month = f"{my_match.group(1).capitalize()} {my_match.group(2)}"

    # 8. Medium of Instruction
    medium = None
    med_match = re.search(r"(?:Medium\s*of\s*Instruction|Medium)[:.\s]*([A-Za-z]+)", full_text, re.IGNORECASE)
    if med_match:
        medium = med_match.group(1).strip().capitalize()

    # 9. Identification Marks
    id_marks = []
    marks_matches = re.findall(r"(?:Identification\s*Marks?|1\.|2\.)[:.\s]*((?:A\s+mole|A\s+scar|Mole|Scar)[A-Za-z\s.]+?)(?=\n|2\.|Total|Grade|$)", full_text, re.IGNORECASE)
    for mm in marks_matches:
        cleaned_m = mm.strip(" .")
        if len(cleaned_m) > 3 and cleaned_m not in id_marks:
            id_marks.append(cleaned_m)

    # 10. Subject-wise Marks / Grades
    subject_marks: List[SubjectMark] = []
    for line in lines:
        line_upper = line.upper()
        for subj in COMMON_SUBJECTS:
            if subj in line_upper:
                grade_match = re.search(r"\b([A-D][1-2]|A\+|A|B\+|B|C|D|E|PASS|FAIL)\b", line_upper)
                numbers = re.findall(r"\b\d{1,3}\b", line)
                marks_obt = numbers[0] if numbers else None
                max_m = numbers[1] if len(numbers) > 1 else "100"
                grade = grade_match.group(1) if grade_match else None
                
                subject_marks.append(SubjectMark(
                    subject=subj.title(),
                    marks_obtained=marks_obt,
                    max_marks=max_m if marks_obt else None,
                    grade=grade
                ))
                break

    # 11. Total Marks / CGPA / Result
    total_result = None
    res_match = re.search(r"(?:Total\s*Marks|Grand\s*Total|CGPA|GPA|Result)[:.\s]*([A-Za-z0-9./\s|–-]+?)(?=\n|$)", full_text, re.IGNORECASE)
    if res_match:
        total_result = res_match.group(1).strip()
    elif re.search(r"\b(PASSED\s+IN\s+FIRST\s+DIVISION|FIRST\s+CLASS|DISTINCTION|PASSED)\b", full_text, re.IGNORECASE):
        div_m = re.search(r"\b(PASSED\s+IN\s+FIRST\s+DIVISION|FIRST\s+CLASS|DISTINCTION|PASSED)\b", full_text, re.IGNORECASE)
        if div_m:
            total_result = div_m.group(1).strip().title()

    model = SSCData(
        candidate_name=candidate_name,
        fathers_name=fathers_name,
        mothers_name=mothers_name,
        roll_number=roll_number,
        dob=dob,
        school_name=school_name,
        passing_year_month=passing_year_month,
        medium=medium,
        identification_marks=id_marks[:2],
        subject_marks=subject_marks,
        total_result=total_result,
    )
    return model.model_dump()
