# opnsense-report

Deutsch | [English](README.en.md)

`opnsense-report` erzeugt aus einer exportierten OPNsense-Konfiguration automatisch eine strukturierte Dokumentation. Das Projekt bereinigt zuerst sensible XML-Elemente, erstellt anschließend per OpenAI API eine deutschsprachige Markdown-Dokumentation und rendert daraus optional eine gut lesbare HTML-Datei.

Das Ziel ist eine wiederholbare, prüfbare und schnell aktualisierbare Dokumentation für OPNsense-Installationen, insbesondere für Betrieb, Übergaben, Audits, Migrationen und Störungsanalyse.

## Funktionen

- Bereinigung sensibler Werte aus einer OPNsense-`config.xml`
- Automatische Generierung einer deutschsprachigen `doku.md`
- Optionales Rendering nach `doku.html`
- Strukturierte Auswertung von Interfaces, VLANs, DHCP, DNS, VPN, Firewall, Routing und Auffälligkeiten
- Klare Trennung zwischen Originalkonfiguration, bereinigter XML-Datei, Markdown-Ausgabe und HTML-Ausgabe
- Nutzung der OpenAI Responses API für die Dokumentationserstellung

## Projektdateien

| Datei | Zweck |
|---|---|
| `cleanup.py` | Entfernt sensible XML-Elemente aus einer OPNsense-Konfiguration. |
| `create.py` | Bereinigt die Konfiguration, ruft die OpenAI API auf und erzeugt `doku.md`. |
| `render.py` | Rendert `doku.md` in eine formatierte `doku.html`. |
| `config.xml` | Erwartete Eingabedatei mit der exportierten OPNsense-Konfiguration. |
| `config-clean.xml` | Bereinigte Zwischenversion der Konfiguration. |
| `doku.md` | Generierte Markdown-Dokumentation. |
| `doku.html` | Generierte HTML-Dokumentation. |
| `blogartikel.md` | Ausführlicher Blogartikel zum Projekt und zum technischen Ansatz. |

## Voraussetzungen

- Python 3
- Ein OpenAI API-Schlüssel
- Das Python-Paket `openai`
- Eine exportierte OPNsense-Konfiguration als XML-Datei

Installation des benötigten Python-Pakets:

```powershell
python -m pip install openai
```

## OpenAI API-Schlüssel konfigurieren

Der API-Schlüssel kann als Umgebungsvariable gesetzt werden:

```powershell
$env:OPENAI_API_KEY="dein-api-schluessel"
```

Alternativ kann im Projektordner eine `.env`-Datei angelegt werden:

```env
OPENAI_API_KEY=dein-api-schluessel
```

Optional kann auch das Modell über eine Umgebungsvariable gesetzt werden:

```env
OPENAI_MODEL=gpt-5.5
```

Wenn kein Modell angegeben wird, verwendet `create.py` den im Skript definierten Standardwert.

## OPNsense-Konfiguration exportieren

1. In der OPNsense-Weboberfläche anmelden.
2. Den Bereich für Konfigurationssicherung öffnen.
3. Die Konfiguration als XML-Datei exportieren.
4. Die Datei im Projektordner als `config.xml` ablegen.

Die exportierte Datei kann sensible Informationen enthalten. Sie sollte nicht unbereinigt veröffentlicht oder in fremde Systeme hochgeladen werden.

## Dokumentation erzeugen

Im Standardfall genügt:

```powershell
python create.py
```

Das Skript führt diese Schritte aus:

1. `config.xml` finden oder eine passende `config*.xml` suchen.
2. Sensible XML-Elemente entfernen.
3. Die bereinigte Datei als `config-clean.xml` schreiben.
4. Die bereinigte Konfiguration an die OpenAI Responses API übergeben.
5. Die generierte Dokumentation als `doku.md` speichern.
6. `doku.md` automatisch nach `doku.html` rendern.

## Wichtige Optionen

