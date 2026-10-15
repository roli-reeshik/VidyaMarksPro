"use client";

import React from "react";
import { Phone, Heart, Shield, Building2 } from "lucide-react";
import { INSTITUTIONAL_INFO } from "../data/semesterData";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-800 text-slate-400 mt-auto py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Institutional & Developer metadata row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pb-6 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 text-white font-semibold text-base mb-2">
              <Building2 className="w-4 h-4 text-blue-400" />
              <span>{INSTITUTIONAL_INFO.institution_name}</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              {INSTITUTIONAL_INFO.location}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Affiliated Examination College Code: <span className="font-mono text-slate-300">{INSTITUTIONAL_INFO.college_code}</span>
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 text-white font-semibold text-base mb-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Statutory Compliance</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Fully compliant with the Indian Nursing Council (INC) Gazette Regulations, INC 10-Point Grading Framework, and SGPGIMS Lucknow Examination Guidelines.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 text-white font-semibold text-base mb-2">
              <Heart className="w-4 h-4 text-rose-400" />
              <span>Platform Developer & Support</span>
            </div>
            <p className="text-xs text-slate-400">
              Technical Lead: <span className="text-slate-200 font-medium">{INSTITUTIONAL_INFO.branding.contact_person}</span>
            </p>
            <a
              href={`tel:${INSTITUTIONAL_INFO.branding.contact_mobile.replace(/[^0-9+]/g, "")}`}
              className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors mt-1 font-mono"
            >
              <Phone className="w-3.5 h-3.5" />
              <span>{INSTITUTIONAL_INFO.branding.contact_mobile}</span>
            </a>
          </div>
        </div>

        {/* Primary Required Attribution Line */}
        <div className="pt-6 text-center">
          <div className="inline-flex flex-wrap items-center justify-center gap-2 px-4 py-2 rounded-full bg-slate-900 border border-slate-800 text-xs sm:text-sm text-slate-300 shadow-inner">
            <span className="font-semibold text-blue-400">Developed at VidyaLabs</span>
            <span className="text-slate-600">|</span>
            <span>Copyright © 2026 VidyaLabs. All Rights Reserved.</span>
            <span className="text-slate-600">|</span>
            <span className="flex items-center gap-1 text-slate-300">
              Contact: <strong className="text-white">Priyanka Kumari</strong>
              <a
                href="tel:+919140189586"
                className="text-blue-400 hover:underline hover:text-blue-300 font-mono ml-0.5"
              >
                (+91-9140189586)
              </a>
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-3">
            VidyaMarksheet™ • Enterprise B.Sc. Nursing Examination Marksheet Processing Platform
          </p>
        </div>
      </div>
    </footer>
  );
};
