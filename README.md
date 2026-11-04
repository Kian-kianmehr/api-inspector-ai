# API Inspector AI

API Inspector AI is the companion AI service for [API Inspector](https://github.com/Kian-kianmehr/api-inspector), a developer-focused platform for understanding API contracts and inspecting real API behavior.

This repository is developed separately from the main application so that API-specific reasoning and analysis can evolve independently of the Django backend and React frontend.

> **Development status:** Early development. The initial API context data models are implemented. Validation, inspection planning, AI-assisted analysis, and the service interface are planned but not implemented yet.

## How the repositories fit together

Both repositories are parts of the same API Inspector product:

| Repository | Responsibility |
| --- | --- |
| [api-inspector](https://github.com/Kian-kianmehr/api-inspector) | Main product: Django REST backend, React frontend, accounts, authentication, and user-facing application |
| [api-inspector-ai](https://github.com/Kian-kianmehr/api-inspector-ai) | Companion AI service: API context processing, inspection planning, and AI-assisted analysis |

The intended integration is service-to-service. The main application will send normalized API context and sanitized inspection results to the AI service. The AI service will return structured plans, findings, and recommendations.

The main application will retain responsibility for user accounts, credentials, permissions, request execution, and security controls. The AI service is not intended to independently execute arbitrary requests against target APIs.

## Planned responsibilities

- Represent API definitions in a normalized internal context.
- Validate API context data before analysis.
- Help plan relevant API inspection scenarios.
- Analyze inspection results and identify potential issues.
- Produce structured findings and recommendations.
- Expose capabilities to the main application through an internal service API.

## Current implementation

The initial context models are in app/core/context/models.py:

- APIContext: metadata and endpoints for an API.
- Endpoint: path, HTTP method, parameters, request body, and responses.
- Parameter: path, query, header, and cookie parameters.
- RequestBody and BodyField: request body metadata and nested fields.
- Response and ResponseField: response metadata and nested fields.

These classes currently describe API structures in Python. They do not yet import OpenAPI documents, parse live traffic, validate definitions, or call an AI model.

## Architecture direction

1. The main application supplies a normalized API context and sanitized inspection data.
2. The AI service validates and analyzes that context.
3. The AI service returns structured plans, findings, and recommendations.
4. The main application decides which permitted actions to execute and manages the resulting records.

Sensitive credentials and unrestricted target-network access should remain outside the AI reasoning layer.

## Technology

- Python
- Python standard library dataclasses and enums for the initial domain models
- FastAPI is planned for the service interface, but has not been integrated yet

## Repository structure

    api-inspector-ai/
    ├── app/
    │   └── core/
    │       └── context/
    │           └── models.py
    ├── test_context.py
    └── .gitignore

The structure will evolve as validation, inspection planning, analysis, and the service interface are implemented.

## Development

Clone the repository:

    git clone https://github.com/Kian-kianmehr/api-inspector-ai.git
    cd api-inspector-ai

Create and activate a virtual environment:

    python -m venv venv
    source venv/bin/activate

On Windows PowerShell:

    venv\Scripts\Activate.ps1

Run the current context model check:

    python test_context.py

## Roadmap

- [x] Initial API context data models
- [ ] Context validation layer
- [ ] Tests for context models and validation
- [ ] Support for importing API specifications, including OpenAPI
- [ ] Inspection planning engine
- [ ] AI-assisted result analysis
- [ ] Internal service API and integration with the main API Inspector application

## Related project

- **Main application:** [Kian-kianmehr/api-inspector](https://github.com/Kian-kianmehr/api-inspector)
