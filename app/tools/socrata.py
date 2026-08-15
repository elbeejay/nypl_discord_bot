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
    clean_boro = str(boroname).strip().upper()
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
