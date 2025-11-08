import pytest
from Application import app  # replace with your Flask file name

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Check if home page loads correctly"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"ACEestFitness and Gym" in response.data
    assert b"No workouts logged yet." in response.data

def test_add_workout(client):
    """Add a workout and check if it appears"""
    response = client.post("/add", data={"workout": "Arms", "duration": "15"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Arms" in response.data
    assert b"15 minutes" in response.data

def test_invalid_duration(client):
    """Try to add workout with invalid duration (non-numeric)"""
    response = client.post("/add", data={"workout": "ThreadMill", "duration": "abc"}, follow_redirects=True)
    # Should not add invalid workout
    assert response.status_code == 200
    assert b"Running - abc minutes" not in response.data

def test_multiple_workouts(client):
    """Add multiple workouts and verify list"""
    client.post("/add", data={"workout": "Pushup", "duration": "20"}, follow_redirects=True)
    client.post("/add", data={"workout": "Plank", "duration": "5"}, follow_redirects=True)
    
    response = client.get("/")
    assert b"Pushup" in response.data
    assert b"20 minutes" in response.data
    assert b"Plank" in response.data
    assert b"5 minutes" in response.data
