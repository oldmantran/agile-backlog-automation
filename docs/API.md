# API Documentation

## Authentication

All API endpoints (except auth endpoints) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Base URL

Development: `http://localhost:8000/api`
Production: `https://api.yourdomain.com/api`

## Endpoints

### Authentication

#### POST /auth/register
Create a new user account.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

#### POST /auth/login
Login and receive JWT tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string"
  }
}
```

### Vision Optimization

#### POST /api/vision/optimize
Optimize a product vision statement with domain weighting.

**Request Body:**
```json
{
  "original_vision": "string",
  "domains": [
    {
      "domain": "string",
      "weight": "number"
    }
  ]
}
```

**Response:**
```json
{
  "id": "number",
  "original_vision": "string",
  "optimized_vision": "string",
  "domains": [
    {
      "domain": "string",
      "weight": "number"
    }
  ],
  "quality_score": "number",
  "quality_rating": "string",
  "optimization_feedback": {
    "changes_made": ["string"],
    "improvements": ["string"],
    "domain_integration": ["string"]
  },
  "created_at": "string"
}
```

#### GET /api/vision/optimized
Get all optimized visions for the authenticated user.

**Response:**
```json
[
  {
    "id": "number",
    "original_vision": "string",
    "optimized_vision": "string",
    "domains": [
      {
        "domain": "string",
        "weight": "number"
      }
    ],
    "quality_score": "number",
    "quality_rating": "string",
    "created_at": "string"
  }
]
```

#### GET /api/vision/optimized/{id}
Get a specific optimized vision by ID.

**Response:**
```json
{
  "id": "number",
  "original_vision": "string",
  "optimized_vision": "string",
  "domains": [
    {
      "domain": "string",
      "weight": "number"
    }
  ],
  "quality_score": "number",
  "quality_rating": "string",
  "optimization_feedback": {
    "changes_made": ["string"],
    "improvements": ["string"],
    "domain_integration": ["string"]
  },
  "created_at": "string"
}
```

### Project Management

#### POST /api/projects/create
Create a new project and generate backlog.

**Request Body:**
```json
{
  "visionStatement": "string",
  "selectedDomains": ["string"],
  "workItemType": "string",
  "organizationUrl": "string",
  "project": "string",
  "personalAccessToken": "string",
  "areaPath": "string",
  "includeTestArtifacts": "boolean",
  "optimizedVisionId": "number (optional)"
}
```

#### GET /api/projects
Get all projects for the authenticated user.

#### GET /api/projects/{id}
Get a specific project by ID.

#### POST /api/projects/{id}/generate-test-artifacts
Generate test artifacts for an existing project.

### LLM Configuration

#### GET /api/llm-configurations/{user_id}
Get LLM configurations and mode for a user.

**Response:**
```json
{
  "configurations": [
    {
      "agent_name": "string",
      "provider": "string",
      "model": "string",
      "temperature": "number",
      "max_tokens": "number"
    }
  ],
  "configuration_mode": "string"
}
```

#### POST /api/llm-configurations/{user_id}
Save LLM configurations and mode for a user.

**Request Body:**
```json
{
  "configurations": [
    {
      "agent_name": "string",
      "provider": "string",
      "model": "string",
      "temperature": "number",
      "max_tokens": "number"
    }
  ],
  "configuration_mode": "string"
}
```

### User Settings

#### GET /api/user/settings
Get user settings.

#### POST /api/user/settings
Update user settings.

**Request Body:**
```json
{
  "notification_email": "string",
  "default_work_item_type": "string",
  "max_parallel_requests": "number"
}
```

### Workflow Progress

#### GET /api/jobs/{jobId}/progress
Get real-time progress updates for a job (Server-Sent Events).

### Domains

#### GET /api/domains
Get all available domains for selection.

**Response:**
```json
[
  {
    "id": "number",
    "name": "string",
    "description": "string"
  }
]
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "string"
}
```

Common HTTP status codes:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- 10 requests per minute for authentication endpoints
- 100 requests per minute for other endpoints
- Headers include rate limit information:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`