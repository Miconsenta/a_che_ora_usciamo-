import streamlit as st
from datetime import datetime, timedelta, time

FORMATO = "%H:%M"

def round_pause_to_45_60_75(pausa_td: timedelta) -> timedelta:
    minuti = pausa_td.total_seconds() / 60.0
    if minuti <= 45:
        return timedelta(minutes=45)
    elif minuti <= 60:
        return timedelta(minutes=60)
    elif minuti <= 75:
        return timedelta(minutes=75)
    else:
        return timedelta(minutes=75)

def to_dt(t: time) -> datetime:
    # data fittizia, ci interessa solo l'orario
    return datetime(2000, 1, 1, t.hour, t.minute)

st.set_page_config(page_title="Calcolo uscita teorica", page_icon="🕒", layout="centered")
st.title("🕒 Calcolo uscita teorica + slot straordinario")

with st.sidebar:
    st.header("Parametri")
    ore_giornaliere = st.number_input("Ore giornaliere", min_value=0, max_value=24, value=7, step=1)
    minuti_giornali = st.number_input("Minuti giornalieri", min_value=0, max_value=59, value=36, step=1)
    limite_superiore = st.time_input("Limite superiore (fine slot)", value=time(20, 0), step=900)

st.subheader("Orari")
ingresso = st.time_input("Orario di ingresso", value=time(9, 0), step=300)
uscita_pranzo = st.time_input("Uscita pranzo", value=time(13, 0), step=300)
rientro_pranzo = st.time_input("Rientro pranzo", value=time(14, 0), step=300)

if st.button("Calcola", type="primary"):
    ingresso_dt = to_dt(ingresso)
    uscita_pranzo_dt = to_dt(uscita_pranzo)
    rientro_pranzo_dt = to_dt(rientro_pranzo)
    limite_dt = to_dt(limite_superiore)

    pausa_effettiva = rientro_pranzo_dt - uscita_pranzo_dt
    if pausa_effettiva.total_seconds() < 0:
        st.error("La pausa risulta negativa: verifica uscita/rientro pranzo.")
        st.stop()

    pausa_normata = round_pause_to_45_60_75(pausa_effettiva)
    tempo_lavoro = timedelta(hours=int(ore_giornaliere), minutes=int(minuti_giornali))
    uscita_teorica = ingresso_dt + tempo_lavoro + pausa_normata

    col1, col2, col3 = st.columns(3)
    col1.metric("Pausa effettiva", f"{int(pausa_effettiva.total_seconds()//60)} min")
    col2.metric("Pausa considerata", f"{int(pausa_normata.total_seconds()//60)} min")
    col3.metric("Uscita teorica", uscita_teorica.strftime(FORMATO))

    if uscita_teorica.hour >= 18:
        st.info('🫠  "Dura portarla a casa oggi eh??"')

    # Slot da 15'
    incremento = timedelta(minutes=15)
    slot_rows = []
    k = 1
    while True:
        corrente = uscita_teorica + incremento * k
        if corrente > limite_dt:
            break
        slot_rows.append({"Straordinario maturato": f"+{k*15} min", "Orario": corrente.strftime(FORMATO)})
        k += 1

    st.subheader("Slot ogni 15'")
    if not slot_rows:
        st.write(f"Nessuno slot entro il limite delle {limite_superiore.strftime(FORMATO)}.")
    else:
        st.dataframe(slot_rows, use_container_width=True)