Eine bestimmte Konfigurationsdatei verwenden:

```powershell
python create.py --config pfad\zur\config.xml
```

Nur Markdown erzeugen und HTML-Rendering überspringen:

```powershell
python create.py --skip-render
```

Andere Ausgabedateien verwenden:

```powershell
python create.py --clean-config bereinigt.xml --markdown report.md --html report.html
```

Ein anderes Modell verwenden:

```powershell
python create.py --model gpt-5.5
```

Einen festen Dokumentationsstand setzen:

```powershell
python create.py --date 2026-06-15
```

## Markdown separat nach HTML rendern

Wenn `doku.md` bereits existiert oder manuell angepasst wurde, kann die HTML-Datei separat neu erzeugt werden:

```powershell
python render.py doku.md doku.html
```

Ohne Parameter verwendet `render.py` standardmäßig `doku.md` als Quelle und `doku.html` als Ziel:

```powershell
python render.py
```

## Nur sensible Daten bereinigen

`cleanup.py` kann auch separat verwendet werden:

```powershell
python cleanup.py config.xml -o config-clean.xml
```

Dabei werden erkannte sensible XML-Elemente geleert. Dazu gehören unter anderem Tags mit Begriffen wie:

- `password`
- `passwd`
- `passphrase`
- `preshared`
- `secret`
- `token`
- `credential`
- `privatekey`
- `psk`

Die Bereinigung ist ein wichtiger Schutzmechanismus, ersetzt aber keine manuelle Prüfung vor Veröffentlichung oder Weitergabe.

## Sicherheitshinweise

OPNsense-Konfigurationen können hochsensible Informationen enthalten. Auch eine bereinigte Dokumentation kann noch interne Strukturinformationen offenlegen, zum Beispiel Netzbereiche, Hostnamen, Dienstnamen, VPN-Gegenstellen oder Firewall-Designs.

Empfehlungen:

- Originale `config.xml` nicht veröffentlichen.
- `config-clean.xml` vor Weitergabe prüfen.
- `doku.md` und `doku.html` vor Veröffentlichung prüfen.
- API-Schlüssel niemals in Git committen.
- `.env` lokal halten und nicht veröffentlichen.
- Für öffentliche Beispiele interne Werte entfernen oder anonymisieren.

## Typischer Workflow

```powershell
python -m pip install openai
$env:OPENAI_API_KEY="dein-api-schluessel"
python create.py
```

Danach liegen typischerweise diese Dateien vor:

- `config-clean.xml`
- `doku.md`
- `doku.html`

## Fehlerbehebung

### `OPENAI_API_KEY ist nicht gesetzt`

Der API-Schlüssel fehlt. Setze ihn als Umgebungsvariable oder lege eine `.env`-Datei an.

### `Das Python-Paket 'openai' fehlt`

Installiere das Paket:

```powershell
python -m pip install openai
```

### `Mehrere Config-Dateien gefunden`

Es liegen mehrere passende XML-Dateien im Projektordner. Gib die gewünschte Datei explizit an:

```powershell
python create.py --config pfad\zur\config.xml
```

### `Die OpenAI-Ausgabe sieht nicht wie eine vollständige Markdown-Dokumentation aus`

Die API-Antwort entsprach nicht dem erwarteten Format. Starte den Lauf erneut oder prüfe Modell, Tokenlimit und Eingabedatei.

## Hinweise zur Ausgabe

Die generierte Dokumentation ist als technische Bestandsaufnahme gedacht. Sie kann Auffälligkeiten und Empfehlungen enthalten, ersetzt aber keine fachliche Prüfung durch Administratorinnen oder Administratoren.

Nicht sichtbare oder nicht konfigurierte Werte werden bewusst als solche gekennzeichnet. Das Skript soll keine Werte erfinden und keine Lücken kreativ auffüllen.

## Repository

GitHub: [GitHub Repository](<LINK_ZUM_REPOSITORY>)
