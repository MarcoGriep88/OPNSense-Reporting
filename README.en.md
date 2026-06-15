# opnsense-report

[Deutsch](README.md) | English

`opnsense-report` automatically creates structured documentation from an exported OPNsense configuration. The project first removes sensitive XML elements, then uses the OpenAI API to generate a German Markdown report, and can optionally render that report into a readable standalone HTML file.

The goal is a repeatable, reviewable, and quickly updateable documentation workflow for OPNsense installations, especially for operations, handovers, audits, migrations, and incident analysis.

## Features

- Removes sensitive values from an OPNsense `config.xml`
- Automatically generates a German `doku.md`
- Optionally renders `doku.md` to `doku.html`
- Structures information about interfaces, VLANs, DHCP, DNS, VPN, firewall rules, routing, and findings
- Keeps original configuration, cleaned XML, Markdown output, and HTML output separate
- Uses the OpenAI Responses API for documentation generation

## Project Files

| File | Purpose |
|---|---|
| `cleanup.py` | Removes sensitive XML elements from an OPNsense configuration. |
| `create.py` | Cleans the configuration, calls the OpenAI API, and creates `doku.md`. |
| `render.py` | Renders `doku.md` into a styled `doku.html`. |
| `config.xml` | Expected input file containing the exported OPNsense configuration. |
| `config-clean.xml` | Cleaned intermediate version of the configuration. |
| `doku.md` | Generated Markdown documentation. |
| `doku.html` | Generated HTML documentation. |
| `blogartikel.md` | Detailed German blog article about the project and technical approach. |

## Requirements

- Python 3
- An OpenAI API key
- The Python package `openai`
- An exported OPNsense configuration as an XML file

Install the required Python package:

```powershell
python -m pip install openai
```

## Configure the OpenAI API Key

The API key can be set as an environment variable:

```powershell
$env:OPENAI_API_KEY="your-api-key"
```

Alternatively, create a `.env` file in the project directory:

```env
OPENAI_API_KEY=your-api-key
```

You can also define the model through an environment variable:

```env
OPENAI_MODEL=gpt-5.5
```

If no model is configured, `create.py` uses the default value defined in the script.

## Export the OPNsense Configuration

1. Log in to the OPNsense web interface.
2. Open the configuration backup area.
3. Export the configuration as an XML file.
4. Place the file in the project directory as `config.xml`.

The exported file may contain sensitive information. Do not publish it or upload it to external systems without reviewing and cleaning it first.

## Generate Documentation

In the default case, run:

```powershell
python create.py
```

The script performs these steps:

1. Finds `config.xml` or searches for a matching `config*.xml`.
2. Removes sensitive XML elements.
3. Writes the cleaned file as `config-clean.xml`.
4. Sends the cleaned configuration to the OpenAI Responses API.
5. Saves the generated documentation as `doku.md`.
6. Automatically renders `doku.md` to `doku.html`.

## Important Options

Use a specific configuration file:

```powershell
python create.py --config path\to\config.xml
```

Generate only Markdown and skip HTML rendering:

```powershell
python create.py --skip-render
```

Use different output files:

```powershell
python create.py --clean-config cleaned.xml --markdown report.md --html report.html
```

Use a different model:

```powershell
python create.py --model gpt-5.5
```

Set a fixed documentation date:

```powershell
python create.py --date 2026-06-15
```

## Render Markdown to HTML Separately

If `doku.md` already exists or has been edited manually, the HTML file can be regenerated separately:

```powershell
python render.py doku.md doku.html
```

Without parameters, `render.py` uses `doku.md` as the source and `doku.html` as the target:

```powershell
python render.py
```

## Clean Sensitive Data Only

`cleanup.py` can also be used separately:

```powershell
python cleanup.py config.xml -o config-clean.xml
```

It clears detected sensitive XML elements. This includes tags containing terms such as:

- `password`
- `passwd`
- `passphrase`
- `preshared`
- `secret`
- `token`
- `credential`
- `privatekey`
- `psk`

The cleaning step is an important safety mechanism, but it does not replace manual review before publishing or sharing files.

## Security Notes

OPNsense configurations can contain highly sensitive information. Even cleaned documentation may still expose internal structure, such as network ranges, hostnames, service names, VPN peers, or firewall design decisions.

Recommendations:

- Do not publish the original `config.xml`.
- Review `config-clean.xml` before sharing it.
- Review `doku.md` and `doku.html` before publishing them.
- Never commit API keys to Git.
- Keep `.env` local and private.
- Remove or anonymize internal values before creating public examples.

## Typical Workflow

```powershell
python -m pip install openai
$env:OPENAI_API_KEY="your-api-key"
python create.py
```

Afterwards, these files are typically available:

- `config-clean.xml`
- `doku.md`
- `doku.html`

## Troubleshooting

### `OPENAI_API_KEY ist nicht gesetzt`

The API key is missing. Set it as an environment variable or create a `.env` file.

### `Das Python-Paket 'openai' fehlt`

Install the package:

```powershell
python -m pip install openai
```

### `Mehrere Config-Dateien gefunden`

Multiple matching XML files exist in the project directory. Specify the desired file explicitly:

```powershell
python create.py --config path\to\config.xml
```

### `Die OpenAI-Ausgabe sieht nicht wie eine vollständige Markdown-Dokumentation aus`

The API response did not match the expected format. Run the command again or check the model, token limit, and input file.

## Output Notes

The generated documentation is intended as a technical inventory. It may highlight findings and recommendations, but it does not replace expert review by administrators.

Values that are not visible or not configured are intentionally marked as such. The script should not invent values or creatively fill documentation gaps.

## More Info
[German Blogarticle about this](https://marcogriep.de/posts/opnsense-automatisch-dokumentieren-firewall-konfiguration-report/)
