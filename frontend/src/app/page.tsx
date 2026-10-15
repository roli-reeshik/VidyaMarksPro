"use client";

import React, { useState } from "react";
import { Navbar, NavTab } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { ExcelUploadZone } from "../components/ExcelUploadZone";
import { MarksheetTemplateEditor } from "../components/MarksheetTemplateEditor";
import { MarksheetDebugCategoriesView } from "../components/MarksheetDebugCategoriesView";
import { SemesterSchemasExplorer } from "../components/SemesterSchemasExplorer";
import { GradingScaleSection } from "../components/GradingScaleSection";
import { QualityAuditGateView } from "../components/QualityAuditGateView";
import { TabulationRegisterView } from "../components/TabulationRegisterView";
import { EvaluatedStudentRecord } from "../types/marksheet";

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavTab>("upload");
  const [evaluatedStudents, setEvaluatedStudents] = useState<EvaluatedStudentRecord[]>([]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "upload" && (
          <ExcelUploadZone
            onStudentsLoaded={(students) => setEvaluatedStudents(students)}
            onNavigateToTemplate={() => setActiveTab("template")}
            onNavigateToDebug={() => setActiveTab("debug")}
            onNavigateToAudit={() => setActiveTab("audit")}
          />
        )}
        {activeTab === "template" && (
          <MarksheetTemplateEditor
            currentStudents={evaluatedStudents}
            onNavigateToDebug={() => setActiveTab("debug")}
          />
        )}
        {activeTab === "debug" && (
          <MarksheetDebugCategoriesView
            currentStudents={evaluatedStudents}
            onNavigateToTemplate={() => setActiveTab("template")}
            onNavigateToCheck={() => setActiveTab("audit")}
          />
        )}
        {activeTab === "audit" && <QualityAuditGateView />}
        {activeTab === "register" && (
          <TabulationRegisterView
            currentStudents={evaluatedStudents}
            onNavigateToUpload={() => setActiveTab("upload")}
          />
        )}
        {activeTab === "schemas" && <SemesterSchemasExplorer />}
        {activeTab === "grading" && <GradingScaleSection />}
      </main>

      <Footer />
    </div>
  );
}
