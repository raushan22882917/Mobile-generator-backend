# System Flow Diagram

## Complete Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  [Text Input: "Create a fitness tracking app..."]        │  │
│  │  [Generate Button]                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ WebSocket Connect
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET MANAGER                            │
│  • Accepts connection                                           │
│  • Routes messages to project                                   │
│  • Manages multiple clients                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Start Generation
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STREAMING GENERATOR                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 1: ANALYZE (5%)                                    │ │
│  │ ┌────────────────┐  ┌────────────────┐                  │ │
│  │ │ Generate Name  │  │ Analyze Screens│  ← Parallel      │ │
│  │ └────────────────┘  └────────────────┘                  │ │
│  │ Progress: "Analyzing your app requirements..."          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 2: CREATE PROJECT (15%)                            │ │
│  │ • Create directory structure                             │ │
│  │ • Initialize Expo project                                │ │
│  │ Progress: "Creating fitness-app-x7k2..."                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 3: GENERATE BASE (25%)                             │ │
│  │ • Create minimal home screen (template)                  │ │
│  │ • Write essential files                                  │ │
│  │ Progress: "Generating base app structure..."             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 4-6: SETUP PREVIEW (55%)                           │ │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │ │
│  │ │Install Deps  │ │Start Server  │ │Create Tunnel │      │ │
│  │ │   (npm i)    │ │(expo start)  │ │   (ngrok)    │      │ │
│  │ └──────────────┘ └──────────────┘ └──────────────┘      │ │
│  │                    ← All Parallel                        │ │
│  │ Progress: "Installing dependencies..."                   │ │
│  │ Progress: "Starting development server..."               │ │
│  │ Progress: "Creating preview link..."                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 7: PREVIEW READY! (60%) ✅                         │ │
│  │ • Send preview URL to client                             │ │
│  │ • User can now test the app                              │ │
│  │ Progress: "Preview ready! Generating additional..."      │ │
│  │ Data: { preview_url: "https://abc.ngrok.io" }           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 8: GENERATE SCREENS (60-85%)                       │ │
│  │ • Generate screens in batches of 2                       │ │
│  │ • Write to project directory                             │ │
│  │ • Hot reload updates preview                             │ │
│  │                                                           │ │
│  │ Batch 1: [Home, Profile]                                 │ │
│  │ Progress: "Added 2/5 screens..."                         │ │
│  │ Data: { screens_added: ["Home", "Profile"] }            │ │
│  │                                                           │ │
│  │ Batch 2: [Workout, Progress]                             │ │
│  │ Progress: "Added 4/5 screens..."                         │ │
│  │ Data: { screens_added: ["Workout", "Progress"] }        │ │
│  │                                                           │ │
│  │ Batch 3: [Settings]                                      │ │
│  │ Progress: "Added 5/5 screens..."                         │ │
│  │ Data: { screens_added: ["Settings"] }                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 9: ADD COMPONENTS (90%)                            │ │
│  │ • Create reusable components                             │ │
│  │ • Card, Button, etc.                                     │ │
│  │ Progress: "Creating reusable components..."              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 10: GENERATE IMAGES (95-100%)                      │ │
│  │ • Generate in background (non-blocking)                  │ │
│  │ • Logo, hero images, icons                               │ │
│  │ • User doesn't wait for this                             │ │
│  │ Progress: "Generating images (background)..."            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stage 11: COMPLETE! (100%) ✅                            │ │
│  │ • All done                                               │ │
│  │ • Send final result                                      │ │
│  │ Progress: "App generation complete!"                     │ │
│  │ Data: { success: true, project_id, preview_url }        │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Send Updates
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET MANAGER                            │
│  • Broadcasts progress to all clients                           │
│  • Sends to specific project                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Real-time Updates
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Progress Bar: [████████████░░░░░░░░] 60%                │  │
│  │  Stage: "Preview Ready!"                                  │  │
│  │  Message: "Scan QR code to test on your phone"           │  │
│  │                                                           │  │
│  │  [QR Code]  [Open Preview Link]                          │  │
│  │                                                           │  │
│  │  Screens Added:                                           │  │
│  │  [Home] [Profile] [Workout] [Progress] [Settings]        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Message Flow

