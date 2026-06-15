#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SENSITIVE_NAME_PARTS = (
    "password",
    "passwd",
    "passphrase",
    "preshared",
    "pre_shared",
    "secret",
    "salt",
    "token",
    "credential",
)

SENSITIVE_CONTAINER_TAGS = {
    "apikeys",
    "authorizedkeys",
    "keypairs",
    "presharedkeys",
    "statickeys",
}

SENSITIVE_EXACT_TAGS = {
    "key",
    "keys",
    "keysig",
    "privkey",
    "privatekey",
    "psk",
}

NON_SECRET_TAGS = {
    "password_show",
    "passwordauth",
    "password_encryption",
    "keyingtries",
    "prefetchkey",
    "pubkeys",
    "rekey_time",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def is_sensitive_tag(tag: str) -> bool:
    name = local_name(tag)
    if name in NON_SECRET_TAGS:
        return False
    return (
        name in SENSITIVE_CONTAINER_TAGS
        or name in SENSITIVE_EXACT_TAGS
        or any(part in name for part in SENSITIVE_NAME_PARTS)
    )


def scrub_tree(root: ET.Element) -> int:
    removed = 0

    def walk(elem: ET.Element) -> None:
        nonlocal removed
        for child in list(elem):
            if is_sensitive_tag(child.tag):
                child.clear()
                child.text = ""
                removed += 1
            else:
                walk(child)

    walk(root)
    return removed


def default_input() -> Path:
    matches = sorted(
        path for path in Path(".").glob("config-*.xml") if not path.stem.endswith("-clean")
    )
    if not matches:
        raise FileNotFoundError("Keine config-*.xml im aktuellen Ordner gefunden.")
    if len(matches) > 1:
        raise RuntimeError(
            "Mehrere config-*.xml gefunden. Bitte Eingabedatei explizit angeben."
        )
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Entfernt kritische Informationen aus einer OPNsense config-*.xml."
    )
    parser.add_argument("input", nargs="?", type=Path, help="OPNsense config-*.xml")
    parser.add_argument("-o", "--output", type=Path, help="Zieldatei")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Originaldatei ueberschreiben. Ohne diese Option wird eine Kopie erzeugt.",
    )
    args = parser.parse_args()

    source = args.input or default_input()
    target = args.output or source.with_name(f"{source.stem}-clean.xml")
    if args.in_place:
        target = source

    tree = ET.parse(source)
    removed = scrub_tree(tree.getroot())
    tree.write(target, encoding="utf-8", xml_declaration=True)

    print(f"{removed} sensible XML-Elemente bereinigt: {target}")

    # delete source config if successfully written to target and in-place option is set
    if args.in_place and target != source:
        source.unlink()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        raise SystemExit(1)
