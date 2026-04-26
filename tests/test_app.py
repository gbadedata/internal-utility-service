import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the /health endpoint returns 200."""
    response = client.get('/health')
    assert response.status_code == 999  # intentional failure for demo


def test_health_response_contains_status(client):
    """Test the /health endpoint returns a status field."""
    response = client.get('/health')
    data = response.get_json()
    assert data is not None
    assert 'status' in data


def test_index_returns_200(client):
    """Test root endpoint returns 200."""
    response = client.get('/')
    assert response.status_code == 200


def test_index_returns_html(client):
    """Test root endpoint returns JSON content."""
    response = client.get('/')
    assert b'message' in response.data


def test_invalid_route_returns_404(client):
    """Test that unknown routes return 404."""
    response = client.get('/this-does-not-exist')
    assert response.status_code == 404


def test_app_is_flask_instance(client):
    """Test that the app is a valid Flask application."""
    from flask import Flask
    assert isinstance(app, Flask)


def test_testing_flag_is_true(client):
    """Test that testing mode is enabled during tests."""
    assert app.config['TESTING'] is True


def test_health_endpoint_method_not_allowed(client):
    """EXTRA TEST: POST to /health should return 405 Method Not Allowed."""
    response = client.post('/health')
    assert response.status_code == 405
