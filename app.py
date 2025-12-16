import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

st.set_page_config(page_title="StreamFlex Manager", layout="wide")
st.title("Panou de Administrare StreamFlex")

load_dotenv()

if "MONGO_URI" in os.environ:
    connection_string = os.environ["MONGO_URI"]
elif "MONGO_URI" in st.secrets:
    connection_string = st.secrets["MONGO_URI"]
else:
    connection_string = None

if not connection_string:
    st.error("Eroare: MONGO_URI nu a fost găsit. Verificați .env (Local) sau Secrets (Cloud).")
    st.stop()

try:
    client = MongoClient(connection_string)
    db = client["StreamFlex"]
    collection = db["divertisment"]
except Exception as e:
    st.error(f"Eroare de Conexiune: {e}")
    st.stop()

st.subheader("Căutare și Filtrare")

with st.form("search_form"):
    c1, c2 = st.columns(2)
    with c1:
        filter_type = st.selectbox("Tip Conținut", ["Toate", "Film", "Serial"])
    with c2:
        search_title = st.text_input("Titlu")

    c3, c4 = st.columns(2)
    with c3:
        search_genre = st.text_input("Gen (ex: Drama)")
    with c4:
        min_rating = st.slider("Notă Minimă", 0.0, 10.0, 0.0, step=0.1)

    st.write("")
    search_submitted = st.form_submit_button("Aplică Filtre")

query = {}
if filter_type != "Toate":
    query["tip"] = filter_type
if search_title:
    query["titlu"] = {"$regex": search_title, "$options": "i"}
if search_genre:
    query["genuri"] = {"$regex": search_genre, "$options": "i"}
if min_rating > 0:
    query["nota"] = {"$gte": min_rating}

items = list(collection.find(query, {"_id": 0, "titlu": 1, "tip": 1, "nota": 1, "genuri": 1, "recomandat": 1}))

st.divider()
st.metric("Rezultate Găsite", len(items))

if items:
    df = pd.DataFrame(items)
    cols = [c for c in ['titlu', 'tip', 'nota', 'recomandat', 'genuri'] if c in df.columns]

    dynamic_height = (len(df) * 35) + 38
    st.dataframe(df[cols], use_container_width=True, height=dynamic_height, hide_index=True)
else:
    st.warning("Nu au fost găsite rezultate.")

st.divider()
st.subheader("Adaugă Titlu Nou")

with st.form("add_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    new_title = c1.text_input("Titlu")
    new_type = c2.selectbox("Tip", ["Film", "Serial"])
    new_rating = c3.number_input("Notă", 0.0, 10.0, step=0.1)
    new_genre = c4.text_input("Gen")
    
    save_submitted = st.form_submit_button("Salvează în Baza de Date")
    
    if save_submitted and new_title:
        new_doc = {
            "titlu": new_title,
            "tip": new_type,
            "nota": new_rating,
            "genuri": [new_genre],
            "data_lansare": datetime.now(),
            "recomandat": True if new_rating >= 8.5 else False
        }
        collection.insert_one(new_doc)
        st.success(f"Succes: {new_title} a fost adăugat.")
        st.rerun()