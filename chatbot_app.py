import streamlit as st
import requests
from datetime import datetime
import re
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd
import mysql.connector
from mysql.connector import Error

load_dotenv()

# CONFIG
st.set_page_config(page_title="💬 Chatbot Customer Service")

API_URL = "http://127.0.0.1:8000/save_customer/"
GET_ALL_URL = "http://127.0.0.1:8000/customers/"

# MySQL Config
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

client = OpenAI()

# Admin credentials
ADMIN_PASSWORD = "admin123"

# STATE
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "role" not in st.session_state:
    st.session_state.role = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = None

if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "name": None,
        "phone": None,
        "address": None,
        "delivery_date": None,
    }

if "step" not in st.session_state:
    st.session_state.step = "start"

if "show_post_submit_options" not in st.session_state:
    st.session_state.show_post_submit_options = False


# UTILS
def extract_phone(text):
    match = re.search(r"(\+?\d{8,15})", text)
    return match.group(1) if match else None


def extract_date(text):
    pattern = r"(\d{1,2}) (\w+) (\d{4})(?: (?:jam )?(\d{1,2})[.:](\d{2}))?"
    match = re.search(pattern, text.lower())
    if match:
        day, month_name, year, hour, minute = match.groups()
        months = {
            "januari": 1,
            "februari": 2,
            "maret": 3,
            "april": 4,
            "mei": 5,
            "juni": 6,
            "juli": 7,
            "agustus": 8,
            "september": 9,
            "oktober": 10,
            "november": 11,
            "desember": 12,
        }
        month = months.get(month_name, 0)
        hour = int(hour) if hour else 10
        minute = int(minute) if minute else 0
        try:
            return datetime(int(year), month, int(day), hour, minute).strftime(
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            return None
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d %H:%M").strftime(
            "%Y-%m-%d %H:%M"
        )
    except:
        return None


def ai_assist(prompt, context="customer support"):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Kamu adalah asisten {context}. Balas singkat dan jelas.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"(AI Error: {e})"


def reset_to_main_menu():
    st.session_state.mode = None
    st.session_state.messages = []
    st.session_state.step = "start"
    st.session_state.user_data = {
        "name": None,
        "phone": None,
        "address": None,
        "delivery_date": None,
    }
    st.session_state.show_post_submit_options = False


def logout():
    st.session_state.authenticated = False
    st.session_state.role = None
    reset_to_main_menu()


