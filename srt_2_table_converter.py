#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from docx import Document
from docx.oxml.shared import OxmlElement, qn

def set_table_borders_black(table):
    """Apply black borders to the Word table."""
    tbl_elem = table._tbl
    tbl_pr = tbl_elem.xpath("./w:tblPr")[0]
    tbl_borders = OxmlElement('w:tblBorders')
    for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border_elem = OxmlElement(f"w:{border_name}")
        border_elem.set(qn('w:val'), 'single')
        border_elem.set(qn('w:sz'), '4')  # Thin line
        border_elem.set(qn('w:space'), '0')
        border_elem.set(qn('w:color'), '000000')  # Black color
        tbl_borders.append(border_elem)
    tbl_pr.append(tbl_borders)

def parse_srt(srt_content):
    """Extract timecodes and text from SRT content."""
    pattern = re.compile(
        r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)\s*(?=\n\d+\n|\Z)',
        re.DOTALL
    )
    return pattern.findall(srt_content)

def create_docx(blocks, output_path):
    """Generate the DOCX file with a table."""
    doc = Document()
    doc.add_heading('Dialogue List', level=1)

    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Timecode'
    hdr_cells[1].text = 'German'
    hdr_cells[2].text = 'English'

    for _, start, end, text in blocks:
        start_time = start.split(',')[0]
        end_time = end.split(',')[0]
        timecode = f"{start_time} --> {end_time}"
        subtitle_text = ' '.join(text.strip().splitlines())

        row_cells = table.add_row().cells
        row_cells[0].text = timecode
        row_cells[1].text = ''
        row_cells[2].text = subtitle_text

    set_table_borders_black(table)
    doc.save(output_path)

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python srt_to_docx.py input_file.srt [output_file.docx]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"❌ Error: File not found -> {input_path}")
        sys.exit(1)

    # Default output name if not specified
    if len(sys.argv) == 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.docx')

    # Read SRT
    with input_path.open('r', encoding='utf-8') as f:
        srt_content = f.read()

    # Convert and export
    blocks = parse_srt(srt_content)
    create_docx(blocks, output_path)
    print(f"✅ DOCX file created: {output_path}")

if __name__ == "__main__":
    main()
