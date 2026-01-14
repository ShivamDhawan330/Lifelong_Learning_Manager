# **Lifelong Learning Manager**

Welcome to Lifelong Learning Manager – a smart, personalized AI-driven web application designed to help users learn topics at their own pace, with AI explanations, real-world examples, and quizzes!

LINK: https://lifelong-learning-manager.onrender.com/


## ___Project Overview___

This web app allows users to:

* Create personalized learning schedules with topics of their choice.

* Learn topics step-by-step where each topic is explained in simple words along with a real-life example.

* Test their understanding using dynamically generated AI-based quizzes (True/False format).

* Track their progress across different schedules.

* Use AI guidance for further clarification if a topic is still confusing.


The goal is to simulate a personal tutor-like experience where the system adapts based on user's learning pace.



## ___Features___ 

### **User Authentication**

Signup/Login system using username, email, and password.


### **Create Your Own Learning Schedule**

Add topics you want to learn sequentially.

Name your schedule (example: "Introduction to Robotics").


### **AI-Powered Topic Explanation**

Each topic is explained by an AI (Gemini model) in beginner-friendly language.

Relatable examples are included to deepen understanding.


### **Dynamic Quiz Generation**

After explanation, a quick 5-question True/False quiz is generated to test comprehension.

User answers are compared with correct answers.

Final Score is displayed.


### **Continue Learning Flow**

User moves to next topic if they understood the previous one.

If confused, a deeper bullet-pointed explanation is generated.


### **Progress Tracking**

Marks topics as completed once understood.

Automatically marks the entire schedule as "Completed" when all topics are finished.


### **Friendly Dashboard**

View all your existing schedules.

Pick up learning from where you left off.

Start new schedules anytime.


### **Secure Session Management**

User login persists across pages until logout.

Session stores schedule-specific context securely.



## ___Tech Stack___

**Backend**: Flask (Python)

**Frontend**: HTML, Bootstrap 5, Jinja Templates

**Database**: PostgreSQL (managed via Supabase)

**LLM**: Google Gemini-2.0-flash-lite

**AI Agent Framework**: Langchain


## ___Flow Diagram___

```
Login/Signup → Dashboard →

    ├── Create New Schedule
           └── Add Topics → Start Learning
    
    └── Existing Schedules
            └── Continue Topics
            

At each topic:

AI explains → User chooses:

OK → Quiz (optional) → Next Topic

Not OK → Get deeper explanation → Then Quiz
```



## ___Future Consideration___

> Add Google OAuth login for faster signup.

> Display analytics dashboard (e.g., % topics completed, average quiz score).

> Email reminders: "Hey, you haven't learned anything today!"

> Mobile-optimized UI (currently desktop-friendly).



## ___Key Motivations___

Promote lifelong learning in an engaging way.
Enable users to control their own learning pace.

## ___Final Note___

"Lifelong Learning Manager" empowers learners by combining human curiosity + AI assistance — making everyday learning simpler, structured, and more joyful.

!!
Copyright (c) 2025 Shivam Dhawan. All rights reserved.  
This app is proprietary and confidential.  
Unauthorized copying, modification, distribution, or use is strictly prohibited. 
!!


