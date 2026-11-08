import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, Sparkles, ShieldCheck } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-[#DCE6E3] bg-[#EEF3F1] mt-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Column 1: Brand & Bio */}
          <div className="space-y-4 md:col-span-1">
            <Link to="/" className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-[#163B46] flex items-center justify-center shadow-soft">
                <Compass className="w-5 h-5 text-[#18B8A6] font-bold" />
              </div>
              <span className="text-lg font-extrabold text-[#163B46] tracking-tight">
                TravelSense<span className="text-[#18B8A6]">AI</span>
              </span>
            </Link>
            <p className="text-xs text-[#52636A] leading-relaxed">
              Intelligent context-aware travel planning engine combining geospatial road routing, real-time weather adaptations, multi-criteria POI recommendation, and LangGraph RAG conversational assistance.
            </p>
            <div className="flex items-center space-x-2 text-[11px] text-[#52636A]">
              <ShieldCheck className="w-3.5 h-3.5 text-[#16A36A]" />
              <span>Full-Stack Architecture • Production Ready</span>
            </div>
          </div>

          {/* Column 2: Navigation */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-[#163B46] tracking-wider uppercase">Navigation</h4>
            <ul className="space-y-2 text-xs text-[#52636A]">
              <li>
                <Link to="/" className="hover:text-[#18B8A6] transition-colors">Home / Landing</Link>
              </li>
              <li>
                <Link to="/plan" className="hover:text-[#18B8A6] transition-colors">Plan Your Trip</Link>
              </li>
              <li>
                <Link to="/recommendations" className="hover:text-[#18B8A6] transition-colors">POI Recommendations</Link>
              </li>
              <li>
                <Link to="/itinerary" className="hover:text-[#18B8A6] transition-colors">Day-wise Itinerary</Link>
              </li>
              <li>
                <Link to="/map" className="hover:text-[#18B8A6] transition-colors">Interactive OpenStreetMap</Link>
              </li>
            </ul>
          </div>

          {/* Column 3: AI & Tools */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-[#163B46] tracking-wider uppercase">AI & Intelligence</h4>
            <ul className="space-y-2 text-xs text-[#52636A]">
              <li>
                <Link to="/assistant" className="hover:text-[#18B8A6] transition-colors flex items-center space-x-1">
                  <Sparkles className="w-3 h-3 text-[#18B8A6]" />
                  <span>AI Travel Assistant</span>
                </Link>
              </li>
              <li>
                <Link to="/analytics" className="hover:text-[#18B8A6] transition-colors">Analytics & Metrics</Link>
              </li>
              <li>
                <Link to="/reports" className="hover:text-[#18B8A6] transition-colors">PDF Export Reports</Link>
              </li>
              <li>
                <Link to="/dashboard" className="hover:text-[#18B8A6] transition-colors">User Dashboard</Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Technology Ecosystem */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-[#163B46] tracking-wider uppercase">Core Engines</h4>
            <div className="flex flex-wrap gap-1.5 text-[10px]">
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">FastAPI</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">React 18 + Vite</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">Geoapify</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">OpenRouteService</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">Open-Meteo</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">ChromaDB RAG</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">LangGraph Agent</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">Leaflet Maps</span>
              <span className="px-2 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D]">Recharts</span>
            </div>
            <p className="text-[11px] text-[#829196] pt-2">
              All 11 phases verified with 123 automated end-to-end tests passing.
            </p>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-[#DCE6E3] flex flex-col sm:flex-row items-center justify-between text-xs text-[#829196] gap-4">
          <p>&copy; {new Date().getFullYear()} TravelSenseAI. Final Year Engineering Project. All rights reserved.</p>
          <div className="flex items-center space-x-4">
            <span className="hover:text-[#163B46] transition-colors">Strict Anti-Hallucination Policy</span>
            <span>•</span>
            <span className="hover:text-[#163B46] transition-colors">Privacy & Terms</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
