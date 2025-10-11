from __future__ import annotations
from lxml import html
from typing import Dict, List
import re
import json
import base64
import unicodedata
import requests
import random
import time
import traceback
import argparse


def _notes(doc, cls: str) -> List[str]:
    xp = f"//div[contains(@class,'notes_list')]//*[@data-nt='{cls}']//text()"
    return [t for t in doc.xpath(xp) if t.strip()]


def _rating(doc, cat: str) -> List[str]:
    xp = f"//div[contains(@class,'rating-details') and @data-type='{cat}']/@data-voting_distribution"
    res = doc.xpath(xp)
    return json.loads(base64.b64decode(res[0])) if res else None


def _classification1(text, chart: str) -> List[str]:
    pattern = f"{chart}.data = (\\[[^\\]]+\\]);"
    match = re.search(pattern, text)
    if not match:
        return None
    data = json.loads(match.group(1))
    return {item["ct_name"]: int(item["votes"]) for item in data}


def _classification2(text, chart: str) -> List[str]:
    pattern = f"createAm5Chart\\('pie', '{chart}', (\\[[^\\]]+\\]),"
    match = re.search(pattern, text)
    if not match:
        return None
    data = json.loads(match.group(1))
    return {item["ct_name"]: int(item["votes"]) for item in data}


def analyze_scent(
    parfumo_text: str, parfumo_classification_text: str
) -> Dict[str, List[str] | str]:
    parfumo_doc = html.fromstring(parfumo_text)

    obj = {
        "scent": _rating(parfumo_doc, "scent"),
        "longevity": _rating(parfumo_doc, "durability"),
        "sillage": _rating(parfumo_doc, "sillage"),
        "pricing": _rating(parfumo_doc, "pricing"),
        "season": _classification1(parfumo_classification_text, "chart3") or _classification2(parfumo_classification_text, "chartdiv3"),
        "occasion": _classification1(parfumo_classification_text, "chart2") or _classification2(parfumo_classification_text, "chartdiv2"),
        "type": _classification1(parfumo_classification_text, "chart4") or _classification2(parfumo_classification_text, "chartdiv4"),
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


_headers = {
    "Host": "www.parfumo.de",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.parfumo.de",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.parfumo.de/",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "TE": "trailers",
    "Cookie": (
        "PHPSESSID=7mptei66ljk0ukdvv6r61coadp; "
        "_sp_enable_dfp_personalized_ads=false; "
        "_sp_su=false; "
        "euconsent-v2=CQX48QAQX48QAAGABBENB3FgAAAAAAAAAAYgAAAAAAAA.YAAAAAAAAAAA; "
        "consentUUID=08c152e4-488b-4897-9e40-636baa8ede10_48; "
        "consentDate=2025-09-17T18:31:38.222Z; "
        "_ga_DVZQF4Y622=GS2.1.s1758133974$o1$g1$t1758133987$j47$l0$h0; "
        "_ga=GA1.1.593544889.1758133975"
    ),
}


def to_path_part(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .replace("-", "_")
        .replace("/", "_")
    )


def to_path(filetype: str, brand: str, name: str, concentration: str | None) -> str:
    return f"data/{filetype}/{to_path_part(brand)} - {to_path_part(name)}{f' - {to_path_part(concentration)}' if concentration else ''}.html"


def save_data(
    filetype: str, brand: str, name: str, concentration: str | None, text: str
) -> None:
    path = to_path(filetype, brand, name, concentration)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _download_data_for_perfume(brand_query: str, name_query: str) -> Dict[str, str]:
    normalized_name_query = (
        name_query.replace("(EdT", "(Eau de Toilette")
        .replace("(EdP", "(Eau de Parfum")
        .replace("(EdC", "(Eau de Cologne")
        .replace("(EDT", "(Eau de Toilette")
        .replace("(EDP", "(Eau de Parfum")
        .replace("(EDC", "(Eau de Cologne")
    )

    livesearch_response = requests.post(
        "https://www.parfumo.de/action/livesearch/livesearch.php",
        headers=_headers,
        data={"q": f"{brand_query} {normalized_name_query}", "iwear": "0"},
    )
    livesearch_response.raise_for_status()
    livesearch_doc = html.fromstring(livesearch_response.text)
    overview_url = livesearch_doc.xpath(
        "//div[contains(@class, 'ls-perfume-item')]//a/@href"
    )[0]

    brand = livesearch_doc.xpath(
        "//div[contains(@class, 'ls-perfume-info')]//span[contains(@class, 'brand')]/text()"
    )[0].strip()
    name = livesearch_doc.xpath(
        "//div[contains(@class, 'ls-perfume-info')]//div[contains(@class, 'name')]/text()"
    )[0].strip()
    concentration = livesearch_doc.xpath(
        "//div[contains(@class, 'ls-perfume-info')]//div[contains(@class, 'name')]//span/text()"
    )
    concentration = concentration[0].strip() if concentration else None

    save_data("livesearch", brand, name, concentration, livesearch_response.text)

    overview_response = requests.get(
        overview_url,
        headers=_headers,
    )
    overview_response.raise_for_status()
    save_data("overview", brand, name, concentration, overview_response.text)

    classification_match = re.search(
        "getClassificationChart\\('pie',(\\d+),'([^']+)'\\);", overview_response.text
    )
    classification_data = {
        "p": classification_match.group(1),
        "h": classification_match.group(2),
        "csrf_key": re.search("csrf_key:'([^']+)'", overview_response.text).group(1),
    }
    classification_response = requests.post(
        "https://www.parfumo.de/action/perfume/get_classification_pie.php",
        headers=_headers,
        data=classification_data,
    )
    classification_response.raise_for_status()
    save_data(
        "classification", brand, name, concentration, classification_response.text
    )

    return {
        "brand": brand,
        "name": name,
        "concentration": concentration,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect missing perfume data.")
    parser.add_argument("-i", "--input", required=True, help="Path to queries file")
    parser.add_argument("-o", "--output", required=True, help="Path to static data output file")
    args = parser.parse_args()

    queries_path = args.input
    static_data_path = args.output

    iteration = 0

    with (open(queries_path, encoding="utf-8") as queries_file,
          open(static_data_path, "a", encoding="utf-8") as static_data_file):
        for query_string in queries_file:
            query = json.loads(query_string)
            id_ = query["id"]
            brand_query = query["brandQuery"]
            name_query = query["nameQuery"]
            print(f"Processing {id_}: {brand_query} - {name_query}...")

            if iteration > 0:
                time.sleep(random.uniform(0.5, 2))
            iteration += 1

            try:
                base_data = _download_data_for_perfume(brand_query, name_query)
                brand = base_data["brand"]
                name = base_data["name"]
                concentration = base_data["concentration"]

                overview_path = to_path("overview", brand, name, concentration)
                classification_path = to_path("classification", brand, name, concentration)
                with (
                    open(overview_path, encoding="utf-8") as overview_file,
                    open(classification_path, encoding="utf-8") as classification_file,
                ):
                    overview_text = overview_file.read()
                    classification_text = classification_file.read()

                    additional_data = analyze_scent(overview_text, classification_text)
                    all_data = {
                        "id": id_,
                        "brandQuery": brand_query,
                        "nameQuery": name_query,
                        "brand": brand,
                        "name": name,
                        "concentration": concentration,
                    } | additional_data
                    static_data_file.write(json.dumps(all_data, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"Error: {e}")
                print(traceback.format_exc())
                continue
