from flask import Flask, render_template, request, redirect, url_for, flash, abort
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "cep-nep2020-local-secret"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

YEARS = [
    (1, "FY BSc IT"),
    (2, "SY BSc IT"),
    (3, "TY BSc IT"),
]

TY_SUBJECTS = [
    (".NET and PWA", "Practical"),
    (".NET and PWA", "Theory"),
    ("AI & AO", "Theory"),
    ("IoT", "Practical"),
]

TEACHERS = [
    "Sharayu Kadam",
    "Archana Sanap",
    "Sunitha Joshi",
    "Rajashree Katnekar",
    "Bhagyashree Kulkarni",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS years (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL DEFAULT 'Information Technology',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            year_id INTEGER NOT NULL,
            FOREIGN KEY (year_id) REFERENCES years(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS teacher_subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            UNIQUE(teacher_id, subject_id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
    """)

    conn.executemany(
        "INSERT OR IGNORE INTO years (id, name) VALUES (?, ?)", YEARS
    )

    teacher_count = conn.execute("SELECT COUNT(*) AS c FROM teachers").fetchone()["c"]
    if teacher_count == 0:
        conn.executemany(
            "INSERT INTO teachers (name) VALUES (?)",
            [(name,) for name in TEACHERS]
        )

    subject_count = conn.execute("SELECT COUNT(*) AS c FROM subjects").fetchone()["c"]
    if subject_count == 0:
        conn.executemany(
            "INSERT INTO subjects (name, subject_type, year_id) VALUES (?, ?, 3)",
            TY_SUBJECTS
        )

    conn.commit()
    conn.close()


@app.context_processor
def inject_globals():
    return {"years": YEARS}


@app.route("/")
def index():
    conn = get_db()
    counts = {
        "teachers": conn.execute("SELECT COUNT(*) AS c FROM teachers").fetchone()["c"],
        "subjects": conn.execute("SELECT COUNT(*) AS c FROM subjects").fetchone()["c"],
    }
    conn.close()
    return render_template("index.html", counts=counts)


@app.route("/year/<int:year_id>")
def year_page(year_id):
    conn = get_db()
    year = conn.execute("SELECT * FROM years WHERE id = ?", (year_id,)).fetchone()
    if not year:
        conn.close()
        abort(404)

    subjects = conn.execute("""
        SELECT s.*, COUNT(ts.teacher_id) AS teacher_count
        FROM subjects s
        LEFT JOIN teacher_subject ts ON ts.subject_id = s.id
        WHERE s.year_id = ?
        GROUP BY s.id
        ORDER BY s.name, s.subject_type
    """, (year_id,)).fetchall()

    teachers = conn.execute("""
        SELECT DISTINCT t.*
        FROM teachers t
        JOIN teacher_subject ts ON ts.teacher_id = t.id
        JOIN subjects s ON s.id = ts.subject_id
        WHERE s.year_id = ?
        ORDER BY t.name
    """, (year_id,)).fetchall()

    # If no assignments exist yet, show all department teachers so the
    # teacher list from the original design is still visible.
    if not teachers:
        teachers = conn.execute(
            "SELECT * FROM teachers ORDER BY name"
        ).fetchall()

    conn.close()
    return render_template(
        "year.html", year=year, subjects=subjects, teachers=teachers
    )


@app.route("/teacher/<int:teacher_id>")
def teacher_detail(teacher_id):
    conn = get_db()
    teacher = conn.execute(
        "SELECT * FROM teachers WHERE id = ?", (teacher_id,)
    ).fetchone()
    if not teacher:
        conn.close()
        abort(404)

    subjects = conn.execute("""
        SELECT s.*, y.name AS year_name
        FROM subjects s
        JOIN teacher_subject ts ON ts.subject_id = s.id
        JOIN years y ON y.id = s.year_id
        WHERE ts.teacher_id = ?
        ORDER BY y.id, s.name
    """, (teacher_id,)).fetchall()
    conn.close()
    return render_template("teacher_detail.html", teacher=teacher, subjects=subjects)


@app.route("/subject/<int:subject_id>")
def subject_detail(subject_id):
    conn = get_db()
    subject = conn.execute("""
        SELECT s.*, y.name AS year_name
        FROM subjects s
        JOIN years y ON y.id = s.year_id
        WHERE s.id = ?
    """, (subject_id,)).fetchone()
    if not subject:
        conn.close()
        abort(404)

    teachers = conn.execute("""
        SELECT t.*
        FROM teachers t
        JOIN teacher_subject ts ON ts.teacher_id = t.id
        WHERE ts.subject_id = ?
        ORDER BY t.name
    """, (subject_id,)).fetchall()
    conn.close()
    return render_template("subject_detail.html", subject=subject, teachers=teachers)


@app.route("/admin")
def admin():
    conn = get_db()
    teachers = conn.execute("SELECT * FROM teachers ORDER BY name").fetchall()
    subjects = conn.execute("""
        SELECT s.*, y.name AS year_name
        FROM subjects s
        JOIN years y ON y.id = s.year_id
        ORDER BY y.id, s.name, s.subject_type
    """).fetchall()
    conn.close()
    return render_template("admin.html", teachers=teachers, subjects=subjects)


@app.route("/admin/teacher/add", methods=["POST"])
def add_teacher():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name:
        flash("Teacher name is required.", "error")
        return redirect(url_for("admin"))

    conn = get_db()
    conn.execute(
        "INSERT INTO teachers (name, email, phone) VALUES (?, ?, ?)",
        (name, email, phone)
    )
    conn.commit()
    conn.close()
    flash("Teacher added successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/teacher/delete/<int:teacher_id>", methods=["POST"])
def delete_teacher(teacher_id):
    conn = get_db()
    conn.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    conn.commit()
    conn.close()
    flash("Teacher deleted.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/subject/add", methods=["POST"])
def add_subject():
    name = request.form.get("name", "").strip()
    subject_type = request.form.get("subject_type", "").strip()
    year_id = request.form.get("year_id", type=int)

    if not name or not subject_type or not year_id:
        flash("Subject name, type and year are required.", "error")
        return redirect(url_for("admin"))

    conn = get_db()
    conn.execute(
        "INSERT INTO subjects (name, subject_type, year_id) VALUES (?, ?, ?)",
        (name, subject_type, year_id)
    )
    conn.commit()
    conn.close()
    flash("Subject added successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/subject/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    conn = get_db()
    conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()
    flash("Subject deleted.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/assign", methods=["POST"])
def assign_teacher():
    teacher_id = request.form.get("teacher_id", type=int)
    subject_id = request.form.get("subject_id", type=int)

    if not teacher_id or not subject_id:
        flash("Please select both teacher and subject.", "error")
        return redirect(url_for("admin"))

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO teacher_subject (teacher_id, subject_id) VALUES (?, ?)",
            (teacher_id, subject_id)
        )
        conn.commit()
        flash("Teacher assigned to subject.", "success")
    except sqlite3.IntegrityError:
        flash("This teacher is already assigned to this subject.", "error")
    finally:
        conn.close()

    return redirect(url_for("admin"))


@app.route("/admin/unassign/<int:assignment_id>", methods=["POST"])
def unassign_teacher(assignment_id):
    conn = get_db()
    conn.execute("DELETE FROM teacher_subject WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()
    flash("Assignment removed.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/assignments")
def assignments():
    conn = get_db()
    rows = conn.execute("""
        SELECT ts.id, t.name AS teacher_name,
               s.name AS subject_name, s.subject_type,
               y.name AS year_name
        FROM teacher_subject ts
        JOIN teachers t ON t.id = ts.teacher_id
        JOIN subjects s ON s.id = ts.subject_id
        JOIN years y ON y.id = s.year_id
        ORDER BY y.id, t.name, s.name
    """).fetchall()

    teachers = conn.execute("SELECT * FROM teachers ORDER BY name").fetchall()
    subjects = conn.execute("""
        SELECT s.*, y.name AS year_name
        FROM subjects s
        JOIN years y ON y.id = s.year_id
        ORDER BY y.id, s.name
    """).fetchall()
    conn.close()
    return render_template(
        "assignments.html", assignments=rows,
        teachers=teachers, subjects=subjects
    )


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)
