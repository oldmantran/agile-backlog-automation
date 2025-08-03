"""
API endpoints for domain management functionality.
Add these endpoints to your main FastAPI server.
"""

from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from db import (
    get_all_domains, 
    save_project_domains, 
    get_project_domains,
    submit_domain_request,
    get_domain_requests
)
import logging

logger = logging.getLogger(__name__)

# =====================================================
# PYDANTIC MODELS
# =====================================================

class DomainSelection(BaseModel):
    domain_id: int
    domain_key: str
    subdomain_id: Optional[int] = None
    subdomain_key: Optional[str] = None
    is_primary: bool = False
    weight: float = 1.0

class ProjectDomainRequest(BaseModel):
    project_id: str
    selected_domains: List[DomainSelection]
    selected_by: str

class DomainRequestSubmission(BaseModel):
    requested_by: str
    request_type: str  # 'new_domain', 'new_subdomain', 'enhancement', 'pattern_addition'
    parent_domain_id: Optional[int] = None
    requested_domain_key: Optional[str] = None
    requested_display_name: Optional[str] = None
    justification: str
    proposed_patterns: Optional[List[str]] = []
    proposed_user_types: Optional[List[Dict[str, Any]]] = []
    proposed_vocabulary: Optional[List[str]] = []
    priority: str = "medium"

# =====================================================
# API ENDPOINTS (Add to your FastAPI app)
# =====================================================

def add_domain_endpoints(app):
    """Add domain management endpoints to FastAPI app."""
    
    @app.get("/api/domains")
    async def get_domains(include_inactive: bool = False) -> Dict[str, Any]:
        """Get all available domains with their subdomains."""
        try:
            domains = get_all_domains(include_inactive=include_inactive)
            return {
                "success": True,
                "domains": domains,
                "count": len(domains)
            }
        except Exception as e:
            logger.error(f"Failed to get domains: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve domains: {str(e)}")

    @app.post("/api/projects/{project_id}/domains")
    async def save_project_domain_selections(project_id: str, request: ProjectDomainRequest) -> Dict[str, Any]:
        """Save domain selections for a project."""
        try:
            # Convert Pydantic models to dictionaries
            domain_selections = []
            for selection in request.selected_domains:
                domain_selections.append({
                    'domain_id': selection.domain_id,
                    'subdomain_id': selection.subdomain_id,
                    'is_primary': selection.is_primary,
                    'weight': selection.weight
                })
            
            save_project_domains(
                project_id=project_id,
                domain_selections=domain_selections,
                selected_by=request.selected_by
            )
            
            return {
                "success": True,
                "message": f"Saved {len(domain_selections)} domain selections for project {project_id}"
            }
        except Exception as e:
            logger.error(f"Failed to save project domains: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save domain selections: {str(e)}")

    @app.get("/api/projects/{project_id}/domains")
    async def get_project_domain_selections(project_id: str) -> Dict[str, Any]:
        """Get domain selections for a project."""
        try:
            selections = get_project_domains(project_id)
            return {
                "success": True,
                "project_id": project_id,
                "domain_selections": selections,
                "count": len(selections)
            }
        except Exception as e:
            logger.error(f"Failed to get project domains: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve project domains: {str(e)}")

    @app.post("/api/domain-requests")
    async def submit_new_domain_request(request: DomainRequestSubmission) -> Dict[str, Any]:
        """Submit a request for a new domain or domain enhancement."""
        try:
            request_data = {
                'requested_by': request.requested_by,
                'request_type': request.request_type,
                'parent_domain_id': request.parent_domain_id,
                'requested_domain_key': request.requested_domain_key,
                'requested_display_name': request.requested_display_name,
                'justification': request.justification,
                'proposed_patterns': request.proposed_patterns,
                'proposed_user_types': request.proposed_user_types,
                'proposed_vocabulary': request.proposed_vocabulary,
                'priority': request.priority
            }
            
            request_id = submit_domain_request(request_data)
            
            return {
                "success": True,
                "request_id": request_id,
                "message": "Domain request submitted successfully"
            }
        except Exception as e:
            logger.error(f"Failed to submit domain request: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to submit domain request: {str(e)}")

    @app.get("/api/domain-requests")
    async def get_domain_request_list(status: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get domain requests with optional filtering."""
        try:
            requests = get_domain_requests(status=status, user_id=user_id)
            return {
                "success": True,
                "requests": requests,
                "count": len(requests)
            }
        except Exception as e:
            logger.error(f"Failed to get domain requests: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve domain requests: {str(e)}")

    @app.get("/api/domains/search")
    async def search_domains(query: str) -> Dict[str, Any]:
        """Search domains by name or keywords."""
        try:
            all_domains = get_all_domains()
            query_lower = query.lower()
            
            matching_domains = []
            for domain in all_domains:
                # Search in domain name and description
                if (query_lower in domain['display_name'].lower() or 
                    query_lower in domain.get('description', '').lower() or
                    query_lower in domain['domain_key'].lower()):
                    matching_domains.append(domain)
                
                # Search in subdomains
                for subdomain in domain.get('subdomains', []):
                    if (query_lower in subdomain['display_name'].lower() or
                        query_lower in subdomain.get('description', '').lower()):
                        if domain not in matching_domains:
                            matching_domains.append(domain)
            
            return {
                "success": True,
                "query": query,
                "domains": matching_domains,
                "count": len(matching_domains)
            }
        except Exception as e:
            logger.error(f"Failed to search domains: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to search domains: {str(e)}")

# =====================================================
# EXAMPLE USAGE IN MAIN FastAPI APP
# =====================================================

"""
To use these endpoints in your main FastAPI application:

from fastapi import FastAPI
from domain_api_endpoints import add_domain_endpoints

app = FastAPI()

# Add domain management endpoints
add_domain_endpoints(app)

# Your existing endpoints...
"""