from __future__ import annotations
from lxml import html
from typing import Dict, List
import re
import json
import base64
import unicodedata
import requests
import csv
import os
import random
import time
import traceback
import sys
import shutil


def _notes(doc, cls: str) -> List[str]:
    xp = f"//div[contains(@class,'notes_list')]//*[@data-nt='{cls}']//text()"
    return [t for t in doc.xpath(xp) if t.strip()]


def _accords(doc) -> List[str]:
    xp = "//h2[normalize-space()='Duftrichtung']/following-sibling::*[1]//text()"
    return [t for t in doc.xpath(xp) if t.strip()]


def _rating(doc, cat: str) -> List[str]:
    xp = f"//div[contains(@class,'rating-details') and @data-type='{cat}']/@data-voting_distribution"
    res = doc.xpath(xp)
    return json.loads(base64.b64decode(res[0])) if res else None


def _classification(text, chart: str) -> List[str]:
    pattern = f"{chart}.data = (\\[[^\\]]+\\]);"
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


def _download_data_for_perfume(brand_query: str, name_query: str) -> None:
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


def download_all_data():
    snapshot_path = "perfumes_table_snapshot.csv"
    output_path = "perfumes.csv"
    error_path = "errors.csv"

    with (
        open(snapshot_path, newline="", encoding="utf-8") as infile,
        open(output_path, "a", newline="", encoding="utf-8") as outfile,
        open(error_path, "a", newline="", encoding="utf-8") as errfile,
    ):
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(
            outfile,
            fieldnames=[
                "id",
                "brand query",
                "name query",
                "brand",
                "name",
                "concentration",
            ],
        )
        errwriter = csv.DictWriter(
            errfile,
            fieldnames=["id", "brand query", "name query", "error", "stack trace"],
        )

        if not os.path.isfile(output_path):
            writer.writeheader()

        for _ in range(333):
            next(reader)

        for row in reader:
            try:
                id_ = row["ID"]
                marke = row["Marke"]
                name = row["Name"]

                print(f"Processing {id_}: {marke} - {name}...")

                data = _download_data_for_perfume(marke, name)
                writer.writerow(
                    {"id": id_, "brand query": marke, "name query": name, **data}
                )
                outfile.flush()
            except Exception as e:
                print(f"Error on {id_}: {marke} - {name}: {e}")

                if not os.path.isfile(error_path):
                    errwriter.writeheader()

                errwriter.writerow(
                    {
                        "id": id_,
                        "brand query": marke,
                        "name query": name,
                        "error": str(e),
                        "stack trace": traceback.format_exc(),
                    }
                )
                errfile.flush()
                continue
            finally:
                time.sleep(random.uniform(30, 120))


def assemble_all_data():
    print("assemble_all_data is currently disabled.")
    # snapshot_path = "perfumes_table_snapshot.csv"
    # output_path = "perfumes.csv"
    # error_path = "errors.csv"

    # with (
    #     open(snapshot_path, newline="", encoding="utf-8") as infile,
    #     open(output_path, "a", newline="", encoding="utf-8") as outfile,
    #     open(error_path, "a", newline="", encoding="utf-8") as errfile,
    # ):
    #     reader = csv.DictReader(infile)
    #     writer = csv.DictWriter(
    #         outfile,
    #         fieldnames=[
    #             "id",
    #             "brand query",
    #             "name query",
    #             "brand",
    #             "name",
    #             "concentration",
    #         ],
    #     )
    #     errwriter = csv.DictWriter(
    #         errfile,
    #         fieldnames=["id", "brand query", "name query", "error", "stack trace"],
    #     )

    #     if not os.path.isfile(output_path):
    #         writer.writeheader()

    #     for _ in range(185):
    #         next(reader)

    #     for row in reader:
    #         try:
    #             id_ = row["ID"]
    #             marke = row["Marke"]
    #             name = row["Name"]

    #             print(f"Processing {id_}: {marke} - {name}...")

    #             data = _download_data_for_perfume(marke, name)
    #             writer.writerow(
    #                 {"id": id_, "brand query": marke, "name query": name, **data}
    #             )
    #             outfile.flush()
    #         except Exception as e:
    #             print(f"Error on {id_}: {marke} - {name}: {e}")

    #             if not os.path.isfile(error_path):
    #                 errwriter.writeheader()

    #             errwriter.writerow(
    #                 {
    #                     "id": id_,
    #                     "brand query": marke,
    #                     "name query": name,
    #                     "error": str(e),
    #                     "stack trace": traceback.format_exc(),
    #                 }
    #             )
    #             errfile.flush()
    #             continue
    #         finally:
    #             time.sleep(random.uniform(30, 120))


def sync_all_data():
    data_file_path = "perfumes.jsonl"
    temp_file_path = "perfumes.jsonl~"

    normalized_file_path = "perfumes.csv"
    error_file_path = "errors.csv"

    with (
        open(data_file_path, "r", encoding="utf-8") as dataf,
        open(temp_file_path, "w", encoding="utf-8") as tempf,
        open(normalized_file_path, "r", encoding="utf-8") as normalizedf,
        open(error_file_path, "r", encoding="utf-8") as errorf,
    ):
        data = {json.loads(line)["id"]: line for line in dataf}

        normalized_reader = csv.DictReader(normalizedf)
        error_reader = csv.DictReader(errorf)

        for row in normalized_reader:
            id_ = row["id"]
            brand_query = row["brand query"]
            name_query = row["name query"]
            brand = row["brand"]
            name = row["name"]
            concentration = row["concentration"] or None

            print(f"Processing {id_}: {brand} - {name}...")

            path = to_path("overview", brand, name, concentration)
            if not os.path.isfile(path):
                print(f"Missing overview file for {id_}: {brand} - {name}")
                continue

            path_classification = to_path("classification", brand, name, concentration)
            if not os.path.isfile(path_classification):
                print(f"Missing classification file for {id_}: {brand} - {name}")
                continue

            with (
                open(path, encoding="utf-8") as f_overview,
                open(path_classification, encoding="utf-8") as f_classification,
            ):
                overview_text = f_overview.read()
                classification_text = f_classification.read()

                try:
                    obj = analyze_scent(overview_text, classification_text)
                    obj |= {
                        "id": id_,
                        "brand query": brand_query,
                        "name query": name_query,
                        "brand": brand,
                        "name": name,
                        "concentration": concentration,
                    }
                    tempf.write(json.dumps(obj, ensure_ascii=False) + "\n")
                except Exception as e:
                    print(f"Error processing {id_}: {brand} - {name}: {e}")
                    print(traceback.format_exc())
                    continue

    shutil.move(temp_file_path, data_file_path)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None
    match action:
        case "download":
            download_all_data()
        case "assemble":
            assemble_all_data()
        case "sync":
            sync_all_data()
        case _:
            print(f"Unknown action: {action}")
