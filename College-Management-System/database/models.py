# database/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def now_iso():
    return datetime.utcnow().isoformat()


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(120), unique=True, nullable=False, index=True)  # e.g. STD-2025-01
    name = db.Column(db.String(255), nullable=False)
    class_name = db.Column(db.String(64), nullable=True)   # called `class` in UI, but `class` is reserved
    roll_no = db.Column(db.String(64), nullable=True, index=True)
    face_image = db.Column(db.String(1024), nullable=True)  # path to stored image
    enrolled_at = db.Column(db.String(64), default=now_iso)

    # relationships
    semesters = db.relationship("Semester", backref="student", cascade="all, delete-orphan", lazy="dynamic")
    marks = db.relationship("Mark", backref="student", cascade="all, delete-orphan", lazy="dynamic")
    attendance_records = db.relationship("Attendance", backref="student", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<Student {self.student_id} {self.name}>"

    def to_dict(self, include_semesters=False, include_marks=False, include_attendance=False):
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "class": self.class_name,
            "roll_no": self.roll_no,
            "face_image": self.face_image,
            "enrolled_at": self.enrolled_at,
        }
        if include_semesters:
            data["semesters"] = [s.to_dict() for s in self.semesters.order_by(Semester.sem_number).all()]
        if include_marks:
            data["marks"] = [m.to_dict() for m in self.marks.all()]
        if include_attendance:
            data["attendance"] = [a.to_dict() for a in self.attendance_records.order_by(Attendance.timestamp.desc()).all()]
        return data


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(128), nullable=True)
    assigned_classes = db.Column(db.String(255), nullable=True)  # comma-separated e.g. "10A,11B"
    face_image = db.Column(db.String(1024), nullable=True)
    enrolled_at = db.Column(db.String(64), default=now_iso)

    def __repr__(self):
        return f"<Teacher {self.teacher_id} {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "name": self.name,
            "department": self.department,
            "assigned_classes": self.assigned_classes,
            "face_image": self.face_image,
            "enrolled_at": self.enrolled_at,
        }


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(120), db.ForeignKey("students.student_id"), nullable=True, index=True)
    timestamp = db.Column(db.String(64), default=now_iso, index=True)
    status = db.Column(db.String(64), default="present")  # present / absent / late / excused
    extra = db.Column(db.String(1024), nullable=True)     # optional JSON or note

    def __repr__(self):
        return f"<Attendance {self.student_id} {self.timestamp} {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "extra": self.extra,
        }


class Mark(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(120), db.ForeignKey("students.student_id"), nullable=False, index=True)
    semester = db.Column(db.Integer, nullable=False, index=True)  # which semester this mark belongs to
    marks = db.Column(db.Float, nullable=True)
    gpa = db.Column(db.Float, nullable=True)
    updated_at = db.Column(db.String(64), default=now_iso)

    def __repr__(self):
        return f"<Mark {self.student_id} sem:{self.semester} marks:{self.marks} gpa:{self.gpa}>"

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "semester": self.semester,
            "marks": self.marks,
            "gpa": self.gpa,
            "updated_at": self.updated_at,
        }


class Semester(db.Model):
    __tablename__ = "semesters"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(120), db.ForeignKey("students.student_id"), nullable=False, index=True)
    sem_number = db.Column(db.Integer, nullable=False, index=True)  # 1..8
    year = db.Column(db.Integer, nullable=True)
    marks = db.Column(db.Float, nullable=True)
    gpa = db.Column(db.Float, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("student_id", "sem_number", name="uq_student_sem"),
    )

    def __repr__(self):
        return f"<Semester {self.student_id} sem:{self.sem_number} marks:{self.marks}>"

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "sem": self.sem_number,
            "year": self.year,
            "marks": self.marks,
            "gpa": self.gpa,
        }


# Helper to create tables (for quick development)
def create_all_if_needed(app=None):
    """
    Call this during app startup (with app context) to ensure tables exist.
    Example:
        from database.models import db, create_all_if_needed
        db.init_app(app)
        with app.app_context():
            create_all_if_needed()
    """
    if app is not None:
        db.init_app(app)
        with app.app_context():
            db.create_all()
    else:
        # if db has been initialized elsewhere, simply create
        db.create_all()
