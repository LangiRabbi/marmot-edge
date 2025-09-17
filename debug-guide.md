# Debugging Guide - Industrial Monitoring System

## General Debugging Workflow

Before each commit, follow this procedure:
1. **Unit Tests** - Run all unit tests
2. **Integration Tests** - Test API endpoints 
3. **Manual Testing** - Test functionality manually
4. **Performance Check** - Monitor memory and CPU usage
5. **Frontend Integration** - Ensure React app still works

## Tools Required

### Testing Tools
- `pytest` - Unit and integration testing
- `curl` / `httpie` - API endpoint testing
- `postman` - API testing with GUI
- `docker logs` - Container debugging

### Monitoring Tools
- `htop` - CPU and memory monitoring
- `docker stats` - Container resource usage
- `pg_stat_activity` - PostgreSQL connection monitoring

### Development Tools
- `uvicorn --reload` - Hot reload during development
- `python -m pdb` - Python debugger
- Browser DevTools - WebSocket and network debugging

---

## CHECKPOINT 0: Project Initialization

### Debug Checklist
- [ ] Python virtual environment activated
- [ ] All dependencies install without errors
- [ ] Database connection successful
- [ ] FastAPI server starts without errors
- [ ] Health endpoint returns 200

### Testing Commands
```bash
# Install and test environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Test database connection
python -c "from app.database import engine; print('DB connected:', engine.connect())"

# Test FastAPI server
python app/main.py

# Test health endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

**Jam Usage**: Record debugging sessions for environment setup issues, monitor console logs during initial server startup

### Common Issues
- **Import errors**: Check Python path and module structure
- **Database connection failed**: Verify PostgreSQL is running
- **Port already in use**: Kill existing processes on port 8000
- **Dependencies conflict**: Use fresh virtual environment

### Debug Commands
```bash
# Check running processes
lsof -i :8000

# View database logs
docker logs postgres_container

# Test database manually
psql -h localhost -U user -d industrial_monitoring
```

---

## CHECKPOINT 1: Basic API Endpoints

### Debug Checklist
- [ ] All API endpoints return correct HTTP status codes
- [ ] Database queries execute successfully  
- [ ] CORS headers present for frontend requests
- [ ] API documentation accessible at `/docs`
- [ ] Frontend can consume API responses

### Testing Commands
```bash
# Test workstations endpoint
curl http://localhost:8000/api/v1/workstations
# Expected: [] or list of workstations

# Test create workstation
curl -X POST http://localhost:8000/api/v1/workstations \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Test Station&location=Factory Floor"
# Expected: {"id": 1, "name": "Test Station", "status": "created"}

# Test zones endpoint
curl http://localhost:8000/api/v1/workstations/1/zones
# Expected: [] or list of zones

# Test CORS
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:8000/api/v1/workstations
# Expected: CORS headers in response
```

### Performance Testing
```bash
# Load test with Apache Bench
ab -n 100 -c 10 http://localhost:8000/api/v1/workstations

# Check database connections
psql -h localhost -U user -d industrial_monitoring \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

### Common Issues
- **404 errors**: Check route definitions and imports
- **CORS errors**: Verify CORS middleware configuration
- **Database errors**: Check model definitions and migrations
- **Slow responses**: Add database indexes, optimize queries

---

## CHECKPOINT 2: YOLOv11 Integration

### Debug Checklist
- [ ] YOLOv11 model downloads and loads successfully
- [ ] Person detection works on test images
- [ ] Zone analysis logic returns correct status
- [ ] Detection results saved to database
- [ ] Confidence thresholds work as expected

### Testing Commands
```bash
# Test YOLO model loading
python -c "from ultralytics import YOLO; model = YOLO('yolov11n.pt'); print('Model loaded')"

# Test detection service
python -c "from app.services.yolo_service import yolo_service; print(yolo_service.model)"

# Test image upload endpoint
curl -X POST http://localhost:8000/api/v1/workstations/1/upload-image \
  -F "file=@test_image.jpg"
# Expected: {"people_detected": N, "zones": [...]}

# Test zone analysis
curl -X POST http://localhost:8000/api/v1/workstations/1/analyze \
  -F "file=@factory_floor.jpg"
# Expected: Zone statuses calculated correctly
```

**Jam Usage**: Record detection testing sessions, monitor network requests during image uploads, debug zone analysis calculations in real-time

### Performance Testing
```bash
# Monitor memory usage during detection
python -m memory_profiler app/services/yolo_service.py

# Test detection speed
time curl -X POST http://localhost:8000/api/v1/detect \
  -F "file=@test_image.jpg"
```

### Test Images Required
- `test_empty.jpg` - Empty scene (should return 0 people)
- `test_one_person.jpg` - One person (zones should show "Work")  
- `test_multiple_people.jpg` - Multiple people (zones should show "Other")
- `test_complex_scene.jpg` - Complex industrial scene

