# Mobile Generator Backend

A FastAPI backend service for generating and managing React Native Expo mobile applications using AI.

## Features

- AI-powered code generation using OpenAI
- Automatic Expo project setup and dependency management
- Screen generation with UI/UX enhancements
- Image generation using Google Gemini
- Ngrok tunnel integration for live preview
- Project lifecycle management
- Automatic icon and image integration

## Requirements

- Python 3.8+
- Node.js and npm
- Expo CLI
- Ngrok account (for tunnel functionality)

## Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with the following variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   NGROK_AUTH_TOKEN=your_ngrok_authtoken
   GEMINI_API_KEY=your_gemini_api_key (optional)
   ```

4. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

## Configuration

### Ngrok Setup

To use ngrok tunnels, you need a valid authtoken:

1. Sign up for a free account at https://dashboard.ngrok.com
2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
3. Add it to your `.env` file as `NGROK_AUTH_TOKEN`

If your authtoken is invalid, you'll see an authentication error. Make sure to:
- Use the correct authtoken from your ngrok dashboard
- Check if your authtoken was reset or revoked
- Verify you're using the correct account credentials

## API Endpoints

- `POST /generate` - Generate a new Expo app
- `GET /status/{project_id}` - Get project status
- `POST /activate-project/{project_id}` - Activate a project
- `POST /create-file` - Create a new file
- `PUT /update-file` - Update an existing file

## License

MIT

