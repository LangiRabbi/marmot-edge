# 🐿️ Marmot Industrial Monitoring System

**Advanced Real-Time Industrial Monitoring with YOLOv11 + BoT-SORT Tracking**

A comprehensive industrial monitoring solution featuring real-time video analytics, zone-based efficiency tracking, and multi-source video stream management.

![Project Status](https://img.shields.io/badge/Status-Active%20Development-green)
![Progress](https://img.shields.io/badge/Progress-56.25%25-blue)
![Latest](https://img.shields.io/badge/Latest-FAZA%20B%20Complete-success)

## 🎯 Project Overview

Marmot is an industrial monitoring system that uses computer vision to track personnel efficiency across production workstations. The system processes real-time video feeds, detects people using YOLOv11, tracks them with BoT-SORT, and calculates efficiency metrics based on zone occupancy.

### 🔥 Key Features (Completed)

- **🎥 Multi-Source Video Processing**: RTSP, USB cameras, IP cameras, file uploads
- **👥 Real-Time Person Detection**: YOLOv11 with BoT-SORT tracking (13.8+ FPS)
- **🎯 Interactive Zone Management**: Draw, edit, resize zones on live video
- **📊 Efficiency Calculation**: Work/Idle/Other status with real-time metrics
- **🏭 Workstation Management**: Complete CRUD operations with video integration
- **📱 USB Camera Integration**: Device enumeration with live preview
- **🌐 RTSP Testing**: Connection validation with status feedback
- **🔌 Real-Time WebSocket Communication**: JWT authentication, rate limiting, connection management
- **⚡ Performance Optimized**: Up to 8 simultaneous person tracking

## 🏗️ Technology Stack

### Frontend
- **React** + **TypeScript** - Modern UI development
- **Vite** - Lightning-fast build tool
- **ShadCN/UI** - Beautiful component library
- **Tailwind CSS** - Utility-first styling
- **React Query** - Smart data fetching and caching
- **HLS.js** - HTTP Live Streaming for RTSP video

### Backend
- **FastAPI** - High-performance Python API
- **YOLOv11** - State-of-the-art object detection
- **BoT-SORT** - Multi-object tracking algorithm
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - Python ORM
- **OpenCV** - Computer vision processing

### Computer Vision
- **Person Detection**: YOLOv11 with 13.8+ FPS performance
- **Multi-Object Tracking**: BoT-SORT with persistent IDs
- **Zone Analysis**: Rectangular zones with O(1) intersection checks
- **Efficiency Metrics**: Real-time work/idle status calculation

## 🏢 Deployment Strategy

Marmot Industrial Monitoring System is designed for flexible deployment scenarios:

### Current: On-Premise PostgreSQL (Q1 2025)
- **Target**: First customer deployments with full control
- **Database**: PostgreSQL with database abstraction layer
- **Hardware**: Dedicated servers, 16GB+ RAM, optional GPU acceleration
- **Deployment**: Docker containers, VM, or shared database integration

### Future: Cloud Expansion (Q2-Q3 2025)
- **Trigger**: After 3+ successful on-premise deployments
- **Implementation**: Supabase adapter, multi-tenant architecture, cloud-native packages
- **Benefits**: Managed services, automatic scaling, reduced IT overhead

### Future: Edge Processing (Q3-Q4 2025)
- **Trigger**: Customers with >15 cameras or distributed locations
- **Implementation**: Raspberry Pi/Jetson packages, central-edge sync, lightweight models
- **Benefits**: Reduced bandwidth, local processing, improved reliability

### Hardware Requirements
- **Minimum**: Intel i5-8400, 16GB RAM, 500GB SSD ($1,500-2,500)
- **Recommended**: Intel i7-10700, 32GB RAM, RTX 3070 ($3,000-4,500)
- **Enterprise**: Xeon/EPYC, 64GB RAM, RTX 4080, RAID storage ($8,000-15,000)

**For detailed deployment specifications, hardware requirements, and IT team communication guides, see [DEPLOYMENT_STRATEGY.md](./DEPLOYMENT_STRATEGY.md)**

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ (via [nvm](https://github.com/nvm-sh/nvm))
- **Python** 3.9+
- **PostgreSQL** 12+
- **Git**

### Frontend Development

```bash
# Clone repository
git clone https://github.com/LangiRabbi/marmot-edge.git
cd marmot-edge

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:8080`

### Backend Development

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8001
```

Backend API runs on `http://localhost:8001`

## 📁 Project Structure

```
marmot-edge/
├── 📁 frontend/                 # React TypeScript frontend
│   ├── 📁 src/
│   │   ├── 📁 components/       # UI components
│   │   │   ├── VideoPlayer.tsx          # Multi-source video player
│   │   │   ├── VideoCanvasOverlay.tsx   # Zone drawing/editing
│   │   │   ├── AddWorkstationModal.tsx  # Enhanced workstation creation
│   │   │   └── WorkstationDetailsModal.tsx  # Video + zone management
│   │   ├── 📁 services/         # API integration
│   │   │   ├── workstationService.ts    # Workstation CRUD + video integration
│   │   │   ├── videoStreamService.ts    # Video stream management
│   │   │   └── zoneService.ts           # Zone management API
│   │   └── 📁 hooks/           # Custom React hooks
│   ├── 📄 package.json
│   └── 📄 vite.config.ts
├── 📁 backend/                  # FastAPI Python backend
│   ├── 📁 app/
│   │   ├── 📁 api/v1/          # API endpoints
│   │   │   ├── workstations.py         # Workstation CRUD
│   │   │   ├── video_streams.py        # Video stream management
│   │   │   ├── zones.py                # Zone management
│   │   │   └── detection.py            # YOLOv11 detection
│   │   ├── 📁 models/          # SQLAlchemy models
│   │   ├── 📁 services/        # Business logic
│   │   │   ├── yolo_service.py         # YOLOv11 + BoT-SORT
│   │   │   ├── video_service.py        # Video source management
│   │   │   └── zone_analyzer.py        # Zone analysis logic
│   │   └── 📁 workers/         # Background processing
│   │       └── video_processor.py     # Multi-threaded video processing
│   ├── 📄 requirements.txt
│   └── 📄 alembic.ini
├── 📄 plan.md                   # Development roadmap
├── 📄 CLAUDE.md                 # Development instructions
└── 📄 README.md                 # This file
```

## 🎯 Current Capabilities

### ✅ **CHECKPOINT 4 FAZA B: Video Player & Zone Management** (Completed)

**Video Processing System**
- Multi-source video support (RTSP, USB, IP, File)
- HLS.js integration for RTSP stream handling
- Real-time video player with custom controls
- Error handling with graceful fallbacks

**Zone Management**
- Interactive zone drawing with mouse
- Drag & drop zone positioning
- Resize handles for precise adjustment
- Context menu for rename/delete operations
- Max 10 zones per workstation limit
- Real-time persistence to backend API

**USB Camera Integration**
- Device enumeration via `navigator.mediaDevices`
- Live camera preview before selection
- Permission handling and error states
- Device selection with friendly names

**RTSP Integration**
- Connection testing with validation
- Mock fallback for development
- Real-time status feedback
- URL format validation

### 🎥 **Video Player Features**
```typescript
// Multi-source video player
<VideoPlayer
  src="rtsp://camera.local/stream"
  sourceType="rtsp"
  showZoneOverlay={true}
  zones={workstationZones}
  onZonesChange={handleZoneUpdate}
  maxZones={10}
/>
```

### 🎯 **Zone Drawing System**
```typescript
// Interactive zone management
<VideoCanvasOverlay
  zones={zones}
  onZonesChange={updateZones}
  isDrawingMode={true}
  maxZones={10}
/>
```

## 📊 Development Progress

| Checkpoint | Status | Completion Date | Description |
|------------|---------|-----------------|-------------|
| **0** | ✅ Complete | 2025-09-17 | Project initialization, models, FastAPI setup |
| **1** | ✅ Complete | 2025-09-17 | Basic API endpoints, CRUD operations, CORS |
| **2** | ✅ Complete | 2025-09-18 | YOLOv11 integration, BoT-SORT tracking, 13.8 FPS |
| **3** | ✅ Complete | 2025-09-18 | Video processing, multi-threading, graceful shutdown |
| **4A** | ✅ Complete | 2025-09-18 | Frontend foundation, API services, React Query |
| **4A+** | ✅ Complete | 2025-09-19 | Enhanced workstation modal, video source selection |
| **4B** | ✅ Complete | 2025-09-19 | **Video player + zone management system** |
| **4C** | 🔄 Next | - | WebSocket real-time updates |
| **5** | ⏳ Planned | - | Analytics & efficiency calculation |
| **6** | ⏳ Planned | - | Alerts & notifications |
| **7** | ⏳ Planned | - | Reports & data export |
| **8** | ⏳ Planned | - | Production deployment |

**Overall Progress: 56.25% (4.5/8 checkpoints completed)**

## 🔧 API Endpoints

### Workstations
- `GET /api/v1/workstations/` - List all workstations
- `POST /api/v1/workstations/` - Create workstation + video stream
- `PUT /api/v1/workstations/{id}` - Update workstation
- `DELETE /api/v1/workstations/{id}` - Delete workstation

### Video Streams
- `GET /api/v1/video-streams/` - List video streams
- `POST /api/v1/video-streams/` - Create video stream
- `GET /api/v1/video-streams/{id}/status` - Stream status
- `POST /api/v1/video-streams/test-rtsp` - Test RTSP connection

### Zones
- `GET /api/v1/zones/?workstation_id={id}` - Get workstation zones
- `POST /api/v1/zones/` - Create zone
- `PUT /api/v1/zones/{id}` - Update zone
- `DELETE /api/v1/zones/{id}` - Delete zone

### Detection (YOLOv11)
- `POST /api/v1/detection/image` - Single image detection
- `GET /api/v1/detection/results/{stream_id}` - Get latest results

## 🎬 Video Source Configuration

The system supports multiple video sources:

```typescript
interface VideoSourceConfig {
  type: 'rtsp' | 'usb' | 'file';
  url?: string;           // RTSP URL
  usbDeviceId?: string;   // USB camera device ID
  fileName?: string;      // Uploaded file name
}
```

### RTSP Streams
```bash
# Example RTSP URLs
rtsp://admin:password@192.168.1.100:554/stream1
rtsp://camera.local:554/live
```

### USB Cameras
- Automatic device enumeration
- Live preview before selection
- Permission-based access

### File Uploads
- Support: MP4, WebM, MOV
- Size limit: 500MB
- Drag & drop interface

## 🎯 Zone-Based Efficiency Logic

```typescript
// Efficiency calculation formula
efficiency = work_time / (total_time - break_time)

// Zone status determination
if (person_count === 1) status = "Work"
else if (person_count === 0) status = "Idle"
else status = "Other" // >1 person
```

## 🧪 Testing

### Frontend Testing
```bash
# Run development server
npm run dev

# Test workstation creation with video sources
# Test zone drawing on video player
# Test USB camera enumeration
# Test RTSP connection validation
```

### Backend Testing
```bash
# Run YOLOv11 detection test
python backend/quick_test.py

# Test video processing
python backend/test_video_streaming.py

# Run API tests
pytest backend/tests/
```

## 🚀 Next Steps (FAZA C)

**WebSocket Real-time Updates** (3-4h estimated)
- [ ] WebSocket client with auto-reconnection
- [ ] Real-time zone status updates
- [ ] Person detection visualization overlays
- [ ] Live efficiency metrics streaming
- [ ] Connection status UI
- [ ] < 100ms latency for updates

## 📝 Latest Changes (2025-09-19)

### 🎥 Complete Video Player System
- **VideoPlayer Component**: Multi-source support (RTSP/HLS/USB/File)
- **VideoCanvasOverlay**: Interactive zone drawing with full CRUD
- **USB Camera Integration**: Real device enumeration + live preview
- **RTSP Testing**: Connection validation with user feedback

### 🔗 Backend Integration
- **VideoStreamService**: Complete API coverage for video streams
- **Auto-Stream Creation**: Workstation creation → Video stream setup
- **Zone Persistence**: Real-time zone saving to backend API
- **Error Handling**: Graceful fallbacks throughout the system

### 🏗️ Architecture Improvements
- **Enhanced Modals**: AddWorkstationModal + WorkstationDetailsModal integration
- **Service Layer**: Complete API abstraction with mock fallbacks
- **Type Safety**: Full TypeScript integration across components
- **Performance**: Efficient zone drawing with resize handles

## 🤝 Contributing

This is an active development project. See `plan.md` for detailed development roadmap and `CLAUDE.md` for development instructions.

## 📜 License

Private development project.

---

**🎯 Ready for FAZA C: WebSocket Real-time Detection Overlays**

*Built with ❤️ using Claude Code*