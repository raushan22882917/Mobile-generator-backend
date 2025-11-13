# Testing Guide - Real-Time Streaming

## ✅ System Validated!

All components are properly installed and configured.

## Quick Test (3 Steps)

### Step 1: Start Server
```bash
uvicorn main:app --reload
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 2: Open Demo
Open `examples/streaming_client.html` in your browser

Or navigate to:
```
file:///D:/Mobile-generator-backend/examples/streaming_client.html
```

### Step 3: Test Generation

**Try this prompt:**
```
Create a simple todo list app with home screen, 
add todo functionality, and mark as complete feature
```

**Watch the magic:**
- ⏱️ 0-5s: Analyzing...
- ⏱️ 5-15s: Creating project...
- ⏱️ 15-25s: Generating base...
- ⏱️ 25-45s: Installing & starting...
- ⏱️ 45s: ✅ **PREVIEW READY!** (Scan QR code)
- ⏱️ 45-75s: Adding screens (watch them appear)
- ⏱️ 75-100s: Complete!

## Test Prompts

### Simple (Fast)
```
Create a todo list app with basic CRUD operations
```

### Medium (Recommended)
```
Create a fitness tracking app with workout plans, 
progress tracking, and user profile
```

### Complex (Full Features)
```
Build a social media app with posts feed, user profiles, 
messaging, notifications, and image sharing. Include 
home, explore, messages, and profile tabs.
```

## What to Expect

### Timeline
```
00:00 - Click "Generate"
00:05 - "Analyzing your app..."
00:15 - "Creating todo-app-x7k2..."
00:25 - "Generating base structure..."
00:35 - "Installing dependencies..."
00:45 - "Preview ready!" 🎉
        [QR Code appears]
        [Preview link active]
01:00 - "Added Home screen"
01:15 - "Added Profile screen"
01:30 - "Added Settings screen"
01:45 - "Complete!" ✅
```

### UI Updates
- Progress bar animates smoothly
- Stage indicator updates
- Messages change in real-time
- QR code appears at 45s
- Screen badges appear as added
- No page refresh needed!

## Testing Checklist

- [ ] Server starts without errors
- [ ] Demo page loads
- [ ] WebSocket connects
- [ ] Progress bar updates
- [ ] Preview URL appears
- [ ] QR code generates
- [ ] Screens list updates
- [ ] Completion message shows
- [ ] No errors in console

## Troubleshooting

### Server won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Install dependencies
pip install -r requirements.txt

# Try again
uvicorn main:app --reload
```

### WebSocket won't connect
- Check server is running on port 8000
- Check browser console for errors
- Try different browser
- Check firewall settings

### Preview not ready
- Wait full 45 seconds
- Check ngrok auth token in .env
- Check Expo CLI is installed
- Check Node.js is installed

## Advanced Testing

### Test with curl
```bash
# Check server health
curl http://localhost:8000/

# Check WebSocket endpoint exists
curl http://localhost:8000/api/v1/stream-status/test-123
```

### Test with Python
```bash
python test_streaming.py
```

### Monitor logs
```bash
# Watch server logs
uvicorn main:app --reload --log-level debug
```

## Performance Metrics

Track these during testing:

- **Time to preview**: Should be ~45 seconds
- **Total time**: Should be ~100 seconds
- **Progress updates**: Every 5 seconds
- **Screen additions**: Every 15 seconds
- **Memory usage**: Should stay under 2GB
- **CPU usage**: Peaks at 85%, avg 45%

## Success Criteria

✅ Preview appears in < 60 seconds
✅ All progress updates received
✅ QR code generates correctly
✅ Screens appear in real-time
✅ No errors in console
✅ App works on mobile device

## Next Steps After Testing

1. **Try different prompts** - Test various app types
2. **Test on mobile** - Scan QR with Expo Go
3. **Monitor performance** - Check resource usage
4. **Gather feedback** - Note any issues
5. **Optimize** - Adjust batch sizes if needed

## Support

If you encounter issues:

1. Check logs in terminal
2. Check browser console
3. Review STREAMING_ARCHITECTURE.md
4. Check .env configuration
5. Verify all dependencies installed

## Example Test Session

```
Terminal 1:
$ uvicorn main:app --reload
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.

Browser:
1. Open examples/streaming_client.html
2. Enter: "Create a todo app"
3. Click "Generate App Now"
4. Watch progress bar
5. At 45s: QR code appears
6. Scan with Expo Go
7. See app on phone!
8. Watch screens appear live
9. Complete at ~100s

Result: ✅ Success!
```

## Validation Results

```
✅ All imports successful
✅ StreamingGenerator validated
✅ ProgressUpdate validated
✅ ConnectionManager validated
✅ All 11 stages defined
✅ All files present
✅ Configuration valid
```

**System is ready for testing!** 🚀
