import dotenv from 'dotenv';
import express from 'express';
import sqlite3 from 'sqlite3';
import bodyParser from 'body-parser';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import multer from 'multer';
import fs from 'fs';


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001;

app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

const otpStore = {};
const verifiedPhones = {};

function generateOTP() {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

function cleanupOtps() {
  const now = Date.now();
  Object.keys(otpStore).forEach(phone => {
    if (otpStore[phone].expiresAt <= now) {
      delete otpStore[phone];
    }
  });
  Object.keys(verifiedPhones).forEach(phone => {
    if (verifiedPhones[phone] <= now) {
      delete verifiedPhones[phone];
    }
  });
}

async function sendSmsNotification(phone, message) {
  const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const authToken = process.env.TWILIO_AUTH_TOKEN;
  const fromNumber = process.env.TWILIO_PHONE_NUMBER;

  if (!accountSid || !authToken || !fromNumber) {
    console.log(`[SMS] Twilio not configured. SMS to ${phone}: ${message}`);
    return { success: false, reason: 'Twilio not configured' };
  }

  const payload = new URLSearchParams({
    To: phone,
    From: fromNumber,
    Body: message
  });

  try {
    const response = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`, {
      method: 'POST',
      headers: {
        Authorization: `Basic ${Buffer.from(`${accountSid}:${authToken}`).toString('base64')}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: payload.toString()
    });

    const result = await response.json();
    if (!response.ok) {
      console.error('Twilio SMS error:', result);
      return { success: false, reason: result.message || 'Twilio error' };
    }

    return { success: true, sid: result.sid };
  } catch (error) {
    console.error('Twilio request failed:', error);
    return { success: false, reason: error.message };
  }
}

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|pdf|doc|docx/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only images, PDFs, and documents are allowed.'));
    }
  }
});

// Serve uploaded files
app.use('/uploads', express.static(uploadsDir));
app.get('/', (req, res) => {
    res.sendFile(__dirname + '/public/login.html');
});

const db = new sqlite3.Database('./medsentinel.db', (err) => {
  if (err) console.error(err);
  else console.log('Database connected');
});

