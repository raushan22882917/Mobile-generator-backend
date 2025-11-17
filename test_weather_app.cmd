@echo off
REM Test Weather App Creation
REM Simple script to create a weather mobile app

echo ============================================================
echo   🌤️  WEATHER APP CREATION TEST
echo ============================================================
echo.
echo 📱 Creating a weather mobile app with:
echo    - Current temperature display
echo    - Weather icons (sunny, cloudy, rainy)
echo    - Location-based weather
echo    - Material Design UI
echo    - Using shared node_modules (no npm install!)
echo.
pause

echo.
echo ============================================================
echo   📤 SENDING REQUEST
echo ============================================================
echo.
echo ⏳ Creating weather app...
echo    (This will take ~30-60 seconds)
echo.

REM Send request
curl -X POST http://localhost:8000/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"Create a weather mobile app with current temperature, weather icons, and location-based forecast\", \"user_id\": \"weather_test_user\"}" ^
  -o response.json

echo.
echo ============================================================
echo   📥 RESPONSE RECEIVED
echo ============================================================
echo.

REM Display response
type response.json

echo.
echo.
echo ============================================================
echo   📱 HOW TO VIEW YOUR APP
echo ============================================================
echo.
echo 🎯 Option 1: Expo Go App (Recommended)
echo    1. Install 'Expo Go' app on your phone
echo    2. Open the app
echo    3. Check response.json for preview_url
echo    4. Enter the URL in Expo Go
echo    5. Your weather app will load!
echo.
echo 🌐 Option 2: Web Browser
echo    Check response.json for preview_url and open it
echo.
echo ============================================================
echo   🎨 WHAT'S IN YOUR APP
echo ============================================================
echo.
echo ✅ Features automatically included:
echo    - Weather icons (from @expo/vector-icons)
echo    - Material Design UI (from react-native-paper)
echo    - Location services (from expo-location)
echo    - Temperature display
echo    - Weather forecast
echo.
echo ✅ Packages used (from shared node_modules):
echo    - @expo/vector-icons (weather icons)
echo    - react-native-paper (UI components)
echo    - expo-location (GPS location)
echo    - axios (weather API calls)
echo    - All 110+ packages available!
echo.
echo ============================================================
echo   ✅ DONE!
echo ============================================================
echo.
echo 🎉 Check response.json for your preview URL!
echo 📱 Open in Expo Go to see it live!
echo.
pause
