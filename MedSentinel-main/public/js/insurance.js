// Insurance Management Functions

async function getUserInsurances(userId) {
    try {
        const response = await fetch(`/api/user-insurances/${userId}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching user insurances:', error);
        return [];
    }
}

async function getInsuranceClaims(userId) {
    try {
        const response = await fetch(`/api/insurance-claims/${userId}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching insurance claims:', error);
        return [];
    }
}

async function submitInsuranceClaim(claimData) {
    try {
        const response = await fetch('/api/insurance-claims', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(claimData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error submitting claim:', error);
        throw error;
    }
}

async function enrollInInsurance(enrollmentData) {
    try {
        const response = await fetch('/api/user-insurances', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(enrollmentData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error enrolling in insurance:', error);
        throw error;
    }
}

async function checkInsuranceEligibility(eligibilityData) {
    try {
        const response = await fetch('/api/insurance-eligibility', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eligibilityData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error checking eligibility:', error);
        throw error;
    }
}

async function removeInsurance(userInsuranceId) {
    try {
        const response = await fetch(`/api/user-insurances/${userInsuranceId}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error removing insurance:', error);
        throw error;
    }
}

function displayUserInsurances(insurances) {
    if (!insurances || insurances.length === 0) {
        return '<p class="text-gray-400 text-center py-8">No active insurance plans. <a href="/insurances.html" class="text-blue-400 hover:text-blue-300">Explore plans</a></p>';
    }

    return insurances.map(insurance => `
        <div class="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-xl font-bold text-white">${insurance.name}</h3>
                    <p class="text-sm text-gray-400">${insurance.provider}</p>
                </div>
                <span class="px-3 py-1 bg-green-500/20 border border-green-400/30 rounded-full text-xs font-semibold text-green-300">${insurance.status}</span>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4 py-4 border-y border-white/10">
                <div>
                    <p class="text-xs text-gray-400 mb-1">Policy Number</p>
                    <p class="font-semibold text-blue-400">${insurance.policy_number}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-400 mb-1">Sum Insured</p>
                    <p class="font-semibold">₹${(insurance.sum_insured / 100000).toFixed(1)}L</p>
                </div>
                <div>
                    <p class="text-xs text-gray-400 mb-1">Coverage Start</p>
                    <p class="font-semibold">${new Date(insurance.coverage_start_date).toLocaleDateString()}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-400 mb-1">Coverage End</p>
                    <p class="font-semibold">${new Date(insurance.coverage_end_date).toLocaleDateString()}</p>
                </div>
            </div>

            <div class="grid grid-cols-3 gap-2">
                <button onclick="alert('Download policy details from your email or login to your insurance provider account')" class="px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-400/30 rounded-lg text-xs font-semibold text-blue-300 transition-all">Download Policy</button>
                <button onclick="navigateToClaimSubmission(${insurance.id})" class="px-3 py-2 bg-green-600/20 hover:bg-green-600/30 border border-green-400/30 rounded-lg text-xs font-semibold text-green-300 transition-all">File Claim</button>
                <button onclick="removeInsurancePlan(${insurance.id})" class="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-400/30 rounded-lg text-xs font-semibold text-red-300 transition-all">Remove</button>
            </div>
        </div>
    `).join('');
}

function displayInsuranceClaims(claims) {
    if (!claims || claims.length === 0) {
        return '<p class="text-gray-400 text-center py-8">No claims submitted yet.</p>';
    }

    return claims.map(claim => `
        <div class="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-lg font-bold text-white">Claim #${claim.id}</h3>
                    <p class="text-sm text-gray-400">${new Date(claim.claim_date).toLocaleDateString()}</p>
                </div>
                <span class="px-3 py-1 ${
                    claim.claim_status === 'approved' ? 'bg-green-500/20 text-green-300 border-green-400/30' :
                    claim.claim_status === 'rejected' ? 'bg-red-500/20 text-red-300 border-red-400/30' :
                    'bg-yellow-500/20 text-yellow-300 border-yellow-400/30'
                } border rounded-full text-xs font-semibold">${claim.claim_status.toUpperCase()}</span>
            </div>
            
            <div class="grid grid-cols-2 gap-4 py-4 border-y border-white/10">
                <div>
                    <p class="text-xs text-gray-400 mb-1">Claim Amount</p>
                    <p class="font-semibold text-blue-400">₹${claim.claim_amount.toLocaleString()}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-400 mb-1">Hospital ID</p>
                    <p class="font-semibold">${claim.hospital_id || 'N/A'}</p>
                </div>
            </div>

            <p class="text-sm text-gray-300 mt-4 mb-4">Description: ${claim.claim_description || 'No description provided'}</p>
            
            <button onclick="viewClaimDetails(${claim.id})" class="px-4 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-400/30 rounded-lg text-sm font-semibold text-blue-300 transition-all">View Details</button>
        </div>
    `).join('');
}

function navigateToClaimSubmission(insuranceId) {
    window.location.href = `/claim-submission.html?insurance_id=${insuranceId}`;
}

function removeInsurancePlan(insuranceId) {
    if (confirm('Are you sure you want to remove this insurance plan?')) {
        removeInsurance(insuranceId).then(() => {
            alert('Insurance plan removed successfully');
            location.reload();
        }).catch(err => {
            alert('Error removing insurance plan');
            console.error(err);
        });
    }
}

function viewClaimDetails(claimId) {
    alert(`Viewing claim details for claim #${claimId}\n\nThis would open a detailed view of the claim status and documents.`);
}

// Insurance Comparison Functions
async function compareInsurances(insuranceIds) {
    try {
        const promises = insuranceIds.map(id => fetch(`/api/insurances/${id}`).then(r => r.json()));
        return await Promise.all(promises);
    } catch (error) {
        console.error('Error comparing insurances:', error);
        throw error;
    }
}

function displayInsuranceComparison(insurances) {
    const comparisonTable = `
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead>
                    <tr class="border-b border-white/10">
                        <th class="px-4 py-3 text-left font-semibold">Feature</th>
                        ${insurances.map((i, idx) => `<th class="px-4 py-3 text-center font-semibold text-blue-400">${i.name}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    <tr class="border-b border-white/10">
                        <td class="px-4 py-3 font-semibold">Provider</td>
                        ${insurances.map(i => `<td class="px-4 py-3 text-center">${i.provider}</td>`).join('')}
                    </tr>
                    <tr class="border-b border-white/10">
                        <td class="px-4 py-3 font-semibold">Coverage Amount</td>
                        ${insurances.map(i => `<td class="px-4 py-3 text-center text-blue-400 font-semibold">₹${(i.coverage_amount / 100000).toFixed(1)}L</td>`).join('')}
                    </tr>
                    <tr class="border-b border-white/10">
                        <td class="px-4 py-3 font-semibold">Monthly Premium</td>
                        ${insurances.map(i => `<td class="px-4 py-3 text-center text-green-400 font-semibold">₹${i.premium_monthly.toLocaleString()}</td>`).join('')}
                    </tr>
                    <tr class="border-b border-white/10">
                        <td class="px-4 py-3 font-semibold">Annual Premium</td>
                        ${insurances.map(i => `<td class="px-4 py-3 text-center">₹${i.premium_annual.toLocaleString()}</td>`).join('')}
                    </tr>
                    <tr class="border-b border-white/10">
                        <td class="px-4 py-3 font-semibold">Waiting Period</td>
                        ${insurances.map(i => `<td class="px-4 py-3 text-center">${i.waiting_period_days} days</td>`).join('')}
                    </tr>
                    <tr class="border-b border-white/10">
                        <td class="px-4 py-3 font-semibold">Cashless Network</td>
                        ${insurances.map(i => `<td class="px-4 py-3 text-center text-blue-300">${i.cashless_network.toLocaleString()}+ hospitals</td>`).join('')}
                    </tr>
                    <tr>
                        <td class="px-4 py-3 font-semibold">Claim Settlement</td>
                        ${insurances.map(i => `<td class="px-4 py-3 text-center">${i.claim_settlement_days} days</td>`).join('')}
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    return comparisonTable;
}
