'use client';

import React from 'react';
import Link from 'next/link';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 border-t border-gray-800 text-gray-400 py-12 px-6">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
        {/* Brand column */}
        <div>
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <span className="material-symbols-outlined text-white text-lg">health_and_safety</span>
            </div>
            <span className="text-xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent font-['Manrope']">
              MedSentinel
            </span>
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">
            Empowering patients with verified treatment costs, government scheme eligibility checks, and health insurance recommendations.
          </p>
        </div>

        {/* Quick Links */}
        <div>
          <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Explore</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="/hospitals" className="hover:text-blue-400 transition-colors">Hospital Directory</Link></li>
            <li><Link href="/comparison" className="hover:text-blue-400 transition-colors">Cost Comparison</Link></li>
            <li><Link href="/schemes" className="hover:text-blue-400 transition-colors">Government Schemes</Link></li>
            <li><Link href="/eligibility" className="hover:text-blue-400 transition-colors">Eligibility Calculator</Link></li>
          </ul>
        </div>

        {/* Services */}
        <div>
          <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Services</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="/insurances" className="hover:text-blue-400 transition-colors">Health Insurance Plans</Link></li>
            <li><Link href="/claims" className="hover:text-blue-400 transition-colors">Insurance Claim Filing</Link></li>
            <li><Link href="/appointments" className="hover:text-blue-400 transition-colors">Book Consultation</Link></li>
            <li><Link href="/medical-vault" className="hover:text-blue-400 transition-colors">Medical Records Vault</Link></li>
          </ul>
        </div>

        {/* Contact & Support */}
        <div>
          <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Support</h4>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center space-x-2">
              <span className="material-symbols-outlined text-base text-blue-400">call</span>
              <span>1800-MED-SENTINEL</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="material-symbols-outlined text-base text-blue-400">mail</span>
              <span>support@medsentinel.in</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="material-symbols-outlined text-base text-blue-400">verified_user</span>
              <span>PM-JAY & State Scheme Partner</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 text-xs text-gray-500">
        <p>© 2026 MedSentinel Technologies. All rights reserved.</p>
        <p>Built with Next.js, FastAPI, MySQL, and Secure JWT Authentication.</p>
      </div>
    </footer>
  );
};
