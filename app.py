from flask import Flask, render_template, request, redirect, session
import difflib
import openai
import os

app = Flask(__name__)
app.secret_key = 'bujja_secret_key'  # Required for session handling

# 🩺 Mock patient database
patients = {
    "john doe": {"age": 45, "visit": "Oct 10", "diagnosis": "Hypertension"},
    "emma": {"age": 32, "visit": "Oct 5", "diagnosis": "Diabetes"},
    "ravi kumar": {"age": 50, "visit": "Oct 12", "diagnosis": "Asthma"},
    "anita": {"age": 28, "visit": "Oct 15", "diagnosis": "Migraine"}
}

# 🔐 Optional: Enable OpenAI smart replies
USE_OPENAI = True
openai.api_key = os.getenv("OPENAI_API_KEY")  # Use Railway Variables

# 🔍 Fuzzy name matching
def find_patient_name(query):
    names = list(patients.keys())
    match = difflib.get_close_matches(query, names, n=1, cutoff=0.6)
    return match[0] if match else None

# 🧠 OpenAI fallback response
def get_openai_response(query):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an EMR support assistant."},
                {"role": "user", "content": query}
            ]
        )
        return completion.choices[0].message.content
    except Exception:
        return "Sorry, I'm having trouble accessing smart replies right now."

# 🔐 Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role')

        if username and role:
            session['username'] = username
            session['role'] = role

            if role == "doctor":
                return redirect('/doctor')
            elif role == "admin":
                return redirect('/admin')
        else:
            return "Missing login details. Please go back and fill in all fields."

    return render_template('login.html')

# 👨‍⚕️ Doctor dashboard
@app.route('/doctor', methods=['GET', 'POST'])
def doctor_dashboard():
    if 'username' not in session or session['role'] != 'doctor':
        return redirect('/')

    response = ""
    if request.method == 'POST':
        query = request.form['query'].lower()

        if "patient" in query:
            found = False
            for name in patients:
                if name in query:
                    data = patients[name]
                    response = f"Patient {name.title()}: Age {data['age']}, Last Visit - {data['visit']}, Diagnosis - {data['diagnosis']}."
                    found = True
                    break
            if not found:
                name_guess = find_patient_name(query)
                if name_guess:
                    data = patients[name_guess]
                    response = f"(Did you mean {name_guess.title()}?) Age {data['age']}, Last Visit - {data['visit']}, Diagnosis - {data['diagnosis']}."
                else:
                    response = "Patient not found in database."
        else:
            response = get_openai_response(query) if USE_OPENAI else "Doctor view: I'm analyzing your query..."

    return render_template('doctor.html', response=response, username=session['username'], role=session['role'], patients=patients)

# 🧑‍💼 Admin dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/')

    response = ""
    if request.method == 'POST':
        query = request.form['query'].lower()

        if "login failed" in query:
            response = "Try resetting your password or check network connectivity."
        elif "error" in query:
            response = "Check server connection or contact system admin."
        else:
            response = get_openai_response(query) if USE_OPENAI else "Admin view: I'm analyzing your query..."

    return render_template('admin.html', response=response, username=session['username'], role=session['role'])

# 🔓 Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 🚀 Railway-compatible run command
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)