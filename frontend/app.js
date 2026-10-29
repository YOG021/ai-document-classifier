// DocuSense AI — Frontend Controller
const API_BASE = window.location.origin;

let currentResponse = null;
let currentExtractedData = {};

// ── DOM refs ──
const dropZone      = document.getElementById('dropZone');
const fileInput     = document.getElementById('fileInput');
const btnBrowse     = document.getElementById('btnBrowse');
const stepper       = document.getElementById('stepper');
const resultCard    = document.getElementById('resultCard');
const previewImg    = document.getElementById('previewImg');
const rawOcrText    = document.getElementById('rawOcrText');
const ocrCount      = document.getElementById('ocrCount');
const fieldsForm    = document.getElementById('fieldsForm');
const jsonCode      = document.getElementById('jsonCode');
const toast         = document.getElementById('toast');

// Result card elements
const rDocBadge   = document.getElementById('rDocBadge');
const rTitle      = document.getElementById('rTitle');
const rReasoning  = document.getElementById('rReasoning');
const confFill    = document.getElementById('confFill');
const confVal     = document.getElementById('confVal');
const rTime       = document.getElementById('rTime');
const rStatus     = document.getElementById('rStatus');
const anchorTags  = document.getElementById('anchorTags');
const resultAlert = document.getElementById('resultAlert');
const alertItems  = document.getElementById('alertItems');

// Modals
const previewModal = document.getElementById('previewModal');
const fieldsModal  = document.getElementById('fieldsModal');

// Modal tabs — Preview
const mtabImg  = document.getElementById('mtabImg');
const mtabOcr  = document.getElementById('mtabOcr');
const mpImage  = document.getElementById('mpImage');
const mpOcr    = document.getElementById('mpOcr');

// Modal tabs — Fields
const mtabForm = document.getElementById('mtabForm');
const mtabJson = document.getElementById('mtabJson');
const mfForm   = document.getElementById('mfForm');
const mfJson   = document.getElementById('mfJson');

// Action buttons (result card)
const btnOpenPreview = document.getElementById('btnOpenPreview');
const btnOpenFields  = document.getElementById('btnOpenFields');
const btnOpenJson    = document.getElementById('btnOpenJson');

// Modal close
const closePreview = document.getElementById('closePreview');
const closeFields  = document.getElementById('closeFields');

// Fields modal actions
const btnCopyJson     = document.getElementById('btnCopyJson');
const btnDownloadJson = document.getElementById('btnDownloadJson');
const btnResetForm    = document.getElementById('btnResetForm');
const btnSaveVerified = document.getElementById('btnSaveVerified');

// ── Field label map ──
const FIELD_LABELS = {
  aadhaar_number:          'Aadhaar Number (12 Digits)',
  vid:                     'Virtual ID (VID 16 Digits)',
  name:                    'Full Name',
  dob_or_yob:              'Date / Year of Birth',
  gender:                  'Gender',
  relation_type:           'Relationship (C/O, S/O, D/O)',
  guardian_name:           'Guardian / Relative Name',
  address:                 'Address',
  pin_code:                'PIN Code',
  photo_detected:          'Photo Detected (Vision)',
  qr_detected:             'QR Code Detected (Vision)',
  pan_number:              'PAN Number (10 Chars)',
  fathers_name:            "Father's Name",
  dob:                     'Date of Birth (DD/MM/YYYY)',
  signature_detected:      'Signature Detected',
  candidate_name:          'Candidate Name',
  mothers_name:            "Mother's Name",
  roll_number:             'Roll / Hall Ticket No',
  school_name:             'School / Institution Name',
  passing_year_month:      'Passing Month & Year',
  medium:                  'Medium of Instruction',
  identification_marks:    'Identification Marks',
  subject_marks:           'Subject-wise Marks',
  total_result:            'Total Result / CGPA',
  passport_number:         'Passport Number',
  given_name:              'Given Name(s)',
  surname:                 'Surname',
  full_name:               'Full Name',
  nationality:             'Nationality',
  place_of_birth:          'Place of Birth',
  place_of_issue:          'Place of Issue',
  date_of_issue:           'Date of Issue',
  date_of_expiry:          'Date of Expiry',
  mrz_lines:               'MRZ Machine Readable Zone',
  application_number:      'Application / Certificate No',
  go_ms_no:                'G.O. Ms. No Reference',
  applicant_name:          'Applicant Name',
  father_or_guardian_name: 'Father / Guardian Name',
  annual_income:           'Annual Income',
  financial_year:          'Financial Year',
  mandal_district:         'Mandal / District',
  issuing_authority:       'Issuing Authority',
};

const FULL_WIDTH_KEYS = new Set(['address', 'mrz_lines', 'subject_marks', 'annual_income', 'identification_marks']);

