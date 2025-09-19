from unittest import TestCase
from collect_missing_data import analyze_scent


class Test(TestCase):
    def test__pyramid(self):
        parfumo_text = open(
            "data/overview/Francesca Bianchi - Byzantine Amber.html", encoding="utf-8"
        ).read()
        parfumo_classification_text = open(
            "data/classification/Francesca Bianchi - Byzantine Amber.html",
            encoding="utf-8",
        ).read()

        data = analyze_scent(parfumo_text, parfumo_classification_text)

        assert data == {
             # "scent": 79.476,
            "scent": {
                "0": 2,
                "10": 1,
                "20": 1,
                "30": 0,
                "40": 3,
                "50": 8,
                "60": 6,
                "70": 33,
                "80": 91,
                "90": 34,
                "100": 12,
            },
            # "longevity": 85.926,
            "longevity": {
                "0": 0,
                "10": 1,
                "20": 0,
                "30": 0,
                "40": 0,
                "50": 0,
                "60": 1,
                "70": 11,
                "80": 56,
                "90": 70,
                "100": 23,
            },
            # "sillage": 79.568,
            "sillage": {
                "0": 0,
                "10": 0,
                "20": 0,
                "30": 0,
                "40": 0,
                "50": 1,
                "60": 8,
                "70": 34,
                "80": 86,
                "90": 20,
                "100": 13,
            },
            # "pricing": 7.4,
            "pricing": {
                "0": 1,
                "10": 0,
                "100": 6,
                "20": 2,
                "30": 1,
                "40": 0,
                "50": 4,
                "60": 12,
                "70": 32,
                "80": 29,
                "90": 16,
            },
            "structure": "pyramid",
            "head": ["Zimt", "Bergamotte"],
            "heart": ["Rosengeranie"],
            "base": ["Styrax", "Benzoe", "Labdanum", "Ambra", "Leder", "Weihrauch"],
            "season": {"Frühling": 24, "Sommer": 14, "Herbst": 77, "Winter": 77},
            "occasion": {
                "Täglich": 17,
                "Freizeit": 53,
                "Ausgehen": 68,
                "Arbeit": 14,
                "Abend": 73,
            },
            "type": {
                "Würzig": 61,
                "Süß": 25,
                "Rauchig": 68,
                "Orientalisch": 36,
                "Ledrig": 74,
                "Holzig": 28,
                "Harzig": 62,
                "Animalisch": 26,
            },
        }

    def test__linear(self):
        parfumo_text = open(
            "data/overview/Matiere Premiere - Oud Seven.html", encoding="utf-8"
        ).read()
        parfumo_classification_text = open(
            "data/classification/Matiere Premiere - Oud Seven.html", encoding="utf-8"
        ).read()

        data = analyze_scent(parfumo_text, parfumo_classification_text)

        assert data["structure"] == "linear"
        assert data["notes"] == [
            "ägyptisches Veilchenblatt Absolue",
            "indonesisches Patchouli",
            "bangladeschisches Oud",
            "spanisches Labdanum Absolue",
            "Amber",
            "Balkan-Tabak Absolue",
            "haitianisches Vetiver",
            "Nagarmotha",
        ]

    def test__analyze_scent__without_pricing_data(self):
        parfumo_text = open(
            "data/overview/Diptyque - L'Eau de Tarocco.html", encoding="utf-8"
        ).read()
        parfumo_classification_text = open(
            "data/classification/Diptyque - L'Eau de Tarocco.html", encoding="utf-8"
        ).read()

        assert (
            analyze_scent(parfumo_text, parfumo_classification_text)["pricing"] is None
        )
        assert (
            analyze_scent(parfumo_text, parfumo_classification_text)["scent"]
            is not None
        )

    def test__analyze_scent__without_classification_chart(self):
        parfumo_text = open(
            "data/overview/Mr Marvis - Club Marevista.html", encoding="utf-8"
        ).read()
        parfumo_classification_text = open(
            "data/classification/Mr Marvis - Club Marevista.html", encoding="utf-8"
        ).read()

        assert analyze_scent(parfumo_text, parfumo_classification_text)["type"] is None
        assert (
            analyze_scent(parfumo_text, parfumo_classification_text)["occasion"]
            is not None
        )