// Initialize database
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT,
    specialization TEXT,
    rating REAL,
    distance REAL,
    cost_range TEXT,
    schemes TEXT,
    image_url TEXT,
    facilities TEXT,
    hospital_type TEXT DEFAULT 'private'
  )`);

  // Add hospital_type column if it doesn't exist
  db.all("PRAGMA table_info(hospitals)", (err, columns) => {
    if (!err && columns && !columns.some(c => c.name === 'hospital_type')) {
      db.run('ALTER TABLE hospitals ADD COLUMN hospital_type TEXT DEFAULT "private"');
    }
  });

  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    password TEXT,
    blood_group TEXT,
    allergies TEXT,
    emergency_contact TEXT,
    schemes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    coverage TEXT,
    eligibility TEXT,
    type TEXT
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS saved_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    hospital_id INTEGER,
    saved_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS user_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    doc_type TEXT,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    preferred_date TEXT NOT NULL,
    preferred_time TEXT NOT NULL,
    department TEXT NOT NULL,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  db.run('CREATE UNIQUE INDEX IF NOT EXISTS idx_appointments_date_time ON appointments(preferred_date, preferred_time)');

  db.run(`CREATE TABLE IF NOT EXISTS insurances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    coverage_amount REAL,
    premium_monthly REAL,
    premium_annual REAL,
    coverage_type TEXT,
    inclusions TEXT,
    exclusions TEXT,
    eligibility_age_min INTEGER,
    eligibility_age_max INTEGER,
    waiting_period_days INTEGER,
    cashless_network INTEGER,
    claim_settlement_days INTEGER,
    features TEXT,
    image_url TEXT,
    rating REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS user_insurances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    insurance_id INTEGER,
    policy_number TEXT UNIQUE,
    enrollment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',
    coverage_start_date TEXT,
    coverage_end_date TEXT,
    sum_insured REAL,
    dependents TEXT
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS insurance_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    insurance_id INTEGER,
    claim_amount REAL,
    claim_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    hospital_id INTEGER,
    claim_status TEXT DEFAULT 'pending',
    claim_description TEXT,
    documents TEXT
  )`);

  // Ensure doc_type column exists for legacy databases
  db.all("PRAGMA table_info(user_documents)", (err, columns) => {
    if (!err && columns && !columns.some(c => c.name === 'doc_type')) {
      db.run('ALTER TABLE user_documents ADD COLUMN doc_type TEXT');
    }
  });

  // Insert sample data
  const hospitals = [
    // Private Hospitals (Higher cost)
    ['Apollo Multispeciality', 'Navi Mumbai', 'Multispecialty', 4.8, 2.4, '₹85,000 - ₹1,25,000', 'Ayushman Bharat (PM-JAY),ESIC,Arogya Karnataka', 'hospital1.jpg', '24/7 ER,ICU,Pharmacy', 'private'],
    ['Fortis Healthcare', 'Mulund West', 'Cardiology', 4.6, 5.1, '₹92,000 - ₹1,50,000', 'CGHS,Ayushman Bharat (PM-JAY),BPL Welfare', 'hospital2.jpg', '24/7 ER,Cardiac Lab', 'private'],
    ['Max Super Speciality', 'South Delhi', 'Multispecialty', 4.8, 1.2, '₹1,45,000 - ₹2,25,000', 'Ayushman Bharat (PM-JAY),CGHS,RSBY', 'hospital3.jpg', '24/7 ER,ICU,Diagnostics', 'private'],
    ['Manipal Hospitals', 'Whitefield', 'Cardiology', 4.9, 5.1, '₹1,82,000 - ₹2,80,000', 'Ayushman Bharat (PM-JAY),CGHS,Yashaswini Health Scheme', 'hospital4.jpg', 'Cardiac Care,ICU', 'private'],
    ['Narayana Health', 'Hosur Road', 'Cardiac', 4.7, 12, '₹1,15,000 - ₹1,75,000', 'Ayushman Bharat (PM-JAY),Senior Citizen Health Scheme', 'hospital5.jpg', 'Cardiac Surgery,ICU', 'private'],
    ['Kokilaben Dhirubhai Ambani Hospital', 'Mumbai', 'Surgery', 4.8, 8.5, '₹1,50,000 - ₹2,50,000', 'Ayushman Bharat (PM-JAY),Yashaswini Health Scheme', 'hospital9.jpg', 'Multi-specialty Surgery,ICU,24/7 ER', 'private'],
    ['Aster CMI Hospital', 'Hebbal, Bengaluru', 'Endocrinology', 4.6, 4.2, '₹75,000 - ₹1,10,000', 'Ayushman Bharat (PM-JAY),BPL Welfare', 'hospital6.jpg', 'Endocrine Care,24/7 ER,ICU,Diagnostic Lab', 'private'],
    ['Columbia Asia', 'Hebbal, Bengaluru', 'Orthopedics', 4.5, 4.8, '₹68,000 - ₹95,000', 'Ayushman Bharat (PM-JAY),CGHS,Arogya Karnataka', 'hospital7.jpg', 'Joint Care,Physiotherapy,Pharmacy', 'private'],
    ['Manipal Hospital', 'Whitefield, Bengaluru', 'General Medicine', 4.7, 5.0, '₹65,000 - ₹90,000', 'Ayushman Bharat (PM-JAY),ESIC', 'hospital8.jpg', 'Emergency Care,Pharmacy,Diagnostics', 'private'],

    // Government Hospitals (Lower cost)
    ['All India Institute of Medical Sciences (AIIMS)', 'New Delhi', 'Multispecialty', 4.5, 3.2, '₹15,000 - ₹35,000', 'Ayushman Bharat (PM-JAY),CGHS,Arogya Karnataka,Rashtriya Swasthya Bima Yojana (RSBY)', 'govt1.jpg', '24/7 ER,Government Schemes,Affordable Care', 'government'],
    ['Safdarjung Hospital', 'New Delhi', 'General Medicine', 4.2, 4.1, '₹8,000 - ₹25,000', 'Ayushman Bharat (PM-JAY),CGHS,ESIC,Senior Citizen Health Scheme', 'govt2.jpg', 'Emergency Care,Government Schemes,Low Cost', 'government'],
    ['Lok Nayak Jai Prakash Narayan Hospital', 'New Delhi', 'Multispecialty', 4.0, 5.5, '₹12,000 - ₹30,000', 'Ayushman Bharat (PM-JAY),CGHS,ESIC,BPL Welfare', 'govt3.jpg', 'Trauma Care,Emergency,Government Schemes', 'government'],
    ['Ram Manohar Lohia Hospital', 'New Delhi', 'Cardiology', 4.1, 6.2, '₹10,000 - ₹28,000', 'Ayushman Bharat (PM-JAY),CGHS,Arogya Karnataka,Senior Citizen Health Scheme', 'govt4.jpg', 'Cardiac Care,Emergency,Government Schemes', 'government'],
    ['Lady Hardinge Medical College', 'New Delhi', 'Maternity', 4.3, 7.1, '₹5,000 - ₹18,000', 'Ayushman Bharat (PM-JAY),CGHS,ESIC', 'govt5.jpg', 'Maternity Care,Women Health,Government Schemes', 'government'],
    ['Rajiv Gandhi Super Speciality Hospital', 'New Delhi', 'Surgery', 4.4, 8.3, '₹18,000 - ₹40,000', 'Ayushman Bharat (PM-JAY),CGHS,Arogya Karnataka,Rashtriya Swasthya Bima Yojana (RSBY)', 'govt6.jpg', 'Super Speciality Surgery,Emergency Care', 'government'],
    ['Guru Teg Bahadur Hospital', 'New Delhi', 'General Medicine', 3.9, 9.2, '₹6,000 - ₹20,000', 'Ayushman Bharat (PM-JAY),ESIC,CGHS,BPL Welfare', 'govt7.jpg', 'General Medicine,Emergency,Government Care', 'government'],
    ['Dr. Ram Manohar Lohia Hospital', 'New Delhi', 'Multispecialty', 4.1, 10.5, '₹14,000 - ₹32,000', 'Ayushman Bharat (PM-JAY),CGHS,Senior Citizen Health Scheme', 'govt8.jpg', 'Multi-specialty,Emergency,Government Schemes', 'government'],
    ['Batra Hospital & Medical Research Centre', 'New Delhi', 'Cancer Care', 4.2, 11.8, '₹25,000 - ₹55,000', 'Ayushman Bharat (PM-JAY),CGHS,Swasthya Sathi', 'govt9.jpg', 'Cancer Treatment,Emergency Care,Government Support', 'government'],
    ['Institute of Liver and Biliary Sciences', 'New Delhi', 'Hepatology', 4.3, 12.9, '₹20,000 - ₹45,000', 'Ayushman Bharat (PM-JAY),CGHS,Arogya Karnataka', 'govt10.jpg', 'Liver Diseases,Emergency Care,Government Schemes', 'government']
  ];

  hospitals.forEach(([name, location, specialization, rating, distance, cost_range, schemes, image_url, facilities, hospital_type]) => {
    db.run(
      `INSERT INTO hospitals (name, location, specialization, rating, distance, cost_range, schemes, image_url, facilities, hospital_type)
       SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
       WHERE NOT EXISTS (SELECT 1 FROM hospitals WHERE name = ?)`,
      [name, location, specialization, rating, distance, cost_range, schemes, image_url, facilities, hospital_type, name]
    );
  });

  db.all('SELECT id, schemes FROM hospitals', (err, rows) => {
    if (!err && rows) {
      const updateStmt = db.prepare('UPDATE hospitals SET schemes = ? WHERE id = ?');
      rows.forEach(({ id, schemes }) => {
        const normalized = schemes
          .split(',')
          .map((s) => s.trim())
          .map((s) => {
            if (s === 'Ayushman Bharat' || s === 'PMJAY') return 'Ayushman Bharat (PM-JAY)';
            return s;
          })
          .filter((v, i, arr) => arr.indexOf(v) === i)
          .join(',');
        if (normalized !== schemes) {
          updateStmt.run(normalized, id);
        }
      });
      updateStmt.finalize();
    }
  });

  const schemes = [
    ['Ayushman Bharat (PM-JAY)', 'Health cover of Rs. 5 lakhs per family per year', '₹5,00,000', 'Low income families (SECC 2011)', 'National'],
    ['Central Government Health Scheme (CGHS)', 'Medical cover for central government employees and pensioners', 'Comprehensive', 'Central govt employees and pensioners', 'National'],
    ['Employees\' State Insurance Scheme (ESIC)', 'Social security and health insurance for workers', 'Comprehensive', 'Employees earning up to ₹21,000/month', 'National'],
    ['MJPJAY Maharashtra', 'State health insurance for Maharashtra residents', '₹1,50,000', 'Yellow/Orange ration card holders', 'State'],
    ['Arogya Karnataka', 'Health insurance for Karnataka households', 'Up to ₹5,00,000', 'Karnataka residents below poverty line', 'State'],
    ['Rashtriya Swasthya Bima Yojana (RSBY)', 'Health insurance for below poverty line families', 'Up to ₹30,000', 'BPL card holders', 'National'],
    ['Swasthya Sathi', 'Health coverage scheme for West Bengal residents', 'Up to ₹5,00,000', 'West Bengal families', 'State'],
    ['Yashaswini Health Scheme', 'Healthcare cover for rural families in Karnataka', 'Up to ₹1,50,000', 'Karnataka rural families', 'State'],
    ['BPL Welfare', 'Government support for Below Poverty Line families', 'Subsidized treatment', 'BPL households', 'National'],
    ['Senior Citizen Health Scheme', 'Special medical support for older adults', 'Senior citizen benefits', 'Age 60+ citizens', 'National']
  ];

  const schemeStmt = db.prepare('INSERT OR IGNORE INTO schemes (name, description, coverage, eligibility, type) VALUES (?, ?, ?, ?, ?)');
  schemes.forEach(s => schemeStmt.run(s));
  schemeStmt.finalize();

  // Insert sample insurance data
  const insurances = [
    ['Apollo Health Insurance Premium', 'Apollo Insurance', 500000, 1299, 12999, 'Comprehensive', 'Hospitalization,OPD,Wellness,Maternity', 'Pre-existing (waiting period applies)', 18, 65, 90, 8000, 30, 'Cashless at 8000+ hospitals,24/7 claim support,Wellness benefits', 'insurance1.jpg', 4.7],
    ['Max Bupa Complete Health', 'Max Bupa', 750000, 1899, 18999, 'Family Floater', 'Hospitalization,Day Care,Critical Illness,Maternity', 'Non-medical expenses,Cosmetic procedures', 18, 75, 60, 10000, 45, 'Family coverage,Annual health checkup,24/7 assistance', 'insurance2.jpg', 4.6],
    ['HDFC Ergo Optima Health', 'HDFC Ergo', 1000000, 2499, 24999, 'Individual', 'Hospitalization,Pre/Post hospitalization,Ambulance,Dental', 'Waiting period exclusions,Adventure sports', 18, 80, 30, 7500, 21, 'No waiting period for accidents,Doorstep claim settlement', 'insurance3.jpg', 4.8],
    ['Aditya Birla Active Health', 'Aditya Birla Insurance', 400000, 999, 9999, 'Budget Friendly', 'Hospitalization,Day Care Procedures,Maternity', 'OPD services,Dental,Vision', 21, 65, 120, 5000, 30, 'Affordable premium,Network of 10000+ hospitals,Free health checkup', 'insurance4.jpg', 4.5],
    ['ICICI Lombard Complete Health', 'ICICI Lombard', 600000, 1599, 15999, 'Comprehensive', 'Hospitalization,OPD,Maternity,Critical Illness', 'Waiting period conditions apply', 18, 70, 90, 8500, 25, 'Customizable cover,Cashless at 9000+ hospitals', 'insurance5.jpg', 4.7],
    ['Bajaj Allianz Health Guard', 'Bajaj Allianz', 800000, 1999, 19999, 'Family', 'Hospitalization,Medical evacuation,Wellness', 'Pre-existing for first 12 months', 18, 75, 90, 7000, 35, 'Lifelong renewability,Health screening benefits', 'insurance6.jpg', 4.6],
    ['Star Health Secure Plus', 'Star Health', 500000, 1199, 11999, 'Comprehensive', 'Hospitalization,Day Care,Outpatient,Maternity', 'Non-medical treatments', 18, 70, 60, 6500, 30, 'Renewal without medical test,Bonus coverage', 'insurance7.jpg', 4.5]
  ];

  const insuranceStmt = db.prepare('INSERT OR IGNORE INTO insurances (name, provider, coverage_amount, premium_monthly, premium_annual, coverage_type, inclusions, exclusions, eligibility_age_min, eligibility_age_max, waiting_period_days, cashless_network, claim_settlement_days, features, image_url, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
  insurances.forEach(i => insuranceStmt.run(i));
  insuranceStmt.finalize();
});

// API Routes
const illnessSpecialtyMap = {
  diabetes: ['Endocrinology', 'General Medicine'],
  heart: ['Cardiology'],
  cardiac: ['Cardiology'],
  hypertension: ['Cardiology'],
  fever: ['General Medicine'],
  cough: ['General Medicine', 'Pulmonology'],
  cold: ['General Medicine'],
  pregnancy: ['Gynecology', 'Obstetrics'],
  maternity: ['Gynecology', 'Obstetrics'],
  kidney: ['Nephrology'],
  cancer: ['Oncology'],
  oncology: ['Oncology'],
  child: ['Pediatrics'],
  pediatric: ['Pediatrics'],
  surgery: ['Surgery', 'Multispecialty'],
  orthopedic: ['Orthopedics'],
  skin: ['Dermatology'],
  mental: ['Psychiatry'],
  asthma: ['Pulmonology']
};

const diagnosticSpecialtyMap = {
  diagnostics: ['Multispecialty', 'General Medicine'],
  diagnostic: ['Multispecialty', 'General Medicine'],
  mri: ['Multispecialty'],
  ct: ['Multispecialty'],
  xray: ['Multispecialty'],
  ultrasound: ['Multispecialty'],
  blood: ['Multispecialty', 'General Medicine'],
  lab: ['Multispecialty', 'General Medicine']
};

app.get('/api/hospitals', (req, res) => {
  const { search, specialization, maxDistance, minRating, scheme } = req.query;
  let query = 'SELECT * FROM hospitals WHERE 1=1';
  const params = [];

  if (search) {
    const lowerSearch = search.toLowerCase();
    const searchTerms = [`%${search}%`, `%${search}%`, `%${search}%`, `%${search}%`, `%${search}%`];
    query += ' AND (name LIKE ? OR location LIKE ? OR specialization LIKE ? OR schemes LIKE ? OR facilities LIKE ?';
    params.push(...searchTerms);

    Object.keys(illnessSpecialtyMap).forEach((key) => {
      if (lowerSearch.includes(key)) {
        illnessSpecialtyMap[key].forEach((tag) => {
          query += ' OR specialization LIKE ?';
          params.push(`%${tag}%`);
        });
      }
    });

    Object.keys(diagnosticSpecialtyMap).forEach((key) => {
      if (lowerSearch.includes(key)) {
        diagnosticSpecialtyMap[key].forEach((tag) => {
          query += ' OR specialization LIKE ?';
          params.push(`%${tag}%`);
        });
      }
    });

    query += ')';
  }
  if (specialization) {
    query += ' AND specialization LIKE ?';
    params.push(`%${specialization}%`);
  }
  if (maxDistance) {
    query += ' AND distance <= ?';
    params.push(maxDistance);
  }
  if (minRating) {
    query += ' AND rating >= ?';
    params.push(minRating);
  }
  if (scheme) {
    query += ' AND schemes LIKE ?';
    params.push(`%${scheme}%`);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.get('/api/hospitals/:id', (req, res) => {
  db.get('SELECT * FROM hospitals WHERE id = ?', [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(row);
  });
});

app.get('/api/schemes', (req, res) => {
  db.all('SELECT * FROM schemes', (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.post('/api/users', (req, res) => {
  const { name, email, phone, blood_group, allergies, emergency_contact } = req.body;
  db.run('INSERT INTO users (name, email, phone, blood_group, allergies, emergency_contact) VALUES (?, ?, ?, ?, ?, ?)',
    [name, email, phone, blood_group, allergies, emergency_contact],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ id: this.lastID });
    }
  );
});

app.get('/api/users/:id', (req, res) => {
  db.get('SELECT * FROM users WHERE id = ?', [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(row);
  });
});

app.post('/api/saved-items', (req, res) => {
  const { user_id, hospital_id } = req.body;
  db.run('INSERT INTO saved_items (user_id, hospital_id) VALUES (?, ?)',
    [user_id, hospital_id],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ id: this.lastID });
    }
  );
});

app.get('/api/saved-items/:userId', (req, res) => {
  db.all(`SELECT h.* FROM hospitals h 
          JOIN saved_items s ON h.id = s.hospital_id 
          WHERE s.user_id = ?`, [req.params.userId], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.delete('/api/saved-items/:userId/:hospitalId', (req, res) => {
  db.run('DELETE FROM saved_items WHERE user_id = ? AND hospital_id = ?',
    [req.params.userId, req.params.hospitalId],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true });
    }
  );
});

app.post('/api/eligibility-check', (req, res) => {
  const { familySize, location, income, conditions } = req.body;
  const eligible = [];
  
  if (income === 'low') {
    eligible.push({ scheme: 'Ayushman Bharat', probability: 94 });
  }
  if (location === 'urban' || location === 'rural') {
    eligible.push({ scheme: 'State Health Scheme', probability: 78 });
  }
  
  res.json({ eligible });
});

// Login endpoint
app.post('/api/login', (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ message: 'Email and password are required' });
  }

  db.get('SELECT id, name, email FROM users WHERE email = ? AND password = ?', 
    [email, password], 
    (err, row) => {
      if (err) {
        return res.status(500).json({ message: 'Database error' });
      }
      
      if (!row) {
        return res.status(401).json({ message: 'Invalid email or password' });
      }

      res.json({
        userId: row.id,
        name: row.name,
        email: row.email,
        message: 'Login successful'
      });
    }
  );
});

// Register endpoint
app.post('/api/register', (req, res) => {
  const { name, email, phone, password } = req.body;

  if (!name || !email || !phone || !password) {
    return res.status(400).json({ message: 'All fields are required' });
  }

  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return res.status(400).json({ message: 'Invalid email format' });
  }

  // Basic password validation
  if (password.length < 6) {
    return res.status(400).json({ message: 'Password must be at least 6 characters' });
  }

  db.run('INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)',
    [name, email, phone, password],
    function(err) {
      if (err) {
        if (err.message.includes('UNIQUE constraint failed')) {
          return res.status(400).json({ message: 'Email already registered' });
        }
        return res.status(500).json({ message: 'Registration failed' });
      }

      res.status(201).json({
        userId: this.lastID,
        name: name,
        email: email,
        message: 'Account created successfully'
      });
    }
  );
});

// Logout endpoint
app.post('/api/logout', (req, res) => {
  res.json({ message: 'Logged out successfully' });
});

// Document upload endpoint
app.post('/api/upload-document', upload.single('document'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const { originalname, filename, size, mimetype } = req.file;
  const userId = 1; // For now, using a default user ID

  const docType = req.body.docType || 'Other';
  db.run(
    'INSERT INTO user_documents (user_id, doc_type, filename, original_name, file_path, file_type, file_size) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [userId, docType, filename, originalname, `/uploads/${filename}`, mimetype, size],
    function(err) {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Failed to save document info' });
      }
      res.json({
        id: this.lastID,
        docType,
        filename: filename,
        originalName: originalname,
        filePath: `/uploads/${filename}`,
        fileType: mimetype,
        fileSize: size,
        message: 'Document uploaded successfully'
      });
    }
  );
});

// Get user documents endpoint
app.get('/api/user-documents/:userId', (req, res) => {
  const userId = req.params.userId;
  db.all('SELECT * FROM user_documents WHERE user_id = ? ORDER BY upload_date DESC', [userId], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Delete document endpoint
app.delete('/api/user-documents/:documentId', (req, res) => {
  const documentId = req.params.documentId;
  
  // First get the file path
  db.get('SELECT file_path FROM user_documents WHERE id = ?', [documentId], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    if (!row) {
      return res.status(404).json({ error: 'Document not found' });
    }

    // Delete the file from filesystem
    const filePath = path.join(__dirname, row.file_path);
    fs.unlink(filePath, (err) => {
      if (err) console.error('Error deleting file:', err);
    });

    // Delete from database
    db.run('DELETE FROM user_documents WHERE id = ?', [documentId], (err) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ message: 'Document deleted successfully' });
    });
  });
});

app.post('/api/send-otp', (req, res) => {
  const { phone } = req.body;
  if (!phone) {
    return res.status(400).json({ error: 'Phone number is required' });
  }

  cleanupOtps();
  const otp = generateOTP();
  otpStore[phone] = {
    otp,
    expiresAt: Date.now() + 5 * 60 * 1000 // 5 minutes
  };

  console.log(`OTP for ${phone}: ${otp}`);
  
  const isDevelopment = process.env.NODE_ENV !== 'production';
  const response = { message: 'OTP sent successfully', expiresIn: 300 };
  if (isDevelopment) {
    response.testOtp = otp;
  }
  res.json(response);
});

app.post('/api/verify-otp', (req, res) => {
  const { phone, otp } = req.body;
  if (!phone || !otp) {
    return res.status(400).json({ error: 'Phone number and OTP are required' });
  }

  cleanupOtps();
  const record = otpStore[phone];
  if (!record || record.otp !== otp) {
    return res.status(400).json({ error: 'Invalid or expired OTP' });
  }

  verifiedPhones[phone] = Date.now() + 5 * 60 * 1000; // allow booking for next 5 minutes
  delete otpStore[phone];
  res.json({ message: 'OTP verified successfully' });
});

app.post('/api/book-consultation', async (req, res) => {
  const { name, phone, email, preferredDate, preferredTime, department, reason } = req.body;
  if (!name || !phone || !email || !preferredDate || !preferredTime || !department) {
    return res.status(400).json({ error: 'All required booking fields must be filled' });
  }

  cleanupOtps();
  if (!verifiedPhones[phone] || verifiedPhones[phone] <= Date.now()) {
    return res.status(400).json({ error: 'Phone not verified. Please verify OTP before booking.' });
  }

  db.get(
    'SELECT id FROM appointments WHERE preferred_date = ? AND preferred_time = ?',
    [preferredDate, preferredTime],
    (err, row) => {
      if (err) {
        console.error('Booking availability check error:', err);
        return res.status(500).json({ error: 'Unable to check appointment availability' });
      }

      if (row) {
        return res.status(409).json({ error: 'This time slot is already booked. Please choose a different time.' });
      }

      const userId = 1; // Replace with authenticated user ID if available
      db.run(
        'INSERT INTO appointments (user_id, name, phone, email, preferred_date, preferred_time, department, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [userId, name, phone, email, preferredDate, preferredTime, department, reason],
        async function(err) {
          if (err) {
            console.error('Booking save error:', err);
            return res.status(500).json({ error: 'Failed to save booking' });
          }

          delete verifiedPhones[phone];
          const smsMessage = `Hi ${name}, your consultation for ${department} is booked on ${preferredDate} at ${preferredTime}. Thank you for choosing MedSentinel.`;
          const smsResult = await sendSmsNotification(phone, smsMessage);

          if (!smsResult.success) {
            return res.json({ message: 'Booking confirmed, but SMS was not sent.', smsInfo: smsResult.reason });
          }

          res.json({ message: 'Booking confirmed and SMS sent successfully.' });
        }
      );
    }
  );
});

app.get('/api/booked-timeslots', (req, res) => {
  const { date } = req.query;
  if (!date) {
    return res.status(400).json({ error: 'Date is required' });
  }

  db.all(
    'SELECT preferred_time FROM appointments WHERE preferred_date = ?',
    [date],
    (err, rows) => {
      if (err) {
        console.error('Booked timeslots error:', err);
        return res.status(500).json({ error: 'Unable to fetch booked time slots' });
      }
      res.json(rows.map(r => r.preferred_time));
    }
  );
});

// Insurance endpoints
app.get('/api/insurances', (req, res) => {
  const { search, coverage_type, maxPremium, minRating, provider } = req.query;
  let query = 'SELECT * FROM insurances WHERE 1=1';
  const params = [];

  if (search) {
    query += ' AND (name LIKE ? OR provider LIKE ? OR features LIKE ? OR inclusions LIKE ?)';
    const searchTerm = `%${search}%`;
    params.push(searchTerm, searchTerm, searchTerm, searchTerm);
  }

  if (coverage_type) {
    query += ' AND coverage_type LIKE ?';
    params.push(`%${coverage_type}%`);
  }

  if (maxPremium) {
    query += ' AND premium_monthly <= ?';
    params.push(maxPremium);
  }

  if (minRating) {
    query += ' AND rating >= ?';
    params.push(minRating);
  }

  if (provider) {
    query += ' AND provider LIKE ?';
    params.push(`%${provider}%`);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.get('/api/insurances/:id', (req, res) => {
  db.get('SELECT * FROM insurances WHERE id = ?', [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(row);
  });
});

app.post('/api/user-insurances', (req, res) => {
  const { user_id, insurance_id, policy_number, coverage_start_date, coverage_end_date, sum_insured, dependents } = req.body;
  
  db.run('INSERT INTO user_insurances (user_id, insurance_id, policy_number, coverage_start_date, coverage_end_date, sum_insured, dependents) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [user_id, insurance_id, policy_number, coverage_start_date, coverage_end_date, sum_insured, dependents],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ id: this.lastID, message: 'Insurance enrolled successfully' });
    }
  );
});

app.get('/api/user-insurances/:userId', (req, res) => {
  db.all(`SELECT i.*, ui.policy_number, ui.enrollment_date, ui.status, ui.coverage_start_date, ui.coverage_end_date, ui.sum_insured, ui.dependents 
          FROM insurances i 
          JOIN user_insurances ui ON i.id = ui.insurance_id 
          WHERE ui.user_id = ?`, [req.params.userId], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.get('/api/insurance-claims/:userId', (req, res) => {
  db.all('SELECT * FROM insurance_claims WHERE user_id = ? ORDER BY claim_date DESC', [req.params.userId], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.post('/api/insurance-claims', (req, res) => {
  const { user_id, insurance_id, claim_amount, hospital_id, claim_description } = req.body;
  
  db.run('INSERT INTO insurance_claims (user_id, insurance_id, claim_amount, hospital_id, claim_description) VALUES (?, ?, ?, ?, ?)',
    [user_id, insurance_id, claim_amount, hospital_id, claim_description],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ id: this.lastID, message: 'Claim submitted successfully', claim_status: 'pending' });
    }
  );
});

app.post('/api/insurance-eligibility', (req, res) => {
  const { age, income_range, family_size, pre_existing_conditions } = req.body;
  const eligible = [];

  db.all('SELECT * FROM insurances', (err, insurances) => {
    if (err) return res.status(500).json({ error: err.message });

    insurances.forEach(insurance => {
      let eligibilityScore = 100;
      
      if (age < insurance.eligibility_age_min || age > insurance.eligibility_age_max) {
        eligibilityScore -= 50;
      }

      if (pre_existing_conditions && insurance.waiting_period_days > 180) {
        eligibilityScore -= 20;
      }

      if (eligibilityScore >= 50) {
        eligible.push({
          id: insurance.id,
          name: insurance.name,
          provider: insurance.provider,
          eligibility_score: eligibilityScore,
          recommended: eligibilityScore >= 80
        });
      }
    });

    res.json({ eligible: eligible.sort((a, b) => b.eligibility_score - a.eligibility_score) });
  });
});

app.delete('/api/user-insurances/:userInsuranceId', (req, res) => {
  db.run('DELETE FROM user_insurances WHERE id = ?', [req.params.userInsuranceId], (err) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true, message: 'Insurance removed successfully' });
  });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
