# PowerShell script to test weather app creation
# For Windows PowerShell

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  🌤️  WEATHER APP CREATION TEST" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Creating a weather mobile app with:" -ForegroundColor Green
Write-Host "   - Current temperature display"
Write-Host "   - Weather icons (sunny, cloudy, rainy)"
Write-Host "   - Location-based weather"
Write-Host "   - Material Design UI"
Write-Host "   - Using shared node_modules (no npm install!)"
Write-Host ""
Read-Host "Press Enter to create the app"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  📤 SENDING REQUEST" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Creating weather app..." -ForegroundColor Yellow
Write-Host "   (This will take ~30-60 seconds)"
Write-Host ""

# Prepare request body
$body = @{
    prompt = "Create a weather mobile app with current temperature, weather icons, and location-based forecast"
    user_id = "weather_test_user"
} | ConvertTo-Json

# Send request
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/generate" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  📥 RESPONSE RECEIVED" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✅ Status: SUCCESS" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  📋 RESPONSE DATA" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  🎯 KEY INFORMATION" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✅ Project ID: $($response.project_id)" -ForegroundColor Green
    Write-Host "✅ Status: $($response.status)" -ForegroundColor Green
    Write-Host "✅ Message: $($response.message)" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Preview URL: $($response.preview_url)" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  📱 HOW TO VIEW YOUR APP" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎯 Option 1: Expo Go App (Recommended)" -ForegroundColor Green
    Write-Host "   1. Install 'Expo Go' app on your phone"
    Write-Host "   2. Open the app"
    Write-Host "   3. Enter this URL:"
    Write-Host "      $($response.preview_url)" -ForegroundColor Cyan
    Write-Host "   4. Your weather app will load!"
    Write-Host ""
    Write-Host "🌐 Option 2: Web Browser" -ForegroundColor Green
    Write-Host "   Open: $($response.preview_url)" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  🎨 WHAT'S IN YOUR APP" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✅ Features automatically included:" -ForegroundColor Green
    Write-Host "   - Weather icons (from @expo/vector-icons)"
    Write-Host "   - Material Design UI (from react-native-paper)"
    Write-Host "   - Location services (from expo-location)"
    Write-Host "   - Temperature display"
    Write-Host "   - Weather forecast"
    Write-Host ""
    Write-Host "✅ Packages used (from shared node_modules):" -ForegroundColor Green
    Write-Host "   - @expo/vector-icons (weather icons)"
    Write-Host "   - react-native-paper (UI components)"
    Write-Host "   - expo-location (GPS location)"
    Write-Host "   - axios (weather API calls)"
    Write-Host "   - All 110+ packages available!"
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  ✅ SUCCESS!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 Your weather app is ready!" -ForegroundColor Green
    Write-Host "🌐 Preview URL: $($response.preview_url)" -ForegroundColor Cyan
    Write-Host "📱 Open in Expo Go to see it live!" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  ❌ ERROR" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "📊 Status Code: $statusCode" -ForegroundColor Red
    
    if ($statusCode -eq 500) {
        Write-Host ""
        Write-Host "⚠️  Server Error - Possible causes:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. OpenAI API Quota Exceeded" -ForegroundColor Yellow
        Write-Host "   - Check your OpenAI account: https://platform.openai.com/account/billing"
        Write-Host "   - Add credits to your account"
        Write-Host "   - Verify OPENAI_API_KEY in .env file"
        Write-Host ""
        Write-Host "2. Backend Configuration" -ForegroundColor Yellow
        Write-Host "   - Check .env file has valid OPENAI_API_KEY"
        Write-Host "   - Restart backend: python main.py"
        Write-Host ""
    }
    
    Write-Host "Error details:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    
    # Try to get response body
    try {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host ""
        Write-Host "Response body:" -ForegroundColor Yellow
        Write-Host $responseBody
    } catch {
        # Ignore if can't read response
    }
}

Write-Host ""
Read-Host "Press Enter to exit"
