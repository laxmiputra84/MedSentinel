
// Main JavaScript for MedSentinel

const API_BASE = 'http://localhost:3001/api';

// Authentication Check - Run on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
});

// Check if user is logged in, redirect to login if not
function checkAuthentication() {
    const isLoggedIn = localStorage.getItem('loggedIn');
    const currentPage = window.location.pathname;
    
    // Pages that require authentication
    const protectedPages = [
        '/index.html',
        '/hospitals.html',
        '/schemes.html',
        '/insurances.html',
        '/insurance-details.html',
        '/claim-submission.html',
        '/comparison.html',
        '/profile.html',
        '/book-consultation.html',
        '/eligibility.html',
        '/hospital-details.html',
        '/search-flow.html'
    ];
    
    // Check if current page is protected
    if (protectedPages.includes(currentPage) || currentPage === '/') {
        if (!isLoggedIn || isLoggedIn !== 'true') {
            // Redirect to login page
            window.location.href = '/login.html';
            return;
        }
    }
}

// Logout function
function logout() {
    localStorage.removeItem('loggedIn');
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
    
    // Make API call to logout
    fetch(`${API_BASE}/logout`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).catch(err => console.log('Logout API called'));
    
    // Redirect to login
    window.location.href = '/login.html';
}

// Search functionality
async function searchHospitals() {
    const query = document.getElementById('searchInput').value.trim();
    if (query) {
        window.location.href = `/hospitals.html?search=${encodeURIComponent(query)}`;
    }
}

function openSearchFlow() {
    const query = document.getElementById('searchInput').value.trim();
    if (query) {
        window.location.href = `/hospitals.html?search=${encodeURIComponent(query)}`;
    } else {
        window.location.href = '/search-flow.html';
    }
}

function quickSearch(category) {
    window.location.href = `/hospitals.html?search=${encodeURIComponent(category)}`;
}

