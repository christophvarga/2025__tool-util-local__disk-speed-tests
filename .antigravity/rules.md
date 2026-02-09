---
title: llm-rule-v5.0.0
version: 5.0.0
source: rules.db
---

# LLM Rules v5.0.0

## Changelog

- **4.9.0** (25.11.2025): content_blocks Tabelle fuer komplexe Markdown-Inhalte; Vollstaendige Migration von v4.6 Inhalten (Workflow, Ordnerstruktur, Tests, Runner, Checklists, HOLD-Template); Dynamische Referenzen (keine hardcoded Dateinamen mehr).
- **4.7.0** (24.11.2025): Einführung der Rules Engine (SQLite); Konsolidierung von .droid.yaml und droid.yaml; Präzisere Stop-Gates für Architektur und Security.
- **4.8.0** (24.11.2025): Optimierung für Gemini 3 & Anthropic: Neue Sektion agent_behavior, präzisere und kürzere Guidelines, Reasoning-Anforderungen.
- **4.6.0** (23.11.2025): Globale Workspace-/Index-DB-Regeln ergänzt (repo-mapping.csv + type-scope-matrix.csv); workspace_index-Block in droid.yaml/.droid.yaml; llm-rule-v4.6 als Master-Dok; Versionen YAML/Markdown auf 4.6.0 ausgerichtet.
- **4.5.0** (20.11.2025): Regeln mit .droid.yaml synchronisiert; Diátaxis- und Dokumentationspflicht explizit; ASK-/STOP-Gates, Design-System- und Git/SSH-Regeln vereinheitlicht.
- **4.2.1** (16.09.2025): Ordnerstruktur vollständig integriert (keine externe Referenz); Erstellungsregeln + Entscheidungslogik; Runner-Fallback; kurze Migration (Legacy → kanonisch); HOLD-Minivorlage.
- **4.4.0** (07.10.2025): GitHub SSH-Setup dokumentiert; Edge-Deployment-Verweis hinzugefügt; Checklisten konsolidiert; Redundanzen eliminiert; Struktur gestrafft.
- **4.3.0** (03.10.2025): Cloudflare Tunnel & Edge-Deployment-Regeln hinzugefügt; Apps laufen über zentralen Edge-Stack (Traefik + Cloudflared); Cloudflare Access für Userverwaltung; Verweis auf Edge-Repo für Details.
- **5.0.0** (02.12.2025): CLAUDE.md Support: Neue Tabellen session_logs, repo_context, sync_status, claude_md_mapping; Generierung von ~/.claude/CLAUDE.md und ~/.claude/rules/*.md; Session-Handoff und Cross-Repo-Context; Background-Sync für alle Formate (CLAUDE.md, .droid.yaml, .antigravity/rules.md)

---

## Agent Behavior

### Output Style
- **format**: Use Markdown headers.
- **instruction**: Put critical instructions at the end of long contexts.

### Persona
- **role**: Senior Software Engineer
- **tone**: Direct, Precise, Efficient
- **instruction**: Avoid filler words. Be concise.

### Reasoning
- **trigger**: Complex tasks
- **action**: Use <thinking> tags before answering.

---

## ASK/CONFIRM/HOLD/ASSUME Regeln


- **[ASK]**: Architektur/Stack-Aenderung, Struktur-Expansion, neue Dependencies, API-Aenderung, Deployment-Aenderung, >30 Zeilen ohne [ASSUME].
- **[CONFIRM]**: 2-3 valide Optionen; kurz bewerten, Empfehlung.
- **[HOLD]**: markierte Blocker nicht bearbeiten; transparent reporten. Ablage: `00_infos/meta/open-questions.md`.
- **[ASSUME]**: lokale, reversible Edits ≤30 Zeilen ohne externe Effekte (Lint, Tippfehler).


## Coding-Standards


**Pflicht:**
- Jede relevante Aenderung braucht passende Tests; fehlende Tests im PR begruenden.
- Keine Secrets im Code; Konfiguration ausschliesslich ueber Umgebungsvariablen.
- Modular bleiben, Dateien moeglichst <300 Zeilen; keinen auskommentierten toten Code.

**Allgemein:**
- **Edit > Rewrite**; vorhandene Patterns nutzen (neue in `00_infos/patterns.md`).
- **Modular**, Dateien **<300 Zeilen**; bei Split `foo.part1.ext`, `foo.part2.ext`.
- **DRY**; **Env-aware** (dev/test/prod).
- **Lokalisierung**: Europe/Vienna; Datum `30.05.2025`; Geld `10.320,00 €`.

**Temporaere Skripte:**
- Nur wenn unbedingt noetig und kurzlebig.
- Ablage ausschliesslich unter `85_code/_temp_scripts/`.
- Keine externen Effekte ohne [ASK].
- Bei Abschluss: entfernen oder in produktiven Code ueberfuehren.


## Edge-Deployment (Pflicht fuer Web-Apps)


- Alle Web-Apps laufen ueber zentralen **Edge-Stack** (Traefik + Cloudflared).
- Keine lokalen Host-Ports oeffnen (`docker-compose.yml` ohne `ports:`).
- Service ins `web`-Netzwerk haengen; Traefik-Labels setzen (Host-Router, Entrypoint, interner Port).
- Cloudflare Access uebernimmt Userverwaltung (Service Tokens fuer CI/CD).
- GHCR privat: Am Zielserver einmalig `docker login ghcr.io`.

**Details & Templates**: Repository `infra--ci-cd`
- Pfad: `/Users/christophvarga/Documents/03_code_repos/infra--ci-cd`


## Ordnerstruktur (kanonisch)


```
<repo-root>/
├── 00_infos/                      # Kontext & Dokumentation
│   ├── llm-context.md             # Kernbrief (immer zuerst)
│   ├── patterns.md                # Wiederverwendbare Patterns
│   ├── details/                   # Architektur & Plaene
│   │   ├── architecture.md
│   │   └── grand-plan.md
│   └── meta/                      # Meta-Dokumente
│       └── open-questions.md      # HOLD-Liste (Pflichtort)
├── 85_code/                       # Produktiver Code (mehrsprachig erlaubt)
│   └── _temp_scripts/             # Nur wenn noetig: temporaere Hilfsskripte
├── 86_assets/                     # Statische Assets (UI/Medien) bei Bedarf
├── 87_tests/                      # Zentrale Tests (Standard)
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── 88_input/
│   └── testdata/                  # Anonymisierte Testdaten (klein)
├── 89_output/
│   └── test_reports/
│       ├── <YYYYMMDD-HHMM>/       # Testartefakte (junit/coverage/...)
│       └── latest -> <TS>         # Symlink auf letzten Lauf
├── 90_reports/
│   ├── test-report.md
│   ├── coverage.md
│   └── changes.md
└── 99_archiv/
    └── old_versions/              # Archivierte Versionen (Doks)
```

**Erstellungsregeln:**
- `00_infos/` ist Pflicht. Andere Ordner nur bei Bedarf anlegen; Struktur-Expansion → [ASK].
- Tests zentral in `87_tests/` (unit/integration/e2e/fixtures).
- Go: paketlokale `*_test.go` fuer Unit erlaubt; Integration/E2E nach `87_tests/`.
- JS/TS: `__tests__/` nur als Legacy; mittelfristig nach `87_tests/` migrieren.
- Temporaere Skripte ausschliesslich unter `85_code/_temp_scripts/`.


## Branches & Deployments (pre/main/demo/prod-*)

## Branches & Deployments (pre/main/demo/prod-*)

- **`pre`** – Preview/Staging-Branch. Dient fuer Reviews und QA; wird automatisch in die Preview-/Staging-Umgebung deployt (eigene Staging-DB / Staging-Secrets).
- **`main`** – Stabiler Release-Branch. Nur gepruefte Releases aus `pre` werden nach `main` gemerged; dient als Single Source of Truth fuer alle produktiven Umgebungen.
- **`prod-1`, `prod-2`, ...** – Produktions-Deploy-Branches. Jeder Branch steht 1:1 fuer einen konkreten Produktiv-Server; wird ausschliesslich aus `main` aktualisiert (Merge/Fast-Forward), kein direktes Hineinentwickeln; eigene Prod-Config/-DB/-Secrets je Branch.
- **`demo`** – Demo-Branch. Technisch eine Kopie von `main`, aber mit eigener Demo-Datenbank und Demo-Config (keine echten Kundendaten).

**Branch-Flow:**
- Feature-Branches immer von `pre` aus erstellen (`feat/...`, `fix/...` etc.) und via PR nach `pre` zurueckfuehren.
- Releases werden als PR von `pre` nach `main` gemerged (optional mit Tagging/Release-Notes).
- Produktions-Rollouts erfolgen aus `main` in die jeweiligen `prod-*`-Branches (z.B. `main → prod-1`, `main → prod-2`), niemals direkt in `prod-*` entwickeln.
- `demo` wird nur aus `main` aktualisiert (kein direktes Hineinentwickeln).

**CI/CD & Daten:**
- Relevante Branches (`pre`, `main`, `demo`, `prod-*`) haben eigene Umgebungen und Secrets (`.env.pre`, `.env.main`, `.env.demo`, `.env.prod-1`, `.env.prod-2`, ... o.ae.).
- `pre`: automatische Deployments in Staging, inklusive Migrations gegen Staging-DB.
- `main`: Release-Quelle fuer alle produktiven Deploy-Branches (`prod-*`) und Demo.
- `prod-*`: Production-Deployments pro Server, mit produktiver Config/DB; Rollout wird ausgelöst, wenn der jeweilige `prod-*`-Branch aktualisiert wird.
- `demo`: Deployments gegen Demo-Umgebung mit Seed-/Dummy-Daten; externe Integrationen nur mit Test-Keys.

**Hotfixes (Empfehlung):**
- Kritische Hotfixes als `hotfix/*` von `main` aus; nach Merge in `main` immer zurueck nach `pre`, `demo` und alle betroffenen `prod-*`-Branches mergen, damit alle Branches synchron bleiben.

## Git & SSH


- Git via SSH (`git@github.com:<user>/<repo>.git`); Remote-URLs pruefen mit `git remote -v`.
- Vor Commit: `git diff --cached` auf Secrets/Keys/Credentials pruefen (Pflicht).
- Branch-Namen: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
- SSH-Key erstellen (ed25519): `ssh-keygen -t ed25519 -C "<email>"` → Public Key bei GitHub hinterlegen.
- Commit-Format: `<type>(<scope>): <kurz>; tests:<added|updated>; bump <file>@<old>-><new>`


## HOLD-Template


Ablage: `00_infos/meta/open-questions.md`

```markdown
# Open Questions (HOLD)

## Aktive HOLDs

- [HOLD-001] Thema: <kurz> — Grund: <warum> — Besitzer: <wer> — Naechster Schritt: <was> — Datum: <YYYYMMDD>
- [HOLD-002] Thema: <kurz> — Grund: <warum> — Besitzer: <wer> — Naechster Schritt: <was> — Datum: <YYYYMMDD>

## Geloeste HOLDs

- [HOLD-003] Thema: <kurz> — Geloest am: <YYYYMMDD> — Loesung: <kurz>
```


## Migration (Legacy → kanonisch)


**Tests:**
- JS/TS: `__tests__/` und `*.test.*` nach `87_tests/` verschieben; Pfade/Imports anpassen.
- Go: Integration/E2E nach `87_tests/`; paketlokale `*_test.go` fuer Unit belassen.
- Python: paketlokale Tests optional; bevorzugt `87_tests/` nutzen.

**Artefakte/Reports:**
- Runner auf `TEST_REPORT_DIR` umstellen; alte Ausgabepfade konsolidieren.

**Temp-Skripte:**
- Ausserhalb von `85_code/_temp_scripts/` entfernen oder verschieben.

**Deployment (Web-Apps):**
- Host-Ports aus `docker-compose.yml` entfernen.
- Traefik-Labels hinzufuegen.
- `web`-Netzwerk konfigurieren.


## Pre-Commit Checklist


**Code & Struktur:**
- [ ] Patterns genutzt? (siehe `00_infos/patterns.md`)
- [ ] Keine Duplikate?
- [ ] Dateien <300 Zeilen?
- [ ] Env-ready (dev/test/prod)?
- [ ] Secrets nur via Umgebungsvariablen?

**Tests & Reports:**
- [ ] Tests gruen (Unit + Smoke/E2E)?
- [ ] Coverage ~60% auf geaendertem Code?
- [ ] Reports aktualisiert (`90_reports/`)?
- [ ] Artefakte in `89_output/test_reports/<YYYYMMDD-HHMM>/`?
- [ ] `TEST_REPORT_DIR` korrekt gesetzt?

**Versionierung:**
- [ ] Versionen gebumpt?
- [ ] Archiv ok (falls Major-Change)?

**Deployment (Web-Apps):**
- [ ] `docker-compose.yml` ohne `ports:`-Sektion?
- [ ] Service im `web`-Netzwerk registriert?
- [ ] Traefik-Labels vollstaendig gesetzt?

**Git:**
- [ ] Branch-Name korrekt (`feat/`, `fix/`, etc.)?
- [ ] Commit-Message folgt Format?
- [ ] SSH-Push erfolgreich?


## Kanonische Referenzen & Prioritaeten


- **llm-context.md** (`00_infos/llm-context.md`): Zentrale Memory-Quelle; IMMER zuerst lesen; bei relevanten Aenderungen aktualisieren und Version bumpen.
- **architecture.md** (`00_infos/details/architecture.md`): Architektur-Skizze; Architektur-Entscheidungen muessen dazu passen.
- **grand-plan.md** (`00_infos/details/grand-plan.md`): Grand-/Master-Plan; Scope und Phasen folgen diesem Plan.

**Prioritaet bei Konflikten:**
```
STOP > HOLD > Architektur > llm-context > grand-plan > sonstige Doks > Code-Kommentare
```


## Reporting (Minimum)


- **Artefakte**: `89_output/test_reports/<YYYYMMDD-HHMM>/` (z.B. `junit*.xml`, `coverage.*`).
- Optional: Symlink `89_output/test_reports/latest` → letzter Run.

**Kurzberichte (Pflicht)** in `90_reports/`:
- `test-report.md`: Datum, Suite, passed/failed, Coverage, Artefakte-Pfad.
- `coverage.md`: Gesamt A%, Delta B%.
- `changes.md`: Aenderung, betroffene Dateien, Tests added/updated, Risiken/HOLDs.

**Collector-Globs** (fuer CI/Tools):
- Tests: `89_output/test_reports/*/junit-*.xml`
- Coverage: `89_output/test_reports/*/coverage-*.xml`, `89_output/test_reports/*/coverage*/lcov.info`


## Runner-Templates (Make/Just)


**Makefile-Target:**
```makefile
.PHONY: test-report
test-report:
	@TS=$$(date +%Y%m%d-%H%M); \
	TEST_REPORT_DIR=89_output/test_reports/$$TS; \
	export TEST_REPORT_DIR; \
	mkdir -p "$$TEST_REPORT_DIR"; \
	if [ -f pyproject.toml ] || [ -f requirements.txt ]; then \
		pytest --junitxml="$$TEST_REPORT_DIR/junit-py.xml" --cov --cov-report=xml:"$$TEST_REPORT_DIR/coverage-py.xml" || true; \
	fi; \
	if [ -f package.json ]; then \
		npx --yes jest --ci --reporters=default --reporters=jest-junit --outputFile="$$TEST_REPORT_DIR/junit-js.xml" --coverage --coverageDirectory="$$TEST_REPORT_DIR/coverage-js" || true; \
	fi; \
	if [ -f go.mod ]; then \
		go test ./... -coverprofile="$$TEST_REPORT_DIR/coverage-go.out" -json > "$$TEST_REPORT_DIR/go-tests.json" || true; \
	fi; \
	rm -f 89_output/test_reports/latest && ln -s "$$TS" 89_output/test_reports/latest || true; \
	echo "Testartefakte: $$TEST_REPORT_DIR"
