# API Inspector AI

API Inspector AI is the companion AI engine for [API Inspector](https://github.com/Kian-kianmehr/api-inspector), a developer-focused platform for understanding API contracts and inspecting real API behavior.

This repository is developed separately from the main application so that API-specific reasoning, test generation, and result analysis can evolve independently of the Django backend and React frontend.

**Development status: Version 1.0 completed.**

## How the Repositories Fit Together

Both repositories are parts of the same API Inspector product.

- **[api-inspector](https://github.com/Kian-kianmehr/api-inspector):** The main application, built with Django REST Framework and React. It handles accounts, authentication, API execution, and user-facing features.
- **[api-inspector-ai](https://github.com/Kian-kianmehr/api-inspector-ai):** The companion AI engine, responsible for API context processing, test generation, and AI-assisted result analysis.

The intended integration is service-to-service. The main application provides normalized API context and sanitized inspection results to the AI engine. The AI engine returns structured test plans, findings, and recommendations.

The main application retains responsibility for user accounts, credentials, permissions, HTTP request execution, and security controls. The AI engine does not independently execute arbitrary requests against target APIs.

## Implemented Features

- **API Context Models:** Structured representation of API definitions, endpoints, parameters, request bodies, and responses.
- **Context Validation:** Validation of API context structures and their fields.
- **AI Test Generation:** Generation of structured API test cases based on API specifications.
- **AI Result Analysis:** Analysis of test execution results to identify unexpected behavior and potential issues.
- **Finding Validation:** Validation of generated findings, severity levels, and recommendations.
- **Evidence-Based Analysis:** Findings are based on supplied test results rather than unsupported assumptions.
- **Local AI Integration:** Integration with Ollama using the Qwen 2.5 model.

## Testing

The project includes automated tests covering:

- API context validation.
- AI request and response validation.
- Test case generation.
- Result analysis.
- Invalid model outputs and unsupported findings.

The automated test suite has passed. The engine has also been evaluated using the local Ollama model with both successful and failed API test scenarios.

## Architecture

1. The main application supplies normalized API context and sanitized inspection results.
2. The AI engine validates the supplied data.
3. The AI engine generates test plans or analyzes execution results.
4. Structured results are returned to the main application.
5. The main application manages execution, permissions, and result storage.

Sensitive credentials and unrestricted target-network access remain outside the AI reasoning layer.

## Technology Stack

- Python
- Ollama
- Qwen 2.5
- Python dataclasses and enums
- Pytest

## Repository Structure

```text
api-inspector-ai/
├── app/
│   └── core/
│       ├── ai/
│       │   ├── interface.py
│       │   ├── models.py
│       │   ├── ollama_engine.py
│       │   ├── test_cases.py
│       │   └── validators.py
│       └── context/
│           ├── models.py
│           └── validators.py
├── test_ai_analysis.py
├── test_ai_generation.py
├── test_ai_interface.py
├── test_ollama_connection.py
└── test_context.py
```

## Development

Clone the repository:

```bash
git clone https://github.com/Kian-kianmehr/api-inspector-ai.git
cd api-inspector-ai
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the automated tests:

```bash
python -m pytest -v
```

Make sure Ollama is installed and the Qwen 2.5 model is available locally before running live AI tests.

## Related Project

- **Main application:** [Kian-kianmehr/api-inspector](https://github.com/Kian-kianmehr/api-inspector)