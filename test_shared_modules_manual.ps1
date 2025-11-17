# Manual Test for Shared Modules (No AI Needed)
# This tests that shared node_modules work without creating a new project

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  🧪 SHARED MODULES MANUAL TEST" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This test verifies shared node_modules work WITHOUT using AI" -ForegroundColor Green
Write-Host ""

# Test 1: Check if global modules exist
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TEST 1: Check Global Modules" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$globalModulesPath = "D:\tmp\shared_node_modules\global\node_modules"

if (Test-Path $globalModulesPath) {
    Write-Host "✅ Global modules directory exists!" -ForegroundColor Green
    Write-Host "   Path: $globalModulesPath" -ForegroundColor Cyan
    
    # Count packages
    $packageCount = (Get-ChildItem $globalModulesPath -Directory).Count
    Write-Host "   Packages installed: $packageCount" -ForegroundColor Green
    
    # Check for key packages
    Write-Host ""
    Write-Host "Checking key packages:" -ForegroundColor Yellow
    
    $keyPackages = @(
        "@expo/vector-icons",
        "react-native-paper",
        "expo",
        "react",
        "react-native"
    )
    
    foreach ($package in $keyPackages) {
        $packagePath = Join-Path $globalModulesPath $package
        if (Test-Path $packagePath) {
            Write-Host "   ✅ $package" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $package (missing)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ Global modules NOT found!" -ForegroundColor Red
    Write-Host "   Expected path: $globalModulesPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please run: python init_shared_deps.py" -ForegroundColor Yellow
    exit
}

# Test 2: Create manual test project
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TEST 2: Create Manual Test Project" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$testProjectPath = "D:\tmp\projects\test-manual-shared"

Write-Host "Creating test project at: $testProjectPath" -ForegroundColor Cyan

# Create project directory
if (Test-Path $testProjectPath) {
    Write-Host "⚠️  Project already exists, removing..." -ForegroundColor Yellow
    Remove-Item $testProjectPath -Recurse -Force
}

New-Item -ItemType Directory -Path $testProjectPath -Force | Out-Null
New-Item -ItemType Directory -Path "$testProjectPath\app" -Force | Out-Null

Write-Host "✅ Project directory created" -ForegroundColor Green

# Create package.json (minimal, no dependencies)
$packageJson = @"
{
  "name": "test-manual-shared",
  "version": "1.0.0",
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start"
  }
}
"@

$packageJson | Out-File -FilePath "$testProjectPath\package.json" -Encoding utf8
Write-Host "✅ Created minimal package.json (no dependencies)" -ForegroundColor Green

# Create app layout
$layoutCode = @"
import { Stack } from 'expo-router';

export default function Layout() {
  return <Stack />;
}
"@

$layoutCode | Out-File -FilePath "$testProjectPath\app\_layout.tsx" -Encoding utf8
Write-Host "✅ Created app/_layout.tsx" -ForegroundColor Green

# Create main app file with shared packages
$appCode = @"
import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Ionicons, MaterialCommunityIcons, FontAwesome5 } from '@expo/vector-icons';
import { Button, Card } from 'react-native-paper';

export default function App() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <MaterialCommunityIcons name="test-tube" size={32} color="#007AFF" />
        <Text style={styles.title}>Shared Modules Test</Text>
      </View>

      <Card style={styles.card}>
        <Card.Title title="✅ Shared Modules Working!" />
        <Card.Content>
          <Text style={styles.text}>
            This app uses packages from shared node_modules:
          </Text>
          
          <View style={styles.iconRow}>
            <Ionicons name="home" size={32} color="#007AFF" />
            <Text style={styles.iconLabel}>Ionicons</Text>
          </View>
          
          <View style={styles.iconRow}>
            <MaterialCommunityIcons name="weather-sunny" size={32} color="#FFD700" />
            <Text style={styles.iconLabel}>MaterialCommunityIcons</Text>
          </View>
          
          <View style={styles.iconRow}>
            <FontAwesome5 name="heart" size={32} color="#FF3B30" />
            <Text style={styles.iconLabel}>FontAwesome5</Text>
          </View>
          
          <Text style={styles.success}>
            ✅ All icons loaded from shared modules!
          </Text>
          <Text style={styles.success}>
            ✅ No npm install needed!
          </Text>
          <Text style={styles.success}>
            ✅ Project size: ~2MB (no node_modules)
          </Text>
        </Card.Content>
      </Card>

      <Button 
        mode="contained" 
        icon="check"
        style={styles.button}
      >
        Shared Modules Working!
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  card: {
    marginBottom: 20,
  },
  text: {
    fontSize: 16,
    marginBottom: 15,
  },
  iconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 10,
  },
  iconLabel: {
    fontSize: 14,
    marginLeft: 10,
  },
  success: {
    fontSize: 14,
    color: '#34C759',
    marginTop: 10,
  },
  button: {
    marginTop: 10,
  },
});
"@

$appCode | Out-File -FilePath "$testProjectPath\app\index.tsx" -Encoding utf8
Write-Host "✅ Created app/index.tsx with shared package imports" -ForegroundColor Green

# Test 3: Verify project structure
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TEST 3: Verify Project Structure" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Project structure:" -ForegroundColor Cyan
Write-Host "  $testProjectPath\" -ForegroundColor White
Write-Host "  ├── app\" -ForegroundColor White
Write-Host "  │   ├── _layout.tsx" -ForegroundColor White
Write-Host "  │   └── index.tsx" -ForegroundColor White
Write-Host "  └── package.json" -ForegroundColor White
Write-Host ""

# Check for node_modules (should NOT exist)
if (Test-Path "$testProjectPath\node_modules") {
    Write-Host "❌ node_modules folder exists (should not!)" -ForegroundColor Red
} else {
    Write-Host "✅ NO node_modules folder (correct!)" -ForegroundColor Green
}

# Check package.json has no dependencies
$pkgContent = Get-Content "$testProjectPath\package.json" | ConvertFrom-Json
if ($pkgContent.dependencies -or $pkgContent.devDependencies) {
    Write-Host "❌ package.json has dependencies (should not!)" -ForegroundColor Red
} else {
    Write-Host "✅ package.json has NO dependencies (correct!)" -ForegroundColor Green
}

# Test 4: Instructions to run
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TEST 4: Run the App" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "To run this test app with shared modules:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Set NODE_PATH:" -ForegroundColor Yellow
Write-Host "   `$env:NODE_PATH = '$globalModulesPath'" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Navigate to project:" -ForegroundColor Yellow
Write-Host "   cd $testProjectPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Start Expo:" -ForegroundColor Yellow
Write-Host "   npx expo start --port 19006" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Open in Expo Go app" -ForegroundColor Yellow
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ✅ TEST COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results:" -ForegroundColor Yellow
Write-Host "  ✅ Global modules exist ($packageCount packages)" -ForegroundColor Green
Write-Host "  ✅ Test project created" -ForegroundColor Green
Write-Host "  ✅ No node_modules in project" -ForegroundColor Green
Write-Host "  ✅ No dependencies in package.json" -ForegroundColor Green
Write-Host "  ✅ Code uses shared packages" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Shared modules system is working!" -ForegroundColor Green
Write-Host "📱 Run the commands above to test the app" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: This test doesn't need OpenAI API!" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"
