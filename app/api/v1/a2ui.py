"""
A2UI Schema Discovery Endpoint.
Allows frontend component registries to discover supported A2UI components and layouts.
"""

from fastapi import APIRouter
from app.schemas.a2ui import (
    ChartData,
    MapData,
    MetricCardData,
    PhotoGalleryData,
    DataTableData,
)

router = APIRouter()


@router.get("/a2ui/catalog", summary="Get A2UI component catalog & schemas")
async def get_a2ui_catalog():
    """
    Returns the supported A2UI declarative components and their JSON schemas.
    """
    return {
        "version": "1.0",
        "description": "Agent-to-User Interface (A2UI) Declarative Visual Component Specification",
        "supported_components": [
            {
                "type": "chart",
                "description": "Interactive multi-type chart (bar, line, pie, doughnut) for statistical breakdown.",
                "schema": ChartData.model_json_schema(),
            },
            {
                "type": "map",
                "description": "Interactive map with pins/markers and coordinates (311 locations, library branches).",
                "schema": MapData.model_json_schema(),
            },
            {
                "type": "metric_card",
                "description": "Stat indicator cards with deltas and status flags.",
                "schema": MetricCardData.model_json_schema(),
            },
            {
                "type": "photo_gallery",
                "description": "Interactive media gallery for NYPL historical digital archives & prints.",
                "schema": PhotoGalleryData.model_json_schema(),
            },
            {
                "type": "data_table",
                "description": "Sortable, searchable data grid for municipal datasets.",
                "schema": DataTableData.model_json_schema(),
            },
        ]
    }
