"""
FRESHMARK DELI INC — Employment Letter Generator
=================================================
Requirements:
    pip install reportlab pillow numpy

Usage:
    1. Place the signature image (signature.png) in the same folder as this script.
    2. Run:  python generate_solano_letter.py
    3. Output: SOLANO_letter.pdf

To customize the letter, edit the LETTER CONTENT section below.
"""

import io
import numpy as np
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Flowable
)

# ============================================================
#  LETTER CONTENT  ← edit everything here
# ============================================================
EMPLOYEE_NAME    = "FRANCISCO SOLANO"
EMPLOYEE_TITLE   = "Deli-man helper"
EMPLOYMENT_TYPE  = "part-time"
COMPANY_NAME     = "FRESHMARK DELI INC"
WEEKLY_GROSS     = "$209.93 (two hundred nine dollars 93/100)"
LETTER_DATE      = "3/23/2026"
CONTACT_PHONE    = "1-347-701-4131"
SIGNER_NAME      = "CARLOS DIAZ"
SIGNER_TITLE     = "MGR"
SIGNATURE_IMAGE  = "signature.png"   # path to signature PNG
OUTPUT_FILE      = "SOLANO_letter.pdf"

# Company header info
COMPANY_ADDRESS1 = "2375-79 SECOND AVE"
COMPANY_ADDRESS2 = "NEW YORK, NY 10035"
COMPANY_PHONE    = "PH. 646-524-5542"
HEADER_COLOR_TOP = "#C04A1A"   # orange/red band
HEADER_COLOR_BOT = "#2F6EB5"   # blue band
# ============================================================


# ── Utility: clean & crop signature image ───────────────────
def load_signature(path):
    """Open a signature PNG, remove white/gray background, tight-crop to ink."""
    img = PILImage.open(path).convert("RGBA")
    w, h = img.size
    # Crop bottom 38% (removes any printed text below the actual signature)
    img = img.crop((0, 0, w, int(h * 0.62)))
    arr = np.array(img)
    # Make all near-white pixels transparent
    mask = (arr[:, :, 0] > 180) & (arr[:, :, 1] > 180) & (arr[:, :, 2] > 180)
    arr[mask] = [255, 255, 255, 0]
    img = PILImage.fromarray(arr)
    img = img.crop(img.getbbox())   # tight-crop to ink bounding box
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf), img.size   # (reader, (px_w, px_h))


# ── Custom Flowable: colored company header ──────────────────
class CompanyHeader(Flowable):
    """Draws the two-tone colored banner with company name and address."""
    def __init__(self, width,
                 company, addr1, addr2, phone,
                 color_top, color_bot):
        super().__init__()
        self.width       = width
        self.height      = 1.05 * inch
        self.company     = company
        self.addr1       = addr1
        self.addr2       = addr2
        self.phone       = phone
        self.color_top   = colors.HexColor(color_top)
        self.color_bot   = colors.HexColor(color_bot)

    def draw(self):
        c     = self.canv
        bot_h = self.height * 0.52
        top_h = self.height * 0.48
        # orange band
        c.setFillColor(self.color_top)
        c.rect(0, bot_h, self.width, top_h, stroke=0, fill=1)
        # blue band
        c.setFillColor(self.color_bot)
        c.rect(0, 0, self.width, bot_h, stroke=0, fill=1)
        # company name
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(0.15 * inch, bot_h + 0.12 * inch, self.company)
        # address lines
        c.setFont("Helvetica-Bold", 8)
        c.drawString(0.15 * inch, bot_h - 0.20 * inch, self.addr1)
        c.setFont("Helvetica", 8)
        c.drawString(0.15 * inch, bot_h - 0.32 * inch, self.addr2)
        c.drawString(0.15 * inch, bot_h - 0.44 * inch, self.phone)


# ── Custom Flowable: signature block ────────────────────────
class SignatureBlock(Flowable):
    """Draws the signature image and signer name/title flush to the left margin."""
    def __init__(self, img_reader, px_size, signer_name, signer_title,
                 display_width=1.8 * inch):
        super().__init__()
        self.img          = img_reader
        px_w, px_h        = px_size
        self.sig_w        = display_width
        self.sig_h        = display_width * (px_h / px_w)
        self.signer_name  = signer_name
        self.signer_title = signer_title
        self.width        = self.sig_w
        self.height       = self.sig_h + 0.45 * inch

    def draw(self):
        c = self.canv
        c.drawImage(self.img, 0, 0.45 * inch,
                    width=self.sig_w, height=self.sig_h, mask='auto')
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(0, 0.25 * inch, self.signer_name)
        c.setFont("Helvetica", 11)
        c.drawString(0, 0.05 * inch, self.signer_title)


# ── Paragraph styles ─────────────────────────────────────────
def make_styles():
    return {
        "date":  ParagraphStyle("dt", fontSize=11, fontName="Helvetica",
                                alignment=2, spaceAfter=16),
        "head":  ParagraphStyle("hd", fontSize=11, fontName="Helvetica-Bold",
                                spaceAfter=18, spaceBefore=24),
        "body":  ParagraphStyle("bd", fontSize=11, fontName="Helvetica",
                                leading=18, spaceAfter=18),
        "close": ParagraphStyle("cl", fontSize=11, fontName="Helvetica",
                                spaceAfter=4),
    }


# ── Main build function ──────────────────────────────────────
def build_letter():
    LM = RM = 1.2 * inch
    content_w = letter[0] - LM - RM

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=letter,
        leftMargin=LM, rightMargin=RM,
        topMargin=0.5 * inch, bottomMargin=1 * inch,
    )

    s = make_styles()

    # Load & clean signature
    sig_reader, sig_px = load_signature(SIGNATURE_IMAGE)

    body_text = (
        f"Please accept this letter as confirmation that Mr. {EMPLOYEE_NAME} has been "
        f"employed, {EMPLOYMENT_TYPE} with {COMPANY_NAME}, currently Mr. {EMPLOYEE_NAME.split()[-1]} "
        f"holds the title of {EMPLOYEE_TITLE}, earning a salary gross of {WEEKLY_GROSS}, "
        f"payable weekly."
    )

    contact_text = (
        f"If you have any question or require further information, please don't hesitate "
        f"to contact me at {CONTACT_PHONE}."
    )

    story = [
        CompanyHeader(
            content_w,
            COMPANY_NAME, COMPANY_ADDRESS1, COMPANY_ADDRESS2, COMPANY_PHONE,
            HEADER_COLOR_TOP, HEADER_COLOR_BOT,
        ),
        Spacer(1, 0.25 * inch),
        Paragraph(LETTER_DATE,       s["date"]),
        Paragraph("TO WHOM IT MAY CONCERN:", s["head"]),
        Paragraph(body_text,         s["body"]),
        Paragraph(contact_text,      s["body"]),
        Spacer(1, 0.35 * inch),
        Paragraph("Sincerely yours,", s["close"]),
        Spacer(1, 0.2 * inch),
        SignatureBlock(sig_reader, sig_px, SIGNER_NAME, SIGNER_TITLE),
    ]

    doc.build(story)
    print(f"✅  Letter saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    build_letter()