def get_customers_from_db():
    """Ambil data customer langsung dari MySQL database"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers ORDER BY id DESC")
        rows = cursor.fetchall()
        return rows
    except Error as err:
        st.error(f"❌ Database Error: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_all_customers():
    """Fallback: coba API dulu, kalau gagal pakai database langsung"""
    try:
        response = requests.get(GET_ALL_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return get_customers_from_db()
    except:
        return get_customers_from_db()


def delete_customer_by_id(customer_id):
    """Hapus 1 data customer berdasarkan ID"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
        conn.commit()
        st.success(f"✅ Data dengan ID {customer_id} berhasil dihapus.")
    except Error as err:
        st.error(f"❌ Gagal menghapus data ID {customer_id}: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def delete_all_customers():
    """Hapus semua data di tabel customers"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers")
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as err:
        st.error(f"❌ Gagal menghapus semua data: {err}")
        return False


if not st.session_state.authenticated:
    st.title("🏢 Customer Service System")
    st.write("Selamat datang! Silakan pilih role Anda:")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")

        if st.button("👤 Masuk sebagai User", width="stretch", type="primary"):
            st.session_state.authenticated = True
            st.session_state.role = "user"
            st.rerun()

        st.markdown("---")

        st.markdown("### 🔐 Login Admin")
        admin_password = st.text_input(
            "Password Admin", type="password", key="admin_password"
        )

        if st.button("🔑 Login sebagai Admin", width="stretch"):
            if admin_password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.role = "admin"
                st.success("Login admin berhasil!")
                st.rerun()
            else:
                st.error("❌ Password admin salah!")

    st.stop()


st.title("💬 Chatbot Customer Service")
col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.role == "admin":
        st.info("👨‍💼 Logged in sebagai: **Admin**")
    else:
        st.info("👤 Logged in sebagai: **User**")
with col2:
    if st.button("🚪 Logout"):
        logout()
        st.rerun()

st.markdown("---")


if st.session_state.role == "admin":
    st.subheader("📊 Admin Dashboard")

    tab1, tab2 = st.tabs(["📋 Database Customer", "📈 Statistik"])

    with tab1:
        st.write("### Data Semua Customer")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("🔄 Refresh Data"):
                st.rerun()

        with col2:
            if "confirm_delete_all" not in st.session_state:
                st.session_state.confirm_delete_all = False

            delete_clicked = st.button("🧹 Delete ALL Data")

            if delete_clicked:
                st.session_state.confirm_delete_all = True

            if st.session_state.confirm_delete_all:
                st.warning(
                    "⚠️ Yakin mau hapus **SEMUA DATA CUSTOMER**? Aksi ini tidak bisa dibatalkan."
                )
                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("✅ YA, Hapus Semua Data"):
                        if delete_all_customers():
                            st.session_state.confirm_delete_all = False
                            st.success("🧹 Semua data berhasil dihapus!")
                            st.rerun()
                with col_confirm2:
                    if st.button("❌ Batal"):
                        st.session_state.confirm_delete_all = False
                        st.rerun()

        with st.spinner("Mengambil data dari database..."):
            customers = get_customers_from_db()

        if customers:
            df = pd.DataFrame(customers)
            st.success(f"✅ Data berhasil diambil dari MySQL Database")

            st.write(f"Total data: **{len(df)}** customer")

            for i, row in df.iterrows():
                col1, col2, col3, col4 = st.columns([1, 2, 3, 1])
                with col1:
                    st.write(f"**ID:** {row['id']}")
                with col2:
                    st.write(row["name"])
                with col3:
                    st.write(row["phone"])
                with col4:
                    if st.button("🗑 Delete", key=f"delete_{row['id']}"):
                        delete_customer_by_id(row["id"])
                        st.rerun()

            # === Tombol download CSV ===
            st.markdown("---")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Data (CSV)",
                data=csv,
                file_name=f'customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime="text/csv",
            )

        else:
            st.warning(
                "⚠️ Belum ada data customer atau gagal mengambil data dari database."
            )
            st.info("💡 Pastikan konfigurasi database di file .env sudah benar")

    with tab2:
        st.write("### Statistik Customer")

        if customers:
            df = pd.DataFrame(customers)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Customer", len(customers))

            with col2:
                if "delivery_date" in df.columns:
                    today = datetime.now().date()
                    df["delivery_date_parsed"] = pd.to_datetime(
                        df["delivery_date"], errors="coerce"
                    )
                    upcoming = len(df[df["delivery_date_parsed"].dt.date >= today])
                    st.metric("Pengiriman Mendatang", upcoming)
                else:
                    st.metric("Pengiriman Mendatang", "-")

            with col3:
                if "phone" in df.columns:
                    unique_phones = df["phone"].nunique()
                    st.metric("Nomor Unik", unique_phones)
                else:
                    st.metric("Nomor Unik", "-")

            if "delivery_date" in df.columns:
                st.markdown("---")
                st.write("#### 📅 Pengiriman per Bulan")
                df["month"] = df["delivery_date_parsed"].dt.to_period("M").astype(str)
                monthly_count = df.groupby("month").size().reset_index(name="count")
                st.bar_chart(monthly_count.set_index("month"))
        else:
            st.info("Belum ada data untuk ditampilkan")


if st.session_state.role == "user":
    if st.session_state.mode not in ["form", "chat"]:
        st.write("Halo! Saya asisten layanan pelanggan Anda 👋")
        st.write("Silakan pilih mode:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Isi Formulir Pengiriman"):
                st.session_state.mode = "form"
                st.rerun()
        with col2:
            if st.button("💭 Ngobrol dengan Asisten"):
                st.session_state.mode = "chat"
                st.session_state.step = "name"
                st.rerun()

    if st.session_state.mode == "form":
        st.subheader("📝 Formulir Pengiriman")

        if st.session_state.show_post_submit_options:
            st.success("✅ Data berhasil disimpan!")
            st.write("Apa yang ingin Anda lakukan selanjutnya?")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🏠 Menu Awal"):
                    reset_to_main_menu()
                    st.rerun()
            with col2:
                if st.button("💭 Tanya AI"):
                    st.session_state.mode = "chat"
                    st.session_state.step = "done"
                    st.session_state.messages = [
                        {
                            "role": "assistant",
                            "content": "Hai! Ada yang bisa saya bantu?",
                        }
                    ]
                    st.session_state.show_post_submit_options = False
                    st.rerun()
            with col3:
                if st.button("✅ Selesai"):
                    st.balloons()
                    st.success("🎉 Terima kasih telah menggunakan layanan kami!")
                    st.info("Silakan logout atau refresh halaman untuk memulai lagi.")
                    st.session_state.show_post_submit_options = False
                    st.stop()
        else:
            with st.form("delivery_form"):
                name = st.text_input("Nama Lengkap")
                phone = st.text_input("Nomor Telepon")
                address = st.text_area("Alamat Lengkap")
                delivery_date = st.text_input(
                    "Tanggal & Jam Pengiriman (contoh: 27 September 2025 jam 17.00)"
                )

                submitted = st.form_submit_button("✅ Kirim")

                if submitted:
                    phone_clean = extract_phone(phone)
                    date_clean = extract_date(delivery_date)

                    if not name or not phone_clean or not address or not date_clean:
                        st.error("⚠️ Mohon isi semua field dengan benar!")
                    else:
                        user_data = {
                            "name": name,
                            "phone": phone_clean,
                            "address": address,
                            "delivery_date": date_clean,
                        }

                        try:
                            response = requests.post(API_URL, json=user_data, timeout=5)
                            if response.status_code == 200:
                                st.session_state.show_post_submit_options = True
                                st.rerun()
                            else:
                                st.error(
                                    f"⚠️ Gagal menyimpan data. Status: {response.status_code}"
                                )
                        except requests.exceptions.RequestException as e:
                            st.error(f"⚠️ Terjadi kesalahan: {e}")

    if st.session_state.mode == "chat":
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        step = st.session_state.step
        user_data = st.session_state.user_data

        if step == "name" and len(st.session_state.messages) == 0:
            st.session_state.messages.append(
                {"role": "assistant", "content": "Siapa nama kamu?"}
            )
            st.rerun()

        if prompt := st.chat_input("Ketik di sini..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            if step == "name":
                user_data["name"] = prompt.strip()
                reply = f"Baik, {user_data['name']}. Nomor telepon yang bisa kami hubungi berapa ya?"
                st.session_state.step = "phone"

            elif step == "phone":
                phone = extract_phone(prompt)
                if phone:
                    user_data["phone"] = phone
                    reply = (
                        "Terima kasih! Sekarang mohon alamat lengkap tujuan pengiriman."
                    )
                    st.session_state.step = "address"
                else:
                    reply = "Nomor telepon tidak terbaca. Coba lagi dengan format yang benar (contoh: 08123456789)"

            elif step == "address":
                user_data["address"] = prompt.strip()
                reply = "Alamat sudah dicatat. Kapan dan jam berapa pengiriman diinginkan? (contoh: 27 September 2025 jam 17.00 WIB)"
                st.session_state.step = "delivery_date"

            elif step == "delivery_date":
                delivery_date = extract_date(prompt)
                if delivery_date:
                    user_data["delivery_date"] = delivery_date
                    st.session_state.step = "confirm"
                else:
                    reply = "Format tanggal/jam belum saya pahami. Coba lagi (contoh: 27 September 2025 jam 17.00)"

            elif step == "done":
                with st.spinner("Asisten sedang mengetik..."):
                    reply = ai_assist(prompt, "layanan pelanggan")
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
                st.rerun()

            if st.session_state.step != "confirm" and step != "done":
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
            st.rerun()

        if step == "confirm":
            summary = (
                f"Berikut data pengiriman yang kamu isi:\n\n"
                f"- Nama: {user_data['name']}\n"
                f"- Nomor: {user_data['phone']}\n"
                f"- Alamat: {user_data['address']}\n"
                f"- Tanggal & Jam: {user_data['delivery_date']} WIB"
            )
            st.chat_message("assistant").write(summary)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Konfirmasi"):
                    try:
                        response = requests.post(API_URL, json=user_data, timeout=5)
                        if response.status_code == 200:
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": "✅ Data kamu sudah berhasil disimpan. Terima kasih!",
                                }
                            )
                            st.session_state.step = "done"
                            st.rerun()
                        else:
                            st.chat_message("assistant").write(
                                f"⚠️ Terjadi kesalahan saat menyimpan data.\nStatus: {response.status_code}\nDetail: {response.text}"
                            )
                    except requests.exceptions.RequestException as e:
                        st.chat_message("assistant").write(
                            f"⚠️ Terjadi kesalahan saat menghubungi server: {e}"
                        )

            with col2:
                if st.button("❌ Edit Data"):
                    st.session_state.step = "name"
                    st.session_state.messages = []
                    st.session_state.user_data = {
                        "name": None,
                        "phone": None,
                        "address": None,
                        "delivery_date": None,
                    }
                    st.rerun()

        if step == "done":
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏠 Kembali ke Menu Awal"):
                    reset_to_main_menu()
                    st.rerun()
            with col2:
                if st.button("✅ Selesai"):
                    st.balloons()
                    st.success("🎉 Terima kasih telah menggunakan layanan kami!")
                    st.info("Silakan logout atau refresh halaman untuk memulai lagi.")
                    st.stop()
