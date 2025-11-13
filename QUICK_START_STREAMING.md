# Quick Start: Real-Time Streaming

## 🚀 Get Started in 3 Steps

### 1. Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Open the Demo Client

```bash
# Open in your browser
open examples/streaming_client.html
# Or navigate to: file:///path/to/examples/streaming_client.html
```

### 3. Generate Your App

1. Enter your app description
2. Click "Generate App Now"
3. Watch real-time progress
4. Preview appears in ~45 seconds!
5. Scan QR code with Expo Go app

## 📱 Example Prompts

**Fitness App:**
```
Create a fitness tracking app with workout plans, progress tracking, 
and social features. Include a home dashboard, workout library, 
progress charts, and user profile.
```

**E-commerce App:**
```
Build an online shopping app with product catalog, shopping cart, 
user authentication, and order tracking. Include home, products, 
cart, and profile screens.
```

**Social Media App:**
```
Create a social media app with posts feed, user profiles, messaging, 
and notifications. Include home feed, explore, messages, and profile tabs.
```

## 🎯 What to Expect

- **5s**: Analysis starts
- **15s**: Project created
- **25s**: Base code generated
- **45s**: ✅ **PREVIEW READY!** (Scan QR code)
- **60-90s**: Additional screens appear
- **100s**: Complete with all features

## 🔧 API Integration

```javascript
const projectId = generateUUID();
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/generate/${projectId}`);

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'start',
    prompt: 'Your app description here',
    user_id: 'user123'
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`${msg.data.progress}%: ${msg.data.message}`);
  
  if (msg.data.preview_url) {
    console.log('Preview:', msg.data.preview_url);
  }
};
```

## ✅ Benefits

- **75% faster** time-to-preview
- **Real-time** progress updates
- **Live preview** while generating
- **Progressive** screen additions
- **Background** image generation

## 📚 More Info

See [STREAMING_ARCHITECTURE.md](STREAMING_ARCHITECTURE.md) for details.
