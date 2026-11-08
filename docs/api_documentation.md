# TravelSenseAI — REST API Specification & Reference Manual

**API Version:** 1.0.0  
**Base URL (Local Development):** `http://localhost:8000/api`  
**Base URL (Production Docker):** `http://localhost/api`  
**Interactive Swagger UI:** `http://localhost:8000/docs`  
**ReDoc Documentation:** `http://localhost:8000/redoc`  
**OpenAPI JSON Schema:** `http://localhost:8000/openapi.json`

---

## 1. Authentication & Security Protocols

### JWT Bearer Authentication
All protected endpoints require an HTTP `Authorization` header containing a valid JSON Web Token (JWT) issued upon successful login or registration:
```http
Authorization: Bearer <eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...>
```

### Standardized Error Format
All application errors follow RFC 7807 problem details semantics:
```json
{
  "status_code": 400,
  "error_code": "INVALID_COORDINATES",
  "message": "Latitude must be between -90 and 90, Longitude between -180 and 180",
  "details": null
}
```

---

## 2. API Endpoints Catalog

### 2.1 System Health & Discovery

#### `GET /api/health`
Checks operational health status, database connectivity, and external API responsiveness.
- **Access:** Public
- **Response (`200 OK`):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-11-04T12:00:00Z",
  "database": "connected",
  "environment": "production"
}
```

---

### 2.2 Authentication & User Profiles

#### `POST /api/auth/register`
Creates a new traveler user account with Argon2id password hashing.
- **Request Body:**
```json
{
  "email": "traveler@example.com",
  "password": "SecurePassword123!",
  "full_name": "Arjun Sharma",
  "preferred_currency": "INR",
  "home_city": "Hyderabad"
}
```
- **Response (`201 Created`):**
```json
{
  "id": 1,
  "email": "traveler@example.com",
  "full_name": "Arjun Sharma",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### `POST /api/auth/login`
Authenticates user credentials and issues an access token.
- **Request Body:**
```json
{
  "email": "traveler@example.com",
  "password": "SecurePassword123!"
}
```
- **Response (`200 OK`):** Returns token payload identical to registration.

#### `GET /api/users/profile`
Retrieves authenticated user profile and saved travel preferences.
- **Headers:** `Authorization: Bearer <token>`
- **Response (`200 OK`):**
```json
{
  "id": 1,
  "email": "traveler@example.com",
  "full_name": "Arjun Sharma",
  "preferred_interests": ["Heritage", "Food"],
  "default_budget": 5000.0,
  "created_at": "2026-11-04T10:00:00Z"
}
```

---

### 2.3 Destinations & Place Discovery

#### `GET /api/destinations/search`
Geocodes a destination name to coordinates with Geoapify.
- **Query Parameters:** `q=Hyderabad&limit=5`
- **Response (`200 OK`):**
```json
[
  {
    "name": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "latitude": 17.360589,
    "longitude": 78.474061,
    "formatted_address": "Hyderabad, Telangana, India"
  }
]
```

#### `GET /api/places/search`
Discovers tourist attractions or restaurants in proximity to coordinates.
- **Query Parameters:** `latitude=17.360589&longitude=78.474061&categories=tourism.attraction&radius_meters=15000&limit=10`
- **Response (`200 OK`):** Array of normalized place objects with opening hours and addresses.

#### `GET /api/places/{place_id}`
Retrieves enriched details for a specific place.

---

### 2.4 Routing & Road Optimization

#### `POST /api/routes/calculate`
Calculates driving distance, travel duration, and polyline geometry between waypoints via OpenRouteService.
- **Request Body:**
```json
{
  "coordinates": [
    {"latitude": 17.360589, "longitude": 78.474061},
    {"latitude": 17.383306, "longitude": 78.401833}
  ],
  "profile": "driving-car"
}
```
- **Response (`200 OK`):**
```json
{
  "distance_km": 11.2,
  "duration_minutes": 26.5,
  "geometry": [[17.360589, 78.474061], [17.383306, 78.401833]],
  "profile": "driving-car"
}
```

#### `POST /api/routes/optimize`
Applies Nearest-Neighbor and 2-Opt local search to find the shortest visiting sequence across POIs.
- **Request Body:**
```json
{
  "places": [
    {"id": "p1", "name": "Charminar", "latitude": 17.3616, "longitude": 78.4747},
    {"id": "p2", "name": "Golconda Fort", "latitude": 17.3833, "longitude": 78.4018},
    {"id": "p3", "name": "Salar Jung Museum", "latitude": 17.3713, "longitude": 78.4804}
  ],
  "transportation": "driving-car"
}
```
- **Response (`200 OK`):**
```json
{
  "ordered_points": [...],
  "original_distance_km": 36.92,
  "optimized_distance_km": 26.81,
  "distance_saved_km": 10.11,
  "improvement_percentage": 27.38
}
```

---

### 2.5 Weather Outlook

#### `GET /api/weather/forecast`
Fetches multi-day temperature, precipitation, and conditions from Open-Meteo.
- **Query Parameters:** `latitude=17.36&longitude=78.47&start_date=2026-11-10&end_date=2026-11-12`
- **Response (`200 OK`):**
```json
{
  "daily": [
    {
      "date": "2026-11-10",
      "temperature_max_c": 31.2,
      "temperature_min_c": 19.5,
      "precipitation_mm": 0.0,
      "condition": "Clear Sky",
      "is_outdoor_favorable": true
    }
  ]
}
```

---

### 2.6 Context-Aware Recommendations

#### `POST /api/recommendations/recommend`
Executes 6-factor contextual recommendation engine ($R(p_i) = \sum w_k x_{ik}$).
- **Request Body:**
```json
{
  "destination": "Hyderabad",
  "interests": ["Historical Places", "Food", "Photography"],
  "budget": 5000.0,
  "available_duration_days": 2,
  "transportation": "Car",
  "daily_touring_hours": 8.0,
  "limit": 5
}
```
- **Response (`200 OK`):**
```json
{
  "destination": "Hyderabad",
  "total_recommended": 5,
  "recommendations": [
    {
      "name": "Golconda Fort",
      "final_score": 0.884,
      "factors": {
        "preference": 1.0,
        "distance": 0.82,
        "time": 0.75,
        "weather": 0.95,
        "category": 1.0,
        "budget": 0.85
      },
      "explanation": "High preference alignment with Historical Places and Photography, with favorable sunny weather."
    }
  ]
}
```

---

### 2.7 Geographic Clustering

#### `POST /api/clustering/generate`
Groups POIs into spatial clusters using DBSCAN with haversine distance metric.
- **Request Body:**
```json
{
  "places": [
    {"id": "1", "name": "Charminar", "latitude": 17.3616, "longitude": 78.4747},
    {"id": "2", "name": "Mecca Masjid", "latitude": 17.3605, "longitude": 78.4735},
    {"id": "3", "name": "Golconda Fort", "latitude": 17.3833, "longitude": 78.4018}
  ],
  "eps_km": 3.0,
  "min_samples": 2
}
```
- **Response (`200 OK`):**
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "cluster_label": "Old City Heritage Corridor",
      "places_count": 2,
      "places": ["Charminar", "Mecca Masjid"]
    }
  ],
  "noise_places_count": 1
}
```

---

### 2.8 Itinerary Generation & Validation

#### `POST /api/itinerary/generate`
Generates an optimized, constraint-compliant multi-day itinerary.
- **Request Body:**
```json
{
  "destination": "Hyderabad",
  "start_date": "2026-11-10",
  "end_date": "2026-11-11",
  "num_travelers": 2,
  "budget": 5000.0,
  "interests": ["Heritage", "Food"],
  "transport_mode": "driving"
}
```
- **Response (`200 OK`):**
```json
{
  "itinerary_id": "itin_7f9c82",
  "destination": "Hyderabad",
  "utility_score": 0.862,
  "total_estimated_cost": 2180.0,
  "budget_surplus": 2820.0,
  "days": [
    {
      "day_number": 1,
      "date": "2026-11-10",
      "schedule": [
        {
          "place_name": "Golconda Fort",
          "arrival_time": "09:30",
          "departure_time": "12:00",
          "visit_duration_mins": 150,
          "cost": 100.0
        },
        {
          "place_name": "Lunch Break: Cafe Bahar",
          "arrival_time": "12:30",
          "departure_time": "13:30",
          "cost": 600.0
        }
      ]
    }
  ]
}
```

#### `POST /api/itinerary/validate`
Validates an itinerary plan for temporal conflicts, opening hour violations, and budget overruns.

---

### 2.9 Conversational AI Assistant & RAG

#### `POST /api/ai/extract-preferences`
Converts natural-language travel requests into structured JSON.
- **Request Body:**
```json
{
  "query": "I want a relaxed 2-day trip to Hyderabad for ₹5,000 interested in forts and biryani"
}
```
- **Response (`200 OK`):**
```json
{
  "destination": "Hyderabad",
  "duration_days": 2,
  "budget": 5000.0,
  "interests": ["forts", "biryani", "heritage", "food"],
  "travel_style": "relaxed",
  "needs_clarification": false
}
```

#### `POST /api/ai/chat`
Interacts with the LangGraph multi-node conversational assistant with RAG source grounding.
- **Request Body:**
```json
{
  "message": "What is the best time to visit Golconda Fort?",
  "session_id": "sess_user_1"
}
```
- **Response (`200 OK`):**
```json
{
  "reply": "Golconda Fort is best visited in the morning around 09:00 AM or late afternoon before the 06:30 PM sound and light show...",
  "intent": "general_qa",
  "sources": [
    {
      "title": "Golconda Fort & Acoustics",
      "source": "Archaeological Survey of India"
    }
  ]
}
```

---

### 2.10 PDF Reports & Travel Analytics

#### `POST /api/reports/generate`
Generates a downloadable ReportLab PDF travel dossier.
- **Request Body:** `{"itinerary_id": "itin_7f9c82"}`
- **Response (`200 OK`):**
```json
{
  "report_id": "rep_3b1a9e",
  "pdf_filename": "TravelSenseAI_Itinerary_Hyderabad.pdf",
  "download_url": "/api/reports/rep_3b1a9e/download",
  "file_size_bytes": 145820
}
```

#### `GET /api/reports/{report_id}/download`
Streams the binary PDF dossier to the client (`Content-Type: application/pdf`).

#### `GET /api/analytics/dashboard/{itinerary_id}`
Returns data for all 7 analytical charts (category distribution, factor scores, expense timeline, travel efficiency).
