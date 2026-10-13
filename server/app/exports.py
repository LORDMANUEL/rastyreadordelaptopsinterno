from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape
from typing import Iterable

from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, LongTable, TableStyle

from .models import AuditEvent, Device


ASSET_HEADERS = [
    "Asset Tag", "Serial", "Hostname", "Fabricante", "Modelo", "Plataforma",
    "Sucursal", "Departamento", "Responsable", "Estado", "Condición",
    "Propiedad", "Contrato Lease", "Proveedor", "Fecha Adquisición",
    "Fecha Asignación", "Costo", "Última Auditoría", "Último Contacto",
    "IP Pública", "SSID", "BitLocker", "TPM", "Antivirus", "Observaciones",
]

AUDIT_HEADERS = [
    "Fecha", "Evento", "Dispositivo", "Actor", "Detalle",
]


def _value(value):
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def asset_rows(devices: Iterable[Device]) -> list[list[str]]:
    return [[
        _value(d.asset_tag), _value(d.serial), _value(d.hostname),
        _value(d.manufacturer), _value(d.model), _value(d.platform),
        _value(d.branch), _value(d.department), _value(d.assigned_to),
        _value(d.asset_status), _value(d.physical_condition), _value(d.ownership_type),
        _value(d.lease_contract), _value(d.provider), _value(d.acquisition_date),
        _value(d.assignment_date), _value(d.acquisition_cost), _value(d.last_audit_at),
        _value(d.last_seen), _value(d.public_ip), _value(d.wifi_ssid),
        _value(d.bitlocker_status), _value(d.tpm_status), _value(d.antivirus_status),
        _value(d.notes),
    ] for d in devices]


def audit_rows(events: Iterable[AuditEvent]) -> list[list[str]]:
    return [[
        _value(e.created_at), _value(e.event_type), _value(e.device_id),
        _value(e.actor), _value(e.detail),
    ] for e in events]


def _safe_excel(value: str) -> str:
    """Force untrusted device/user values to be literal XLSX text."""
    value = str(value)
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def build_xlsx(headers: list[str], rows: list[list[str]], sheet_name: str) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append([_safe_excel(v) for v in row])

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    for column in sheet.columns:
        max_length = min(
            45,
            max((len(str(cell.value or "")) for cell in column), default=10) + 2,
        )
        sheet.column_dimensions[column[0].column_letter].width = max(12, max_length)

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def build_pdf(title: str, headers: list[str], rows: list[list[str]]) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(letter),
        rightMargin=24,
        leftMargin=24,
        topMargin=28,
        bottomMargin=28,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"])]

    # PDFs stay readable by limiting very wide tables to key columns.
    cell_style = styles["BodyText"]
    cell_style.fontSize = 6
    cell_style.leading = 8
    cell_style.wordWrap = "CJK"
    table_data = [[Paragraph(escape(str(value))[:500], cell_style) for value in line] for line in [headers] + rows]
    table = LongTable(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8ECF4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8FA")]),
    ]))
    story.append(table)
    document.build(story)
    return output.getvalue()
