from app import create_app


def test_health_endpoint():
    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()

    assert data["status"] == "ok"
    assert data["phase"] == 1
    assert "database" in data
