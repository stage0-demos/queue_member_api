"""
Review routes for Flask API.

Provides endpoints for Review domain:
- POST /api/review - Create a new review document
- GET /api/review - Get all review documents (with optional ?name= query parameter)
- GET /api/review/<id> - Get a specific review document by ID
- PATCH /api/review/<id> - Update a review document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.review_service import ReviewService

import logging
logger = logging.getLogger(__name__)


def create_review_routes():
    """
    Create a Flask Blueprint exposing review endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with review routes
    """
    review_routes = Blueprint('review_routes', __name__)
    
    @review_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_review():
        """
        POST /api/review - Create a new review document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created review document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        review_id = ReviewService.create_review(data, token, breadcrumb)
        review = ReviewService.get_review(review_id, token, breadcrumb)
        
        logger.info(f"create_review Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(review), 201
    
    @review_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_reviews():
        """
        GET /api/review - Retrieve infinite scroll batch of sorted, filtered review documents.
        
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
        result = ReviewService.get_reviews(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_reviews Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @review_routes.route('/<review_id>', methods=['GET'])
    @handle_route_exceptions
    def get_review(review_id):
        """
        GET /api/review/<id> - Retrieve a specific review document by ID.
        
        Args:
            review_id: The review ID to retrieve
            
        Returns:
            JSON response with the review document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        review = ReviewService.get_review(review_id, token, breadcrumb)
        logger.info(f"get_review Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(review), 200
    
    @review_routes.route('/<review_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_review(review_id):
        """
        PATCH /api/review/<id> - Update a review document.
        
        Args:
            review_id: The review ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated review document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        review = ReviewService.update_review(review_id, data, token, breadcrumb)
        
        logger.info(f"update_review Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(review), 200
    
    logger.info("Review Flask Routes Registered")
    return review_routes