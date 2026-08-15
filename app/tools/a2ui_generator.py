"""
A2UI Component Builders & Utilities.
Transforms raw query responses from NYC Open Data and NYPL archives into interactive A2UI payloads.
"""

from typing import List, Dict, Any, Optional
import re
from app.schemas.a2ui import (
    A2UIComponent,
    A2UIPayload,
    ChartData,
    ChartDataset,
    MapData,
    MapMarker,
    MetricCardData,
    MetricItem,
    PhotoGalleryData,
    PhotoItem,
    DataTableData,
)


def build_chart_component(
    title: str,
    labels: List[str],
    data: List[float],
    chart_type: str = "bar",
    dataset_label: str = "Count",
    colors: Optional[List[str]] = None,
) -> A2UIComponent:
    """Builds an interactive chart component."""
    default_colors = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
        "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16"
    ]
    bg_colors = colors or default_colors[:len(labels)]
    
    return A2UIComponent(
        type="chart",
        title=title,
        data=ChartData(
            chart_type=chart_type,  # type: ignore
            title=title,
            labels=labels,
            datasets=[
                ChartDataset(
                    label=dataset_label,
                    data=data,
                    background_color=bg_colors if chart_type in ("pie", "doughnut") else bg_colors[0],
                )
            ],
        ),
    )


def build_map_component(
    title: str,
    markers: List[Dict[str, Any]],
    center_lat: float = 40.7128,
    center_lng: float = -74.0060,
    zoom: int = 12,
) -> A2UIComponent:
    """Builds an interactive map component."""
    map_markers = [
        MapMarker(
            title=m.get("title", "Location"),
            lat=float(m["lat"]),
            lng=float(m["lng"]),
            description=m.get("description"),
            category=m.get("category"),
        )
        for m in markers
        if "lat" in m and "lng" in m
    ]
    
    return A2UIComponent(
        type="map",
        title=title,
        data=MapData(
            title=title,
            center_lat=center_lat,
            center_lng=center_lng,
            zoom=zoom,
            markers=map_markers,
        ),
    )


def build_metric_card_component(
    title: str,
    metrics: List[Dict[str, Any]],
) -> A2UIComponent:
    """Builds a key metrics/stat cards component."""
    metric_items = [
        MetricItem(
            label=m["label"],
            value=m["value"],
            delta=m.get("delta"),
            status=m.get("status", "neutral"),
        )
        for m in metrics
    ]
    return A2UIComponent(
        type="metric_card",
        title=title,
        data=MetricCardData(title=title, metrics=metric_items),
    )


def build_photo_gallery_component(
    title: str,
    photos: List[Dict[str, Any]],
) -> A2UIComponent:
    """Builds an interactive photo/media gallery component."""
    items = [
        PhotoItem(
            title=p.get("title", "Historical Item"),
            image_url=p.get("image_url", ""),
            thumbnail_url=p.get("thumbnail_url"),
            link=p.get("link"),
            caption=p.get("caption"),
            date=p.get("date"),
        )
        for p in photos
    ]
    return A2UIComponent(
        type="photo_gallery",
        title=title,
        data=PhotoGalleryData(title=title, items=items),
    )


def build_table_component(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
) -> A2UIComponent:
    """Builds a sortable data table component."""
    return A2UIComponent(
        type="data_table",
        title=title,
        data=DataTableData(
            title=title,
            columns=columns,
            rows=rows,
        ),
    )


def extract_a2ui_from_text_response(text: str, command_name: str = "ask") -> Optional[A2UIPayload]:
    """
    Intelligently extracts A2UI visual components from unstructured agent text
    when direct tool components were not explicitly structured.
    """
    components: List[A2UIComponent] = []

    # 1. NYPL Photo Links Extractor
    # Looks for markdown links with digitalcollections.nypl.org
    nypl_links = re.findall(r'\[([^\]]+)\]\((http[s]?://digitalcollections\.nypl\.org/items/([a-zA-Z0-9\-]+))\)', text)
    if nypl_links:
        photos = []
        for label, url, item_id in nypl_links[:6]:
            # Generate NYPL image thumbnail URL format
            thumb_url = f"https://images.nypl.org/index.php?id={item_id}&t=w"
            photos.append({
                "title": label.strip(),
                "link": url,
                "image_url": thumb_url,
                "thumbnail_url": thumb_url,
                "caption": f"NYPL Digital Collections Item: {item_id}",
            })
        if photos:
            components.append(build_photo_gallery_component(
                title="Historical Digital Collection Items",
                photos=photos,
            ))

    # 2. 311 Noise / Open Data Category & Stats Extractor
    if "311" in text or "complaint" in text.lower() or "violation" in text.lower():
        # Look for bullet points with complaint categories
        lines = text.split("\n")
        categories: Dict[str, int] = {}
        for line in lines:
            line_str = line.strip()
            if line_str.startswith(("-", "*", "•")):
                # Check for categories like Manufacturing, Street/Sidewalk, Residential, Commercial
                match = re.search(r'[\*\*_]*([A-Za-z0-9\s/&]+)[\*\*_]*\s*:\s*(.+)', line_str.lstrip("-*• "))
                if match:
                    cat = match.group(1).strip()
                    if len(cat) < 35 and not cat.lower().startswith("location"):
                        categories[cat] = categories.get(cat, 0) + 1
        
        if len(categories) >= 2:
            labels = list(categories.keys())[:8]
            data = [float(categories[k]) for k in labels]
            components.append(build_chart_component(
                title="Reported Incident Distribution",
                labels=labels,
                data=data,
                chart_type="doughnut",
                dataset_label="Reports",
            ))

    if not components:
        return None

    return A2UIPayload(components=components)
