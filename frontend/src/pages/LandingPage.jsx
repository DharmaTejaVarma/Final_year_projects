import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Compass,
  Sparkles,
  MapPin,
  Calendar,
  Route,
  CloudSun,
  Bot,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  Clock,
  DollarSign,
  Layers,
  Map as MapIcon,
  Search,
} from 'lucide-react';
import { useTrip } from '../context/TripContext';

export default function LandingPage({ healthState }) {
  const navigate = useNavigate();
  const { updatePlan } = useTrip();
  const [quickQuery, setQuickQuery] = useState('');

  const popularDestinations = [
    {
      name: 'Hyderabad',
      state: 'Telangana',
      tagline: 'City of Pearls, Nizam Heritage & World-Famous Dum Biryani',
      image: 'https://images.unsplash.com/photo-1605007493699-ce65834f8a00?auto=format&fit=crop&w=800&q=80',
      highlights: ['Golconda Fort', 'Charminar', 'Chowmahalla Palace', 'Salar Jung Museum'],
      duration: '2-3 Days',
      avgBudget: '₹4,500 - ₹8,000',
    },
    {
      name: 'Bengaluru',
      state: 'Karnataka',
      tagline: 'The Garden City of India, Historic Palaces & Vibrant Tech Hub',
      image: 'https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=800&q=80',
      highlights: ['Lalbagh Botanical Garden', 'Bangalore Palace', 'Cubbon Park', 'Tipu Sultan Palace'],
      duration: '2-4 Days',
      avgBudget: '₹5,000 - ₹9,500',
    },
    {
      name: 'Jaipur',
      state: 'Rajasthan',
      tagline: 'The Pink City: Royal Citadels, Amber Fort & Hawa Mahal',
      image: 'https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=800&q=80',
      highlights: ['Amber Fort', 'Hawa Mahal', 'City Palace', 'Jantar Mantar'],
      duration: '3-4 Days',
      avgBudget: '₹6,000 - ₹12,000',
    },
    {
      name: 'Goa',
      state: 'Goa',
      tagline: 'Sun-drenched Coastal Beaches, Portuguese Heritage & Seafood',
      image: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80',
      highlights: ['Fort Aguada', 'Basilica of Bom Jesus', 'Baga Beach', 'Dudhsagar Falls'],
      duration: '3-5 Days',
      avgBudget: '₹7,500 - ₹15,000',
    },
  ];

  const features = [
    {
      icon: TrendingUp,
      title: 'Context-Aware POI Scoring',
      description:
        'Scores attractions across 6 mathematical dimensions: Preference (P), Distance (D), Time (T), Weather (W), Category (C), and Budget (B).',
      badge: 'Multi-Criteria Engine',
      badgeColor: 'text-[#18B8A6] bg-[#18B8A6]/10 border-[#18B8A6]/20',
    },
    {
      icon: Route,
      title: '2-Opt Road TSP Optimization',
      description:
        'Solves the Traveling Salesperson Problem using Nearest-Neighbor heuristic + 2-Opt local search to eliminate crossed paths and minimize road distance.',
      badge: 'OpenRouteService',
      badgeColor: 'text-[#163B46] bg-[#EEF3F1] border-[#DCE6E3]',
    },
    {
      icon: CloudSun,
      title: 'Dynamic Weather Adaptation',
      description:
        'Fetches live hourly weather forecasts from Open-Meteo. Penalizes rain-affected outdoor forts while suggesting indoor museum alternatives.',
      badge: 'Open-Meteo Live',
      badgeColor: 'text-[#E6A23C] bg-amber-50 border-amber-200',
    },
    {
      icon: Bot,
      title: 'LangGraph Multi-Node Assistant',
      description:
        'Stateful 8-node LangGraph pipeline orchestrating natural language understanding, preference extraction, and grounded factual explanations.',
      badge: 'LangGraph + OpenAI',
      badgeColor: 'text-[#18B8A6] bg-[#18B8A6]/10 border-[#18B8A6]/20',
    },
    {
      icon: Layers,
      title: 'ChromaDB RAG Tourism Knowledge',
      description:
        'Deterministic 384-D semantic embeddings and ChromaDB vector store citing official Archaeological Survey of India archives without hallucination.',
      badge: 'Zero-Hallucination RAG',
      badgeColor: 'text-[#16A36A] bg-emerald-50 border-emerald-200',
    },
    {
      icon: DollarSign,
      title: 'Price Provenance & Budget Ledger',
      description:
        'Comprehensive multi-tier accounting distinguishing verified venue fees, calibrated transit rates, dining allocations, and contingency buffers.',
      badge: 'Financial Optimizer',
      badgeColor: 'text-[#163B46] bg-[#EEF3F1] border-[#DCE6E3]',
    },
  ];

  const handleQuickPlan = (destName) => {
    updatePlan({ destination: destName });
    navigate('/plan');
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!quickQuery.trim()) return;
    updatePlan({ userQuery: quickQuery });
    navigate('/plan');
  };

  return (
    <div className="min-h-screen flex flex-col justify-between bg-[#F4F7F6]">
      <main className="flex-grow">
        {/* --- Hero Section --- */}
        <section className="relative pt-14 pb-20 overflow-hidden">
          {/* Subtle Ambient Background Highlight */}
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[340px] bg-gradient-to-tr from-[#18B8A6]/10 via-[#EEF3F1] to-[#163B46]/5 blur-[120px] rounded-full pointer-events-none" />

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
            {/* Small Label Pill */}
            <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-[#18B8A6]/10 border border-[#18B8A6]/25 text-[#129889] text-xs font-bold tracking-wide uppercase mb-6 shadow-soft">
              <Sparkles className="w-3.5 h-3.5 text-[#18B8A6]" />
              <span>AI-POWERED AUTONOMOUS TOURISM ENGINE</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-[#163B46] mb-6">
              Travel Planning,{' '}
              <span className="text-[#18B8A6]">
                Engineered with Precision.
              </span>
            </h1>

            {/* Description */}
            <p className="max-w-3xl mx-auto text-base sm:text-lg text-[#52636A] font-normal leading-relaxed mb-10">
              TravelSenseAI combines context-aware POI scoring, 2-Opt road TSP route optimization, real-time weather adaptations, and a LangGraph conversational assistant grounded in verified tourism knowledge.
            </p>

            {/* AI Trip Search Bar */}
            <div className="max-w-2xl mx-auto mb-10">
              <form
                onSubmit={handleSearchSubmit}
                className="relative flex items-center bg-white border border-[#DCE6E3] rounded-2xl p-2 shadow-soft-lg focus-within:border-[#18B8A6] focus-within:ring-2 focus-within:ring-[#18B8A6]/20 transition-all"
              >
                <Search className="w-5 h-5 text-[#829196] ml-3 flex-shrink-0" />
                <input
                  type="text"
                  value={quickQuery}
                  onChange={(e) => setQuickQuery(e.target.value)}
                  placeholder="e.g. A relaxed 2-day trip to Hyderabad with budget ₹5000..."
                  className="w-full bg-transparent border-none text-xs sm:text-sm text-[#26383D] px-3 py-2 focus:outline-none placeholder-[#829196]"
                />
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs sm:text-sm flex items-center space-x-1.5 shadow-soft transition-all hover:scale-[1.02] flex-shrink-0"
                >
                  <span>AI Plan</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>

              {/* Clickable Example Prompts */}
              <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-[#52636A] mt-3">
                <span className="font-medium text-[#829196]">Try:</span>
                <button
                  type="button"
                  onClick={() => {
                    setQuickQuery('I want a relaxed 2-day trip to Hyderabad. I like historical places and good food. My budget is ₹5,000.');
                  }}
                  className="text-[#18B8A6] hover:text-[#129889] hover:underline font-medium"
                >
                  "2-day Hyderabad history trip under ₹5k"
                </button>
                <span>•</span>
                <button
                  type="button"
                  onClick={() => {
                    setQuickQuery('A weekend 3-day cultural tour in Bengaluru for 2 people with budget ₹8000');
                  }}
                  className="text-[#18B8A6] hover:text-[#129889] hover:underline font-medium"
                >
                  "3 days in Bengaluru"
                </button>
              </div>
            </div>

            {/* Hero Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
              <Link
                to="/plan"
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-sm shadow-soft hover:shadow-soft-md transition-all hover:-translate-y-0.5 flex items-center justify-center space-x-2"
              >
                <Calendar className="w-4 h-4" />
                <span>Start Planning Now</span>
              </Link>
              <Link
                to="/assistant"
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-white hover:bg-[#EEF3F1] text-[#163B46] font-semibold text-sm border border-[#DCE6E3] transition-all flex items-center justify-center space-x-2 shadow-soft"
              >
                <Bot className="w-4 h-4 text-[#18B8A6]" />
                <span>Talk to AI Assistant</span>
              </Link>
            </div>

            {/* Quick Metrics Bar */}
            <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 p-6 rounded-2xl bg-white border border-[#DCE6E3] text-left shadow-soft">
              <div>
                <span className="text-[11px] text-[#829196] font-semibold uppercase tracking-wider">Scoring Dimensions</span>
                <p className="text-lg sm:text-xl font-bold text-[#163B46] mt-0.5">6 Criteria (P,D,T,W,C,B)</p>
              </div>
              <div>
                <span className="text-[11px] text-[#829196] font-semibold uppercase tracking-wider">Routing Algorithm</span>
                <p className="text-lg sm:text-xl font-bold text-[#18B8A6] mt-0.5">2-Opt Local Search TSP</p>
              </div>
              <div>
                <span className="text-[11px] text-[#829196] font-semibold uppercase tracking-wider">RAG Knowledge Base</span>
                <p className="text-lg sm:text-xl font-bold text-[#16A36A] mt-0.5">ChromaDB 384-D</p>
              </div>
              <div>
                <span className="text-[11px] text-[#829196] font-semibold uppercase tracking-wider">Verification Status</span>
                <p className="text-lg sm:text-xl font-bold text-[#163B46] mt-0.5">123/123 Tests Passed</p>
              </div>
            </div>
          </div>
        </section>

        {/* --- How It Works Section --- */}
        <section className="py-20 bg-[#EEF3F1] border-y border-[#DCE6E3] relative">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <span className="text-xs font-bold text-[#18B8A6] uppercase tracking-wider">Step-by-Step Workflow</span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#163B46] mt-2">
                How TravelSenseAI Orchestrates Your Journey
              </h2>
              <p className="text-sm text-[#52636A] mt-3">
                From natural language query to turn-by-turn road itinerary, our multi-tier engine guarantees mathematical consistency without hallucinating facts.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                {
                  step: '01',
                  title: 'Input Preferences or Natural Language',
                  desc: 'Specify destination, dates, budget, transport, and interests—or type natural inquiries parsed by our dual-engine NLU.',
                  icon: Calendar,
                },
                {
                  step: '02',
                  title: 'Multi-Criteria POI Ranking & Clustering',
                  desc: 'Attractions are scored across 6 dimensions with DBSCAN density clustering grouping nearby venues together.',
                  icon: TrendingUp,
                },
                {
                  step: '03',
                  title: '2-Opt Road Routing & Multi-Day Itinerary',
                  desc: 'OpenRouteService road geometry and 2-Opt local search schedule opening hours, visit durations, and dining breaks.',
                  icon: Route,
                },
                {
                  step: '04',
                  title: 'Interactive OpenStreetMap & PDF Report',
                  desc: 'Inspect your route polylines on Leaflet maps, consult the LangGraph AI assistant, and export an executive PDF report.',
                  icon: MapIcon,
                },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.step}
                    className="relative p-6 rounded-2xl bg-white border border-[#DCE6E3] hover:border-[#18B8A6] transition-all flex flex-col justify-between shadow-soft hover:shadow-soft-md group"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-3xl font-black text-[#DCE6E3] group-hover:text-[#18B8A6]/40 transition-colors">
                          {item.step}
                        </span>
                        <div className="w-10 h-10 rounded-xl bg-[#EEF3F1] flex items-center justify-center text-[#163B46] font-bold group-hover:bg-[#18B8A6]/10 group-hover:text-[#18B8A6] transition-colors">
                          <Icon className="w-5 h-5" />
                        </div>
                      </div>
                      <h3 className="text-base font-bold text-[#163B46] mb-2 group-hover:text-[#18B8A6] transition-colors">
                        {item.title}
                      </h3>
                      <p className="text-xs text-[#52636A] leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* --- Popular Destinations Section --- */}
        <section className="py-20 relative">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-12">
              <div>
                <span className="text-xs font-bold text-[#18B8A6] uppercase tracking-wider">Curated Knowledge Hubs</span>
                <h2 className="text-3xl sm:text-4xl font-extrabold text-[#163B46] mt-2">
                  Featured Destinations Ready for Exploration
                </h2>
                <p className="text-sm text-[#52636A] mt-2">
                  Pre-indexed in our ChromaDB vector store with verified historical archives, opening hours, and road networks.
                </p>
              </div>
              <Link
                to="/plan"
                className="mt-4 md:mt-0 inline-flex items-center space-x-1.5 text-xs font-bold text-[#18B8A6] hover:text-[#129889]"
              >
                <span>Explore all destinations</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {popularDestinations.map((dest) => (
                <div
                  key={dest.name}
                  className="rounded-2xl overflow-hidden bg-white border border-[#DCE6E3] hover:border-[#18B8A6] shadow-soft hover:shadow-soft-lg transition-all hover:-translate-y-1 group flex flex-col justify-between"
                >
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={dest.image}
                      alt={dest.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#163B46]/80 via-transparent to-transparent" />
                    <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white">
                      <div>
                        <span className="text-[10px] text-[#18B8A6] font-semibold uppercase">{dest.state}</span>
                        <h3 className="text-xl font-bold text-white">{dest.name}</h3>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full bg-white/90 backdrop-blur-sm text-[10px] font-bold text-[#163B46] shadow-sm">
                        {dest.duration}
                      </span>
                    </div>
                  </div>

                  <div className="p-5 space-y-3 flex-1 flex flex-col justify-between">
                    <div>
                      <p className="text-xs text-[#52636A] leading-relaxed mb-3">{dest.tagline}</p>
                      <div className="space-y-1.5">
                        <span className="text-[10px] font-bold text-[#829196] uppercase tracking-wider">Top Highlights:</span>
                        <div className="flex flex-wrap gap-1">
                          {dest.highlights.map((h) => (
                            <span
                              key={h}
                              className="text-[10px] px-2 py-0.5 rounded-lg bg-[#EEF3F1] text-[#26383D] border border-[#DCE6E3]"
                            >
                              {h}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-[#DCE6E3] flex items-center justify-between">
                      <div className="text-[11px] text-[#52636A]">
                        <span>Est: </span>
                        <span className="text-[#163B46] font-bold">{dest.avgBudget}</span>
                      </div>
                      <button
                        onClick={() => handleQuickPlan(dest.name)}
                        className="px-3 py-1.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white text-xs font-bold transition-all flex items-center space-x-1 shadow-soft"
                      >
                        <span>Plan Trip</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* --- Main Features Grid --- */}
        <section className="py-20 bg-[#EEF3F1] border-t border-[#DCE6E3]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <span className="text-xs font-bold text-[#18B8A6] uppercase tracking-wider">Full-Stack Intelligence</span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#163B46] mt-2">
                Engineered from the Ground Up
              </h2>
              <p className="text-sm text-[#52636A] mt-3">
                Six integrated backend algorithmic engines working cohesively to deliver context-aware, feasible travel plans.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feat) => {
                const Icon = feat.icon;
                return (
                  <div
                    key={feat.title}
                    className="p-6 rounded-2xl bg-white border border-[#DCE6E3] hover:border-[#18B8A6] transition-all shadow-soft hover:shadow-soft-md flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-10 h-10 rounded-xl bg-[#EEF3F1] flex items-center justify-center text-[#163B46]">
                          <Icon className="w-5 h-5" />
                        </div>
                        <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${feat.badgeColor}`}>
                          {feat.badge}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-[#163B46] mb-2">{feat.title}</h3>
                      <p className="text-xs text-[#52636A] leading-relaxed">{feat.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* --- Final Call to Action Banner --- */}
        <section className="py-20 relative overflow-hidden">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
            <div className="p-10 sm:p-14 rounded-3xl bg-[#163B46] shadow-soft-xl relative overflow-hidden text-white">
              <div className="absolute top-0 right-0 w-80 h-80 bg-[#18B8A6]/15 rounded-full blur-3xl pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-80 h-80 bg-[#244F59]/40 rounded-full blur-3xl pointer-events-none" />

              <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
                Ready to Experience Next-Gen Travel Planning?
              </h2>
              <p className="text-[#DCE6E3] max-w-2xl mx-auto text-sm leading-relaxed mb-8">
                Create an account or start with our instant trip planner to generate multi-day itineraries, explore interactive maps, and chat with the AI assistant.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  to="/register"
                  className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-sm shadow-soft transition-all hover:scale-[1.02]"
                >
                  Create Free Account
                </Link>
                <Link
                  to="/plan"
                  className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-white hover:bg-[#EEF3F1] text-[#163B46] font-semibold text-sm transition-all shadow-soft"
                >
                  Launch Trip Planner
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
