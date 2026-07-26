import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from openpyxl import Workbook

from app.config import (
    GENERIC_VARIANT_FILE,
    HEAVY_DIESEL_VARIANT_FILE,
    LIGHT_DIESEL_VARIANT_FILE,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TrainTypeVariant:
    display_name: str
    json_path: str


class RebuildService:
    def __init__(self) -> None:
        self._variants: dict[str, TrainTypeVariant] = {
            "Generic": TrainTypeVariant("Generic", GENERIC_VARIANT_FILE),
            "Heavy Diesel": TrainTypeVariant("Heavy Diesel", HEAVY_DIESEL_VARIANT_FILE),
            "Light Diesel": TrainTypeVariant("Light Diesel", LIGHT_DIESEL_VARIANT_FILE),
        }

    def get_available_train_types(self) -> list[str]:
        return list(self._variants.keys())

    def _load_variant_json(self, train_type: str) -> dict[str, Any]:
        variant = self._variants.get(train_type)
        if variant is None:
            raise ValueError(f"Unknown train type: '{train_type}'")

        if not os.path.exists(variant.json_path):
            raise FileNotFoundError(f"Variant file not found: {variant.json_path}")

        logger.info("Loading train type variant from: %s", variant.json_path)
        with open(variant.json_path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)

        required_keys = {"sheet_name", "cells", "column_widths", "row_heights", "merged_cells"}
        missing = required_keys - set(data.keys())
        if missing:
            raise ValueError(
                f"Variant file '{variant.json_path}' is missing required keys: {', '.join(sorted(missing))}"
            )

        return data

    def generate_excel(self, train_type: str, output_path: str) -> None:
        data = self._load_variant_json(train_type)

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = data["sheet_name"]

        for address, cell_data in data["cells"].items():
            worksheet[address] = cell_data.get("value")

        for col, width in data["column_widths"].items():
            if width is not None:
                worksheet.column_dimensions[col].width = width

        for row_num, height in data["row_heights"].items():
            if height is not None:
                worksheet.row_dimensions[int(row_num)].height = height

        for merged_range in data["merged_cells"]:
            try:
                worksheet.merge_cells(merged_range)
            except Exception:
                logger.warning("Merge error for range %s", merged_range, exc_info=True)

        workbook.save(output_path)
        logger.info("Saved rebuilt workbook for '%s' to: %s", train_type, output_path)