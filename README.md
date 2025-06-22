# FastAPI + Angular Full Stack Project

This is a full stack application with a FastAPI backend and Angular frontend.

## Project Structure

```
project-root/
├── backend/         # FastAPI application
└── frontend/        # Angular application
```

## Backend Setup

1. Navigate to the backend directory:
```
cd backend
```

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run the application:
```
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## Frontend Setup

1. Navigate to the frontend directory:
```
cd frontend
```

2. Install dependencies:
```
npm install
```

3. Run the development server:
```
npm start
```

The application will be available at http://localhost:4200

## Development

- Backend API documentation: http://localhost:8000/docs
- Backend ReDoc: http://localhost:8000/redoc
- Frontend development server: http://localhost:4200

## Features

- RESTful API with FastAPI
- Angular frontend with components and services
- Item listing and detail views
- Responsive design
