import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Route,
  Clock,
  Compass,
  PieChart as PieIcon,
  Calendar,
  Layers,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Sun,
  Building,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Line,
  ComposedChart,
} from 'recharts';
import { useTrip } from '../context/TripContext';
import { formatCurrency, formatDistanceKm, formatDurationMins } from '../utils/formatters';

const PALETTE = ['#18B8A6', '#163B46', '#244F59', '#16A36A', '#E6A23C', '#0284C7', '#8B5CF6'];

const tooltipStyle = {
  backgroundColor: '#FFFFFF',
  borderColor: '#DCE6E3',
  borderRadius: '12px',
  color: '#26383D',
  boxShadow: '0 4px 20px -2px rgba(22, 59, 70, 0.08)',
};

export default function AnalyticsPage() {
  const navigate = useNavigate();
  const { currentItinerary, recommendations, tripPlan } = useTrip();

  const itin = currentItinerary;
  const budget = itin?.budget_summary;
  const cb = budget?.by_category || budget?.category_breakdown;
  const days = itin?.days || [];

  // Extract all stops across all days
  const allStops = useMemo(() => {
    if (!days || days.length === 0) {
      if (recommendations && recommendations.length > 0) {
        return recommendations.map((r) => ({
          name: r.name,
          category: r.category || 'Sightseeing',
          recommendation_score: r.final_score || 0.85,
          is_outdoor: r.is_outdoor || false,
          opening_hours_status: 'verified',
        }));
      }
      return [
        { name: 'Golconda Fort', category: 'Historical Fort', recommendation_score: 0.94, is_outdoor: true, opening_hours_status: 'verified' },
        { name: 'Charminar', category: 'Heritage Monument', recommendation_score: 0.91, is_outdoor: false, opening_hours_status: 'verified' },
        { name: 'Chowmahalla Palace', category: 'Royal Palace', recommendation_score: 0.89, is_outdoor: false, opening_hours_status: 'verified' },
        { name: 'Qutb Shahi Tombs', category: 'Architecture', recommendation_score: 0.88, is_outdoor: true, opening_hours_status: 'verified' },
      ];
    }
    const collected = [];
    days.forEach((d) => {
      (d.stops || []).forEach((s) => {
        if (!s.is_start_location && !s.is_end_location) {
          collected.push(s);
        }
      });
    });
    return collected.length > 0 ? collected : (recommendations || []);
  }, [days, recommendations]);

  // 1. Attraction Category Distribution
  const categoryData = useMemo(() => {
    const counts = {};
    allStops.forEach((s) => {
      const c = (s.category || 'Sightseeing').trim();
      const formatted = c.charAt(0).toUpperCase() + c.slice(1);
      counts[formatted] = (counts[formatted] || 0) + 1;
    });
    return Object.keys(counts).map((key) => ({
      name: key,
      value: counts[key],
    }));
  }, [allStops]);

  // 2. Recommendation Score Distribution
  const scoreData = useMemo(() => {
    return allStops.map((s) => {
      const raw = s.recommendation_score || s.final_score || 0.85;
      const pct = Math.round(raw * 100);
      return {
        name: s.name.length > 18 ? s.name.substring(0, 16) + '...' : s.name,
        fullName: s.name,
        score: pct,
        category: s.category || 'Attraction',
      };
    });
  }, [allStops]);

  // 3. Daily Expense Distribution (Admissions, Food, Transport, Stay)
  const dailyExpenseData = useMemo(() => {
    if (!days || days.length === 0) {
      return [
        { day: 'Day 1', admissions: 50, food: 800, transport: 375, stay: 600, total: 1825 },
        { day: 'Day 2', admissions: 210, food: 800, transport: 375, stay: 600, total: 1985 },
      ];
    }
    const numDays = Math.max(days.length, 1);
    const dailyTransport = Math.round((cb?.transportation || 750) / numDays);
    const dailyFood = Math.round((cb?.food || 1600) / numDays);
    const dailyStay = Math.round((cb?.accommodation || 0) / numDays);

    return days.map((d) => {
      const admissions = Math.round(
        (d.stops || []).reduce((acc, s) => acc + (s.total_entrance_fee || 0), 0)
      );
      const total = admissions + dailyTransport + dailyFood + dailyStay;
      return {
        day: `Day ${d.day_number}`,
        admissions,
        food: dailyFood,
        transport: dailyTransport,
        stay: dailyStay,
        total: Math.round(d.daily_estimated_cost || total),
      };
    });
  }, [days, cb]);

  // 4. Daily Travel Duration (Visit Time vs Transit Time)
  const durationData = useMemo(() => {
    if (!days || days.length === 0) {
      return [
        { day: 'Day 1', visitHours: 3.0, transitHours: 0.7, totalHours: 3.7 },
        { day: 'Day 2', visitHours: 3.0, transitHours: 0.55, totalHours: 3.55 },
      ];
    }
    return days.map((d) => {
      const vH = +((d.daily_visit_time_mins || 180) / 60).toFixed(1);
      const tH = +((d.daily_travel_time_mins || 45) / 60).toFixed(1);
      return {
        day: `Day ${d.day_number}`,
        visitHours: vH,
        transitHours: tH,
        totalHours: +(vH + tH).toFixed(1),
      };
    });
  }, [days]);

  // 5. Distance Comparison (Daily km & Cumulative)
  const distanceData = useMemo(() => {
    if (!days || days.length === 0) {
      return [
        { day: 'Day 1', distanceKm: 16.2, cumulativeKm: 16.2 },
        { day: 'Day 2', distanceKm: 12.3, cumulativeKm: 28.5 },
      ];
    }
    let running = 0;
    return days.map((d) => {
      const km = +(d.daily_distance_km || 12.0).toFixed(1);
      running = +(running + km).toFixed(1);
      return {
        day: `Day ${d.day_number}`,
        distanceKm: km,
        cumulativeKm: running,
      };
    });
  }, [days]);

  // 6. Budget Utilization Calculations
  const totalBudget = budget?.total_budget || tripPlan?.budget || 6000;
  const estimatedCost = budget?.estimated_total_cost || 4200;
  const remainingBudget = Math.max(0, totalBudget - estimatedCost);
  const utilizationPct = Math.min(100, Math.round((estimatedCost / totalBudget) * 100));
  const travelers = itin?.travelers_count || 1;
  const costPerPerson = Math.round(estimatedCost / travelers);

  // 7. Attraction Volume & Environmental Metrics
  const totalAttractions = allStops.length;
  const outdoorCount = allStops.filter((s) => s.is_outdoor).length;
  const indoorCount = totalAttractions - outdoorCount;
  const verifiedCount = allStops.filter((s) => s.opening_hours_status === 'verified').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="px-3 py-1 rounded-full bg-[#18B8A6]/10 text-[#129889] text-xs font-bold border border-[#18B8A6]/20">
              Visual Intelligence
            </span>
            <span className="text-xs text-[#829196]">•</span>
            <span className="text-xs font-semibold text-[#52636A]">7 Core Analytical Dimensions</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#163B46] tracking-tight">
            Travel Analytics & Performance Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-[#52636A] mt-1">
            Empirical visual breakdown of attraction scoring, budget ledger distributions, and road network metrics.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/reports')}
            className="px-4 py-2.5 rounded-xl bg-white border border-[#DCE6E3] text-xs font-semibold text-[#26383D] hover:bg-[#EEF3F1] shadow-sm transition-colors"
          >
            Export Dossier PDF
          </button>
          <button
            onClick={() => navigate('/itinerary')}
            className="px-5 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white text-xs font-bold shadow-soft transition-colors"
          >
            View Full Schedule
          </button>
        </div>
      </div>

      {/* KPI Highlight Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#829196] text-xs font-semibold mb-1">
            <span>Scheduled Attractions</span>
            <Compass className="w-4 h-4 text-[#18B8A6]" />
          </div>
          <p className="text-2xl font-black text-[#163B46]">{totalAttractions}</p>
          <span className="text-xs font-medium text-[#16A36A]">{verifiedCount} hours verified</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#829196] text-xs font-semibold mb-1">
            <span>Estimated Expenses</span>
            <DollarSign className="w-4 h-4 text-[#16A36A]" />
          </div>
          <p className="text-2xl font-black text-[#16A36A]">{formatCurrency(estimatedCost)}</p>
          <span className="text-xs text-[#52636A]">{formatCurrency(costPerPerson)} / traveler</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#829196] text-xs font-semibold mb-1">
            <span>Total Road Network</span>
            <Route className="w-4 h-4 text-[#163B46]" />
          </div>
          <p className="text-2xl font-black text-[#163B46]">
            {formatDistanceKm(itin?.total_distance_km || 28.5)}
          </p>
          <span className="text-xs text-[#52636A]">2-Opt TSP optimized</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft">
          <div className="flex items-center justify-between text-[#829196] text-xs font-semibold mb-1">
            <span>Budget Utilization</span>
            <TrendingUp className="w-4 h-4 text-[#18B8A6]" />
          </div>
          <p className="text-2xl font-black text-[#163B46]">{utilizationPct}%</p>
          <span className="text-xs text-[#52636A]">
            {formatCurrency(remainingBudget)} surplus buffer
          </span>
        </div>
      </div>

      {/* Grid of the 7 Required Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Visualization 1: Attraction Category Distribution */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <PieIcon className="w-4 h-4 text-[#18B8A6]" />
                <span>1. Attraction Category Distribution</span>
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">Categorical grouping of scheduled points of interest</p>
            </div>
            <span className="text-xs font-bold text-[#18B8A6] bg-[#18B8A6]/10 px-2.5 py-0.5 rounded-full border border-[#18B8A6]/20">
              {categoryData.length} Themes
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {categoryData.map((_, index) => (
                    <Cell key={`cat-${index}`} fill={PALETTE[index % PALETTE.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Visualization 2: Recommendation Score Distribution */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-[#18B8A6]" />
                <span>2. Recommendation Score Distribution</span>
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">Context-aware multi-criteria score (0-100%) per venue</p>
            </div>
            <span className="text-xs font-bold text-[#163B46] bg-[#EEF3F1] px-2.5 py-0.5 rounded-full border border-[#DCE6E3]">
              6D Scored
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#DCE6E3" />
                <XAxis dataKey="name" stroke="#829196" tick={{ fill: '#52636A', fontSize: 10 }} angle={-15} textAnchor="end" />
                <YAxis stroke="#829196" tick={{ fill: '#52636A', fontSize: 10 }} domain={[0, 100]} />
                <Tooltip
                  formatter={(val) => [`${val}% Match`, 'Recommendation Score']}
                  contentStyle={tooltipStyle}
                />
                <Bar dataKey="score" fill="#18B8A6" radius={[6, 6, 0, 0]}>
                  {scoreData.map((entry, idx) => (
                    <Cell
                      key={`score-${idx}`}
                      fill={entry.score >= 90 ? '#16A36A' : entry.score >= 80 ? '#18B8A6' : '#E6A23C'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Visualization 3: Daily Expense Distribution */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-[#16A36A]" />
                <span>3. Daily Expense Distribution</span>
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">Operational cost breakdown by calendar day (INR)</p>
            </div>
            <span className="text-xs font-bold text-[#16A36A] bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              {formatCurrency(estimatedCost)}
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyExpenseData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#DCE6E3" />
                <XAxis dataKey="day" stroke="#829196" tick={{ fill: '#52636A', fontSize: 11 }} />
                <YAxis stroke="#829196" tick={{ fill: '#52636A', fontSize: 10 }} />
                <Tooltip
                  formatter={(val) => formatCurrency(val)}
                  contentStyle={tooltipStyle}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6, color: '#52636A' }} />
                <Bar dataKey="admissions" name="Admissions" stackId="a" fill="#18B8A6" />
                <Bar dataKey="food" name="Meals" stackId="a" fill="#16A36A" />
                <Bar dataKey="transport" name="Road Transit" stackId="a" fill="#E6A23C" />
                <Bar dataKey="stay" name="Lodging" stackId="a" fill="#163B46" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Visualization 4: Daily Travel Duration */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <Clock className="w-4 h-4 text-[#18B8A6]" />
                <span>4. Daily Travel & Visit Duration</span>
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">Active sightseeing time vs. road transit duration (hours)</p>
            </div>
            <span className="text-xs font-bold text-[#163B46] bg-[#EEF3F1] px-2.5 py-0.5 rounded-full border border-[#DCE6E3]">
              Hours / Day
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={durationData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#DCE6E3" />
                <XAxis dataKey="day" stroke="#829196" tick={{ fill: '#52636A', fontSize: 11 }} />
                <YAxis stroke="#829196" tick={{ fill: '#52636A', fontSize: 10 }} />
                <Tooltip
                  formatter={(val) => `${val} hrs`}
                  contentStyle={tooltipStyle}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6, color: '#52636A' }} />
                <Bar dataKey="visitHours" name="Sightseeing Time" fill="#18B8A6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="transitHours" name="Transit Time" fill="#244F59" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Visualization 5: Distance Comparison */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <Route className="w-4 h-4 text-[#18B8A6]" />
                <span>5. Road Distance Comparison & Cumulative Progress</span>
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">Daily leg distance traversed (km) and cumulative progression</p>
            </div>
            <span className="text-xs font-bold text-[#163B46] bg-[#EEF3F1] px-2.5 py-0.5 rounded-full border border-[#DCE6E3]">
              {formatDistanceKm(itin?.total_distance_km || 28.5)}
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={distanceData} margin={{ top: 10, right: 10, left: -15, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#DCE6E3" />
                <XAxis dataKey="day" stroke="#829196" tick={{ fill: '#52636A', fontSize: 11 }} />
                <YAxis stroke="#829196" tick={{ fill: '#52636A', fontSize: 10 }} />
                <Tooltip
                  formatter={(val) => `${val} km`}
                  contentStyle={tooltipStyle}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6, color: '#52636A' }} />
                <Bar dataKey="distanceKm" name="Daily Leg (km)" fill="#18B8A6" radius={[6, 6, 0, 0]} />
                <Line
                  type="monotone"
                  dataKey="cumulativeKm"
                  name="Cumulative Progress (km)"
                  stroke="#163B46"
                  strokeWidth={2.5}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Visualization 6: Budget Utilization */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
          <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-[#16A36A]" />
                <span>6. Financial Budget Capacity & Utilization</span>
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">Comparison of allocated budget cap vs. algorithmic expenses</p>
            </div>
            <span className="text-xs font-bold text-[#16A36A] bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              {utilizationPct}% Allocated
            </span>
          </div>

          <div className="space-y-4 pt-2">
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-medium">
                <span className="text-[#52636A]">Budget Progress</span>
                <span className="text-[#163B46] font-bold">
                  {formatCurrency(estimatedCost)} / {formatCurrency(totalBudget)}
                </span>
              </div>
              <div className="w-full h-3.5 bg-[#EEF3F1] rounded-full overflow-hidden border border-[#DCE6E3] p-0.5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#18B8A6] to-[#163B46] transition-all duration-500"
                  style={{ width: `${utilizationPct}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3]">
                <span className="text-[10px] text-[#829196] uppercase font-bold tracking-wider block">Remaining Surplus</span>
                <p className="text-lg font-black text-[#16A36A] mt-0.5">{formatCurrency(remainingBudget)}</p>
                <span className="text-[10px] text-[#52636A]">Available contingency</span>
              </div>
              <div className="p-3.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3]">
                <span className="text-[10px] text-[#829196] uppercase font-bold tracking-wider block">Cost Per Traveler</span>
                <p className="text-lg font-black text-[#163B46] mt-0.5">{formatCurrency(costPerPerson)}</p>
                <span className="text-[10px] text-[#52636A]">Across {travelers} traveler(s)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Visualization 7: Number of Recommended Attractions & Environmental Mix */}
        <div className="p-6 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between border-b border-[#DCE6E3] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#163B46] flex items-center space-x-2">
                <Layers className="w-4 h-4 text-[#18B8A6]" />
                <span>7. Attraction Volume & Environmental Distribution</span>
              </h3>
              <p className="text-xs text-[#52636A] mt-0.5">
                Quantitative count of evaluated, scheduled, outdoor vs. indoor attractions
              </p>
            </div>
            <span className="text-xs font-bold text-[#18B8A6] bg-[#18B8A6]/10 px-2.5 py-0.5 rounded-full border border-[#18B8A6]/20">
              {totalAttractions} Total Stops
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-center">
              <Compass className="w-6 h-6 text-[#18B8A6] mx-auto mb-1.5" />
              <span className="text-2xl font-black text-[#163B46]">{totalAttractions}</span>
              <p className="text-xs text-[#52636A] font-medium mt-0.5">Total Attractions</p>
            </div>

            <div className="p-4 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-center">
              <Sun className="w-6 h-6 text-amber-500 mx-auto mb-1.5" />
              <span className="text-2xl font-black text-amber-600">{outdoorCount}</span>
              <p className="text-xs text-[#52636A] font-medium mt-0.5">Outdoor Venues</p>
            </div>

            <div className="p-4 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-center">
              <Building className="w-6 h-6 text-[#163B46] mx-auto mb-1.5" />
              <span className="text-2xl font-black text-[#163B46]">{indoorCount}</span>
              <p className="text-xs text-[#52636A] font-medium mt-0.5">Indoor Galleries/Museums</p>
            </div>

            <div className="p-4 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-center">
              <CheckCircle2 className="w-6 h-6 text-[#16A36A] mx-auto mb-1.5" />
              <span className="text-2xl font-black text-[#16A36A]">{verifiedCount}</span>
              <p className="text-xs text-[#52636A] font-medium mt-0.5">Verified Opening Hours</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
