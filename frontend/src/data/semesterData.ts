import { SemesterDefinition, IncGradingScaleItem, InstitutionalMetadata } from "../types/marksheet";

export const INSTITUTIONAL_INFO: InstitutionalMetadata = {
  application_name: "VidyaMarksheet",
  application_subtitle: "B.Sc. Nursing Marksheet Generation & Evaluation System",
  institution_name: "College of Nursing, Sanjay Gandhi Postgraduate Institute of Medical Sciences (SGPGIMS)",
  location: "Raebareli Road, Lucknow - 226014, Uttar Pradesh, India",
  college_code: "1313",
  regulatory_framework: "Indian Nursing Council (INC) Gazette Notification & SGPGIMS Examination Byelaws",
  branding: {
    developed_by: "VidyaLabs",
    copyright: "Copyright © 2026 VidyaLabs. All Rights Reserved.",
    contact_person: "Priyanka Kumari",
    contact_mobile: "+91-9140189586"
  }
};

export const INC_GRADING_SCALE: IncGradingScaleItem[] = [
  {
    percentage_range: "85.00% & Above",
    letter_grade: "O",
    grade_point: 10,
    qualitative_description: "Outstanding",
    notes: "Distinction grade for exceptional theoretical & clinical mastery"
  },
  {
    percentage_range: "80.00% to 84.99%",
    letter_grade: "A+",
    grade_point: 9,
    qualitative_description: "Excellent",
    notes: "First Class with Distinction"
  },
  {
    percentage_range: "75.00% to 79.99%",
    letter_grade: "A",
    grade_point: 8,
    qualitative_description: "Very Good",
    notes: "First Class honors"
  },
  {
    percentage_range: "65.00% to 74.99%",
    letter_grade: "B+",
    grade_point: 7,
    qualitative_description: "Good",
    notes: "Higher Second Class performance"
  },
  {
    percentage_range: "60.00% to 64.99%",
    letter_grade: "B",
    grade_point: 6,
    qualitative_description: "Above Average",
    notes: "Second Class standard"
  },
  {
    percentage_range: "50.00% to 59.99%",
    letter_grade: "C",
    grade_point: 5,
    qualitative_description: "Average / Pass",
    notes: "Minimum qualifying threshold for all standard nursing courses"
  },
  {
    percentage_range: "40.00% to 49.99%",
    letter_grade: "P",
    grade_point: 4,
    qualitative_description: "Pass (Electives / English)",
    notes: "Restricted STRICTLY to Communicative English (Sem 1) and Elective Modules (Sem 4, 6, 8)"
  },
  {
    percentage_range: "Below 50.00% (<40% for English/Electives)",
    letter_grade: "F",
    grade_point: 0,
    qualitative_description: "Fail",
    notes: "Candidate has failed to meet the passing threshold and must reappear"
  },
  {
    percentage_range: "Absent in Exam",
    letter_grade: "Ab",
    grade_point: 0,
    qualitative_description: "Absent",
    notes: "Candidate was absent; calculated as zero grade point"
  }
];