### Common Issues
- **CUDA/GPU errors**: Ensure YOLO runs on CPU if no GPU
- **Memory errors**: Reduce image size or batch processing
- **False detections**: Adjust confidence thresholds
- **Slow inference**: Consider lighter YOLO models

---

## CHECKPOINT 3: Video Processing

### Debug Checklist
- [ ] Can connect to RTSP streams
- [ ] USB camera detection works
- [ ] IP camera integration successful
- [ ] Frame processing pipeline operational
- [ ] Error handling and reconnection working

### Testing Commands
```bash
# Test RTSP connection
python -c "import cv2; cap = cv2.VideoCapture('rtsp://example.com/stream'); print('RTSP:', cap.isOpened())"

# Test USB camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('USB cam:', cap.isOpened())"

# Test video processing service
curl -X PUT http://localhost:8000/api/v1/workstations/1/video-source \
  -d "video_source_type=rtsp&video_source_url=rtsp://example.com/stream"

# Check video processing logs
tail -f logs/video_processor.log
```

### Performance Monitoring
```bash
# Monitor CPU usage during video processing
htop

# Check memory usage
ps aux | grep python | grep video

# Monitor frame processing rate
tail -f logs/app.log | grep "FPS:"
```

### Test Video Sources
- **RTSP Stream**: `rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4`
- **USB Camera**: Index 0, 1, 2 (depending on system)
- **IP Camera**: Local IP camera or public test streams
- **Video File**: Upload MP4 file for testing

### Common Issues
- **Connection timeout**: Check network connectivity and credentials
- **High CPU usage**: Reduce frame processing frequency
- **Memory leaks**: Ensure proper cleanup of video captures
- **Frame drops**: Optimize detection pipeline

---

## CHECKPOINT 4: WebSocket Real-time Updates

### Debug Checklist
- [ ] WebSocket connections establish successfully
- [ ] Real-time zone updates broadcast to clients
- [ ] Multiple client connections handled
- [ ] Connection cleanup on disconnect
- [ ] Frontend receives and processes updates

### Testing Commands
```bash
# Test WebSocket connection with wscat
npm install -g wscat
wscat -c ws://localhost:8000/ws/workstation/1

# Test from Python
python -c "
import asyncio
import websockets

async def test():
    uri = 'ws://localhost:8000/ws/workstation/1'
    async with websockets.connect(uri) as websocket:
        message = await websocket.recv()
        print(f'Received: {message}')

asyncio.run(test())
"

# Monitor WebSocket connections
curl http://localhost:8000/api/v1/websockets/status
```

### Frontend Integration Test
```javascript
// Test in browser console
const ws = new WebSocket('ws://localhost:8000/ws/workstation/1');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Received:', JSON.parse(event.data));
ws.onerror = (error) => console.error('Error:', error);
```

### Performance Testing
```bash
# Test multiple connections
for i in {1..10}; do
  wscat -c ws://localhost:8000/ws/workstation/1 &
done

# Monitor connection count
ss -tulpn | grep :8000
```

### Common Issues
- **Connection refused**: Check WebSocket endpoint configuration
- **Memory leaks**: Ensure proper connection cleanup
- **Message flooding**: Implement rate limiting
- **CORS issues**: Configure WebSocket CORS properly

---

## CHECKPOINT 5: Analytics & Efficiency Calculation

### Debug Checklist
- [ ] Time tracking accurate across status changes
- [ ] Efficiency calculation follows correct formula
- [ ] Settings can be updated and persisted
- [ ] Historical data properly stored
- [ ] Background analytics tasks running

### Testing Commands
```bash
# Test efficiency calculation  
python -c "
from app.services.efficiency_calculator import EfficiencyCalculator
calc = EfficiencyCalculator()
eff = calc.calculate_zone_efficiency(480, 60, 30, 30)  # 8h work, 1h idle, 30min other, 30min break
print(f'Efficiency: {eff}%')
# Expected: ~89.2%
"

# Test settings API
curl http://localhost:8000/api/v1/settings
curl -X PUT http://localhost:8000/api/v1/settings \
  -H "Content-Type: application/json" \
  -d '{"analytics": {"break_duration_minutes": 45}}'

# Check background tasks
ps aux | grep celery
```

**Jam Usage**: Record efficiency calculation testing sessions, monitor background analytics tasks, debug time tracking accuracy issues

### Manual Calculation Verification
Use Jam to record and debug efficiency calculation testing sessions:
```python
# Test efficiency calculation manually with Jam recording
work_time = 480  # 8 hours in minutes
idle_time = 60   # 1 hour
other_time = 30  # 30 minutes  
break_time = 30  # 30 minutes break

total_time = work_time + idle_time + other_time  # 570 minutes
productive_time = total_time - break_time        # 540 minutes
efficiency = (work_time / productive_time) * 100 # 88.89%

print(f"Efficiency: {efficiency:.2f}%")
```

