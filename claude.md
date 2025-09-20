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

### 🎯 File Upload Dialog System - COMPLETED ✅
**Commit**: TBD - file chooser dialog fixed with native HTML label approach

#### 🐛 Critical File Upload Issues Fixed:
1. ✅ **File Chooser Dialog Not Opening** - File dialog now opens correctly for real users
2. ✅ **Remove Confusing Native Input** - Eliminated ugly gray "Wybierz plik" button
3. ✅ **Native HTML Label Solution** - Used `<label htmlFor="id">` instead of programmatic click()
4. ✅ **Clean User Interface** - Only stylized "Add File" button visible to users
5. ✅ **Real File Selection Works** - Tested with actual file: wideo_pionowe.mp4 (7.0 MB)

#### Technical Implementation:
- ✅ **label + htmlFor Pattern**: Native HTML file input activation
- ✅ **sr-only Class**: Hidden but accessible file input element
- ✅ **User Testing Verified**: Manual browser testing confirmed dialog opens
- ✅ **Playwright False Positive**: Playwright intercepts file choosers, masking real issues
- ✅ **Production Ready**: Clean, professional file upload interface

### 🎯 Complete Video Management System - COMPLETED ✅
**Commit**: `d6ebe94 fix: complete video management system with user file uploads`
3. ✅ **User-Uploaded File Integration** - Files now properly used instead of Google fallback
4. ✅ **Video Player Cleanup Error Loops** - Eliminated error cycles during modal closure
5. ✅ **React Router Warnings** - Added v7 future flags, clean console output

#### Technical Implementations:
- ✅ **isMounted Pattern**: Prevents callback execution after component unmount
- ✅ **useRef File Input**: Replaced broken document.querySelector with proper React pattern
- ✅ **VideoSourceConfig System**: Complete end-to-end video configuration architecture
- ✅ **Object URL Integration**: File upload → URL.createObjectURL() → VideoPlayer
- ✅ **Dynamic Source Resolution**: Each workstation uses its configured video source
- ✅ **Type-Safe Architecture**: Full TypeScript integration with proper interfaces

#### Testing Results (Real Files):
- ✅ **File Upload**: `wideo_pionowe.mp4` (7.0 MB) successfully uploaded and played
- ✅ **Multiple Sources**: RTSP, USB Camera, File Upload all supported
- ✅ **Clean Console**: No errors during video lifecycle (load → play → cleanup)
- ✅ **Workstation Persistence**: Video configs saved and retrieved correctly
- ✅ **Fallback System**: Graceful degradation when video config missing

#### Production Ready Features:
- ✅ **Error-Free Operation**: Clean console throughout video lifecycle
- ✅ **Multi-Source Support**: RTSP streams, USB cameras, uploaded files
- ✅ **File Storage Ready**: Easy cloud storage integration (S3, etc.)
- ✅ **Performance Optimized**: Proper cleanup prevents memory leaks
- ✅ **Future-Proof**: React Router v7 compatibility

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