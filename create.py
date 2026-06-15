#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from cleanup import scrub_tree


DEFAULT_MODEL = "gpt-5.5"
SYSTEM_MESSAGE = """Du bist ein präziser technischer Dokumentationsgenerator für OPNsense-Konfigurationen.

Erzeuge ausschließlich eine vollständige Markdown-Datei für doku.md.
Schreibe auf Deutsch und verwende immer korrekte Umlaute, also Ä, Ö, Ü, ä, ö, ü und ß.
Nutze ausschließlich Informationen aus der bereitgestellten, bereinigten config.xml.
Erfinde keine Werte. Wenn ein Wert nicht sichtbar ist, schreibe "nicht sichtbar" oder "nicht konfiguriert".
Schreibe keine Geheimnisse, Schlüssel, Passwörter, Tokens, Zertifikats-Private-Keys oder PSK-Werte aus.

Die Ausgabe muss sich an der vorhandenen doku.html orientieren:
- Titel: "# OPNsense Konfigurationsdokumentation"
- Danach Metadatenzeilen: Quelle, System, Zeitzone, Dokumentationsstand
- Danach exakt diese Hauptabschnitte:
  1. Kurzüberblick
  2. System- und Basisdienste
  3. Interface-Übersicht
  4. Physische Port-Zuordnung
  5. VLAN-Dokumentation
  6. DHCP und DNS
  7. VPN-Dokumentation
  8. Firewall- und Routing-Kontext
  9. Auffälligkeiten und Empfehlungen
  10. Zusammenfassung der Netze

Formatregeln:
- Gib nur Markdown aus, ohne erklärenden Vor- oder Nachtext.
- Verwende kompakte Tabellen für strukturierte Daten.
- Verwende Backticks für technische Namen, IPs, Netze, Interfaces und Dienste.
- Verwende in Markdown-Tabellen innerhalb einer Tabellenzelle kein senkrechtes Pipe-Zeichen. Schreibe stattdessen "und".
- Setze keine HTML-Blöcke ein.
- Halte die Dokumentation sachlich und prüfbar.
"""

USER_PROMPT_TEMPLATE = """Analysiere diese bereinigte OPNsense config.xml und erzeuge daraus die komplette doku.md.

Aktuelles Datum für den Dokumentationsstand: {document_date}
Name der ursprünglichen Quelle: {source_name}

Bereinigte config.xml:

```xml
{config_xml}
```
"""


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def find_config() -> Path:
    if Path("config.xml").exists():
        return Path("config.xml")

    matches = sorted(
        path
        for path in Path(".").glob("config*.xml")
        if not path.stem.endswith("-clean")
    )
    if not matches:
        raise FileNotFoundError("Keine config.xml oder config*.xml im aktuellen Ordner gefunden.")
    if len(matches) > 1:
        names = ", ".join(str(path) for path in matches)
        raise RuntimeError(
            f"Mehrere Config-Dateien gefunden: {names}. Bitte mit --config explizit auswählen."
        )
    return matches[0]


def clean_config(source: Path, target: Path) -> int:
    tree = ET.parse(source)
    removed = scrub_tree(tree.getroot())
    tree.write(target, encoding="utf-8", xml_declaration=True)
    return removed


def call_openai(model: str, user_prompt: str, max_output_tokens: int, temperature: float | None) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Das Python-Paket 'openai' fehlt. Installation: python -m pip install openai"
        ) from exc

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY ist nicht gesetzt. Lege ihn als Umgebungsvariable oder in .env ab."
        )

    client = OpenAI()
    request = {
        "model": model,
        "instructions": SYSTEM_MESSAGE,
        "input": user_prompt,
        "max_output_tokens": max_output_tokens,
    }
    if temperature is not None:
        request["temperature"] = temperature

    try:
        response = client.responses.create(**request)
    except Exception as exc:
        if temperature is None:
            raise
        message = str(exc).lower()
        if "temperature" not in message and "unsupported" not in message and "unknown parameter" not in message:
            raise
        request.pop("temperature", None)
        response = client.responses.create(**request)

    output = getattr(response, "output_text", None)
    if output:
        return output

    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    if chunks:
        return "\n".join(chunks)

    raise RuntimeError("Die OpenAI API hat keinen Text für doku.md zurückgegeben.")


def normalize_markdown(text: str) -> str:
    cleaned = text.strip()
    fence = re.fullmatch(r"```(?:markdown|md)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    if not cleaned.startswith("# "):
        raise RuntimeError("Die OpenAI-Ausgabe sieht nicht wie eine vollständige Markdown-Dokumentation aus.")
    return cleaned.rstrip() + "\n"


def render_html(markdown: Path, html: Path) -> None:
    subprocess.run(
        [sys.executable, str(Path("render.py")), str(markdown), str(html)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bereinigt eine OPNsense config.xml, erzeugt doku.md per OpenAI API und rendert doku.html."
    )
    parser.add_argument("--config", type=Path, help="Pfad zur OPNsense config.xml")
    parser.add_argument("--clean-config", type=Path, default=Path("config-clean.xml"), help="Ziel für bereinigte XML")
    parser.add_argument("--markdown", type=Path, default=Path("doku.md"), help="Ziel für Markdown")
    parser.add_argument("--html", type=Path, default=Path("doku.html"), help="Ziel für HTML")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL), help="OpenAI Modell")
    parser.add_argument("--date", default=date.today().isoformat(), help="Dokumentationsstand")
    parser.add_argument("--max-output-tokens", type=int, default=20000, help="Maximale Ausgabetokens")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperatur für möglichst stabile Ausgabe. Bei API-Ablehnung wird ohne Temperatur erneut versucht.",
    )
    parser.add_argument("--skip-render", action="store_true", help="Nur doku.md erzeugen, render.py nicht starten")
    parser.add_argument("--env-file", type=Path, default=Path(".env"), help="Optionale .env-Datei")
    args = parser.parse_args()

    load_dotenv(args.env_file)

    source = args.config or find_config()
    removed = clean_config(source, args.clean_config)
    print(f"{removed} sensible XML-Elemente bereinigt: {args.clean_config}")

    config_xml = args.clean_config.read_text(encoding="utf-8")
    user_prompt = USER_PROMPT_TEMPLATE.format(
        document_date=args.date,
        source_name=source.name,
        config_xml=config_xml,
    )

    print(f"Erzeuge {args.markdown} über OpenAI Responses API mit Modell {args.model} ...")
    markdown = normalize_markdown(
        call_openai(
            model=args.model,
            user_prompt=user_prompt,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
        )
    )
    args.markdown.write_text(markdown, encoding="utf-8")
    print(f"Geschrieben: {args.markdown}")

    if not args.skip_render:
        render_html(args.markdown, args.html)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Fehler beim Rendern: {exc}", file=sys.stderr)
        raise SystemExit(exc.returncode or 1)
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        raise SystemExit(1)
