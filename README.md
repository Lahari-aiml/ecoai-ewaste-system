# EcoAI – Intelligent E-Waste Management System

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203-green.svg)](https://flask.palletsprojects.com/)
[![Machine Learning](https://img.shields.io/badge/AI%2FML-Scikit--Learn%20%26%20Deep%20Learning-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3%20(Normalized)-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/Academic-B.Tech%20CSE--AI%2FML-emerald.svg)]()

> **B.Tech Computer Science & Engineering (Artificial Intelligence & Machine Learning) Capstone Project**  
> An intelligent circular lifecycle disposition web platform that processes natural language electronic waste descriptions and categorizes them into **Repair**, **Reuse**, or **Recycle**, matches local service providers via Haversine distance calculations on interactive Leaflet maps, and manages doorstep e-waste collection.

---

## 📌 Project Overview

Millions of tons of toxic electronic waste enter municipal landfills annually, leaching hazardous heavy metals (lead, cadmium, mercury, flame retardants) into groundwater tables. Many discarded gadgets could be economically repaired or refurbished for students and charities.

**EcoAI** automates electronic waste disposition triage:
1. **User Description**: Users enter informal descriptions of electronic items (e.g. *"My old laptop switches on, but its screen is damaged and flickering."*).
2. **Dual-Model AI Inference**: 
   - **NLP Model**: Text cleaning, stopword removal, tokenization, and TF-IDF n-gram vectorization with calibrated probability output.
   - **Deep Learning Model**: Multi-Layer Perceptron (MLP) Neural Network architecture (`Input (3000 TF-IDF features) -> Dense(128, ReLU) -> Dense(64, ReLU) -> Softmax(3 classes)`).
   - **Ensemble Decision Engine**: Weighted consensus computation producing verifiable, real confidence percentages.
3. **Structured Advisory**: Delivers customized repair diagnostics, cryptographic data-wipe procedures, or hazardous handling directives stored dynamically in the database.
4. **Spatial Provider Matching**: Calculates exact straight-line distances using the mathematical **Haversine formula** in Python, displaying nearby centers on an interactive **Leaflet.js / OpenStreetMap** view.
5. **Doorstep Pickup Dispatch**: Enables users to schedule pickups from active providers, with lifecycle tracking (`Pending` → `Confirmed` → `Picked Up` → `Completed`).
6. **Role-Based Access Control**: Strict separation between authenticated **Users** and **System Administrators**.

---

## 🏗️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla ES6), Bootstrap 5.3, Bootstrap Icons |
| **Mapping & GIS** | Leaflet.js, OpenStreetMap, Browser Geolocation API |
| **Backend** | Python 3, Flask 3.1, Werkzeug (PBKDF2 Password Hashing) |
| **Production WSGI** | Waitress 3.0 (Windows/Cross-platform), Gunicorn (Linux/Cloud) |
| **Database** | SQLite3 (Normalized, Foreign Keys enabled, Indexed) |
| **NLP Pipeline** | Regex Tokenizer, Stopword Filter, TF-IDF Vectorizer (`ngram_range=(1,2)`) |
| **Machine Learning** | Calibrated Logistic Regression, Multinomial Classifiers |
| **Deep Learning** | Deep Neural Network (`128-64` Dense layers, ReLU activations, Softmax output) |
| **Distance Calculation**| Haversine Spherical Trigonometry in Pure Python |

---

## 🗂️ Project Architecture

```text
EcoAI/
├── app.py                      # Application factory, routes, and authentication
├── config.py                   # Configuration classes (Dev, Testing, Production)
├── wsgi.py                     # WSGI production entrypoint
├── server_production.py        # Production server runner (Waitress WSGI)
├── requirements.txt            # Python dependencies
├── Procfile                    # Cloud deployment runner (Render/Railway/Heroku)
├── render.yaml                 # Render cloud blueprint specification
├── Dockerfile                  # Containerized deployment specification
├── .dockerignore               # Docker ignore rules
├── run_app.ps1                 # Windows PowerShell quick-start launcher
├── run_app.bat                 # Windows CMD quick-start launcher
├── database/
│   ├── db.py                   # Connection management, query & execute helpers
│   ├── schema.sql              # Normalized DDL schema with foreign keys
│   └── seed.py                 # Initial data seeder (Categories, Demo data, Users)
├── model/
│   ├── dataset.py              # 180 curated e-waste training samples
│   ├── nlp_model.py            # Text preprocessor, TF-IDF, Calibrated NLP model
│   ├── deeplearning.py         # Deep Neural Network classifier (MLP with Softmax)
│   ├── train_model.py          # Standalone training & evaluation pipeline
│   ├── tfidf_vectorizer.pkl    # Serialized TF-IDF feature extractor
│   ├── nlp_classifier.pkl      # Serialized NLP model weights
│   └── dl_classifier.pkl       # Serialized Deep Learning model weights
├── services/
│   ├── classification_service.py # Singleton ensemble inference engine
│   ├── recommendation_service.py # Database-backed recommendation manager
│   ├── location_service.py     # Haversine distance calculator & spatial queries
│   └── pickup_service.py       # Pickup request lifecycle & transition validator
├── templates/
│   ├── base.html               # Master layout, navigation, alerts, footer
│   ├── index.html              # Landing page, 3 pillars, how-it-works, telemetry
│   ├── signup.html             # User registration with server validation
│   ├── login.html              # User login screen
│   ├── dashboard.html          # User dashboard with metrics & quick actions
│   ├── classify.html           # Interactive classification form with sample loader
│   ├── result.html             # Classification result card, confidence, instructions
│   ├── providers.html          # Nearby service providers & Leaflet map view
│   ├── pickup_request.html     # Doorstep pickup booking form
│   ├── my_pickups.html         # User pickup request tracking & cancellation
│   ├── history.html            # User-isolated prediction history table
│   ├── admin_login.html        # Dedicated administrator authentication
│   ├── admin_dashboard.html    # Admin KPI dashboard & quick management
│   ├── admin_users.html        # User account management (toggle status, delete)
│   ├── admin_predictions.html  # System-wide inference audit logs & search
│   ├── admin_categories.html   # 3R Category and recommendation directive CRUD
│   ├── admin_providers.html    # Service provider directory & GPS coordinates
│   └── admin_pickups.html      # Pickup dispatch manifest & status transition modal
├── static/
│   ├── css/
│   │   └── style.css           # Custom eco-friendly design system
│   ├── js/
│   │   └── main.js             # Geolocation, Leaflet map engine, sample loader
│   └── images/                 # Static graphical assets
└── tests/
    ├── test_app.py             # 13 core SRS scenario test cases
    ├── test_models.py          # NLP & Deep Learning model unit tests
    ├── test_services.py        # Location & pickup business logic tests
    └── test_routes.py          # Integration route tests
```

---

## 🔑 Default Credentials

The database is pre-seeded with two dedicated testing accounts:

| Role | Username | Email | Password | Access Area |
|---|---|---|---|---|
| **System Administrator** | `admin` | `admin@ecoai.org` | `Admin@EcoAI2026` | `/admin/login` & `/admin/dashboard` |
| **Demo Citizen / User** | `demo_user` | `demo@ecoai.org` | `User@EcoAI2026` | `/login` & `/dashboard` |

> *Note: Regular users cannot register as administrators via the signup form. Admin access is strictly enforced via database role verification (`role == 'admin'`).*

---

## 🚀 Running Locally (Windows / PowerShell)

### Method 1: Using the PowerShell Launcher (Recommended)
Open PowerShell in the project directory and run:
```powershell
.\run_app.ps1
```

### Method 2: Running via Python Directly
Using the system Python interpreter:
```powershell
& "C:\Users\medis\AppData\Local\Python\pythoncore-3.14-64\python.exe" server_production.py
```
Or with standard `python` if configured on your PATH:
```bash
python server_production.py
```

### Method 3: Development Mode with Live Debugger
```bash
python app.py
```

Access the application in your web browser at:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running the Automated Test Suite

EcoAI includes an automated test suite with **38 test cases** covering all 13 SRS specifications:

```powershell
& "C:\Users\medis\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m unittest discover tests/ -v
```

### Test Coverage Highlights:
- ✅ **Test 1**: User registration and login authentication
- ✅ **Test 2**: Duplicate email and username prevention
- ✅ **Test 3**: Protected page redirection for unauthorized users
- ✅ **Test 4**: Role-based access separation between User and Admin
- ✅ **Test 5**: AI classification with valid electronic descriptions
- ✅ **Test 6**: Server-side validation for empty/whitespace input
- ✅ **Test 7**: Database-backed recommendation retrieval
- ✅ **Test 8**: Haversine formula distance calculation and radius filtering
- ✅ **Test 9**: City coordinate fallback when GPS permission is unavailable
- ✅ **Test 10**: Doorstep pickup request submission with date/phone validation
- ✅ **Test 11**: Pickup request cancellation and state machine transitions
- ✅ **Test 12**: Cryptographic user data isolation in history and requests
- ✅ **Test 13**: Admin CRUD operations (Users, Providers, Categories, Pickups)

---

## 🌐 Cloud Deployment Options

### Option A: Deploy to Render (Recommended & Free)
1. Push your repository to GitHub or GitLab.
2. In [Render Dashboard](https://dashboard.render.com/), click **New** → **Web Service**.
3. Select your repository.
4. Set the following configuration:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python database/seed.py && python model/train_model.py`
   - **Start Command**: `python server_production.py`
5. Click **Create Web Service**. Render will provision your URL automatically!

*(Alternatively, use Render Blueprints with the included `render.yaml`)*

### Option B: Deploy with Docker
1. Build the container:
   ```bash
   docker build -t ecoai .
   ```
2. Run the container:
   ```bash
   docker run -d -p 5000:5000 --name ecoai-app ecoai
   ```
3. Open `http://localhost:5000` in your browser.

### Option C: Deploy to Railway / Heroku
The included `Procfile` automatically instructs Railway, Fly.io, or Heroku to launch:
```text
web: python server_production.py
```

---

## 🧠 AI / ML Pipeline Details

### Text Preprocessing
- Normalization (lowercasing, punctuation stripping, regex cleansing).
- Elimination of high-frequency English stopwords.
- Sublinear term-frequency scaling.

### NLP Model (TF-IDF + Calibrated Linear Classifier)
- Unigrams and bigrams (`ngram_range=(1, 2)`).
- Balanced class weights to account for disposition category parity.
- Platt scaling / calibrated probability distribution across `Repair`, `Reuse`, and `Recycle`.

### Deep Neural Network (MLP)
- Input: 3000-dimensional TF-IDF feature space.
- Hidden Layer 1: 128 units, ReLU activation function.
- Hidden Layer 2: 64 units, ReLU activation function.
- Output Layer: 3 units, Softmax activation function.
- Optimization: Adam optimizer with adaptive learning rate and early stopping.

### Model Comparison Diagnostic
On every classification result page, students and evaluators can view individual model performance side-by-side, verifying that predictions are genuine mathematical inferences rather than hardcoded rules.

---

## 🗺️ Mathematical Distance Calculation

The system implements the **Haversine Formula** in pure Python to calculate great-circle distances over the Earth's surface:

$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2\cdot\text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$
$$d = R \cdot c$$

Where:
- $\phi_1, \phi_2$ are the latitudes in radians.
- $\Delta\phi = \phi_2 - \phi_1$ and $\Delta\lambda = \lambda_2 - \lambda_1$.
- $R = 6371.0\text{ km}$ (Earth's mean spherical radius).

---

## 🛡️ Security Implementation
- **Password Protection**: Passwords securely hashed with `werkzeug.security.generate_password_hash` (PBKDF2-HMAC-SHA256).
- **Session Protection**: `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`.
- **SQL Injection Prevention**: 100% parameterized queries using SQLite placeholder syntax (`?`).
- **Role Isolation**: Strict backend check via `@admin_required` prevents privilege escalation.
- **Data Isolation**: All user-specific queries filter by `WHERE user_id = ?`.

---

## 🎓 Academic Viva & Project Demonstration Guide

When presenting to evaluators, showcase:
1. **Landing Page**: Environmental metrics dynamically generated from live database tables.
2. **AI Classification**: Enter *"Screen has vertical pink lines but phone boots and vibrates"* → Observes **Repair** outcome with ~80%+ confidence.
3. **Model Comparison**: Expand the AI Architecture Diagnostics section comparing the NLP TF-IDF classifier vs. the Deep Neural Network output.
4. **Geolocation & Map**: Open Nearby Providers, select **Bengaluru** or use GPS detection, inspect Leaflet markers and popup cards.
5. **Doorstep Pickup**: Book a collection date, observe the request in **My Pickups** with status `Pending`.
6. **Admin Panel**: Sign in as `admin`, navigate to **Pickup Dispatch**, confirm the request, update notes, and inspect user/provider CRUD features.
7. **Test Suite**: Run `python -m unittest discover tests/ -v` to prove complete code reliability.

---

*Developed for the B.Tech CSE (AI & ML) Academic Project Curriculum.*
