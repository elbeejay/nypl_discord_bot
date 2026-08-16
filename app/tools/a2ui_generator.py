"""
A2UI Component Builders & Utilities.
Transforms raw query responses from NYC Open Data and NYPL archives into interactive A2UI payloads.
"""

from typing import List, Dict, Any, Optional
import re
from app.schemas.a2ui import (
    A2UIAction,
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
    actions: Optional[List[A2UIAction]] = None,
) -> A2UIComponent:
    """Builds an interactive chart component."""
    default_colors = [
        "#D41B2C", "#2563EB", "#B8860B", "#10B981", "#8B5CF6",
        "#F59E0B", "#06B6D4", "#EC4899", "#6366F1", "#84CC16"
    ]
    bg_colors = colors or default_colors[:len(labels)]
    
    return A2UIComponent(
        type="chart",
        title=title,
        actions=actions,
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
    actions: Optional[List[A2UIAction]] = None,
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
        actions=actions,
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
    actions: Optional[List[A2UIAction]] = None,
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
        actions=actions,
        data=MetricCardData(title=title, metrics=metric_items),
    )


def build_photo_gallery_component(
    title: str,
    photos: List[Dict[str, Any]],
    actions: Optional[List[A2UIAction]] = None,
) -> A2UIComponent:
    """Builds an interactive photo/media gallery component."""
    items = [
        PhotoItem(
            title=p.get("title", "Historical Item"),
            image_url=p.get("image_url", ""),
            thumbnail_url=p.get("thumbnail_url") or p.get("image_url"),
            link=p.get("link"),
            caption=p.get("caption"),
            date=p.get("date"),
        )
        for p in photos
    ]
    return A2UIComponent(
        type="photo_gallery",
        title=title,
        actions=actions,
        data=PhotoGalleryData(title=title, items=items),
    )


def build_table_component(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    actions: Optional[List[A2UIAction]] = None,
) -> A2UIComponent:
    """Builds a sortable data table component."""
    return A2UIComponent(
        type="data_table",
        title=title,
        actions=actions,
        data=DataTableData(
            title=title,
            columns=columns,
            rows=rows,
        ),
    )


KNOWN_NYPL_LOCATIONS = {
    "schwarzman": {"title": "Stephen A. Schwarzman Building", "lat": 40.7532, "lng": -73.9822, "category": "nypl_branch", "description": "476 5th Ave (Main Library & Rose Main Reading Room)"},
    "schomburg": {"title": "Schomburg Center for Research in Black Culture", "lat": 40.8144, "lng": -73.9419, "category": "nypl_branch", "description": "515 Malcolm X Blvd, Harlem"},
    "performing arts": {"title": "Library for the Performing Arts (LPA)", "lat": 40.7725, "lng": -73.9837, "category": "nypl_branch", "description": "Lincoln Center Plaza"},
    "snfl": {"title": "Stavros Niarchos Foundation Library (SNFL)", "lat": 40.7518, "lng": -73.9818, "category": "nypl_branch", "description": "455 5th Ave (Circulating Flagship)"},
    "mid-manhattan": {"title": "Stavros Niarchos Foundation Library (SNFL)", "lat": 40.7518, "lng": -73.9818, "category": "nypl_branch", "description": "455 5th Ave"},
}

KNOWN_NYPL_IMAGES = {
    "510d47e1-e341-a3d9-e040-e00a18064a99": "https://images.nypl.org/index.php?id=724982b&t=w",
    "510d47e1-e342-a3d9-e040-e00a18064a99": "https://images.nypl.org/index.php?id=724985b&t=w",
    "510d47e1-e343-a3d9-e040-e00a18064a99": "https://images.nypl.org/index.php?id=1255554&t=w",
    "510d47e1-e344-a3d9-e040-e00a18064a99": "https://images.nypl.org/index.php?id=724989b&t=w",
    "510d47e1-e345-a3d9-e040-e00a18064a99": "https://images.nypl.org/index.php?id=724991b&t=w",
}


