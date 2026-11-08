import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Utensils, Clock, DollarSign, Navigation, Calendar } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';

// Map Auto-Fitter Helper Component
function ChangeView({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      try {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
      } catch (e) {
        console.warn('Map fitBounds error:', e);
      }
    }
  }, [bounds, map]);
  return null;
}

// Custom HTML DivIcons with sequence numbers and styling
const createNumberIcon = (number, color = '#18B8A6') => {
  return L.divIcon({
    className: 'custom-map-marker',
    html: `
      <div style="
        background-color: ${color};
        color: #ffffff;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 13px;
        box-shadow: 0 4px 14px rgba(22, 59, 70, 0.25);
        border: 2.5px solid #ffffff;
      ">
        ${number}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
};

const createRestaurantIcon = () => {
  return L.divIcon({
    className: 'custom-map-marker-restaurant',
    html: `
      <div style="
        background-color: #16A36A;
        color: #ffffff;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        box-shadow: 0 4px 10px rgba(22, 59, 70, 0.2);
        border: 2.5px solid #ffffff;
      ">
        🍽️
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
};

const DAY_COLORS = ['#18B8A6', '#163B46', '#244F59', '#16A36A', '#E6A23C', '#0284C7'];

export default function MapComponent({
  itinerary,
  standalonePlaces = [],
  center = [17.3850, 78.4867],
  zoom = 12,
  height = '500px',
  selectedDay = null, // null means all days
}) {
  const [activeDayFilter, setActiveDayFilter] = useState(selectedDay || 'all');

  // Parse stops from itinerary days
  const { allStops, mealBreaks, dayPolylines } = useMemo(() => {
    if (!itinerary || !itinerary.days) {
      return { allStops: [], mealBreaks: [], dayPolylines: [] };
    }

    const stopsList = [];
    const mealsList = [];
    const polylinesList = [];

    itinerary.days.forEach((day, dayIndex) => {
      const color = DAY_COLORS[dayIndex % DAY_COLORS.length];
      const dayCoordinates = [];

      // Process stops
      (day.stops || []).forEach((stop) => {
        if (!stop.is_start_location && !stop.is_end_location && stop.latitude && stop.longitude) {
          stopsList.push({
            ...stop,
            dayNumber: day.day_number,
            color,
          });
          dayCoordinates.push([stop.latitude, stop.longitude]);
        }
      });

      // Process meal breaks if coordinates exist
      (day.meal_breaks || []).forEach((meal) => {
        if (meal.latitude && meal.longitude) {
          mealsList.push({
            ...meal,
            dayNumber: day.day_number,
          });
        }
      });

      // Process route geometry string if returned by backend
      let polylinePoints = [];
      if (day.geometry && Array.isArray(day.geometry) && day.geometry.length > 0) {
        day.geometry.forEach((item) => {
          if (typeof item === 'string') {
            const parts = item.trim().split(/\s+/);
            for (let i = 0; i < parts.length - 1; i += 2) {
              const lat = parseFloat(parts[i]);
              const lon = parseFloat(parts[i + 1]);
              if (!isNaN(lat) && !isNaN(lon)) {
                polylinePoints.push([lat, lon]);
              }
            }
          }
        });
      }

      // If backend geometry was straight point-to-point, fallback to stop coordinates
      if (polylinePoints.length < 2) {
        polylinePoints = dayCoordinates;
      }

      if (polylinePoints.length >= 2) {
        polylinesList.push({
          dayNumber: day.day_number,
          points: polylinePoints,
          color,
        });
      }
    });

    return { allStops: stopsList, mealBreaks: mealsList, dayPolylines: polylinesList };
  }, [itinerary]);

  // Filter stops and polylines based on active day filter
  const visibleStops = useMemo(() => {
    if (activeDayFilter === 'all') return allStops;
    return allStops.filter((s) => s.dayNumber === parseInt(activeDayFilter, 10));
  }, [allStops, activeDayFilter]);

  const visiblePolylines = useMemo(() => {
    if (activeDayFilter === 'all') return dayPolylines;
    return dayPolylines.filter((p) => p.dayNumber === parseInt(activeDayFilter, 10));
  }, [dayPolylines, activeDayFilter]);

  const visibleMeals = useMemo(() => {
    if (activeDayFilter === 'all') return mealBreaks;
    return mealBreaks.filter((m) => m.dayNumber === parseInt(activeDayFilter, 10));
  }, [mealBreaks, activeDayFilter]);

  // Compute bounding box for visible elements
  const mapBounds = useMemo(() => {
    const points = [];
    visibleStops.forEach((s) => points.push([s.latitude, s.longitude]));
    visibleMeals.forEach((m) => points.push([m.latitude, m.longitude]));
    standalonePlaces.forEach((p) => {
      if (p.latitude && p.longitude) points.push([p.latitude, p.longitude]);
    });
    return points.length > 0 ? points : null;
  }, [visibleStops, visibleMeals, standalonePlaces]);

  // Resolved Center
  const resolvedCenter = useMemo(() => {
    if (visibleStops.length > 0) {
      return [visibleStops[0].latitude, visibleStops[0].longitude];
    }
    if (standalonePlaces.length > 0) {
      return [standalonePlaces[0].latitude, standalonePlaces[0].longitude];
    }
    return center;
  }, [visibleStops, standalonePlaces, center]);

  return (
    <div className="relative rounded-2xl overflow-hidden border border-[#DCE6E3] shadow-soft-md bg-white flex flex-col">
      {/* Top Filter Controls (If Itinerary is present) */}
      {itinerary?.days && itinerary.days.length > 1 && (
        <div className="bg-white px-4 py-2.5 border-b border-[#DCE6E3] flex flex-wrap items-center justify-between gap-3 text-xs z-20">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[#52636A] font-medium flex items-center mr-1">
              <Calendar className="w-3.5 h-3.5 mr-1 text-[#18B8A6]" />
              Filter Day:
            </span>
            <button
              onClick={() => setActiveDayFilter('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                activeDayFilter === 'all'
                  ? 'bg-[#18B8A6] text-white shadow-soft'
                  : 'bg-[#F4F7F6] text-[#52636A] hover:bg-[#EEF3F1] hover:text-[#163B46]'
              }`}
            >
              All Days ({allStops.length} stops)
            </button>
            {itinerary.days.map((day, idx) => (
              <button
                key={day.day_number}
                onClick={() => setActiveDayFilter(String(day.day_number))}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                  activeDayFilter === String(day.day_number)
                    ? 'bg-[#163B46] text-white shadow-soft'
                    : 'bg-[#F4F7F6] text-[#52636A] hover:bg-[#EEF3F1] hover:text-[#163B46]'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: DAY_COLORS[idx % DAY_COLORS.length] }}
                />
                <span>Day {day.day_number}</span>
              </button>
            ))}
          </div>

          <div className="hidden sm:flex items-center space-x-3 text-[11px] text-[#52636A] font-medium">
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 rounded-full bg-[#18B8A6] mr-1.5" /> Attraction
            </span>
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 rounded-full bg-[#16A36A] mr-1.5" /> Dining
            </span>
            <span className="flex items-center">
              <span className="w-4 h-0.5 bg-[#18B8A6] mr-1.5" /> Route Polyline
            </span>
          </div>
        </div>
      )}

      {/* Map Container */}
      <div style={{ height }} className="w-full relative z-10">
        <MapContainer
          center={resolvedCenter}
          zoom={zoom}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%' }}
        >
          <ChangeView bounds={mapBounds} />

          {/* OpenStreetMap CartoDB Voyager Light tiles */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            maxZoom={19}
          />

          {/* Route Polylines */}
          {visiblePolylines.map((poly, idx) => (
            <Polyline
              key={`polyline-day-${poly.dayNumber}-${idx}`}
              positions={poly.points}
              pathOptions={{
                color: poly.color,
                weight: 4,
                opacity: 0.85,
                dashArray: '3, 6',
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
          ))}

          {/* Sequential Itinerary Stops */}
          {visibleStops.map((stop, index) => (
            <Marker
              key={`stop-${stop.place_id || stop.id || index}`}
              position={[stop.latitude, stop.longitude]}
              icon={createNumberIcon(stop.stop_order || index + 1, stop.color)}
            >
              <Popup>
                <div className="space-y-2 p-1 text-[#26383D] min-w-[210px]">
                  <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#18B8A6]">
                      Day {stop.dayNumber} • Stop #{stop.stop_order || index + 1}
                    </span>
                    <span className="text-[10px] text-[#52636A] capitalize">{stop.category || 'Sight'}</span>
                  </div>

                  <h4 className="text-sm font-bold text-[#163B46] leading-tight">{stop.name}</h4>

                  {stop.address && (
                    <p className="text-[11px] text-[#52636A] line-clamp-2">{stop.address}</p>
                  )}

                  <div className="grid grid-cols-2 gap-1.5 pt-1 text-[11px] text-[#26383D]">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-[#E6A23C]" />
                      <span>{stop.arrival_time} - {stop.departure_time}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <DollarSign className="w-3 h-3 text-[#16A36A]" />
                      <span>{stop.total_entrance_fee > 0 ? formatCurrency(stop.total_entrance_fee) : 'Free'}</span>
                    </div>
                  </div>

                  <div className="pt-2 text-center border-t border-[#DCE6E3]">
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${stop.latitude},${stop.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-[11px] text-[#18B8A6] hover:text-[#129889] font-semibold"
                    >
                      <Navigation className="w-3 h-3" />
                      <span>Open in Google Maps</span>
                    </a>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Scheduled Meal Stops */}
          {visibleMeals.map((meal, idx) => (
            <Marker
              key={`meal-${meal.id || idx}`}
              position={[meal.latitude, meal.longitude]}
              icon={createRestaurantIcon()}
            >
              <Popup>
                <div className="space-y-1 text-[#26383D] min-w-[180px]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#16A36A]">
                    Day {meal.dayNumber} • Dining Break
                  </span>
                  <h4 className="text-xs font-bold text-[#163B46]">{meal.name}</h4>
                  <p className="text-[11px] text-[#52636A]">
                    {meal.scheduled_start} - {meal.scheduled_end} ({meal.duration_mins} mins)
                  </p>
                  <p className="text-[11px] text-[#16A36A] font-semibold">
                    Budget Est: {formatCurrency(meal.estimated_cost || 0)}
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Standalone POIs (e.g. from Recommendations view) */}
          {standalonePlaces.map((poi, idx) => (
            <Marker
              key={`place-${poi.place_id || poi.id || idx}`}
              position={[poi.latitude, poi.longitude]}
              icon={createNumberIcon(idx + 1, '#18B8A6')}
            >
              <Popup>
                <div className="space-y-1.5 text-[#26383D] min-w-[200px]">
                  <span className="text-[10px] font-bold uppercase text-[#18B8A6]">
                    Recommended Attraction #{idx + 1}
                  </span>
                  <h4 className="text-xs font-bold text-[#163B46]">{poi.name}</h4>
                  <p className="text-[11px] text-[#52636A]">{poi.address || poi.category}</p>
                  {poi.final_score && (
                    <div className="text-[11px] text-[#18B8A6] font-semibold">
                      Score: {(poi.final_score * 100).toFixed(0)}% Match
                    </div>
                  )}
                  {poi.entrance_fee !== undefined && (
                    <div className="text-[11px] text-[#16A36A] font-medium">
                      Admission: {poi.entrance_fee > 0 ? formatCurrency(poi.entrance_fee) : 'Free / Included'}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
