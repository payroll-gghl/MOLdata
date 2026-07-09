"""
MOHRE Employee List — PDF to data.js converter
================================================
Drop any MOHRE "List of Employees" PDFs into the same folder as this
script (or pass a folder path), run it, and it regenerates data.js
which the app (index.html) reads.

Usage:
    python parse_pdfs.py                # scans current folder for *.pdf
    python parse_pdfs.py "C:\\HR\\PDFs"  # scans a specific folder

Requires:  pip install pdfplumber
"""

import sys, os, re, json, glob
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber is not installed. Run:  pip install pdfplumber")

DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
CODE_RE = re.compile(r"\b(\d{11,15})\b")          # person code (e.g. 10009038101728)
CARDNO_RE = re.compile(r"\b(\d{8,9})\b")          # card number (e.g. 136713310)
ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def english_lines(cell):
    """Keep only the English lines of a bilingual cell, joined with a space."""
    if not cell:
        return ""
    keep = []
    for line in cell.split("\n"):
        line = line.strip()
        if not line or ARABIC_RE.search(line):
            continue
        keep.append(line)
    return re.sub(r"\s+", " ", " ".join(keep)).strip()


def parse_person_cell(cell):
    """Split the Person Name cell into (english name, person code)."""
    if not cell:
        return "", ""
    code = ""
    name_parts = []
    for line in cell.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = CODE_RE.fullmatch(line.replace(" ", ""))
        if m:
            code = m.group(1)
            continue
        if ARABIC_RE.search(line):
            # a code may be glued onto an Arabic line
            m2 = CODE_RE.search(line)
            if m2 and not code:
                code = m2.group(1)
            continue
        name_parts.append(line)
    return re.sub(r"\s+", " ", " ".join(name_parts)).strip(), code


def parse_cardno_cell(cell):
    """Split the Card Number cell into (card number, expiry date, notes)."""
    if not cell:
        return "", "", ""
    text = cell.replace("\n", " ")
    card = ""
    m = CARDNO_RE.search(text)
    if m:
        card = m.group(1)
    expiry = ""
    d = DATE_RE.search(text)
    if d:
        expiry = d.group(1)
    notes = english_lines(cell)
    if card:
        notes = notes.replace(card, "")
    if expiry:
        notes = notes.replace(expiry, "")
    notes = re.sub(r"\s+", " ", notes).strip(" *")
    return card, expiry, notes


def parse_establishment(first_page_text):
    """Pull establishment number and English name from the page header."""
    num, name = "", ""
    lines = first_page_text.split("\n")
    for i, line in enumerate(lines[:12]):
        if "Establishment Number" in line:
            # the next non-empty line usually holds:  59299 ESTABLISHMENT NAME...
            for nxt in lines[i + 1: i + 4]:
                m = re.match(r"\s*(\d{4,7})\s+(.*)", nxt)
                if m:
                    num = m.group(1)
                    name = english_lines(m.group(2))
                    return num, name
                m = re.match(r"\s*(\d{4,7})\s*$", nxt)
                if m:
                    num = m.group(1)
    # fallback: search whole header block
    m = re.search(r"Establishment Number[^\d]*(\d{4,7})", first_page_text)
    if m:
        num = m.group(1)
    return num, name


def parse_pdf(path):
    records = []
    with pdfplumber.open(path) as pdf:
        est_num, est_name = parse_establishment(pdf.pages[0].extract_text() or "")
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 7:
                        continue
                    c = [(x or "").strip() for x in row[:7]]
                    joined = " ".join(c)
                    # skip header rows
                    if "Passport Number" in joined or "PPaassssppoorrtt" in joined:
                        continue
                    passport = english_lines(c[0]).replace(" ", "")
                    name, pcode = parse_person_cell(c[1])
                    card_type = english_lines(c[2])
                    job = english_lines(c[3])
                    nationality = english_lines(c[4])
                    cardno, expiry, notes = parse_cardno_cell(c[5])
                    contract = english_lines(c[6])

                    # continuation row: table split across a page break —
                    # usually only the person code (or nothing) is present
                    if not passport and records:
                        prev = records[-1]
                        if pcode and not prev["personCode"]:
                            prev["personCode"] = pcode
                        if name and not prev["personName"]:
                            prev["personName"] = name
                        if cardno and not prev["cardNumber"]:
                            prev["cardNumber"] = cardno
                        if expiry and not prev["expiryDate"]:
                            prev["expiryDate"] = expiry
                        continue
                    if not passport:
                        continue

                    records.append({
                        "estNumber": est_num,
                        "estName": est_name,
                        "passport": passport,
                        "personName": name,
                        "personCode": pcode,
                        "cardType": card_type,
                        "jobName": job,
                        "nationality": nationality,
                        "cardNumber": cardno,
                        "expiryDate": expiry,
                        "contractType": contract,
                        "notes": notes,
                        "sourceFile": os.path.basename(path),
                    })
    return records


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    pdfs = sorted(glob.glob(os.path.join(folder, "*.pdf")))
    if not pdfs:
        sys.exit(f"No PDF files found in {folder}")

    all_records = []
    for p in pdfs:
        recs = parse_pdf(p)
        print(f"  {os.path.basename(p)}: {len(recs)} records")
        all_records.extend(recs)

    out = {
        "generated": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "files": [os.path.basename(p) for p in pdfs],
        "records": all_records,
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("window.MOHRE_DATA = ")
        json.dump(out, f, ensure_ascii=False)
        f.write(";")
    print(f"\nTotal: {len(all_records)} records  ->  {out_path}")


if __name__ == "__main__":
    main()
