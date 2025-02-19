README 
# Medspa API

This is a **Django REST Framework (DRF)**-based API that allows users to manage **Medspas, Services, and Appointments**. It supports **user authentication, CRUD operations**, and **token-based authentication**.

---

## Features
- **User Authentication** (Token-based)
- **CRUD Operations** for:
  - Medspas
  - Services
  - Appointments
- **Filtering & Ordering**
- **Permissions & Authorization**
- **PostgreSQL Database** (Dockerized)

---

## Setup & Installation

### **1️⃣ Clone the Repository**
```bash

git clone git@github.com:Rene314159/medspa_project.git
cd medspa_project

2️⃣ Create a Virtual Environment
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate     # On Windows
3️⃣ Run the Project with Docker
docker-compose up -d  # Start PostgreSQL & Django in containers
docker-compose run web python manage.py makemigrations medspa_api
docker-compose run web python manage.py migrate
docker-compose run web python manage.py createsuperuser  # Create admin user
API Usage

Authentication

🔹 Obtain Auth Token
POST /api-token-auth/
Request Body:
{
    "email": "admin@example.com",
    "password": "yourpassword"
}
Response:
{
    "token": "your-generated-token"
}
Endpoints Overview
Resource	Endpoint	Methods	Description
Auth Token	/api-token-auth/	POST	Get user token
Medspas	/api/medspas/	GET, POST	List & create Medspas
Services	/api/services/	GET, POST	List & create Services
Appointments	/api/appointments/	GET, POST	List & create Appointments

Examples of API Calls

🔹 Create a Medspa
POST /api/medspas/
Authorization: Token your-token
{
    "name": "Luxury Spa",
    "address": "123 Spa St, City",
    "phone_number": "+123456789",
    "email": "contact@luxuryspa.com"
}
🔹 Create a Service
POST /api/services/
Authorization: Token your-token
{
    "medspa": "medspa-uuid",
    "name": "Facial Treatment",
    "description": "A relaxing facial treatment.",
    "price": 100.00,
    "duration": 60
}
🔹 Create an Appointment
POST /api/appointments/
Authorization: Token your-token
{
    "medspa": "medspa-uuid",
    "start_time": "2025-02-20T14:00:00Z",
    "service_ids": ["service-uuid-1", "service-uuid-2"]
}
🐳 Docker Commands
docker-compose down -v  # Reset database (CAUTION!)
docker-compose up -d  # Start project
docker-compose run web python manage.py createsuperuser  # Create admin
📝 Notes
• API requires authentication. Include your token in the Authorization header.
• UUIDs are required for medspa and service_ids.
• Use Postman or cURL for testing API endpoints.
📌 License

This project is for testing purposes. No license is included.