// Location functionality
function showLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                try {
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`);
                    const data = await response.json();
                    const place = data.display_name || `${latitude}, ${longitude}`;
                    alert(`Your location: ${place}`);
                } catch (err) {
                    alert(`Your location: ${latitude}, ${longitude}`);
                }
            },
            (error) => {
                alert('Location access denied. Please enable location services.');
            }
        );
    } else {
        alert('Geolocation is not supported by your browser.');
    }
}

// AI Chatbot responses
const chatbotResponses = {
    // Hospital related
    'nearby|near me|closest|nearest': {
        keywords: ['nearby', 'near me', 'closest', 'nearest', 'near'],
        response: 'Looking for hospitals near you? 🏥\n\nIf you are in Bengaluru, Karnataka, these hospitals are great nearby options:\n• Narayana Health, Hosur Road\n• Aster CMI Hospital, Hebbal\n• Columbia Asia, Hebbal\n• Manipal Hospital, Whitefield\n\nUse the location button on the top of the page to get your live nearby search and find the best hospital for your treatment.'
    },
    'hospital|find|location': {
        keywords: ['hospital', 'find', 'location', 'closest', 'nearby'],
        response: 'I can help you find hospitals! 🏥\n\n📍 We have 10,000+ verified hospitals in our network.\n\nYou can:\n• Search by location (City/Area)\n• Filter by specialization (Cardiology, Orthopedics, etc.)\n• Compare by price and ratings\n• Check bed availability\n\nUse the location icon next to Profile to find hospitals closest to you.\n\nWhat type of hospital or treatment are you looking for?'
    },
    
    // Scheme and eligibility
    'scheme|eligibility|coverage|ayushman|pmjay': {
        keywords: ['scheme', 'eligibility', 'covered', 'coverage', 'ayushman', 'pmjay', 'esic', 'cghs', 'insurance'],
        response: 'I\'ll help you understand your healthcare coverage! 💳\n\n🏛️ Government Schemes Available:\n• Ayushman Bharat (₹5 Lakhs coverage)\n• PMJAY (PM-JAY)\n• ESIC (Employee coverage)\n• CGHS (Central Government)\n\n✅ Our app helps you:\n• Check eligibility instantly\n• See which hospitals accept your scheme\n• Understand coverage limits\n\nTo check your eligibility, visit our Eligibility page. What scheme do you have?'
    },
    
    // Cost and pricing
    'cost|price|affordable|cheap|expensive|compare': {
        keywords: ['cost', 'price', 'how much', 'affordable', 'expensive', 'compare', 'cheap', 'expensive'],
        response: 'Let\'s find affordable treatment options! 💰\n\n💡 Cost Comparison Features:\n• Compare prices across 10,000+ hospitals\n• See transparent pricing for procedures\n• Find most affordable options\n• Check for discounts and offers\n\nCommon procedures:\n• General checkup: ₹500-₹1,500\n• Blood test: ₹300-₹800\n• Ultrasound: ₹800-₹2,000\n• Consultation: ₹300-₹1,000\n\nWhat procedure are you interested in?'
    },
    
    // Symptoms and health issues
    'symptom|fever|pain|cough|cold|headache|diabetes|heart|bp|blood pressure|cancer|covid|disease|illness|sick|health': {
        keywords: ['symptom', 'fever', 'pain', 'cough', 'cold', 'headache', 'diabetes', 'heart', 'bp', 'blood pressure', 'cancer', 'covid', 'disease', 'illness', 'sick', 'health', 'ache', 'tired'],
        response: 'I understand your health concerns. 🏥\n\n⚠️ Important: For serious health issues, please consult a medical professional immediately.\n\n💊 Common Treatments:\n• Fever/Cold: Consult General Physician\n• Chest pain: Cardiology\n• Diabetes: Endocrinology\n• Headaches: Neurology\n• Orthopedic issues: Orthopedic Surgery\n\n� Looking for hospitals for your condition?\n• Search hospitals for diabetes here: /hospitals.html?search=diabetes\n\n�📞 You can:\n• Book online consultation immediately\n• Find specialists nearby\n• Get appointment in 24 hours\n\nWhat health issue are you experiencing?'
    },
    
    // Doctor and specialist consultation
    'doctor|consultant|specialist|appointment|book|consultation|online': {
        keywords: ['doctor', 'consultant', 'specialist', 'appointment', 'book', 'consultation', 'online', 'meeting'],
        response: 'Book your consultation easily! 📋\n\n👨‍⚕️ Doctor Booking Features:\n• Online video consultations available\n• In-person appointments\n• Choose your preferred time\n• Get consultation within 24 hours\n• Prescription delivery at home\n\n🏥 Specialties Available:\n• General Medicine\n• Cardiology\n• Orthopedics\n• Pediatrics\n• Psychiatry\n• Dermatology\n• And many more!\n\nClick "Book Consultation" to get started!'
    },
    
    // Emergency
    'emergency|urgent|critical|accident|ambulance|911': {
        keywords: ['emergency', 'urgent', 'critical', 'accident', 'ambulance', '911', 'help', 'immediately'],
        response: 'MEDICAL EMERGENCY? 🚨\n\n☎️ IMMEDIATE ACTIONS:\n1. Call 911 or local emergency number\n2. Visit nearest hospital emergency room\n3. Our app helps find emergency care nearby\n\n🏥 Our Emergency Features:\n• Locate 24/7 emergency hospitals\n• Ambulance availability check\n• Pre-register for faster admission\n• Emergency contact info\n\nIf you\'re not in immediate danger, I can help find emergency facilities nearby!'
    },
    
    // Medicine and medication
    'medicine|drug|medication|tablet|injection|prescription': {
        keywords: ['medicine', 'drug', 'medication', 'tablet', 'injection', 'prescription', 'medicine'],
        response: 'Medicine Information 💊\n\n⚠️ Disclaimer: Consult your doctor before taking any medicine.\n\n📖 Our Medicine Features:\n• Medicine comparison\n• Generic vs branded options\n• Multiple pharmacy options\n• Online prescription required\n• Home delivery available\n\n💡 Tips:\n• Always take medicines as prescribed\n• Don\'t self-medicate\n• Check expiry dates\n• Store properly\n\nDo you need help finding a specific medicine?'
    },
    
    // Preventive care
    'prevent|checkup|wellness|vaccine|screening|health check|healthy': {
        keywords: ['prevent', 'checkup', 'wellness', 'vaccine', 'screening', 'health check', 'healthy', 'fitness', 'nutrition'],
        response: 'Preventive Healthcare 💪\n\n🏃 Wellness Services:\n• Regular health checkups\n• Health screening packages\n• Vaccination services\n• Fitness consultations\n• Nutrition planning\n\n📋 Checkup Packages:\n• Basic health checkup\n• Comprehensive health screening\n• Cardiac health assessment\n• Diabetes screening\n• Cancer screening\n\n💡 Prevention is better than cure!\nWould you like to book a checkup?'
    }
};

// Get chatbot response based on message
function getResponse(message) {
    const lower = message.toLowerCase();
    
    for (const key in chatbotResponses) {
        const data = chatbotResponses[key];
        for (const keyword of data.keywords) {
            if (lower.includes(keyword)) {
                return data.response;
            }
        }
    }
    
    // Default helpful response
    return 'I\'m here to help! 😊\n\n📍 You can ask me about:\n✓ Finding hospitals near you\n✓ Healthcare schemes & eligibility\n✓ Treatment costs & comparisons\n✓ Booking doctor consultations\n✓ Health issues & symptoms\n✓ Medicines & prescriptions\n✓ Preventive health checkups\n✓ Emergency services\n\nWhat can I help you with today?';
}

// Add message to chat
function addMessage(text, isUser) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex ' + (isUser ? 'justify-end' : 'justify-start');
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'max-w-xs p-3 rounded-lg ' + (isUser ? 'bg-blue-600 text-white' : 'bg-white text-gray-800 shadow-sm');
    
    const senderSpan = document.createElement('p');
    senderSpan.className = 'text-xs font-semibold ' + (isUser ? 'text-blue-100' : 'text-blue-600');
    senderSpan.textContent = isUser ? 'You' : 'MedSentinel';
    
    const textSpan = document.createElement('p');
    textSpan.className = 'text-sm mt-1';
    textSpan.textContent = text;
    
    contentDiv.appendChild(senderSpan);
    contentDiv.appendChild(textSpan);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send message from chat
function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    if (!message) return;
    
    addMessage(message, true);
    chatInput.value = '';
    
    // Simulate AI thinking
    setTimeout(() => {
        const response = getResponse(message);
        addMessage(response, false);
    }, 500);
}

// Close chat modal
function closeChat() {
    const chatModal = document.getElementById('chatModal');
    if (chatModal) {
        chatModal.remove();
    }
}

// Chat functionality - Create modal overlay
function openChat() {
    // Create modal backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-50';
    backdrop.id = 'chatModal';
    backdrop.onclick = (e) => {
        if (e.target === backdrop) closeChat();
    };
    
    backdrop.innerHTML = `
        <div class="bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 h-screen max-h-screen sm:h-auto sm:max-h-96 flex flex-col">
            <!-- Header -->
            <div class="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 flex items-center justify-between rounded-t-lg">
                <div>
                    <h2 class="text-lg font-bold">MedSentinel AI Assistant</h2>
                    <p class="text-xs opacity-90">Powered by Healthcare AI</p>
                </div>
                <button onclick="closeChat()" class="text-white hover:bg-blue-800 p-2 rounded-lg transition-all">
                    <span class="material-symbols-outlined text-xl">close</span>
                </button>
            </div>
            
            <!-- Messages Area -->
            <div id="chatMessages" class="flex-1 p-4 overflow-y-auto space-y-3 bg-gray-50">
                <div class="flex justify-start">
                    <div class="bg-white p-3 rounded-lg shadow-sm max-w-xs">
                        <p class="text-sm font-semibold text-blue-600">MedSentinel</p>
                        <p class="text-sm mt-1">Hello! I'm your healthcare assistant. I can help you with:</p>
                        <ul class="mt-2 text-sm space-y-1 text-gray-700">
                            <li>✓ Finding hospitals near you</li>
                            <li>✓ Checking scheme eligibility</li>
                            <li>✓ Comparing treatment costs</li>
                            <li>✓ Booking consultations</li>
                            <li>✓ Health information</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Input Area -->
            <div class="p-4 border-t bg-white rounded-b-lg">
                <div class="flex gap-2">
                    <input type="text" id="chatInput" placeholder="Ask me anything..." class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-black placeholder-gray-400">
                    <button onclick="sendChatMessage()" class="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition-all">Send</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(backdrop);
    
    // Focus on input
    setTimeout(() => {
        const input = document.getElementById('chatInput');
        if (input) {
            input.focus();
            // Add Enter key listener
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendChatMessage();
                }
            });
        }
    }, 100);
}

