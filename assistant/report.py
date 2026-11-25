"""Monthly report PDF (add-assistant-planning design decision 5).

Rendered from the figures frozen in a report card, with xhtml2pdf: pure Python
(ReportLab underneath), so it installs with pip on Windows, unlike WeasyPrint.
"""

import io

from django.template.loader import render_to_string


def report_html(figures, summary):
    return render_to_string("assistant/report.html", {"f": figures, "summary": summary})


def report_pdf(figures, summary):
    """The report as PDF bytes; raises RuntimeError if xhtml2pdf reports an error."""
    from xhtml2pdf import pisa

    out = io.BytesIO()
    result = pisa.CreatePDF(report_html(figures, summary), dest=out, encoding="utf-8")
    if result.err:
        raise RuntimeError("The report could not be rendered.")
    return out.getvalue()