```
Client                    WebSocket Manager           Streaming Generator
  │                              │                            │
  ├─ Connect ──────────────────→ │                            │
  │                              ├─ Accept                    │
  │                              │                            │
  ├─ Send Start ────────────────→ │                            │
  │                              ├─ Route ──────────────────→ │
  │                              │                            ├─ Start Gen
  │                              │                            │
  │                              │ ←─ Progress (5%) ─────────┤
  │ ←─ Progress Update ──────────┤                            │
  │                              │                            │
  │                              │ ←─ Progress (15%) ────────┤
  │ ←─ Progress Update ──────────┤                            │
  │                              │                            │
  │                              │ ←─ Progress (25%) ────────┤
  │ ←─ Progress Update ──────────┤                            │
  │                              │                            │
  │                              │ ←─ Progress (55%) ────────┤
  │ ←─ Progress Update ──────────┤                            │
  │                              │                            │
  │                              │ ←─ Preview Ready (60%) ───┤
  │ ←─ Preview URL ──────────────┤    + preview_url          │
  │                              │                            │
  │  [User scans QR code]        │                            │
  │  [App opens on phone]        │                            │
  │                              │                            │
  │                              │ ←─ Screen Added (65%) ────┤
  │ ←─ Screen Update ────────────┤    + screens_added        │
  │  [Screen appears in app]     │                            │
  │                              │                            │
  │                              │ ←─ Screen Added (70%) ────┤
  │ ←─ Screen Update ────────────┤    + screens_added        │
  │  [Screen appears in app]     │                            │
  │                              │                            │
  │                              │ ←─ Complete (100%) ───────┤
  │ ←─ Final Result ─────────────┤                            │
  │                              │                            │
  ├─ Disconnect ─────────────────→ │                            │
  │                              ├─ Cleanup                   │
```

## Data Flow

```
┌──────────────┐
│ User Prompt  │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Sanitize & Validate  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Generate App Name    │────→│ fitness-app-x7k2│
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Analyze Screens      │────→│ [Home, Profile, │
└──────┬───────────────┘     │  Workout, etc.] │
       │                     └─────────────────┘
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Create Project       │────→│ /projects/abc/  │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Generate Base Code   │────→│ index.tsx       │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Install Dependencies │────→│ node_modules/   │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Start Expo Server    │────→│ localhost:19006 │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Create Ngrok Tunnel  │────→│ abc.ngrok.io    │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐
│ ✅ PREVIEW READY     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Generate Screens     │────→│ profile.tsx     │
│ (Batch 1)            │     │ workout.tsx     │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Generate Screens     │────→│ progress.tsx    │
│ (Batch 2)            │     │ settings.tsx    │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Add Components       │────→│ Card.tsx        │
└──────┬───────────────┘     │ Button.tsx      │
       │                     └─────────────────┘
       ▼
┌──────────────────────┐     ┌─────────────────┐
│ Generate Images      │────→│ logo.png        │
│ (Background)         │     │ hero.png        │
└──────┬───────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────┐
│ ✅ COMPLETE          │
└──────────────────────┘
```

## Timeline Comparison

```
BEFORE (Sequential):
0s    30s   60s   90s   120s  150s  180s
├─────┼─────┼─────┼─────┼─────┼─────┤
│ Gen │ Proj│ Deps│ Srv │ Tun │ Img │
└─────┴─────┴─────┴─────┴─────┴─────┴─→ Preview Ready

AFTER (Parallel + Streaming):
0s    15s   30s   45s   60s   75s   90s   100s
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ Ana │ Proj│ Base│Setup│Scrn1│Scrn2│ Cmp │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─→ Complete
                        ↑
                   Preview Ready!
                   (User can test)
```

## Parallel Operations

```
Time: 20-45 seconds (Setup Preview Stage)

Thread 1: Install Dependencies
├─ npm install
├─ Download packages
└─ Build native modules

Thread 2: Start Server
├─ Wait for deps
├─ expo start
└─ Wait for ready

Thread 3: Create Tunnel
├─ Wait for server
├─ ngrok http 19006
└─ Get public URL

All complete → Preview Ready!
```
