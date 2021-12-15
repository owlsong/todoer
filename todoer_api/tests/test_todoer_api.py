from todoer_api import __version__
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_version():
    assert __version__ == "0.3.0"


def test_read_main():
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    body = response.json()
    # assert response.json() == {"msg": "Hello World"}
    assert body["service"] == "ToDoer"
    assert body["data_source"] == "mongo"
    assert body["version"] == __version__
