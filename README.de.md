> English version: [README.md](README.md)

# applytrack


Automatisierte E-Mail-Verfolgung für Bewerbungen via IMAP mit lokaler LLM-Extraktion und DSGVO konformem Excel-Export.

---

## Projektziel
- Automatisierte Nachverfolgung von Bewerbungsprozessen
- Abruf von Bewerbungs-E-Mails per IMAP
- Lokale LLM-basierte Extraktion relevanter Informationen
- Strukturierte Zusammenführung zusammengehöriger Bewerbungen für das Ergebnis
- Auflösung fehlender Adressdaten über definierte Fallbacks
  - Manuelle Datenbank
  - OpenRegister
  - Interaktive Ergänzung
- DSGVO-konforme, lokale Verarbeitung
- Export der folgenden Ergebnisse in eine vordefinierte Excel-Vorlage
  - Unternehmensnamen
  - Kontaktdaten
  - Kontaktpersonen
  - Stellenbezeichnungen
  - Datumsangaben
  - Bewerbungsstatus

---

## Welches Problem wird gelöst?
- Vermeidung von Regex-basierter E-Mail-Auswertung
- Bewerbungs-E-Mails sind stark uneinheitlich in:
  - Aufbau
  - Sprache
  - Formulierungen
- Regex-Lösungen sind dadurch:
  - komplex
  - fehleranfällig
  - schlecht wartbar
- Einsatz einer lokalen LLM zur semantischen Extraktion
- Vorteile gegenüber Regex:
  - robustere Inhaltserfassung
  - weniger Sonderfälle
  - geringerer Wartungsaufwand

---

## Architekturdesign
Siehe Abbildung **applytrack – System Components**  
![Komponentendiagramm](docs/diagrams/components.png)

---

## Geschäftslogik
Siehe Abbildung **applytrack – Workflow**  
![Aktivitätsdiagramm](docs/diagrams/activity.png)

---

## Demo-Ausgabe
Die folgende Abbildung zeigt eine **Beispiel-Excel-Ausgabe, die von applytrack erzeugt wurde**.  
Alle dargestellten Daten sind fiktiv und dienen ausschließlich Demonstrationszwecken.

![Demo Excel Output](docs/images/demo_excel.png)

---

## Verwendete Technologien:
- Lokale Desktop-Umgebung
- Hardware: 16 GB RAM
- Laufzeitumgebung: Python 3
- Verwendete Bibliotheken und Komponenten:
  - IMAP-Zugriff: `IMAPClient`
  - E-Mail-Aufbereitung: `html2text`
  - LLM-Extraktion: `ollama` (Modell: phi4)
  - Modellansteuerung: `openai` (Python-Client, ausschließlich lokale Nutzung über Ollama)
  - Datenhaltung: `sqlite3`
  - Excel-Export: `openpyxl`
- Programmstart über `main.py`
- Zugriff ausschließlich:
  - lesend
  - per IMAP
  - auf das eigene E-Mail-Postfach
- AI als Werkzeug zum Programmieren

---

## Entwicklerdokumentation
- Dokumentation über Docstrings im Code
- Ergänzt durch:
  - Komponenten-Diagramm
  - Aktivitätsdiagramm
- Technische Referenz für:
  - Code-Struktur
  - Modulverantwortlichkeiten
  - Datenflüsse

---

# Haftungsausschluss / Disclaimer
- Ausschließlich für private Nutzung vorgesehen
- Zweck:
  - Organisation und Nachverfolgung eigener Bewerbungen
  - Verarbeitung eingehender Bewerbungs-E-Mails aus dem eigenen Postfach
- Verarbeitung personenbezogener Daten möglich:
  - Unternehmensnamen
  - Kontaktdaten
  - Kontaktpersonen
  - Stellenbezeichnungen
  - Datumsangaben
  - Bewerbungsstatus (z. B. Absage, Zwischenstand, Einladung)
- Verarbeitung erfolgt:
  - vollständig lokal
  - nutzerinitiiert
  - nutzerkontrolliert

---

## Verantwortung des Nutzers
- Nutzer ist Verantwortlicher im Sinne von Art. 4 Nr. 7 DSGVO
- Einhaltung der Datenschutzgesetze liegt vollständig beim Nutzer
- Insbesondere sicherzustellen:
  - Rechtsgrundlage gemäß Art. 6 Abs. 1 DSGVO
  - Zweckbindung und Datenminimierung (Art. 5 Abs. 1 lit. b, c DSGVO)
  - Technische und organisatorische Maßnahmen (Art. 5 Abs. 1 lit. f, Art. 32 DSGVO)
  - Aufbewahrungs- und Löschfristen (Art. 5 Abs. 1 lit. e DSGVO)
- Projektautor ist:
  - kein Verantwortlicher
  - kein Auftragsverarbeiter
  - ohne Zugriff auf verarbeitete Daten

---

## Verwendung externer Datenquellen (Adressdaten)
- Optionale Nutzung offener Registerdaten zur Adressauflösung
- Datenquelle:
  - OffeneRegister.de
  - OpenCorporates
- Lizenz:
  - Creative Commons Attribution 4.0 International (CC BY 4.0)
- Verarbeitung:
  - ausschließlich lokal
  - SQLite-Datenbank
- Zweck:
  - Ergänzung von Unternehmensanschriften
- Verantwortung für:
  - Attribution
  - Lizenzkonformität
  - rechtmäßige Nutzung
  - liegt beim Nutzer
- Weitere Informationen:
  - https://offeneregister.de
  - https://opencorporates.com

---

## Vorgesehener Anwendungsbereich
- Private Bewerbungsverwaltung
- Verarbeitung direkt empfangener E-Mails
- Persönliche Dokumentation:
  - Eigenübersicht
  - Nachweispflichten gegenüber Behörden

---

## Nicht vorgesehene Nutzung
- Zugriff auf fremde E-Mail-Postfächer
- Systematische oder massenhafte Datenerfassung
- Kommerzielle Nutzung oder SaaS-Betrieb
- Profiling oder automatisierte Personenbewertung
- Umgehung technischer oder rechtlicher Schutzmechanismen

---

## Keine Rechtsberatung
- Keine Rechtsberatung
- Keine Garantie für rechtliche Zulässigkeit
- Keine Haftung für Einsatzszenarien

---

© 2026 kaydev24. Alle rechte vorbehalten.