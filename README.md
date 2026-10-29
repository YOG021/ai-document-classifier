# Indian Document Classification & Intelligent OCR Extraction System

An intelligent document processing engine built with **FastAPI**, **PaddleOCR**, **OpenCV**, and Python pattern matching rules. The system classifies and extracts structured JSON fields from 5 major Indian documents:
1. **Aadhaar Card**
2. **PAN Card**
3. **SSC Marks Card (10th Standard)**
4. **Passport (Republic of India)**
5. **Income Certificate**

---

## 📚 Libraries Used and Why They Were Used

| Library | Version | Why It Was Used |
| :--- | :--- | :--- |
| **`paddleocr`** | `^3.7.0` | **State-of-the-Art OCR:** Performs text line detection, angle/orientation classification, and text recognition across low-resolution scans, multi-lingual scripts, and rotated mobile photos with high accuracy. |
| **`paddlepaddle`** | `^3.3.0` | **Deep Learning Framework:** Underpins PaddleOCR with native Apple Silicon / CPU runtime acceleration. |
| **`fastapi`** | `^0.110.0` | **High-Performance Async Backend:** Modern, production-ready web framework with automatic OpenAPI documentation, schema validation via Pydantic, and native async file streaming. |
| **`uvicorn`** | `^0.28.0` | **Lightning-fast ASGI Server:** Drives the asynchronous event loop for high-concurrency document requests. |
| **`pydantic`** | `^2.6.0` | **Strict Schema Validation & Serialization:** Enforces strict typing for classification results, document-specific fields, and API contracts. |
| **`pypdfium2`** | `^5.0.0` | **Self-Contained PDF Rendering:** Converts multi-page PDF documents into high-DPI PIL images without requiring external OS-level `poppler` or `pdftoppm` binaries. |
| **`opencv-contrib-python`** | `^4.10.0` | **Computer Vision & Feature Detection:** Detects QR codes (`QRCodeDetector`), locates passport/cardholder photos via Haar Cascades (`CascadeClassifier`), and isolates signature bounding regions. |
| **`pillow` (PIL)** | `^10.0.0` | **Image Manipulation & Enhancement:** Used for image loading, contrast enhancement, scaling, format conversions, and generating synthetic test documents. |
| **`numpy`** | `^1.24.0` | **Vectorized Array Operations:** Intermediary matrix representations between PIL, OpenCV, and PaddleOCR pipelines. |

---

## 🏗️ Architecture & Pipeline Flow

```
[ Upload PDF / Image / 1-Click Sample ]
                  │
                  ▼
┌──────────────────────────────────────────┐
│ Step 1: Preprocessing & Rendering        │
│ • pypdfium2 (PDF to 250 DPI PIL images)  │
│ • PIL Contrast enhancement               │
│ • OpenCV QR Code & Face Detection        │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│ Step 2: PaddleOCR Execution              │
│ • Document unwarping & orientation fix   │
│ • Text bounding polygon detection        │
│ • Optical text recognition (en)          │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│ Step 3: Document Classification Scoring  │
│ • Primary header/emblem anchors (UIDAI,  │
│   Income Tax, Board of Sec. Ed, etc.)    │
│ • Format regex (PAN, Aadhaar UID, MRZ)   │
│ • Confidence score calculation (0 - 100%)│
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│ Step 4: Document-Specific Extraction     │
│ • Aadhaar: UID, VID, Name, DOB, Address  │
│ • PAN: 10-char PAN, Father, Name, DOB    │
│ • SSC: Hall Ticket, Subjects, CGPA, Div  │
│ • Passport: ICAO Doc 9303 MRZ parsing    │
│ • Income: G.O. Ms., Tahsildar, Amount    │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│ Step 5: Validation & Human Review UI     │
│ • Entity code & checksum checks          │
│ • Side-by-side preview & field editor    │
│ • Real-time clean JSON export & download │
└──────────────────────────────────────────┘
```

---

## 🎯 Classification Anchors & Extraction Field Specification

### 1. Aadhaar Card
- **Classification Anchors:**
  - *Header / Keywords:* `"Government of India"`, `"UIDAI"`, `"Unique Identification Authority of India"`, `"Mera Aadhaar, Meri Pehchan"`
  - *UID Format:* 12-digit number (Pattern: `XXXX XXXX XXXX`)
- **Extraction Fields:**
  - `aadhaar_number` (12 digits)
  - `vid` (Virtual ID, 16 digits – if present)
  - `name` (Full Name)
  - `dob_or_yob` (Date of Birth DD/MM/YYYY or Year of Birth)
  - `gender` (Male / Female / Transgender)
  - `relation_type` (C/O, S/O, D/O, W/O)
  - `guardian_name` (Guardian/Relative Name)
  - `address` (including PIN code)
  - `photo_detected` (Face detection via OpenCV)
  - `qr_detected` (Decoded QR pattern)

