"""
Curriculum routes for Flask API.

Provides endpoints for Curriculum domain:
- POST /api/curriculum - Create a new curriculum document
- GET /api/curriculum - Get all curriculum documents (with optional ?name= query parameter)
- GET /api/curriculum/<id> - Get a specific curriculum document by ID
- PATCH /api/curriculum/<id> - Update a curriculum document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.curriculum_service import CurriculumService

import logging
logger = logging.getLogger(__name__)


def create_curriculum_routes():
    """
    Create a Flask Blueprint exposing curriculum endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with curriculum routes
    """
    curriculum_routes = Blueprint('curriculum_routes', __name__)
    
    @curriculum_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_curriculum():
        """
        POST /api/curriculum - Create a new curriculum document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created curriculum document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        curriculum_id = CurriculumService.create_curriculum(data, token, breadcrumb)
        curriculum = CurriculumService.get_curriculum(curriculum_id, token, breadcrumb)
        
        logger.info(f"create_curriculum Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(curriculum), 201
    
    @curriculum_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_curriculums():
        """
        GET /api/curriculum - Retrieve infinite scroll batch of sorted, filtered curriculum documents.
        
        Query Parameters:
            name: Optional name filter
            after_id: Cursor for infinite scroll (ID of last item from previous batch, omit for first request)
            limit: Items per batch (default: 10, max: 100)
            sort_by: Field to sort by (default: 'name')
            order: Sort order 'asc' or 'desc' (default: 'asc')
        
        Returns:
            JSON response with infinite scroll results: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None
            }
        
        Raises:
            400 Bad Request: If invalid parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Get query parameters
        name = request.args.get('name')
        after_id = request.args.get('after_id')
        limit = request.args.get('limit', 10, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        
        # Service layer validates parameters and raises HTTPBadRequest if invalid
        # @handle_route_exceptions decorator will catch and format the exception
        result = CurriculumService.get_curriculums(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_curriculums Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @curriculum_routes.route('/<curriculum_id>', methods=['GET'])
    @handle_route_exceptions
    def get_curriculum(curriculum_id):
        """
        GET /api/curriculum/<id> - Retrieve a specific curriculum document by ID.
        
        Args:
            curriculum_id: The curriculum ID to retrieve
            
        Returns:
            JSON response with the curriculum document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        curriculum = CurriculumService.get_curriculum(curriculum_id, token, breadcrumb)
        logger.info(f"get_curriculum Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(curriculum), 200
    
    @curriculum_routes.route('/<curriculum_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_curriculum(curriculum_id):
        """
        PATCH /api/curriculum/<id> - Update a curriculum document.
        
        Args:
            curriculum_id: The curriculum ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated curriculum document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        curriculum = CurriculumService.update_curriculum(curriculum_id, data, token, breadcrumb)
        
        logger.info(f"update_curriculum Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(curriculum), 200
    
    logger.info("Curriculum Flask Routes Registered")
    return curriculum_routes