def extract_a2ui_from_text_response(text: str, command_name: str = "ask") -> Optional[A2UIPayload]:
    """
    Intelligently extracts A2UI visual components from unstructured agent text
    when direct tool components were not explicitly structured.
    """
    components: List[A2UIComponent] = []

    # 1. NYPL Photo Links Extractor
    nypl_links = re.findall(r'\[([^\]]+)\]\((http[s]?://digitalcollections\.nypl\.org/items/([a-zA-Z0-9\-]+))\)', text)
    if nypl_links:
        photos = []
        for label, url, item_id in nypl_links[:8]:
            thumb_url = KNOWN_NYPL_IMAGES.get(item_id, f"https://images.nypl.org/index.php?id={item_id}&t=w")
            photos.append({
                "title": label.strip(),
                "link": url,
                "image_url": thumb_url,
                "thumbnail_url": thumb_url,
                "caption": f"NYPL Digital Collection Item",
            })
        if photos:
            components.append(build_photo_gallery_component(
                title="Historical Digital Collection Archives",
                photos=photos,
                actions=[
                    A2UIAction(label="Explore More NYPL Archives", action_type="prompt", payload="Show me more historic photographs from this same era in NYPL collections")
                ]
            ))

    # 2. Known Library Branches / Locations Extractor for Map
    matched_markers = []
    text_lower = text.lower()
    for key, loc in KNOWN_NYPL_LOCATIONS.items():
        if key in text_lower:
            matched_markers.append(loc)
    
    if matched_markers:
        components.append(build_map_component(
            title="NYPL Library Locations & Research Centers",
            markers=matched_markers,
            center_lat=matched_markers[0]["lat"],
            center_lng=matched_markers[0]["lng"],
            zoom=13,
            actions=[
                A2UIAction(label="Find Nearest NYPL Branch", action_type="prompt", payload="What are the operating hours and services at these NYPL locations?")
            ]
        ))

    # 3. Markdown Tables Extractor
    table_pattern = re.compile(r'(\|.+?\|\n\|[-:\s|]+?\|\n(?:\|.+?\|\n?)+)', re.MULTILINE)
    table_match = table_pattern.search(text)
    if table_match:
        table_raw = table_match.group(1).strip().split('\n')
        if len(table_raw) >= 3:
            headers = [h.strip() for h in table_raw[0].split('|')[1:-1]]
            rows = []
            for row_line in table_raw[2:]:
                if not row_line.strip() or not row_line.startswith('|'):
                    continue
                cells = [c.strip() for c in row_line.split('|')[1:-1]]
                if len(cells) == len(headers):
                    rows.append(cells)
            
            if headers and rows:
                components.append(build_table_component(
                    title="Dataset Records",
                    columns=headers,
                    rows=rows,
                ))

    # 4. 311 Noise / Open Data Category & Stats Extractor (Doughnut Chart)
    if "311" in text or "complaint" in text.lower() or "violation" in text.lower():
        lines = text.split("\n")
        categories: Dict[str, int] = {}
        for line in lines:
            line_str = line.strip()
            if line_str.startswith(("-", "*", "•")):
                match = re.search(r'[\*\*_]*([A-Za-z0-9\s/&]+)[\*\*_]*\s*:\s*(.+)', line_str.lstrip("-*• "))
                if match:
                    cat = match.group(1).strip()
                    if len(cat) < 35 and not cat.lower().startswith("location"):
                        categories[cat] = categories.get(cat, 0) + 1
        
        if len(categories) >= 2:
            labels = list(categories.keys())[:8]
            data = [float(categories[k]) for k in labels]
            components.append(build_chart_component(
                title="Reported Incident Breakdown",
                labels=labels,
                data=data,
                chart_type="doughnut",
                dataset_label="Reports",
                actions=[
                    A2UIAction(label="Filter by Borough", action_type="prompt", payload="Break down these 311 issues by borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island)")
                ]
            ))

    if not components:
        return None

    return A2UIPayload(components=components)
