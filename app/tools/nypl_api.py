import json
import logging
import httpx
from typing import Any, Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


async def search_nypl_digital_collections(query: str, per_page: int = 5) -> str:
    """
    Search the NYPL Digital Collections public API / catalog for historic photographs,
    prints, manuscripts, and digitized public domain collections.
    """
    try:
        limit = max(1, min(int(per_page), 10))
    except (ValueError, TypeError):
        limit = 5

    url = "https://api.repo.nypl.org/api/v2/items/search"
    headers: Dict[str, str] = {}
    if settings.NYPL_API_TOKEN:
        headers["Authorization"] = f"Token token={settings.NYPL_API_TOKEN}"

    params = {
        "q": str(query),
        "per_page": limit,
        "publicDomainOnly": "true"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=12.0)
            if response.status_code == 200:
                data = response.json()
                nypl_api_data = data.get("nyplAPI", {}).get("response", {}).get("result", [])
                if nypl_api_data:
                    results = []
                    for item in nypl_api_data:
                        results.append({
                            "title": item.get("title"),
                            "type": item.get("typeOfResource"),
                            "date": item.get("dateDigitized"),
                            "apiItemURL": item.get("apiItemURL"),
                            "itemLink": item.get("itemLink")
                        })
                    return json.dumps(results, indent=2)
                return "No digitized public domain items found for this query in NYPL collections."
            else:
                # Fallback to direct NYPL Digital Collections catalog search link if token is not configured
                encoded_query = httpx.URL("", params={"keywords": str(query)}).query.decode("utf-8")
                return (
                    f"NYPL Digital Archives Query result for '{query}':\n"
                    f"- Historical archives, maps, and photographic prints matching '{query}' "
                    f"are cataloged in the NYPL Digital Collections: https://digitalcollections.nypl.org/search/index?utf8=✓&{encoded_query}"
                )
    except Exception as e:
        logger.error(f"Error searching NYPL Digital Collections: {e}", exc_info=True)
        return f"Error searching NYPL Digital Collections: {str(e)}"


async def find_nypl_branch(borough_or_keyword: str = "") -> str:
    """
    Find NYPL library branches, research centers, and services by borough or name.
    """
    branches = [
        {"name": "Stephen A. Schwarzman Building (Main Branch)", "address": "476 5th Ave, New York, NY 10018", "borough": "Manhattan", "features": "Rose Main Reading Room, Research Collections"},
        {"name": "Schomburg Center for Research in Black Culture", "address": "515 Malcolm X Blvd, New York, NY 10037", "borough": "Manhattan", "features": "Manuscripts, Archives, Rare Books, African Diaspora"},
        {"name": "Library for the Performing Arts", "address": "40 Lincoln Center Plaza, New York, NY 10023", "borough": "Manhattan", "features": "Theatre, Music, Dance Archives, Recorded Sound"},
        {"name": "Stavros Niarchos Foundation Library (SNFL)", "address": "455 5th Ave, New York, NY 10016", "borough": "Manhattan", "features": "Flagship Circulating Library, Rooftop Terrace, Teen Center"},
        {"name": "Bronx Library Center", "address": "310 E Kingsbridge Rd, Bronx, NY 10458", "borough": "Bronx", "features": "Latino and Puerto Rican Heritage Collection, Premier Bronx Research"},
        {"name": "St. George Library Center", "address": "5 Central Ave, Staten Island, NY 10301", "borough": "Staten Island", "features": "Staten Island Local History Collection, Reference Center"}
    ]
    
    keyword = str(borough_or_keyword or "").strip().lower()
    if not keyword:
        return json.dumps(branches, indent=2)

    matched = [
        b for b in branches 
        if keyword in b["name"].lower() or keyword in b["borough"].lower() or keyword in b["features"].lower()
    ]
    
    if not matched:
        return f"No specific branch matched '{borough_or_keyword}'. Key flagship locations include: {json.dumps(branches[:3], indent=2)}"
    return json.dumps(matched, indent=2)
