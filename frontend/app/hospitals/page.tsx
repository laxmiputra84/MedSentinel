'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Hospital, SearchIntentMeta } from '@/lib/types';
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

  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [searchIntent, setSearchIntent] = useState<SearchIntentMeta | null>(null);

  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [savedHospitalIds, setSavedHospitalIds] = useState<number[]>([]);
  const [compareIds, setCompareIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Toggle user GPS proximity
  const handleUseMyLocation = () => {
    if (coords) {
      setCoords(null);
      return;
    }
    if (typeof window === 'undefined' || !navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        });
        setGpsLoading(false);
      },
      (err) => {
        console.warn('Geolocation unavailable or denied:', err);
        // Fallback default coordinates at REVA University campus
        setCoords({
          lat: 13.1147,
          lon: 77.6346,
        });
        setGpsLoading(false);
      },
      { timeout: 5000 }
    );
  };

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
    setError(null);
    try {
      const params: Record<string, string | number> = {};
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (selectedLocation && selectedLocation !== 'All Locations') params.location = selectedLocation;
      if (selectedScheme && selectedScheme !== 'All Schemes') params.scheme = selectedScheme;
      if (minRating > 0) params.minRating = minRating;

      // Only pass distance and coordinates when GPS is actively enabled
      if (coords) {
        params.latitude = coords.lat;
        params.longitude = coords.lon;
        if (maxDistance) {
          params.maxDistance = maxDistance;
        }
      }

      const res = await api.get<Hospital[]>('/hospitals', { params });
      let data = res.data;

      // Extract search intent from response headers
      const searchType = res.headers['x-search-type'] as any;
      if (searchQuery.trim() || searchType) {
        setSearchIntent({
          search_query: searchQuery.trim() || null,
          search_type: searchType || 'keyword',
          is_nearby_search: res.headers['x-nearby-intent'] === 'true',
          detected_location: res.headers['x-detected-location'] || null,
          detected_specialty: res.headers['x-detected-specialty'] || null,
          has_coordinates: res.headers['x-has-coordinates'] === 'true',
        });
      } else {
        setSearchIntent(null);
      }

      // Sort client-side if no GPS coordinates active
      if (!coords) {
        if (sortBy === 'rating') {
          data.sort((a, b) => (b.rating || 0) - (a.rating || 0));
        } else if (sortBy === 'distance') {
          data.sort((a, b) => (a.distance || 0) - (b.distance || 0));
        }
      }

      setHospitals(data);
    } catch (err) {
      console.error('Error fetching hospitals:', err);
      setError('Unable to load hospital records. Please check your network connection or try again.');
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
  }, [searchQuery, selectedLocation, selectedScheme, maxDistance, minRating, sortBy, coords]);

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
                  setCoords(null);
                  setSearchIntent(null);
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
              <button
                type="button"
                onClick={handleUseMyLocation}
                disabled={gpsLoading}
                className={`mt-2 w-full py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                  coords
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30'
                    : 'bg-white/5 text-gray-300 border border-white/10 hover:text-white hover:bg-white/10'
                }`}
              >
                <span className="material-symbols-outlined text-sm">
                  {coords ? 'my_location' : 'location_searching'}
                </span>
                <span>{gpsLoading ? 'Detecting Location...' : coords ? 'GPS Proximity Active (Clear)' : 'Use GPS Proximity'}</span>
              </button>
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
                <option value="Bengaluru">Bengaluru, Karnataka</option>
                <option value="Mumbai">Mumbai, Maharashtra</option>
                <option value="Delhi">New Delhi, NCR</option>
                <option value="Chennai">Chennai, Tamil Nadu</option>
                <option value="Hyderabad">Hyderabad / Secunderabad</option>
                <option value="Pune">Pune, Maharashtra</option>
                <option value="Kolkata">Kolkata, West Bengal</option>
                <option value="Ahmedabad">Ahmedabad, Gujarat</option>
                <option value="Jaipur">Jaipur, Rajasthan</option>
                <option value="Kochi">Kochi, Kerala</option>
                <option value="Gurugram">Gurugram, Haryana</option>
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
          {/* GPS Proximity / Filter Status Banner */}
          <div className={`mb-6 p-4 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 backdrop-blur-md shadow-lg ${
            coords
              ? 'bg-emerald-950/40 border-emerald-500/30'
              : 'bg-blue-950/30 border-blue-500/20'
          }`}>
            <div className="flex items-center gap-3">
              <span className={`material-symbols-outlined text-2xl p-2 rounded-xl ${
                coords ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'
              }`}>
                {coords ? 'near_me' : 'explore'}
              </span>
              <div>
                <p className="text-sm font-bold text-white">
                  {coords ? (
                    <span>Showing hospitals within {maxDistance} km.</span>
                  ) : (
                    <span>Showing hospitals without distance filtering.</span>
                  )}
                </p>
                <p className="text-xs text-gray-400">
                  {coords ? (
                    <span>GPS proximity active ({coords.lat.toFixed(4)}, {coords.lon.toFixed(4)}). Ranked nearest first.</span>
                  ) : (
                    <span>Enable GPS to find hospitals near you and filter by maximum distance.</span>
                  )}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleUseMyLocation}
              disabled={gpsLoading}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shrink-0 ${
                coords
                  ? 'bg-emerald-600/30 border border-emerald-500 text-emerald-300 hover:bg-emerald-600/40'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-md'
              }`}
            >
              <span className="material-symbols-outlined text-sm">
                {coords ? 'my_location' : 'location_searching'}
              </span>
              <span>{gpsLoading ? 'Locating...' : coords ? 'GPS Active (Clear)' : 'Use GPS Proximity'}</span>
            </button>
          </div>

          {/* Search Intent Banner (if NLP intent detected) */}
          {searchIntent && (searchIntent.search_query || searchIntent.is_nearby_search) && (
            <div className="mb-6 p-4 bg-gradient-to-r from-purple-900/30 via-indigo-900/20 to-gray-900/50 border border-purple-500/30 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 backdrop-blur-md">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-400 font-semibold">Search Intent:</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                    searchIntent.search_type === 'nearby'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                      : searchIntent.search_type === 'specialty_location'
                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                      : searchIntent.search_type === 'location'
                      ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                      : searchIntent.search_type === 'specialty'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-gray-800 text-gray-300 border border-white/10'
                  }`}>
                    {searchIntent.search_type === 'nearby' && '📍 Nearby Search'}
                    {searchIntent.search_type === 'specialty_location' && '🩺 Specialty + Location'}
                    {searchIntent.search_type === 'location' && '🏙️ Location Search'}
                    {searchIntent.search_type === 'specialty' && '⚕️ Specialty Search'}
                    {searchIntent.search_type === 'keyword' && '🔍 Keyword Search'}
                  </span>
                  {searchIntent.detected_location && (
                    <span className="bg-blue-500/20 border border-blue-500/30 text-blue-200 px-2.5 py-0.5 rounded-md text-xs font-medium">
                      Location: <strong>{searchIntent.detected_location}</strong>
                    </span>
                  )}
                  {searchIntent.detected_specialty && (
                    <span className="bg-emerald-500/20 border border-emerald-500/30 text-emerald-200 px-2.5 py-0.5 rounded-md text-xs font-medium">
                      Specialty: <strong>{searchIntent.detected_specialty}</strong>
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  Active Query: <span className="text-white font-medium italic">"{searchIntent.search_query}"</span>
                </p>
              </div>
            </div>
          )}

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

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-base">error</span>
                <span>{error}</span>
              </div>
              <button
                onClick={fetchHospitals}
                className="px-3 py-1 bg-red-600/60 hover:bg-red-600 text-white font-bold rounded-lg transition-all"
              >
                Retry
              </button>
            </div>
          )}

          {/* Cards Loading / List */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-gray-800/50 rounded-2xl h-80 animate-pulse border border-white/5"></div>
              ))}
            </div>
          ) : hospitals.length === 0 ? (
            <div className="bg-gray-800/60 rounded-2xl p-10 text-center border border-white/10 shadow-2xl">
              <span className="material-symbols-outlined text-amber-400/80 text-5xl mb-2">domain_disabled</span>
              <h3 className="text-xl font-bold text-white mb-2 font-['Manrope']">No Hospitals Found</h3>
              
              {/* Detailed Specific Reason Box */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 max-w-lg mx-auto mb-6 text-left space-y-2 text-xs text-gray-300">
                <div className="font-semibold text-gray-200 border-b border-white/10 pb-1.5 flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-amber-400 text-sm">info</span>
                  <span>Filtered Reason Analysis:</span>
                </div>
                {searchQuery.trim() && (
                  <p>• No hospitals match search condition: <strong className="text-white">"{searchQuery.trim()}"</strong></p>
                )}
                {selectedLocation && selectedLocation !== 'All Locations' && (
                  <p>• No hospitals found in location: <strong className="text-white">"{selectedLocation}"</strong></p>
                )}
                {selectedScheme && selectedScheme !== 'All Schemes' && (
                  <p>• No hospitals accept empanelled scheme: <strong className="text-white">"{selectedScheme}"</strong></p>
                )}
                {minRating > 0 && (
                  <p>• No hospitals meet the minimum patient rating of <strong className="text-white">{minRating}★</strong></p>
                )}
                {coords && maxDistance && (
                  <p>• No hospitals found within <strong className="text-white">{maxDistance} km</strong> of your GPS coordinates</p>
                )}
                {!searchQuery.trim() && !selectedLocation && !selectedScheme && minRating === 0 && (!coords || !maxDistance) && (
                  <p>• No records found matching the active query criteria. Try clearing search filters.</p>
                )}
              </div>

              <div className="flex justify-center gap-3 flex-wrap">
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedLocation('');
                    setSelectedScheme('');
                    setMaxDistance(15);
                    setMinRating(0);
                    setCoords(null);
                    setSearchIntent(null);
                  }}
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-bold rounded-xl text-xs transition-all shadow-lg"
                >
                  Clear All Filters
                </button>
                {coords && (
                  <button
                    onClick={() => setCoords(null)}
                    className="px-4 py-2.5 bg-white/10 hover:bg-white/15 text-gray-200 font-semibold rounded-xl text-xs transition-all border border-white/10"
                  >
                    Disable GPS Distance Filter
                  </button>
                )}
              </div>
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
