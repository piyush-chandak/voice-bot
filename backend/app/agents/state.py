import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    messages: Annotated[List[Dict[str, str]], operator.add]
    session_id: str
    user_id: int
    user_role: str
    latitude: Optional[float]
    longitude: Optional[float]
    location_verified: bool
    nearby_assets: List[Dict[str, Any]]
    selected_asset_id: Optional[int]
    active_ticket_id: Optional[int]
    active_asset_id: Optional[int]
    issue_description: Optional[str]
    ticket_summary: Optional[Dict[str, str]]
    ticket_id: Optional[int]
    next_node: str
    tickets: Optional[List[Dict[str, Any]]]
    intent: Optional[str]
    data: Optional[Dict[str, Any]]
    pending_confirmation: Optional[Dict[str, Any]]
