from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field

DocumentType = Literal["aadhaar", "pan", "ssc", "passport", "income_cert", "unknown"]

class ClassificationResult(BaseModel):
    doc_type: DocumentType
    document_title: str
    confidence: float
    matched_anchors: List[str] = Field(default_factory=list)
    secondary_signals: List[str] = Field(default_factory=list)
    reasoning: str

class AadhaarData(BaseModel):
    aadhaar_number: Optional[str] = Field(None, description="12-digit UID pattern XXXX XXXX XXXX")
    vid: Optional[str] = Field(None, description="Virtual ID 16 digits if present")
    name: Optional[str] = Field(None, description="Full Name")
    dob_or_yob: Optional[str] = Field(None, description="DOB (DD/MM/YYYY) or YOB (YYYY)")
    gender: Optional[str] = Field(None, description="Male / Female / Transgender")
    relation_type: Optional[str] = Field(None, description="C/O, S/O, D/O, W/O")
    guardian_name: Optional[str] = Field(None, description="Guardian/Relative Name")
    address: Optional[str] = Field(None, description="Address including PIN code")
    pin_code: Optional[str] = Field(None, description="6-digit PIN code")
    photo_detected: bool = Field(False, description="Whether photo region was detected")
    qr_detected: bool = Field(False, description="Whether QR Code was detected")

class PANData(BaseModel):
    pan_number: Optional[str] = Field(None, description="10-character alphanumeric PAN")
    name: Optional[str] = Field(None, description="Cardholder Name")
    fathers_name: Optional[str] = Field(None, description="Father's Name")
    dob: Optional[str] = Field(None, description="Date of Birth DD/MM/YYYY")
    photo_detected: bool = Field(False, description="Cardholder photo detected")
    signature_detected: bool = Field(False, description="Signature box detected")
    qr_detected: bool = Field(False, description="QR Code detected")

class SubjectMark(BaseModel):
    subject: str
    marks_obtained: Optional[str] = None
    max_marks: Optional[str] = None
    grade: Optional[str] = None

class SSCData(BaseModel):
    candidate_name: Optional[str] = Field(None, description="Candidate Name")
    fathers_name: Optional[str] = Field(None, description="Father's Name")
    mothers_name: Optional[str] = Field(None, description="Mother's Name")
    roll_number: Optional[str] = Field(None, description="Roll Number / Hall Ticket Number")
    dob: Optional[str] = Field(None, description="Date of Birth")
    school_name: Optional[str] = Field(None, description="School / Institution Name")
    passing_year_month: Optional[str] = Field(None, description="Month & Year of Examination / Passing")
    medium: Optional[str] = Field(None, description="Medium of Instruction (English, Telugu, Hindi, etc.)")
    identification_marks: List[str] = Field(default_factory=list, description="Moles / personal physical marks")
    subject_marks: List[SubjectMark] = Field(default_factory=list, description="Subject-wise Marks/Grades")
    total_result: Optional[str] = Field(None, description="Total Marks / CGPA / Result (PASS/FAIL/Division)")

class PassportData(BaseModel):
    passport_number: Optional[str] = Field(None, description="Passport Number (Letter + 7 digits)")
    full_name: Optional[str] = Field(None, description="Full Name")
    given_name: Optional[str] = Field(None, description="Given Name(s)")
    surname: Optional[str] = Field(None, description="Surname")
    nationality: Optional[str] = Field(None, description="Nationality (e.g. INDIAN)")
    dob: Optional[str] = Field(None, description="Date of Birth")
    gender: Optional[str] = Field(None, description="M / F")
    place_of_birth: Optional[str] = Field(None, description="Place of Birth")
    place_of_issue: Optional[str] = Field(None, description="Place of Issue")
    date_of_issue: Optional[str] = Field(None, description="Date of Issue")
    date_of_expiry: Optional[str] = Field(None, description="Date of Expiry")
    mrz_lines: List[str] = Field(default_factory=list, description="Machine Readable Zone lines")
    photo_detected: bool = Field(False, description="Passport Photo detected")

class IncomeCertData(BaseModel):
    application_number: Optional[str] = Field(None, description="Application / Certificate Number")
    go_ms_no: Optional[str] = Field(None, description="Government Order Reference (G.O. Ms. No.)")
    date_of_issue: Optional[str] = Field(None, description="Date of Application / Date of Issue")
    applicant_name: Optional[str] = Field(None, description="Applicant Name")
    father_or_guardian_name: Optional[str] = Field(None, description="Father's / Husband's / Guardian's Name")
    annual_income: Optional[str] = Field(None, description="Annual Income in numbers and words")
    financial_year: Optional[str] = Field(None, description="Financial Year / Validity Period")
    address: Optional[str] = Field(None, description="House/Door No, Street, Village/Town")
    mandal_district: Optional[str] = Field(None, description="Mandal / Taluk & District")
    issuing_authority: Optional[str] = Field(None, description="Issuing Authority Designation & Seal")

class DocumentProcessResponse(BaseModel):
    filename: str
    page_count: int
    classification: ClassificationResult
    extracted_data: Dict[str, Any]
    validation_status: Literal["valid", "warning", "invalid"]
    validation_issues: List[str] = Field(default_factory=list)
    raw_ocr_lines: List[str] = Field(default_factory=list)
    processing_time_ms: float
