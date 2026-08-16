import httpx
import logging

logger = logging.getLogger(__name__)


async def search_nyc_datasets(keyword: str) -> list[dict]:
    """
    Search the NYC Open Data catalog for datasets matching a keyword.
    Returns a list of datasets with their resource IDs (4x4 identifiers) and descriptions.
    """
    url = f"https://socrata.com{keyword}&domains=data.cityofnewyork.us&limit=3"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                resource = item.get("resource", {})
                results.append({
                    "dataset_name": resource.get("name"),
                    "four_by_four_id": resource.get("id"),  # e.g., 'erm2-nwe9'
                    "description": resource.get("description"),
                    "columns": [col.get("name") for col in resource.get("columns", [])[:10]]  # First 10 columns
                })
            return results
    except Exception as e:
        logger.error(f"Error searching NYC datasets: {e}")
        return []


async def query_dynamic_dataset(four_by_four_id: str, soql_where: str) -> list[dict]:
    """
    Queries any NYC Open Data dataset dynamically using its 4x4 ID and a SoQL WHERE clause.
    """
    url = f"https://cityofnewyork.us{four_by_four_id}.json"
    params = {"$where": soql_where, "$limit": 5}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error querying dynamic dataset {four_by_four_id}: {e}")
        return []
