import io
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import pypdfium2 as pdfium
from typing import List, Dict, Any, Tuple

# Global PaddleOCR singleton instance
_ocr_instance = None
_face_cascade = None

def get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if os.path.exists(cascade_path):
            _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade

def get_ocr_engine():
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        # Initialize PaddleOCR with orientation classification enabled
        _ocr_instance = PaddleOCR(
            use_textline_orientation=True,
            lang="en"
        )
    return _ocr_instance

class DocumentPage:
    def __init__(self, image: Image.Image, page_num: int = 1):
        self.image = image
        self.page_num = page_num
        self.cv_image = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        self.gray = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)

    def detect_qr(self) -> Tuple[bool, List[str]]:
        """Detect QR codes using OpenCV QRCodeDetector"""
        try:
            detector = cv2.QRCodeDetector()
            retval, decoded_info, points, _ = detector.detectAndDecodeMulti(self.cv_image)
            if retval and decoded_info:
                valid_qrs = [q for q in decoded_info if q.strip()]
                return (True if (points is not None and len(points) > 0) else False, valid_qrs)
            # Fallback single QR check
            val, pts, _ = detector.detectAndDecode(self.gray)
            if pts is not None and len(pts) > 0:
                return (True, [val] if val else ["QR_DETECTED"])
        except Exception:
            pass
        return (False, [])

    def detect_face(self) -> bool:
        """Detect human face (photo) using Haar Cascade"""
        try:
            cascade = get_face_cascade()
            if cascade is not None:
                # Resize for fast face detection
                h, w = self.gray.shape[:2]
                scale = 800.0 / max(h, w) if max(h, w) > 800 else 1.0
                small = cv2.resize(self.gray, (int(w * scale), int(h * scale))) if scale != 1.0 else self.gray
                faces = cascade.detectMultiScale(small, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                return len(faces) > 0
        except Exception:
            pass
        return False

    def detect_signature_region(self) -> bool:
        """Heuristic for detecting signature box / hand-drawn stroke signatures"""
        try:
            # Check lower half of document for signature-like contour clusters
            h, w = self.gray.shape[:2]
            lower_region = self.gray[int(h * 0.4):, :]
            blurred = cv2.GaussianBlur(lower_region, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            sig_candidates = 0
            for cnt in contours:
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = cw / float(ch) if ch > 0 else 0
                if 2.0 < aspect_ratio < 10.0 and 40 < cw < int(w * 0.6) and 15 < ch < 120:
                    sig_candidates += 1
            return sig_candidates > 0
        except Exception:
            return False

def preprocess_and_load_file(file_bytes: bytes, filename: str) -> List[DocumentPage]:
    """Converts uploaded image or PDF into a list of preprocessed DocumentPage objects"""
    pages: List[DocumentPage] = []
    lower_fn = filename.lower()
    
    if lower_fn.endswith(".pdf"):
        # Use pypdfium2 for robust PDF rendering without system poppler requirement
        pdf = pdfium.PdfDocument(file_bytes)
        for i, page in enumerate(pdf):
            # Render page at 200 DPI (scale ~2.77)
            bitmap = page.render(scale=2.5)
            pil_img = bitmap.to_pil()
            pages.append(DocumentPage(pil_img, page_num=i + 1))
    else:
        # Load image via PIL
        pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        # Enhance slight contrast if needed
        enhancer = ImageEnhance.Contrast(pil_img)
        enhanced = enhancer.enhance(1.1)
        pages.append(DocumentPage(enhanced, page_num=1))

    return pages

def run_paddle_ocr(pages: List[DocumentPage]) -> Dict[str, Any]:
    """Runs PaddleOCR on each page and aggregates extracted text, boxes, QR and photo signals"""
    ocr = get_ocr_engine()
    all_lines: List[str] = []
    all_scores: List[float] = []
    all_boxes: List[Any] = []
    has_qr = False
    has_photo = False
    has_signature = False
    qr_payloads: List[str] = []

    for page in pages:
        # Check computer vision anchors
        page_has_qr, qr_texts = page.detect_qr()
        if page_has_qr:
            has_qr = True
            qr_payloads.extend(qr_texts)
        if page.detect_face():
            has_photo = True
        if page.detect_signature_region():
            has_signature = True

        # Run OCR
        np_img = np.array(page.image)
        try:
            # Try predict or ocr
            if hasattr(ocr, "predict"):
                results = ocr.predict(np_img)
            else:
                results = ocr.ocr(np_img)
        except Exception:
            results = ocr.ocr(np_img)

        if results:
            for item in results:
                # Check PaddleX 3.x OCRResult format
                if isinstance(item, dict) or hasattr(item, "__getitem__"):
                    if "rec_texts" in item:
                        rec_texts = item.get("rec_texts", [])
                        rec_scores = item.get("rec_scores", [])
                        rec_boxes = item.get("rec_boxes", [])
                        for t, s in zip(rec_texts, rec_scores):
                            t_clean = str(t).strip()
                            if t_clean:
                                all_lines.append(t_clean)
                                all_scores.append(float(s) if s is not None else 0.9)
                        if rec_boxes is not None:
                            all_boxes.extend(rec_boxes)
                        continue
                
                # Check legacy PaddleOCR format: [[[x1, y1]...], (text, score)]
                if isinstance(item, list):
                    for line_item in item:
                        if isinstance(line_item, (list, tuple)) and len(line_item) >= 2:
                            text_score = line_item[1]
                            if isinstance(text_score, (list, tuple)) and len(text_score) >= 1:
                                t = str(text_score[0]).strip()
                                s = float(text_score[1]) if len(text_score) > 1 else 0.9
                                if t:
                                    all_lines.append(t)
                                    all_scores.append(s)

    # Heuristic checks on text lines for QR, Photo, Signature if OCR recognized them directly
    text_corpus_upper = " ".join(all_lines).upper()
    if "SIGNATURE" in text_corpus_upper or "CARDHOLDER'S SIGNATURE" in text_corpus_upper:
        has_signature = True
    if "QR CODE" in text_corpus_upper or "SCAN QR" in text_corpus_upper:
        has_qr = True

    return {
        "lines": all_lines,
        "full_text": "\n".join(all_lines),
        "scores": all_scores,
        "avg_confidence": (sum(all_scores) / len(all_scores)) if all_scores else 0.0,
        "has_qr": has_qr,
        "qr_payloads": qr_payloads,
        "has_photo": has_photo,
        "has_signature": has_signature,
        "page_count": len(pages),
    }
