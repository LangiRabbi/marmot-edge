# Industrial Monitoring System - Claude Instructions

## Project Overview
Developing an industrial monitoring system with YOLOv11 video analysis:
- **Frontend**: React + TypeScript + ShadCN/UI + Vite (COMPLETED)
- **Backend**: FastAPI + YOLOv11 + PostgreSQL + WebSockets
- **Functionality**: Real-time person detection in zones, efficiency calculation
- **Video Sources**: RTSP, USB, IP cameras, file upload
- **Logic**: 1 person = Work, 0 = Idle, >1 = Other
- **Efficiency**: work_time / (total_time - break_time)

## Development Methodology
**ONE COMPONENT AT A TIME** → debug → test → checkpoint → GitHub commit

### Debugging Workflow (Before Each Commit)
1. **Unit Tests** - Run all unit tests
2. **Integration Tests** - Test API endpoints
3. **Manual Testing** - Test functionality manually
4. **Performance Check** - Monitor memory and CPU usage
5. **Frontend Integration** - Ensure React app still works

### Required Tools
- **Testing**: pytest, curl, postman, docker logs
- **Monitoring**: htop, docker stats, pg_stat_activity
- **Development**: uvicorn --reload, python -m pdb, Browser DevTools
- **MCP**: Jam for AI-powered debugging sessions

## Project Files Structure
```
project/
├── claude.md (this file)
├── plan.md (development checkpoints)
├── debug-guide.md (debugging procedures)
├── backend/ (to be created)
└── frontend/ (existing)
```

## Key References
- **Development Plan**: See `plan.md` for detailed checkpoints
- **Debugging Guide**: See `debug-guide.md` for testing procedures
- **GitHub Actions**: See `.github/workflows/` directory

## MCP Tools Configuration
Required MCP tools for this project:
1. **github** - Code management, commits, issues
2. **Context7** - Library documentation (YOLOv11, FastAPI, SQLAlchemy)  
3. **jam** - AI-powered debugging with session recordings and console logs

## Current Status
- [ ] Project initialization
- [ ] Backend structure setup
- [ ] API development
- [ ] YOLOv11 integration
- [ ] Video processing
- [ ] WebSocket real-time updates
- [ ] Analytics & efficiency
- [ ] Alerts & notifications
- [ ] Reports & export
- [ ] Production deployment

## Next Steps
1. Review `plan.md` for current checkpoint
2. Follow debugging procedures from `debug-guide.md`
3. Update checkpoint status after each commit
4. Use MCP tools for development assistance

## Important Notes
- **ALWAYS** follow the 5-step debugging workflow before committing
- Update plan.md status after each successful checkpoint
- Use Jam MCP for recording debugging sessions during complex issues
- Follow debugging guide for each component - see `debug-guide.md`
- Create GitHub issues for any bugs found
- Test mathematical calculations with MCP tools when needed
- Monitor performance during video processing and WebSocket operations