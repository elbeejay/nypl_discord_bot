import json
import logging
import httpx
from typing import Any, Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Common NYC Open Data SODA Resource Endpoints
DATASETS = {
    "311_service_requests": "erm2-nwe9",
    "restaurant_inspections": "43nn-pn8j",
    "tree_census_2015": "5rq2-4hqu",
    "nypd_complaints": "5uac-w243",
    "subway_stations": "kk4q-3rt2",
}


async def query_socrata_dataset(
    dataset_id: str,
    where: Optional[str] = None,
    select: Optional[str] = None,
    order: Optional[str] = None,
    group: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Executes a SoQL query against NYC Open Data (SODA API).
    """
    endpoint = f"https://data.cityofnewyork.us/resource/{dataset_id}.json"
    headers: Dict[str, str] = {}
    if settings.NYC_SOCRATA_APP_TOKEN:
        headers["X-App-Token"] = settings.NYC_SOCRATA_APP_TOKEN

    try:
        parsed_limit = max(1, min(int(limit), 25))
    except (ValueError, TypeError):
        parsed_limit = 5

    params: Dict[str, Any] = {"$limit": parsed_limit}
    if where:
        params["$where"] = where
    if select:
        params["$select"] = select
    if order:
        params["$order"] = order
    if group:
        params["$group"] = group

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, params=params, headers=headers, timeout=12.0)
            if response.status_code != 200:
                logger.warning(f"SODA query failed ({response.status_code}): {response.text}")
                return [{"error": f"API error {response.status_code}: {response.text}"}]
            return response.json()
    except Exception as e:
        logger.error(f"Error querying Socrata dataset {dataset_id}: {e}", exc_info=True)
        return [{"error": f"Network or request error: {str(e)}"}]


async def query_nyc_311(query_filter: str, limit: int = 5) -> str:
    """
    Query NYC 311 service requests.
    Example filter: "complaint_type = 'Noise' AND borough = 'BROOKLYN'" or "incident_zip = '11201'"
    Note: Borough names in 311 are uppercase: 'MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND'.
    """
    data = await query_socrata_dataset(
        dataset_id=DATASETS["311_service_requests"],
        where=query_filter,
        select="unique_key,created_date,complaint_type,descriptor,borough,incident_zip,incident_address,status,resolution_description",
        order="created_date DESC",
        limit=limit,
    )
    if not data:
        return "No 311 service records found matching the criteria."
    return json.dumps(data, indent=2)


async def query_restaurant_inspections(dba_name: str, limit: int = 5) -> str:
    """
    Query NYC DOHMH restaurant health inspection grades and violations by restaurant name (DBA).
    Example dba_name: "KATZ'S DELICATESSEN" or "SHAKE SHACK"
    """
    escaped_dba = str(dba_name).upper().replace("'", "''")
    where_clause = f"upper(dba) like '%{escaped_dba}%'"
    data = await query_socrata_dataset(
        dataset_id=DATASETS["restaurant_inspections"],
        where=where_clause,
        select="dba,boro,building,street,zipcode,cuisine_description,inspection_date,action,violation_code,violation_description,critical_flag,score,grade",
        order="inspection_date DESC",
        limit=limit,
    )
    if not data:
        return f"No health inspection records found for restaurant '{dba_name}'."
    return json.dumps(data, indent=2)


async def query_tree_census(boroname: str, spc_common: Optional[str] = None, limit: int = 5) -> str:
    """
    Query NYC Street Tree Census data.
    Example: boroname="Queens", spc_common="honeylocust"
    """
    clean_boro = str(boroname).strip().upper().replace("'", "''")
    where = f"upper(boroname) = '{clean_boro}'"
    if spc_common:
        escaped_species = str(spc_common).strip().upper().replace("'", "''")
        where += f" AND upper(spc_common) like '%{escaped_species}%'"
    
    data = await query_socrata_dataset(
        dataset_id=DATASETS["tree_census_2015"],
        where=where,
        select="tree_id,tree_dbh,status,health,spc_common,spc_latin,address,boroname,zipcode",
        limit=limit,
    )
    if not data:
        return f"No tree census records found for borough '{boroname}'."
    return json.dumps(data, indent=2)


async def search_nyc_datasets(keyword: str, limit: int = 5) -> str:
    """
    Search the NYC Open Data catalog (Discovery API) for datasets matching a keyword or topic.
    Returns a list of datasets with their 4x4 resource IDs (e.g., 'erm2-nwe9', 'n6c5-95xh'),
    descriptions, and available column field names for querying.
    Use this tool to find dataset IDs when the user asks about civic topics outside 311, trees, or restaurant inspections.
    """
    url = "https://api.us.socrata.com/api/catalog/v1"
    try:
        parsed_limit = max(1, min(int(limit), 10))
    except (ValueError, TypeError):
        parsed_limit = 5

    params: Dict[str, Any] = {
        "domains": "data.cityofnewyork.us",
        "q": keyword,
        "limit": parsed_limit,
    }
    headers: Dict[str, str] = {}
    if settings.NYC_SOCRATA_APP_TOKEN:
        headers["X-App-Token"] = settings.NYC_SOCRATA_APP_TOKEN

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=12.0)
            if response.status_code != 200:
                logger.warning(f"Socrata catalog search failed ({response.status_code}): {response.text}")
                return json.dumps([{"error": f"Catalog API error {response.status_code}: {response.text}"}])
            data = response.json()

            results = []
            for item in data.get("results", []):
                resource = item.get("resource", {})
                fields = resource.get("columns_field_name") or [
                    col.get("name") for col in resource.get("columns", []) if isinstance(col, dict)
                ]
                results.append({
                    "dataset_name": resource.get("name"),
                    "four_by_four_id": resource.get("id"),
                    "description": resource.get("description", "")[:300] if resource.get("description") else "",
                    "columns": fields[:15] if fields else [],
                })
            if not results:
                return f"No NYC Open Data catalog entries found for '{keyword}'."
            return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error searching NYC datasets for '{keyword}': {e}", exc_info=True)
        return json.dumps([{"error": f"Network or catalog search error: {str(e)}"}])


async def query_dynamic_dataset(
    four_by_four_id: str,
    query_filter: Optional[str] = None,
    select: Optional[str] = None,
    order: Optional[str] = None,
    limit: int = 5,
    soql_where: Optional[str] = None,
) -> str:
    """
    Query any NYC Open Data dataset dynamically using its 4x4 ID (e.g. 'n6c5-95xh', '4y8i-pbvd')
    and optional SoQL filters ($where, $select, $order).
    """
    effective_where = query_filter or soql_where
    data = await query_socrata_dataset(
        dataset_id=four_by_four_id,
        where=effective_where,
        select=select,
        order=order,
        limit=limit,
    )
    if not data:
        return f"No records found in dataset '{four_by_four_id}' matching the criteria."
    return json.dumps(data, indent=2)