// ════════════════════════════════════════
// INIT
// ════════════════════════════════════════
function initApp() {
  // Upload
  btnBrowse.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault(); dropZone.classList.remove('dragover');
    if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', (e) => { if (e.target.files?.[0]) handleFileUpload(e.target.files[0]); });

  // Open modals
  btnOpenPreview.addEventListener('click', () => openModal(previewModal));
  btnOpenFields.addEventListener('click', () => { switchFieldsTab('form'); openModal(fieldsModal); });
  btnOpenJson.addEventListener('click', () => { switchFieldsTab('json'); openModal(fieldsModal); });

  // Close modals
  closePreview.addEventListener('click', () => closeModal(previewModal));
  closeFields.addEventListener('click', () => closeModal(fieldsModal));
  previewModal.addEventListener('click', (e) => { if (e.target === previewModal) closeModal(previewModal); });
  fieldsModal.addEventListener('click', (e) => { if (e.target === fieldsModal) closeModal(fieldsModal); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeModal(previewModal); closeModal(fieldsModal); } });

  // Preview modal tabs
  mtabImg.addEventListener('click', () => switchPreviewTab('img'));
  mtabOcr.addEventListener('click', () => switchPreviewTab('ocr'));

  // Fields modal tabs
  mtabForm.addEventListener('click', () => switchFieldsTab('form'));
  mtabJson.addEventListener('click', () => switchFieldsTab('json'));

  // JSON actions
  btnCopyJson.addEventListener('click', copyJson);
  btnDownloadJson.addEventListener('click', downloadJson);
  btnResetForm.addEventListener('click', resetForm);
  btnSaveVerified.addEventListener('click', () => { closeModal(fieldsModal); showToast('✓ Record confirmed & saved'); });
}

// ── Modal helpers ──
function openModal(overlay) { overlay.classList.add('open'); document.body.style.overflow = 'hidden'; }
function closeModal(overlay) { overlay.classList.remove('open'); document.body.style.overflow = ''; }

function switchPreviewTab(tab) {
  mtabImg.classList.toggle('active', tab === 'img');
  mtabOcr.classList.toggle('active', tab === 'ocr');
  mpImage.style.display = tab === 'img' ? 'flex' : 'none';
  mpOcr.style.display   = tab === 'ocr' ? 'block' : 'none';
}

function switchFieldsTab(tab) {
  mtabForm.classList.toggle('active', tab === 'form');
  mtabJson.classList.toggle('active', tab === 'json');
  mfForm.style.display = tab === 'form' ? 'block' : 'none';
  mfJson.style.display = tab === 'json' ? 'block' : 'none';
}

