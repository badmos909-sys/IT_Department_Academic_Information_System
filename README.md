# Information Technology Department Academic Information System

A small localhost Flask + SQLite project for a BSc IT CEP / NEP 2020 academic-information module.

## Features
- FY / SY / TY BSc IT navigation
- Teacher list and teacher details
- Subject list and subject details
- Teacher-subject assignment
- Add/delete teachers
- Add/delete subjects
- SQLite database
- Simple responsive local UI

## Run on Windows

1. Install Python 3.10+ from python.org.
2. Open Command Prompt in this project folder.
3. Create a virtual environment:

   `python -m venv venv`

4. Activate it:

   `venv\Scripts\activate`

5. Install Flask:

   `pip install -r requirements.txt`

6. Start the project:

   `python app.py`

7. Open:

   `http://127.0.0.1:5000`

The SQLite database `database.db` is created automatically the first time the application runs.

## Initial data

Teachers:
- Sharayu Kadam
- Archana Sanap
- Sunitha Joshi
- Rajashree Katnekar
- Bhagyashree Kulkarni

TY BSc IT subjects:
- .NET and PWA — Practical
- .NET and PWA — Theory
- AI & AO — Theory
- IoT — Practical

FY and SY are included as year sections; their subjects can be added later from the Admin page.

## Project flow

Home
→ FY / SY / TY
→ Teachers / Subjects
→ Teacher details / Subject details

Admin
→ Manage teachers
→ Manage subjects
→ Assign teachers to subjects
