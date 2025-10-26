from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT"),
}


class Customer(BaseModel):
    name: str
    phone: str
    address: str
    delivery_date: str


@app.get("/")
def home():
    return {"message": "✅ Chatbot API aktif dan siap menerima data!"}


@app.get("/customers/", response_model=List[dict])
def get_all_customers():
    """Endpoint untuk mengambil semua data customer"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except mysql.connector.Error as err:
        return {"error": str(err)}


@app.post("/save_customer/")
def save_customer(data: Customer):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
            INSERT INTO customers (name, phone, address, delivery_date)
            VALUES (%s, %s, %s, %s)
        """
        values = (data.name, data.phone, data.address, data.delivery_date)
        cursor.execute(query, values)
        conn.commit()
        return {"message": "✅ Data berhasil disimpan ke database!"}

    except Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")

    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()
