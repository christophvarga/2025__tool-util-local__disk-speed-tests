# QLab Disk Performance Tester - API Dokumentation

## Überblick

Diese Dokumentation beschreibt die verfügbaren API-Endpunkte des Bridge Servers, der als Middleware zwischen dem Web-Browser und der Test-Engine (FIO) fungiert. Alle API-Calls benutzen HTTP und kommunizieren JSON-Datenformate.

## Endpunkte

### 1. `/api/status`
- **Method**: GET
- **Beschreibung**: Überprüft den aktuellen Status des Systems und des FIO-Dienstes.
- **Antwort**: JSON-Objekt mit Systemstatus und FIO-Informationen.
- **Beispiel**:
  ```json
  {
    "status": "running",
    "fio_version": "fio-3.25"
  }
  ```

### 2. `/api/disks`
- **Method**: GET
- **Beschreibung**: Listet alle verfügbaren Festplatten auf, die für Tests verwendet werden können.
- **Antwort**: JSON-Array mit Festplatteninformationen.
- **Beispiel**:
  ```json
  [
    {"name": "Macintosh HD", "path": "/dev/disk1s1", "size": "1TB"},
    {"name": "External Drive", "path": "/dev/disk2s1", "size": "500GB"}
  ]
  ```

### 3. `/api/test/start`
- **Method**: POST
- **Beschreibung**: Startet einen neuen Test mit den angegebenen Parametern.
- **Anfrageparameter**: JSON-Objekt mit Testdetails.
  ```json
  {
    "test_id": "quick_max_mix",
    "disk_path": "/dev/disk1s1",
    "size_gb": 10
  }
  ```
- **Antwort**: JSON-Objekt mit Teststatus und ID.
- **Beispiel**:
  ```json
  {
    "test_id": "12345-abcde",
    "status": "started"
  }
  ```

### 4. `/api/test/{id}`
- **Method**: GET
- **Beschreibung**: Holt den aktuellen Status für einen laufenden oder abgeschlossenen Test.
- **Antwort**: JSON-Objekt mit Testdetails.
- **Beispiel**:
  ```json
  {
    "test_id": "12345-abcde",
    "status": "in_progress",
    "progress": "50%"
  }
  ```

### 5. `/api/setup`
- **Method**: POST
- **Beschreibung**: Initialisiert die Testumgebung und überprüft die FIO-Installation.
- **Anfrageparameter**: Keine
- **Antwort**: JSON-Objekt mit Setup-Status.
- **Beispiel**:
  ```json
  {
    "status": "ready",
    "fio_installed": true
  }
  ```

### 6. `/api/validate`
- **Method**: POST
- **Beschreibung**: Führt eine Systemvalidierung durch und gibt Empfehlungen aus.
- **Anfrageparameter**: Keine
- **Antwort**: JSON-Objekt mit Validierungsergebnissen.
- **Beispiel**:
  ```json
  {
    "cpu": "supported",
    "ram": "sufficient",
    "fio_version": "latest"
  }
  ```

## Fehlercodes
- **400**: Ungültige Anfrageparameter
- **404**: Ressource nicht gefunden
- **500**: Interner Serverfehler

## Authentifizierung
Derzeit keine Authentifizierung erforderlich.

## Hinweise
Diese API ist für den lokalen Gebrauch vorgesehen und nicht für den öffentlichen Zugriff gedacht. Beachten Sie alle Datenschutz- und Sicherheitsrichtlinien Ihrer Organisation.
