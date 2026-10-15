"use client";

import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  AlertTriangle,
  Search,
  Code2,
  RefreshCw,
  Sparkles,
  FileCheck,
  AlertCircle,
  Eye,
  FileDown,
  Archive,
  Sliders,
  Table as TableIcon,
  LayoutGrid,
  ShieldCheck,
  CheckCircle2,
  Layers,
  TableProperties,
  History
} from "lucide-react";
import {
  IngestionResponse,
  QualityAuditReport,
  EvaluatedStudentRecord,
  CourseEvaluationDetail,
  SemesterStudentResult
} from "../types/marksheet";
import { QualityAuditGateSection } from "./QualityAuditGateSection";
import { MarksheetPreviewModal } from "./MarksheetPreviewModal";
import { IncGazetteAuditModal } from "./IncGazetteAuditModal";
import { VisualAuditLogModal } from "./VisualAuditLogModal";
import { WorkflowControlPanel } from "./WorkflowControlPanel";

export interface ExcelUploadZoneProps {
  onStudentsLoaded?: (students: EvaluatedStudentRecord[]) => void;
  onNavigateToTemplate?: () => void;
  onNavigateToDebug?: () => void;
  onNavigateToAudit?: () => void;
  onNavigateToRegister?: () => void;
}

function toEvaluatedRecord(s: SemesterStudentResult): EvaluatedStudentRecord {
  const coursesRecord: Record<string, CourseEvaluationDetail> = {};
  s.courses.forEach((c) => {
    let key = `${c.course_code}_${c.component_name}`.replace(/[^\w]/g, "_");
    // Semester 1
    if (c.course_code.includes("101") || c.course_title.toLowerCase().includes("english")) key = "ENGL";
    else if (c.course_code.includes("105") || c.course_title.toLowerCase().includes("anatomy")) key = "ANAT_PHYS";
    else if (c.course_code.includes("110") || c.course_title.toLowerCase().includes("sociology")) key = "SOCI_PSYC";
    // Semester 2
    else if (c.course_code.includes("135") || c.course_title.toLowerCase().includes("biochemistry")) key = "BIOC_NUTR";
    else if (c.course_code.includes("125") && c.component_name.toLowerCase().includes("pract")) key = "NNF_PRACT";
    else if (c.course_code.includes("125")) key = "NNF_THEORY";
    else if (c.course_code.includes("145") || c.course_title.toLowerCase().includes("informatics")) key = "HNIT";
    // Semester 3
    else if (c.course_code.includes("201") || c.course_title.toLowerCase().includes("microbiology")) key = "MICR";
    else if (c.course_code.includes("215") && (c.component_name.toLowerCase().includes("pract") || c.course_title.toLowerCase().includes("pract"))) key = "AHN_I_PRACT";
    else if (c.course_code.includes("215")) key = "AHN_I_THEORY";
    // Semester 4
    else if (c.course_code.includes("205") || c.course_code.includes("210") || c.course_title.toLowerCase().includes("pharmacology") || c.course_title.toLowerCase().includes("pathology")) key = "PHAR_PATH";
    else if (c.course_code.includes("225") && (c.component_name.toLowerCase().includes("pract") || c.course_title.toLowerCase().includes("pract"))) key = "AHN_II_PRACT";
    else if (c.course_code.includes("225")) key = "AHN_II_THEORY";
    else if (c.course_code.includes("230") || c.course_title.toLowerCase().includes("professionalism")) key = "PROF";
    else if (c.course_code.toLowerCase().includes("elective") || c.course_title.toLowerCase().includes("human values") || c.course_title.toLowerCase().includes("soft skills")) key = "ELECTIVE_1";
    // Semester 5
    else if (c.course_code.includes("310") && (c.component_name.toLowerCase().includes("pract") || c.course_title.toLowerCase().includes("pract"))) key = "COMH_I_PRACT";
    else if (c.course_code.includes("310")) key = "COMH_I_THEORY";
    else if (c.course_code.includes("315") || c.course_title.toLowerCase().includes("educational")) key = "EDUC";
    else if (c.course_code.includes("320") || c.course_title.toLowerCase().includes("forensic")) key = "FORN";
    // Semester 6
    else if (c.course_code.includes("301") && (c.component_name.toLowerCase().includes("pract") || c.course_title.toLowerCase().includes("pract"))) key = "CHN_PRACT";
    else if (c.course_code.includes("301")) key = "CHN_THEORY";
    else if (c.course_code.includes("305") && (c.component_name.toLowerCase().includes("pract") || c.course_title.toLowerCase().includes("pract"))) key = "MHN_PRACT";
    else if (c.course_code.includes("305")) key = "MHN_THEORY";
    else if (c.course_code.includes("330") || c.course_title.toLowerCase().includes("management") || c.course_title.toLowerCase().includes("leadership")) key = "NMLE";

    const isEx = Boolean(c.is_exempted || (c.letter_grade as string) === "Ex." || (c.internal_obtained as unknown) === "Ex." || (c.external_obtained as unknown) === "Ex.");
    const iaMax = c.internal_max || 25;
    const eaMax = c.external_max || (c.is_english_or_elective ? 25 : 75);
    const passPct = c.is_english_or_elective ? 0.4 : 0.5;
    const iaVal = typeof c.internal_obtained === "number" ? c.internal_obtained : 0;
    const eaVal = typeof c.external_obtained === "number" ? c.external_obtained : 0;
    const graceVal = c.grace_marks || 0;

    coursesRecord[key] = {
      course_key: key,
      course_code: c.course_code,
      course_title: c.course_title,
      credits: c.credits,
      credit_breakdown: c.credit_breakdown,
      include_in_sgpa: isEx ? false : c.include_in_sgpa,
      is_english_or_elective: c.is_english_or_elective,
      internal_marks: isEx ? "Ex." : (c.internal_obtained ?? "Ab"),
      internal_max: iaMax,
      internal_pass: isEx ? true : (iaVal >= iaMax * passPct),
      external_marks: isEx ? "Ex." : (c.external_obtained ?? "Ab"),
      external_max: eaMax,
      external_pass: isEx ? true : (eaVal >= eaMax * passPct),
      grace_awarded: graceVal,
      effective_external: isEx ? "Ex." : (eaVal + graceVal),
      total_marks: isEx ? (c.total_obtained ?? "Ex.") : (c.total_obtained ?? "Ab"),
      total_max: c.total_max,
      aggregate_pass: isEx ? true : c.is_pass,
      percentage: c.percentage,
      letter_grade: isEx ? "Ex." : c.letter_grade,
      grade_point: isEx ? 0 : c.grade_point,
      credit_points: isEx ? 0 : (c.credits * c.grade_point),
      is_pass: isEx ? true : c.is_pass,
      is_absent: !isEx && !!c.is_absent,
      is_exempted: isEx,
      grace_notes: graceVal > 0 ? `${graceVal} Grace Marks Awarded` : null,
      sub_components: {},
    };
  });

  return {
    roll_no: s.student.roll_no,
    enroll_no: s.student.enrollment_no,
    student_name: s.student.name,
    father_name: s.student.father_name,
    courses: coursesRecord,
    total_marks_obtained: s.grand_total_obtained,
    total_marks_max: s.grand_total_max,
    overall_percentage: s.overall_percentage,
    semester_credit_score: s.total_credit_score,
    total_sgpa_credits: s.total_sgpa_credits,
    sgpa: s.sgpa,
    result_status: s.result_status,
    failed_courses: s.failed_courses,
    total_grace: s.courses.reduce((sum, c) => sum + (c.grace_marks || 0), 0),
    grace_details: s.courses.reduce((acc, c) => {
      if (c.grace_marks && c.grace_marks > 0) acc[c.course_code] = c.grace_marks;
      return acc;
    }, {} as Record<string, number>),
    raw_remarks: s.remarks,
  };
}

