"""
A2UI (Agent-to-User Interface) Declarative UI Specification & Schemas.

Allows AI agents to emit rich, interactive data visualization and media components
on the fly alongside natural language responses. Frontend frameworks (React, Vue,
Svelte, Vanilla Web Components) can dynamically render these components.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
import uuid
import time


# ==========================================
# Component Data Payloads
# ==========================================

class ChartDataset(BaseModel):
    label: str
    data: List[Union[int, float]]
    background_color: Optional[Union[str, List[str]]] = None
    border_color: Optional[str] = None


class ChartData(BaseModel):
    chart_type: Literal["bar", "line", "pie", "doughnut", "radar"] = "bar"
    title: str
    subtitle: Optional[str] = None
    labels: List[str]
    datasets: List[ChartDataset]


class MapMarker(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    lat: float
    lng: float
    description: Optional[str] = None
    category: Optional[str] = None  # e.g., "311_complaint", "library_branch", "restaurant"
    icon: Optional[str] = None


class MapData(BaseModel):
    title: str
    center_lat: float = 40.7128
    center_lng: float = -74.0060
    zoom: int = 12
    markers: List[MapMarker] = Field(default_factory=list)


class MetricItem(BaseModel):
    label: str
    value: Union[str, int, float]
    delta: Optional[str] = None
    status: Optional[Literal["neutral", "positive", "negative", "warning", "info", "critical", "error"]] = "neutral"
    icon: Optional[str] = None


class MetricCardData(BaseModel):
    title: str
    metrics: List[MetricItem] = Field(default_factory=list)


class PhotoItem(BaseModel):
    id: Optional[str] = None
    title: str
    image_url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    link: Optional[str] = None
    date: Optional[str] = None


class PhotoGalleryData(BaseModel):
    title: str
    items: List[PhotoItem] = Field(default_factory=list)


class DataTableData(BaseModel):
    title: str
    columns: List[str]
    rows: List[List[Any]]
    searchable: bool = True
    sortable: bool = True


# ==========================================
# Generic A2UI Component & Container
# ==========================================

class A2UIAction(BaseModel):
    label: str
    action_type: Literal["prompt", "link", "filter"] = "prompt"
    payload: str  # Prompt text or URL target


class A2UIComponent(BaseModel):
    id: str = Field(default_factory=lambda: f"a2ui-{uuid.uuid4().hex[:8]}")
    type: Literal["chart", "map", "metric_card", "photo_gallery", "data_table"]
    title: Optional[str] = None
    data: Union[ChartData, MapData, MetricCardData, PhotoGalleryData, DataTableData, Dict[str, Any]]
    actions: Optional[List[A2UIAction]] = None


class A2UIPayload(BaseModel):
    version: str = "1.0"
    layout: Literal["vertical", "grid", "carousel", "tabs"] = "vertical"
    components: List[A2UIComponent] = Field(default_factory=list)


# ==========================================
# Frontend API Request / Response Models
# ==========================================

class FrontendChatRequest(BaseModel):
    query: str = Field(..., description="User question or prompt")
    command: Optional[str] = Field("ask", description="Direct agent routing: 'ask', 'nypl', 'nycdata'")
    session_id: Optional[str] = Field(None, description="Multi-turn conversation session ID")
    enable_a2ui: bool = Field(True, description="Whether agent should generate A2UI visualizations")


class FrontendChatResponse(BaseModel):
    query: str
    command: str
    session_id: str
    response: str
    a2ui: Optional[A2UIPayload] = None
    created_at: float = Field(default_factory=time.time)