```

**Runner-Fallback (ohne Make/Just):**
```bash
TS=$(date +%Y%m%d-%H%M)
export TEST_REPORT_DIR=89_output/test_reports/$TS
mkdir -p "$TEST_REPORT_DIR"

# Python
if [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  pytest --junitxml="$TEST_REPORT_DIR/junit-py.xml" --cov --cov-report=xml:"$TEST_REPORT_DIR/coverage-py.xml" || true
fi

# JS/TS
if [ -f package.json ]; then
  npx --yes jest --ci --reporters=default --reporters=jest-junit --outputFile="$TEST_REPORT_DIR/junit-js.xml" --coverage --coverageDirectory="$TEST_REPORT_DIR/coverage-js" || true
fi

# Go
if [ -f go.mod ]; then
  go test ./... -coverprofile="$TEST_REPORT_DIR/coverage-go.out" -json > "$TEST_REPORT_DIR/go-tests.json" || true
fi

ln -sfn "$TS" 89_output/test_reports/latest || true
```


## Tests (Minimum)


- **Pflicht**: Unit fuer Logik, Smoke/E2E fuer Happy Path; Bugfix → Regressionstest.
- **Qualitaet**: deterministisch; Coverage-Ziel auf geaendertem Code ~60% (Unterschreitung kurz begruenden).
- **Orte & Benennung**:
  - `87_tests/unit/`, `87_tests/integration/`, `87_tests/e2e/`, `87_tests/fixtures/`
  - Python: `87_tests/` (`test_*.py`). Paketlokale Unit-Tests moeglich, bevorzugt zentral.
  - JS/TS: bevorzugt `87_tests/`; `__tests__/` neben Modulen nur als Legacy.
  - Go: Unit `*_test.go` paketlokal erlaubt; Integration/E2E unter `87_tests/`.
- **Runner**: Projekt-Runner muss `TEST_REPORT_DIR=89_output/test_reports/<YYYYMMDD-HHMM>` respektieren.
- **Kein Framework**: Smoke-Kommando (z.B. `<tool> --help`) mit Exit 0.


## Workflow (8 Schritte)


1. `llm-context` lesen, HOLDs pruefen.
2. Task abgrenzen; bei Unsicherheit [ASK]/[CONFIRM].
3. Implementieren (klein, modular, ≤30 Zeilen ohne externe Effekte → [ASSUME] ok).
4. Tests schreiben/aktualisieren (Unit + Smoke/E2E).
5. Testlauf via `make test-report` oder `just test-report`; gruen halten.
6. Artefakte nach `89_output/test_reports/<YYYYMMDD-HHMM>/` (Pflicht). `TEST_REPORT_DIR` setzen.
7. Kurzberichte in `90_reports/`: `test-report.md`, `coverage.md`, `changes.md`.
8. Versionsnummern aktualisieren; ggf. Archiv; `git add/commit/push`.


## STOP Gates (Pre-Commit)

- [ ] LLM Rules Änderung ohne [ASK]? (betrifft ALLE Projekte!)
- [ ] Design System Änderung ohne [ASK]? (betrifft alle UI-Projekte!)
- [ ] Neue Dependency ohne [ASK]?
- [ ] Offene HOLDs? (00_infos/meta/open-questions.md)
- [ ] llm-context.md aktuell und Version gebumpt?
- [ ] .antigravity/rules.md Version gebumpt bei Änderungen?
- [ ] git diff --cached auf Secrets/Keys/Credentials geprüft?
- [ ] Secrets nur via Umgebungsvariablen?
- [ ] Architektur-Change ohne Freigabe?
- [ ] Struktur-Expansion ohne Permission?
- [ ] Fehlende Tests/Reports?
- [ ] Web-App ohne Edge-Integration?
