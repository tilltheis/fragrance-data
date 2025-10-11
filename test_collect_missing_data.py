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
                "20": 2,
                "30": 1,
                "40": 0,
                "50": 4,
                "60": 12,
                "70": 32,
                "80": 29,
                "90": 16,
                "100": 6,
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

    def test__new_pyramid(self):
        parfumo_text = open(
            "data/overview/Etat Libre d'Orange - Like This.html", encoding="utf-8"
        ).read()
        parfumo_classification_text = open(
            "data/classification/Etat Libre d'Orange - Like This.html",
            encoding="utf-8",
        ).read()

        data = analyze_scent(parfumo_text, parfumo_classification_text)

        assert data == {
            "scent": {
                "0": 1,
                "10": 3,
                "20": 1,
                "30": 10,
                "40": 12,
                "50": 28,
                "60": 56,
                "70": 98,
                "80": 64,
                "90": 47,
                "100": 17,
            },
            "longevity": {
                "0": 0,
                "10": 0,
                "20": 2,
                "30": 1,
                "40": 3,
                "50": 22,
                "60": 31,
                "70": 123,
                "80": 48,
                "90": 5,
                "100": 16,
            },
            "sillage": {
                "0": 0,
                "10": 0,
                "20": 7,
                "30": 2,
                "40": 8,
                "50": 53,
                "60": 69,
                "70": 70,
                "80": 18,
                "90": 5,
                "100": 7,
            },
            "pricing": {
                "0": 0,
                "10": 0,
                "20": 2,
                "30": 0,
                "40": 5,
                "50": 9,
                "60": 15,
                "70": 31,
                "80": 23,
                "90": 5,
                "100": 8,
            },
            "structure": "pyramid",
            "head": ["Ingwer", "Kürbis", "Mandarine"],
            "heart": ["Immortelle", "Neroli", "Rose"],
            "base": ["Heliotrop", "Moschus", "Vetiver"],
            "season": {"Winter": 66, "Herbst": 134, "Sommer": 43, "Frühling": 82},
            "occasion": {
                "Täglich": 99,
                "Freizeit": 108,
                "Ausgehen": 48,
                "Arbeit": 72,
                "Abend": 67,
            },
             "type": {
                "Würzig": 123,
                "Süß": 79,
                "Pudrig": 28,
                "Holzig": 35,
                "Gourmand": 46,
                "Fruchtig": 62,
                "Blumig": 90,
            },
        }
