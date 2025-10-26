# 🧠 Customer Service Chatbot — Version 2 🤖

A complete **Customer Service Chatbot System** built for efficient delivery scheduling and customer support using a modern **Python stack**.

## ✨ Features

* **🌐 Frontend:** Interactive UI built with **Streamlit**.
* **⚙️ Backend:** Robust RESTful API using **FastAPI** for data handling.
* **💾 Database:** Persistent storage for customer and delivery data using **MySQL**.
* **🧠 AI Core:** Conversational assistance powered by **OpenAI GPT-4o-mini**.
* **🔐 Admin Dashboard:** View, export, and manage customer records.

---

## 🚀 Quick Start

Follow these steps to get the system running locally:

### 1. Prerequisites

* Python $\ge 3.9$
* MySQL $\ge 8$

### 2. Setup Database & Environment

1.  Create the database and user in MySQL (see detailed `schema.sql`).
2.  Create a **`.env`** file with your database credentials and `OPENAI_API_KEY`.

### 3. Run Application

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Start the **FastAPI Backend**:
    ```bash
    uvicorn main:app --reload
    ```
    *(Access API docs at: http://127.0.0.1:8000/docs)*

3.  Start the **Streamlit Frontend**:
    ```bash
    streamlit run chatbot_app.py
    ```
    *(Access UI at: http://localhost:8501)*

### 4. Project Structure

```bash
CHATBOT-2.0/
├─ chatbot_app.py      # Streamlit frontend
├─ README.md           # README file
├─ main.py             # FastAPI backend
├─ schema.sql          # MySQL database schema
├─ .env                # Environment variables
└─ requirements.txt    # Python dependencies