**Jam Benefits**: Record the calculation process, monitor console output, debug edge cases with AI assistance

### Common Issues
- **Incorrect calculations**: Verify formula implementation
- **Time zone issues**: Ensure UTC consistency
- **Data inconsistency**: Add validation for time tracking
- **Performance issues**: Optimize database queries

---

## CHECKPOINT 6: Alerts & Notifications

### Debug Checklist
- [ ] All alert types trigger correctly
- [ ] Alert thresholds configurable
- [ ] Real-time alerts via WebSocket
- [ ] Notification recipients manageable
- [ ] No duplicate alerts sent

### Testing Commands
```bash
# Test device offline alert
# Disconnect camera and wait for threshold time

# Test no operator alert  
# Ensure zone stays empty for configured duration

# Test extended break alert
# Configure break threshold and simulate long idle

# Test alert API
curl http://localhost:8000/api/v1/alerts/test
curl -X POST http://localhost:8000/api/v1/settings/notification-recipients \
  -d "name=Test User&email=test@example.com&role=supervisor"
```

### Alert Scenarios
1. **Device Offline**: Disconnect camera, wait 5 minutes (default)
2. **No Operator**: Empty zone for 10+ minutes  
3. **Extended Break**: Zone idle for 30+ minutes
4. **Low Efficiency**: Workstation efficiency below threshold

### Common Issues
- **Alert spam**: Implement cooldown periods
- **False alerts**: Fine-tune detection thresholds
- **Missing alerts**: Check background task execution
- **Email issues**: Verify SMTP configuration

---

## CHECKPOINT 7: Reports & Data Export

### Debug Checklist
- [ ] Efficiency reports generate correctly
- [ ] Data export works for all formats
- [ ] Date range filtering accurate
- [ ] Large dataset performance acceptable
- [ ] CSV format properly structured

### Testing Commands
```bash
# Test efficiency report
curl "http://localhost:8000/api/v1/reports/efficiency?start_date=2024-01-01&end_date=2024-01-31"

# Test data export
curl "http://localhost:8000/api/v1/reports/export?workstation_id=1&format=json" > export.json
curl "http://localhost:8000/api/v1/reports/export?workstation_id=1&format=csv" > export.csv

# Verify CSV format
head -5 export.csv
csvstat export.csv
```

### Performance Testing
```bash
# Test large dataset export
curl "http://localhost:8000/api/v1/reports/export?workstation_id=1&start_date=2023-01-01&format=csv"

# Monitor database performance
psql -h localhost -U user -d industrial_monitoring \
  -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Common Issues
- **Timeout on large exports**: Implement pagination
- **Memory issues**: Stream data instead of loading all
- **Incorrect CSV format**: Validate CSV structure
- **Query performance**: Add database indexes

---

## CHECKPOINT 8: Production Deployment

### Debug Checklist
- [ ] All containers start successfully
- [ ] Database migrations run correctly
- [ ] Environment variables properly set
- [ ] Logging system operational
- [ ] Health checks passing

### Testing Commands
```bash
# Build and test Docker containers
docker-compose build
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs postgres
docker-compose logs redis

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/workstations

# Test database in container
docker-compose exec postgres psql -U user -d industrial_monitoring -c "SELECT version();"
```

### Security Testing
```bash
# Check for exposed secrets
grep -r "password\|secret\|key" . --exclude-dir=.git

# Test HTTPS (if configured)
curl -I https://your-domain.com

# Verify firewall rules
iptables -L
```

### Performance Testing
```bash
# Load test
ab -n 1000 -c 50 http://localhost:8000/api/v1/workstations

# Monitor container resources
docker stats

# Check disk usage
df -h
```

### Common Issues
- **Container startup failures**: Check environment variables
- **Database connection issues**: Verify container networking
- **Performance problems**: Adjust resource limits
- **Security concerns**: Review exposed ports and secrets

---

## General Troubleshooting

### Log Files
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`  
- Video processing: `logs/video.log`
- Database logs: Check PostgreSQL data directory

### Environment Variables
Always verify these are set correctly:
- `DATABASE_URL`
- `REDIS_URL` 
- `SECRET_KEY`
- `YOLO_MODEL_PATH`
- `ALLOWED_ORIGINS`

### Quick Health Checks
```bash
# Database connectivity
python -c "from app.database import get_db; next(get_db())"

# Redis connectivity  
redis-cli ping

# Model loading
python -c "from app.services.yolo_service import yolo_service; print(yolo_service.model is not None)"

# API availability
curl http://localhost:8000/health
```