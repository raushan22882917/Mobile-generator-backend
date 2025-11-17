# Quick Setup Script for Gemini Fallback

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  🔧 GEMINI FALLBACK SETUP" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will help you set up Gemini as a fallback for OpenAI" -ForegroundColor Green
Write-Host ""

# Step 1: Check if google-generativeai is installed
Write-Host "Step 1: Checking if google-generativeai is installed..." -ForegroundColor Yellow
try {
    python -c "import google.generativeai; print('✅ Already installed')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ google-generativeai is already installed" -ForegroundColor Green
    } else {
        throw "Not installed"
    }
} catch {
    Write-Host "⚠️  google-generativeai not installed" -ForegroundColor Yellow
    Write-Host "Installing..." -ForegroundColor Cyan
    pip install google-generativeai
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ google-generativeai installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install google-generativeai" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 2: Check .env file
Write-Host "Step 2: Checking .env file..." -ForegroundColor Yellow

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    if ($envContent -match "GEMINI_API_KEY=(.+)") {
        $geminiKey = $matches[1].Trim()
        if ($geminiKey -and $geminiKey -ne "") {
            Write-Host "✅ GEMINI_API_KEY found in .env" -ForegroundColor Green
            Write-Host "   Key: $($geminiKey.Substring(0, [Math]::Min(10, $geminiKey.Length)))..." -ForegroundColor Cyan
        } else {
            Write-Host "⚠️  GEMINI_API_KEY is empty in .env" -ForegroundColor Yellow
            $needsKey = $true
        }
    } else {
        Write-Host "⚠️  GEMINI_API_KEY not found in .env" -ForegroundColor Yellow
        $needsKey = $true
    }
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    $needsKey = $true
}

Write-Host ""

# Step 3: Get API key if needed
if ($needsKey) {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  🔑 GET GEMINI API KEY (FREE!)" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Open this URL in your browser:" -ForegroundColor Green
    Write-Host "   https://makersuite.google.com/app/apikey" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Click 'Create API Key'" -ForegroundColor Green
    Write-Host ""
    Write-Host "3. Copy the API key" -ForegroundColor Green
    Write-Host ""
    Write-Host "4. Paste it below" -ForegroundColor Green
    Write-Host ""
    
    $apiKey = Read-Host "Enter your Gemini API key (or press Enter to skip)"
    
    if ($apiKey) {
        # Add to .env file
        if (Test-Path ".env") {
            Add-Content ".env" "`nGEMINI_API_KEY=$apiKey"
        } else {
            "GEMINI_API_KEY=$apiKey" | Out-File ".env" -Encoding utf8
        }
        Write-Host "✅ GEMINI_API_KEY added to .env" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Skipped - you can add it later to .env file" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 4: Test Gemini
Write-Host "Step 3: Testing Gemini connection..." -ForegroundColor Yellow

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "GEMINI_API_KEY=(.+)") {
        $geminiKey = $matches[1].Trim()
        if ($geminiKey -and $geminiKey -ne "") {
            Write-Host "Testing API key..." -ForegroundColor Cyan
            
            $testScript = @"
import google.generativeai as genai
import sys

try:
    genai.configure(api_key='$geminiKey')
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content('Say hello')
    print('✅ Gemini API key is valid!')
    print(f'Response: {response.text[:50]}...')
    sys.exit(0)
except Exception as e:
    print(f'❌ Gemini API key test failed: {e}')
    sys.exit(1)
"@
            
            $testScript | python
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Gemini is working!" -ForegroundColor Green
            } else {
                Write-Host "❌ Gemini test failed - check your API key" -ForegroundColor Red
            }
        }
    }
}

Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What's configured:" -ForegroundColor Yellow
Write-Host "  ✅ google-generativeai package installed" -ForegroundColor Green
Write-Host "  ✅ GEMINI_API_KEY in .env file" -ForegroundColor Green
Write-Host ""
Write-Host "How it works:" -ForegroundColor Yellow
Write-Host "  1. System tries OpenAI first" -ForegroundColor White
Write-Host "  2. If OpenAI quota exceeded → automatically uses Gemini" -ForegroundColor White
Write-Host "  3. Code generation never fails!" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart backend: python main.py" -ForegroundColor Cyan
Write-Host "  2. Test weather app: .\test_weather_app.ps1" -ForegroundColor Cyan
Write-Host "  3. Even if OpenAI quota exceeded, Gemini will work!" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 You're all set!" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to exit"
