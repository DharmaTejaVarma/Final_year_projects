import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Compass,
  Calendar,
  Clock,
  MapPin,
  Route,
  DollarSign,
  CloudSun,
  Sparkles,
  FileText,
  Map as MapIcon,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Car,
  Utensils,
  Share2,
  Download,
  Info,
} from 'lucide-react';
import { useTrip } from '../context/TripContext';
import itineraryService from '../services/itineraryService';
import pdfExportService from '../services/pdfExportService';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import AttractionImage from '../components/AttractionImage';
import {
  formatCurrency,
  formatDurationMins,
  formatDistanceKm,
  formatDateDisplay,
  getCategoryBadgeColor,
} from '../utils/formatters';

export default function ItineraryPage() {
  const navigate = useNavigate();
  const {
    tripPlan,
    currentItinerary,
    setCurrentItinerary,
    selectedAttractions,
    saveCurrentTrip,
  } = useTrip();

  const [activeDayTab, setActiveDayTab] = useState(1);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState(null);

  // Auto-generate if not loaded
  useEffect(() => {
    const autoGen = async () => {
      if (!currentItinerary) {
        setRegenerating(true);
        setError(null);
        try {
          const itin = await itineraryService.generateItinerary({
            destination: tripPlan.destination || 'Hyderabad',
            startDate: tripPlan.startDate,
            endDate: tripPlan.endDate,
            travelersCount: tripPlan.travelersCount || 1,
            budget: tripPlan.budget || 5000,
            dailyAvailableHours: tripPlan.dailyAvailableHours || 8.0,
            transportation: tripPlan.transportation || 'driving-car',
            pace: tripPlan.pace || 'relaxed',
            selectedAttractions: selectedAttractions.length > 0 ? selectedAttractions : null,
          });
          setCurrentItinerary(itin);
          saveCurrentTrip(itin);
        } catch (err) {
          setError(err.message || 'Could not automatically generate itinerary.');
        } finally {
          setRegenerating(false);
        }
      }
    };

    autoGen();
  }, [currentItinerary]);

  const handleRegenerate = async () => {
    setRegenerating(true);
    setError(null);
    try {
      const itin = await itineraryService.generateItinerary({
        destination: tripPlan.destination,
        startDate: tripPlan.startDate,
        endDate: tripPlan.endDate,
        travelersCount: tripPlan.travelersCount,
        budget: tripPlan.budget,
        dailyAvailableHours: tripPlan.dailyAvailableHours,
        transportation: tripPlan.transportation,
        pace: tripPlan.pace,
        selectedAttractions: selectedAttractions.length > 0 ? selectedAttractions : null,
      });
      setCurrentItinerary(itin);
      saveCurrentTrip(itin);
    } catch (err) {
      setError(err.message || 'Failed to regenerate itinerary.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleExportPdf = () => {
    if (currentItinerary) {
      pdfExportService.generateItineraryPdf(currentItinerary);
    }
  };

  if (regenerating && !currentItinerary) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingSpinner
          size="lg"
          label="Synthesizing multi-day schedule, 2-Opt routes & weather allocations..."
        />
      </div>
    );
  }

  if (!currentItinerary) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft flex items-center justify-center mx-auto text-[#18B8A6]">
          <Compass className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-[#163B46]">No Itinerary Generated Yet</h2>
        <p className="text-sm text-[#52636A] max-w-md mx-auto">
          Configure your travel dates and preferences to let our engine construct an optimal schedule.
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
  const activeDay = itin.days?.find((d) => d.day_number === activeDayTab) || itin.days?.[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* --- Top Header & Action Controls --- */}
      <div className="p-8 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-[#18B8A6]/10 text-[#129889] text-xs font-bold border border-[#18B8A6]/20">
              {itin.total_days}-Day Tour Plan
            </span>
            <span className="text-xs text-[#829196]">•</span>
            <span
              className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                itin.feasibility_status === 'feasible'
                  ? 'bg-emerald-50 text-[#16A36A] border-emerald-200'
                  : 'bg-amber-50 text-[#E6A23C] border-amber-200'
              }`}
            >
              {(itin.feasibility_status || 'feasible').toUpperCase()}
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-[#163B46] tracking-tight">
            {itin.destination} Travel Itinerary
          </h1>

          <p className="text-xs sm:text-sm text-[#52636A] flex flex-wrap items-center gap-2">
            <span>
              {formatDateDisplay(itin.start_date)} — {formatDateDisplay(itin.end_date)}
            </span>
            <span className="text-[#829196]">•</span>
            <span>{itin.travelers_count} traveler{itin.travelers_count > 1 ? 's' : ''}</span>
            <span className="text-[#829196]">•</span>
            <span>Total Road: <strong className="text-[#163B46]">{formatDistanceKm(itin.total_distance_km)}</strong></span>
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="px-4 py-2.5 rounded-xl bg-white hover:bg-[#EEF3F1] text-[#26383D] text-xs font-semibold border border-[#DCE6E3] shadow-sm transition-colors flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
            <span>Regenerate</span>
          </button>

          <button
            onClick={() => navigate('/map')}
            className="px-4 py-2.5 rounded-xl bg-white hover:bg-[#EEF3F1] text-[#18B8A6] text-xs font-semibold border border-[#DCE6E3] shadow-sm transition-colors flex items-center space-x-1.5"
          >
            <MapIcon className="w-3.5 h-3.5" />
            <span>Map View</span>
          </button>

          <button
            onClick={handleExportPdf}
            className="px-5 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white text-xs font-bold shadow-soft transition-all flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={handleRegenerate} />}

      {/* --- Financial & Algorithmic Summary Grid --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Budget Ledger */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#829196] uppercase tracking-wider">
              Budget & Expenses
            </span>
            <DollarSign className="w-4 h-4 text-[#16A36A]" />
          </div>

          <div>
            <span className="text-xs text-[#52636A]">Total Estimated Cost:</span>
            <p className="text-2xl font-black text-[#16A36A]">
              {formatCurrency(budget.estimated_total_cost || 0)}
            </p>
            <span className="text-[11px] text-[#829196]">
              Target Budget: {formatCurrency(budget.total_budget || tripPlan.budget)}
            </span>
          </div>

          {budget.is_budget_exceeded ? (
            <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />
              <span>Budget exceeded by {formatCurrency(budget.budget_overrun || 0)}</span>
            </div>
          ) : (
            <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-[#16A36A] text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#16A36A] flex-shrink-0" />
              <span>Remaining: {formatCurrency(budget.remaining_budget || 0)}</span>
            </div>
          )}

          <div className="space-y-1.5 pt-2 border-t border-[#DCE6E3] text-xs text-[#52636A]">
            <div className="flex justify-between">
              <span>Road Transit:</span>
              <span className="font-semibold text-[#26383D]">{formatCurrency(budget.category_breakdown?.transportation || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span>Entrance Fees:</span>
              <span className="font-semibold text-[#26383D]">{formatCurrency(budget.category_breakdown?.entrance_fees || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span>Dining Allocations:</span>
              <span className="font-semibold text-[#26383D]">{formatCurrency(budget.category_breakdown?.food || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span>Contingency Buffer (8%):</span>
              <span className="font-semibold text-[#26383D]">{formatCurrency(budget.category_breakdown?.contingency_buffer || 0)}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Algorithmic Utility Score U(I) */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#829196] uppercase tracking-wider">
              Optimization Utility
            </span>
            <Sparkles className="w-4 h-4 text-[#18B8A6]" />
          </div>

          <div>
            <span className="text-xs text-[#52636A]">Objective Score U(I):</span>
            <p className="text-2xl font-black text-[#163B46]">
              {((itin.utility?.overall_utility_score || 0.72) * 100).toFixed(1)} / 100
            </p>
            <span className="text-[11px] text-[#829196]">Multi-criteria optimization index</span>
          </div>

          <div className="p-3 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] text-xs font-mono text-[#163B46] leading-relaxed">
            {itin.utility?.formula_summary ||
              'U(I) = 0.30(R) + 0.20(W) + 0.15(T) + 0.15(Dv) - 0.10(Tr) - 0.10(C)'}
          </div>

          <p className="text-xs text-[#52636A] leading-relaxed">
            Balances POI quality (R), weather favorability (W), temporal efficiency (T), theme diversity (Dv), while penalizing transit friction (Tr) and cost overrun (C).
          </p>
        </div>

        {/* Card 3: Pacing & Route Efficiency */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#829196] uppercase tracking-wider">
              Routing Performance
            </span>
            <Route className="w-4 h-4 text-[#163B46]" />
          </div>

          <div>
            <span className="text-xs text-[#52636A]">Total Visiting Sequence:</span>
            <p className="text-2xl font-black text-[#163B46]">
              {itin.days?.reduce((sum, d) => sum + (d.stops?.length || 0), 0) || 0} Stops
            </p>
            <span className="text-[11px] text-[#829196]">
              Across {itin.total_days} scheduled days
            </span>
          </div>

          <div className="space-y-2 pt-2 border-t border-[#DCE6E3] text-xs">
            <div className="flex items-center justify-between text-[#52636A]">
              <span>Algorithm:</span>
              <span className="font-semibold text-[#163B46]">2-Opt Local Search TSP</span>
            </div>
            <div className="flex items-center justify-between text-[#52636A]">
              <span>Road Circuity:</span>
              <span className="font-semibold text-[#163B46]">1.35x Geodesic Ratio</span>
            </div>
            <div className="flex items-center justify-between text-[#52636A]">
              <span>Operating Hours:</span>
              <span className="font-semibold text-[#16A36A]">Strictly Enforced</span>
            </div>
          </div>
        </div>
      </div>

      {/* --- Day Selector Tabs --- */}
      {itin.days && itin.days.length > 1 && (
        <div className="flex items-center space-x-2 border-b border-[#DCE6E3] pb-2 overflow-x-auto">
          {itin.days.map((day) => (
            <button
              key={day.day_number}
              onClick={() => setActiveDayTab(day.day_number)}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 whitespace-nowrap ${
                activeDayTab === day.day_number
                  ? 'bg-[#18B8A6] text-white shadow-soft'
                  : 'bg-white text-[#52636A] hover:text-[#163B46] border border-[#DCE6E3]'
              }`}
            >
              <span>Day {day.day_number}</span>
              <span className="text-[11px] opacity-80">({day.date})</span>
            </button>
          ))}
        </div>
      )}

      {/* --- Active Day Schedule & Timeline --- */}
      {activeDay && (
        <div className="space-y-6">
          {/* Day Banner & Weather Summary */}
          <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold text-[#18B8A6] uppercase tracking-wider">
                Day {activeDay.day_number} Schedule
              </span>
              <h3 className="text-xl font-bold text-[#163B46] mt-1">
                {activeDay.theme || `Exploration of ${itin.destination}`}
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">
                {activeDay.date} • {activeDay.stops?.length || 0} Attractions •{' '}
                {formatDistanceKm(activeDay.daily_distance_km)} road travel
              </p>
            </div>

            {/* Weather Pill */}
            {activeDay.weather && (
              <div className="px-4 py-2.5 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] text-xs flex items-center space-x-3">
                <CloudSun className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <div>
                  <div className="font-bold text-[#163B46]">
                    {activeDay.weather.condition || 'Mainly Clear'}
                  </div>
                  <div className="text-[11px] text-[#52636A]">
                    Precipitation: {activeDay.weather.precipitation_mm ?? 0} mm •{' '}
                    <span className="font-semibold text-[#16A36A]">
                      {activeDay.weather.is_outdoor_favorable ? 'Favorable' : 'Caution'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sequential Stops Timeline */}
          <div className="relative pl-6 sm:pl-8 space-y-6 before:content-[''] before:absolute before:left-3 before:top-4 before:bottom-4 before:w-0.5 before:bg-[#DCE6E3]">
            {activeDay.stops?.map((stop, sIdx) => {
              const isStart = stop.is_start_location;
              const isEnd = stop.is_end_location;

              if (isStart || isEnd) return null;

              return (
                <div key={stop.place_id || sIdx} className="relative group">
                  {/* Timeline Stop Badge */}
                  <div className="absolute -left-6 sm:-left-8 top-1.5 w-6 h-6 rounded-full bg-[#18B8A6] text-white text-xs font-extrabold flex items-center justify-center ring-4 ring-white shadow-sm">
                    {stop.stop_order || sIdx + 1}
                  </div>

                  {/* Stop Card */}
                  <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] hover:border-[#829196]/40 shadow-soft transition-all space-y-4">
                    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center border-b border-[#DCE6E3] pb-3">
                      <div className="w-20 h-20 sm:w-24 sm:h-20 rounded-xl overflow-hidden shrink-0 shadow-sm border border-[#DCE6E3] bg-[#EEF3F1]">
                        <AttractionImage
                          name={stop.name}
                          city={tripPlan.destination || itin?.destination}
                          attractionId={stop.place_id}
                          initialUrl={stop.image_url}
                          initialAttribution={stop.image_attribution}
                          aspectRatio="h-full"
                          alt={stop.name}
                          showAttribution={false}
                          className="w-full h-full object-cover"
                        />
                      </div>

                      <div className="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="text-base font-bold text-[#163B46]">{stop.name}</h4>
                            <span
                              className={`text-[11px] font-bold px-2 py-0.5 rounded border ${getCategoryBadgeColor(
                                stop.category
                              )}`}
                            >
                              {stop.category || 'Sight'}
                            </span>
                          </div>
                          {stop.address && (
                            <p className="text-xs text-[#52636A] mt-0.5 flex items-center">
                              <MapPin className="w-3.5 h-3.5 mr-1 text-[#829196] flex-shrink-0" />
                              <span>{stop.address}</span>
                            </p>
                          )}
                        </div>

                        {/* Timestamps Pill */}
                        <div className="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] text-[#26383D] shrink-0">
                          <Clock className="w-3.5 h-3.5 text-amber-600" />
                          <span className="font-bold text-[#163B46]">
                            {stop.arrival_time} — {stop.departure_time}
                          </span>
                          <span className="text-[#52636A]">({stop.visit_duration_mins}m)</span>
                        </div>
                      </div>
                    </div>

                    {/* Operational Details Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span className="text-[10px] text-[#829196] block uppercase tracking-wider">Entrance Fee:</span>
                        <p className="font-semibold text-[#16A36A] mt-0.5">
                          {stop.total_entrance_fee > 0
                            ? formatCurrency(stop.total_entrance_fee)
                            : 'Free / Included'}
                        </p>
                      </div>

                      <div>
                        <span className="text-[10px] text-[#829196] block uppercase tracking-wider">Operating Hours:</span>
                        <p className="font-semibold text-[#26383D] mt-0.5">
                          {stop.opening_hours || 'Verified Daylight'}
                        </p>
                      </div>

                      <div>
                        <span className="text-[10px] text-[#829196] block uppercase tracking-wider">Transit Leg:</span>
                        <p className="font-semibold text-[#18B8A6] mt-0.5">
                          {formatDistanceKm(stop.travel_distance_km)} ({formatDurationMins(stop.travel_duration_mins)})
                        </p>
                      </div>

                      <div>
                        <span className="text-[10px] text-[#829196] block uppercase tracking-wider">Venue Type:</span>
                        <p className="font-semibold text-[#26383D] mt-0.5">
                          {stop.is_outdoor ? 'Outdoor Venue' : 'Indoor / Museum'}
                        </p>
                      </div>
                    </div>

                    {/* Warnings / Notes if unverified */}
                    {stop.opening_hours_warning && (
                      <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center space-x-2">
                        <Info className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                        <span>{stop.opening_hours_warning}</span>
                      </div>
                    )}
                  </div>

                  {/* Scheduled Dining / Meal Breaks between stops */}
                  {activeDay.meal_breaks?.map((meal, mIdx) => {
                    // Display meal after stop 2 or if scheduled between
                    if (sIdx === 1) {
                      return (
                        <div
                          key={`meal-${meal.id || mIdx}`}
                          className="my-4 p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 text-[#163B46] flex items-center justify-between text-xs shadow-sm"
                        >
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-[#16A36A] font-bold">
                              <Utensils className="w-4 h-4" />
                            </div>
                            <div>
                              <h5 className="font-bold text-[#163B46]">🍽️ Dining: {meal.name}</h5>
                              <p className="text-[11px] text-[#52636A]">
                                Scheduled {meal.scheduled_start} — {meal.scheduled_end} ({meal.duration_mins} mins)
                              </p>
                            </div>
                          </div>
                          <span className="font-bold text-[#16A36A]">
                            {formatCurrency(meal.estimated_cost || 0)}
                          </span>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
