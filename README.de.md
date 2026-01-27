> English version: [README.md](README.md)

# applytrack

Automatisiertes E-Mail-Tracking für Bewerbungen über IMAP mit lokaler LLM-Extraktion und Excel-Export zur strukturierten Dokumentation von Bewerbungsaktivitäten.

---

## Projektziel

applytrack unterstützt die automatisierte Nachverfolgung von Bewerbungsprozessen durch:

- Abruf von Bewerbungs-E-Mails per IMAP
- Lokale Extraktion relevanter Informationen mittels LLM
- Zusammenführung zusammengehöriger Bewerbungen (Deduplication + Merge)
- Ergänzung fehlender Adressdaten über definierte Fallbacks
- Export in eine vordefinierte Excel-Vorlage zur Nachweisführung

---

## Welches Problem wird gelöst?

Bewerbungs-E-Mails sind stark uneinheitlich in:

- Aufbau
- Sprache
- Formulierungen
- Signaturen und Ansprechpartnern

Regex-basierte Auswertung ist dadurch:

- komplex
- fehleranfällig
- schlecht wartbar

applytrack nutzt stattdessen eine lokale LLM zur semantischen Extraktion.

Vorteile:

- robustere Inhaltserkennung
- weniger Sonderfälle
- bessere Wartbarkeit

---

## Architekturdesign

Siehe Abbildung **applytrack – System Components**  
![Komponentendiagramm](docs/diagrams/components.png)

---

## Workflow / Geschäftslogik

Siehe Abbildung **applytrack – Workflow**  
![Aktivitätsdiagramm](docs/diagrams/activity.png)

---

## Demo-Ausgabe

Beispiel einer erzeugten Excel-Ausgabe (fiktive Daten):

![Demo Excel Output](docs/images/demo_excel.png)

---

## Verwendete Technologien

- **Python 3**
- **IMAPClient** - Abruf von E-Mails per IMAP (SSL)
- **html2text** - Umwandlung von HTML Mails in Klartext
- **Ollama (lokal)** - Ausführung eines lokalen LLM (Modell: phi4)
- **OpenAI Python Client** - Nutzung der Ollama-API über OpenAI-kompatibles Interface
- **sqlite3** - Speicherung manueller und externer Adressdaten
- **openpyxl** - Export in eine Excel-Vorlage

---

## Datenschutz-Hinweis

Dieses Projekt ist ausschließlich für private Nutzung vorgesehen.

Es verarbeitet Bewerbungs-E-Mails lokal auf dem Gerät des Nutzers.  
Dabei können personenbezogene Daten enthalten sein:

- Unternehmensnamen
- Kontaktpersonen
- Stellenbezeichnungen
- Datumsangaben
- Bewerbungsstatus (Absage, Einladung, Zwischenstand)

Die Verarbeitung erfolgt:

- vollständig lokal
- nutzerinitiiert
- ohne Cloud-Übertragung

Der Nutzer ist selbst verantwortlich für die rechtmäßige Nutzung und die Einhaltung geltender Datenschutzvorschriften.

Dieses Projekt stellt keine Rechtsberatung dar.

---

## Adressdaten (optional)

Zur Ergänzung fehlender Anschriften kann eine lokale SQLite-Datenbank mit offenen Registerdaten genutzt werden  
(OffeneRegister.de oder OpenCorporates, Lizenz: CC BY 4.0).

Die Verantwortung für Attribution und Lizenzkonformität liegt beim Nutzer.

---

## Vorgesehener Anwendungsbereich

- Private Bewerbungsverwaltung
- Dokumentation eigener Bewerbungsaktivitäten
- Nachweispflichten gegenüber Behörden

---

## Nicht vorgesehene Nutzung

- Zugriff auf fremde Postfächer
- Massenhafte Datenerfassung
- Kommerzielle Nutzung oder SaaS-Betrieb
- Profiling oder automatisierte Personenbewertung

---

## Disclaimer

Dieses Projekt wird ohne Garantie bereitgestellt.  
Der Autor übernimmt keine Haftung für missbräuchliche oder rechtswidrige Nutzung.

---