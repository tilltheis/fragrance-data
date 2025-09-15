from __future__ import annotations
from lxml import html
from typing import Dict, List
import re
import json
import base64


def _notes(doc, cls: str) -> List[str]:
    xp = f"//div[contains(@class,'notes_list')]//*[@data-nt='{cls}']//text()"
    return [t for t in doc.xpath(xp) if t.strip()]


def _accords(doc) -> List[str]:
    xp = "//h2[normalize-space()='Duftrichtung']/following-sibling::*[1]//text()"
    return [t for t in doc.xpath(xp) if t.strip()]


def _rating(doc, cat: str) -> List[str]:
    xp = f"//div[contains(@class,'rating-details') and @data-type='{cat}']/@data-voting_distribution"
    return json.loads(base64.b64decode(doc.xpath(xp)[0]))


def _classification(text, chart: str) -> List[str]:
    pattern = f"{chart}.data = (\\[[^\\]]+\\]);"
    match = re.search(pattern, text)
    data = json.loads(match.group(1))
    return {item["ct_name"]: int(item["votes"]) for item in data}


def analyze_scent(
    parfumo_text: str, parfumo_classification_text: str, brand: str, name: str
) -> Dict[str, List[str] | str]:
    parfumo_doc = html.fromstring(parfumo_text)

    obj = {
        "brand": brand,
        "name": name,
        "accords": _accords(parfumo_doc),
        "scent": _rating(parfumo_doc, "scent"),
        "longevity": _rating(parfumo_doc, "durability"),
        "sillage": _rating(parfumo_doc, "sillage"),
        "pricing": _rating(parfumo_doc, "pricing"),
        "season": _classification(parfumo_classification_text, "chart3"),
        "occasion": _classification(parfumo_classification_text, "chart2"),
        "type": _classification(parfumo_classification_text, "chart4"),
    }

    notes = _notes(parfumo_doc, "n")

    if len(notes) > 0:
        obj.update(
            {
                "structure": "linear",
                "notes": _notes(parfumo_doc, "n"),
            }
        )
    else:
        obj.update(
            {
                "structure": "pyramid",
                "head": _notes(parfumo_doc, "t"),
                "heart": _notes(parfumo_doc, "m"),
                "base": _notes(parfumo_doc, "b"),
            }
        )

    return obj


def _collect_statements(text: str) -> List[str]:
    doc = html.fromstring(text)
    nodes = doc.xpath("//div[contains(@class, 'statement_text_text')]")
    text_groups = (g.xpath("text()") for g in nodes)
    statements = ("\n".join(t.strip() for t in g if t.strip()) for g in text_groups)
    return [statement for statement in statements if statement]


if __name__ == "__main__":
    with open("parfumo-statements/byzantine-amber.html", "r", encoding="utf-8") as f:
        html_text = f.read()

    for statement in _collect_statements(html_text):
        print(statement)
        print("----")
