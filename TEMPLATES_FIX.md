# Templates Endpoint Fix

## Issue
Frontend was calling `/api/templates` but the endpoint was only registered at `/templates`, causing a 500 error.

## Fix
Added `/api/templates` as an alias to the templates endpoint:

```python
@app.get("/templates")
@app.get("/api/templates")  # Added this line
async def get_templates():
    ...
```

## What It Does
Returns all available UI templates with their color schemes:
- Modern Dark
- Ocean Blue
- Sunset Orange
- Forest Green
- Royal Purple
- Minimal Light

## Response Format
```json
{
  "success": true,
  "templates": [
    {
      "id": "modern_dark",
      "name": "Modern Dark",
      "description": "Sleek dark theme with vibrant accents",
      "colors": {
        "primary": "#6366F1",
        "secondary": "#8B5CF6",
        ...
      },
      "preview_image": "...",
      "preview_url": "/template-preview/modern_dark"
    }
  ]
}
```

## Testing
```bash
curl http://localhost:8000/api/templates
```

or

```bash
curl http://localhost:8000/templates
```

Both should work now!
