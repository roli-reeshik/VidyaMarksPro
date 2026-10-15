/**
 * TypeScript Data Models for B.Sc. Nursing Marksheet System
 * Compliant with Indian Nursing Council (INC) Gazette and SGPGIMS Lucknow Regulations.
 * Copyright © 2026 VidyaLabs. Developed at VidyaLabs.
 */

export type CourseType = "CORE" | "COLLEGE_EXAM" | "ELECTIVE" | "CLINICAL_COMPETENCY";
export type ComponentType = "THEORY" | "PRACTICAL" | "THEORY_AND_PRACTICAL" | "COMPETENCY";

export type LetterGrade = "O" | "A+" | "A" | "B+" | "B" | "C" | "P" | "F" | "Ab";

export interface IncGradingScaleItem {
  percentage_range: string;
  letter_grade: LetterGrade;
  grade_point: number;
  qualitative_description: string;
  notes: string;
}

export interface InstitutionalMetadata {
  application_name: string;
  application_subtitle: string;
  institution_name: string;
  location: string;
  college_code: string;
  regulatory_framework: string;
  branding: {
    developed_by: string;
    copyright: string;
    contact_person: string;
    contact_mobile: string;
  };
}

export interface SubComponentDefinition {
  name: string;
  code?: string;
  max_marks: number;
  min_pass_marks?: number;
}

export interface ExamComponentSchema {
  name: string;
  credits: number;
  ia_max: number;
  ia_min_pass?: number;
  ea_max: number;
  ea_min_pass?: number;
  total_max: number;
  min_pass_percentage: number;
  sub_components?: SubComponentDefinition[];
}

export interface CourseDefinition {
  sl_no: number;
  course_code: string;
  title: string;
  credits: number;
  credit_breakdown?: string;
  course_type: CourseType;
  component_type: ComponentType;
  passing_threshold_percent: number; // 50% for standard, 40% for English/Electives
  is_english_or_elective: boolean; // strictly English and Electives qualify for 'P'
  include_in_sgpa: boolean;
  components: ExamComponentSchema[];
  footnotes?: string;
}

export interface SemesterDefinition {
  semester_number: number;
  year: number;
  semester_name: string;
  year_name: string;
  degree_title: string;
  college_name: string;
  college_code?: string;
  total_prescribed_credits: number;
  sgpa_eligible_credits: number;
  grand_total_marks: number;
  courses: CourseDefinition[];
}

export interface StudentDemographics {
  serial_no?: number | null;
  name: string;
  father_name: string;
  enrollment_no: string;
  roll_no: string;
}

export interface SubComponentMark {
  name: string;
  code?: string;
  obtained?: number | null;
  max_marks: number;
  is_absent?: boolean;
}

export interface EvaluatedCourseComponent {
  course_code: string;
  course_title: string;
  component_name: string;
  credits: number;
  credit_breakdown?: string;

  internal_obtained?: number | null;
  internal_max: number;
  external_obtained?: number | null;
  external_max: number;
  sub_components: SubComponentMark[];

  total_obtained?: number | null;
  total_max: number;
  percentage: number;

  letter_grade: LetterGrade;
  grade_point: number;
  is_pass: boolean;
  grace_marks?: number;
  is_absent?: boolean;
  is_exempted?: boolean;

  is_english_or_elective: boolean;
  include_in_sgpa: boolean;
  footnotes?: string;
}

export interface SemesterStudentResult {
  student: StudentDemographics;
  semester_number: number;
  degree_title: string;
  examination_session?: string;
  college_name: string;
  college_code: string;

  courses: EvaluatedCourseComponent[];

  grand_total_obtained: number;
  grand_total_max: number;
  overall_percentage: number;
  sgpa: number;
  total_credit_score: number;
  total_sgpa_credits: number;

  result_status: "PASS" | "FAIL" | "PASS WITH GRACE MARKS" | string;
  failed_courses: string[];
  remarks?: string | null;
}

export interface IngestionResponse {
  success: boolean;
  filename: string;
  semester: number;
  examination_session?: string;
  total_students: number;
  passed_students: number;
  failed_students: number;
  results: SemesterStudentResult[];
  warnings: string[];
}

export interface CanonicalCourseMarks {
  int_marks: number | string;
  ex_marks?: number | string;
  ex_part_a?: number | string;
  ex_part_b?: number | string;
  ex_total?: number | string;
  grace?: number;
  total: number | string;
}

export interface StudentRecord {
  roll_no: string;
  enroll_no: string;
  student_name: string;
  father_name: string;
  courses: {
    ANAT_PHYS?: CanonicalCourseMarks;
    SOCI_PSYC?: CanonicalCourseMarks;
    ENGL?: CanonicalCourseMarks;
    [key: string]: CanonicalCourseMarks | undefined;
  };
  raw_remarks?: string;
}

export interface ExamCellIngestionBatchResponse {
  success: boolean;
  branding: string;
  total_records: number;
  records: StudentRecord[];
  warnings: string[];
}

export interface AuditAnomalyItem {
  roll_no: string;
  student_name: string;
  field: string;
  raw_value: string;
  expected_value: string;
  severity: "CRITICAL" | "WARNING";
  category: "ARITHMETIC_INVARIANCE" | "GRACE_POLICY" | "OUTLIER_BOUNDARY" | "DEMOGRAPHIC";
  description: string;
}

