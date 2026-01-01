import os
import numpy as np
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from sqlalchemy.dialects.postgresql import UUID
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import select


if not os.getenv("RENDER"):
    env_path = os.path.join(os.path.dirname(__file__), "A.env")
    print(env_path)
    load_dotenv(env_path, override=True)


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


#------------------------------- DATABASE ---------------------------

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': NullPool,
    'connect_args': {
        'keepalives': 1,
        'keepalives_idle': 30,
    }
}

db = SQLAlchemy(app)


class users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Text)
    email = db.Column(db.Text, unique=True)
    password_hash = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
class ustatus(db.Model):
    __tablename__ = 'ustatus'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    topic_id = db.Column(db.Integer)
    schedule_title = db.Column(db.Text)
    utid = db.Column(db.Text)
    status = db.Column(db.String(100)) 
    result = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('users', backref='statuses')


class utopic(db.Model):
    __tablename__ = 'utopic'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utid = db.Column(db.Text, db.ForeignKey('ustatus.utid'), nullable=False)
    seq_number = db.Column(db.Integer)
    title = db.Column(db.String(500))
    content = db.Column(db.Text)
    score = db.Column(db.Integer)
    status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

# ------------------------------------------------------------------------------#

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------Credentials -------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form
        if users.query.filter_by(email=data["email"]).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("signup"))

        hashed_pw = generate_password_hash(data["password"], method='pbkdf2:sha256')
        user = users(username=data["username"], email=data["email"], password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    print("🔹 Login Page Accessed")
    if "attempts" not in session:
        session["attempts"] = 3  # Set login attempts to 3
        
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print(f"🔹 Received Login Attempt for Email: {email}")
        user = users.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.user_id
            session.pop("attempts", None)
            flash(f"Login successful! Welcome {user.username}!", "success")
            return redirect(url_for("schedule"))
        else:
            session["attempts"] -= 1
            flash(f"Incorrect credentials. Attempts left: {session['attempts']}", "danger")
            if session["attempts"] <= 0:
                flash("Too many failed attempts. Try later.", "danger")
                return redirect(url_for("home"))
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))

# -----------------------------------------------------------------

@app.route("/schedule")
def schedule():
    if "user_id" not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for("home"))
    
    user = users.query.get(session["user_id"])
    return render_template("schedule.html", user=user)

@app.route('/existing')
def existing_schedules():

    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))


    schedules = ustatus.query.filter_by(user_id=user_id).all()

    if not schedules:
        return render_template("schedule.html", message="❌ No Existing Schedule. Please create one.", topics=None)


    return render_template("existing_schedules.html", message=None, schedules=schedules)



@app.route("/view_schedule_topics/", methods=["GET"])
def view_schedule_topics():
    user_id = session.get("user_id")
    if not user_id:
        flash("Unauthorized access.")
        return redirect(url_for("login"))
    
    utid = request.args.get("utid")
    if not utid:
        flash("No schedule selected.", "danger")
        return redirect(url_for("existing_schedules"))

    topics = utopic.query.filter_by(utid=utid).order_by(utopic.seq_number.asc()).all()
    sch = ustatus.query.filter_by(utid=utid).first()
    session['schedule_title'] = sch.schedule_title

    return render_template("view_topics.html", topics=topics, utid=utid)



@app.route("/new_schedule", methods=["GET", "POST"])
def new_schedule():
    if "user_id" not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        schedule_title = request.form.get("schedule_title")
        topics = request.form.getlist("topics")

        if not schedule_title or not topics:
            flash("Schedule title and at least one topic are required.", "danger")
            return redirect(url_for("new_schedule"))


        last_entry = ustatus.query.filter_by(user_id=user_id).order_by(ustatus.topic_id.desc()).first()
        next_topic_id = 1 if not last_entry else last_entry.topic_id + 1


        utid = f"{user_id}-{next_topic_id}"


        new_status = ustatus(
            user_id=user_id,
            topic_id=next_topic_id,
            schedule_title=schedule_title,
            utid=utid,
            status="In Progress",
            result=None
        )
        db.session.add(new_status)
        db.session.commit()


        for i, topic in enumerate(topics, start=1):
            db.session.add(utopic(
                utid=utid,
                seq_number=i,
                title=topic,
                status=False  # Not completed yet
            ))

        db.session.commit()
        flash("✅ Schedule created successfully!", "success")
        return redirect(url_for("schedule"))

    return render_template("new_schedule.html")



