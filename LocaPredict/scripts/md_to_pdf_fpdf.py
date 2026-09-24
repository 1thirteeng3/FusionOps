#!/usr/bin/env python3
"""
Convert LocaPredict SLA Guard v3 markdown to PDF using fpdf2 with Unicode font support.
"""

import markdown
import re
from fpdf import FPDF
import os

INPUT_MD = os.path.join(os.path.dirname(__file__), "..", "docs", "LocaPredict_SLA_Guard_v3_Reestruturado.md")
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "..", "docs", "LocaPredict_SLA_Guard_v3.pdf")

FONT_DIR = r"C:\Windows\Fonts"


class MyFPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Register Unicode fonts
        self.add_font("Arial", "", os.path.join(FONT_DIR, "arial.ttf"), uni=True)
        self.add_font("Arial", "B", os.path.join(FONT_DIR, "arialbd.ttf"), uni=True)
        self.add_font("Arial", "I", os.path.join(FONT_DIR, "ariali.ttf"), uni=True)
        self.add_font("Arial", "BI", os.path.join(FONT_DIR, "arialbi.ttf"), uni=True)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, "LocaPredict SLA Guard v3 — FusionOps Intelligence Platform", align="L")
            self.ln(5)
            self.set_draw_color(200, 200, 200)
            self.line(20, self.get_y(), self.w - 20, self.get_y())
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Página {self.page_no() - 1}", align="C")


def preprocess_markdown(md_text):
    """Clean up markdown for better conversion."""
    md_text = md_text.replace("\\.", ".")
    md_text = re.sub(r'([^\n])(\n#{1,3} )', r'\1\n\n\2', md_text)
    md_text = re.sub(r'(\n#{1,3} [^\n]+)\n([^\n])', r'\1\n\n\2', md_text)
    return md_text


def main():
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    md_text = preprocess_markdown(md_text)

    extensions = ["tables", "fenced_code", "sane_lists"]
    html_body = markdown.markdown(md_text, extensions=extensions)

    # Style mermaid code blocks
    html_body = re.sub(
        r'<div class="highlight"><pre>(.*?)</pre></div>',
        r'<pre style="background:#1e293b;color:#e2e8f0;padding:10px;font-size:8pt;white-space:pre-wrap;">\1</pre>',
        html_body,
        flags=re.DOTALL
    )

    styled_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
{html_body}
</body>
</html>"""

    pdf = MyFPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)

    # Cover page
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Arial", "B", 26)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 15, "LocaPredict SLA Guard v3", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 16)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 12, "FusionOps Intelligence Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Arial", "I", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Predict. Explain. Prevent. Optimize.", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "Documento de Especificação Completa do Projeto", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Versão 3.0 — 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # Content pages
    pdf.add_page()
    pdf.write_html(styled_html)

    pdf.output(OUTPUT_PDF)
    print(f"PDF gerado com sucesso: {OUTPUT_PDF}")
    print(f"Total de páginas: {pdf.page_no()}")


if __name__ == "__main__":
    main()