export interface QualityAuditReport {
  is_valid: boolean;
  can_export_pdf: boolean;
  total_candidates: number;
  clean_candidates: number;
  flagged_candidates: number;
  critical_errors_count: number;
  warnings_count: number;
  anomalies: AuditAnomalyItem[];
  summary: string;
}

export interface CourseEvaluationDetail {
  course_key: string;
  course_code: string;
  course_title: string;
  credits: number;
  credit_breakdown?: string;
  include_in_sgpa: boolean;
  is_english_or_elective: boolean;

  internal_marks: number | string;
  internal_max: number;
  internal_pass: boolean;

  external_marks: number | string;
  external_max: number;
  external_pass: boolean;
  grace_awarded: number;
  effective_external: number | string;

  total_marks: number | string;
  total_max: number;
  aggregate_pass: boolean;

  percentage: number;
  letter_grade: LetterGrade | string;
  grade_point: number;
  credit_points: number;

  is_pass: boolean;
  is_absent: boolean;
  is_exempted?: boolean;
  grace_notes?: string | null;
  sub_components?: Record<string, unknown>;
}

export interface EvaluatedStudentRecord {
  roll_no: string;
  enroll_no: string;
  student_name: string;
  father_name: string;
  courses: Record<string, CourseEvaluationDetail>;

  total_marks_obtained: number;
  total_marks_max: number;
  overall_percentage: number;

  semester_credit_score: number;
  total_sgpa_credits: number;
  sgpa: number;

  result_status: string;
  failed_courses: string[];
  total_grace: number;
  grace_details: Record<string, number>;
  raw_remarks?: string | null;
}

export interface EvaluationBatchResult {
  success: boolean;
  branding: string;
  total_candidates: number;
  passed_count: number;
  failed_count: number;
  grace_awarded_count: number;
  results: EvaluatedStudentRecord[];
  warnings: string[];
}

export interface UploadAuditResponse {
  success: boolean;
  audit_report: QualityAuditReport;
  evaluation: EvaluationBatchResult;
}

export interface MarksheetTemplateConfig {
  institution_name: string;
  college_name: string;
  college_code: string;
  exam_title: string;
  place: string;
  issue_date: string;
  paper_size: string;
  top_margin: string;
  bottom_margin: string;
  left_margin: string;
  right_margin: string;
  row_padding: "compact" | "standard" | "relaxed";
  font_size_header: string;
  font_size_demo: string;
  font_size_table: string;
  font_size_signatures: string;
  col_label_sno: string;
  col_label_course_code: string;
  col_label_course_title: string;
  col_label_credits: string;
  col_label_internal: string;
  col_label_external: string;
  col_label_total: string;
  col_label_grade: string;
  col_label_grade_point: string;
  col_label_credit_points: string;
  show_sno: boolean;
  show_course_code: boolean;
  show_course_title: boolean;
  show_credits: boolean;
  show_internal: boolean;
  show_external: boolean;
  show_total: boolean;
  show_grade: boolean;
  show_grade_point: boolean;
  show_credit_points: boolean;
  sig1_title: string;
  sig2_title: string;
  sig3_title: string;
  sig4_title: string;
  show_sig4: boolean;
  statutory_note: string;
}

export interface DebugCategoryItem {
  category: "PASS" | "GRACE" | "FAIL" | "DISTINCTION" | "BORDERLINE";
  category_title: string;
  badge_color: string;
  description: string;
  source: string;
  student: EvaluatedStudentRecord;
  telemetry: {
    rule: string;
    grace_used: number;
    sgpa: number | null;
    percentage: number;
    verdict: string;
  };
}

export interface CandidateAuditDetail {
  roll_no: string;
  student_name: string;
  father_name: string;
  result_status: string;
  overall_percentage: number;
  sgpa: number | null;
  grace_marks_used: number;
  is_inc_compliant: boolean;
  status_category: "PASS" | "PASS_WITH_GRACE" | "FAIL" | "FLAGGED";
  compliance_notes: string[];
  anomalies: string[];
}

export interface IncGazetteAuditReport {
  success: boolean;
  compliance_verdict: string;
  total_candidates: number;
  clean_passes: number;
  grace_passes: number;
  failures: number;
  anomalies_count: number;
  can_proceed_to_print: boolean;
  gazette_clauses_applied: string[];
  candidates: CandidateAuditDetail[];
}

export type WorkflowStatus = "DRAFT" | "SCRUTINIZED" | "APPROVED" | "LOCKED";
export type UserRole = "Scrutiny Committee" | "Admin / Sub-Dean" | "Operator / Data Entry";

export interface AuditLogEntry {
  id: number;
  timestamp: string | null;
  modified_by: string;
  entity_type?: string;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  change_reason: string;
}

export interface StudentWorkflowSummary {
  student_id?: number;
  roll_no: string;
  enrollment_no: string;
  student_name: string;
  father_name?: string;
  semester_number: number;
  workflow_status: WorkflowStatus;
  sgpa: number | null;
  result_status?: string;
  workflow_updated_at: string | null;
  workflow_updated_by: string | null;
  workflow_remarks: string | null;
  is_locked: boolean;
}

export interface SemesterWorkflowSummary {
  semester_number: number;
  batch_id?: number | null;
  total_students: number;
  counts: Record<WorkflowStatus, number>;
  overall_status: WorkflowStatus;
  students: StudentWorkflowSummary[];
}



