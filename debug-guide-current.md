# Current Stage Debugging Guide - Post-SQLite Migration

## Quick Status Check

### ✅ WORKING Systems
- **Backend Server**: http://localhost:8001 - Health endpoint responds ✅
- **Database Seeding**: SQLite insert operations working ✅
- **API Endpoints**: Workstations list returns 6 workstations + zones ✅
- **Frontend**: React dev server on http://localhost:8083 ✅
- **File Upload**: Native HTML label approach working ✅

### 🔍 Current Development Focus
**Stage**: CHECKPOINT 4 - Frontend Completion & WebSocket Integration
**Priority**: Video Player & Zone Drawing + Real-time Updates

## Immediate Testing Protocol

### 1. Backend Health Check
```bash
# Test core endpoints
curl http://localhost:8001/health
# Expected: {"status":"healthy","service":"marmot-backend","environment":"development"}

curl http://localhost:8001/api/v1/workstations/
# Expected: Array of 6 workstations with zones

# Test seeding (if needed)
curl -X POST http://localhost:8001/api/v1/seed/?force=true
# Expected: {"message":"Database seeded successfully","workstations_created":6,"zones_created":8}
```

### 2. Frontend Integration Test
```bash
# Check if frontend can connect to backend
# Open browser: http://localhost:8083
# Check console for API calls to localhost:8001
# Verify workstations load from backend (not mock data)
```

### 3. File Upload Verification
```bash
# Test via frontend:
# 1. Click "Add Workstation"
# 2. Select "Upload Video File"
# 3. Click "Add File" button
# 4. Verify file dialog opens
# 5. Select a video file
# 6. Verify file shows in form
```

## Current Issues & Solutions

### Fixed Issues ✅
1. **SQLite Timestamp Error**: Fixed `datetime.utcnow` to `lambda: datetime.utcnow()`
2. **Multiple Backend Processes**: Cleaned up, running single process on port 8001
3. **File Upload Dialog**: Native HTML label approach working

### Monitoring Areas 🔍
1. **Memory Usage**: Check for memory leaks in video processing
2. **Database Locks**: SQLite concurrent access issues
3. **CORS Errors**: Frontend-backend communication
4. **WebSocket Connections**: When implementing real-time features

## Development Workflow

### Before Each Feature Implementation:
1. **Test Current State**:
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8001/api/v1/workstations/
   ```

2. **Check Frontend**:
   - Open http://localhost:8083
   - Verify no console errors
   - Test existing functionality

3. **Database Backup**:
   ```bash
   cp backend/marmot_industrial.db backend/marmot_industrial.db.backup
   ```

### After Each Change:
1. **API Testing**:
   ```bash
   # Test changed endpoints
   curl -X POST http://localhost:8001/api/v1/new-endpoint
   ```

2. **Frontend Testing**:
   - Refresh browser
   - Test affected components
   - Check browser console

3. **Database Verification**:
   ```bash
   sqlite3 backend/marmot_industrial.db ".tables"
   sqlite3 backend/marmot_industrial.db "SELECT COUNT(*) FROM workstations;"
   ```

## Next Development Steps

### 1. Video Player Component (Priority 1)
**File**: `src/components/VideoPlayer.tsx`
```bash
# Test plan:
# 1. Create basic video player component
# 2. Test with uploaded video files
# 3. Add canvas overlay for zones
# 4. Test zone drawing functionality
```

### 2. WebSocket Real-time Updates (Priority 2)
**Files**:
- `backend/app/api/v1/websockets.py`
- `src/services/websocketService.ts`

```bash
# Test plan:
# 1. Implement backend WebSocket endpoints
# 2. Test connection with wscat
# 3. Add frontend WebSocket client
# 4. Test real-time data flow
```

### 3. Zone Management Integration (Priority 3)
```bash
# Test plan:
# 1. Test zone CRUD operations
# 2. Verify zone persistence
# 3. Test video-zone coordinate mapping
# 4. Test zone status updates
```

## Performance Monitoring

### Resource Usage
```bash
# Monitor backend process
ps aux | grep uvicorn
htop

# Monitor database size
ls -lh backend/marmot_industrial.db

# Monitor frontend bundle size
npm run build
ls -lh dist/
```

### API Performance
```bash
# Test response times
time curl http://localhost:8001/api/v1/workstations/

# Load testing (when needed)
ab -n 100 -c 10 http://localhost:8001/api/v1/workstations/
```

## Troubleshooting Common Issues

### Backend Won't Start
```bash
# Check port conflicts
netstat -ano | findstr :8001
# Kill conflicting processes if needed

# Check database permissions
ls -la backend/marmot_industrial.db

# Check Python dependencies
cd backend && pip list | grep -E "(fastapi|sqlalchemy|uvicorn)"
```

### Frontend Build Errors
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check TypeScript errors
npm run type-check
```

### Database Corruption
```bash
# Check database integrity
sqlite3 backend/marmot_industrial.db "PRAGMA integrity_check;"

# Restore from backup if needed
cp backend/marmot_industrial.db.backup backend/marmot_industrial.db

# Re-seed if necessary
curl -X POST http://localhost:8001/api/v1/seed/?force=true
```

## CI/CD Integration

### GitHub Actions Status
- ✅ **Basic CI Pipeline**: Created `.github/workflows/ci.yml`
- 🔄 **Testing**: Backend tests, frontend tests, integration tests
- 🔄 **Security**: Bandit scan, npm audit, secret detection

### Local Testing Before Commit
```bash
# Run full test suite locally
cd backend && python -m pytest tests/ -v
npm test
npm run build

# Run linting
cd backend && flake8 . --max-line-length=88
npm run lint

# Test Docker build (if available)
docker build -t marmot-backend backend/
```

## Success Metrics

### Current Stage Goals
- [ ] Video player component renders videos
- [ ] Zone drawing works on video canvas
- [ ] WebSocket connection established
- [ ] Real-time zone status updates
- [ ] All tests passing in CI

### Performance Targets
- Backend response time: < 200ms for API calls
- Frontend load time: < 3 seconds
- Video processing: > 10 FPS for real-time analysis
- Memory usage: < 1GB for full stack

## Emergency Procedures

### System Recovery
```bash
# Quick reset - if everything breaks
git stash
git checkout main
npm install
cd backend && pip install -r requirements.txt

# Start fresh backend
cd backend && rm marmot_industrial.db
curl -X POST http://localhost:8001/api/v1/seed/?force=true
```

### Data Recovery
```bash
# If database corrupted
cp backend/marmot_industrial.db.backup backend/marmot_industrial.db

# If git history needed
git log --oneline -10
git checkout <last-known-good-commit>
```