# QLab Disk Performance Tester - Open Questions & HOLDs
*Version 1.0 - Erstellt am 29.07.2025*

## ⚠️ HOLD Items (Nicht bearbeiten!)

### HOLD-001: DMG Packaging
**Topic**: Desktop App Packaging
**Reason**: Nicht MVP-kritisch, erhöht Komplexität
**Impact**: Distribution bleibt GitHub-basiert
**Review**: Phase 3 (Q1 2026)

### HOLD-002: Code Signing
**Topic**: macOS Code Signierung
**Reason**: Kosten (99€/Jahr), nicht für Alpha nötig
**Impact**: Gatekeeper Warnungen bei Installation
**Review**: Bei 100+ Users

### HOLD-003: Auto-Update
**Topic**: Automatische Update-Funktion
**Reason**: Komplexität, Security Concerns
**Impact**: Manuelle Updates nötig
**Review**: Phase 3

### HOLD-004: FIO SHM Issues
**Topic**: macOS Shared Memory Limitations
**Reason**: OS-Level Problem, Workaround exists
**Impact**: Custom fio-nosmh Binary nötig
**Review**: Bei macOS Major Updates

### HOLD-005: Browser Security
**Topic**: Zukünftige Browser Restriktionen
**Reason**: Noch kein akutes Problem
**Impact**: Könnte localhost Access limitieren
**Review**: Ongoing Monitoring

## ❓ Offene Fragen (Klärung nötig)

### Technical
1. **Chart Library Choice**
   - Chart.js vs D3.js?
   - Decision: Chart.js (einfacher)
   - Status: Sprint 3
   - Dependencies: CDN oder local bundle

2. **FIO Parameter Optimization**
   - Welche Flags für macOS optimal?
   - Research nötig
   - Status: Sprint 4

3. **PDF Export Library**
   - Browser-native vs jsPDF?
   - Testing required
   - Status: Sprint 3

### Business
1. **Beta Tester Recruitment**
   - Wo finden? QLab Forum?
   - Incentives?
   - Status: Plan bis Sprint 2

2. **Support Model**
   - GitHub Issues only?
   - Community Forum?
   - Status: Phase 3 Decision

3. **Licensing**
   - MIT vs GPL?
   - Impact on QLab Integration
   - Status: Legal Review nötig

### UX/Design
1. **Quick Test Duration**
   - GEKLÄRT: 5 Min (bereits implementiert)
   - Zusätzlich: 10 Min ProRes Quick Test
   - Status: Sprint 2 Implementation

2. **Result Visualization**
   - Welche Metriken prominent?
   - Laien vs Profis Balance
   - Status: Sprint 3 Design

3. **Error Message Tone**
   - Technisch vs Freundlich?
   - Beispiele sammeln
   - Status: Sprint 1

## 🔄 Review Schedule

### Weekly Review (Freitags)
- Technical Questions
- Sprint Blockers
- Priority Changes

### Monthly Review
- HOLD Items Status
- Strategic Questions
- Resource Planning

### Quarterly Review
- Architecture Decisions
- Phase Transitions
- Budget Allocation

## 📝 Decision Log

### 29.07.2025
- **Decision**: Chart.js über D3.js
- **Reason**: Einfachere Integration
- **Impact**: Schnellere Entwicklung

### 29.07.2025
- **Decision**: Volumes als Default Path
- **Reason**: Permission Issues vermeiden
- **Impact**: Bessere UX

### 29.07.2025
- **Decision**: SQLite statt JSON für State Management
- **Reason**: Robustere Lösung, bessere Performance
- **Impact**: Migration in Sprint 5 geplant

### 29.07.2025
- **Decision**: 5 Min Quick Test beibehalten
- **Reason**: Bereits implementiert und getestet
- **Impact**: 10 Min ProRes Test als Zusatz

## 🎯 Nächste Entscheidungen

1. **Diese Woche**: Error Message Templates
2. **Sprint 2**: Beta Tester Strategy
3. **Sprint 3**: Export Format Details

---

*Updates bei jeder Entscheidung - HOLDs nur mit expliziter Freigabe bearbeiten*
