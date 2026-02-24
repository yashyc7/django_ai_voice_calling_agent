import openpyxl
from pathlib import Path

EXCEL_FILE = Path("user_data.xlsx")

def save_to_excel(name, age, weight):
    if not EXCEL_FILE.exists():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Name", "Age", "Weight"])
        wb.save(EXCEL_FILE)
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([name, age, weight])
    wb.save(EXCEL_FILE)