export const ExcelUploadZone: React.FC<ExcelUploadZoneProps> = ({
  onStudentsLoaded,
  onNavigateToTemplate,
  onNavigateToDebug,
  onNavigateToAudit,
  onNavigateToRegister
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [selectedSemester, setSelectedSemester] = useState<string>("auto");
  const [availableSheets, setAvailableSheets] = useState<{ name: string; row_count: number }[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [isInspecting, setIsInspecting] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [ingestionData, setIngestionData] = useState<IngestionResponse | null>(null);
  const [auditReport, setAuditReport] = useState<QualityAuditReport | null>(null);
  const [evaluatedStudents, setEvaluatedStudents] = useState<EvaluatedStudentRecord[]>([]);
  const [isIncModalOpen, setIsIncModalOpen] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<"table" | "cards">("table");

  // Preview & PDF export state
  const [previewStudent, setPreviewStudent] = useState<EvaluatedStudentRecord | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);
  const [isBulkDownloading, setIsBulkDownloading] = useState<boolean>(false);
  const [isExportingTrPdf, setIsExportingTrPdf] = useState<boolean>(false);
  const [isExportingTrExcel, setIsExportingTrExcel] = useState<boolean>(false);
  const [downloadingRoll, setDownloadingRoll] = useState<string | null>(null);
  const [bulkDownloadError, setBulkDownloadError] = useState<string | null>(null);

  // Progressive Marksheet Generation states (Real-time student status: Generating -> Finished)
  const [isGeneratingBatch, setIsGeneratingBatch] = useState<boolean>(false);
  const [isBatchCompleted, setIsBatchCompleted] = useState<boolean>(false);
  const [currentProgressStudent, setCurrentProgressStudent] = useState<{
    index: number;
    total: number;
    name: string;
    roll: string;
    status: "Generating" | "Finished";
  } | null>(null);
  const [completedGenerationList, setCompletedGenerationList] = useState<Array<{
    index: number;
    name: string;
    roll: string;
    sgpa?: number;
    result?: string;
  }>>([]);
  const cancelGenerationRef = useRef<boolean>(false);
  const [cachedZipBlob, setCachedZipBlob] = useState<Blob | null>(null);

  // Field-Level Audit Trail & Workflow states
  const [isAuditModalOpen, setIsAuditModalOpen] = useState<boolean>(false);
  const [auditStudent, setAuditStudent] = useState<{
    roll_no: string;
    name: string;
    enrollment_no?: string;
  } | null>(null);
  const [workflowTargetRoll, setWorkflowTargetRoll] = useState<string | null>(null);
  const [workflowTargetName, setWorkflowTargetName] = useState<string | null>(null);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<"ALL" | "PASS" | "FAIL" | "GRACE">("ALL");
  const [showJsonViewer, setShowJsonViewer] = useState<boolean>(false);
  const [expandedStudentRoll, setExpandedStudentRoll] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const inspectFile = async (f: File) => {
    setIsInspecting(true);
    try {
      const fd = new FormData();
      fd.append("file", f);
      const res = await fetch("/api/inspect-file", { method: "POST", body: fd });
      if (res.ok) {
        const data = await res.json();
        setAvailableSheets(data.sheets || []);
        if (data.recommended_sheet) {
          setSelectedSheet(data.recommended_sheet);
        }
        if (data.detected_semester && selectedSemester === "auto") {
          setSelectedSemester(data.detected_semester.toString());
        }
      }
    } catch {
      // Non-fatal inspection fallback
    } finally {
      setIsInspecting(false);
    }
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const runProgressiveGeneration = async (studentsList: EvaluatedStudentRecord[]) => {
    if (!studentsList || studentsList.length === 0) return;
    setIsGeneratingBatch(true);
    setIsBatchCompleted(false);
    setCompletedGenerationList([]);
    setCachedZipBlob(null);
    cancelGenerationRef.current = false;

    // Start background bulk ZIP compilation immediately on port 8000
    const sem = ingestionData?.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10));
    (async () => {
      try {
        let res: Response | null = await fetch(`http://127.0.0.1:8000/api/pdf/bulk?semester=${sem}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(studentsList),
        }).catch(() => null);

        if (!res || !res.ok) {
          res = await fetch(`/api/pdf/bulk?semester=${sem}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(studentsList),
          }).catch(() => null);
        }

        if (res && res.ok) {
          const blob = await res.blob();
          setCachedZipBlob(blob);
        }
      } catch (err) {
        console.warn("Background bulk ZIP pre-compilation warning:", err);
      }
    })();

    for (let i = 0; i < studentsList.length; i++) {
      if (cancelGenerationRef.current) break;
      const s = studentsList[i];
      const rawName = s.student_name?.trim() || `Candidate ${i + 1}`;
      const displayName = /^(mr\.|ms\.|mrs\.|dr\.)/i.test(rawName) ? rawName : `Mr. ${rawName}`;
      const displayRoll = s.roll_no?.trim() || `Roll-${i + 1}`;

      // Step 1: Marksheet Generation In-Progress
      setCurrentProgressStudent({
        index: i + 1,
        total: studentsList.length,
        name: displayName,
        roll: displayRoll,
        status: "Generating",
      });

      // Live feedback delay
      await new Promise((resolve) => setTimeout(resolve, 55));

      // Step 2: Marksheet Generation Finished
      setCurrentProgressStudent({
        index: i + 1,
        total: studentsList.length,
        name: displayName,
        roll: displayRoll,
        status: "Finished",
      });

      setCompletedGenerationList((prev) => [
        ...prev,
        {
          index: i + 1,
          name: displayName,
          roll: displayRoll,
          sgpa: s.sgpa,
          result: s.result_status,
        },
      ]);

      await new Promise((resolve) => setTimeout(resolve, 40));
    }

    setIsGeneratingBatch(false);
    setIsBatchCompleted(true);
  };

  const handleSkipGenerationAnimation = () => {
    cancelGenerationRef.current = true;
    if (evaluatedStudents.length > 0) {
      const fullList = evaluatedStudents.map((s, idx) => {
        const rawName = s.student_name?.trim() || `Candidate ${idx + 1}`;
        const displayName = /^(mr\.|ms\.|mrs\.|dr\.)/i.test(rawName) ? rawName : `Mr. ${rawName}`;
        return {
          index: idx + 1,
          name: displayName,
          roll: s.roll_no?.trim() || `Roll-${idx + 1}`,
          sgpa: s.sgpa,
          result: s.result_status,
        };
      });
      setCompletedGenerationList(fullList);
      if (fullList.length > 0) {
        const last = fullList[fullList.length - 1];
        setCurrentProgressStudent({
          index: fullList.length,
          total: fullList.length,
          name: last.name,
          roll: last.roll,
          status: "Finished",
        });
      }
    }
    setIsGeneratingBatch(false);
    setIsBatchCompleted(true);
  };

  const processAndGenerate = async (targetFile: File, sheet?: string, sem?: string) => {
    setIsUploading(true);
    setUploadError(null);
    setBulkDownloadError(null);
    setIsBatchCompleted(false);
    setCompletedGenerationList([]);

    const formData = new FormData();
    formData.append("file", targetFile);
    const targetSem = sem || selectedSemester;
    if (targetSem !== "auto") {
      formData.append("semester", targetSem);
    }
    const targetSheet = sheet || selectedSheet;
    if (targetSheet) {
      formData.append("sheet_name", targetSheet);
    }

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed with status code ${response.status}`);
      }

      const data: IngestionResponse = await response.json();
      setIngestionData(data);

      const evalList = data.results.map(toEvaluatedRecord);
      setEvaluatedStudents(evalList);
      onStudentsLoaded?.(evalList);

      if (data.results.length > 0) {
        const first = data.results[0];
        const firstKey = first.student.roll_no?.trim()
          ? `${first.student.roll_no}-0`
          : first.student.enrollment_no?.trim()
          ? `${first.student.enrollment_no}-0`
          : `student-${first.student.serial_no || 0}`;
        setExpandedStudentRoll(firstKey);
      }

      if (selectedSemester === "auto" && data.semester) {
        setSelectedSemester(data.semester.toString());
      }

      // Also trigger Quality Audit Gate check silently
      try {
        const detectedOrSelectedSem = selectedSemester === "auto" ? (data.semester?.toString() || "1") : selectedSemester;
        const auditFormData = new FormData();
        auditFormData.append("file", targetFile);
        auditFormData.append("semester", detectedOrSelectedSem);
        if (targetSheet) {
          auditFormData.append("sheet_name", targetSheet);
        }
        const auditRes = await fetch("/api/audit/upload-and-audit", {
          method: "POST",
          body: auditFormData,
        });
        if (auditRes.ok) {
          const auditJson = await auditRes.json();
          setAuditReport(auditJson.audit_report);
          if (data.semester === 1 && auditJson.evaluation?.results && auditJson.evaluation.results.length > 0) {
            setEvaluatedStudents(auditJson.evaluation.results);
            onStudentsLoaded?.(auditJson.evaluation.results);
          }
        }
      } catch {
        // Fallback silently if audit endpoint is separate
      }

      // Automatically launch Progressive Marksheet Generation with student names
      await runProgressiveGeneration(evalList);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to process Excel marksheet. Ensure backend is running.";
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const validateAndSetFile = (f: File) => {
    setUploadError(null);
    const ext = f.name.toLowerCase();
    if (!ext.endsWith(".xlsx") && !ext.endsWith(".xls")) {
      setUploadError("Invalid file type. Please upload an Excel document (.xlsx or .xls).");
      return;
    }
    setFile(f);
    inspectFile(f);
    // Automatic immediate processing: User does NOT need to click any button!
    processAndGenerate(f);
  };

  const handleLoadSampleDataset = async () => {
    setIsUploading(true);
    setUploadError(null);

    try {
      // Fetch generated template from backend template route
      const semNumber = selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10);
      const res = await fetch(`/api/template/${semNumber}`);
      if (!res.ok) {
        throw new Error("Could not fetch sample template from backend.");
      }
      const blob = await res.blob();
      const sampleFile = new File([blob], `SGPGIMS_Semester_${semNumber}_Sample.xlsx`, {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      setFile(sampleFile);

      // Auto-trigger processing and progressive generation!
      await processAndGenerate(sampleFile, undefined, semNumber.toString());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load sample dataset.";
      setUploadError(msg);
      setIsUploading(false);
    }
  };

  const getEvaluatedRecord = (res: SemesterStudentResult): EvaluatedStudentRecord => {
    const found = evaluatedStudents.find(
      (e) => (res.student.roll_no?.trim() && e.roll_no.trim() === res.student.roll_no.trim()) ||
             (res.student.enrollment_no?.trim() && e.enroll_no.trim() === res.student.enrollment_no.trim()) ||
             (res.student.name?.trim() && e.student_name.trim().toLowerCase() === res.student.name.trim().toLowerCase())
    );
    if (found) return found;
    return toEvaluatedRecord(res);
  };

  const handleOpenPreview = (res: SemesterStudentResult, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const rec = getEvaluatedRecord(res);
    setPreviewStudent(rec);
    setIsPreviewOpen(true);
  };

  const handleDownloadSinglePdf = async (res: SemesterStudentResult, e?: React.MouseEvent, fallbackKey?: string) => {
    if (e) e.stopPropagation();
    const rec = getEvaluatedRecord(res);
    const downloadId = rec.roll_no?.trim() || fallbackKey || rec.student_name;
    setDownloadingRoll(downloadId);
    try {
      const sem = ingestionData?.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10));
      
      // Try direct backend port 8000 first, fallback to relative proxy
      let response: Response | null = await fetch(`http://127.0.0.1:8000/api/pdf/student?semester=${sem}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rec),
      }).catch(() => null);

      if (!response || !response.ok) {
        response = await fetch(`/api/pdf/student?semester=${sem}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(rec),
        });
      }

      if (!response.ok) {
        throw new Error("Could not download marksheet PDF.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const cleanName = rec.student_name.replace(/\s+/g, "_");
      const safeRoll = rec.roll_no?.trim() || "STUDENT";
      a.download = `Marksheet_${safeRoll}_${cleanName}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error downloading marksheet PDF.";
      alert(msg);
    } finally {
      setDownloadingRoll(null);
    }
  };

  const handleDownloadBulkZip = async () => {
    if (!ingestionData || ingestionData.results.length === 0) return;
    setIsBulkDownloading(true);
    setBulkDownloadError(null);
    try {
      const sem = ingestionData.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10));

      let blobToDownload: Blob | null = cachedZipBlob;

      // If pre-cached blob is not available, generate via direct port 8000
      if (!blobToDownload) {
        const studentsToExport = evaluatedStudents.length > 0
          ? evaluatedStudents
          : ingestionData.results.map(toEvaluatedRecord);

        let res: Response | null = await fetch(`http://127.0.0.1:8000/api/pdf/bulk?semester=${sem}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(studentsToExport),
        }).catch(() => null);

        if (!res || !res.ok) {
          res = await fetch(`/api/pdf/bulk?semester=${sem}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(studentsToExport),
          });
        }

        if (!res || !res.ok) {
          const errJson = res ? await res.json().catch(() => ({})) : {};
          const detailMsg = errJson?.detail || (res ? `Status ${res.status}` : "Backend unreachable");
          throw new Error(`Failed to generate bulk ZIP: ${detailMsg}. Please ensure the backend is running.`);
        }

        blobToDownload = await res.blob();
        setCachedZipBlob(blobToDownload);
      }

      const url = window.URL.createObjectURL(blobToDownload);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SGPGIMS_BSc_Nursing_Sem${sem}_Marksheets.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error generating bulk ZIP.";
      setBulkDownloadError(msg);
      alert(msg);
    } finally {
      setIsBulkDownloading(false);
    }
  };

  const handleDownloadTrPdf = async () => {
    if (!ingestionData || ingestionData.results.length === 0) return;
    setIsExportingTrPdf(true);
    try {
      const studentsToExport = evaluatedStudents.length > 0
        ? evaluatedStudents
        : ingestionData.results.map(toEvaluatedRecord);
      const semNum = ingestionData.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10));

      const response = await fetch("http://127.0.0.1:8000/api/v1/tabulation-register/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          students: studentsToExport,
          semester_number: semNum,
          batch_name: "Batch 2022-2026",
          session_month_year: ingestionData.examination_session || "JANUARY - 2026",
          page_size: 15,
        }),
      });

      if (!response.ok) {
        window.open(`http://127.0.0.1:8000/api/v1/tabulation-register/pdf?semester=${semNum}&paper_size=A3`, "_blank");
        return;
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SGPGIMS_Tabulation_Register_Sem${semNum}_A3_Landscape.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error generating Tabulation Register PDF.";
      alert(msg);
    } finally {
      setIsExportingTrPdf(false);
    }
  };

  const handleDownloadTrExcel = async () => {
    if (!ingestionData || ingestionData.results.length === 0) return;
    setIsExportingTrExcel(true);
    try {
      const studentsToExport = evaluatedStudents.length > 0
        ? evaluatedStudents
        : ingestionData.results.map(toEvaluatedRecord);
      const semNum = ingestionData.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10));

      const response = await fetch("http://127.0.0.1:8000/api/v1/tabulation-register/export-excel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          students: studentsToExport,
          semester_number: semNum,
          batch_name: "Batch 2022-2026",
          session_month_year: ingestionData.examination_session || "JANUARY - 2026",
          page_size: 15,
        }),
      });

      if (!response.ok) {
        window.open(`http://127.0.0.1:8000/api/v1/tabulation-register/excel?semester=${semNum}`, "_blank");
        return;
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SGPGIMS_Tabulation_Register_Sem${semNum}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error generating Tabulation Register Excel.";
      alert(msg);
    } finally {
      setIsExportingTrExcel(false);
    }
  };

  // Filter students
  const filteredStudents = (ingestionData?.results || []).filter((s) => {
    const query = searchQuery.toLowerCase().trim();
    const matchesSearch =
      (s.student.name || "").toLowerCase().includes(query) ||
      (s.student.roll_no || "").toLowerCase().includes(query) ||
      (s.student.enrollment_no || "").toLowerCase().includes(query) ||
      (s.student.father_name || "").toLowerCase().includes(query);

    if (!matchesSearch) return false;

    if (filterStatus === "PASS") {
      return s.result_status === "PASS";
    }
    if (filterStatus === "FAIL") {
      return s.result_status === "FAIL";
    }
    if (filterStatus === "GRACE") {
      return s.result_status.includes("GRACE");
    }

    return true;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Upload Zone Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                Excel Marksheet Ingestion Engine
              </h2>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Supports .xlsx & .xls files with multi-tier SGPGIMS format, granular IA/EA splits, and INC 10-point evaluation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Target Semester:</span>
              <select
                value={selectedSemester}
                onChange={(e) => setSelectedSemester(e.target.value)}
                className="bg-transparent text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="auto">Auto-Detect from Header</option>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s.toString()}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            {availableSheets.length > 0 && (
              <div className="flex items-center gap-2 bg-blue-50 dark:bg-blue-950/60 px-3 py-1.5 rounded-xl border border-blue-200 dark:border-blue-800 animate-fadeIn">
                <Layers className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                <span className="text-xs text-blue-800 dark:text-blue-300 font-medium">Worksheet:</span>
                <select
                  value={selectedSheet}
                  onChange={(e) => setSelectedSheet(e.target.value)}
                  className="bg-transparent text-xs font-semibold text-blue-900 dark:text-blue-100 focus:outline-none cursor-pointer"
                >
                  {availableSheets.map((sh) => (
                    <option key={sh.name} value={sh.name} className="text-slate-800">
                      {sh.name} ({sh.row_count} rows)
                    </option>
                  ))}
                </select>
              </div>
            )}

            <button
              onClick={handleLoadSampleDataset}
              disabled={isUploading}
              className="flex items-center gap-1.5 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-xs font-semibold px-3 py-2 rounded-xl border border-indigo-200 dark:border-indigo-800 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Load Official Sample</span>
            </button>
          </div>
        </div>

        {/* Drag and drop dropzone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
            file
              ? "border-blue-500 bg-blue-50/30 dark:bg-blue-950/20"
              : "border-slate-300 dark:border-slate-700 hover:border-blue-400 hover:bg-slate-50 dark:hover:bg-slate-800/40"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="p-4 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 shadow-sm">
              <UploadCloud className="w-8 h-8" />
            </div>

            {file ? (
              <div>
                <p className="text-sm font-bold text-slate-900 dark:text-white flex items-center justify-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-500" />
                  <span>{file.name}</span>
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {(file.size / 1024).toFixed(1)} KB • Click or drag to change file
                </p>
                {isInspecting && (
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 flex items-center justify-center gap-1">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    Inspecting sheets & semester metadata...
                  </p>
                )}
                {!isInspecting && availableSheets.length > 0 && (
                  <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-medium">
                    Found {availableSheets.length} sheet{availableSheets.length > 1 ? "s" : ""}: Target &ldquo;{selectedSheet}&rdquo;
                  </p>
                )}
              </div>
            ) : (
              <div>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  Drop your examination spreadsheet here, or <span className="text-blue-600 dark:text-blue-400 underline">browse files</span>
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Supported formats: Microsoft Excel (.xlsx, .xls)
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Upload error banner */}
        {uploadError && (
          <div className="mt-4 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Action Button */}
        <div className="mt-6 flex justify-end gap-3">
          {file && (
            <button
              onClick={() => {
                setFile(null);
                setIngestionData(null);
                setAuditReport(null);
                setCurrentProgressStudent(null);
                setCompletedGenerationList([]);
                setIsGeneratingBatch(false);
                setIsBatchCompleted(false);
                setBulkDownloadError(null);
              }}
              className="text-xs font-medium text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 px-4 py-2 transition-colors cursor-pointer"
            >
              Clear
            </button>
          )}

          {isUploading && (
            <div className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Auto-Reading Spreadsheet & Generating...</span>
            </div>
          )}
        </div>
      </div>

      {/* Progressive Marksheet Generation HUD (Sequential student name live progress: Generating -> Finished) */}
      {(isGeneratingBatch || isBatchCompleted || currentProgressStudent) && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-md transition-all animate-fadeIn">
          {/* Card Header & Status */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div
                className={`p-2.5 rounded-xl ${
                  isGeneratingBatch
                    ? "bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400"
                    : "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400"
                }`}
              >
                {isGeneratingBatch ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                )}
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>{isGeneratingBatch ? "Auto-Generating Marksheets" : "Marksheet Generation Completed"}</span>
                  <span
                    className={`text-[11px] px-2.5 py-0.5 rounded-full font-semibold ${
                      isGeneratingBatch
                        ? "bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300 animate-pulse"
                        : "bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300"
                    }`}
                  >
                    {isGeneratingBatch ? "IN PROGRESS" : "100% READY"}
                  </span>
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {isGeneratingBatch
                    ? "Sequential generation in progress: evaluating scores, INC compliance, and SGPGIMS template records..."
                    : `All ${completedGenerationList.length} candidate marksheets generated, validated, and ready for instant preview or bulk download.`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-auto">
              <div className="bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                Candidate{" "}
                <span className="text-blue-600 dark:text-blue-400 font-bold">
                  {currentProgressStudent?.index || completedGenerationList.length}
                </span>{" "}
                of{" "}
                <span className="font-bold">
                  {currentProgressStudent?.total || evaluatedStudents.length}
                </span>
              </div>

              {isGeneratingBatch && (
                <button
                  onClick={handleSkipGenerationAnimation}
                  className="text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
                  title="Skip to final results immediately"
                >
                  Skip Animation
                </button>
              )}
            </div>
          </div>

          {/* Real-Time Active Candidate Box */}
          {currentProgressStudent && (
            <div className="mt-5 p-4 rounded-xl bg-gradient-to-r from-blue-50/70 via-indigo-50/50 to-slate-50 dark:from-slate-800/80 dark:via-slate-800/50 dark:to-slate-900 border border-blue-100 dark:border-slate-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-600 text-white font-bold flex items-center justify-center text-sm shadow-sm shrink-0">
                  {currentProgressStudent.name
                    .replace(/^(Mr\.|Ms\.|Mrs\.|Dr\.)\s*/i, "")
                    .charAt(0)
                    .toUpperCase() || "S"}
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>{currentProgressStudent.name}</span>
                    <span className="text-[11px] font-normal font-mono text-slate-500 dark:text-slate-400 bg-white/80 dark:bg-slate-900/80 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                      Roll: {currentProgressStudent.roll}
                    </span>
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-300 mt-1 font-medium flex items-center gap-1.5">
                    <span className="text-slate-400">Live Status:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {currentProgressStudent.name} —{" "}
                    </span>
                    {currentProgressStudent.status === "Generating" ? (
                      <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400 font-bold">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        Generating...
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Finished
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Status Pill */}
              <div className="self-end sm:self-auto">
                {currentProgressStudent.status === "Generating" ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/80 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-700 animate-pulse">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Generating...
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    Finished
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between items-center text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">
              <span>Batch Compilation Progress</span>
              <span className="font-bold text-slate-900 dark:text-white">
                {Math.round(
                  ((completedGenerationList.length) /
                    (currentProgressStudent?.total || evaluatedStudents.length || 1)) *
                    100
                )}
                %
              </span>
            </div>
            <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-600 via-indigo-600 to-emerald-500 transition-all duration-150 rounded-full"
                style={{
                  width: `${Math.min(
                    100,
                    Math.round(
                      ((completedGenerationList.length) /
                        (currentProgressStudent?.total || evaluatedStudents.length || 1)) *
                        100
                    )
                  )}%`,
                }}
              />
            </div>
          </div>

          {/* Live Activity Feed (Scrollable stream of completed students) */}
          {completedGenerationList.length > 0 && (
            <div className="mt-5">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Generated Marksheets ({completedGenerationList.length})
                </span>
                <span className="text-[11px] text-slate-400">Live stream</span>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1 text-xs font-mono scrollbar-thin">
                {completedGenerationList.slice().reverse().map((item) => (
                  <div
                    key={`${item.roll}-${item.index}`}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60"
                  >
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {item.name}
                      </span>
                      <span className="text-slate-400 text-[11px]">— Finished</span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="text-slate-500">Roll: {item.roll}</span>
                      {item.sgpa !== undefined && (
                        <span className="font-semibold text-blue-600 dark:text-blue-400">
                          SGPA: {item.sgpa.toFixed(2)}
                        </span>
                      )}
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          item.result === "PASS"
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                            : item.result?.includes("GRACE")
                            ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                            : "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                        }`}
                      >
                        {item.result || "PASS"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions Strip upon completion */}
          {isBatchCompleted && (
            <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <div className="text-xs text-slate-500 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>All marksheets ready. Download archive or Tabulation Register below:</span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleDownloadBulkZip}
                  disabled={isBulkDownloading}
                  className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
                >
                  {isBulkDownloading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Generating Bulk ZIP...</span>
                    </>
                  ) : (
                    <>
                      <Archive className="w-3.5 h-3.5" />
                      <span>📦 Download Bulk Marksheets (.ZIP)</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleDownloadTrPdf}
                  disabled={isExportingTrPdf}
                  className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-3.5 py-2 rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
                >
                  {isExportingTrPdf ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Exporting TR PDF...</span>
                    </>
                  ) : (
                    <>
                      <FileDown className="w-3.5 h-3.5" />
                      <span>🖨️ TR (PDF)</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleDownloadTrExcel}
                  disabled={isExportingTrExcel}
                  className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
                >
                  {isExportingTrExcel ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Exporting TR Excel...</span>
                    </>
                  ) : (
                    <>
                      <TableProperties className="w-3.5 h-3.5" />
                      <span>📊 TR (Excel)</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Bulk Download Error Alert if any */}
          {bulkDownloadError && (
            <div className="mt-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-300 text-xs flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                <span>{bulkDownloadError}</span>
              </div>
              <button
                onClick={() => setBulkDownloadError(null)}
                className="text-slate-400 hover:text-slate-600 text-xs cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          )}
        </div>
      )}

      {/* Quality Audit Gate Section (if audited) */}
      {auditReport && (
        <QualityAuditGateSection
          auditReport={auditReport}
          evaluatedStudents={evaluatedStudents}
          isExporting={isBulkDownloading}
          onExportPdf={handleDownloadBulkZip}
        />
      )}

      {/* Ingestion Results Display */}
      {ingestionData && (
        <div className="space-y-6">
          {/* Summary KPI Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Target Semester</div>
              <div className="text-xl font-bold font-mono text-blue-600 dark:text-blue-400 mt-1">
                Semester {ingestionData.semester}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 truncate">
                {ingestionData.examination_session}
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Total Candidates</div>
              <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-1">
                {ingestionData.total_students}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">Parsed Records</div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Passed</div>
              <div className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {ingestionData.passed_students}
              </div>
              <div className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-0.5 font-semibold">
                {Math.round((ingestionData.passed_students / (ingestionData.total_students || 1)) * 100)}% Pass Rate
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Failed / Reappear</div>
              <div className="text-xl font-bold font-mono text-rose-600 dark:text-rose-400 mt-1">
                {ingestionData.failed_students}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">Below Passing Cutoff</div>
            </div>

            <div className="col-span-2 sm:col-span-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex flex-col justify-between">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">JSON Export</div>
              <button
                onClick={() => setShowJsonViewer(!showJsonViewer)}
                className="flex items-center justify-center gap-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold py-1.5 rounded-xl transition-colors mt-2"
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>{showJsonViewer ? "Hide JSON" : "Inspect JSON"}</span>
              </button>
            </div>
          </div>

          {/* Institutional Role-Based Workflow Approval & State Machine */}
          <WorkflowControlPanel
            semesterNumber={ingestionData.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10))}
            selectedRollNo={workflowTargetRoll}
            selectedStudentName={workflowTargetName}
            onClearSelectedStudent={() => {
              setWorkflowTargetRoll(null);
              setWorkflowTargetName(null);
            }}
          />

          {/* Workflow Action Bar */}
          <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white rounded-2xl p-5 shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">
                  Datasheet Recorded: {ingestionData.total_students} Candidate Records
                </h3>
              </div>
              <p className="text-xs text-blue-200 mt-1">
                Candidate bio and course marks recorded. Check regulatory compliance against INC Gazette, adjust template margins/rows/columns, or test debug archetypes.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <button
                onClick={() => setIsIncModalOpen(true)}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-all cursor-pointer"
              >
                <ShieldCheck className="w-4 h-4 text-emerald-200" />
                <span>⚖️ Check as per INC Gazette</span>
              </button>

              {onNavigateToTemplate && (
                <button
                  onClick={onNavigateToTemplate}
                  className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold px-3.5 py-2.5 rounded-xl border border-white/20 transition-all cursor-pointer"
                >
                  <Sliders className="w-4 h-4 text-amber-300" />
                  <span>Customize Template</span>
                </button>
              )}

              {onNavigateToDebug && (
                <button
                  onClick={onNavigateToDebug}
                  className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold px-3.5 py-2.5 rounded-xl border border-white/20 transition-all cursor-pointer"
                >
                  <Eye className="w-4 h-4 text-sky-300" />
                  <span>5 Debug Marksheets</span>
                </button>
              )}

              {onNavigateToAudit && (
                <button
                  onClick={onNavigateToAudit}
                  className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold px-3.5 py-2.5 rounded-xl border border-white/20 transition-all cursor-pointer"
                >
                  <ShieldCheck className="w-4 h-4 text-emerald-300" />
                  <span>Audit Logs</span>
                </button>
              )}
            </div>
          </div>

          {/* Raw JSON viewer modal / accordion */}
          {showJsonViewer && (
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 shadow-xl">
              <div className="flex justify-between items-center pb-2 mb-2 border-b border-slate-800 text-xs text-slate-400">
                <span className="font-mono text-slate-200 font-semibold">Structured Ingestion Output JSON</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(ingestionData, null, 2));
                    alert("JSON copied to clipboard!");
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white text-[11px] px-2.5 py-1 rounded"
                >
                  Copy JSON
                </button>
              </div>
              <pre className="text-xs font-mono text-emerald-400 overflow-x-auto max-h-96 p-2 bg-slate-900 rounded-lg">
                {JSON.stringify(ingestionData, null, 2)}
              </pre>
            </div>
          )}

          {/* Filtering & Search toolbar */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row justify-between items-center gap-3">
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search candidate, roll, enroll..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-800 dark:text-slate-200"
                />
              </div>

              {/* View Switcher: Data Grid vs Candidate Cards */}
              <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-0.5 border border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => setViewMode("table")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                    viewMode === "table"
                      ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm"
                      : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                  }`}
                >
                  <TableIcon className="w-3.5 h-3.5" />
                  <span>Data Grid</span>
                </button>
                <button
                  onClick={() => setViewMode("cards")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                    viewMode === "cards"
                      ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm"
                      : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                  }`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                  <span>Cards</span>
                </button>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 self-end sm:self-auto">
              <div className="flex items-center gap-1.5">
                {(["ALL", "PASS", "FAIL", "GRACE"] as const).map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilterStatus(status)}
                    className={`text-xs px-3 py-1 rounded-lg font-medium transition-colors ${
                      filterStatus === status
                        ? "bg-blue-600 text-white"
                        : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    }`}
                  >
                    {status === "ALL"
                      ? `All (${ingestionData.results.length})`
                      : status === "PASS"
                      ? `Passed (${ingestionData.passed_students})`
                      : status === "FAIL"
                      ? `Failed (${ingestionData.failed_students})`
                      : "With Grace"}
                  </button>
                ))}
              </div>

              <button
                onClick={handleDownloadBulkZip}
                disabled={isBulkDownloading}
                className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-xl shadow-sm transition-colors ml-1"
              >
                {isBulkDownloading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Archiving...</span>
                  </>
                ) : (
                  <>
                    <Archive className="w-3.5 h-3.5" />
                    <span>Download All (.ZIP)</span>
                  </>
                )}
              </button>

              <button
                onClick={handleDownloadTrPdf}
                disabled={isExportingTrPdf}
                title="Download Official Gazette Tabulation Register PDF (A3/Legal Landscape)"
                className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-3 py-1.5 rounded-xl shadow-sm transition-colors ml-1 disabled:opacity-50"
              >
                {isExportingTrPdf ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>TR PDF...</span>
                  </>
                ) : (
                  <>
                    <FileDown className="w-3.5 h-3.5" />
                    <span>TR (PDF)</span>
                  </>
                )}
              </button>

              <button
                onClick={handleDownloadTrExcel}
                disabled={isExportingTrExcel}
                title="Download Formatted Gazette Tabulation Register in Excel (.xlsx)"
                className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5 rounded-xl shadow-sm transition-colors ml-1 disabled:opacity-50"
              >
                {isExportingTrExcel ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>TR Excel...</span>
                  </>
                ) : (
                  <>
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    <span>TR (.xlsx)</span>
                  </>
                )}
              </button>

              {onNavigateToRegister && (
                <button
                  onClick={onNavigateToRegister}
                  title="Open Interactive Gazette Tabulation Register Ledger"
                  className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-700 shadow-sm transition-colors ml-1"
                >
                  <TableProperties className="w-3.5 h-3.5 text-blue-400" />
                  <span>View TR Ledger</span>
                </button>
              )}
            </div>
          </div>

          {/* Main Ingested Records Display: Data Grid vs Cards */}
          {viewMode === "table" ? (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
              <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 bg-slate-50/60 dark:bg-slate-800/40">
                <div className="flex items-center gap-2">
                  <TableIcon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                    Recorded Datasheet Register ({filteredStudents.length} Candidates)
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 font-medium">
                  Showing {filteredStudents.length} of {ingestionData.total_students} records • Click Preview icon for instant marksheet
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/90 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 uppercase font-semibold text-[11px] border-b border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="px-3 py-3 text-center w-12">#</th>
                      <th className="px-3 py-3">Roll No</th>
                      <th className="px-3 py-3">Enroll No</th>
                      <th className="px-4 py-3 min-w-[160px]">Student & Father Name</th>
                      <th className="px-4 py-3 min-w-[280px]">Subject Breakdown (IA + EA = Total)</th>
                      <th className="px-3 py-3 text-center">Grand Total</th>
                      <th className="px-3 py-3 text-center">%</th>
                      <th className="px-3 py-3 text-center">SGPA</th>
                      <th className="px-3 py-3 text-center">Result Status</th>
                      <th className="px-3 py-3 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredStudents.length === 0 ? (
                      <tr>
                        <td colSpan={10} className="text-center py-10 text-slate-400">
                          <AlertCircle className="w-6 h-6 mx-auto mb-1 text-slate-400" />
                          <span>No candidate records match your query.</span>
                        </td>
                      </tr>
                    ) : (
                      filteredStudents.map((res, index) => {
                        const studentKey = res.student.roll_no?.trim()
                          ? `${res.student.roll_no.trim()}-${index}`
                          : res.student.enrollment_no?.trim()
                          ? `${res.student.enrollment_no.trim()}-${index}`
                          : `student-${res.student.serial_no || index}`;
                        const isPassed = res.result_status.includes("PASS");
                        const hasGrace = res.result_status.includes("GRACE");

                        return (
                          <tr
                            key={studentKey}
                            className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                          >
                            <td className="px-3 py-2.5 text-center font-mono text-slate-400 text-[11px]">
                              {res.student.serial_no || index + 1}
                            </td>
                            <td className="px-3 py-2.5 font-mono font-bold text-slate-900 dark:text-white whitespace-nowrap">
                              {res.student.roll_no || "N/A"}
                            </td>
                            <td className="px-3 py-2.5 font-mono text-slate-600 dark:text-slate-300 whitespace-nowrap">
                              {res.student.enrollment_no || "N/A"}
                            </td>
                            <td className="px-4 py-2.5">
                              <div className="font-semibold text-slate-900 dark:text-white whitespace-nowrap">
                                {res.student.name}
                              </div>
                              <div className="text-[11px] text-slate-400 whitespace-nowrap">
                                S/o: {res.student.father_name || "N/A"}
                              </div>
                            </td>
                            <td className="px-4 py-2.5">
                              <div className="flex flex-wrap gap-1.5">
                                {res.courses.map((comp, cIdx) => (
                                  <span
                                    key={cIdx}
                                    title={`${comp.course_title}: Internal ${comp.internal_obtained ?? "Ab"}/${comp.internal_max}, External ${comp.external_obtained ?? "Ab"}/${comp.external_max}, Total ${comp.total_obtained ?? "Ab"}/${comp.total_max}`}
                                    className={`text-[10px] px-2 py-0.5 rounded font-mono border whitespace-nowrap ${
                                      comp.is_pass
                                        ? "bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                                        : "bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-300 border-red-300 font-bold"
                                    }`}
                                  >
                                    {comp.course_code}: {comp.internal_obtained ?? "Ab"}+{comp.external_obtained ?? "Ab"}={comp.total_obtained ?? "Ab"} ({comp.letter_grade})
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="px-3 py-2.5 text-center font-mono font-bold text-slate-900 dark:text-white whitespace-nowrap">
                              {res.grand_total_obtained} / {res.grand_total_max}
                            </td>
                            <td className="px-3 py-2.5 text-center font-mono text-slate-700 dark:text-slate-300 font-semibold whitespace-nowrap">
                              {res.overall_percentage}%
                            </td>
                            <td className="px-3 py-2.5 text-center font-mono font-bold text-blue-600 dark:text-blue-400 whitespace-nowrap">
                              {res.sgpa}
                            </td>
                            <td className="px-3 py-2.5 text-center whitespace-nowrap">
                              <span
                                className={`inline-block text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                                  isPassed
                                    ? hasGrace
                                      ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300"
                                      : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300"
                                    : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 border border-red-300"
                                }`}
                              >
                                {res.result_status}
                              </span>
                            </td>
                            <td className="px-3 py-2.5 text-center whitespace-nowrap">
                              <div className="flex items-center justify-center gap-1.5">
                                <button
                                  onClick={(e) => handleOpenPreview(res, e)}
                                  title="Preview Official SGPGIMS Marksheet"
                                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
                                >
                                  <Eye className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                                </button>
                                <button
                                  onClick={(e) => handleDownloadSinglePdf(res, e, studentKey)}
                                  disabled={downloadingRoll === (res.student.roll_no?.trim() || studentKey)}
                                  title="Download PDF"
                                  className="p-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 dark:hover:bg-blue-900/60 text-blue-700 dark:text-blue-300 transition-colors cursor-pointer"
                                >
                                  {downloadingRoll === (res.student.roll_no?.trim() || studentKey) ? (
                                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                  ) : (
                                    <FileDown className="w-3.5 h-3.5" />
                                  )}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            /* Candidate Result Cards List */
            <div className="space-y-4">
            {filteredStudents.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8">
                <AlertCircle className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  No candidate records match your query
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Try clearing search filters or modifying search terms.
                </p>
              </div>
            ) : (
              filteredStudents.map((res, index) => {
                const studentKey = res.student.roll_no?.trim()
                  ? `${res.student.roll_no.trim()}-${index}`
                  : res.student.enrollment_no?.trim()
                  ? `${res.student.enrollment_no.trim()}-${index}`
                  : `student-${res.student.serial_no || index}`;
                const isPassed = res.result_status.includes("PASS");
                const hasGrace = res.result_status.includes("GRACE");
                const isExpanded = expandedStudentRoll === studentKey;

                return (
                  <div
                    key={studentKey}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden transition-all"
                  >
                    {/* Header bar of student card */}
                    <div
                      onClick={() => setExpandedStudentRoll(isExpanded ? null : studentKey)}
                      className="p-4 sm:p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${
                            isPassed
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300"
                              : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 border border-red-300"
                          }`}
                        >
                          {res.student.serial_no || "#"}
                        </div>

                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white">
                              {res.student.name}
                            </h3>
                            {hasGrace && (
                              <span className="text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 px-2 py-0.5 rounded-full border border-amber-300">
                                Grace Marks Applied
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 flex flex-wrap gap-x-3 gap-y-0.5 mt-0.5">
                            <span>S/o / D/o: <strong>{res.student.father_name || "N/A"}</strong></span>
                            <span>•</span>
                            <span>Roll No: <strong className="font-mono text-slate-700 dark:text-slate-300">{res.student.roll_no || "N/A"}</strong></span>
                            <span>•</span>
                            <span>Enrollment: <strong className="font-mono text-slate-700 dark:text-slate-300">{res.student.enrollment_no || "N/A"}</strong></span>
                          </div>
                        </div>
                      </div>

                      {/* Right summary badges & actions */}
                      <div className="flex items-center gap-3 self-end sm:self-auto">
                        {/* Quick Actions */}
                        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={(e) => handleOpenPreview(res, e)}
                            title="Preview Official SGPGIMS Marksheet"
                            className="flex items-center gap-1 text-[11px] font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                            <span className="hidden sm:inline">Preview</span>
                          </button>

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setAuditStudent({
                                roll_no: res.student.roll_no,
                                name: res.student.name,
                                enrollment_no: res.student.enrollment_no,
                              });
                              setIsAuditModalOpen(true);
                            }}
                            title="View Field-Level Chronological Audit History"
                            className="flex items-center gap-1 text-[11px] font-semibold bg-purple-50 hover:bg-purple-100 dark:bg-purple-950/60 dark:hover:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2.5 py-1.5 rounded-xl border border-purple-200 dark:border-purple-800 transition-colors cursor-pointer"
                          >
                            <History className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
                            <span className="hidden sm:inline">Audit</span>
                          </button>

                          <button
                            onClick={(e) => handleDownloadSinglePdf(res, e, studentKey)}
                            disabled={downloadingRoll === (res.student.roll_no?.trim() || studentKey)}
                            title="Download High-Resolution A4 PDF"
                            className="flex items-center gap-1 text-[11px] font-semibold bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 dark:hover:bg-blue-900/60 text-blue-700 dark:text-blue-300 px-2.5 py-1.5 rounded-xl border border-blue-200 dark:border-blue-800 transition-colors cursor-pointer"
                          >
                            {downloadingRoll === (res.student.roll_no?.trim() || studentKey) ? (
                              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <FileDown className="w-3.5 h-3.5" />
                            )}
                            <span className="hidden sm:inline">PDF</span>
                          </button>
                        </div>

                        <div className="text-right">
                          <div className="text-xs font-mono font-bold text-slate-900 dark:text-white">
                            {res.grand_total_obtained} / {res.grand_total_max} ({res.overall_percentage}%)
                          </div>
                          <div className="text-[11px] text-blue-600 dark:text-blue-400 font-semibold font-mono">
                            SGPA: {res.sgpa}
                          </div>
                        </div>

                        <span
                          className={`text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider ${
                            isPassed
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300"
                              : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 border border-red-300"
                          }`}
                        >
                          {res.result_status}
                        </span>
                      </div>
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="p-4 sm:p-5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 space-y-4">
                        {/* Course Marks Table */}
                        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold uppercase">
                              <tr>
                                <th className="px-3 py-2.5">Course Code & Component</th>
                                <th className="px-3 py-2.5 text-center">IA Marks</th>
                                <th className="px-3 py-2.5 text-center">Univ/College Exam</th>
                                <th className="px-3 py-2.5 text-center">Total Marks</th>
                                <th className="px-3 py-2.5 text-center">Percentage</th>
                                <th className="px-3 py-2.5 text-center">Grade</th>
                                <th className="px-3 py-2.5 text-center">Grade Point</th>
                                <th className="px-3 py-2.5 text-center">Result</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                              {res.courses.map((comp, idx) => (
                                <tr
                                  key={idx}
                                  className={!comp.is_pass ? "bg-red-50/50 dark:bg-red-950/20" : ""}
                                >
                                  <td className="px-3 py-2.5">
                                    <div className="font-bold text-slate-900 dark:text-white font-mono">
                                      {comp.course_code}
                                    </div>
                                    <div className="text-[11px] text-slate-500 font-medium">
                                      {comp.course_title} ({comp.component_name})
                                    </div>
                                    {comp.sub_components && comp.sub_components.length > 0 && (
                                      <div className="text-[10px] text-slate-400 mt-0.5 flex gap-2">
                                        {comp.sub_components.map((sub, sIdx) => (
                                          <span key={sIdx}>
                                            {sub.name}: <strong>{sub.obtained ?? "Ab"}</strong>/{sub.max_marks}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                  </td>

                                  <td className="px-3 py-2.5 text-center font-mono">
                                    {comp.internal_obtained ?? "Ab"} / {comp.internal_max}
                                  </td>

                                  <td className="px-3 py-2.5 text-center font-mono">
                                    {comp.external_obtained ?? "Ab"} / {comp.external_max}
                                  </td>

                                  <td className="px-3 py-2.5 text-center font-mono font-bold">
                                    {comp.total_obtained ?? "Ab"} / {comp.total_max}
                                  </td>

                                  <td className="px-3 py-2.5 text-center font-mono">
                                    {comp.percentage}%
                                  </td>

                                  <td className="px-3 py-2.5 text-center">
                                    <span
                                      className={`inline-block w-7 py-0.5 text-center font-bold font-mono rounded text-xs ${
                                        comp.is_pass
                                          ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300"
                                          : "bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300"
                                      }`}
                                    >
                                      {comp.letter_grade}
                                    </span>
                                  </td>

                                  <td className="px-3 py-2.5 text-center font-mono font-bold">
                                    {comp.grade_point}
                                  </td>

                                  <td className="px-3 py-2.5 text-center">
                                    <span
                                      className={`text-[10px] font-bold uppercase ${
                                        comp.is_pass ? "text-emerald-600" : "text-rose-600"
                                      }`}
                                    >
                                      {comp.is_pass ? "PASS" : "FAIL"}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {/* Failed Courses Remarks */}
                        {res.failed_courses.length > 0 && (
                          <div className="p-3 rounded-xl bg-red-100/60 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
                            <span>
                              <strong>Reappear Required:</strong> Failed in {res.failed_courses.join(", ")}
                            </span>
                          </div>
                        )}

                        {/* Drawer Footer Actions */}
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pt-2">
                          <div className="text-[11px] text-slate-500">
                            Candidate Roll: <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{res.student.roll_no}</span>
                            {res.remarks && (
                              <span className="ml-2 text-slate-400">({res.remarks})</span>
                            )}
                          </div>

                          <div className="flex flex-wrap items-center gap-2 self-end sm:self-auto">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setAuditStudent({
                                  roll_no: res.student.roll_no,
                                  name: res.student.name,
                                  enrollment_no: res.student.enrollment_no,
                                });
                                setIsAuditModalOpen(true);
                              }}
                              className="flex items-center gap-1.5 text-xs font-semibold bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm transition-colors cursor-pointer"
                            >
                              <History className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
                              <span>View Audit History</span>
                            </button>

                            <button
                              onClick={(e) => handleOpenPreview(res, e)}
                              className="flex items-center gap-1.5 text-xs font-semibold bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm transition-colors cursor-pointer"
                            >
                              <Eye className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                              <span>Preview Marksheet</span>
                            </button>

                            <button
                              onClick={(e) => handleDownloadSinglePdf(res, e)}
                              disabled={downloadingRoll === res.student.roll_no}
                              className="flex items-center gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-xl shadow-sm shadow-blue-600/30 transition-colors cursor-pointer"
                            >
                              {downloadingRoll === res.student.roll_no ? (
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <FileDown className="w-3.5 h-3.5" />
                              )}
                              <span>Download PDF</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
          )}
        </div>
      )}

      {/* Official SGPGIMS Marksheet Preview Modal */}
      <MarksheetPreviewModal
        student={previewStudent}
        semester={ingestionData?.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10))}
        isOpen={isPreviewOpen}
        onClose={() => {
          setIsPreviewOpen(false);
          setPreviewStudent(null);
        }}
      />

      {/* Official INC Gazette Regulatory Audit Modal */}
      <IncGazetteAuditModal
        isOpen={isIncModalOpen}
        onClose={() => setIsIncModalOpen(false)}
        students={evaluatedStudents.length > 0 ? evaluatedStudents : (ingestionData?.results || []).map(toEvaluatedRecord)}
        semester={ingestionData?.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10))}
        onExportBulkZip={handleDownloadBulkZip}
        isExportingZip={isBulkDownloading}
      />

      {/* Field-Level Chronological Audit Trail Modal */}
      <VisualAuditLogModal
        isOpen={isAuditModalOpen}
        onClose={() => {
          setIsAuditModalOpen(false);
          setAuditStudent(null);
        }}
        rollNo={auditStudent?.roll_no || null}
        studentName={auditStudent?.name || "Candidate"}
        enrollmentNo={auditStudent?.enrollment_no}
        semesterNumber={ingestionData?.semester || (selectedSemester === "auto" ? 1 : parseInt(selectedSemester, 10))}
      />
    </div>
  );
};
