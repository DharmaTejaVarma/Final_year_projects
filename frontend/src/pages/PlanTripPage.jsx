import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Compass,
  Calendar,
  MapPin,
  Users,
  DollarSign,
  Car,
  Footprints,
  Bike,
  Sparkles,
  ArrowRight,
  Clock,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Wand2,
} from 'lucide-react';
import { useTrip } from '../context/TripContext';
import recommendationService from '../services/recommendationService';
import itineraryService from '../services/itineraryService';
import aiService from '../services/aiService';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { formatCurrency } from '../utils/formatters';

const POPULAR_DESTINATIONS = ['Hyderabad', 'Bengaluru', 'Jaipur', 'Goa', 'Delhi', 'Mumbai'];

const AVAILABLE_INTERESTS = [
  'Historical Places',
  'Food',
  'Photography',
  'Culture',
  'Nature',
  'Shopping',
  'Architecture',
  'Museums',
];

export default function PlanTripPage() {
  const navigate = useNavigate();
  const { tripPlan, updatePlan, setRecommendations, setCurrentItinerary } = useTrip();

  // Natural language extraction state
  const [nlQuery, setNlQuery] = useState(tripPlan.userQuery || '');
  const [extracting, setExtracting] = useState(false);
  const [extractionResult, setExtractionResult] = useState(null);

  // Form states
  const [destination, setDestination] = useState(tripPlan.destination || 'Hyderabad');
  const [startDate, setStartDate] = useState(tripPlan.startDate);
  const [endDate, setEndDate] = useState(tripPlan.endDate);
  const [travelersCount, setTravelersCount] = useState(tripPlan.travelersCount || 1);
  const [budget, setBudget] = useState(tripPlan.budget || 5000);
  const [transportation, setTransportation] = useState(tripPlan.transportation || 'driving-car');
  const [pace, setPace] = useState(tripPlan.pace || 'relaxed');
  const [dailyHours, setDailyHours] = useState(tripPlan.dailyAvailableHours || 8.0);
  const [interests, setInterests] = useState(tripPlan.interests || ['Historical Places', 'Food', 'Culture']);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Auto-calculate trip duration in days
  const durationDays = React.useMemo(() => {
    if (!startDate || !endDate) return 1;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    return Math.max(1, isNaN(diffDays) ? 1 : diffDays);
  }, [startDate, endDate]);

  // Handle Natural Language Extraction via backend AI
  const handleExtractPreferences = async (textToExtract) => {
    const query = textToExtract || nlQuery;
    if (!query.trim()) return;

    setExtracting(true);
    setError(null);
    try {
      const res = await aiService.extractPreferences(query.trim());
      setExtractionResult(res);

      const p = res.preferences;
      if (p.destination) setDestination(p.destination);
      if (p.budget) setBudget(p.budget);
      if (p.travel_style) setPace(p.travel_style);
      if (p.transportation) setTransportation(p.transportation);
      if (p.travelers_count) setTravelersCount(p.travelers_count);

      if (p.interests && p.interests.length > 0) {
        const mapped = p.interests.map((item) => {
          if (item === 'history') return 'Historical Places';
          if (item === 'food') return 'Food';
          if (item === 'photography') return 'Photography';
          if (item === 'culture') return 'Culture';
          if (item === 'nature') return 'Nature';
          if (item === 'shopping') return 'Shopping';
          return item.charAt(0).toUpperCase() + item.slice(1);
        });
        setInterests([...new Set(mapped)]);
      }

      if (p.duration_days) {
        const start = new Date();
        start.setDate(start.getDate() + 7);
        const end = new Date(start);
        end.setDate(start.getDate() + (p.duration_days - 1));
        setStartDate(start.toISOString().split('T')[0]);
        setEndDate(end.toISOString().split('T')[0]);
      }
    } catch (err) {
      setError(err.message || 'Could not extract preferences from text.');
    } finally {
      setExtracting(false);
    }
  };

  useEffect(() => {
    if (tripPlan.userQuery && !extractionResult) {
      handleExtractPreferences(tripPlan.userQuery);
    }
  }, []);

  const toggleInterest = (interest) => {
    setInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  };

  const syncPlanContext = () => {
    updatePlan({
      destination,
      startDate,
      endDate,
      travelersCount,
      budget,
      transportation,
      pace,
      dailyAvailableHours: dailyHours,
      interests,
    });
  };

  const handleDiscoverRecommendations = async () => {
    if (!destination.trim()) {
      setError('Please select or specify a destination.');
      return;
    }

    syncPlanContext();
    setLoading(true);
    setError(null);

    try {
      const data = await recommendationService.getRecommendations({
        destination,
        interests,
        budget,
        availableDurationDays: durationDays,
        transportation,
        dailyTouringHours: dailyHours,
        limit: 12,
      });

      setRecommendations(data.recommendations || []);
      navigate('/recommendations');
    } catch (err) {
      setError(err.message || 'Failed to retrieve POI recommendations.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateItineraryDirect = async () => {
    if (!destination.trim()) {
      setError('Please select or specify a destination.');
      return;
    }

    syncPlanContext();
    setLoading(true);
    setError(null);

    try {
      const itin = await itineraryService.generateItinerary({
        destination,
        startDate,
        endDate,
        travelersCount,
        budget,
        dailyAvailableHours: dailyHours,
        transportation,
        pace,
      });

      setCurrentItinerary(itin);
      navigate('/itinerary');
    } catch (err) {
      setError(err.message || 'Failed to generate itinerary. You can discover recommendations first.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Top Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#18B8A6]/10 text-[#129889] border border-[#18B8A6]/25 text-xs font-bold uppercase tracking-wider">
          <Sliders className="w-3.5 h-3.5" />
          <span>Trip Customization & Planning</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#163B46]">
          Configure Your Perfect Travel Itinerary
        </h1>
        <p className="text-xs sm:text-sm text-[#52636A] max-w-2xl mx-auto">
          Tailor your destinations, budget, and travel pacing. You can fill out the form manually or let our AI assistant extract your requirements instantly.
        </p>
      </div>

      {error && <ErrorMessage message={error} onRetry={() => setError(null)} />}

      {/* --- Natural Language AI Extractor Banner --- */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft-md relative overflow-hidden">
        <div className="flex items-center space-x-2.5 mb-3">
          <div className="w-9 h-9 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] flex items-center justify-center text-[#18B8A6]">
            <Wand2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#163B46]">Natural-Language AI Auto-Fill</h3>
            <p className="text-[11px] text-[#52636A]">
              Type or speak your travel desires in plain English to automatically populate all parameters below.
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="relative">
            <textarea
              rows={2}
              value={nlQuery}
              onChange={(e) => setNlQuery(e.target.value)}
              placeholder="e.g. I want a relaxed 2-day trip to Hyderabad. I like historical places and good food. My budget is ₹5,000."
              className="w-full p-3.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-xs sm:text-sm text-[#26383D] placeholder-[#829196] focus:outline-none focus:border-[#18B8A6] focus:bg-white resize-none transition-colors"
            />
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            {/* Quick Prompts */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-[#52636A]">
              <span className="text-[#829196] font-medium">Quick Fill:</span>
              <button
                type="button"
                onClick={() => {
                  const q = 'I want a relaxed 2-day trip to Hyderabad. I like historical places and good food. My budget is ₹5,000.';
                  setNlQuery(q);
                  handleExtractPreferences(q);
                }}
                className="px-2.5 py-1 rounded-lg bg-[#EEF3F1] hover:bg-[#DCE6E3] text-[#163B46] border border-[#DCE6E3] font-medium transition-colors"
              >
                Hyderabad 2-Day History (₹5k)
              </button>
              <button
                type="button"
                onClick={() => {
                  const q = 'A fast packed 3 days walking tour in Bengaluru with Rs 6000 for 2 people';
                  setNlQuery(q);
                  handleExtractPreferences(q);
                }}
                className="px-2.5 py-1 rounded-lg bg-[#EEF3F1] hover:bg-[#DCE6E3] text-[#163B46] border border-[#DCE6E3] font-medium transition-colors"
              >
                Bengaluru 3-Day Walking (₹6k)
              </button>
            </div>

            <button
              type="button"
              onClick={() => handleExtractPreferences()}
              disabled={extracting || !nlQuery.trim()}
              className="px-4 py-2 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs flex items-center space-x-1.5 shadow-soft transition-all disabled:opacity-50"
            >
              {extracting ? (
                <LoadingSpinner size="sm" label="" />
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Parse with AI</span>
                </>
              )}
            </button>
          </div>

          {/* Extraction Confirmation Pill */}
          {extractionResult && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-[#16A36A]">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-[#16A36A] flex-shrink-0" />
                <span>
                  Extracted via <strong>{extractionResult.source}</strong> ({(extractionResult.confidence * 100).toFixed(0)}% confidence). Parameters applied to form below.
                </span>
              </div>
              {extractionResult.preferences?.needs_clarification && (
                <span className="text-[11px] text-[#E6A23C] font-semibold">
                  Note: Some criteria need user confirmation.
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* --- Structured Form Card --- */}
      <div className="p-8 sm:p-10 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft-lg space-y-8">
        {/* Section 1: Destination Selection */}
        <div className="space-y-3">
          <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider flex items-center">
            <MapPin className="w-3.5 h-3.5 mr-1.5 text-[#18B8A6]" />
            1. Target Destination City
          </label>
          <div className="space-y-2">
            <input
              type="text"
              required
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Hyderabad, Bengaluru, Jaipur"
              className="w-full px-4 py-3 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white text-sm text-[#26383D] placeholder-[#829196] focus:outline-none transition-all"
            />
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[11px] text-[#829196] mr-1 font-medium">Popular hubs:</span>
              {POPULAR_DESTINATIONS.map((dest) => (
                <button
                  key={dest}
                  type="button"
                  onClick={() => setDestination(dest)}
                  className={`text-xs px-3 py-1 rounded-xl border transition-all ${
                    destination.toLowerCase() === dest.toLowerCase()
                      ? 'bg-[#18B8A6] text-white border-[#18B8A6] font-bold shadow-soft'
                      : 'bg-[#F4F7F6] text-[#52636A] border-[#DCE6E3] hover:bg-[#EEF3F1] hover:text-[#163B46]'
                  }`}
                >
                  {dest}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Section 2: Dates & Duration */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider flex items-center">
              <Calendar className="w-3.5 h-3.5 mr-1.5 text-[#18B8A6]" />
              2. Start Date
            </label>
            <input
              type="date"
              required
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white text-sm text-[#26383D] focus:outline-none transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider flex items-center justify-between">
              <span className="flex items-center">
                <Calendar className="w-3.5 h-3.5 mr-1.5 text-[#18B8A6]" />
                End Date
              </span>
              <span className="text-[11px] text-[#18B8A6] font-bold lowercase">
                ({durationDays} day{durationDays > 1 ? 's' : ''})
              </span>
            </label>
            <input
              type="date"
              required
              value={endDate}
              min={startDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white text-sm text-[#26383D] focus:outline-none transition-all"
            />
          </div>
        </div>

        {/* Section 3: Travelers & Budget */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider flex items-center">
              <Users className="w-3.5 h-3.5 mr-1.5 text-[#18B8A6]" />
              3. Number of Travelers
            </label>
            <div className="flex items-center space-x-2 bg-[#F4F7F6] border border-[#DCE6E3] p-1.5 rounded-xl">
              {[1, 2, 3, 4, 6].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setTravelersCount(num)}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    travelersCount === num
                      ? 'bg-[#163B46] text-white shadow-soft'
                      : 'text-[#52636A] hover:text-[#163B46] hover:bg-white'
                  }`}
                >
                  {num} {num === 1 ? 'Solo' : num === 2 ? 'Couple' : `${num}`}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider flex items-center justify-between">
              <span className="flex items-center">
                <DollarSign className="w-3.5 h-3.5 mr-1.5 text-[#16A36A]" />
                Total Budget (INR)
              </span>
              <span className="text-[11px] text-[#16A36A] font-bold">
                {formatCurrency(budget)}
              </span>
            </label>
            <input
              type="number"
              min="1000"
              step="500"
              value={budget}
              onChange={(e) => setBudget(parseFloat(e.target.value) || 0)}
              className="w-full px-4 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white text-sm text-[#26383D] focus:outline-none transition-all"
            />
          </div>
        </div>

        {/* Section 4: Transportation & Pacing */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Transport */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider">
              4. Transportation
            </label>
            <div className="grid grid-cols-3 gap-1.5 bg-[#F4F7F6] p-1.5 rounded-xl border border-[#DCE6E3]">
              {[
                { id: 'driving-car', label: 'Car', icon: Car },
                { id: 'foot-walking', label: 'Walk', icon: Footprints },
                { id: 'cycling-regular', label: 'Bike', icon: Bike },
              ].map((m) => {
                const Icon = m.icon;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setTransportation(m.id)}
                    className={`py-2 px-1 rounded-lg text-[11px] font-bold flex flex-col items-center justify-center space-y-1 transition-all ${
                      transportation === m.id
                        ? 'bg-[#18B8A6] text-white shadow-soft'
                        : 'text-[#52636A] hover:bg-white hover:text-[#163B46]'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{m.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Travel Pace */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider">
              5. Pacing Style
            </label>
            <div className="grid grid-cols-3 gap-1.5 bg-[#F4F7F6] p-1.5 rounded-xl border border-[#DCE6E3]">
              {[
                { id: 'relaxed', label: 'Relaxed' },
                { id: 'moderate', label: 'Moderate' },
                { id: 'packed', label: 'Packed' },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setPace(p.id)}
                  className={`py-2 px-1 rounded-lg text-[11px] font-bold capitalize transition-all ${
                    pace === p.id
                      ? 'bg-[#163B46] text-white shadow-soft'
                      : 'text-[#52636A] hover:bg-white hover:text-[#163B46]'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Daily Touring Hours */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider flex items-center justify-between">
              <span>6. Touring Hours</span>
              <span className="text-[11px] text-[#18B8A6] font-bold">{dailyHours}h/day</span>
            </label>
            <div className="grid grid-cols-3 gap-1.5 bg-[#F4F7F6] p-1.5 rounded-xl border border-[#DCE6E3]">
              {[6.0, 8.0, 10.0].map((hrs) => (
                <button
                  key={hrs}
                  type="button"
                  onClick={() => setDailyHours(hrs)}
                  className={`py-2 px-1 rounded-lg text-[11px] font-bold transition-all ${
                    dailyHours === hrs
                      ? 'bg-[#163B46] text-white shadow-soft'
                      : 'text-[#52636A] hover:bg-white hover:text-[#163B46]'
                  }`}
                >
                  {hrs}h/day
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Section 5: Interests Selection */}
        <div className="space-y-3">
          <label className="text-xs font-bold text-[#163B46] uppercase tracking-wider flex items-center justify-between">
            <span>7. Tourism Interests & Themes (Factor P)</span>
            <span className="text-[11px] text-[#829196] font-normal">
              {interests.length} selected
            </span>
          </label>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_INTERESTS.map((interest) => {
              const selected = interests.includes(interest);
              return (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    selected
                      ? 'bg-[#18B8A6]/15 text-[#129889] border-[#18B8A6] shadow-soft'
                      : 'bg-[#F4F7F6] text-[#52636A] border-[#DCE6E3] hover:bg-[#EEF3F1] hover:text-[#163B46]'
                  }`}
                >
                  {interest}
                </button>
              );
            })}
          </div>
        </div>

        {/* Actions Bar */}
        <div className="pt-6 border-t border-[#DCE6E3] flex flex-col sm:flex-row items-center justify-between gap-4">
          <button
            type="button"
            onClick={handleDiscoverRecommendations}
            disabled={loading}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-[#EEF3F1] hover:bg-[#DCE6E3] text-[#163B46] font-bold text-xs sm:text-sm border border-[#DCE6E3] transition-all flex items-center justify-center space-x-2 shadow-soft disabled:opacity-50"
          >
            <span>Browse Recommendations First</span>
            <ArrowRight className="w-4 h-4 text-[#18B8A6]" />
          </button>

          <button
            type="button"
            onClick={handleGenerateItineraryDirect}
            disabled={loading}
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs sm:text-sm shadow-soft hover:shadow-soft-md transition-all hover:scale-[1.02] flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <LoadingSpinner size="sm" label="" />
            ) : (
              <>
                <Calendar className="w-4 h-4" />
                <span>Generate Itinerary Directly</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
