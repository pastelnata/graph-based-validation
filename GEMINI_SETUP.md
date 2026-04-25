# Gemini API Integration Setup Guide

## Overview

Your project has been set up to connect with Google's Gemini API. The system will:
1. Accept a list of genome properties via REST API
2. Generate a prompt describing these properties
3. Send the prompt to Gemini API for dependency inference
4. Parse the JSON response containing validation rules
5. Return structured rules with cross-field validation expressions

## Setup Steps

### 1. Get Your Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Click "Get API Key" → "Create API key in new Google Cloud project"
3. Copy your API key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi[standard]` - Web framework
- `pytest` - Testing framework
- `pylint` - Code linting
- `google-genai` - Gemini API client

### 3. Configure Environment Variable

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-api-key-here
```

Or set it as an environment variable:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Testing

### Run Unit Tests (No API Key Required)

```bash
pytest app/tests/test_main.py app/tests/test_gemini_service.py -v
```

### Run Integration Tests (Requires API Key)

```bash
# Run with real API calls
pytest app/tests/test_gemini_integration.py -v

# Run all tests
pytest -v
```

## Using the API

### 1. Start the Development Server

```bash
fastapi dev
```

The server will start at `http://127.0.0.1:8000`

### 2. Test the Endpoint

**Health Check:**
```bash
curl http://127.0.0.1:8000/
```

**Build Graph (with validation rules):**
```bash
curl -X POST http://127.0.0.1:8000/graphs/ \
  -H "Content-Type: application/json" \
  -d '{
    "properties": [
      {
        "property_type": "STANDARD",
        "name": "age",
        "value": "25",
        "unit": "years",
        "genome_type": "integer"
      },
      {
        "property_type": "STANDARD",
        "name": "height",
        "value": "180",
        "unit": "cm",
        "genome_type": "float"
      }
    ]
  }'
```

Expected response (array of rules):
```json
[
  {
    "inputs": ["age", "height"],
    "expression": "age > 18 -> height >= 150"
  }
]
```

### 3. View Interactive API Docs

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Files

**New files created:**
- `app/services/gemini_service.py` - Gemini API wrapper
- `app/tests/test_gemini_service.py` - Service unit tests
- `app/tests/test_gemini_integration.py` - Integration tests
- `.env.example` - Environment variable template

**Modified files:**
- `app/routers/graphs.py` - Now calls Gemini API
- `requirements.txt` - Added google-genai
- `app/tests/test_main.py` - Updated tests

## Key Components

### GeminiService (`app/services/gemini_service.py`)

```python
service = GeminiService()  # Uses GEMINI_API_KEY env var
response = service.query(prompt)  # Send prompt to API
rules = service.parse_rules_json(response)  # Parse JSON rules
```

### FastAPI Endpoint (`app/routers/graphs.py`)

```
POST /graphs/
  Input: List of genome properties
  Output: List of Rule objects (inputs, expression)
```

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure the `.env` file exists or environment variable is set
- Check that you've copied the full API key correctly

### "No module named 'google'"
```bash
pip install google-genai
```

### "Empty response from Gemini"
- Check your API quota
- Try with simpler property list
- Check logs for detailed error messages

### Tests not finding the module
```bash
# Add current directory to Python path
set PYTHONPATH=%PYTHONPATH%;.
pytest
```

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Set `GEMINI_API_KEY` environment variable
3. ✅ Run tests: `pytest`
4. ✅ Start server: `fastapi dev`
5. ✅ Test the API endpoint

Questions? Check the test files for usage examples!
