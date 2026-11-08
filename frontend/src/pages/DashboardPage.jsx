import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User,
  Compass,
  Calendar,
  MapPin,
  Clock,
  DollarSign,
  Route,
  Sparkles,
  ArrowRight,
  Bookmark,
  Trash2,
  Eye,
  FileText,
  Map as MapIcon,
  PlusCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTrip } from '../context/TripContext';
import { formatCurrency, formatDistanceKm, getCategoryBadgeColor } from '../utils/formatters';

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const {
    savedTrips,
    currentItinerary,
    savedPlaces,
    toggleSavePlace,
    setCurrentItinerary,
    updatePlan,
  } = useTrip();

  // Combine saved trips with current itinerary if not duplicate
  const allTrips = React.useMemo(() => {
    const list = [...savedTrips];
    if (currentItinerary && !list.some((t) => t.itinerary_id === currentItinerary.itinerary_id)) {
      list.unshift(currentItinerary);
    }
    return list;
  }, [savedTrips, currentItinerary]);

  const handleOpenItinerary = (trip) => {
    setCurrentItinerary(trip);
    navigate('/itinerary');
  };

  const handleOpenMap = (trip) => {
    setCurrentItinerary(trip);
    navigate('/map');
  };

  const handleQuickNewTrip = (destination = 'Hyderabad') => {
    updatePlan({ destination });
    navigate('/plan');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* --- Top Welcome Banner --- */}
      <div className="p-8 sm:p-10 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft-md relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2 relative z-10">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-[#18B8A6]/10 text-[#129889] text-xs font-bold border border-[#18B8A6]/20">
              Traveler Dashboard
            </span>
            <span className="text-xs text-[#829196]">•</span>
            <span className="text-xs text-[#52636A]">Account ID: #{user?.id || 'GUEST'}</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-[#163B46]">
            Welcome back, <span className="text-[#18B8A6]">{user?.full_name || 'Traveler'}</span>!
          </h1>
          <p className="text-xs sm:text-sm text-[#52636A] max-w-2xl leading-relaxed">
            Manage your personalized itineraries, explore context-aware POI recommendations, inspect road maps, and consult your LangGraph travel assistant.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 relative z-10">
          <button
            onClick={() => handleQuickNewTrip()}
            className="px-5 py-3 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs sm:text-sm shadow-soft transition-all hover:scale-[1.02] flex items-center space-x-2"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Plan New Trip</span>
          </button>
          <Link
            to="/assistant"
            className="px-4 py-3 rounded-xl bg-[#EEF3F1] hover:bg-white text-[#163B46] font-semibold text-xs sm:text-sm border border-[#DCE6E3] transition-all flex items-center space-x-2 shadow-soft"
          >
            <Sparkles className="w-4 h-4 text-[#18B8A6]" />
            <span>AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* --- Quick Metrics Cards --- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#52636A] text-xs mb-2">
            <span className="font-medium">Itineraries Planned</span>
            <Calendar className="w-4 h-4 text-[#18B8A6]" />
          </div>
          <p className="text-2xl font-black text-[#163B46]">{allTrips.length}</p>
          <span className="text-[11px] text-[#829196]">Saved in session & storage</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#52636A] text-xs mb-2">
            <span className="font-medium">Saved Attractions</span>
            <Bookmark className="w-4 h-4 text-[#18B8A6]" />
          </div>
          <p className="text-2xl font-black text-[#163B46]">{savedPlaces.length}</p>
          <span className="text-[11px] text-[#829196]">Bookmarked points of interest</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#52636A] text-xs mb-2">
            <span className="font-medium">Active Destination</span>
            <MapPin className="w-4 h-4 text-[#E6A23C]" />
          </div>
          <p className="text-2xl font-black text-[#163B46]">
            {currentItinerary?.destination || 'Hyderabad'}
          </p>
          <span className="text-[11px] text-[#829196]">Ready for optimization</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#52636A] text-xs mb-2">
            <span className="font-medium">AI Knowledge Engine</span>
            <Compass className="w-4 h-4 text-[#163B46]" />
          </div>
          <p className="text-2xl font-black text-[#18B8A6]">RAG Active</p>
          <span className="text-[11px] text-[#829196]">ChromaDB 384-D Vectorizer</span>
        </div>
      </div>

      {/* --- Recent Itineraries Section --- */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-[#163B46]">Recent & Saved Itineraries</h2>
            <p className="text-xs text-[#52636A]">
              Multi-day plans generated by the constraint scheduling and 2-Opt road optimizer.
            </p>
          </div>
          {allTrips.length > 0 && (
            <Link to="/itinerary" className="text-xs text-[#18B8A6] hover:underline font-semibold">
              View current schedule →
            </Link>
          )}
        </div>

        {allTrips.length === 0 ? (
          <div className="p-10 rounded-2xl bg-white border border-[#DCE6E3] text-center space-y-3 shadow-soft">
            <Compass className="w-10 h-10 text-[#829196] mx-auto" />
            <h3 className="text-base font-bold text-[#163B46]">No Itineraries Generated Yet</h3>
            <p className="text-xs text-[#52636A] max-w-md mx-auto">
              Ready to generate your first optimized multi-day travel schedule? Use our preference form or natural-language AI assistant.
            </p>
            <button
              onClick={() => handleQuickNewTrip('Hyderabad')}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs shadow-soft transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Generate Hyderabad Plan</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {allTrips.map((trip, idx) => (
              <div
                key={trip.itinerary_id || idx}
                className="p-6 rounded-2xl bg-white border border-[#DCE6E3] hover:border-[#18B8A6] shadow-soft hover:shadow-soft-md transition-all flex flex-col justify-between space-y-4 group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-[#18B8A6] uppercase tracking-wider flex items-center">
                      <MapPin className="w-3.5 h-3.5 mr-1" />
                      {trip.destination}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        trip.feasibility_status === 'feasible'
                          ? 'bg-emerald-50 text-[#16A36A] border-emerald-200'
                          : 'bg-amber-50 text-[#E6A23C] border-amber-200'
                      }`}
                    >
                      {trip.feasibility_status || 'Feasible'}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-[#163B46] mb-1 group-hover:text-[#18B8A6] transition-colors">
                    {trip.total_days}-Day {trip.destination} Exploration
                  </h3>
                  <p className="text-xs text-[#52636A]">
                    {trip.start_date} → {trip.end_date} ({trip.travelers_count} traveler{trip.travelers_count > 1 ? 's' : ''})
                  </p>

                  <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-[#DCE6E3] text-xs">
                    <div>
                      <span className="text-[10px] text-[#829196] font-medium">Est. Budget</span>
                      <p className="font-bold text-[#16A36A]">
                        {formatCurrency(trip.budget_summary?.estimated_total_cost || 0)}
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#829196] font-medium">Road Distance</span>
                      <p className="font-bold text-[#163B46]">
                        {formatDistanceKm(trip.total_distance_km || 0)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-[#DCE6E3] flex items-center justify-between gap-2">
                  <button
                    onClick={() => handleOpenItinerary(trip)}
                    className="flex-1 py-2 px-3 rounded-xl bg-[#EEF3F1] hover:bg-[#18B8A6] hover:text-white text-[#163B46] text-xs font-semibold flex items-center justify-center space-x-1 transition-all"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Itinerary</span>
                  </button>
                  <button
                    onClick={() => handleOpenMap(trip)}
                    className="py-2 px-3 rounded-xl bg-white hover:bg-[#EEF3F1] text-[#18B8A6] border border-[#DCE6E3] text-xs font-semibold transition-colors shadow-soft"
                    title="View on Map"
                  >
                    <MapIcon className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      setCurrentItinerary(trip);
                      navigate('/reports');
                    }}
                    className="py-2 px-3 rounded-xl bg-white hover:bg-[#EEF3F1] text-[#163B46] border border-[#DCE6E3] text-xs font-semibold transition-colors shadow-soft"
                    title="Export PDF Report"
                  >
                    <FileText className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* --- Saved Attractions Section --- */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-[#163B46]">Bookmarked Points of Interest</h2>
            <p className="text-xs text-[#52636A]">
              Attractions saved for inclusion in upcoming itineraries.
            </p>
          </div>
          {savedPlaces.length > 0 && (
            <Link to="/recommendations" className="text-xs text-[#18B8A6] hover:underline font-semibold">
              Discover more attractions →
            </Link>
          )}
        </div>

        {savedPlaces.length === 0 ? (
          <div className="p-8 rounded-2xl bg-white border border-[#DCE6E3] text-center text-xs text-[#829196] shadow-soft">
            No attractions bookmarked yet. When browsing recommendations, click the bookmark icon to save them here.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {savedPlaces.map((place) => (
              <div
                key={place.place_id || place.id}
                className="p-5 rounded-2xl bg-white border border-[#DCE6E3] hover:border-[#18B8A6] shadow-soft transition-all flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getCategoryBadgeColor(place.category)}`}>
                      {place.category || 'Sight'}
                    </span>
                    <button
                      onClick={() => toggleSavePlace(place)}
                      title="Remove bookmark"
                      className="text-[#829196] hover:text-[#DC5555] p-1 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <h4 className="text-sm font-bold text-[#163B46] line-clamp-1">{place.name}</h4>
                  <p className="text-[11px] text-[#52636A] line-clamp-2 mt-1">
                    {place.address || 'Address provided upon itinerary generation'}
                  </p>
                </div>

                <div className="pt-2 border-t border-[#DCE6E3] flex items-center justify-between text-[11px]">
                  <span className="text-[#52636A]">
                    Admission:{' '}
                    <strong className="text-[#16A36A]">
                      {place.entrance_fee > 0 ? formatCurrency(place.entrance_fee) : 'Free / TBA'}
                    </strong>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
