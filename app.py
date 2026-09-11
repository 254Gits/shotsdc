import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import os

# --- App Configuration ---
st.set_page_config(page_title="WEKENI ZA CABBAGE GUYS", layout="centered")
st.title("SAFARICOM CHAPA DIMBA NYANZA REGION FINALS: Shot Map")

# --- Goal Dimensions & Config ---
left_post = 41.0
right_post = 48.65
crossbar_height = 2.47
CSV_FILE = "chapa_dimba_shot_data.csv"
HEADERS = ["Team", "Player Name", "Jersey No", "X", "Y", "Result"]

# --- Helper Function to Clean Data ---
def sanitize_dataframe(df):
    # Ensure all columns exist
    for col in HEADERS:
        if col not in df.columns:
            df[col] = ""
    
    # Fill missing values and convert types
    df = df[HEADERS].fillna("-")
    
    # Format Jersey Numbers as clean strings without decimal points (e.g., "10" instead of "10.0")
    def format_jersey(val):
        val_str = str(val).strip()
        if val_str.endswith(".0"):
            return val_str[:-2]
        return val_str if val_str != "nan" else "-"

    df["Jersey No"] = df["Jersey No"].apply(format_jersey)
    return df

# --- Initialize Session State DataFrame ---
if "shot_df" not in st.session_state:
    if os.path.exists(CSV_FILE):
        try:
            raw_df = pd.read_csv(CSV_FILE, on_bad_lines='skip')
            st.session_state.shot_df = sanitize_dataframe(raw_df)
        except Exception:
            st.session_state.shot_df = pd.DataFrame(columns=HEADERS)
    else:
        st.session_state.shot_df = pd.DataFrame(columns=HEADERS)

# --- Sidebar Inputs ---
st.sidebar.header("Record New Shot")

team_name = st.sidebar.selectbox("Select Team", ["AWENDO FOOTBALL ACADEMY", "INDOMITABLE LION", "SAMETA HIGHSCHOOL"])
player_name = st.sidebar.text_input("Player Name", value="Player")
player_pos = st.sidebar.text_input("Player Position", value = "position")
jersey_no = st.sidebar.text_input("Jersey Number", value="10")

x_val = st.sidebar.slider("Pitch Width (X)", min_value=37.0, max_value=52.65, value=44.8, step=0.05)
y_val = st.sidebar.slider("Goal Height (Y)", min_value=-0.5, max_value=3.5, value=1.2, step=0.05)

# Determine Goal vs Miss
is_goal = (left_post <= x_val <= right_post) and (0 <= y_val <= crossbar_height)
status = "Goal" if is_goal else "Miss"

# --- Save Action ---
if st.sidebar.button("Save Shot"):
    new_entry = pd.DataFrame([[team_name, player_name, jersey_no, x_val, y_val, status]], columns=HEADERS)
    
    # Append & sanitize session data
    st.session_state.shot_df = pd.concat([st.session_state.shot_df, new_entry], ignore_index=True)
    st.session_state.shot_df = sanitize_dataframe(st.session_state.shot_df)
    
    # Save clean dataset to disk
    st.session_state.shot_df.to_csv(CSV_FILE, index=False)
    
    st.sidebar.success(f"Recorded: [{team_name}] #{jersey_no} {player_name} {player_pos} - {status}")
    st.rerun()

# --- Reset Action ---
st.sidebar.markdown("---")
st.sidebar.header("Match Control")

if st.sidebar.button("Clear Data / Start Fresh"):
    st.session_state.shot_df = pd.DataFrame(columns=HEADERS)
    st.session_state.shot_df.to_csv(CSV_FILE, index=False)
    st.sidebar.warning("Cleared all shot records!")
    st.rerun()

# --- Dashboard Visualization Filter ---
st.subheader("Filter Goal Map")
view_option = st.radio("Display Shots For:", ["All Teams","AWENDO FOOTBALL ACADEMY", "INDOMITABLE LION", "SAMETA HIGHSCHOOL"], horizontal=True)

# Filter Data based on selection
if view_option == "All Teams":
    filtered_df = st.session_state.shot_df
else:
    filtered_df = st.session_state.shot_df[st.session_state.shot_df["Team"] == view_option]

# --- Plotting Goal Map ---
fig, ax = plt.subplots(figsize=(10, 6))

# Net mesh lines
y_curr = 0.3
while y_curr < crossbar_height:
    ax.plot([left_post, right_post], [y_curr, y_curr], color="#e0e0e0", linestyle="--", lw=0.6, zorder=1)
    y_curr += 0.3

x_curr = left_post + 0.5
while x_curr < right_post:
    ax.plot([x_curr, x_curr], [0, crossbar_height], color="#e0e0e0", linestyle="--", lw=0.6, zorder=1)
    x_curr += 0.5

# Main Goal Frame & Ground Line
ax.plot([left_post, right_post], [crossbar_height, crossbar_height], color="black", lw=4, zorder=3)
ax.plot([left_post, left_post], [0, crossbar_height], color="black", lw=4, zorder=3)
ax.plot([right_post, right_post], [0, crossbar_height], color="black", lw=4, zorder=3)
ax.axhline(0, color='darkgreen', lw=3, zorder=2)

# Plot saved shots with Jersey Number labels
for _, row in filtered_df.iterrows():
    try:
        x_pt, y_pt = float(row["X"]), float(row["Y"])
    except (ValueError, TypeError):
        continue
        
    color = "lime" if str(row["Result"]).strip() == "Goal" else "red"
    ax.plot(x_pt, y_pt, 'o', color=color, markersize=10, markeredgecolor="black", zorder=4)
    
    # Annotate clean Jersey Number
    j_num = str(row["Jersey No"]).strip()
    if j_num and j_num not in ["-", "nan", "None"]:
        ax.annotate(
            f"#{j_num}", 
            (x_pt, y_pt), 
            xytext=(5, 5), 
            textcoords="offset points", 
            fontsize=8, 
            fontweight='bold', 
            zorder=5
        )

# Plot current target crosshair
current_color = "lime" if is_goal else "red"
ax.plot(x_val, y_val, 'X', color=current_color, markersize=12, markeredgecolor="black", zorder=6, label="Current Selection")

# Axis & Display Settings
ax.set_xlim(37, 52.65)
ax.set_ylim(-0.5, 3.5)
ax.set_aspect('equal', adjustable='box')
ax.set_xlabel("Pitch Width (X)", labelpad=8)
ax.set_ylabel("Goal Height (Y)", labelpad=8)
ax.grid(True, linestyle=":", alpha=0.4)

st.pyplot(fig)

# --- Logs & Export ---
st.subheader("Match Shot History")
st.dataframe(st.session_state.shot_df, use_container_width=True)

st.download_button(
    label="Download Complete Match Data CSV",
    data=st.session_state.shot_df.to_csv(index=False),
    file_name="chapa_dimba_match_shots.csv",
    mime="text/csv"
)
