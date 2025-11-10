# Security Features

This document describes the security features implemented in the AI Expo App Builder backend.

## Overview

The application implements three layers of security:
1. **API Key Authentication** - Optional authentication for the /generate endpoint
2. **Rate Limiting** - Prevents abuse by limiting requests per user
3. **Input Sanitization** - Validates and sanitizes all user inputs to prevent injection attacks

## 1. API Key Authentication

### Configuration

API key authentication is optional and can be enabled via environment variables:

```bash
# Enable API key authentication
REQUIRE_API_KEY=true
API_KEY=your-secret-api-key-here
```

### Usage

When authentication is enabled, clients must include the API key in the `X-API-Key` header:

```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"prompt": "Create a todo app"}'
```

### Error Responses

- **401 Unauthorized**: Missing or invalid API key
  ```json
  {
    "detail": "Invalid or missing API key"
  }
  ```

## 2. Rate Limiting

### Configuration

Rate limiting is automatically enabled for the `/generate` endpoint with the following defaults:
- **10 requests per minute** per user
- Rate limits are tracked per API key (if provided) or IP address

### Response Headers

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

### Error Responses

- **429 Too Many Requests**: Rate limit exceeded
  ```json
  {
    "detail": "Rate limit exceeded. Please try again in 30 seconds"
  }
  ```
  - Includes `Retry-After` header with seconds to wait

## 3. Input Sanitization

### Prompt Sanitization

All user prompts are automatically sanitized to prevent injection attacks:

**Checks performed:**
- Length validation (max 5000 characters)
- Removal of shell metacharacters (`;`, `|`, `&`, `` ` ``, `$`)
- Detection of command substitution attempts (`$(...)`, `` `...` ``)
- Detection of script injection (`<script>`, `javascript:`, event handlers)
- Excessive special character detection (>30% of content)

**Example:**
```python
# Valid prompt
"Create a todo app with React Native"  # ✓ Accepted

# Invalid prompts
"Create app; rm -rf /"  # ✗ Rejected: shell metacharacters
"Create app <script>alert(1)</script>"  # ✗ Rejected: script injection
```

### Project ID Validation

Project IDs are validated to ensure they are safe identifiers:
- Must be 8-36 characters long
- Only alphanumeric characters and hyphens allowed
- No directory traversal sequences

### Path Sanitization

File paths are sanitized to prevent directory traversal attacks:
- No `..` sequences allowed
- No absolute paths allowed
- No shell special characters

### Command Argument Sanitization

Command line arguments are validated before execution:
- Only safe commands allowed: `npm`, `npx`, `expo`, `node`
- No shell metacharacters in arguments
- No quotes in arguments

## Security Best Practices

### For Deployment

1. **Always enable API key authentication in production:**
   ```bash
   REQUIRE_API_KEY=true
   API_KEY=$(openssl rand -hex 32)
   ```

2. **Use HTTPS only** - Configure your reverse proxy (nginx, Caddy) to enforce HTTPS

3. **Rotate API keys regularly** - Change API keys periodically and when compromised

4. **Monitor rate limit violations** - Set up alerts for excessive 429 responses

5. **Keep dependencies updated** - Regularly update Python packages for security patches

### For Development

1. **Never commit API keys** - Use `.env` files and add them to `.gitignore`

2. **Test with authentication disabled** - Set `REQUIRE_API_KEY=false` for local testing

3. **Use different API keys per environment** - Separate keys for dev, staging, production

## Testing Security Features

Run the security test suite:

```bash
pytest backend/tests/test_security.py -v
```

This tests:
- Input sanitization functions
- Rate limiting token bucket algorithm
- Various injection attack scenarios

## Reporting Security Issues

If you discover a security vulnerability, please email security@example.com instead of using the issue tracker.

## Security Checklist

- [x] API key authentication implemented
- [x] Rate limiting enabled (10 req/min)
- [x] Input sanitization for prompts
- [x] Project ID validation
- [x] Path sanitization
- [x] Command argument validation
- [x] Shell command whitelist
- [x] CORS configuration
- [x] Error message sanitization (no sensitive data leaked)
- [x] Comprehensive security tests

## Future Enhancements

Potential security improvements for future versions:
- OAuth 2.0 / JWT authentication
- Per-user rate limiting with database persistence
- IP-based blocking for repeated violations
- Content Security Policy (CSP) headers
- Request signing for API integrity
- Audit logging for security events
