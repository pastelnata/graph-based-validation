# Graph-based Validation System with LLM
A graph-based validation system that retrieves genome attributes and uses LLM assistance to infer
dependencies between them.

## How to Run the App Locally

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Start the FastAPI app:
   ```
   fastapi dev
   ```

This will launch the development server. Visit http://127.0.0.1:8000 in your browser.

## Run with Docker

1. Build the image:

   ```
   docker build -t graph-validation .
   ```

2. Run the container (foreground):

   ```
   docker run --rm -p 8000:8000 graph-validation
   ```

   Or run it in the background (detached):

   ```
   docker run -d -p 8000:8000 graph-validation
   ```

## Desired Project Structure

```
code/
├── app/                # Main application folder
│   ├── __init__.py
│   ├── main.py         # FastAPI app entry point
│   ├── dependencies.py # Shared dependencies for routes
│   ├── routers/        # API route modules
│   ├── core/           # Core settings and security
│   ├── schemas/        # Pydantic schemas for validation
│   ├── services/       # Business logic and helpers
├── tests/              # Test cases
├── .env                # Environment variables
├── .gitignore          # Git ignore rules
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── run.sh              # Script to run the app
```
