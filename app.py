import streamlit as st
import pandas as pd
import json

# Konfiguracja strony
st.set_page_config(page_title="TTBZ - Pełne Statystyki", layout="wide")
st.title("🏆 Profesjonalny System Statystyk: Twoja Twarz Brzmi Znajomo")

# Stałe
VALID_POINTS = [10, 7, 6, 5, 4, 3, 2, 1]

# CSS do kolorowania wierszy w Streamlit
def highlight_ranks(row):
    if "M-ce" in row.index: m_ce = row["M-ce"]
    elif "Miejsce" in row.index: m_ce = row["Miejsce"]
    else: return [''] * len(row)
    if m_ce == 1: return ['background-color: #d4a017; color: black; font-weight: bold'] * len(row)
    elif m_ce == 2: return ['background-color: #c0c0c0; color: black; font-weight: bold'] * len(row)
    elif m_ce == 3: return ['background-color: #cd7f32; color: black; font-weight: bold'] * len(row)
    elif m_ce == 8: return ['background-color: #f4cccc; color: black; font-weight: bold'] * len(row)
    return [''] * len(row)

# --- INICJALIZACJA STAŁEJ BAZY STREAMLIT ---
def load_db():
    try:
        db_conn = st.connection("storage", type="dict")
        if "ttbz_data" in db_conn:
            return json.loads(db_conn["ttbz_data"])
    except Exception:
        pass
    
    if "local_db" not in st.session_state:
        st.session_state["local_db"] = {"editions": {}}
    return st.session_state["local_db"]

def save_db(data):
    st.session_state["local_db"] = data
    try:
        db_conn = st.connection("storage", type="dict")
        db_conn["ttbz_data"] = json.dumps(data, ensure_ascii=False, indent=4)
    except Exception:
        pass

db = load_db()

# --- SYSTEM LOGOWANIA ---
ADMIN_USER = "admin"
ADMIN_PASSWORD = "twoje_haslo123"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

with st.sidebar:
    st.header("🔐 Panel Administratora")
    if not st.session_state["logged_in"]:
        username = st.text_input("Użytkownik")
        password = st.text_input("Hasło", type="password")
        if st.button("Zaloguj się"):
            if username == ADMIN_USER and password == ADMIN_PASSWORD:
                st.session_state["logged_in"] = True
                st.success("Zalogowano pomyślnie!")
                st.rerun()
            else:
                st.error("Błędne dane logowania.")
    else:
        st.write("👋 Witaj, Administratorze!")
        if st.button("Wyloguj się"):
            st.session_state["logged_in"] = False
            st.rerun()

# --- WYBÓR I KONFIGURACJA EDYCJI ---
st.subheader("📁 Zarządzanie i Wybór Edycji")
editions_list = list(db["editions"].keys())

if st.session_state["logged_in"]:
    with st.expander("➕ UTWÓRZ / EDYTUJ EDYCJĘ", expanded=False):
        new_edition_name = st.text_input("Nazwa edycji (np. 'Edycja 1')")
        
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            pts_input = st.text_input("Punkty za miejsca 1-8 (po przecinku):", value="10, 7, 6, 5, 4, 3, 2, 1")
        with col_cfg2:
            jury_input = st.text_input("Jurorzy (po przecinku):", value="Juror 1, Juror 2, Juror 3, Juror 4")
            
        st.markdown("**👥 Lista 8 uczestników:**")
        new_participants = []
        cols_p = st.columns(4)
        for i in range(8):
            with cols_p[i % 4]:
                p_name = st.text_input(f"Uczestnik {i+1}", key=f"new_p_{i}")
                if p_name: new_participants.append(p_name.strip())
        
        if st.button("Zapisz Fonts", type="primary"):
            try:
                parsed_pts = [int(x.strip()) for x in pts_input.split(",")]
                parsed_jury = [x.strip() for x in jury_input.split(",") if x.strip()]
                if not new_edition_name or len(new_participants) < 8 or len(parsed_pts) != 8 or len(parsed_jury) == 0:
                    st.error("Wypełnij poprawnie wszystkie pola!")
                else:
                    db["editions"][new_edition_name] = {
                        "participants": new_participants,
                        "point_system": parsed_pts,
                        "jury_members": parsed_jury,
                        "episodes": {}
                    }
                    save_db(db)
                    st.success(f"Pomyślnie utworzono edycję: {new_edition_name}!")
                    st.rerun()
            except ValueError:
                st.error("Wpisz poprawne liczby rozdzielone przecinkami!")

if editions_list:
    selected_edition = st.selectbox("Wybierz edycję do wyświetlenia statystyk", editions_list)
else:
    st.info("Brak utworzonych edycji. Zaloguj się jako administrator, aby dodać pierwszą edycję.")
    selected_edition = None