// Load schemes on homepage
async function loadHomeSchemes() {
    try {
        const response = await fetch(`${API_BASE}/schemes`);
        const schemes = await response.json();
        
        const grid = document.getElementById('schemesGrid');
        if (grid) {
            grid.innerHTML = schemes.slice(0, 3).map((s, index) => {
                const colors = [
                    { from: 'from-blue-600', to: 'to-blue-700', badge: 'bg-blue-500' },
                    { from: 'from-purple-600', to: 'to-purple-700', badge: 'bg-purple-500' },
                    { from: 'from-green-600', to: 'to-green-700', badge: 'bg-green-500' }
                ];
                const color = colors[index];
                
                return `
                <div class="group bg-gradient-to-br ${color.from} ${color.to} text-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 relative overflow-hidden">
                    <!-- Decorative Background -->
                    <div class="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
                    <div class="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
                    
                    <div class="relative z-10">
                        <div class="flex items-center justify-between mb-4">
                            <span class="${color.badge} text-white text-xs font-bold px-3 py-1.5 rounded-lg uppercase tracking-wide">${s.type}</span>
                            <span class="material-symbols-outlined text-white/80 text-3xl">verified</span>
                        </div>
                        <h3 class="text-2xl font-bold mb-3 leading-tight">${s.name}</h3>
                        <p class="text-white/90 text-sm mb-6 leading-relaxed">${s.description}</p>
                        
                        <!-- Coverage Badge -->
                        <div class="bg-white/20 backdrop-blur-sm rounded-xl p-3 mb-6 border border-white/30">
                            <div class="text-xs text-white/80 mb-1">Coverage</div>
                            <div class="text-lg font-bold">${s.coverage}</div>
                        </div>
                        
                        <a href="/schemes.html" class="inline-flex items-center space-x-2 bg-white text-gray-900 px-6 py-3 rounded-xl font-bold hover:shadow-xl transition-all group-hover:scale-105">
                            <span>Learn More</span>
                            <span class="material-symbols-outlined text-lg">arrow_forward</span>
                        </a>
                    </div>
                </div>
            `}).join('');
        }
    } catch (error) {
        console.error('Error loading schemes:', error);
    }
}

