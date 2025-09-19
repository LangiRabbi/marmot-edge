# Industrial Monitoring System - Claude Instructions

## Project Overview
Developing an industrial monitoring system with YOLOv11 BoT-SORT tracking:
- **Frontend**: React + TypeScript + ShadCN/UI + Vite (COMPLETED)
- **Backend**: FastAPI + YOLOv11 + BoT-SORT + PostgreSQL + WebSockets
- **Functionality**: Multi-person tracking with persistent IDs, zone analysis, efficiency calculation
- **Video Sources**: RTSP, USB, IP cameras, file upload (tested with 720x1280 video)
- **Logic**: 1 person = Work, 0 = Idle, >1 = Other
- **Efficiency**: work_time / (total_time - break_time)
- **Performance**: 13.8+ FPS real-time tracking, up to 8 persons simultaneously

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
4. **playwright** - Frontend E2E testing and UI verification

## Current Status
- [x] Project initialization (COMPLETED)
- [x] Backend structure setup (COMPLETED)
- [x] API development (COMPLETED)
- [x] YOLOv11 BoT-SORT integration (COMPLETED)
- [x] Video processing (COMPLETED - real-time multi-threading)
- [x] Enhanced Add Workstation Modal (COMPLETED - video sources)
- [ ] WebSocket real-time updates (IN PROGRESS)
- [ ] USB Camera detection and preview
- [ ] RTSP connection testing
- [ ] Analytics & efficiency
- [ ] Alerts & notifications
- [ ] Reports & export
- [ ] Production deployment

## Next Steps
1. Review `plan.md` for current checkpoint
2. Follow debugging procedures from `debug-guide.md`
3. Update checkpoint status after each commit
4. Use MCP tools for development assistance

## Frontend Testing Protocol with Playwright MCP

### OBOWIĄZKOWE po każdej zmianie frontendu:
1. **Automatyczny test Playwright** - ZAWSZE po modyfikacji komponentów
2. **Screenshot przed/po zmianie** - dokumentacja wizualna zmian
3. **Test interakcji** - kliknięcia, formularze, navigation
4. **Konsultacja z użytkownikiem** - pokazanie wyniku testu
5. **Rzetelna ocena** - raportowanie błędów i problemów UX

### Wyjątki od testowania:
- Użytkownik może wyłączyć testy mówiąc: "bez testów" lub "skip tests"
- Drobne zmiany CSS mogą być testowane wsadowo (batch)
- Pure refactoring bez zmian UI

### Przykład workflow frontendu:
```bash
# Po zmianie komponentu React
1. Save files (Edit/Write tools)
2. npm run dev (sprawdź czy się kompiluje)
3. Playwright: screenshot i test funkcjonalności
4. Pokaż użytkownikowi: "Test pokazuje że..."
5. Czekaj na potwierdzenie przed kolejną zmianą
```

### Co testować przez Playwright:
- **UI Components**: Czy renderują się poprawnie
- **Navigation**: Menu, routing, modal opening/closing
- **Forms**: Validation, submission, error states
- **Data Loading**: Loading states, error boundaries
- **Responsive**: Mobile/desktop layouts
- **Integration**: API calls, WebSocket connections

### Raportowanie do użytkownika:
```
✅ TEST PASSED: Komponent WorkstationCard renderuje się poprawnie
📸 Screenshot: [attached]
🔧 Testowane: Kliknięcie "View Details", dropdown menu
❌ PROBLEM: Modal nie zamyka się na ESC key
```

## Latest Achievements (2025-09-19)

### 🎯 Enhanced Add Workstation Modal - COMPLETED
**Commit**: `bfa0abb feat: enhanced Add Workstation modal with video source selection`

#### Features Implemented:
- ✅ **Video Source Selection**: Radio buttons (RTSP, USB Camera, Upload File)
- ✅ **RTSP Configuration**: URL input + Test Connection button
- ✅ **USB Camera**: Device dropdown + camera preview placeholder
- ✅ **File Upload**: MP4/WebM/MOV support with 500MB validation
- ✅ **Modal Stability Fix**: Removed glass-card hover transform conflicts
- ✅ **Enhanced UX**: File size warnings, visual feedback, proper spacing
- ✅ **TypeScript**: VideoSourceConfig interface with type safety

#### Technical Solutions:
1. **Modal Jumping Issue**: Fixed by removing `glass-card:hover { transform: translateY(-1px) }` CSS conflict
2. **File Input Visibility**: Improved with `h-12` height and proper container spacing
3. **Form Validation**: 500MB file size limit with real-time warnings
4. **Conditional Rendering**: Dynamic UI based on selected video source type

#### Testing Results (Playwright):
- ✅ Modal stability during interactions
- ✅ Radio button switching works perfectly
- ✅ All video source options render correctly
- ✅ File input fully visible and functional
- ✅ Form validation and error handling working

#### Next Implementation Phase:
- [ ] Real USB camera device enumeration (`navigator.mediaDevices.enumerateDevices()`)
- [ ] Live camera preview functionality
- [ ] RTSP connection testing implementation
- [ ] Supabase storage integration for file uploads

## Important Notes
- **ALWAYS** follow the 5-step debugging workflow before committing
- **ALWAYS** test frontend changes with Playwright MCP (unless user says skip)
- Update plan.md status after each successful checkpoint
- Use Jam MCP for recording debugging sessions during complex issues
- Follow debugging guide for each component - see `debug-guide.md`
- Create GitHub issues for any bugs found
- Test mathematical calculations with MCP tools when needed
- Monitor performance during video processing and WebSocket operations
- **BE HONEST** about test results - report UI bugs and UX issues