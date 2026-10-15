"""
SQLAlchemy 2.0 Relational Models for VidyaMarksheet Examination Persistence Engine.
Compliant with Indian Nursing Council (INC) Gazette Regulations (Gazette No. 205, April 2022)
and SGPGIMS Lucknow Regulations (College Code: 1313).
VidyaLabs Copyright © 2026.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    String,
    Numeric,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import relationship

from backend.db.database import Base


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_name = Column(String(50), unique=True, nullable=False, index=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    total_prescribed_credits = Column(Integer, default=151, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    students = relationship("Student", back_populates="batch", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Batch(id={self.id}, batch_name='{self.batch_name}')>"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    roll_no = Column(String(30), unique=True, nullable=False, index=True)
    enrollment_no = Column(String(30), unique=True, nullable=False, index=True)
    student_name = Column(String(150), nullable=False)
    father_name = Column(String(150), nullable=False)
    institutional_status = Column(String(30), default="REGULAR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    batch = relationship("Batch", back_populates="students")
    registrations = relationship(
        "StudentSemesterRegistration", back_populates="student", cascade="all, delete-orphan"
    )
    academic_summary = relationship(
        "CumulativeAcademicSummary",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, roll_no='{self.roll_no}', name='{self.student_name}')>"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    semester_number = Column(SmallInteger, nullable=False, index=True)
    course_code = Column(String(50), nullable=False)
    course_title = Column(String(200), nullable=False)
    credits = Column(Numeric(4, 1), nullable=False)
    is_theory = Column(Boolean, default=True, nullable=False)
    is_practical = Column(Boolean, default=False, nullable=False)
    is_college_exam = Column(Boolean, default=False, nullable=False)
    include_in_sgpa = Column(Boolean, default=True, nullable=False)  # False for ENGL 101, Electives 1/2/3
    min_pass_pct = Column(Numeric(5, 2), default=Decimal("50.00"), nullable=False)  # 40.00 for English & Electives
    max_internal = Column(Numeric(5, 2), nullable=False)
    max_external = Column(Numeric(5, 2), nullable=False)
    max_total = Column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("semester_number", "course_code", name="uq_course_sem_code"),
        Index("idx_courses_sem_code", "semester_number", "course_code"),
    )

    # Relationships
    marks = relationship("StudentCourseMark", back_populates="course")

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, sem={self.semester_number}, code='{self.course_code}')>"


class StudentSemesterRegistration(Base):
    __tablename__ = "student_semester_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_number = Column(SmallInteger, nullable=False, index=True)
    exam_month_year = Column(String(50), nullable=False)
    exam_type = Column(String(20), default="MAIN", nullable=False)  # 'MAIN' or 'RE-APPEAR'
    attempt_number = Column(SmallInteger, default=0, nullable=False)
    attempt_label = Column(String(30), default="MAIN", nullable=False)  # 'MAIN', 'REAPPEAR - I', etc.
    total_credits_registered = Column(Numeric(4, 1), nullable=True)
    sgpa_credits = Column(Numeric(4, 1), nullable=True)
    grand_total_obtained = Column(Numeric(6, 2), nullable=True)
    grand_total_max = Column(Numeric(6, 2), nullable=True)
    percentage = Column(Numeric(5, 2), nullable=True)
    credit_score = Column(Numeric(6, 2), nullable=True)
    sgpa = Column(Numeric(4, 2), nullable=True)
    result_status = Column(String(50), nullable=True)  # 'PASS', 'PASS WITH GRACE', 'FAIL'
    result_remarks = Column(Text, nullable=True)
    grading_performance = Column(String(50), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)
    workflow_status = Column(String(30), default="DRAFT", nullable=False)  # 'DRAFT', 'SCRUTINIZED', 'APPROVED', 'LOCKED'
    workflow_updated_at = Column(DateTime(timezone=True), nullable=True)
    workflow_updated_by = Column(String(100), nullable=True)
    workflow_remarks = Column(Text, nullable=True)
    delivery_status = Column(String(20), default="PROVISIONAL", nullable=False)  # 'DRAFT', 'PROVISIONAL', 'FINAL'
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    delivered_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "semester_number", "exam_type", name="uq_reg_student_sem_type"),
        Index("idx_registrations_student_sem", "student_id", "semester_number"),
    )

    # Relationships
    student = relationship("Student", back_populates="registrations")
    course_marks = relationship(
        "StudentCourseMark", back_populates="registration", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Registration(id={self.id}, student_id={self.student_id}, sem={self.semester_number}, status='{self.result_status}')>"


class StudentCourseMark(Base):
    __tablename__ = "student_course_marks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_id = Column(
        Integer, ForeignKey("student_semester_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    internal_obtained = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    external_part_a = Column(Numeric(5, 2), nullable=True)  # e.g., Anatomy (37) / PHAR (38)
    external_part_b = Column(Numeric(5, 2), nullable=True)  # e.g., Physiology (38) / PATH (25)
    external_part_c = Column(Numeric(5, 2), nullable=True)  # e.g., Genetics (12)
    external_obtained = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    grace_awarded = Column(Numeric(4, 2), default=Decimal("0.00"), nullable=False)
    total_obtained = Column(Numeric(5, 2), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)
    letter_grade = Column(String(5), nullable=False)
    grade_point = Column(Integer, nullable=False)
    course_result = Column(String(20), nullable=False)  # 'PASS', 'FAIL', 'Ab'
    is_exempted = Column(Boolean, default=False, nullable=False)
    original_exam_month_year = Column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("registration_id", "course_id", name="uq_mark_reg_course"),
        Index("idx_course_marks_reg_course", "registration_id", "course_id"),
    )

    # Relationships
    registration = relationship("StudentSemesterRegistration", back_populates="course_marks")
    course = relationship("Course", back_populates="marks")

    def __repr__(self) -> str:
        return f"<Mark(id={self.id}, reg_id={self.registration_id}, course_id={self.course_id}, grade='{self.letter_grade}')>"


class CumulativeAcademicSummary(Base):
    __tablename__ = "cumulative_academic_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    sem1_credits = Column(Numeric(4, 1), nullable=True)
    sem1_sgpa = Column(Numeric(4, 2), nullable=True)
    sem1_pct = Column(Numeric(5, 2), nullable=True)

    sem2_credits = Column(Numeric(4, 1), nullable=True)
    sem2_sgpa = Column(Numeric(4, 2), nullable=True)
    sem2_pct = Column(Numeric(5, 2), nullable=True)

    sem3_credits = Column(Numeric(4, 1), nullable=True)
    sem3_sgpa = Column(Numeric(4, 2), nullable=True)
    sem3_pct = Column(Numeric(5, 2), nullable=True)

    sem4_credits = Column(Numeric(4, 1), nullable=True)
    sem4_sgpa = Column(Numeric(4, 2), nullable=True)
    sem4_pct = Column(Numeric(5, 2), nullable=True)

    sem5_credits = Column(Numeric(4, 1), nullable=True)
    sem5_sgpa = Column(Numeric(4, 2), nullable=True)
    sem5_pct = Column(Numeric(5, 2), nullable=True)

    sem6_credits = Column(Numeric(4, 1), nullable=True)
    sem6_sgpa = Column(Numeric(4, 2), nullable=True)
    sem6_pct = Column(Numeric(5, 2), nullable=True)

    sem7_credits = Column(Numeric(4, 1), nullable=True)
    sem7_sgpa = Column(Numeric(4, 2), nullable=True)
    sem7_pct = Column(Numeric(5, 2), nullable=True)

    sem8_credits = Column(Numeric(4, 1), nullable=True)
    sem8_sgpa = Column(Numeric(4, 2), nullable=True)
    sem8_pct = Column(Numeric(5, 2), nullable=True)

    cumulative_earned_credits = Column(Numeric(5, 1), default=Decimal("0.0"), nullable=False)
    total_credits = Column(Numeric(5, 1), default=Decimal("151.0"), nullable=False)
    total_prescribed_credits = Column(Numeric(5, 1), default=Decimal("151.0"), nullable=False)
    cgpa = Column(Numeric(4, 2), nullable=True)
    overall_percentage = Column(Numeric(5, 2), nullable=True)
    final_percentage = Column(Numeric(5, 2), nullable=True)
    overall_grade = Column(String(10), nullable=True)
    final_letter_grade = Column(String(10), nullable=True)
    grading_performance = Column(String(50), nullable=True)
    division_classification = Column(String(50), nullable=True)
    final_result = Column(String(20), nullable=True)  # 'PASS' or 'FAIL'
    overall_result = Column(String(30), nullable=True)  # 'PASSED', 'FAILED', 'ARREARS'
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    student = relationship("Student", back_populates="academic_summary")

    def __repr__(self) -> str:
        return f"<Summary(student_id={self.student_id}, cgpa={self.cgpa}, result='{self.final_result or self.overall_result}')>"


class MarksAuditLog(Base):
    __tablename__ = "marks_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=True)  # 'student', 'registration', 'course_mark'
    entity_id = Column(Integer, nullable=True)
    student_roll_no = Column(String(30), nullable=True, index=True)
    semester_number = Column(SmallInteger, nullable=True, index=True)
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    modified_by = Column(String(100), default="SYSTEM_ETL", nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_audit_roll", "student_roll_no"),
        Index("idx_audit_sem", "semester_number"),
    )

    def __repr__(self) -> str:
        return f"<Audit(id={self.id}, roll='{self.student_roll_no}', sem={self.semester_number}, field='{self.field_name}')>"


class TemplateDesignAuditLog(Base):
    __tablename__ = "template_design_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    semester_number = Column(SmallInteger, nullable=False, index=True)
    changed_property = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    modified_by = Column(String(100), default="Marksheet Layout Studio", nullable=False)
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_template_design_sem", "semester_number"),
    )

    def __repr__(self) -> str:
        return f"<TemplateAudit(id={self.id}, sem={self.semester_number}, prop='{self.changed_property}')>"

