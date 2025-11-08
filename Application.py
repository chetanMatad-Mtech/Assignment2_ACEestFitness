from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Store workouts in memory (use a database in real apps)
workouts = []

# HTML template (inline for simplicity, you can separate into templates/)
template = """
<!DOCTYPE html>
<html>
<head>
    <title>ACEestFitness and Gym</title>
</head>
<body>
    <h1>ACEestFitness and Gym</h1>

    <h2>Add Workout</h2>
    <form method="POST" action="{{ url_for('add_workout') }}">
        <label for="workout">Workout:</label>
        <input type="text" id="workout" name="workout" required><br><br>

        <label for="duration">Duration (minutes):</label>
        <input type="number" id="duration" name="duration" required><br><br>

        <button type="submit">Add Workout</button>
    </form>

    <h2>Logged Workouts</h2>
    {% if workouts %}
        <ul>
        {% for w in workouts %}
            <li>{{ loop.index }}. {{ w['workout'] }} - {{ w['duration'] }} minutes</li>
        {% endfor %}
        </ul>
    {% else %}
        <p>No workouts logged yet.</p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(template, workouts=workouts)

@app.route("/add", methods=["POST"])
def add_workout():
    workout = request.form.get("workout")
    duration = request.form.get("duration")

    if workout and duration.isdigit():
        workouts.append({"workout": workout, "duration": int(duration)})
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
