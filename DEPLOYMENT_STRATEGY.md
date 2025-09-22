# Deployment Strategy & Future Roadmap

## Current Status: On-Premise PostgreSQL Focus

**Decision**: Priorytet na on-premise deployment z PostgreSQL jako primary database.
**Timeline**: Q1 2025 - Dokończyć WebSocket + first customer deployments

## Future Expansion Options

### Cloud Expansion (Q2-Q3 2025)
**Trigger**: Po 3+ successful on-premise deployments
**Implementation**:
- Supabase adapter dla database abstraction layer
- Multi-tenant database schema
- Cloud-native deployment packages
**Effort**: 3-4 tygodnie development

### Edge Processing (Q3-Q4 2025)
**Trigger**: Customers z >15 cameras lub distributed locations
**Implementation**:
- Edge device packages (Raspberry Pi, Jetson)
- Central-edge sync protocols
- Lightweight YOLOv11 models
**Effort**: 6-8 tygodni development + hardware testing

### Hybrid Deployments (2026)
**Trigger**: Enterprise customers z complex requirements
**Implementation**:
- Edge processing + Cloud management
- Multi-location coordination
- Advanced analytics aggregation

## Hardware Specifications

### On-Premise Minimum Requirements
- CPU: Intel i5-8400 (6 cores) / AMD Ryzen 5 3600
- RAM: 16GB DDR4
- Storage: 500GB SSD + 2TB HDD
- Network: Gigabit Ethernet
- GPU: Optional (GTX 1660+) - 3-5x performance boost
- Cost: $1500-2500

### On-Premise Recommended (5-15 cameras)
- CPU: Intel i7-10700 (8 cores) / AMD Ryzen 7 5700X
- RAM: 32GB DDR4
- GPU: RTX 3070 / RTX 4060 Ti (significant YOLOv11 acceleration)
- Storage: 1TB SSD + 4TB HDD
- Cost: $3000-4500

### Enterprise Configuration (15+ cameras)
- CPU: Intel Xeon / AMD EPYC (16+ cores)
- RAM: 64GB+ DDR4 ECC
- GPU: RTX 4080 / A4000 Professional
- Storage: 2TB NVMe + 8TB+ RAID
- Network: 10Gb + enterprise switch
- Additional: UPS, redundant storage, climate control
- Cost: $8000-15000

## Customer Existing Server Integration

### Docker Deployment (Recommended)
- Requires: Docker 20.10+, 16GB RAM dedicated, 200GB storage
- Benefits: Isolation, easy updates, standard deployment
- IT Effort: Medium

### VM Deployment
- Requires: VMware/Hyper-V, dedicated VM resources
- Benefits: Integration with existing infrastructure
- IT Effort: Medium-High

### Shared Database Integration
- Requires: PostgreSQL 12+ access, schema management
- Benefits: Leverages existing DB infrastructure
- IT Effort: High (requires DBA involvement)

## IT Team Communication Guide

### Technical Spec Sheet Template
```
Marmot Industrial Monitoring System
- Technology: Docker containers, PostgreSQL, Python/React
- Ports: 8001 (API), 8080 (Web UI), 5432 (Database)
- Storage: 500GB+ for video retention (configurable)
- Resources: 16GB RAM minimum, 32GB recommended
- CPU: 8+ cores for real-time AI processing
- GPU: Optional but recommended for performance
- Network: Gigabit ethernet, RTSP camera access
- Security: On-premise deployment, no cloud dependencies
- Maintenance: Quarterly updates, automated backups
```

### Key Value Propositions for IT
1. **Security**: All data stays on customer network
2. **Standards**: Uses industry-standard protocols and containers
3. **Maintenance**: Low maintenance overhead with Docker deployment
4. **Flexibility**: No vendor lock-in, open architecture
5. **Support**: Technical support and training included

### Common IT Concerns & Responses
- **"Another system to maintain"** → Containerized deployment minimizes maintenance
- **Security risks** → On-premise deployment, no external data transmission
- **Integration complexity** → Standard APIs, existing network infrastructure
- **Performance impact** → Dedicated resources, optimized processing pipeline
- **Vendor lock-in** → Open architecture, customer owns all data

## Decision Points & Triggers

### When to add Cloud capability
- 3+ customers ask about SaaS option
- Competition offers cloud-first solutions
- Customer feedback indicates preference for managed service

### When to add Edge processing
- Customer has >15 cameras per location
- Network bandwidth limitations identified
- Distributed facility requirements (multiple buildings)
- Real-time processing requirements <100ms

### When to consider Hybrid architecture
- Enterprise customers with complex multi-site requirements
- Compliance needs requiring local processing + cloud analytics
- Competitive differentiation opportunity identified

## Risk Mitigation

### Technical Risks
- **Over-engineering**: Focus on current customer needs first
- **Abstraction complexity**: Keep interfaces simple and focused
- **Performance degradation**: Validate no performance impact from abstraction

### Business Risks
- **Feature creep**: Resist adding cloud/edge until customer demand proven
- **Resource allocation**: Don't split development focus too early
- **Market timing**: Wait for clear market signals before major pivots

## Success Metrics

### Short-term (6 months)
- 3+ successful on-premise deployments
- <2 hours average deployment time
- Zero post-deployment technical escalations
- Customer satisfaction >4.5/5 for deployment experience

### Long-term (12 months)
- Decision point reached on cloud/edge expansion
- Clear ROI demonstrated for current architecture
- Scalable deployment process established
- Technical debt minimized for future expansion

## Implementation Architecture

### Database Abstraction Layer
```
Frontend (React/TypeScript)
├── services/database/factory.ts
├── services/database/interface.ts
├── services/database/postgresql-service.ts
└── services/database/supabase-service.ts (future)

Backend (FastAPI/Python)
├── core/database_service.py (Protocol interfaces)
├── core/database_factory.py (Factory pattern)
├── core/postgresql_service.py (Current implementation)
├── core/supabase_service.py (future)
└── core/config.py (Deployment configuration)
```

### Configuration Management
```bash
# Environment Variables
DEPLOYMENT_TYPE=onpremise  # onpremise|cloud|edge
DATABASE_TYPE=postgresql   # postgresql|supabase|sqlite
STORAGE_TYPE=local        # local|s3|azure|gcs
AUTH_TYPE=local          # local|oauth|saml|ldap

# On-premise specific
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marmot
MAX_VIDEO_STREAMS=8
VIDEO_PROCESSING_THREADS=2

# Cloud specific (future)
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_ANON_KEY=eyJ...
AWS_BUCKET_NAME=marmot-storage

# Edge specific (future)
CENTRAL_SERVER_URL=https://central.marmot.com
SYNC_INTERVAL=300
```

### Validation & Testing
- All existing tests must pass
- Zero changes in API contracts
- Performance cannot degrade
- Deploy on localhost works identically

---

*Last updated: 2025-09-22*
*Next review: After first customer deployment*