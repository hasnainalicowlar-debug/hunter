# Windows Setup & Deployment Guide
**Pakistan Food Business Database & Restaurant POS Sales Intelligence Platform**

This guide provides step-by-step instructions for running the platform natively on Windows 10/11 or Windows Server.

---

## 1. Prerequisites
- **Python 3.10+** (Python 3.12 or 3.14 recommended).
  - During Python installation, ensure the checkbox **"Add Python to PATH"** is checked.
- **Git** (optional, for version tracking).
- Modern web browser (Chrome, Edge, Firefox, Brave).

---

## 2. Quickstart (Native Windows PowerShell / Command Prompt)

### Step 1: Open Terminal in Project Directory
Open PowerShell or Command Prompt and navigate to the project directory:
```powershell
cd C:\Users\Hasnain.DESKTOP-80IKSQ9\Desktop\pos\pakistan_food_pos_intel
```

### Step 2: Create and Activate Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or use `cmd.exe`).*

### Step 3: Install Required Python Packages
```powershell
pip install -r requirements.txt
```

### Step 4: Verify Database and Seed Data
```powershell
python database/db_manager.py
```
This ensures SQLite tables, categories, Pakistan administrative regions, POS vendors, and research sources are ready.

### Step 5: Run Data Collection Pipeline
```powershell
python collector/orchestrator.py
```
This ingests verified baseline establishments, active buyer intent signals, newly opened businesses, and runs OpenStreetMap Nominatim discovery with deduplication and lead scoring.

### Step 6: Generate Master Excel and CSV Exports
```powershell
python exports/export_generator.py
```
This compiles the **24-Sheet Excel Workbook** (`Pakistan_Food_Business_POS_Intelligence.xlsx`) and the **Master CSV File** (`all_food_businesses_pakistan.csv`) in the `exports/` folder.

### Step 7: Launch the Platform Server
```powershell
python run.py
# or: python api/server.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 3. Windows Batch One-Click Startup Script

For seamless execution without typing commands, double-click `start_platform.bat` (provided in the root directory) or run:
```bat
start_platform.bat
```

---

## 4. Running Automated Tests on Windows
Execute the built-in test suite:
```powershell
python -m unittest tests/test_platform.py -v
```
All 10 integration and unit tests will verify database schema, deduplication, scoring algorithms, 24-sheet Excel generation, and API responses.

---

## 5. File Locations
- **Database:** `database/food_intel.db`
- **Master Excel File:** `exports/Pakistan_Food_Business_POS_Intelligence.xlsx`
- **Master CSV File:** `exports/all_food_businesses_pakistan.csv`
- **Market Report:** `../PAKISTAN_FOOD_SERVICE_MARKET_BASELINE_REPORT.md`
- **Frontend Assets:** `static/index.html`, `static/style.css`, `static/app.js`
