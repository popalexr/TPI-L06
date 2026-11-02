import pytest
from fastapi.testclient import TestClient

from hello import DB, app


@pytest.fixture
def client():
    DB.clear()
    with TestClient(app) as test_client:
        yield test_client
    DB.clear()


def make_reading(seq=1, **changes):
    reading = {
        "dev": "senzor-1",
        "seq": seq,
        "ts": 1762096000,
        "temp": 21.5,
        "hum": 40,
    }
    reading.update(changes)
    return reading


def add_readings(client):
    for seq in (1, 2):
        assert client.post("/readings", json=make_reading(seq)).status_code == 201


# Cele 11 teste din PDF.
def test_post_reading(client):
    reading = make_reading()
    response = client.post("/readings", json=reading)

    assert response.status_code == 201
    assert response.json() == reading
    assert client.get("/devices/senzor-1/readings").json() == [reading]


def test_post_duplicate(client):
    reading = make_reading()
    assert client.post("/readings", json=reading).status_code == 201

    response = client.post("/readings", json=make_reading(temp=30))

    assert response.status_code == 409
    assert response.json()["detail"]
    assert client.get("/devices/senzor-1/readings").json() == [reading]


def test_post_invalid_temperature(client):
    response = client.post("/readings", json=make_reading(seq=2, temp=100))

    assert response.status_code == 422
    assert client.get("/devices/senzor-1/readings").status_code == 404


def test_post_invalid_device(client):
    response = client.post("/readings", json=make_reading(dev="Senzor 1"))

    assert response.status_code == 422


def test_post_without_humidity(client):
    reading = make_reading(seq=2)
    del reading["hum"]

    response = client.post("/readings", json=reading)

    assert response.status_code == 201
    assert response.json() == {**reading, "hum": None}


def test_get_readings(client):
    add_readings(client)

    response = client.get("/devices/senzor-1/readings")

    assert response.status_code == 200
    assert response.json() == [make_reading(1), make_reading(2)]


def test_get_since(client):
    assert client.post("/readings", json=make_reading(1)).status_code == 201
    reading = make_reading(2, hum=None)
    assert client.post("/readings", json=reading).status_code == 201

    response = client.get("/devices/senzor-1/readings?since=1")

    assert response.status_code == 200
    assert response.json() == [reading]


def test_get_limit(client):
    add_readings(client)

    response = client.get("/devices/senzor-1/readings?limit=1")

    assert response.status_code == 200
    assert response.json() == [make_reading(1)]


def test_get_invalid_limit(client):
    response = client.get("/devices/senzor-1/readings?limit=0")

    assert response.status_code == 422


def test_get_unknown_device(client):
    response = client.get("/devices/necunoscut/readings")

    assert response.status_code == 404


def test_get_invalid_device(client):
    response = client.get("/devices/ABC/readings")

    assert response.status_code == 422


# Teste pentru bonusuri.
def test_min_temp_filters_before_limit(client):
    for seq, temp in ((4, 30), (2, 20), (1, 10), (3, 25)):
        response = client.post("/readings", json=make_reading(seq, temp=temp))
        assert response.status_code == 201

    response = client.get(
        "/devices/senzor-1/readings?since=1&min_temp=25&limit=1"
    )

    assert response.status_code == 200
    assert response.json() == [make_reading(3, temp=25)]


def test_min_temp_no_results(client):
    add_readings(client)

    response = client.get("/devices/senzor-1/readings?min_temp=30")

    assert response.status_code == 200
    assert response.json() == []


def test_min_temp_zero(client):
    for seq, temp in ((1, -5), (2, 0)):
        assert client.post("/readings", json=make_reading(seq, temp=temp)).status_code == 201

    response = client.get("/devices/senzor-1/readings?min_temp=0")

    assert response.status_code == 200
    assert response.json() == [make_reading(2, temp=0)]


def test_devices_empty(client):
    response = client.get("/devices")

    assert response.status_code == 200
    assert response.json() == []


def test_devices_counts(client):
    assert client.post("/readings", json=make_reading(dev="senzor-2")).status_code == 201
    add_readings(client)
    assert client.post("/readings", json=make_reading()).status_code == 409
    assert client.post("/readings", json=make_reading(dev="senzor-3", temp=100)).status_code == 422

    response = client.get("/devices")

    assert response.status_code == 200
    assert response.json() == [
        {"dev": "senzor-1", "readings_count": 2},
        {"dev": "senzor-2", "readings_count": 1},
    ]


# Alte verificari.
@pytest.mark.parametrize("query", ["since=-1", "since=abc", "limit=101", "min_temp=abc"])
def test_invalid_query(client, query):
    response = client.get(f"/devices/senzor-1/readings?{query}")

    assert response.status_code == 422


def test_readings_sorted(client):
    for seq in (3, 1, 2):
        assert client.post("/readings", json=make_reading(seq)).status_code == 201

    response = client.get("/devices/senzor-1/readings")

    assert response.status_code == 200
    assert [reading["seq"] for reading in response.json()] == [1, 2, 3]


def test_same_seq_different_devices(client):
    for dev in ("senzor-1", "senzor-2"):
        assert client.post("/readings", json=make_reading(dev=dev)).status_code == 201


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
