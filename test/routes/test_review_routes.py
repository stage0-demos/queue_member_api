"""
Unit tests for Review routes.

These tests validate the Flask route layer for the Review domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.review_routes import create_review_routes


class TestReviewRoutes(unittest.TestCase):
    """Test cases for Review routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_review_routes(),
            url_prefix="/api/review",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.review_routes.create_flask_token")
    @patch("src.routes.review_routes.create_flask_breadcrumb")
    @patch("src.routes.review_routes.ReviewService.create_review")
    @patch("src.routes.review_routes.ReviewService.get_review")
    def test_create_review_success(
        self,
        mock_get_review,
        mock_create_review,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/review for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_review.return_value = "123"
        mock_get_review.return_value = {
            "_id": "123",
            "name": "test-review",
            "status": "active",
        }

        response = self.client.post(
            "/api/review",
            json={"name": "test-review", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_review.assert_called_once()
        mock_get_review.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.review_routes.create_flask_token")
    @patch("src.routes.review_routes.create_flask_breadcrumb")
    @patch("src.routes.review_routes.ReviewService.get_reviews")
    def test_get_reviews_no_filter(
        self,
        mock_get_reviews,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/review without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_reviews.return_value = {
            "items": [
                {"_id": "123", "name": "review1"},
                {"_id": "456", "name": "review2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/review")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_reviews.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.review_routes.create_flask_token")
    @patch("src.routes.review_routes.create_flask_breadcrumb")
    @patch("src.routes.review_routes.ReviewService.get_reviews")
    def test_get_reviews_with_name_filter(
        self,
        mock_get_reviews,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/review with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_reviews.return_value = {
            "items": [{"_id": "123", "name": "test-review"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/review?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_reviews.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.review_routes.create_flask_token")
    @patch("src.routes.review_routes.create_flask_breadcrumb")
    @patch("src.routes.review_routes.ReviewService.get_review")
    def test_get_review_success(
        self,
        mock_get_review,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/review/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_review.return_value = {
            "_id": "123",
            "name": "review1",
        }

        response = self.client.get("/api/review/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_review.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.review_routes.create_flask_token")
    @patch("src.routes.review_routes.create_flask_breadcrumb")
    @patch("src.routes.review_routes.ReviewService.get_review")
    def test_get_review_not_found(
        self,
        mock_get_review,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/review/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_review.side_effect = HTTPNotFound(
            "Review 999 not found"
        )

        response = self.client.get("/api/review/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Review 999 not found")

    @patch("src.routes.review_routes.create_flask_token")
    def test_create_review_unauthorized(self, mock_create_token):
        """Test POST /api/review when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/review",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
