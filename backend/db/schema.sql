-- ============================================================================
-- Relational Database Schema Definition (SQL DDL)
-- Database: vidya_examination_db
-- Developed at VidyaLabs. Copyright © 2026 VidyaLabs.
-- Contact: Priyanka Kumari (+91-9140189586)
-- Compliant with INC Gazette Regulations & SGPGIMS Lucknow Regulations.
-- ============================================================================

-- 1. batches table
CREATE TABLE IF NOT EXISTS batches (
    id SERIAL PRIMARY KEY,
    batch_name VARCHAR(50) UNIQUE NOT NULL,
    start_year INT,
    end_year INT,
    total_prescribed_credits INT DEFAULT 151,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    batch_id INT REFERENCES batches(id) ON DELETE RESTRICT,
    roll_no VARCHAR(30) UNIQUE NOT NULL,
    enrollment_no VARCHAR(30) UNIQUE NOT NULL,
    student_name VARCHAR(150) NOT NULL,
    father_name VARCHAR(150) NOT NULL,
    institutional_status VARCHAR(30) DEFAULT 'REGULAR',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. courses table
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    semester_number SMALLINT NOT NULL,
    course_code VARCHAR(50) NOT NULL,
    course_title VARCHAR(200) NOT NULL,
    credits NUMERIC(4, 1) NOT NULL,
    is_theory BOOLEAN DEFAULT TRUE,
    is_practical BOOLEAN DEFAULT FALSE,
    is_college_exam BOOLEAN DEFAULT FALSE,
    include_in_sgpa BOOLEAN DEFAULT TRUE,  -- FALSE for ENGL 101, Electives 1/2/3
    min_pass_pct NUMERIC(5, 2) DEFAULT 50.00, -- 40.00 for English & Electives
    max_internal NUMERIC(5, 2) NOT NULL,
    max_external NUMERIC(5, 2) NOT NULL,
    max_total NUMERIC(5, 2) NOT NULL,
    CONSTRAINT uq_course_sem_code UNIQUE (semester_number, course_code)
);

-- 4. student_semester_registrations table
CREATE TABLE IF NOT EXISTS student_semester_registrations (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    semester_number SMALLINT NOT NULL,
    exam_month_year VARCHAR(50) NOT NULL,
    exam_type VARCHAR(20) DEFAULT 'MAIN', -- 'MAIN' or 'RE-APPEAR'
    attempt_number SMALLINT DEFAULT 0,
    attempt_label VARCHAR(30) DEFAULT 'MAIN', -- 'MAIN', 'REAPPEAR - I', etc.
    total_credits_registered NUMERIC(4, 1),
    sgpa_credits NUMERIC(4, 1),
    grand_total_obtained NUMERIC(6, 2),
    grand_total_max NUMERIC(6, 2),
    percentage NUMERIC(5, 2),
    credit_score NUMERIC(6, 2),
    sgpa NUMERIC(4, 2),
    result_status VARCHAR(50), -- 'PASS', 'PASS WITH GRACE', 'FAIL'
    result_remarks TEXT,
    grading_performance VARCHAR(50),
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by VARCHAR(100),
    workflow_status VARCHAR(30) DEFAULT 'DRAFT', -- 'DRAFT', 'SCRUTINIZED', 'APPROVED', 'LOCKED'
    workflow_updated_at TIMESTAMP WITH TIME ZONE,
    workflow_updated_by VARCHAR(100),
    workflow_remarks TEXT,
    delivery_status VARCHAR(20) DEFAULT 'PROVISIONAL', -- 'DRAFT', 'PROVISIONAL', 'FINAL'
    delivered_at TIMESTAMP WITH TIME ZONE,
    delivered_by VARCHAR(100),
    CONSTRAINT uq_reg_student_sem_type UNIQUE (student_id, semester_number, exam_type)
);

-- 5. student_course_marks table
CREATE TABLE IF NOT EXISTS student_course_marks (
    id SERIAL PRIMARY KEY,
    registration_id INT REFERENCES student_semester_registrations(id) ON DELETE CASCADE,
    course_id INT REFERENCES courses(id) ON DELETE RESTRICT,
    internal_obtained NUMERIC(5, 2) DEFAULT 0.00,
    external_part_a NUMERIC(5, 2), -- e.g., Anatomy (37) / PHAR (38)
    external_part_b NUMERIC(5, 2), -- e.g., Physiology (38) / PATH (25)
    external_part_c NUMERIC(5, 2), -- e.g., Genetics (12)
    external_obtained NUMERIC(5, 2) DEFAULT 0.00,
    grace_awarded NUMERIC(4, 2) DEFAULT 0.00,
    total_obtained NUMERIC(5, 2) NOT NULL,
    percentage NUMERIC(5, 2) NOT NULL,
    letter_grade VARCHAR(5) NOT NULL,
    grade_point INT NOT NULL,
    course_result VARCHAR(20) NOT NULL, -- 'PASS', 'FAIL', 'Ab'
    is_exempted BOOLEAN DEFAULT FALSE,
    original_exam_month_year VARCHAR(50),
    CONSTRAINT uq_mark_reg_course UNIQUE (registration_id, course_id)
);