// Load hospitals on homepage
async function loadHomeHospitals() {
    try {
        const response = await fetch(`${API_BASE}/hospitals`);
        const hospitals = await response.json();
        
        // Hospital placeholder images from Unsplash
        const hospitalImages = [
            'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=400&h=300&fit=crop',
            'https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=400&h=300&fit=crop',
            'https://images.unsplash.com/photo-1516549655169-df83a0774514?w=400&h=300&fit=crop'
        ];
        
        const grid = document.getElementById('hospitalsGrid');
        if (grid) {
            grid.innerHTML = hospitals.slice(0, 3).map((h, index) => `
                <div class="group bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-2xl transition-all duration-300 border border-gray-100 hover:border-blue-200 hover:-translate-y-2">
                    <div class="h-48 bg-gradient-to-br from-blue-100 to-blue-200 relative overflow-hidden">
                        <img src="${hospitalImages[index]}" alt="${h.name}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" onerror="this.src='https://via.placeholder.com/400x300/3b82f6/ffffff?text=Hospital'">
                        <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
                        <div class="absolute top-4 right-4 bg-white/95 backdrop-blur-sm px-3 py-1.5 rounded-full text-xs font-bold text-green-600 flex items-center gap-1 shadow-lg">
                            <span class="material-symbols-outlined text-sm">star</span> ${h.rating}
                        </div>
                    </div>
                    <div class="p-6">
                        <h3 class="text-xl font-bold text-gray-900 mb-3 group-hover:text-blue-600 transition-colors">${h.name}</h3>
                        <div class="space-y-2.5 mb-6">
                            <div class="flex items-center gap-2 text-gray-600 text-sm">
                                <span class="material-symbols-outlined text-base text-blue-600">location_on</span>
                                <span>${h.location}</span>
                            </div>
                            <div class="flex items-center gap-2 text-gray-600 text-sm">
                                <span class="material-symbols-outlined text-base text-green-600">payments</span>
                                <span>Starting at <span class="font-bold text-gray-900">${h.cost_range}</span></span>
                            </div>
                        </div>
                        <div class="flex flex-wrap gap-2 mb-6">
                            ${h.schemes.split(',').slice(0, 2).map(s => `
                                <span class="text-xs font-semibold px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg border border-blue-100">${s.trim()}</span>
                            `).join('')}
                        </div>
                        <a href="/hospital-details.html?id=${h.id}" class="block w-full py-3.5 text-center rounded-xl bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold hover:shadow-lg hover:scale-105 transition-all">View Details →</a>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading hospitals:', error);
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

function init() {
    // Load data for homepage
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        loadHomeSchemes();
        loadHomeHospitals();
    }
    
    // Add enter key support for search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchHospitals();
            }
        });
    }
}
