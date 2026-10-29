import os
import io
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict

def get_font(size: int = 20, bold: bool = False):
    try:
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        if not os.path.exists(font_path):
            font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        return ImageFont.truetype(font_path, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.load_default()

def draw_qr_placeholder(draw: ImageDraw.ImageDraw, x: int, y: int, size: int):
    draw.rectangle([x, y, x + size, y + size], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    step = size // 8
    for ox, oy in [(x + 4, y + 4), (x + size - 3 * step, y + 4), (x + 4, y + size - 3 * step)]:
        draw.rectangle([ox, oy, ox + 2 * step, oy + 2 * step], fill=(0, 0, 0))
        draw.rectangle([ox + 4, oy + 4, ox + 2 * step - 4, oy + 2 * step - 4], fill=(255, 255, 255))
        draw.rectangle([ox + 7, oy + 7, ox + 2 * step - 7, oy + 2 * step - 7], fill=(0, 0, 0))
    np.random.seed(42)
    for r in range(2, 6):
        for c in range(2, 6):
            if np.random.rand() > 0.4:
                draw.rectangle([x + c * step, y + r * step, x + (c + 1) * step - 2, y + (r + 1) * step - 2], fill=(0, 0, 0))

def draw_face_placeholder(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    draw.rectangle([x, y, x + w, y + h], fill=(235, 240, 245), outline=(120, 130, 140), width=2)
    head_cx = x + w // 2
    head_cy = y + int(h * 0.38)
    head_r = int(w * 0.22)
    draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], fill=(160, 175, 190))
    draw.chord([x + int(w * 0.15), y + int(h * 0.55), x + int(w * 0.85), y + int(h * 1.1)], start=180, end=360, fill=(100, 120, 140))

def generate_aadhaar_sample() -> Image.Image:
    w, h = 900, 560
    img = Image.new("RGB", (w, h), (252, 253, 255))
    draw = ImageDraw.ImageDraw(img)

    draw.rectangle([0, 0, w, 22], fill=(225, 105, 40))
    draw.rectangle([0, h - 22, w, h], fill=(30, 130, 60))

    f_head = get_font(22, bold=True)
    f_sub = get_font(16, bold=False)
    f_bold = get_font(18, bold=True)
    f_text = get_font(17, bold=False)
    f_uid = get_font(30, bold=True)

    draw.text((120, 35), "GOVERNMENT OF INDIA", fill=(20, 20, 20), font=f_head)
    draw.text((120, 65), "UNIQUE IDENTIFICATION AUTHORITY OF INDIA (UIDAI)", fill=(60, 60, 60), font=f_sub)
    draw.text((120, 90), "Mera Aadhaar, Meri Pehchan", fill=(180, 50, 30), font=f_bold)

    draw_face_placeholder(draw, 50, 135, 160, 200)
    draw_qr_placeholder(draw, 700, 135, 150)

    draw.text((240, 145), "Rahul Sharma", fill=(10, 10, 10), font=f_bold)
    draw.text((240, 180), "DOB: 15/08/1995", fill=(30, 30, 30), font=f_text)
    draw.text((240, 210), "Gender: Male", fill=(30, 30, 30), font=f_text)
    draw.text((240, 240), "C/O: Ramesh Sharma", fill=(30, 30, 30), font=f_text)
    draw.text((240, 270), "Address: H.No 4-52/1, Gandhi Nagar, Hyderabad - 500034", fill=(40, 40, 40), font=f_text)

    draw.line([50, 370, 850, 370], fill=(200, 200, 200), width=1)
    draw.text((270, 395), "5482 9102 3847", fill=(180, 20, 20), font=f_uid)
    draw.text((285, 445), "VID : 9123 4567 8901 2345", fill=(70, 70, 70), font=f_text)
    draw.text((310, 485), "www.uidai.gov.in | Help@uidai.gov.in | 1947", fill=(100, 100, 100), font=f_sub)

    return img

def generate_pan_sample() -> Image.Image:
    w, h = 900, 560
    img = Image.new("RGB", (w, h), (242, 246, 252))
    draw = ImageDraw.ImageDraw(img)

    draw.rectangle([0, 0, w, 18], fill=(35, 75, 135))

    f_head = get_font(21, bold=True)
    f_sub = get_font(18, bold=True)
    f_label = get_font(14, bold=False)
    f_val = get_font(18, bold=True)
    f_pan = get_font(28, bold=True)

    draw.text((50, 32), "INCOME TAX DEPARTMENT", fill=(15, 30, 70), font=f_head)
    draw.text((650, 32), "GOVT. OF INDIA", fill=(15, 30, 70), font=f_head)
    draw.text((220, 75), "PERMANENT ACCOUNT NUMBER CARD", fill=(170, 30, 20), font=f_sub)

    draw_face_placeholder(draw, 50, 130, 150, 190)
    draw_qr_placeholder(draw, 690, 130, 150)

    draw.text((240, 135), "Name / नाम", fill=(100, 100, 100), font=f_label)
    draw.text((240, 155), "PRIYA VERMA", fill=(10, 10, 10), font=f_val)

    draw.text((240, 195), "Father's Name / पिता का नाम", fill=(100, 100, 100), font=f_label)
    draw.text((240, 215), "ANIL VERMA", fill=(10, 10, 10), font=f_val)

    draw.text((240, 255), "Date of Birth / जन्म की तारीख", fill=(100, 100, 100), font=f_label)
    draw.text((240, 275), "22/11/1992", fill=(10, 10, 10), font=f_val)

    draw.line([50, 345, 850, 345], fill=(210, 215, 225), width=2)

    draw.text((50, 370), "Permanent Account Number :", fill=(80, 80, 80), font=f_sub)
    draw.text((430, 365), "ABCPE1234F", fill=(10, 25, 80), font=f_pan)

    # Signature box
    draw.rectangle([500, 430, 800, 495], fill=(255, 255, 255), outline=(150, 150, 150), width=1)
    draw.text((560, 445), "Priya Verma", fill=(20, 30, 80), font=get_font(22, bold=False))
    draw.text((540, 505), "Cardholder's Signature", fill=(110, 110, 110), font=f_label)

    return img

def generate_ssc_sample() -> Image.Image:
    w, h = 900, 850
    img = Image.new("RGB", (w, h), (255, 254, 250))
    draw = ImageDraw.ImageDraw(img)

    draw.rectangle([15, 15, w - 15, h - 15], outline=(160, 130, 60), width=3)
    draw.rectangle([22, 22, w - 22, h - 22], outline=(190, 160, 90), width=1)

    f_title = get_font(22, bold=True)
    f_sub = get_font(18, bold=True)
    f_label = get_font(15, bold=False)
    f_val = get_font(16, bold=True)

    draw.text((210, 40), "BOARD OF SECONDARY EDUCATION", fill=(120, 40, 20), font=f_title)
    draw.text((150, 75), "SECONDARY SCHOOL CERTIFICATE (SSC) EXAMINATION", fill=(20, 20, 20), font=f_sub)
    draw.text((300, 105), "MEMORANDUM OF MARKS", fill=(160, 90, 20), font=f_sub)

    draw.text((60, 150), "Roll Number : 2022-SSC-984321", fill=(10, 10, 10), font=f_val)
    draw.text((60, 185), "Candidate Name : VIKRAM ADITYA", fill=(10, 10, 10), font=f_val)
    draw.text((60, 220), "Father's Name : SUBRAHMANYAM ADITYA", fill=(10, 10, 10), font=f_val)
    draw.text((520, 220), "Mother's Name : LAKSHMI ADITYA", fill=(10, 10, 10), font=f_val)

    draw.text((60, 255), "Date of Birth : 18/06/2006", fill=(10, 10, 10), font=f_val)
    draw.text((520, 255), "Medium : English", fill=(10, 10, 10), font=f_val)

    draw.text((60, 290), "School Name : ST. XAVIER HIGH SCHOOL, HYDERABAD", fill=(10, 10, 10), font=f_val)
    draw.text((60, 325), "Month and Year : March 2022", fill=(10, 10, 10), font=f_val)

    draw.text((60, 360), "Identification Marks : 1. A mole on the right cheek", fill=(20, 20, 20), font=f_val)
    draw.text((60, 385), "2. A scar on left forehead", fill=(20, 20, 20), font=f_val)

    # Subject table
    table_y = 430
    draw.rectangle([50, table_y, 850, table_y + 35], fill=(235, 235, 240), outline=(100, 100, 100))
    draw.text((70, table_y + 8), "Subject Name", fill=(0, 0, 0), font=f_val)
    draw.text((450, table_y + 8), "Max Marks", fill=(0, 0, 0), font=f_val)
    draw.text((600, table_y + 8), "Marks Obtained", fill=(0, 0, 0), font=f_val)
    draw.text((760, table_y + 8), "Grade", fill=(0, 0, 0), font=f_val)

    rows = [
        ("FIRST LANGUAGE (ENGLISH)", "100", "92", "A1"),
        ("SECOND LANGUAGE (HINDI)", "100", "88", "A2"),
        ("MATHEMATICS", "100", "95", "A1"),
        ("GENERAL SCIENCE", "100", "90", "A1"),
        ("SOCIAL STUDIES", "100", "89", "A2"),
    ]
    cur_y = table_y + 35
    for subj, mx, obt, grd in rows:
        draw.rectangle([50, cur_y, 850, cur_y + 35], outline=(180, 180, 180))
        draw.text((70, cur_y + 8), subj, fill=(30, 30, 30), font=f_label)
        draw.text((480, cur_y + 8), mx, fill=(30, 30, 30), font=f_label)
        draw.text((630, cur_y + 8), obt, fill=(10, 10, 10), font=f_val)
        draw.text((770, cur_y + 8), grd, fill=(10, 80, 20), font=f_val)
        cur_y += 35

    draw.rectangle([50, cur_y, 850, cur_y + 40], fill=(245, 248, 255), outline=(100, 100, 100))
    draw.text((70, cur_y + 10), "Grand Total: 454 / 500  |  CGPA: 9.6", fill=(0, 0, 0), font=f_val)
    draw.text((540, cur_y + 10), "Result: PASSED IN FIRST DIVISION", fill=(20, 110, 30), font=f_val)

    return img

def generate_passport_sample() -> Image.Image:
    w, h = 900, 620
    img = Image.new("RGB", (w, h), (247, 248, 252))
    draw = ImageDraw.ImageDraw(img)

    f_title = get_font(22, bold=True)
    f_sub = get_font(16, bold=False)
    f_label = get_font(13, bold=False)
    f_val = get_font(16, bold=True)
    f_mrz = get_font(17, bold=True)

    draw.text((320, 25), "REPUBLIC OF INDIA", fill=(10, 20, 60), font=f_title)
    draw.text((400, 55), "PASSPORT", fill=(120, 30, 20), font=f_title)

    draw_face_placeholder(draw, 50, 100, 160, 200)

    draw.text((250, 100), "Passport No : Z8492015", fill=(10, 15, 80), font=get_font(20, bold=True))
    draw.text((250, 140), "Surname : KUMAR", fill=(10, 10, 10), font=f_val)
    draw.text((250, 180), "Given Name : ARJUN", fill=(10, 10, 10), font=f_val)
    draw.text((250, 220), "Nationality : INDIAN", fill=(10, 10, 10), font=f_val)
    draw.text((540, 220), "Sex : M", fill=(10, 10, 10), font=f_val)
    draw.text((250, 260), "Date of Birth : 10/04/1990", fill=(10, 10, 10), font=f_val)
    draw.text((540, 260), "Place of Birth : DELHI", fill=(10, 10, 10), font=f_val)
    draw.text((250, 300), "Date of Issue : 14/02/2020", fill=(10, 10, 10), font=f_val)
    draw.text((540, 300), "Place of Issue : DELHI", fill=(10, 10, 10), font=f_val)
    draw.text((250, 340), "Date of Expiry : 13/02/2030", fill=(10, 10, 10), font=f_val)

    # Machine Readable Zone
    draw.line([40, 440, 860, 440], fill=(180, 180, 180), width=2)
    draw.rectangle([40, 460, 860, 560], fill=(240, 240, 240), outline=(150, 150, 150))
    draw.text((55, 475), "P<INDKUMAR<<ARJUN<<<<<<<<<<<<<<<<<<<<<<<<<<<", fill=(0, 0, 0), font=f_mrz)
    draw.text((55, 515), "Z8492015<8IND9004104M3002138<<<<<<<<<<<<<<<4", fill=(0, 0, 0), font=f_mrz)

    return img

def generate_income_sample() -> Image.Image:
    w, h = 900, 780
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.ImageDraw(img)

    draw.rectangle([20, 20, w - 20, h - 20], outline=(40, 100, 60), width=2)

    f_title = get_font(21, bold=True)
    f_sub = get_font(17, bold=True)
    f_body = get_font(16, bold=False)
    f_bold = get_font(16, bold=True)

    draw.text((260, 40), "GOVERNMENT OF ANDHRA PRADESH", fill=(20, 80, 40), font=f_title)
    draw.text((320, 70), "REVENUE DEPARTMENT", fill=(30, 30, 30), font=f_sub)
    draw.text((340, 100), "INCOME CERTIFICATE", fill=(180, 30, 20), font=f_title)

    draw.text((60, 150), "Application No : IC012293847291", fill=(20, 20, 20), font=f_bold)
    draw.text((600, 150), "Date of Issue : 12/06/2024", fill=(20, 20, 20), font=f_bold)

    draw.text((60, 185), "G.O. Ms. No. 186, Revenue (Ser.II) Dept., Dated: 27-05-2011", fill=(60, 60, 60), font=f_body)

    draw.line([50, 220, 850, 220], fill=(200, 200, 200), width=1)

    draw.text((60, 250), "Applicant Name : MANOJ KUMAR REDDY", fill=(20, 20, 20), font=f_bold)
    draw.text((60, 285), "Father's Name : NARAYANA REDDY", fill=(20, 20, 20), font=f_bold)
    draw.text((60, 320), "Address : Door No 2-104, Main Road, Chandragiri Village", fill=(30, 30, 30), font=f_body)
    draw.text((60, 355), "Mandal: Chandragiri, District: Tirupati, Andhra Pradesh", fill=(30, 30, 30), font=f_body)
    draw.text((60, 395), "Annual Income : Rs. 75,000/- (Rupees Seventy Five Thousand only)", fill=(10, 30, 100), font=f_bold)
    draw.text((60, 430), "Financial Year : 2024-2025", fill=(30, 30, 30), font=f_bold)

    draw.line([50, 470, 850, 470], fill=(200, 200, 200), width=1)

    draw.text((60, 500), "This certificate is issued for educational and scholarship purposes.", fill=(60, 60, 60), font=f_body)
    draw.text((60, 535), "Validity Period: 2024-2025", fill=(20, 20, 20), font=f_body)

    # Authority Signature Stamp
    draw.rectangle([540, 580, 820, 700], outline=(50, 100, 160), width=1)
    draw.text((560, 595), "Digitally Signed by:", fill=(80, 80, 80), font=get_font(13))
    draw.text((560, 615), "TAHSILDAR", fill=(10, 20, 90), font=f_bold)
    draw.text((560, 640), "Chandragiri Mandal, Tirupati", fill=(50, 50, 50), font=f_body)
    draw.text((560, 665), "Date: 12-06-2024 14:32 IST", fill=(80, 80, 80), font=get_font(13))

    return img

def get_sample_bytes(doc_type: str) -> bytes:
    generators = {
        "aadhaar": generate_aadhaar_sample,
        "pan": generate_pan_sample,
        "ssc": generate_ssc_sample,
        "passport": generate_passport_sample,
        "income_cert": generate_income_sample,
    }
    gen = generators.get(doc_type, generate_aadhaar_sample)
    img = gen()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