-- 6. cumulative_academic_summary table (Longitudinal metrics through Sem 8)
CREATE TABLE IF NOT EXISTS cumulative_academic_summary (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE UNIQUE,
    sem1_credits NUMERIC(4, 1),
    sem1_sgpa NUMERIC(4, 2),
    sem1_pct NUMERIC(5, 2),
    sem2_credits NUMERIC(4, 1),
    sem2_sgpa NUMERIC(4, 2),
    sem2_pct NUMERIC(5, 2),
    sem3_credits NUMERIC(4, 1),
    sem3_sgpa NUMERIC(4, 2),
    sem3_pct NUMERIC(5, 2),
    sem4_credits NUMERIC(4, 1),
    sem4_sgpa NUMERIC(4, 2),
    sem4_pct NUMERIC(5, 2),
    sem5_credits NUMERIC(4, 1),
    sem5_sgpa NUMERIC(4, 2),
    sem5_pct NUMERIC(5, 2),
    sem6_credits NUMERIC(4, 1),
    sem6_sgpa NUMERIC(4, 2),
    sem6_pct NUMERIC(5, 2),
    sem7_credits NUMERIC(4, 1),
    sem7_sgpa NUMERIC(4, 2),
    sem7_pct NUMERIC(5, 2),
    sem8_credits NUMERIC(4, 1),
    sem8_sgpa NUMERIC(4, 2),
    sem8_pct NUMERIC(5, 2),
    cumulative_earned_credits NUMERIC(5, 1) DEFAULT 0.0,
    total_credits NUMERIC(5, 1) DEFAULT 151.0,
    total_prescribed_credits NUMERIC(5, 1) DEFAULT 151.0,
    cgpa NUMERIC(4, 2),
    overall_percentage NUMERIC(5, 2),
    final_percentage NUMERIC(5, 2),
    overall_grade VARCHAR(10),
    final_letter_grade VARCHAR(10),
    grading_performance VARCHAR(50),
    division_classification VARCHAR(50),
    final_result VARCHAR(20),
    overall_result VARCHAR(30),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. student_backlogs table (Tracking Backlogs & Arrears across Reappear cycles)
CREATE TABLE IF NOT EXISTS student_backlogs (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    course_id INT REFERENCES courses(id) ON DELETE RESTRICT,
    original_registration_id INT REFERENCES student_semester_registrations(id) ON DELETE CASCADE,
    failed_exam_month_year VARCHAR(50) NOT NULL,
    forthcoming_exam_month_year VARCHAR(50),
    semester_number SMALLINT NOT NULL,
    academic_year VARCHAR(50),
    failed_component VARCHAR(50),
    deficit_marks NUMERIC(5, 2),
    attempt_count SMALLINT DEFAULT 1,
    backlog_status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'CLEARED', 'DROPPED'
    cleared_in_registration_id INT REFERENCES student_semester_registrations(id) ON DELETE SET NULL,
    cleared_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_student_backlog ON student_backlogs (student_id, course_id, backlog_status) WHERE backlog_status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_backlogs_student_sem ON student_backlogs (student_id, semester_number);

-- 8. marks_audit_log table (Tracking modifications)
CREATE TABLE IF NOT EXISTS marks_audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_id INT,
    student_roll_no VARCHAR(30),
    semester_number SMALLINT,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    modified_by VARCHAR(100) DEFAULT 'SYSTEM_ETL',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. template_design_audit_log table (Tracking template customizer changes)
CREATE TABLE IF NOT EXISTS template_design_audit_log (
    id SERIAL PRIMARY KEY,
    semester_number SMALLINT NOT NULL,
    changed_property VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    modified_by VARCHAR(100) DEFAULT 'Marksheet Layout Studio',
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Performance & Query Optimization Indexes
CREATE INDEX IF NOT EXISTS idx_students_roll_no ON students(roll_no);
CREATE INDEX IF NOT EXISTS idx_students_batch ON students(batch_id);
CREATE INDEX IF NOT EXISTS idx_courses_sem_code ON courses(semester_number, course_code);
CREATE INDEX IF NOT EXISTS idx_registrations_student_sem ON student_semester_registrations(student_id, semester_number);
CREATE INDEX IF NOT EXISTS idx_course_marks_reg_course ON student_course_marks(registration_id, course_id);
CREATE INDEX IF NOT EXISTS idx_cumulative_student ON cumulative_academic_summary(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_roll ON marks_audit_log(student_roll_no);
CREATE INDEX IF NOT EXISTS idx_audit_sem ON marks_audit_log(semester_number);
CREATE INDEX IF NOT EXISTS idx_template_design_sem ON template_design_audit_log(semester_number);

-- 9. app_users table (Enterprise Hardened Role-Based Access Control)
CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    must_change_password BOOLEAN DEFAULT TRUE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    token_version INT DEFAULT 1,
    created_by VARCHAR(50) DEFAULT 'Admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- 10. auth_security_audit_log table (Authentication Security Audit)
CREATE TABLE IF NOT EXISTS auth_security_audit_log (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    action VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON app_users(username);
CREATE INDEX IF NOT EXISTS idx_auth_audit_user ON auth_security_audit_log(username);
CREATE INDEX IF NOT EXISTS idx_auth_audit_time ON auth_security_audit_log(timestamp);