---

### 2. PAN Card
- **Classification Anchors:**
  - *Header / Keywords:* `"Income Tax Department"`, `"Govt. of India"`, `"Permanent Account Number Card"`
  - *PAN Format:* 10-character alphanumeric regex (`[A-Z]{5}[0-9]{4}[A-Z]{1}`)
- **Extraction Fields:**
  - `pan_number` (10 alphanumeric characters)
  - `name` (Cardholder Name)
  - `fathers_name` (Father's Name)
  - `dob` (Date of Birth DD/MM/YYYY)
  - `photo_detected` (Cardholder photo flag)
  - `signature_detected` (Signature box heuristic)
  - `qr_detected` (QR code detection)

---

### 3. SSC Marks Card (10th Standard)
- **Classification Anchors:**
  - *Header / Keywords:* `"Board of Secondary Education"`, `"Secondary School Certificate"`, `"SSC"`, `"Memorandum of Marks"`
  - *Structure:* Subject table with Maximum Marks, Marks Obtained, and Letter Grades
- **Extraction Fields:**
  - `candidate_name`
  - `fathers_name`
  - `mothers_name`
  - `roll_number` (Roll Number / Hall Ticket Number)
  - `dob` (Date of Birth)
  - `school_name` (School / Institution Name)
  - `passing_year_month` (Month & Year of Examination / Passing)
  - `medium` (English, Telugu, Hindi, etc.)
  - `identification_marks` (Personal physical marks / moles)
  - `subject_marks` (Subject-wise Marks/Grades table)
  - `total_result` (Total Marks / CGPA / Result: PASS / Division)

---

### 4. Passport (Republic of India)
- **Classification Anchors:**
  - *Header / Keywords:* `"Republic of India"`, `"Passport"`, `"Passport No"`, `"Passam"`
  - *MRZ Zone:* Machine Readable Zone lines at the bottom: `P<IND...`
- **Extraction Fields:**
  - `passport_number` (1 letter followed by 7 digits, e.g. `Z8492015`)
  - `full_name`, `given_name`, `surname`
  - `nationality` (e.g. `INDIAN`)
  - `dob` (Date of Birth)
  - `gender` (`M` / `F`)
  - `place_of_birth`
  - `place_of_issue`
  - `date_of_issue`
  - `date_of_expiry`
  - `mrz_lines` (Parsed ICAO TD3 Lines 1 & 2)
  - `photo_detected`

---

### 5. Income Certificate
- **Classification Anchors:**
  - *Header / Keywords:* `"Revenue Department"`, `"Income Certificate"`, `"Annual Income"`, `"Tahsildar"`, `"MeeSeva"` / State Portal
  - *Format:* Certified declaration text, government order reference, state authority seal
- **Extraction Fields:**
  - `application_number` (Application / Certificate Number)
  - `go_ms_no` (Government Order Reference: G.O. Ms. No.)
  - `date_of_issue` (Date of Application / Date of Issue)
  - `applicant_name`
  - `father_or_guardian_name` (Father's / Husband's / Guardian's Name)
  - `annual_income` (in numbers and words, e.g., `₹ 75,000/- Seventy Five Thousand`)
  - `financial_year` (Financial Year / Validity Period)
  - `address` (House / Door No, Street, Village/Town)
  - `mandal_district` (Mandal / Taluk & District)
  - `issuing_authority` (Designation & Digital Signature: Tahsildar)

---

## 🚀 Running the Project

### 1. Start the FastAPI Server
From the project root:
```bash
/opt/miniconda3/envs/mlenv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access the Application
- **Interactive Web App & Review Dashboard:** [http://localhost:8000/](http://localhost:8000/)
- **Swagger / OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Spec:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing with 1-Click Synthetic Samples
The frontend contains built-in 1-click test sample buttons for all 5 document types:
- Click **"Aadhaar Card"** to test Aadhaar classification, 12-digit UID extraction, and QR/Photo detection.
- Click **"PAN Card"** to test PAN regex format verification and Father's Name parsing.
- Click **"SSC 10th Card"** to test subject marks tabular parsing, Hall Ticket No, and CGPA extraction.
- Click **"Passport"** to test ICAO Doc 9303 MRZ dual-line decoding.
- Click **"Income Certificate"** to test G.O. Ms. No, annual income in numbers & words, and Tahsildar seal recognition.
