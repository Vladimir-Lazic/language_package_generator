from docx import Document
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.oxml.shared import OxmlElement, qn

def set_table_borders(table):
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

def write_docx(original_subs, translations, output_languages, input_language, output_file):
    """Generate one DOCX file with timestamps + target languages + original language."""
    document = Document()

    # Header row: Timestamp + [target langs...] + input language
    header = ['Timestamp'] + output_languages + [input_language.upper()]
    table = document.add_table(rows=1, cols=len(header))
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(header):
        hdr_cells[i].text = h

    set_table_borders(table)

    # Add rows
    for i, entry in enumerate(original_subs):
        row = table.add_row().cells
        timestamp = f"{entry['start']} --> {entry['end']}"
        row[0].text = timestamp

        # Fill target language columns
        for col_idx, lang_code in enumerate(output_languages, start=1):
            translated_text = translations.get(lang_code, [])[i]['text'] if lang_code in translations else ''
            row[col_idx].text = translated_text

        # Fill original language at the end
        row[len(header)-1].text = entry['text']

    document.save(output_file)