export const ALL_SEMESTERS_DATA: Record<number, SemesterDefinition> = {
  1: {
    semester_number: 1,
    year: 1,
    semester_name: "FIRST SEMESTER",
    year_name: "FIRST YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
    college_code: "1313",
    total_prescribed_credits: 14,
    sgpa_eligible_credits: 12,
    grand_total_marks: 250,
    courses: [
      {
        sl_no: 1,
        course_code: "ENGL 101",
        title: "Communicative English",
        credits: 2,
        credit_breakdown: "2",
        course_type: "COLLEGE_EXAM",
        component_type: "THEORY",
        passing_threshold_percent: 40.0,
        is_english_or_elective: true,
        include_in_sgpa: false,
        footnotes: "* College Exam, Marks are not added for calculating SGPA, Pass marks-40% as per INC, New Delhi",
        components: [
          {
            name: "College Exam",
            credits: 2,
            ia_max: 25,
            ia_min_pass: 10,
            ea_max: 25,
            ea_min_pass: 10,
            total_max: 50,
            min_pass_percentage: 40.0
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "ANAT 105 & PHYS 110",
        title: "Applied Anatomy & Applied Physiology",
        credits: 6,
        credit_breakdown: "(3+3)",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 6,
            ia_max: 25,
            ia_min_pass: 12.5,
            ea_max: 75,
            ea_min_pass: 37.5,
            total_max: 100,
            min_pass_percentage: 50.0,
            sub_components: [
              { name: "Applied Anatomy", code: "ANAT 105", max_marks: 37 },
              { name: "Applied Physiology", code: "PHYS 110", max_marks: 38 }
            ]
          }
        ]
      },
      {
        sl_no: 3,
        course_code: "SOCI 115 & PSYC 120",
        title: "Applied Sociology & Applied Psychology",
        credits: 6,
        credit_breakdown: "(3+3)",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 6,
            ia_max: 25,
            ia_min_pass: 12.5,
            ea_max: 75,
            ea_min_pass: 37.5,
            total_max: 100,
            min_pass_percentage: 50.0,
            sub_components: [
              { name: "Applied Sociology", code: "SOCI 115", max_marks: 37 },
              { name: "Applied Psychology", code: "PSYC 120", max_marks: 38 }
            ]
          }
        ]
      }
    ]
  },

  2: {
    semester_number: 2,
    year: 1,
    semester_name: "SECOND SEMESTER",
    year_name: "FIRST YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
    college_code: "1313",
    total_prescribed_credits: 31,
    sgpa_eligible_credits: 31,
    grand_total_marks: 350,
    courses: [
      {
        sl_no: 1,
        course_code: "BIOC 135 & NUTR 140",
        title: "Applied Biochemistry & Applied Nutrition & Dietetics",
        credits: 5,
        credit_breakdown: "(2+3)",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 5,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0,
            sub_components: [
              { name: "Applied Biochemistry", code: "BIOC 135", max_marks: 37 },
              { name: "Applied Nutrition & Dietetics", code: "NUTR 140", max_marks: 38 }
            ]
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "N-NF (I & II) 125",
        title: "Nursing Foundation I & II Incl. Health Assessment Module",
        credits: 23,
        credit_breakdown: "T-12 (6+6), P-11 (4+7)",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory (T-12)",
            credits: 12,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical (P-11)",
            credits: 11,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 3,
        course_code: "HNIT 145",
        title: "Health/Nursing Informatics & Technology",
        credits: 3,
        credit_breakdown: "3",
        course_type: "COLLEGE_EXAM",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        footnotes: "*HNIT 145 College Exam T-Theory. P-Practical. Presc. : Prescribed Obtd. : Obtained",
        components: [
          {
            name: "College Exam",
            credits: 3,
            ia_max: 25,
            ea_max: 25,
            total_max: 50,
            min_pass_percentage: 50.0
          }
        ]
      }
    ]
  },

  3: {
    semester_number: 3,
    year: 2,
    semester_name: "THIRD SEMESTER",
    year_name: "SECOND YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
    college_code: "1313",
    total_prescribed_credits: 17,
    sgpa_eligible_credits: 17,
    grand_total_marks: 300,
    courses: [
      {
        sl_no: 1,
        course_code: "MICR 201",
        title: "Applied Microbiology and Infection Control including Safety",
        credits: 3,
        credit_breakdown: "3",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 3,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "N-AHN (I) 215",
        title: "Adult Health Nursing I with Integrated Pathophysiology including BCLS module",
        credits: 14,
        credit_breakdown: "T-7, P-7",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 7,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical",
            credits: 7,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      }
    ]
  },

  4: {
    semester_number: 4,
    year: 2,
    semester_name: "FOURTH SEMESTER",
    year_name: "SECOND YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
    college_code: "1313",
    total_prescribed_credits: 21,
    sgpa_eligible_credits: 20,
    grand_total_marks: 350,
    courses: [
      {
        sl_no: 1,
        course_code: "PHAR (I & II)-205 & PATH (I & II)-210",
        title: "Pharmacology (I & II) & Pathology (I & II) (including Genetics)",
        credits: 6,
        credit_breakdown: "(4+2)",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 6,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0,
            sub_components: [
              { name: "Pharmacology (I & II)", code: "PHAR 205", max_marks: 38 },
              { name: "Pathology (I & II) & Genetics", code: "PATH 210", max_marks: 37 }
            ]
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "N-AHN (II) 225",
        title: "Adult Health Nursing II with Integrated Pathophysiology",
        credits: 14,
        credit_breakdown: "T-7, P-7",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 7,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical",
            credits: 7,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 3,
        course_code: "PROF 230",
        title: "Professionalism, Professional Values & Ethics including Bioethics",
        credits: 1,
        credit_breakdown: "1",
        course_type: "COLLEGE_EXAM",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        footnotes: "* Prof 230-College Exam",
        components: [
          {
            name: "College Exam",
            credits: 1,
            ia_max: 25,
            ea_max: 25,
            total_max: 50,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 4,
        course_code: "Elective-1",
        title: "Elective Module (Soft Skills / Human Values)",
        credits: 1,
        credit_breakdown: "1",
        course_type: "ELECTIVE",
        component_type: "THEORY",
        passing_threshold_percent: 40.0,
        is_english_or_elective: true,
        include_in_sgpa: false,
        footnotes: "**Elective 1-College Exam, Marks are not Added for Calculating SGPA, Pass Mark-40%",
        components: [
          {
            name: "Elective Assessment",
            credits: 1,
            ia_max: 0,
            ea_max: 100,
            total_max: 100,
            min_pass_percentage: 40.0
          }
        ]
      }
    ]
  },

  5: {
    semester_number: 5,
    year: 3,
    semester_name: "FIFTH SEMESTER",
    year_name: "THIRD YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
    college_code: "1313",
    total_prescribed_credits: 11,
    sgpa_eligible_credits: 11,
    grand_total_marks: 350,
    courses: [
      {
        sl_no: 1,
        course_code: "N-COMH (I) 310",
        title: "Community Health Nursing I including Environmental Science & Epidemiology",
        credits: 7,
        credit_breakdown: "T-5, P-2",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 5,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical",
            credits: 2,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "EDUC 315",
        title: "Educational Technology / Nursing Education",
        credits: 3,
        credit_breakdown: "3",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 3,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 3,
        course_code: "N-FORN 320",
        title: "Introduction to Forensic Nursing",
        credits: 1,
        credit_breakdown: "1",
        course_type: "COLLEGE_EXAM",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        footnotes: "*N-FORN 320 - College Exam",
        components: [
          {
            name: "College Exam",
            credits: 1,
            ia_max: 25,
            ea_max: 25,
            total_max: 50,
            min_pass_percentage: 50.0
          }
        ]
      }
    ]
  },

  6: {
    semester_number: 6,
    year: 3,
    semester_name: "SIXTH SEMESTER",
    year_name: "THIRD YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
    college_code: "1313",
    total_prescribed_credits: 22,
    sgpa_eligible_credits: 21,
    grand_total_marks: 500,
    courses: [
      {
        sl_no: 1,
        course_code: "N-CHN (I & II) 301",
        title: "Child Health Nursing (I & II)",
        credits: 9,
        credit_breakdown: "T-5 (3+2), P-4 (3+1)",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 5,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical",
            credits: 4,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "N-MHN (I & II) 305",
        title: "Mental Health Nursing (I & II)",
        credits: 8,
        credit_breakdown: "T-5 (3+2), P-3 (1+2)",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 5,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical",
            credits: 3,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 3,
        course_code: "NMLE 330",
        title: "Nursing Management & Leadership",
        credits: 4,
        credit_breakdown: "4 (T-3, P-1)",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 4,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 4,
        course_code: "Elective-2",
        title: "Accreditation and Practice Standards (Elective)",
        credits: 1,
        credit_breakdown: "1",
        course_type: "ELECTIVE",
        component_type: "THEORY",
        passing_threshold_percent: 40.0,
        is_english_or_elective: true,
        include_in_sgpa: false,
        footnotes: "*Elective-2-College Exam, Marks are not added for calculating SGPA, Pass mark-40%",
        components: [
          {
            name: "Elective Assessment",
            credits: 1,
            ia_max: 0,
            ea_max: 100,
            total_max: 100,
            min_pass_percentage: 40.0
          }
        ]
      }
    ]
  },

  7: {
    semester_number: 7,
    year: 4,
    semester_name: "SEVENTH SEMESTER",
    year_name: "FOURTH YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
    college_code: "1313",
    total_prescribed_credits: 26,
    sgpa_eligible_credits: 26,
    grand_total_marks: 500,
    courses: [
      {
        sl_no: 1,
        course_code: "N-COMH (II) 401",
        title: "Community Health Nursing II",
        credits: 7,
        credit_breakdown: "T-5, P-2",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 5,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical",
            credits: 2,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "NRST 405",
        title: "Nursing Research & Statistics",
        credits: 4,
        credit_breakdown: "4 (T-2, P-2)",
        course_type: "CORE",
        component_type: "THEORY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 4,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 3,
        course_code: "N-MIDW/OBGN (I & II) 335 & 410",
        title: "Midwifery/Obstetrics and Gynaecology (OBG) Nursing I & II",
        credits: 15,
        credit_breakdown: "T-6 (3+3), P-9 (4+5)",
        course_type: "CORE",
        component_type: "THEORY_AND_PRACTICAL",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Theory",
            credits: 6,
            ia_max: 25,
            ea_max: 75,
            total_max: 100,
            min_pass_percentage: 50.0
          },
          {
            name: "Practical",
            credits: 9,
            ia_max: 50,
            ea_max: 50,
            total_max: 100,
            min_pass_percentage: 50.0
          }
        ]
      }
    ]
  },

  8: {
    semester_number: 8,
    year: 4,
    semester_name: "EIGHTH SEMESTER",
    year_name: "FOURTH YEAR",
    degree_title: "B.Sc. NURSING",
    college_name: "COLLEGE OF NURSING, SGPGIMS, LUCKNOW (CODE - 1313)",
    college_code: "1313",
    total_prescribed_credits: 13,
    sgpa_eligible_credits: 12,
    grand_total_marks: 300,
    courses: [
      {
        sl_no: 1,
        course_code: "INTE 415, 420, 425, 430 & 435",
        title: "Competency Assessment (Internship / Intensive Clinical Practicum: 1. Community Health Nursing, 2. Adult Health Nursing, 3. Child Health Nursing, 4. Mental Health Nursing, 5. Midwifery/OBG Nursing)",
        credits: 12,
        credit_breakdown: "P-12",
        course_type: "CLINICAL_COMPETENCY",
        component_type: "COMPETENCY",
        passing_threshold_percent: 50.0,
        is_english_or_elective: false,
        include_in_sgpa: true,
        components: [
          {
            name: "Competency Assessment (C1)",
            credits: 12,
            ia_max: 100,
            ia_min_pass: 50,
            ea_max: 100,
            ea_min_pass: 50,
            total_max: 200,
            min_pass_percentage: 50.0
          }
        ]
      },
      {
        sl_no: 2,
        course_code: "Elective-3",
        title: "Scientific Writing Skills (Elective)",
        credits: 1,
        credit_breakdown: "1",
        course_type: "ELECTIVE",
        component_type: "THEORY",
        passing_threshold_percent: 40.0,
        is_english_or_elective: true,
        include_in_sgpa: false,
        footnotes: "*Elective 3-Marks are not added for calculating SGPA, Pass Mark-40%",
        components: [
          {
            name: "Elective Assessment",
            credits: 1,
            ia_max: 0,
            ea_max: 100,
            total_max: 100,
            min_pass_percentage: 40.0
          }
        ]
      }
    ]
  }
};
