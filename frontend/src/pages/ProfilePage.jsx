import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Mail,
  Sliders,
  Bookmark,
  Shield,
  Save,
  LogOut,
  CheckCircle2,
  Trash2,
  Compass,
  ArrowRight,
  Car,
  DollarSign,
  Heart,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTrip } from '../context/TripContext';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { formatCurrency, getCategoryBadgeColor } from '../utils/formatters';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, updateProfile, logout } = useAuth();
  const { savedPlaces, toggleSavePlace } = useTrip();

  // Local form state
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [preferredCategories, setPreferredCategories] = useState(
    user?.preferences?.preferred_categories || 'Sightseeing, Culture, Food'
  );
  const [preferredActivities, setPreferredActivities] = useState(
    user?.preferences?.preferred_activities || 'Exploring historic landmarks, dining'
  );
  const [preferredTransport, setPreferredTransport] = useState(
    user?.preferences?.preferred_transport || 'Public Transit'
  );
  const [preferredBudget, setPreferredBudget] = useState(
    user?.preferences?.preferred_budget || 'Medium'
  );
  const [preferredStyle, setPreferredStyle] = useState(
    user?.preferences?.preferred_travel_style || 'Balanced'
  );

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Sync if user data changes
  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      if (user.preferences) {
        setPreferredCategories(user.preferences.preferred_categories || 'Sightseeing, Culture, Food');
        setPreferredActivities(user.preferences.preferred_activities || 'Exploring historic landmarks, dining');
        setPreferredTransport(user.preferences.preferred_transport || 'Public Transit');
        setPreferredBudget(user.preferences.preferred_budget || 'Medium');
        setPreferredStyle(user.preferences.preferred_travel_style || 'Balanced');
      }
    }
  }, [user]);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      await updateProfile({
        fullName: fullName.trim(),
        preferences: {
          preferred_categories: preferredCategories,
          preferred_activities: preferredActivities,
          preferred_transport: preferredTransport,
          preferred_budget: preferredBudget,
          preferred_travel_style: preferredStyle,
        },
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      setError(err.message || 'Failed to update user profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#DCE6E3] pb-5">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="px-3 py-1 rounded-full bg-[#18B8A6]/10 text-[#129889] text-xs font-bold border border-[#18B8A6]/20">
              Account Management
            </span>
            <span className="text-xs text-[#829196]">•</span>
            <span className="text-xs font-semibold text-[#52636A]">ID: #{user?.id || 'GUEST'}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#163B46] tracking-tight">
            Traveler Profile & Preferences
          </h1>
          <p className="text-xs sm:text-sm text-[#52636A] mt-1">
            Personalize your travel interests, transport mode, and budget baseline applied during recommendation scoring.
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="self-start sm:self-auto px-4 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Log Out</span>
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {saveSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-[#16A36A] text-xs flex items-center space-x-2 shadow-sm">
          <CheckCircle2 className="w-4 h-4 text-[#16A36A] flex-shrink-0" />
          <span>Profile and travel preferences updated successfully!</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Account Details Card */}
        <div className="md:col-span-1 space-y-6">
          <div className="p-6 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
            <div className="flex flex-col items-center text-center space-y-2">
              <div className="w-16 h-16 rounded-2xl bg-[#163B46] flex items-center justify-center text-[#18B8A6] font-bold text-2xl shadow-soft">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <h2 className="text-lg font-bold text-[#163B46]">{user?.full_name || 'Traveler'}</h2>
              <p className="text-xs text-[#52636A]">{user?.email}</p>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-[#16A36A] border border-emerald-200 text-[10px] font-bold uppercase">
                Active Account
              </span>
            </div>

            <div className="pt-4 border-t border-[#DCE6E3] space-y-2 text-xs text-[#52636A]">
              <div className="flex justify-between">
                <span className="text-[#829196]">Account Type:</span>
                <span className="font-semibold text-[#163B46]">Full Access</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#829196]">Security:</span>
                <span className="font-semibold text-[#16A36A]">Argon2id Hash</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#829196]">JWT Token:</span>
                <span className="font-semibold text-[#18B8A6]">Active</span>
              </div>
            </div>
          </div>

          {/* Quick Stats Pill */}
          <div className="p-5 rounded-2xl bg-white border border-[#DCE6E3] shadow-soft space-y-3">
            <h3 className="text-xs font-bold text-[#829196] uppercase tracking-wider">
              Saved Bookmarks
            </h3>
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-[#163B46]">{savedPlaces.length} Saved Places</span>
              <Bookmark className="w-4 h-4 text-[#18B8A6]" />
            </div>
          </div>
        </div>

        {/* Right Column: Preferences Form */}
        <div className="md:col-span-2 space-y-6">
          <form
            onSubmit={handleSaveProfile}
            className="p-8 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft space-y-6"
          >
            <div className="border-b border-[#DCE6E3] pb-3 flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#163B46] uppercase tracking-wider flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-[#18B8A6]" />
                <span>Travel Customization & Baselines</span>
              </h3>
              <span className="text-[11px] text-[#829196]">Saved to Database</span>
            </div>

            {/* Full Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#163B46]">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white focus:ring-2 focus:ring-[#18B8A6]/20 text-xs sm:text-sm text-[#26383D] focus:outline-none transition-all"
              />
            </div>

            {/* Preferred Categories */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#163B46]">
                Preferred Tourism Categories (Factor P)
              </label>
              <input
                type="text"
                value={preferredCategories}
                onChange={(e) => setPreferredCategories(e.target.value)}
                placeholder="e.g. Sightseeing, Culture, Food, Nature"
                className="w-full px-4 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white focus:ring-2 focus:ring-[#18B8A6]/20 text-xs sm:text-sm text-[#26383D] focus:outline-none transition-all"
              />
              <span className="text-[11px] text-[#829196]">
                Comma-separated list used by the recommendation engine baseline.
              </span>
            </div>

            {/* Preferred Activities */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#163B46]">
                Preferred Activities
              </label>
              <input
                type="text"
                value={preferredActivities}
                onChange={(e) => setPreferredActivities(e.target.value)}
                placeholder="e.g. Exploring historic landmarks, dining, photography"
                className="w-full px-4 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white focus:ring-2 focus:ring-[#18B8A6]/20 text-xs sm:text-sm text-[#26383D] focus:outline-none transition-all"
              />
            </div>

            {/* Dropdown / Selection Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Transport */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#163B46]">Default Transport</label>
                <select
                  value={preferredTransport}
                  onChange={(e) => setPreferredTransport(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white text-xs text-[#26383D] focus:outline-none transition-all"
                >
                  <option value="Public Transit">Public Transit / Metro</option>
                  <option value="Car">Car / Taxi</option>
                  <option value="Walking">Walking Tour</option>
                  <option value="Bicycle">Cycling</option>
                </select>
              </div>

              {/* Budget Tier */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#163B46]">Budget Tier</label>
                <select
                  value={preferredBudget}
                  onChange={(e) => setPreferredBudget(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white text-xs text-[#26383D] focus:outline-none transition-all"
                >
                  <option value="Budget">Budget Conscious</option>
                  <option value="Medium">Medium / Balanced</option>
                  <option value="Luxury">Luxury / Premium</option>
                </select>
              </div>

              {/* Travel Style */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#163B46]">Travel Style</label>
                <select
                  value={preferredStyle}
                  onChange={(e) => setPreferredStyle(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white text-xs text-[#26383D] focus:outline-none transition-all"
                >
                  <option value="Relaxed">Relaxed (Slow-Paced)</option>
                  <option value="Balanced">Balanced</option>
                  <option value="Packed">Packed (Fast-Paced)</option>
                </select>
              </div>
            </div>

            {/* Save Button */}
            <div className="pt-4 border-t border-[#DCE6E3] flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs shadow-soft transition-all flex items-center space-x-2 disabled:opacity-50"
              >
                {saving ? (
                  <LoadingSpinner size="sm" label="" />
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Bookmarked Attractions Management */}
          <div className="p-6 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft space-y-4">
            <h3 className="text-sm font-bold text-[#163B46] uppercase tracking-wider flex items-center space-x-2">
              <Bookmark className="w-4 h-4 text-[#18B8A6]" />
              <span>Saved Places Management ({savedPlaces.length})</span>
            </h3>

            {savedPlaces.length === 0 ? (
              <p className="text-xs text-[#829196] italic">No attractions saved yet.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {savedPlaces.map((p) => (
                  <div
                    key={p.place_id || p.id}
                    className="p-3.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] flex items-center justify-between text-xs"
                  >
                    <div>
                      <h4 className="font-bold text-[#163B46] line-clamp-1">{p.name}</h4>
                      <span className="text-[10px] text-[#829196]">{p.category}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleSavePlace(p)}
                      title="Remove bookmark"
                      className="text-[#829196] hover:text-rose-600 p-1.5 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
