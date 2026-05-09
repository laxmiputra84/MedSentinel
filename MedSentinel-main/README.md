# MedSentinel - Healthcare Cost Comparison Platform

A full-stack web application for comparing healthcare costs across hospitals and checking government scheme eligibility.

## Features

- 🏥 Hospital Search & Comparison
- 💰 Cost Transparency Dashboard
- 🏛️ Government Scheme Eligibility Checker
- �️ **Insurance Plans** - Browse, compare, and enroll in health insurance plans
- 📋 **Insurance Claims** - File and track insurance claims
- �👤 User Profile & Saved Items
- 📊 Real-time Cost Analytics
- 🔍 Advanced Filtering System

## Tech Stack

**Frontend:**
- HTML5, CSS3, JavaScript
- Tailwind CSS
- Google Material Icons

**Backend:**
- Node.js
- Express.js
- SQLite3 Database

## Installation & Setup

### Prerequisites
- Node.js (v14 or higher)
- npm (Node Package Manager)

### Steps

1. **Navigate to project directory:**
   ```bash
   cd "d:\arena blitz\mini project\medsentinel"
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the server:**
   ```bash
   npm start
   ```

4. **Access the application:**
   Open your browser and go to:
   ```
   http://localhost:3000
   ```

## Project Structure

```
medsentinel/
├── public/
│   ├── index.html              # Landing page
│   ├── hospitals.html          # Hospital search
│   ├── hospital-details.html   # Hospital details
│   ├── schemes.html            # Government schemes
│   ├── eligibility.html        # Eligibility checker
│   ├── profile.html            # User profile
│   ├── comparison.html         # Cost comparison
│   ├── css/
│   │   └── styles.css          # Custom styles
│   └── js/
│       └── main.js             # Main JavaScript
├── server.js                   # Express server
├── package.json                # Dependencies
└── medsentinel.db             # SQLite database (auto-created)
```

## API Endpoints

### Hospitals
- `GET /api/hospitals` - Get all hospitals (with filters)
- `GET /api/hospitals/:id` - Get hospital by ID

### Schemes
- `GET /api/schemes` - Get all government schemes

### Users
- `POST /api/users` - Create user
- `GET /api/users/:id` - Get user by ID

### Saved Items
- `POST /api/saved-items` - Save hospital
- `GET /api/saved-items/:userId` - Get saved hospitals
- `DELETE /api/saved-items/:userId/:hospitalId` - Remove saved hospital

### Eligibility
- `POST /api/eligibility-check` - Check scheme eligibility

### Insurance
- `GET /api/insurances` - Get all insurance plans (with filters)
- `GET /api/insurances/:id` - Get insurance plan by ID
- `POST /api/user-insurances` - Enroll user in insurance plan
- `GET /api/user-insurances/:userId` - Get user's insurance plans
- `DELETE /api/user-insurances/:userInsuranceId` - Cancel insurance enrollment
- `POST /api/insurance-claims` - Submit insurance claim
- `GET /api/insurance-claims/:userId` - Get user's insurance claims
- `POST /api/insurance-eligibility` - Check insurance eligibility

## Usage

### Search Hospitals
1. Enter treatment or symptoms in search bar
2. Apply filters (distance, rating, schemes)
3. View detailed hospital information
4. Compare costs across hospitals

### Check Eligibility
1. Navigate to Schemes page
2. Click "Check Eligibility" on any scheme
3. Fill in household details
4. Get instant eligibility results

### Save Hospitals
1. Browse hospitals
2. Click "Save" button
3. Access saved items from Profile page

## Database Schema

### Hospitals Table
- id, name, location, specialization, rating, distance, cost_range, schemes, facilities

### Users Table
- id, name, email, phone, blood_group, allergies, emergency_contact, schemes

### Schemes Table
- id, name, description, coverage, eligibility, type

### Saved Items Table
- id, user_id, hospital_id, saved_at

## Troubleshooting

**Port already in use:**
```bash
# Change PORT in server.js or kill existing process
```

**Database not created:**
```bash
# Delete medsentinel.db and restart server
```

**MIME type errors:**
- Make sure you're accessing via `http://localhost:3000` not file://
- Don't use Live Server extension, use the Node.js server

## Future Enhancements

- User authentication & authorization
- Real-time chat with AI assistant
- Payment gateway integration
- Mobile app (React Native)
- Advanced analytics dashboard
- Multi-language support

## License

MIT License - Free to use for educational purposes

## Contact

For issues or questions, please create an issue in the repository.
