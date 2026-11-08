import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Download,
  Calendar,
  MapPin,
  DollarSign,
  Route,
  CheckCircle2,
  Clock,
  Printer,
  Compass,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  BarChart3,
  Loader2,
  AlertCircle,
  FileCheck,
} from 'lucide-react';
import { useTrip } from '../context/TripContext';
import reportService from '../services/reportService';
import pdfExportService from '../services/pdfExportService';
import {
  formatCurrency,
  formatDistanceKm,
  formatDurationMins,
  formatDateDisplay,
  getCategoryBadgeColor,
} from '../utils/formatters';

export default function ReportsPage() {
  const navigate = useNavigate();
  const { currentItinerary, tripPlan } = useTrip();

  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [generatedReport, setGeneratedReport] = useState(null);
  const [reportError, setReportError] = useState(null);
  const [activeTab, setActiveTab] = useState('dossier'); // 'dossier' | 'analytics'

  if (!currentItinerary) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft flex items-center justify-center mx-auto text-[#18B8A6]">
          <Compass className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-[#163B46]">No Generated Itinerary Report Available</h2>
        <p className="text-sm text-[#52636A] max-w-md mx-auto">
          Please configure and generate a travel itinerary first before exporting a PDF travel dossier.
        </p>
        <button
          onClick={() => navigate('/plan')}
          className="px-6 py-3 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs shadow-soft transition-colors"
        >
          Go to Trip Planner
        </button>
      </div>
    );
  }

  const itin = currentItinerary;
  const budget = itin.budget_summary || {};
  const cb = budget.by_category || budget.category_breakdown || {};

  // Generate ReportLab PDF via backend
  const handleGenerateReportLabPdf = async () => {
    setGenerating(true);
    setReportError(null);
    try {
      const data = await reportService.generateReport({
        itinerary_id: itin.itinerary_id,
        itinerary_data: itin,
        title: `${itin.total_days || 2}-Day Executive Travel Dossier: ${itin.destination}`,
        planning_notes: itin.general_notes ? itin.general_notes.join('; ') : '',
      });
      setGeneratedReport(data);
    } catch (err) {
      console.error('Failed to generate backend report:', err);
      setReportError(err?.response?.data?.detail || 'Failed to generate backend ReportLab PDF. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  // Download backend ReportLab PDF
  const handleDownloadBackendPdf = async () => {
    if (!generatedReport?.report_id) {
      await handleGenerateReportLabPdf();
      return;
    }
    setDownloading(true);
    try {
      await reportService.downloadReportPdf(generatedReport.report_id, itin.destination);
    } catch (err) {
      console.error('Download error:', err);
      setReportError('Failed to download PDF. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  // Quick client-side fallback
  const handleQuickClientPdf = () => {
    pdfExportService.generateItineraryPdf(itin);
  };

  const analytics = generatedReport?.analytics;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header and Download Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#DCE6E3] pb-5">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="px-3 py-1 rounded-full bg-[#18B8A6]/10 text-[#129889] text-xs font-bold border border-[#18B8A6]/20">
              Reporting & Analytics
            </span>
            <span className="text-xs text-[#829196]">•</span>
            <span className="text-xs font-semibold text-[#52636A]">ReportLab Enterprise Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#163B46] tracking-tight">
            Travel Reports & Analytics Dossier
          </h1>
          <p className="text-xs sm:text-sm text-[#52636A] mt-1">
            Publication-grade PDF reports with strict provenance verification, route metrics, and visual analytics.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <button
            onClick={() => window.print()}
            className="px-3.5 py-2.5 rounded-xl bg-white border border-[#DCE6E3] text-[#26383D] hover:bg-[#EEF3F1] text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print</span>
          </button>

          <button
            onClick={handleQuickClientPdf}
            className="px-3.5 py-2.5 rounded-xl bg-white border border-[#DCE6E3] text-[#26383D] hover:bg-[#EEF3F1] text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
            title="Instant in-browser PDF generation"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Quick Export</span>
          </button>

          <button
            onClick={handleDownloadBackendPdf}
            disabled={generating || downloading}
            className="px-5 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white text-xs font-bold shadow-soft transition-all flex items-center space-x-2 disabled:opacity-60"
          >
            {generating || downloading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{generating ? 'Compiling PDF...' : 'Downloading...'}</span>
              </>
            ) : (
              <>
                <FileCheck className="w-4 h-4" />
                <span>{generatedReport ? 'Download ReportLab PDF' : 'Generate Enterprise PDF'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {reportError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600" />
          <span>{reportError}</span>
        </div>
      )}

      {/* Backend Report Confirmation Card */}
      {generatedReport && (
        <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 shadow-soft flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 border border-emerald-300 flex items-center justify-center text-[#16A36A] font-bold">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-bold text-[#163B46]">ReportLab Dossier Compiled</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-[#16A36A] text-[10px] font-bold">
                  Verified Ready
                </span>
              </div>
              <p className="text-xs text-[#52636A] mt-0.5">
                Report ID: <span className="text-[#18B8A6] font-mono">{generatedReport.report_id}</span> • File Size:{' '}
                {(generatedReport.file_size_bytes / 1024).toFixed(1)} KB • Multi-Page Layout
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleDownloadBackendPdf}
              disabled={downloading}
              className="px-4 py-2 rounded-xl bg-[#16A36A] hover:bg-emerald-700 text-white font-bold text-xs flex items-center space-x-1.5 transition-colors shadow-sm"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download PDF File</span>
            </button>
            <button
              onClick={() => navigate('/analytics')}
              className="px-4 py-2 rounded-xl bg-white border border-[#DCE6E3] text-[#26383D] hover:bg-[#EEF3F1] font-semibold text-xs flex items-center space-x-1.5 transition-colors shadow-sm"
            >
              <BarChart3 className="w-3.5 h-3.5 text-[#18B8A6]" />
              <span>Interactive Analytics</span>
            </button>
          </div>
        </div>
      )}

      {/* View Switcher Tabs */}
      <div className="flex items-center space-x-2 border-b border-[#DCE6E3] pb-2">
        <button
          onClick={() => setActiveTab('dossier')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'dossier'
              ? 'bg-[#18B8A6] text-white shadow-soft'
              : 'bg-white text-[#52636A] hover:text-[#163B46] border border-[#DCE6E3]'
          }`}
        >
          Printable Dossier Preview
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'analytics'
              ? 'bg-[#18B8A6] text-white shadow-soft'
              : 'bg-white text-[#52636A] hover:text-[#163B46] border border-[#DCE6E3]'
          }`}
        >
          Analytics & Metrics Summary
        </button>
      </div>

      {activeTab === 'dossier' ? (
        /* Printable Report Document Card Preview */
        <div className="p-8 sm:p-12 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft space-y-10 font-sans text-[#26383D]">
          {/* Document Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#DCE6E3] pb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[#163B46] flex items-center justify-center text-[#18B8A6] font-bold shadow-sm">
                <Compass className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xl font-extrabold text-[#163B46] tracking-tight">TravelSenseAI</span>
                <p className="text-xs text-[#52636A]">Autonomous Geospatial & Optimization Engine</p>
              </div>
            </div>

            <div className="text-right text-xs text-[#52636A]">
              <p className="font-semibold text-[#163B46]">Itinerary ID: {itin.itinerary_id}</p>
              <p className="text-[11px] text-[#829196] mt-0.5">
                Generated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
          </div>

          {/* Section 1: Trip Overview Grid */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-[#829196] uppercase tracking-wider flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-[#18B8A6]" />
              <span>1. Trip Overview</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-5 rounded-2xl bg-[#F4F7F6] border border-[#DCE6E3] text-xs">
              <div>
                <span className="text-[10px] text-[#829196] uppercase font-semibold">Destination</span>
                <p className="font-bold text-[#163B46] text-sm mt-0.5">{itin.destination}</p>
              </div>
              <div>
                <span className="text-[10px] text-[#829196] uppercase font-semibold">Travel Dates</span>
                <p className="font-bold text-[#163B46] text-sm mt-0.5">
                  {formatDateDisplay(itin.start_date)} - {formatDateDisplay(itin.end_date)}
                </p>
              </div>
              <div>
                <span className="text-[10px] text-[#829196] uppercase font-semibold">Total Road Distance</span>
                <p className="font-bold text-[#18B8A6] text-sm mt-0.5">{formatDistanceKm(itin.total_distance_km)}</p>
              </div>
              <div>
                <span className="text-[10px] text-[#829196] uppercase font-semibold">Estimated Budget</span>
                <p className="font-bold text-[#16A36A] text-sm mt-0.5">
                  {formatCurrency(budget.estimated_total_cost || 0)}
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: Day-by-Day Schedule */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-[#829196] uppercase tracking-wider flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-[#18B8A6]" />
              <span>2. Day-by-Day Touring Sequence</span>
            </h3>

            <div className="space-y-4">
              {itin.days?.map((day) => (
                <div key={day.day_number} className="rounded-2xl bg-[#F4F7F6] border border-[#DCE6E3] p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-2">
                    <span className="text-xs font-bold text-[#163B46]">
                      Day {day.day_number}: {day.theme || 'Sightseeing'} ({day.date})
                    </span>
                    <span className="text-[11px] text-[#52636A]">
                      {day.stops?.length || 0} Places • {formatDistanceKm(day.daily_distance_km)} Road
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#DCE6E3] text-[11px] text-[#829196]">
                          <th className="pb-2">Seq</th>
                          <th className="pb-2">Attraction / Activity</th>
                          <th className="pb-2">Scheduled Window</th>
                          <th className="pb-2">Duration</th>
                          <th className="pb-2">Admission Fee</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#DCE6E3] text-[#26383D]">
                        {day.stops?.map((stop, sIdx) => {
                          if (stop.is_start_location || stop.is_end_location) return null;
                          return (
                            <tr key={stop.place_id || sIdx} className="hover:bg-white/80 transition-colors">
                              <td className="py-2.5 font-bold text-[#18B8A6]">#{stop.stop_order || sIdx + 1}</td>
                              <td className="py-2.5 font-semibold text-[#163B46]">{stop.name}</td>
                              <td className="py-2.5 text-[#52636A]">
                                {stop.arrival_time} - {stop.departure_time}
                              </td>
                              <td className="py-2.5 text-[#52636A]">{stop.visit_duration_mins} mins</td>
                              <td className="py-2.5 text-[#16A36A] font-semibold">
                                {stop.total_entrance_fee > 0
                                  ? formatCurrency(stop.total_entrance_fee)
                                  : 'Free / Included'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Financial Budget Ledger */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-[#829196] uppercase tracking-wider flex items-center space-x-2">
              <DollarSign className="w-4 h-4 text-[#16A36A]" />
              <span>3. Financial Budget Ledger & Price Provenance</span>
            </h3>

            <div className="overflow-x-auto p-5 rounded-2xl bg-[#F4F7F6] border border-[#DCE6E3]">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#DCE6E3] text-[11px] text-[#829196]">
                    <th className="pb-2">Expense Category</th>
                    <th className="pb-2">Estimated Amount</th>
                    <th className="pb-2">Allocation</th>
                    <th className="pb-2">Provenance Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DCE6E3] text-[#26383D]">
                  <tr>
                    <td className="py-2.5 font-medium">Road Transportation</td>
                    <td className="py-2.5 text-[#16A36A] font-bold">{formatCurrency(cb.transportation || 0)}</td>
                    <td className="py-2.5 text-[#52636A]">
                      {(((cb.transportation || 0) / (budget.estimated_total_cost || 1)) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 text-[#829196]">OpenRouteService rate model</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 font-medium">Attraction Entrance Fees</td>
                    <td className="py-2.5 text-[#16A36A] font-bold">{formatCurrency(cb.entrance_fees || 0)}</td>
                    <td className="py-2.5 text-[#52636A]">
                      {(((cb.entrance_fees || 0) / (budget.estimated_total_cost || 1)) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 text-[#829196]">Verified venue fees</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 font-medium">Food & Dining</td>
                    <td className="py-2.5 text-[#16A36A] font-bold">{formatCurrency(cb.food || 0)}</td>
                    <td className="py-2.5 text-[#52636A]">
                      {(((cb.food || 0) / (budget.estimated_total_cost || 1)) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 text-[#829196]">Regional moderate tier</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 font-medium">Accommodation</td>
                    <td className="py-2.5 text-[#16A36A] font-bold">{formatCurrency(cb.accommodation || 0)}</td>
                    <td className="py-2.5 text-[#52636A]">
                      {(((cb.accommodation || 0) / (budget.estimated_total_cost || 1)) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 text-[#829196]">Lodging tier estimate</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 font-medium">Contingency Buffer (8%)</td>
                    <td className="py-2.5 text-[#16A36A] font-bold">{formatCurrency(cb.contingency_buffer || 0)}</td>
                    <td className="py-2.5 text-[#52636A]">
                      {(((cb.contingency_buffer || 0) / (budget.estimated_total_cost || 1)) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 text-[#829196]">Incidentals buffer</td>
                  </tr>
                  <tr className="font-bold text-[#163B46] bg-white">
                    <td className="py-3">Total Estimated Cost</td>
                    <td className="py-3 text-[#16A36A] text-sm">{formatCurrency(budget.estimated_total_cost || 0)}</td>
                    <td className="py-3">100.0%</td>
                    <td className="py-3 text-[#18B8A6]">{itin.feasibility_status}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 4: Travel Guidelines */}
          <div className="p-5 rounded-2xl bg-teal-50/60 border border-[#18B8A6]/30 text-xs text-[#52636A] space-y-2">
            <span className="font-bold text-[#163B46] flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-[#18B8A6]" />
              <span>TravelSenseAI Certification Notice</span>
            </span>
            <p className="leading-relaxed">
              This itinerary has been algorithmically validated for time constraints and road connectivity. Opening hours and admission fees for designated attractions are verified against archaeological and tourism archives. Travelers are advised to carry digital or physical copies of this document during transit.
            </p>
          </div>
        </div>
      ) : (
        /* Visual Analytics Tab Summary */
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
              <span className="text-xs font-semibold text-[#829196] uppercase tracking-wider">Total Attractions</span>
              <p className="text-2xl font-black text-[#163B46] mt-1">
                {itin.total_attractions_scheduled || itin.days?.reduce((sum, d) => sum + (d.stops?.length || 0), 0) || 4}
              </p>
              <span className="text-xs text-[#18B8A6] font-medium">Scheduled by 2-Opt TSP</span>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
              <span className="text-xs font-semibold text-[#829196] uppercase tracking-wider">Total Road Route</span>
              <p className="text-2xl font-black text-[#163B46] mt-1">{formatDistanceKm(itin.total_distance_km)}</p>
              <span className="text-xs text-[#18B8A6] font-medium">Optimized Road Network</span>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
              <span className="text-xs font-semibold text-[#829196] uppercase tracking-wider">Budget Capacity</span>
              <p className="text-2xl font-black text-[#163B46] mt-1">{formatCurrency(budget.total_budget || 5000)}</p>
              <span className="text-xs text-[#16A36A] font-medium">
                {((budget.estimated_total_cost / (budget.total_budget || 1)) * 100).toFixed(0)}% Utilized
              </span>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
              <span className="text-xs font-semibold text-[#829196] uppercase tracking-wider">Active Touring Time</span>
              <p className="text-2xl font-black text-[#163B46] mt-1">
                {((itin.total_visit_time_mins || 360) / 60).toFixed(1)} hrs
              </p>
              <span className="text-xs text-[#52636A]">
                + {((itin.total_travel_time_mins || 60) / 60).toFixed(1)} hrs road transit
              </span>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft flex items-center justify-between">
            <div>
              <h4 className="text-base font-bold text-[#163B46]">Full Analytics Dashboard Available</h4>
              <p className="text-xs text-[#52636A] mt-0.5">
                Explore all 7 visual analytics charts (Category distribution, Score breakdown, Daily expense ledger, Travel duration, Distance progression, Budget gauge, Attraction metrics).
              </p>
            </div>
            <button
              onClick={() => navigate('/analytics')}
              className="px-5 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs flex items-center space-x-2 transition-colors whitespace-nowrap shadow-soft"
            >
              <span>Open Analytics</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
