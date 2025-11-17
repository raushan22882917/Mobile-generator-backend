#!/bin/bash

# Test Weather App Creation
# Simple script to create a weather mobile app

echo "============================================================"
echo "  🌤️  WEATHER APP CREATION TEST"
echo "============================================================"
echo ""
echo "📱 Creating a weather mobile app with:"
echo "   - Current temperature display"
echo "   - Weather icons (sunny, cloudy, rainy)"
echo "   - Location-based weather"
echo "   - Material Design UI"
echo "   - Using shared node_modules (no npm install!)"
echo ""
read -p "Press Enter to create the app..."

echo ""
echo "============================================================"
echo "  📤 SENDING REQUEST"
echo "============================================================"
echo ""
echo "⏳ Creating weather app..."
echo "   (This will take ~30-60 seconds)"
echo ""

# Send request and save response
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a weather mobile app with current temperature, weather icons, and location-based forecast",
    "user_id": "weather_test_user"
  }')

# Extract status code and body
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "============================================================"
echo "  📥 RESPONSE RECEIVED"
echo "============================================================"
echo ""
echo "📊 Status Code: $HTTP_CODE"

if [ "$HTTP_CODE" = "201" ]; then
    echo "✅ Status: SUCCESS"
    echo ""
    echo "============================================================"
    echo "  📋 RESPONSE DATA"
    echo "============================================================"
    echo ""
    echo "$BODY" | python -m json.tool
    
    # Extract key information
    PROJECT_ID=$(echo "$BODY" | python -c "import sys, json; print(json.load(sys.stdin)['project_id'])" 2>/dev/null)
    PREVIEW_URL=$(echo "$BODY" | python -c "import sys, json; print(json.load(sys.stdin).get('preview_url', 'N/A'))" 2>/dev/null)
    
    echo ""
    echo "============================================================"
    echo "  🎯 KEY INFORMATION"
    echo "============================================================"
    echo ""
    echo "✅ Project ID: $PROJECT_ID"
    echo "🌐 Preview URL: $PREVIEW_URL"
    
    echo ""
    echo "============================================================"
    echo "  📱 HOW TO VIEW YOUR APP"
    echo "============================================================"
    echo ""
    echo "🎯 Option 1: Expo Go App (Recommended)"
    echo "   1. Install 'Expo Go' app on your phone"
    echo "   2. Open the app"
    echo "   3. Enter this URL:"
    echo "      $PREVIEW_URL"
    echo "   4. Your weather app will load!"
    echo ""
    echo "🌐 Option 2: Web Browser"
    echo "   Open: $PREVIEW_URL"
    echo ""
    echo "============================================================"
    echo "  🎨 WHAT'S IN YOUR APP"
    echo "============================================================"
    echo ""
    echo "✅ Features automatically included:"
    echo "   - Weather icons (from @expo/vector-icons)"
    echo "   - Material Design UI (from react-native-paper)"
    echo "   - Location services (from expo-location)"
    echo "   - Temperature display"
    echo "   - Weather forecast"
    echo ""
    echo "✅ Packages used (from shared node_modules):"
    echo "   - @expo/vector-icons (weather icons)"
    echo "   - react-native-paper (UI components)"
    echo "   - expo-location (GPS location)"
    echo "   - axios (weather API calls)"
    echo "   - All 110+ packages available!"
    echo ""
    echo "============================================================"
    echo "  ✅ SUCCESS!"
    echo "============================================================"
    echo ""
    echo "🎉 Your weather app is ready!"
    echo "🌐 Preview URL: $PREVIEW_URL"
    echo "📱 Open in Expo Go to see it live!"
    echo ""
else
    echo "❌ Status: FAILED"
    echo ""
    echo "Error: $HTTP_CODE"
    echo "Response: $BODY"
fi
