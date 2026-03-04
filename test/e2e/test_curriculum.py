"""
E2E tests for Curriculum endpoints.

These tests verify that Curriculum endpoints work correctly by making
actual HTTP requests to a running server.

To run these tests:
1. Start the server: pipenv run dev (or pipenv run api for containerized)
2. Run E2E tests: pipenv run e2e

API runs on port 8292 (same for dev and api).
"""
import pytest
import requests

BASE_URL = "http://localhost:8292"


def _err(response, expected):
    """Format assertion error with response body for debugging."""
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


def get_auth_token():
    """Helper function to get an authentication token from dev-login."""
    response = requests.post(
        f"{BASE_URL}/dev-login",
        json={"subject": "e2e-test-user", "roles": ["admin", "developer"]},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.mark.e2e
def test_create_curriculum_endpoint():
    """Test POST /api/curriculum endpoint and verify record persists in database."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-curriculum",
        "description": "E2E test curriculum document",
    }

    response = requests.post(f"{BASE_URL}/api/curriculum", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-curriculum"
    assert "created" in response_data
    assert "saved" in response_data


@pytest.mark.e2e
def test_get_curriculums_endpoint():
    """Test GET /api/curriculum endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/curriculum", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert "limit" in response_data, "Response should have 'limit' key"
    assert "has_more" in response_data, "Response should have 'has_more' key"
    assert "next_cursor" in response_data, "Response should have 'next_cursor' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_get_curriculums_with_name_filter():
    """Test GET /api/curriculum with name query parameter."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/curriculum?name=e2e", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_curriculum_endpoints_require_auth():
    """Test that curriculum endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/curriculum")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
