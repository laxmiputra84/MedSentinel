'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Hospital } from '@/lib/types';
import { HospitalCard } from '@/components/HospitalCard';
import api from '@/lib/api';

export default function HospitalsPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center text-gray-400 text-sm">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          Loading Hospital Directory...
        </div>
      }
    >
      <HospitalsContent />
    </Suspense>
  );
}

function HospitalsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Filter states initialized from URL query params
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || searchParams.get('illness') || '');
  const [selectedLocation, setSelectedLocation] = useState(searchParams.get('location') || '');
  const [selectedScheme, setSelectedScheme] = useState(searchParams.get('scheme') || '');
  const [maxDistance, setMaxDistance] = useState<number>(15);
  const [minRating, setMinRating] = useState<number>(0);
  const [sortBy, setSortBy] = useState<'rating' | 'distance'>('rating');

  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [savedHospitalIds, setSavedHospitalIds] = useState<number[]>([]);
  const [compareIds, setCompareIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch saved hospitals
  const fetchSavedHospitals = async () => {
    try {
      const res = await api.get<Hospital[]>('/saved-items');
      setSavedHospitalIds(res.data.map((h) => h.id));
    } catch (err) {
      // User not logged in, ignore
    }
  };

  // Fetch filtered hospitals
  const fetchHospitals = async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {};
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (selectedLocation) params.location = selectedLocation;
      if (selectedScheme) params.scheme = selectedScheme;
      if (maxDistance < 25) params.maxDistance = maxDistance;
      if (minRating > 0) params.minRating = minRating;

      const res = await api.get<Hospital[]>('/hospitals', { params });
      let data = res.data;

      // Sort client-side for instant snappy response
      if (sortBy === 'rating') {
        data.sort((a, b) => b.rating - a.rating);
      } else if (sortBy === 'distance') {
        data.sort((a, b) => a.distance - b.distance);
      }

      setHospitals(data);
    } catch (err) {
      console.error('Error fetching hospitals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedHospitals();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchHospitals();
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, selectedLocation, selectedScheme, maxDistance, minRating, sortBy]);

  // Handle Save / Unsave
  const handleSaveToggle = async (hospitalId: number) => {
    if (savedHospitalIds.includes(hospitalId)) {
      try {
        await api.delete(`/saved-items/${hospitalId}`);
        setSavedHospitalIds(savedHospitalIds.filter((id) => id !== hospitalId));
      } catch (err) {
        console.error('Error removing saved hospital:', err);
      }
    } else {
      try {
        await api.post('/saved-items', { hospital_id: hospitalId });
        setSavedHospitalIds([...savedHospitalIds, hospitalId]);
      } catch (err: any) {
        if (err.response?.status === 401) {
          router.push('/login');
        } else {
          console.error('Error saving hospital:', err);
        }
      }
    }
  };

  // Handle Compare Selection
  const handleCompareToggle = (hospitalId: number) => {
    if (compareIds.includes(hospitalId)) {
      setCompareIds(compareIds.filter((id) => id !== hospitalId));
    } else {
      if (compareIds.length >= 3) {
        alert('You can compare a maximum of 3 hospitals simultaneously.');
        return;
      }
      setCompareIds([...compareIds, hospitalId]);
    }
  };

  const navigateToComparison = () => {
    if (compareIds.length < 2) {
      alert('Please select at least 2 hospitals to compare.');
      return;
    }
    router.push(`/comparison?ids=${compareIds.join(',')}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Manrope'] mb-2">
          Hospitals Directory & Search
        </h1>
        <p className="text-gray-400 text-sm">
          Discover verified hospitals, check diagnostic tariffs, and see which government schemes are accepted.
        </p>
      </div>

      {/* Main Grid: Sidebar Filters + Cards */}
      <div className="grid lg:grid-cols-4 gap-8">
        {/* Sidebar Filter Panel */}
        <aside className="lg:col-span-1 space-y-6">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <h2 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-1.5">
                <span className="material-symbols-outlined text-blue-400 text-xl">tune</span>
                <span>Filters</span>
              </h2>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedLocation('');
                  setSelectedScheme('');
                  setMaxDistance(15);
                  setMinRating(0);
                  setSortBy('rating');
                }}
                className="text-xs text-gray-400 hover:text-blue-400 font-semibold"
              >
                Reset All
              </button>
            </div>

            {/* Keyword / Illness search */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-2">Search Condition / Hospital</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-base">
                  search
                </span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g. Cardiology, Fortis, MRI..."
                  className="w-full pl-9 pr-3 py-2 bg-gray-900 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-xs"
                />
              </div>
            </div>

            {/* Location Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-2">City / Location</label>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-white/15 rounded-xl text-white text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="">All Locations</option>
                <option value="Bengaluru">Bengaluru</option>
                <option value="Indiranagar">Indiranagar, Bengaluru</option>
                <option value="Bannerghatta">Bannerghatta Road, Bengaluru</option>
                <option value="Central">Central City</option>
              </select>
            </div>

            {/* Government Scheme Filter */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-2">Empanelled Scheme</label>
              <select
                value={selectedScheme}
                onChange={(e) => setSelectedScheme(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-white/15 rounded-xl text-white text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="">All Schemes</option>
                <option value="Ayushman Bharat">Ayushman Bharat (PM-JAY)</option>
                <option value="MJPJAY">MJPJAY Maharashtra</option>
                <option value="CGHS">CGHS Central Govt</option>
                <option value="ESIC">ESIC Social Security</option>
              </select>
            </div>

            {/* Distance Slider */}
            <div>
              <div className="flex justify-between text-xs font-semibold text-gray-300 mb-2">
                <span>Max Distance</span>
                <span className="text-blue-400">{maxDistance} km</span>
              </div>
              <input
                type="range"
                min="1"
                max="25"
                value={maxDistance}
                onChange={(e) => setMaxDistance(parseInt(e.target.value, 10))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>

            {/* Minimum Rating */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-2">Minimum Patient Rating</label>
              <div className="grid grid-cols-4 gap-2">
                {[0, 4.0, 4.5, 4.8].map((rating) => (
                  <button
                    key={rating}
                    type="button"
                    onClick={() => setMinRating(rating)}
                    className={`py-1.5 rounded-lg text-xs font-bold transition-all ${
                      minRating === rating
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-900 text-gray-400 border border-white/10 hover:text-white'
                    }`}
                  >
                    {rating === 0 ? 'All' : `${rating}★`}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Compare Bar Floating / Sticky */}
          {compareIds.length > 0 && (
            <div className="bg-gradient-to-r from-purple-900/90 to-blue-900/90 backdrop-blur-xl rounded-2xl p-5 border border-purple-500/30 shadow-2xl space-y-3 animate-fade-in">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-white">Compare Hospitals</span>
                <span className="bg-purple-500/30 text-purple-300 px-2 py-0.5 rounded-full font-bold">
                  {compareIds.length} / 3 selected
                </span>
              </div>
              <button
                onClick={navigateToComparison}
                className="w-full py-2.5 bg-white text-gray-900 font-bold rounded-xl text-xs hover:bg-gray-100 transition-all shadow-md flex items-center justify-center gap-1"
              >
                <span>Launch Comparison Matrix</span>
                <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </button>
            </div>
          )}
        </aside>

        {/* Hospital Cards List */}
        <main className="lg:col-span-3">
          {/* Top Sorting Bar */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 bg-gray-800/40 p-4 rounded-xl border border-white/5">
            <span className="text-xs text-gray-400">
              Found <strong className="text-white font-bold">{hospitals.length}</strong> hospitals matching criteria
            </span>
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-gray-400">Sort by:</span>
              <button
                onClick={() => setSortBy('rating')}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  sortBy === 'rating'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:text-white border border-white/10'
                }`}
              >
                Highest Rating
              </button>
              <button
                onClick={() => setSortBy('distance')}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  sortBy === 'distance'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:text-white border border-white/10'
                }`}
              >
                Closest Distance
              </button>
            </div>
          </div>

          {/* Cards Loading / List */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-gray-800/50 rounded-2xl h-80 animate-pulse border border-white/5"></div>
              ))}
            </div>
          ) : hospitals.length === 0 ? (
            <div className="bg-gray-800/60 rounded-2xl p-12 text-center border border-white/10">
              <span className="material-symbols-outlined text-gray-500 text-5xl mb-2">domain_disabled</span>
              <h3 className="text-xl font-bold text-white mb-2">No Hospitals Found</h3>
              <p className="text-gray-400 text-sm mb-6">
                Try widening your distance range or searching for broader symptoms.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedLocation('');
                  setSelectedScheme('');
                  setMaxDistance(25);
                }}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-all shadow-lg"
              >
                Clear All Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {hospitals.map((hospital) => (
                <div key={hospital.id} className="relative group">
                  <HospitalCard
                    hospital={hospital}
                    isSaved={savedHospitalIds.includes(hospital.id)}
                    onSaveToggle={handleSaveToggle}
                  />

                  {/* Add to Compare Checkbox Button */}
                  <div className="mt-2 flex justify-end">
                    <button
                      onClick={() => handleCompareToggle(hospital.id)}
                      className={`text-xs px-3 py-1 rounded-lg border transition-all flex items-center gap-1.5 ${
                        compareIds.includes(hospital.id)
                          ? 'bg-purple-600 border-purple-500 text-white font-bold'
                          : 'bg-black/30 border-white/10 text-gray-400 hover:text-white'
                      }`}
                    >
                      <span className="material-symbols-outlined text-xs">
                        {compareIds.includes(hospital.id) ? 'check_box' : 'check_box_outline_blank'}
                      </span>
                      <span>{compareIds.includes(hospital.id) ? 'Selected to Compare' : 'Add to Compare'}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
