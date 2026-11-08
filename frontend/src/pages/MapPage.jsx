import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPin,
  Calendar,
  Route,
  Clock,
  Compass,
  ArrowRight,
  Sparkles,
  Layers,
  Utensils,
  Navigation,
} from 'lucide-react';
import { useTrip } from '../context/TripContext';
import MapComponent from '../components/MapComponent';
import { formatCurrency, formatDistanceKm, getCategoryBadgeColor } from '../utils/formatters';

export default function MapPage() {
  const navigate = useNavigate();
  const { currentItinerary, recommendations, tripPlan } = useTrip();

  const [activeDayFilter, setActiveDayFilter] = useState('all');

  const destinationName = currentItinerary?.destination || tripPlan.destination || 'Hyderabad';

  // Gather stops from active day or all days
  const activeStops = React.useMemo(() => {
    if (!currentItinerary || !currentItinerary.days) return [];

    const stops = [];
    currentItinerary.days.forEach((day) => {
      if (activeDayFilter === 'all' || String(day.day_number) === activeDayFilter) {
        (day.stops || []).forEach((stop) => {
          if (!stop.is_start_location && !stop.is_end_location) {
            stops.push({
              ...stop,
              dayNumber: day.day_number,
            });
          }
        });
      }
    });
    return stops;
  }, [currentItinerary, activeDayFilter]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="px-3 py-1 rounded-full bg-[#18B8A6]/10 text-[#129889] text-xs font-bold border border-[#18B8A6]/20">
              OpenStreetMap + Leaflet
            </span>
            <span className="text-xs text-[#829196]">•</span>
            <span className="text-xs font-semibold text-[#52636A]">OpenRouteService Polylines</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#163B46] tracking-tight">
            Interactive Route Map & Sequences — {destinationName}
          </h1>
          <p className="text-xs sm:text-sm text-[#52636A] mt-1">
            Visualize day-wise visiting sequences, restaurant stops, and 2-Opt road route polylines.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => navigate('/itinerary')}
            className="px-4 py-2.5 rounded-xl bg-white border border-[#DCE6E3] text-xs font-semibold text-[#26383D] hover:bg-[#EEF3F1] shadow-sm transition-colors"
          >
            Itinerary Schedule
          </button>
          <button
            onClick={() => navigate('/plan')}
            className="px-5 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white text-xs font-bold shadow-soft transition-colors"
          >
            Adjust Plan
          </button>
        </div>
      </div>

      {/* Main Map & Side Sequence Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left / Center: The Leaflet Map Component */}
        <div className="lg:col-span-2 space-y-4">
          <MapComponent
            itinerary={currentItinerary}
            standalonePlaces={!currentItinerary ? recommendations : []}
            height="620px"
          />

          {/* Quick Map Legend */}
          <div className="p-4 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft flex flex-wrap items-center justify-between text-xs text-[#52636A] gap-3">
            <div className="flex items-center space-x-5">
              <span className="flex items-center space-x-1.5">
                <span className="w-4 h-4 rounded-full bg-[#18B8A6] flex items-center justify-center text-[10px] font-bold text-white shadow-xs">
                  1
                </span>
                <span className="font-medium text-[#26383D]">Visiting Sequence</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-4 h-4 rounded-full bg-emerald-100 border border-emerald-300 flex items-center justify-center text-[10px] text-emerald-800">
                  🍽️
                </span>
                <span className="font-medium text-[#26383D]">Meal Break</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-5 h-1.5 rounded-full bg-[#18B8A6]" />
                <span className="font-medium text-[#26383D]">Road Polyline</span>
              </span>
            </div>
            <span className="text-[11px] text-[#829196]">
              Click any marker to inspect arrival times & entrance fees.
            </span>
          </div>
        </div>

        {/* Right: Sequential Itinerary Stops List */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft flex flex-col justify-between space-y-4 max-h-[690px] overflow-hidden">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <Route className="w-4 h-4 text-[#18B8A6]" />
                <span>Visiting Stops Sequence</span>
              </h3>
              <span className="text-xs text-[#18B8A6] font-bold bg-[#18B8A6]/10 px-2.5 py-0.5 rounded-full border border-[#18B8A6]/20">
                {activeStops.length} Place{activeStops.length > 1 ? 's' : ''}
              </span>
            </div>

            {/* Stops Scrollable Container */}
            <div className="space-y-3 overflow-y-auto max-h-[520px] pr-1">
              {activeStops.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#829196] space-y-3">
                  <p>No itinerary loaded yet.</p>
                  <button
                    onClick={() => navigate('/plan')}
                    className="px-4 py-2 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white text-xs font-bold shadow-soft transition-colors"
                  >
                    Generate Plan
                  </button>
                </div>
              ) : (
                activeStops.map((stop, index) => (
                  <div
                    key={stop.place_id || index}
                    className="p-3.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] hover:border-[#829196]/40 transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="w-5 h-5 rounded-full bg-[#18B8A6] text-white text-[11px] font-extrabold flex items-center justify-center shadow-xs">
                          {stop.stop_order || index + 1}
                        </span>
                        <h4 className="text-xs font-bold text-[#163B46] line-clamp-1">{stop.name}</h4>
                      </div>
                      <span className="text-[10px] font-semibold text-[#829196]">Day {stop.dayNumber}</span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-[#52636A] pt-1">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5 text-amber-600" />
                        <span>{stop.arrival_time} - {stop.departure_time}</span>
                      </span>
                      <span className="font-semibold text-[#16A36A]">
                        {stop.total_entrance_fee > 0 ? formatCurrency(stop.total_entrance_fee) : 'Free'}
                      </span>
                    </div>

                    {stop.travel_distance_km > 0 && (
                      <div className="text-[10px] text-[#829196] flex items-center space-x-1 pt-0.5">
                        <Navigation className="w-3 h-3 text-[#18B8A6]" />
                        <span>Transit leg: {formatDistanceKm(stop.travel_distance_km)}</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
