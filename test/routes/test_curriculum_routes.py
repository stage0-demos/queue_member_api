"""
Unit tests for Curriculum routes.

These tests validate the Flask route layer for the Curriculum domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.curriculum_routes import create_curriculum_routes


class TestCurriculumRoutes(unittest.TestCase):
    """Test cases for Curriculum routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_curriculum_routes(),
            url_prefix="/api/curriculum",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.curriculum_routes.create_flask_token")
    @patch("src.routes.curriculum_routes.create_flask_breadcrumb")
    @patch("src.routes.curriculum_routes.CurriculumService.create_curriculum")
    @patch("src.routes.curriculum_routes.CurriculumService.get_curriculum")
    def test_create_curriculum_success(
        self,
        mock_get_curriculum,
        mock_create_curriculum,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/curriculum for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_curriculum.return_value = "123"
        mock_get_curriculum.return_value = {
            "_id": "123",
            "name": "test-curriculum",
            "status": "active",
        }

        response = self.client.post(
            "/api/curriculum",
            json={"name": "test-curriculum", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_curriculum.assert_called_once()
        mock_get_curriculum.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.curriculum_routes.create_flask_token")
    @patch("src.routes.curriculum_routes.create_flask_breadcrumb")
    @patch("src.routes.curriculum_routes.CurriculumService.get_curriculums")
    def test_get_curriculums_no_filter(
        self,
        mock_get_curriculums,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/curriculum without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_curriculums.return_value = {
            "items": [
                {"_id": "123", "name": "curriculum1"},
                {"_id": "456", "name": "curriculum2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/curriculum")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_curriculums.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.curriculum_routes.create_flask_token")
    @patch("src.routes.curriculum_routes.create_flask_breadcrumb")
    @patch("src.routes.curriculum_routes.CurriculumService.get_curriculums")
    def test_get_curriculums_with_name_filter(
        self,
        mock_get_curriculums,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/curriculum with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_curriculums.return_value = {
            "items": [{"_id": "123", "name": "test-curriculum"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/curriculum?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_curriculums.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.curriculum_routes.create_flask_token")
    @patch("src.routes.curriculum_routes.create_flask_breadcrumb")
    @patch("src.routes.curriculum_routes.CurriculumService.get_curriculum")
    def test_get_curriculum_success(
        self,
        mock_get_curriculum,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/curriculum/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_curriculum.return_value = {
            "_id": "123",
            "name": "curriculum1",
        }

        response = self.client.get("/api/curriculum/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_curriculum.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.curriculum_routes.create_flask_token")
    @patch("src.routes.curriculum_routes.create_flask_breadcrumb")
    @patch("src.routes.curriculum_routes.CurriculumService.get_curriculum")
    def test_get_curriculum_not_found(
        self,
        mock_get_curriculum,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/curriculum/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_curriculum.side_effect = HTTPNotFound(
            "Curriculum 999 not found"
        )

        response = self.client.get("/api/curriculum/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Curriculum 999 not found")

    @patch("src.routes.curriculum_routes.create_flask_token")
    def test_create_curriculum_unauthorized(self, mock_create_token):
        """Test POST /api/curriculum when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/curriculum",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
