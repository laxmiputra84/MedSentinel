'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SearchFlowPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1 data
  const [condition, setCondition] = useState('');
  const [location, setLocation] = useState('');
  const [urgency, setUrgency] = useState<'emergency' | 'scheduled' | 'flexible' | ''>('scheduled');

  // Step 2 data
  const [fullName, setFullName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [income, setIncome] = useState('low');
  const [state, setState] = useState('');
  const [aadhaar, setAadhaar] = useState('');

  const [validationError, setValidationError] = useState('');

  const handleGoToStep2 = () => {
    if (!condition.trim()) {
      setValidationError('Please enter a medical condition or treatment procedure');
      return;
    }
    setValidationError('');
    setStep(2);
  };

  const handleProcessSearch = () => {
    setStep(3);
    // Simulate AI processing delay before forwarding to hospitals page
    setTimeout(() => {
      const params = new URLSearchParams();
      if (condition) params.set('search', condition);
      if (location) params.set('location', location);
      if (income) params.set('income', income);
      router.push(`/hospitals?${params.toString()}`);
    }, 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Progress Steps Header */}
      <div className="mb-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all ${
                step === 1 ? 'bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/30' : 'bg-emerald-500'
              }`}
            >
              {step > 1 ? '✓' : '1'}
            </div>
            <span className={`text-sm font-semibold ${step === 1 ? 'text-white' : 'text-gray-400'}`}>
              Medical Search
            </span>
          </div>

          <div className={`flex-1 h-1 mx-4 rounded ${step >= 2 ? 'bg-emerald-500' : 'bg-gray-700'}`}></div>

          <div className="flex items-center space-x-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all ${
                step === 2
                  ? 'bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/30'
                  : step > 2
                  ? 'bg-emerald-500'
                  : 'bg-gray-700'
              }`}
            >
              {step > 2 ? '✓' : '2'}
            </div>
            <span className={`text-sm font-semibold ${step === 2 ? 'text-white' : 'text-gray-400'}`}>
              Patient Profile
            </span>
          </div>

          <div className={`flex-1 h-1 mx-4 rounded ${step === 3 ? 'bg-blue-500' : 'bg-gray-700'}`}></div>

          <div className="flex items-center space-x-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all ${
                step === 3
                  ? 'bg-gradient-to-br from-blue-500 to-purple-600 animate-pulse shadow-lg shadow-blue-500/30'
                  : 'bg-gray-700'
              }`}
            >
              3
            </div>
            <span className={`text-sm font-semibold ${step === 3 ? 'text-white' : 'text-gray-400'}`}>
              AI Results
            </span>
          </div>
        </div>
      </div>

      {validationError && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-sm flex items-center gap-2">
          <span className="material-symbols-outlined">error</span>
          <span>{validationError}</span>
        </div>
      )}

      {/* Step 1: Medical Search */}
      {step === 1 && (
        <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 border border-white/10 shadow-2xl space-y-6">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent font-['Manrope'] mb-2">
              What treatment or consultation do you need?
            </h2>
            <p className="text-gray-400 text-sm">
              Our intelligent engine maps symptoms to specialized hospitals and verified tariffs.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-2">Medical Condition or Procedure</label>
            <input
              type="text"
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              placeholder="e.g., Heart Surgery, Cataract, Diabetes Treatment, Knee Replacement"
              className="w-full px-4 py-3.5 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
            />
            <p className="text-xs text-gray-400 mt-2">
              💡 Common searches: <button onClick={() => setCondition('Cardiology')} className="text-blue-400 hover:underline">Cardiology</button>, <button onClick={() => setCondition('Endocrinology')} className="text-blue-400 hover:underline">Diabetes</button>, <button onClick={() => setCondition('Orthopedics')} className="text-blue-400 hover:underline">Joint Care</button>
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-2">Location Preference</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="City or Area (e.g., Mumbai, Bengaluru, Delhi)"
              className="w-full px-4 py-3.5 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-2">Treatment Urgency</label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setUrgency('emergency')}
                className={`px-4 py-3 rounded-xl border text-center transition-all ${
                  urgency === 'emergency'
                    ? 'bg-red-500/20 border-red-500 text-red-300'
                    : 'bg-black/40 border-white/10 text-gray-400 hover:border-white/20'
                }`}
              >
                <span className="material-symbols-outlined text-red-400 text-2xl block mb-1">emergency</span>
                <span className="text-xs font-bold block">Emergency</span>
              </button>

              <button
                type="button"
                onClick={() => setUrgency('scheduled')}
                className={`px-4 py-3 rounded-xl border text-center transition-all ${
                  urgency === 'scheduled'
                    ? 'bg-blue-500/20 border-blue-500 text-blue-300'
                    : 'bg-black/40 border-white/10 text-gray-400 hover:border-white/20'
                }`}
              >
                <span className="material-symbols-outlined text-blue-400 text-2xl block mb-1">calendar_month</span>
                <span className="text-xs font-bold block">Scheduled</span>
              </button>

              <button
                type="button"
                onClick={() => setUrgency('flexible')}
                className={`px-4 py-3 rounded-xl border text-center transition-all ${
                  urgency === 'flexible'
                    ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                    : 'bg-black/40 border-white/10 text-gray-400 hover:border-white/20'
                }`}
              >
                <span className="material-symbols-outlined text-emerald-400 text-2xl block mb-1">schedule</span>
                <span className="text-xs font-bold block">Flexible</span>
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleGoToStep2}
            className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/30 transition-all text-sm transform hover:scale-[1.01]"
          >
            Continue to Patient Details →
          </button>
        </div>
      )}

      {/* Step 2: Patient Details */}
      {step === 2 && (
        <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 border border-white/10 shadow-2xl space-y-6">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent font-['Manrope'] mb-2">
              Patient Demographic Information
            </h2>
            <p className="text-gray-400 text-sm">
              We cross-reference this information to compute eligibility for PM-JAY and state healthcare assistance.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Patient legal name"
                className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Age</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="e.g. 45"
                className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900 border border-white/15 rounded-xl text-white focus:outline-none focus:border-blue-500 text-sm"
              >
                <option value="">Select Gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Income Category</label>
              <select
                value={income}
                onChange={(e) => setIncome(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900 border border-white/15 rounded-xl text-white focus:outline-none focus:border-blue-500 text-sm"
              >
                <option value="bpl">Below Poverty Line (BPL Card)</option>
                <option value="low">Low Income (&lt; ₹3L/year)</option>
                <option value="middle">Middle Income (₹3L - ₹12L/year)</option>
                <option value="high">High Income (&gt; ₹12L/year)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">State of Residence</label>
              <input
                type="text"
                value={state}
                onChange={(e) => setState(e.target.value)}
                placeholder="e.g., Maharashtra, Karnataka, Delhi"
                className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Aadhaar (Optional)</label>
              <input
                type="text"
                value={aadhaar}
                onChange={(e) => setAadhaar(e.target.value)}
                placeholder="XXXX-XXXX-XXXX"
                className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="py-3.5 px-6 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl text-sm transition-all"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={handleProcessSearch}
              className="flex-1 py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/30 transition-all text-sm transform hover:scale-[1.01]"
            >
              Find Best Healthcare Options →
            </button>
          </div>
        </div>
      )}

      {/* Step 3: AI Processing */}
      {step === 3 && (
        <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-12 border border-white/10 shadow-2xl text-center space-y-6">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto animate-pulse shadow-lg shadow-blue-500/40">
            <span className="material-symbols-outlined text-white text-4xl">psychology</span>
          </div>
          <h2 className="text-3xl font-bold text-white font-['Manrope']">MedSentinel AI is analyzing options...</h2>
          <p className="text-gray-400 text-sm">Matching hospital tariffs, distance, and government scheme qualifications...</p>

          <div className="space-y-3 max-w-md mx-auto pt-4 text-left">
            <div className="flex items-center gap-3 bg-black/30 p-3 rounded-xl border border-white/5">
              <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-ping"></div>
              <span className="text-xs text-gray-300">Comparing procedure tariffs across empanelled hospitals...</span>
            </div>
            <div className="flex items-center gap-3 bg-black/30 p-3 rounded-xl border border-white/5">
              <div className="w-2.5 h-2.5 bg-purple-500 rounded-full animate-ping"></div>
              <span className="text-xs text-gray-300">Evaluating Ayushman Bharat PM-JAY & state eligibility...</span>
            </div>
            <div className="flex items-center gap-3 bg-black/30 p-3 rounded-xl border border-white/5">
              <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-ping"></div>
              <span className="text-xs text-gray-300">Generating tailored recommendations & savings matrix...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