# --- GŁÓWNA LOGIKA STRONY ---
if selected_edition:
    current_edition = db["editions"][selected_edition]
    participants = current_edition["participants"]
    episodes = current_edition["episodes"]
    
    valid_points = current_edition.get("point_system", [10, 7, 6, 5, 4, 3, 2, 1])
    jury_members = current_edition.get("jury_members", ["Juror 1", "Juror 2", "Juror 3", "Juror 4"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Wprowadzanie Odcinka", 
        "📅 Wyniki i Tabele Cząstkowe", 
        "📊 Klasyfikacja Generalna (Główna)", 
        "📈 Statystyki Szegółowe i Bonusy"
    ])

    # ==================== ZAKŁADKA 1: WPROWADZANIE DANYCH ====================
    with tab1:
        st.header(f"Zarządzanie odcinkami w: {selected_edition}")
        if st.session_state["logged_in"]:
            ep_num = st.number_input("Numer odcinka", min_value=1, step=1, value=len(episodes) + 1)
            
            jury_data = {p: {} for p in participants}
            bonus_votes = {}
            performance_data = {}
            
            st.markdown("### 🎪 1. Oceny, Postacie i Piosenki")
            
            # Dynamiczne nagłówki tabeli wejściowej
            cols_h = st.columns([2, 1.5, 1.5] + [1] * len(jury_members))
            with cols_h[0]: st.markdown("**Uczestnik**")
            with cols_h[1]: st.markdown("**Występuje jako (Postać)**")
            with cols_h[2]: st.markdown("**Piosenka**")
            for j_idx, j_name in enumerate(jury_members, start=3):
                with cols_h[j_idx]: st.markdown(f"**{j_name}**")
            
            for p in participants:
                cols = st.columns([2, 1.5, 1.5] + [1] * len(jury_members))
                with cols[0]: st.write(f"**{p}**")
                as_character = cols[1].text_input(f"Postać-{p}", value="", label_visibility="collapsed", key=f"char_{p}")
                song_title = cols[2].text_input(f"Piosenka-{p}", value="", label_visibility="collapsed", key=f"song_{p}")
                
                performance_data[p] = {"character": as_character, "song": song_title}
                
                jury_sum = 0
                for j_idx, j_name in enumerate(jury_members, start=3):
                    val = cols[j_idx].selectbox(f"{j_name}-{p}", valid_points, index=len(valid_points)-1, label_visibility="collapsed", key=f"j_{j_name}_{p}")
                    jury_data[p][j_name] = val
                    jury_sum += val
                jury_data[p]["jury_pts"] = jury_sum
            
            st.markdown("### 🎁 2. Głosowanie Uczestników (Kto komu daje +5 pkt)")
            cols_b = st.columns(4)
            for idx, p in enumerate(participants):
                with cols_b[idx % 4]:
                    recipients = [r for r in participants if r != p]
                    voted_to = st.selectbox(f"Głos od: {p}", recipients, key=f"v_from_{p}")
                    bonus_votes[p] = voted_to

            bonus_received = {p: 0 for p in participants}
            for giver, receiver in bonus_votes.items():
                bonus_received[receiver] += 5
                
            final_rows = []
            for p in participants:
                row = {
                    "name": p, 
                    "character": performance_data[p]["character"],
                    "song": performance_data[p]["song"],
                    "jury_pts": jury_data[p]["jury_pts"], 
                    "bonus": bonus_received[p],
                    "total_with_bonus": jury_data[p]["jury_pts"] + bonus_received[p], 
                    "voted_to": bonus_votes[p]
                }
                for j_name in jury_members: row[j_name] = jury_data[p][j_name]
                final_rows.append(row)
                
            df_calc = pd.DataFrame(final_rows)
            max_score = df_calc["total_with_bonus"].max()
            potential_winners = df_calc[df_calc["total_with_bonus"] == max_score]["name"].tolist()
            
            chosen_winner = None
            if len(potential_winners) > 1:
                st.warning("⚠️ Wykryto REMIS na 1. miejscu! Zdecyduj ręcznie, kto wygrywa ten odcinek:")
                chosen_winner = st.radio("Wybierz zwycięzcę odcinka:", potential_winners)
            
            if st.button("Zapisz odcinek", type="primary"):
                df_calc = df_calc.sort_values(by="total_with_bonus", ascending=False).reset_index(drop=True)
                if chosen_winner:
                    winner_idx = df_calc[df_calc["name"] == chosen_winner].index[0]
                    winner_row = df_calc.iloc[[winner_idx]]
                    df_calc = df_calc.drop(winner_idx).reset_index(drop=True)
                    df_calc = pd.concat([winner_row, df_calc], ignore_index=True)
                
                df_calc["rank"] = df_calc.index + 1
                db["editions"][selected_edition]["episodes"][str(ep_num)] = df_calc.to_dict(orient="records")
                save_db(db)
                st.success(f"Odcinek {ep_num} został zapisany w stałej bazie danych!")
                st.rerun()
        else:
            st.warning("⚠️ Tylko zalogowany administrator może wprowadzać lub edytować wyniki odcinków.")

    # Słownik wyciągający ostatnią postać uczestnika w danej edycji (do mniejszego druku)
    def get_last_characters(until_ep):
        last_chars = {p: "" for p in participants}
        for ep_id in sorted([int(k) for k in episodes.keys()]):
            if ep_id <= until_ep:
                for row in episodes[str(ep_id)]:
                    if row["name"] in last_chars and row.get("character"):
                        last_chars[row["name"]] = row["character"]
        return last_chars

    def get_general_up_to_episode(limit_ep):
        totals = {p: {"total": 0, "jury": 0, "bonus": 0} for p in participants}
        for ep_id, ep_data in episodes.items():
            if int(ep_id) <= limit_ep:
                for row in ep_data:
                    if row["name"] in totals:
                        totals[row["name"]]["total"] += row["total_with_bonus"]
                        totals[row["name"]]["jury"] += row["jury_pts"]
                        totals[row["name"]]["bonus"] += row["bonus"]
        return totals

    # ==================== ZAKŁADKA 2: HISTORIA I TABELE CZĄSTKOWE ====================
    with tab2:
        st.header(f"Archiwum wyników - {selected_edition}")
        if episodes:
            ep_list = sorted([int(k) for k in episodes.keys()])
            selected_ep = st.selectbox("Wybierz numer odcinka", ep_list, key="view_ep_select")
            
            if selected_ep:
                st.subheader(f"➔ Wyniki samego Odcinka {selected_ep}")
                ep_data = episodes[str(selected_ep)]
                df_ep = pd.DataFrame(ep_data)
                
                current_ep_jurors = [j for j in jury_members if j in df_ep.columns]
                # Dodane kolumny character i song
                display_cols = ["rank", "name", "character", "song"] + current_ep_jurors + ["jury_pts", "bonus", "total_with_bonus"]
                
                df_display = df_ep[display_cols].copy()
                df_display.columns = ["M-ce", "Uczestnik", "Występujący jako", "Piosenka"] + current_ep_jurors + ["Suma od Jury", "Bonusy (+5)", "Łącznie"]
                st.dataframe(df_display.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
                
                st.subheader(f"➔ Klasyfikacje generalne CZĄSTKOWE (Stan po Odcinku {selected_ep})")
                snap = get_general_up_to_episode(selected_ep)
                snap_chars = get_last_characters(selected_ep)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**1. Ogólna po tym odcinku**")
                    df_c1 = pd.DataFrame([{"Uczestnik": f"{k}\n({snap_chars[k]})" if snap_chars[k] else k, "Suma": v["total"]} for k, v in snap.items()]).sort_values(by="Suma", ascending=False).reset_index(drop=True)
                    df_c1.insert(0, "M-ce", df_c1.index + 1)
                    st.dataframe(df_c1.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
                with col2:
                    st.markdown("**2. Tylko Jurorzy po tym odcinku**")
                    df_c2 = pd.DataFrame([{"Uczestnik": f"{k}\n({snap_chars[k]})" if snap_chars[k] else k, "Suma": v["jury"]} for k, v in snap.items()]).sort_values(by="Suma", ascending=False).reset_index(drop=True)
                    df_c2.insert(0, "M-ce", df_c2.index + 1)
                    st.dataframe(df_c2.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
                with col3:
                    st.markdown("**3. Tylko Bonusy po tym odcinku**")
                    df_c3 = pd.DataFrame([{"Uczestnik": f"{k}\n({snap_chars[k]})" if snap_chars[k] else k, "Suma": v["bonus"]} for k, v in snap.items()]).sort_values(by="Suma", ascending=False).reset_index(drop=True)
                    df_c3.insert(0, "M-ce", df_c3.index + 1)
                    st.dataframe(df_c3.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("Brak zapisanych odcinków.")

    # ==================== ZAKŁADKA 3: GŁÓWNA KLASYFIKACJA ZBIORCZA ====================
    with tab3:
        st.header(f"Aktualna Główna Klasyfikacja Zbiorcza - {selected_edition}")
        if episodes:
            all_totals = get_general_up_to_episode(999)
            global_last_chars = get_last_characters(999)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.subheader("📊 1. Główna Tabela OGÓLNA")
                # Formatowanie tekstu uczestnika z postacią pod spodem (Streamlit obsługuje znaki nowej linii w tabelach)
                df_m1 = pd.DataFrame([{"Uczestnik": f"{k}\n({global_last_chars[k]})" if global_last_chars[k] else k, "Punkty Łącznie": v["total"]} for k, v in all_totals.items()]).sort_values(by="Punkty Łącznie", ascending=False).reset_index(drop=True)
                df_m1.insert(0, "M-ce", df_m1.index + 1)
                st.dataframe(df_m1.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
            with c2:
                st.subheader("⚖️ 2. Ranking Samych JURORÓW")
                df_m2 = pd.DataFrame([{"Uczestnik": f"{k}\n({global_last_chars[k]})" if global_last_chars[k] else k, "Punkty z Ocen": v["jury"]} for k, v in all_totals.items()]).sort_values(by="Punkty z Ocen", ascending=False).reset_index(drop=True)
                df_m2.insert(0, "M-ce", df_m2.index + 1)
                st.dataframe(df_m2.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
            with c3:
                st.subheader("🎁 3. Ranking Samych BONUSÓW")
                df_m3 = pd.DataFrame([{"Uczestnik": f"{k}\n({global_last_chars[k]})" if global_last_chars[k] else k, "Punkty z Bonusów": v["bonus"]} for k, v in all_totals.items()]).sort_values(by="Punkty z Bonusów", ascending=False).reset_index(drop=True)
                df_m3.insert(0, "M-ce", df_m3.index + 1)
                st.dataframe(df_m3.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
                
            st.subheader("🎪 Klasyfikacje Uczestników u Poszczególnych Jurorów")
            j_totals = {p: {j: 0 for j in jury_members} for p in participants}
            for ep_data in episodes.values():
                for row in ep_data:
                    if row["name"] in j_totals:
                        for j_name in jury_members: j_totals[row["name"]][j_name] += row.get(j_name, 0)
            j_cols = st.columns(len(jury_members))
            for j_idx, j_name in enumerate(jury_members):
                with j_cols[j_idx]:
                    st.markdown(f"**Ranking: {j_name}**")
                    df_j_single = pd.DataFrame([{"Uczestnik": f"{k}\n({global_last_chars[k]})" if global_last_chars[k] else k, "Suma pkt": v[j_name]} for k, v in j_totals.items()]).sort_values(by="Suma pkt", ascending=False).reset_index(drop=True)
                    df_j_single.insert(0, "Miejsce", df_j_single.index + 1)
                    st.dataframe(df_j_single.style.apply(highlight_ranks, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("Brak danych.")

    # ==================== ZAKŁADKA 4: STATYSTYKI I MATRYCA BONUSÓW ====================
    with tab4:
        st.header(f"Statystyki ocen, miejsc oraz przepływu bonusów - {selected_edition}")
        if episodes:
            stats = {p: {
                "points": {pt: 0 for pt in valid_points}, "ranks": {r: 0 for r in range(1, 9)},
                "bonus_given": {r: 0 for r in participants if r != p}
            } for p in participants}
            for ep_data in episodes.values():
                for row in ep_data:
                    p_name = row["name"]
                    if p_name in stats:
                        for j_name in jury_members:
                            val = row.get(j_name)
                            if val in stats[p_name]["points"]: stats[p_name]["points"][val] += 1
                        stats[p_name]["ranks"][row["rank"]] += 1
                        if "voted_to" in row and row["voted_to"] in stats[p_name]["bonus_given"]:
                            stats[p_name]["bonus_given"][row["voted_to"]] += 1
            
            st.subheader("🔢 Zliczanie pojedynczych ocen od sędziów:")
            rows_p = []
            for p, data in stats.items():
                p_row = {"Uczestnik": p}
                for pt in sorted(valid_points, reverse=True): p_row[f"Noty '{pt}'"] = data["points"].get(pt, 0)
                rows_p.append(p_row)
            st.dataframe(pd.DataFrame(rows_p).set_index("Uczestnik"), use_container_width=True)
            
            st.subheader("🏁 Zliczanie zajętych miejsc w odcinkach:")
            rows_r = [{"Uczestnik": p, **{f"{k}. m-ce": v for k, v in data["ranks"].items()}} for p, data in stats.items()]
            st.dataframe(pd.DataFrame(rows_r).set_index("Uczestnik"), use_container_width=True)
            
            st.subheader("🤝 Matryca Relacji: Kto komu ile razy przyznał bonusowe +5 punktów?")
            matrix_data = {}
            for giver in participants:
                matrix_data[giver] = {}
                for receiver in participants:
                    if giver == receiver: matrix_data[giver][receiver] = "-"
                    else: matrix_data[giver][receiver] = f"{stats[giver]['bonus_given'].get(receiver, 0)}x"
            st.dataframe(pd.DataFrame.from_dict(matrix_data, orient='index'), use_container_width=True)