@app.route("/ai_agent_summary/<utid>", methods=["GET", "POST"])
def ai_agent_summary(utid):
    print(f"🔁 Method: {request.method}, UTID received: {utid}")
    if request.method == "POST":   
        stmt = select(utopic).where(utopic.utid == utid)
        with db.engine.connect() as conn:
            df = pd.read_sql(stmt,conn)

            if df.empty:
                return render_template("schedule.html", message="No topics found for this user/session.")


            df = df.sort_values(by="seq_number").reset_index(drop=True)
            if df["status"].all():
                db.session.query(ustatus).filter_by(utid=utid).update({"status": "Completed"})
                total_score = df["score"].sum()
                db.session.query(ustatus).filter_by(utid=utid).update({"result": int(total_score)})
                db.session.commit()
                return render_template("ai_output.html", message="🎉 All topics covered ✅")

            first_incomplete = df[df["status"] == False].iloc[0]
            topic = first_incomplete["title"]
            topic_row_id = first_incomplete["utid"]
            seq_number = int(first_incomplete["seq_number"])
            schedule_title = session.get("schedule_title", "related to the topic")


        summary_prompt = PromptTemplate(
            input_variables=["topic","schedule_title"],
            template="""
            You are a helpful teaching assistant.
            Explain the topic "{topic}", as a part of subject "{schedule_title}", in a simplified and summarized way for a beginner.
            Then give one real-life example that helps to understand it better.
            Return only the summary and the real-life example in two short paragraphs.
            """
        )


        llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        temperature=0)


        explanation = llm.invoke(summary_prompt.format(topic=topic,schedule_title=schedule_title)).content
        parts = explanation.split('\n', 1)
        explanation_text = parts[0].strip()
        example_text = parts[1].strip() if len(parts) > 1 else ""

        db.session.query(utopic).filter_by(utid=topic_row_id,seq_number = seq_number).update({"content": explanation_text})
        db.session.commit()
        return render_template("ai_output.html", topic=topic, explanation=explanation_text, example=example_text,utid=utid,seq_number=seq_number)

    else:
        return redirect(url_for('schedule'))


@app.route("/mark_complete/<utid>/<int:seq_number>", methods=["POST"])
def mark_complete(utid, seq_number):
    

    db.session.query(utopic).filter_by(utid=utid,seq_number = seq_number).update({"status": True})
    db.session.commit()
    

    return render_template("next_topic_prompt.html", utid=utid)


@app.route("/quiz/<utid>/<int:seq_number>",methods=["GET", "POST"])
def quiz(utid, seq_number):
    
    llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0)
    
    if request.method == "GET":
        topic_row = db.session.query(utopic).filter_by(utid=utid, seq_number=seq_number).first()
        topic = topic_row.title
        quiz_prompt = PromptTemplate(
            input_variables=["topic"],
            template="""
            Generate 5 True/ False type quiz questions and answers (give answers only as True or False, without including any explanation) on the topic: "{topic}".
            Format the response like:
            Q1: ...
            A1: ...
            Q2: ...
            A2: ...
            ...
            """)
        quiz_chain = LLMChain(llm=llm, prompt=quiz_prompt)

        quiz_output = quiz_chain.run(topic=topic)


        questions, answers = [], []
        for line in quiz_output.split("\n"):
            if line.strip().startswith("Q"):
                questions.append(line.strip())
            elif line.strip().startswith("A"):
                parts = line.strip().split(":", 1)
                if len(parts) > 1:
                    answers.append(parts[1].strip().capitalize())
        
        session["quiz_questions"] = questions
        session["quiz_answers"] = answers

        return render_template("quiz.html", topic=topic, questions=questions, answers=answers,utid=utid, seq_number=seq_number)
    
    else:
        score = 0
        user_answers=[]
        correct_answers = []
        questions = []
        q = session.get("quiz_questions", [])
        a = session.get("quiz_answers", [])
        for i in range(5):
            ua = request.form.get(f"q{i}")
            correct_answer = a[i] if i < len(a) else None
            question = q[i] if i < len(q) else None
            questions.append(question)
            correct_answers.append(correct_answer)
            user_answers.append(ua)
            if ua == correct_answer:
                score += 1
                
        

        db.session.query(utopic).filter_by(utid=utid, seq_number=seq_number).update({"score": score})
        db.session.commit()

        return render_template("quiz_result.html", score=score, total=5, utid=utid,seq_number=seq_number, qa_data=zip(questions, user_answers, correct_answers))



@app.route("/explain_more/<utid>/<int:seq_number>")
def explain_more(utid, seq_number):
    
    topic_row = db.session.query(utopic).filter_by(utid=utid, seq_number=seq_number).first()
    topic = topic_row.title if topic_row else None
    
    explain_prompt = PromptTemplate(
        input_variables=["topic"],
        template="""
        You are an expert tutor.
        Provide the detailed explaination of the topic "{topic}" in the form of bullet points. Explain the topic like you are explaining it to 5 year old kid.
        Limit to 5-6 key points only.
        Format as:
        - Point 1
        - Point 2
        ...
        """
    )

    llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0)
    
    explain_chain = LLMChain(llm=llm, prompt=explain_prompt)

    detailed_output = explain_chain.run(topic=topic)

    db.session.query(utopic).filter_by(utid=utid, seq_number=seq_number).update({"content": detailed_output})
    db.session.commit()

    return render_template("detailed_explanation.html", topic=topic, explanation=detailed_output, utid = utid,seq_number=seq_number)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),debug=True)