// ════════════════════════════════════════
// UPLOAD & SAMPLE
// ════════════════════════════════════════
async function handleFileUpload(file) {
  if (file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (e) => { previewImg.src = e.target.result; };
    reader.readAsDataURL(file);
  } else {
    previewImg.src = '';
  }
  showStepper();
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/api/process`, { method: 'POST', body: fd });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Processing failed'); }
    renderResults(await res.json());
  } catch (err) {
    showToast(`Error: ${err.message}`);
    hideStepper();
  }
}

async function handleSampleSelect(type) {
  showStepper();
  previewImg.src = `${API_BASE}/api/sample/${type}`;
  try {
    const res = await fetch(`${API_BASE}/api/process-sample/${type}`, { method: 'POST' });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Sample failed'); }
    renderResults(await res.json());
  } catch (err) {
    showToast(`Error: ${err.message}`);
    hideStepper();
  }
}

// ── Stepper ──
const STEPS = ['s1','s2','s3','s4','s5'];
function showStepper() {
  resultCard.style.display = 'none';
  stepper.style.display = 'flex';
  STEPS.forEach(id => document.getElementById(id)?.classList.remove('active','done'));
  STEPS.forEach((id, i) => {
    setTimeout(() => {
      const el = document.getElementById(id);
      if (!el) return;
      el.classList.add('active');
      if (i > 0) document.getElementById(STEPS[i-1])?.classList.replace('active','done');
    }, i * 280);
  });
}
function hideStepper() { stepper.style.display = 'none'; }

// ════════════════════════════════════════
// RENDER RESULTS
// ════════════════════════════════════════
function renderResults(res) {
  currentResponse = res;
  currentExtractedData = JSON.parse(JSON.stringify(res.extracted_data));

  hideStepper();

  const cls = res.classification;
  const pct = Math.round(cls.confidence * 100);

  // Result card top
  rDocBadge.textContent  = cls.doc_type.toUpperCase();
  rTitle.textContent     = cls.document_title;
  rReasoning.textContent = cls.reasoning;
  confFill.style.width   = `${pct}%`;
  confVal.textContent    = `${pct}%`;
  rTime.textContent      = `${res.processing_time_ms} ms`;

  const status = res.validation_status || 'valid';
  rStatus.className   = `status-pill ${status}`;
  rStatus.textContent = status.toUpperCase();

  // Anchors — only show Header/Keyword type, not raw Format Pattern values
  anchorTags.innerHTML = '';
  (cls.matched_anchors || []).filter(a => !a.startsWith('Format Pattern:')).forEach(a => {
    const s = document.createElement('span');
    s.className = 'anchor-tag';
    s.textContent = a;
    anchorTags.appendChild(s);
  });

  // Alert
  if (res.validation_issues?.length) {
    resultAlert.style.display = 'flex';
    alertItems.innerHTML = res.validation_issues.map(i => `<li>${i}</li>`).join('');
  } else {
    resultAlert.style.display = 'none';
  }

  // OCR / preview
  ocrCount.textContent = res.raw_ocr_lines.length;
  rawOcrText.textContent = res.raw_ocr_lines.join('\n');

  // Reset modal tabs to defaults
  switchPreviewTab('img');
  switchFieldsTab('form');

  // Build form & JSON
  buildForm(cls.doc_type, currentExtractedData);
  updateJson();

  // Show result card
  resultCard.style.display = 'flex';
  resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  showToast(`Classified: ${cls.document_title} · ${pct}% confidence`);
}

// ════════════════════════════════════════
// DYNAMIC FORM
// ════════════════════════════════════════
function buildForm(docType, data) {
  fieldsForm.innerHTML = '';
  // Ensure vid is never rendered or retained in UI
  delete currentExtractedData.vid;

  Object.entries(data).forEach(([key, val]) => {
    // Always hide VID field from form
    if (key === 'vid') return;

    // Skip fields with no value (null, undefined, empty string, empty array)
    if (val === null || val === undefined) return;
    if (typeof val === 'string' && val.trim() === '') return;
    if (Array.isArray(val) && val.length === 0) return;

    const label = FIELD_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const wrap = document.createElement('div');
    wrap.className = 'form-field' + (FULL_WIDTH_KEYS.has(key) ? ' full-width' : '');

    const lbl = document.createElement('label');
    lbl.textContent = label;
    wrap.appendChild(lbl);

    if (typeof val === 'boolean') {
      const row = document.createElement('div');
      row.className = 'bool-row';
      const chk = document.createElement('input');
      chk.type = 'checkbox'; chk.checked = val;
      chk.addEventListener('change', e => { currentExtractedData[key] = e.target.checked; updateJson(); });
      const span = document.createElement('span');
      span.textContent = val ? 'Detected by OpenCV / Paddle' : 'Not detected';
      row.appendChild(chk); row.appendChild(span);
      wrap.appendChild(row);

    } else if (Array.isArray(val) || FULL_WIDTH_KEYS.has(key)) {
      const ta = document.createElement('textarea');
      ta.rows = Array.isArray(val) && typeof val[0] === 'object' ? 5 : 2;
      ta.value = Array.isArray(val) ? JSON.stringify(val, null, 2) : (val || '');
      ta.addEventListener('input', e => {
        try { currentExtractedData[key] = Array.isArray(val) ? JSON.parse(e.target.value) : e.target.value; }
        catch (_) { currentExtractedData[key] = e.target.value; }
        updateJson();
      });
      wrap.appendChild(ta);

    } else {
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.value = val ?? '';
      inp.placeholder = label;
      inp.addEventListener('input', e => { currentExtractedData[key] = e.target.value; updateJson(); });
      wrap.appendChild(inp);
    }

    fieldsForm.appendChild(wrap);
  });
}

// ════════════════════════════════════════
// JSON
// ════════════════════════════════════════
function updateJson() {
  const out = {
    document_type:             currentResponse?.classification?.doc_type,
    document_title:            currentResponse?.classification?.document_title,
    classification_confidence: currentResponse?.classification?.confidence,
    verified_data:             currentExtractedData,
    validation_status:         currentResponse?.validation_status,
    timestamp:                 new Date().toISOString(),
  };
  jsonCode.textContent = JSON.stringify(out, null, 2);
}

function copyJson() {
  navigator.clipboard.writeText(jsonCode.textContent)
    .then(() => showToast('JSON copied to clipboard'));
}

function downloadJson() {
  const blob = new Blob([jsonCode.textContent], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `${currentResponse?.classification?.doc_type || 'doc'}_extracted.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('JSON downloaded');
}

function resetForm() {
  if (!currentResponse) return;
  currentExtractedData = JSON.parse(JSON.stringify(currentResponse.extracted_data));
  buildForm(currentResponse.classification.doc_type, currentExtractedData);
  updateJson();
  showToast('Form reset to original OCR values');
}

// ════════════════════════════════════════
// TOAST
// ════════════════════════════════════════
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}

// Boot
initApp();
