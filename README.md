# NID-Egypt

A comprehensive FastAPI-based REST API for validating and extracting information from Egyptian National ID numbers. This service provides detailed validation, data extraction, and API management capabilities with built-in rate limiting and usage tracking.

## 🚀 Features

### Core Functionality
- **National ID Validation**: Validate 14-digit Egyptian National ID numbers
- **Data Extraction**: Extract comprehensive information including:
  - Date of birth and age calculation
  - Gender identification
  - Birth governorate and location
  - Sequence number and century
  - Checksum validation
- **Bulk Processing**: Support for validating multiple IDs in a single request
- **Comprehensive Error Handling**: Detailed validation errors and feedback

### API Management
- **Client Management**: Create and manage API clients with unique keys
- **Rate Limiting**: Configurable rate limiting per API key or IP address
- **Usage Tracking**: Detailed API usage analytics and monitoring
- **Authentication**: Secure API key-based authentication

### Technical Features
- **Async/Await**: Fully asynchronous FastAPI implementation
- **Database Support**: SQLAlchemy with async support (SQLite by default)
- **Pydantic Validation**: Strong data validation and serialization
- **CLI Tools**: Command-line interface for project management
- **Modular Architecture**: Clean separation of concerns with apps-based structure

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd NID-Egypt
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Linux/Mac
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./db.sqlite3

# Security Settings
SECRET_KEY=your-secret-key-here
API_JWT_SECRET=your-jwt-secret-here
API_JWT_ALGORITHM=HS256

# Rate Limiting
MAX_REQUESTS=10
WINDOW_SECONDS=60

# Application Settings
DEBUG=True
ALLOWED_HOSTS=["*"]
```

## 🚀 Running the Application

### Development Server
```bash
# Using the CLI tool
python cli.py runserver --reload

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server
```bash
# Using the CLI tool
python cli.py runserver --host 0.0.0.0 --port 8000 --workers 4

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔧 API Endpoints

### National ID Validation

#### Validate Single National ID
```http
POST /nid-egypt/
Content-Type: application/json
x-api-key: your-api-key

{
    "national_id": "29501011234567"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "national_id": "29501011234567",
        "is_valid": true,
        "date_of_birth": {
            "full_date": "1995-01-01",
            "year": 1995,
            "month": 1,
            "day": 1,
            "age": 29
        },
        "gender": "male",
        "location": {
            "governorate_code": "12",
            "governorate_name": "Dakahlia"
        },
        "sequence_number": "1234",
        "century": 1900,
        "errors": []
    },
    "message": "Validation completed successfully"
}
```

### Client Management

#### Create API Client
```http
POST /clients/
Content-Type: application/json

{
    "name": "My Application",
    "description": "Application for NID validation"
}
```

#### List API Clients
```http
GET /clients/
```

## 🏗️ Project Structure

```
NID-Egypt/
├── apps/                          # Application modules
│   ├── clients/                   # Client management app
│   │   ├── models.py             # Database models
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── services.py           # Business logic
│   │   ├── routes.py             # API endpoints
│   │   └── repos.py              # Data access layer
│   └── egypt_national_id/        # National ID validation app
│       ├── models.py             # Database models
│       ├── schemas.py            # Pydantic schemas & validation logic
│       ├── services.py           # Business logic
│       ├── routes.py             # API endpoints
│       └── repos.py              # Data access layer
├── bases/                         # Base classes and utilities
│   ├── base_orm.py               # Base ORM class
│   ├── business_logic.py         # Base business logic
│   ├── model.py                  # Base model class
│   ├── schema.py                 # Base schema class
│   └── session_manager.py        # Database session management
├── core/                          # Core application components
│   ├── app.py                    # FastAPI app configuration
│   ├── logger.py                 # Logging configuration
│   ├── middlewares.py            # Custom middlewares
│   ├── security.py               # Security utilities
│   └── settings.py               # Application settings
├── project_structure/             # Project templates
│   ├── app_template/             # App template for CLI
│   └── project_template/         # Project template for CLI
├── cli.py                        # Command-line interface
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🛠️ CLI Commands

The project includes a CLI tool for project management:

### Create New Project
```bash
python cli.py createproject my-new-project
```

### Create New App
```bash
# Feature-based structure (default)
python cli.py startapp my-new-app

# Type-based structure
python cli.py startapp my-new-app --tb
```

### Run Development Server
```bash
python cli.py runserver --host 0.0.0.0 --port 8000 --reload
```

## 🔒 Security Features

- **API Key Authentication**: Secure access using API keys
- **Rate Limiting**: Configurable rate limiting per client
- **Input Validation**: Comprehensive validation of all inputs
- **Error Handling**: Secure error responses without sensitive information

## 📊 Monitoring and Analytics

The application includes built-in usage tracking:

- **API Call Tracking**: Monitor all API calls with timestamps
- **Performance Metrics**: Track response times and status codes
- **Client Analytics**: Per-client usage statistics
- **Rate Limit Monitoring**: Track rate limit violations

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.

# Run specific test file
python -m pytest apps/egypt_national_id/tests.py
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
SECRET_KEY=your-production-secret-key
API_JWT_SECRET=your-production-jwt-secret
API_JWT_ALGORITHM=HS256
DEBUG=False
MAX_REQUESTS=100
WINDOW_SECONDS=3600
```


## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the code examples in the `tests/` directory


---

**Note**: This API is designed for educational and development purposes. For production use, ensure proper security measures and compliance with local regulations regarding personal data handling.