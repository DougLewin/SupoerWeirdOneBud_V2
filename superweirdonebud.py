import streamlit as st
import pandas as pd
import numpy as np
import datetime
import boto3
import io

st.set_page_config(page_title="Rottnest Island Conditions Tracker", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
body {background:#0e1117;}
.block-container {
  max-width:100% !important;          /* allow full fluid width */
  width:100%;
  margin:0 auto 2.5rem;
  padding:clamp(0.75rem,1.2vw,1.5rem) clamp(1rem,2vw,2.25rem) 3rem clamp(1rem,2vw,2.25rem);
  border:2px solid #2e6f75;
  border-radius:18px;
  box-shadow:0 4px 18px -4px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.04) inset;
  background:linear-gradient(145deg,#162127 0%,#121b20 60%,#10181c 100%);
  position:relative;
  box-sizing:border-box;
}

/* Responsive padding tweaks */
@media (max-width:1200px){
  .block-container {padding:1rem 1.25rem 2.25rem 1.25rem;}
}
@media (max-width:900px){
  .block-container {padding:0.85rem 1rem 2rem 1rem;}
  .create-float {top:0.6rem; right:1rem;}
}
@media (max-width:700px){
  .create-float .stButton>button {padding:.6rem 1rem; font-size:1rem;}
}

/* Convert summary header row to wrap on narrow screens */
.summary-row, .summary-header {
  display:flex;
  flex-wrap:wrap;
  gap:0.35rem;
  align-items:stretch;
}
.summary-header > div, .summary-row > div {
  flex:1 1 clamp(120px,16%,260px);
  min-width:120px;
}

/* Commentary column grows more */
.summary-row .commentary, .summary-header .commentary {
  flex:2 1 clamp(200px,32%,600px);
}

/* Details button cell */
.summary-row .actions, .summary-header .actions {
  flex:0 0 auto;
}

/* Create button container uses flex instead of absolute if too narrow */
@media (max-width:640px){
  .create-float {
    position:static;
    margin-bottom:0.75rem;
    display:flex;
    justify-content:flex-end;
  }
}

/* Existing styles retained below */
h1, .stMarkdown h1 {margin-top:0.2rem;}
.create-wrapper .stButton>button {width:100%; background:#0f3d3d; border:2px solid #2e6f75; color:#2e6f75; font-weight:600; font-size:1.05rem; padding:.75rem 1.4rem; border-radius:10px; letter-spacing:.5px;}
.create-wrapper .stButton>button:hover {background:#145252; color:#fff; border-color:#2e8f95;}
.create-float {position:absolute; top:1.1rem; right:2rem; z-index:20;}
.create-float .stButton>button {background:#0f3d3d; border:3px solid #2e6f75; color:#2eecb5; font-size:1.25rem; font-weight:700; padding:1rem 2.2rem; border-radius:14px; box-shadow:0 0 0 2px #0a2426 inset;}
.create-float .stButton>button:hover {background:#145252; border-color:#33a9b3; color:#ffffff; transform:translateY(-2px);}
input.new-break-input {autocomplete:off !important;}
.final-score-box {background:linear-gradient(135deg,#143b3f 0%,#0f2b30 60%); border:2px solid #2e6f75; padding:0.9rem 1.1rem; border-radius:14px; box-shadow:0 0 0 1px #1a474d, 0 4px 10px -2px rgba(0,0,0,0.55); font-size:0.95rem;}
.final-score-box h4{margin:0 0 .4rem 0; color:#2eecb5;}
.final-score-val{font-weight:700; color:#fff; font-size:1.05rem;}
.final-score-label{color:#7fc9c5; font-size:.75rem; letter-spacing:.07em;}
</style>
""", unsafe_allow_html=True)

# S3 Configuration
S3_BUCKET = "superweirdonebud"
S3_KEY = "Rotto_Tracker.csv"

# Initialize S3 client
try:
    # Try with environment variables first (for production deployment)
    s3 = boto3.client('s3', region_name='ap-southeast-2')
except:
    try:
        # Fallback to local profile for development
        s3 = boto3.Session(profile_name='doug-personal').client('s3', region_name='ap-southeast-2')
    except Exception as e:
        st.error(f"Failed to connect to AWS S3: {str(e)}")
        st.error("Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are set")
        st.stop()

COLUMNS = ["Date","Time","Break","Zone","TOTAL SCORE",
           "Surfline Primary Swell Size (m)","Seabreeze Swell (m)",
           "Swell Period (s)","Swell Direction","Suitable Swell?","Swell Score","Final Swell Score","Swell Comments",
           "Wind Bearing","Wind Speed (kn)","Suitable Wind?","Wind Score","Wind Final Score","Wind Comments",
           "Tide Reading (m)","Tide Direction","Tide Suitable?","Tide Score","Tide Final Score","Tide Comments","Full Commentary"]

UNIT_LABELS = {
    "Surfline Primary Swell Size (m)": "Surfline Swell (m)",
    "Seabreeze Swell (m)": "Seabreeze Swell (m)",
    "Swell Period (s)": "Swell Period (s)",
    "Wind Speed (kn)": "Wind Speed (kn)",
    "Tide Reading (m)": "Tide Reading (m)"
}

def load_df():
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return pd.read_csv(obj['Body'])
    except Exception as e:
        st.error(f"⚠️ Failed to load data from S3: {str(e)}")
        st.error(f"Bucket: {S3_BUCKET}, Key: {S3_KEY}")
        if "InvalidAccessKeyId" in str(e) or "SignatureDoesNotMatch" in str(e):
            st.error("❌ AWS credentials are invalid or expired. Please update your credentials.")
            st.info("Check the AWS_CREDENTIALS_SETUP.md file for instructions.")
        elif "NoSuchKey" in str(e):
            st.warning("📄 The file doesn't exist in S3 yet. Create your first record!")
        return pd.DataFrame(columns=COLUMNS)

def save_df(df):
    try:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=csv_buffer.getvalue())
        st.success("✅ Data saved to S3 successfully!")
    except Exception as e:
        st.error(f"❌ Failed to save data to S3: {str(e)}")
        if "InvalidAccessKeyId" in str(e) or "SignatureDoesNotMatch" in str(e):
            st.error("AWS credentials are invalid or expired. Data was NOT saved!")
        raise e  # Re-raise so the caller knows the save failed

def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    # add missing
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    # drop extras & reorder
    return df[[c for c in COLUMNS]]

def safe_int(v, default=0):
    try:
        if v is None: return default
        if isinstance(v, str):
            v = v.strip()
            if v == "": return default
        fv = float(v)
        if np.isnan(fv): return default
        return int(fv)
    except:
        return default

def safe_float(v, default=0.0):
    try:
        if v is None: return default
        if isinstance(v, str):
            v = v.strip()
            if v == "": return default
        fv = float(v)
        if np.isnan(fv): return default
        return fv
    except:
        return default

def has_any_comment(d: dict) -> bool:
    return any([
        (d.get("Swell Comments","") or "").strip(),
        (d.get("Wind Comments","") or "").strip(),
        (d.get("Tide Comments","") or "").strip()
    ])

def is_valid_password(p: str) -> bool:
    return (p or "").strip().lower() in {"utfs","utsf"}  # accept UTFS and common transposition UTSF

surf_df = ensure_columns(load_df())
if "Zone" not in surf_df.columns:
    surf_df["Zone"] = ""
surf_df = ensure_columns(surf_df)

# Normalize column names and migrate legacy column names
surf_df.columns = surf_df.columns.str.strip()
legacy_map = {
    "Swell Size": "Surfline Primary Swell Size (m)",
    "Surfline Primary Swell Size": "Surfline Primary Swell Size (m)",
    "Seabreeze Swell Size": "Seabreeze Swell (m)",
    "Swell Period": "Swell Period (s)",
    "Wind Speed": "Wind Speed (kn)",
    "Tide Reading": "Tide Reading (m)",
    "Swell Direction ": "Swell Direction",
    "Wind Bearing ": "Wind Bearing"
}
for old, new in legacy_map.items():
    if old in surf_df.columns and new not in surf_df.columns:
        surf_df.rename(columns={old: new}, inplace=True)
surf_df = ensure_columns(surf_df)

# Enforce data types and normalize values
if "Swell Direction" in surf_df.columns:
    surf_df["Swell Direction"] = pd.to_numeric(surf_df["Swell Direction"], errors="coerce").round(0)

if "Wind Bearing" in surf_df.columns:
    surf_df["Wind Bearing"] = surf_df["Wind Bearing"].fillna("").astype(str).replace({"nan": ""})

if "TOTAL SCORE" in surf_df.columns:
    surf_df["TOTAL SCORE"] = pd.to_numeric(surf_df["TOTAL SCORE"], errors="coerce").round(1)

if "Tide Direction" in surf_df.columns:
    surf_df["Tide Direction"] = (
        surf_df["Tide Direction"]
        .astype(str)
        .str.strip()
        .replace({"Dropping": "Falling"})
    )

st.title("Super Weird One Bud")

# Ensure auth + inline prompt state
if 'edit_auth' not in st.session_state: st.session_state.edit_auth=False
if 'pw_prompt_for' not in st.session_state: st.session_state.pw_prompt_for=None

if 'creating' not in st.session_state: st.session_state.creating=False
if 'c_page' not in st.session_state: st.session_state.c_page=0
if 'draft' not in st.session_state: st.session_state.draft={}
if 'editing' not in st.session_state: st.session_state.editing=False
if 'edit_index' not in st.session_state: st.session_state.edit_index=None
if 'confirm_delete' not in st.session_state: st.session_state.confirm_delete=None
COMPASS_DIRECTIONS = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]

# LIST PAGE
if not st.session_state.creating:
    # Track break selection change to reset pagination
    if 'summary_page' not in st.session_state: st.session_state.summary_page = 0
    if 'prev_break_sel' not in st.session_state: st.session_state.prev_break_sel = None
    if 'prev_zone_sel' not in st.session_state: st.session_state.prev_zone_sel = None

    with st.container():
        st.markdown('<div class="create-float">', unsafe_allow_html=True)
        if st.button("Create New", key="create_new_btn"):
            st.session_state.creating=True; st.session_state.c_page=0; st.session_state.draft={}; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    zones = ["All"] + sorted([z for z in surf_df["Zone"].dropna().unique() if str(z).strip()])
    zone_sel = st.selectbox("Zone", zones)
    if st.session_state.prev_zone_sel != zone_sel:
        st.session_state.summary_page = 0
        st.session_state.prev_zone_sel = zone_sel
        st.session_state.prev_break_sel = None  # reset break when zone changes

    zone_view = surf_df if zone_sel == "All" else surf_df[surf_df["Zone"] == zone_sel]

    breaks = ["All"] + sorted([b for b in zone_view["Break"].dropna().unique()])
    sel = st.selectbox("Break", breaks)
    if st.session_state.prev_break_sel != sel:
        st.session_state.summary_page = 0
        st.session_state.prev_break_sel = sel

    # INIT sort state (default now TOTAL SCORE to align with 'top scores')
    if 'sort_col' not in st.session_state: st.session_state.sort_col = "TOTAL SCORE"
    if 'sort_desc' not in st.session_state: st.session_state.sort_desc = True

    view = zone_view if sel=="All" else zone_view[zone_view["Break"]==sel]

    # APPLY sort
    sc, sd = st.session_state.sort_col, st.session_state.sort_desc
    if sc == "Date":
        view = view.assign(_d=pd.to_datetime(view["Date"], errors="coerce")).sort_values("_d", ascending=not sd).drop(columns="_d")
    else:
        # ensure numeric for TOTAL SCORE if sorting on it
        if sc == "TOTAL SCORE":
            view = view.assign(_score=pd.to_numeric(view["TOTAL SCORE"], errors="coerce")).sort_values("_score", ascending=not sd, kind="mergesort").drop(columns="_score")
        else:
            view = view.sort_values(sc, ascending=not sd, kind="mergesort")

    # Pagination (10 per page)
    PAGE_SIZE = 10
    total_rows = len(view)
    total_pages = (total_rows + PAGE_SIZE - 1) // PAGE_SIZE if total_rows else 1
    current_page = min(st.session_state.summary_page, max(total_pages-1,0))
    start = current_page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_view = view.iloc[start:end]

    cols_show = ["Date","Break","TOTAL SCORE","Surfline Primary Swell Size (m)","Seabreeze Swell (m)","Swell Direction","Wind Bearing","Full Commentary"]
    sortable = {"Date","Break","TOTAL SCORE","Surfline Primary Swell Size (m)","Seabreeze Swell (m)","Swell Direction"}
    if 'detail' not in st.session_state: st.session_state.detail=None

    st.subheader("Summary (Top scores paginated)")
    widths = [1,1,1,1.05,1.05,0.9,0.9,6,1]

    header_cols = st.columns(widths)
    for i,h in enumerate(cols_show):
        base_display = "Score" if h == "TOTAL SCORE" else h
        display_h = UNIT_LABELS.get(h, base_display)
        if h == "Surfline Primary Swell Size (m)": display_h = "Surfline\nSwell (m)"
        elif h == "Seabreeze Swell (m)": display_h = "Seabreeze\nSwell (m)"
        elif h == "Swell Direction": display_h = "Swell\nDir (°)"
        elif h == "Wind Bearing": display_h = "Wind\nDir"
        if h in sortable:
            arrow = "▼" if (st.session_state.sort_col==h and st.session_state.sort_desc) else ("▲" if st.session_state.sort_col==h else "")
            if header_cols[i].button(f"{display_h} {arrow}", key=f"sort_{h}"):
                if st.session_state.sort_col == h:
                    st.session_state.sort_desc = not st.session_state.sort_desc
                else:
                    st.session_state.sort_col = h
                    st.session_state.sort_desc = True
                st.session_state.summary_page = 0
                st.rerun()
        else:
            header_cols[i].markdown(f"*{display_h}*")
    header_cols[-1].markdown("*Details*")

    for idx,row in page_view.iterrows():
        row_cols = st.columns(widths)
        for i,c in enumerate(cols_show):
            val = row.get(c)
            if c == "Wind Bearing" and (pd.isna(val) or str(val).lower()=="nan"): val = ""
            if c == "Swell Direction" and pd.notna(val):
                try: val = int(float(val))
                except: pass
            if c == "TOTAL SCORE" and pd.notna(val):
                try: val = round(float(val),1)
                except: pass
            row_cols[i].write(val)
        if row_cols[-1].button("See details", key=f"d_{idx}"):
            st.session_state.detail=idx

    # Pagination controls
    if total_pages > 1:
        pc1, pc2, pc3, pc4 = st.columns([1,1,2,6])
        with pc1:
            if st.button("Prev", disabled=current_page==0):
                st.session_state.summary_page = current_page-1; st.rerun()
        with pc2:
            if st.button("Next", disabled=current_page >= total_pages-1):
                st.session_state.summary_page = current_page+1; st.rerun()
        with pc3:
            st.write(f"Page {current_page+1} / {total_pages} (rows {start+1}-{min(end,total_rows)} of {total_rows})")

    if st.session_state.detail is not None and st.session_state.detail in surf_df.index:
        r = surf_df.loc[st.session_state.detail]
        with st.expander(f"Details for record {st.session_state.detail}", expanded=True):
            idx = st.session_state.detail
            factor_map = {"Yes":1,"Ok":0.5,"No":0,"Too Big":0}
            key_fields = ["Surfline Primary Swell Size (m)","Seabreeze Swell (m)","Swell Period (s)","Swell Direction","Wind Speed (kn)","Wind Bearing","Tide Reading (m)","Tide Direction"]
            if not (st.session_state.editing and st.session_state.edit_index==idx):
                # DISPLAY MODE
                hdr_cols = st.columns([6,2,1])  # title | password (when needed) | edit button
                with hdr_cols[0]:
                    st.markdown("### Additional Details")
                with hdr_cols[2]:
                    if st.button("✏️ Edit", key=f"edit_{idx}"):
                        if st.session_state.edit_auth:
                            st.session_state.editing=True
                            st.session_state.edit_index=idx
                            st.session_state.edit_cache=r.to_dict()
                            st.rerun()
                        else:
                            st.session_state.pw_prompt_for=idx
                            st.rerun()
                with hdr_cols[1]:
                    if (not st.session_state.edit_auth) and st.session_state.pw_prompt_for==idx:
                        pw_val = st.text_input("Password", "", key=f"pw_inline_{idx}")
                        c1, c2 = st.columns([1,1])
                        with c1:
                            if st.button("Unlock", key=f"unlock_{idx}"):
                                if is_valid_password(pw_val):
                                    st.session_state.edit_auth=True
                                    st.session_state.editing=True
                                    st.session_state.edit_index=idx
                                    st.session_state.edit_cache=r.to_dict()
                                    st.session_state.pw_prompt_for=None
                                    st.success("Editing enabled")
                                    st.rerun()
                                else:
                                    st.warning("Incorrect password")
                                    # revert to read-only details
                                    st.session_state.pw_prompt_for=None
                                    st.session_state.editing=False
                                    st.session_state.edit_index=None
                                    st.rerun()
                        with c2:
                            if st.button("Cancel", key=f"pw_cancel_{idx}"):
                                st.session_state.pw_prompt_for=None
                                st.rerun()
                kvals = {k: r.get(k) for k in key_fields}
                top_cols = st.columns(3)
                for i,(k,v) in enumerate(kvals.items()):
                    label = UNIT_LABELS.get(k, k)
                    with top_cols[i % 3]: st.metric(label, v)
                st.markdown("---")
                for c in COLUMNS:
                    if c in key_fields: continue
                    label = UNIT_LABELS.get(c, c)
                    if c == "Full Commentary":
                        st.markdown("*Full Commentary*"); st.write(r.get(c))
                    else:
                        st.write(f"{label}: {r.get(c)}")
                if st.button("Close details"): st.session_state.detail=None; st.session_state.pw_prompt_for=None; st.rerun()
            else:
                # EDIT MODE
                ec = st.session_state.edit_cache
                st.markdown("### Edit Record")
                # Editable fields (exclude computed finals & TOTAL SCORE)
                edit_fields = [
                    "Date","Time","Break","Zone",
                    "Surfline Primary Swell Size (m)","Seabreeze Swell (m)","Swell Period (s)","Swell Direction","Suitable Swell?","Swell Score","Swell Comments",
                    "Wind Bearing","Wind Speed (kn)","Suitable Wind?","Wind Score","Wind Comments",
                    "Tide Reading (m)","Tide Direction","Tide Suitable?","Tide Score","Tide Comments"
                ]
                for f in edit_fields:
                    label = UNIT_LABELS.get(f, f)
                    if "Date"==f:
                        ec[f]=st.date_input(label, pd.to_datetime(ec.get(f)).date() if pd.notna(ec.get(f)) else datetime.date.today())
                    elif "Time"==f:
                        # try parse time
                        try:
                            tparts=str(ec.get(f,"08:00:00")).split(":"); ec[f]=st.time_input(label, datetime.time(int(tparts[0]),int(tparts[1])))
                        except: ec[f]=st.time_input(label, datetime.time(8,0))
                    elif f=="Wind Bearing":
                        idx_opt = COMPASS_DIRECTIONS.index(ec.get(f)) if ec.get(f) in COMPASS_DIRECTIONS else 0
                        ec[f]=st.selectbox(label, COMPASS_DIRECTIONS, index=idx_opt)
                    elif f=="Tide Direction":
                        # Updated Tide Direction options per spec
                        tide_opts = ["High","Low","Falling","Rising"]
                        cur_val = ec.get(f)
                        if cur_val not in tide_opts:  # map legacy 'Dropping'
                            if cur_val == "Dropping": cur_val = "Falling"
                        ec[f] = st.selectbox(label, tide_opts,
                                             index=tide_opts.index(cur_val) if cur_val in tide_opts else 0)
                    elif f=="Zone":
                        zones_exist = sorted([z for z in surf_df["Zone"].dropna().unique() if z])
                        z_opts = zones_exist + ["Add new..."]
                        cur_z = ec.get(f,"")
                        z_idx = z_opts.index(cur_z) if cur_z in z_opts else 0
                        z_sel = st.selectbox("Zone (existing or new)", z_opts, index=z_idx)
                        if z_sel == "Add new...":
                            ec[f] = st.text_input("New Zone Name","", key="edit_new_zone").strip()
                        else:
                            ec[f] = z_sel
                    elif "Suitable" in f:
                        opts=["Yes","No","Ok","Too Big"] if "Swell" in f else ["Yes","No","Ok"]
                        ec[f]=st.selectbox(label, opts, index=opts.index(ec.get(f)) if ec.get(f) in opts else 0)
                    elif "Comments" in f:
                        ec[f]=st.text_area(label, ("" if pd.isna(ec.get(f)) else ec.get(f)) or "")
                    elif f in ["Swell Period (s)","Swell Direction","Wind Speed (kn)"]:
                        ec[f]=st.number_input(label, value=safe_int(ec.get(f)), step=1, format="%d")
                    elif f in ["Swell Score","Wind Score","Tide Score"]:
                        ec[f]=st.number_input(label, min_value=0, max_value=10, value=safe_int(ec.get(f)), step=1, format="%d")
                    elif f in ["Surfline Primary Swell Size (m)","Seabreeze Swell (m)","Tide Reading (m)"]:
                        ec[f]=st.number_input(label, value=safe_float(ec.get(f)), step=0.1, format="%.1f")
                    else:
                        ec[f]=st.text_input(label, str(ec.get(f) or ""))
                # Recompute finals
                final_swell = round((ec.get("Swell Score") or 0)*factor_map.get(ec.get("Suitable Swell?"),0),1)
                final_wind  = round((ec.get("Wind Score")  or 0)*factor_map.get(ec.get("Suitable Wind?"),0),1)
                final_tide  = round((ec.get("Tide Score")  or 0)*factor_map.get(ec.get("Tide Suitable?"),0),1)
                total_score = (final_swell*final_wind*final_tide)/3 if all(v is not None for v in [final_swell,final_wind,final_tide]) else 0
                total_score = round(total_score,1)
                st.markdown(f"*Live Final Scores:* Swell {final_swell} | Wind {final_wind} | Tide {final_tide} | Total {total_score:.1f}")
                # Actions
                ac1,ac2,ac3,ac4 = st.columns(4)
                if ac1.button("Cancel Edit"):
                    st.session_state.editing=False; st.session_state.edit_index=None; st.session_state.confirm_delete=None; st.rerun()
                save_clicked = ac2.button("Save Changes")
                if save_clicked:
                    # Full commentary from component comments
                    full_comm = " ".join([ec.get("Swell Comments","") or "", ec.get("Wind Comments","") or "", ec.get("Tide Comments","") or ""]).strip()
                    if "Swell Direction" in ec and ec.get("Swell Direction") not in (None,""):
                        try: ec["Swell Direction"] = int(float(ec["Swell Direction"]))
                        except: pass
                    updates = {
                        "Date":ec.get("Date"),
                        "Time":ec.get("Time"),
                        "Break":ec.get("Break"),
                        "Zone":ec.get("Zone"),
                        "Surfline Primary Swell Size (m)":ec.get("Surfline Primary Swell Size (m)"),
                        "Seabreeze Swell (m)":ec.get("Seabreeze Swell (m)"),
                        "Swell Period (s)":ec.get("Swell Period (s)"),
                        "Swell Direction":ec.get("Swell Direction"),
                        "Suitable Swell?":ec.get("Suitable Swell?"),
                        "Swell Score":ec.get("Swell Score"),
                        "Final Swell Score":final_swell,
                        "Swell Comments":ec.get("Swell Comments"),
                        "Wind Bearing":ec.get("Wind Bearing"),
                        "Wind Speed (kn)":ec.get("Wind Speed (kn)"),
                        "Suitable Wind?":ec.get("Suitable Wind?"),
                        "Wind Score":ec.get("Wind Score"),
                        "Wind Final Score":final_wind,
                        "Wind Comments":ec.get("Wind Comments"),
                        "Tide Reading (m)":ec.get("Tide Reading (m)"),
                        "Tide Direction":ec.get("Tide Direction"),
                        "Tide Suitable?":ec.get("Tide Suitable?"),
                        "Tide Score":ec.get("Tide Score"),
                        "Tide Final Score":final_tide,
                        "Tide Comments":ec.get("Tide Comments"),
                        "TOTAL SCORE":total_score,
                        "Full Commentary":full_comm
                    }
                    for k,v in updates.items():
                        surf_df.at[idx,k]=v
                    surf_df = ensure_columns(surf_df)
                    save_df(surf_df)
                    st.session_state.editing=False; st.session_state.edit_index=None
                    st.success("Record updated")
                    st.rerun()
                # DELETE workflow
                if ac3.button("Delete Record", key=f"del_{idx}"):
                    st.session_state.confirm_delete = idx if st.session_state.confirm_delete != idx else None
                if st.session_state.confirm_delete == idx:
                    st.warning("Confirm delete? This cannot be undone.")
                    dc1,dc2 = st.columns(2)
                    if dc1.button("Yes, delete now", key=f"del_yes_{idx}"):
                        surf_df = surf_df.drop(index=idx).reset_index(drop=True)
                        surf_df = ensure_columns(surf_df)
                        save_df(surf_df)
                        st.session_state.detail=None
                        st.session_state.editing=False
                        st.session_state.edit_index=None
                        st.session_state.confirm_delete=None
                        st.success("Record deleted")
                        st.rerun()
                    if dc2.button("Cancel delete", key=f"del_no_{idx}"):
                        st.session_state.confirm_delete=None
                        st.rerun()
                if ac4.button("Close details"):
                    st.session_state.detail=None; st.session_state.editing=False; st.session_state.edit_index=None; st.session_state.confirm_delete=None; st.rerun()

# CREATE PAGE
else:
    st.markdown("### New Record")
    if st.button("Back to List"): st.session_state.creating=False; st.rerun()
    breaks_exist = sorted([b for b in surf_df["Break"].dropna().unique() if b])
    P1 = ["Zone","Break","Date","Time"]  # include Zone first
    SWELL = ["Surfline Primary Swell Size (m)","Seabreeze Swell (m)","Swell Period (s)","Swell Direction","Suitable Swell?","Swell Score","Swell Comments"]
    WIND  = ["Wind Bearing","Wind Speed (kn)","Suitable Wind?","Wind Score","Wind Comments"]
    TIDE  = ["Tide Reading (m)","Tide Direction","Tide Suitable?","Tide Score","Tide Comments"]
    PAGES = [("Session",P1),("Swell",SWELL),("Wind",WIND),("Tide",TIDE)]
    p = st.session_state.c_page
    st.markdown(f"*Page {p+1}/{len(PAGES)}: {PAGES[p][0]}*")
    factor_map = {"Yes":1,"Ok":0.5,"No":0,"Too Big":0}
    layout_cols = st.columns([2,1])
    with layout_cols[0]:
        whole_int = {"Swell Period (s)","Swell Direction","Wind Speed (kn)"}
        int_scores = {"Swell Score","Tide Score","Wind Score"}
        one_dp = {"Surfline Primary Swell Size (m)","Seabreeze Swell (m)","Wind Final Score","Tide Reading (m)","Tide Final Score","Final Swell Score"}
        
        for f in PAGES[p][1]:
            label = UNIT_LABELS.get(f, f)
            if f=="Zone":
                zones_exist = sorted([z for z in surf_df["Zone"].dropna().unique() if z])
                z_opts = zones_exist + ["Add new..."]
                prev_z = st.session_state.draft.get("Zone","")
                z_idx = z_opts.index(prev_z) if prev_z in z_opts else 0
                z_sel = st.selectbox("Zone (existing or new)", z_opts, index=z_idx)
                if z_sel == "Add new...":
                    new_zone = st.text_input("New Zone Name","", key="new_zone_name", placeholder="Enter new zone").strip()
                    st.session_state.draft["Zone"] = new_zone
                else:
                    st.session_state.draft["Zone"] = z_sel
            elif f=="Break":
                # (Break list can optionally be filtered by chosen zone)
                chosen_zone = st.session_state.draft.get("Zone","")
                zone_filtered_df = surf_df if not chosen_zone else surf_df[surf_df["Zone"]==chosen_zone]
                breaks_exist = sorted([b for b in zone_filtered_df["Break"].dropna().unique() if b])
                options = breaks_exist + ["Add new..."]
                prev_break = st.session_state.draft.get("Break","")
                idx = options.index(prev_break) if prev_break in options else 0
                sel = st.selectbox("Break (existing or new)", options, index=idx)
                if sel == "Add new...":
                    new_name = st.text_input("New Break Name","", key="new_break_name", placeholder="Enter new break").strip()
                    st.session_state.draft["Break"] = new_name
                else:
                    st.session_state.draft["Break"] = sel
            elif f=="Date":
                st.session_state.draft[f]=st.date_input(label, st.session_state.draft.get(f, datetime.date.today()))
            elif f=="Time":
                st.session_state.draft[f]=st.time_input(label, st.session_state.draft.get(f, datetime.time(8,0)))
            elif f=="Wind Bearing":
                existing = st.session_state.draft.get(f,"")
                idx_dir = COMPASS_DIRECTIONS.index(existing) if existing in COMPASS_DIRECTIONS else 0
                st.session_state.draft[f]=st.selectbox(label, COMPASS_DIRECTIONS, index=idx_dir)
            elif f=="Tide Direction":
                tide_opts = ["High","Low","Falling","Rising"]
                cur_val = st.session_state.draft.get(f)
                if cur_val == "Dropping":  # legacy value
                    cur_val = "Falling"
                st.session_state.draft[f] = st.selectbox(
                    label, tide_opts,
                    index=tide_opts.index(cur_val) if cur_val in tide_opts else 0
                )
            elif "Comments" in f:
                st.session_state.draft[f]=st.text_area(label, ("" if pd.isna(st.session_state.draft.get(f)) else st.session_state.draft.get(f,"")))
            elif "Suitable" in f:
                st.session_state.draft[f]=st.selectbox(
                    label, ["Yes","No","Ok","Too Big"] if "Swell" in f else ["Yes","No","Ok"],
                    index=["Yes","No","Ok","Too Big"].index(st.session_state.draft.get(f,"Yes"))
                        if st.session_state.draft.get(f,"Yes") in ["Yes","No","Ok","Too Big"] else 0
                )
            else:
                cur = st.session_state.draft.get(f)
                if f in int_scores:
                    st.session_state.draft[f]=st.number_input(label, min_value=0, max_value=10,
                                                              value=safe_int(cur), step=1, format="%d")
                elif f in whole_int:
                    st.session_state.draft[f]=st.number_input(label, value=safe_int(cur), step=1, format="%d")
                elif f in one_dp:
                    st.session_state.draft[f]=st.number_input(label, value=safe_float(cur), step=0.1, format="%.1f")
                else:
                    st.session_state.draft[f]=st.number_input(label, value=safe_float(cur), step=0.1)

    # compute finals AFTER inputs so they reflect latest changes
    d = st.session_state.draft
    fs = (d.get("Swell Score") or 0)*factor_map.get(d.get("Suitable Swell?"),0)
    fw = (d.get("Wind Score") or 0)*factor_map.get(d.get("Suitable Wind?"),0)
    ft = (d.get("Tide Score") or 0)*factor_map.get(d.get("Tide Suitable?"),0)
    d["Final Swell Score"] = round(fs,1); d["Wind Final Score"]=round(fw,1); d["Tide Final Score"]=round(ft,1)
    total_live = (fs*fw*ft)/3 if all(v is not None for v in [fs,fw,ft]) else 0
    total_live = round(total_live,1)

    if "Swell Direction" in d and d.get("Swell Direction") not in (None,""):
        try: d["Swell Direction"] = int(float(d["Swell Direction"]))
        except: pass

    with layout_cols[1]:
        st.markdown(f"""
<div class="final-score-box">
  <h4>FINAL SCORES</h4>
  <div><span class="final-score-label">SWELL</span><br><span class="final-score-val">{fs:.1f}</span></div>
  <div style="margin-top:.4rem;"><span class="final-score-label">WIND</span><br><span class="final-score-val">{fw:.1f}</span></div>
  <div style="margin-top:.4rem;"><span class="final-score-label">TIDE</span><br><span class="final-score-val">{ft:.1f}</span></div>
  <hr style="margin:.6rem 0;border:0;border-top:1px solid #255d63;">
  <div><span class="final-score-label">TOTAL (live)</span><br><span class="final-score-val">{total_live:.1f}</span></div>
</div>
""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    if c1.button("Cancel"): st.session_state.creating=False; st.session_state.draft={}; st.rerun()
    if p>0 and c2.button("Prev"): st.session_state.c_page-=1; st.rerun()
    
    if p < len(PAGES)-1:
        if c3.button("Next"):
            d = st.session_state.draft
            block_reason = None
            if p == 0:
                if not (d.get("Break","") or "").strip():
                    block_reason = "Please enter a Break before continuing."
            elif p == 1:
                sps = d.get("Surfline Primary Swell Size (m)") or 0
                sbs = d.get("Seabreeze Swell (m)") or 0
                if (sps is None or sps <= 0) and (sbs is None or sbs <= 0):
                    block_reason = "Enter at least one positive swell size (Surfline or Seabreeze)."
            elif p == 2:
                wb = d.get("Wind Bearing","")
                if wb not in COMPASS_DIRECTIONS:
                    block_reason = "Select a Wind Bearing direction."
            if block_reason:
                st.error(block_reason)
            else:
                st.session_state.c_page += 1
                st.rerun()
    if p == len(PAGES)-1 and c4.button("Submit"):
        d = st.session_state.draft
        comments_present = has_any_comment(d)
        missing = []
        if not (d.get("Break","") or "").strip(): missing.append("Break")
        sps = d.get("Surfline Primary Swell Size (m)") or 0
        sbs = d.get("Seabreeze Swell (m)") or 0
        if (sps is None or sps <= 0) and (sbs is None or sbs <= 0): missing.append("Surfline or Seabreeze Swell (>0)")
        wind_bearing = d.get("Wind Bearing")
        if wind_bearing not in COMPASS_DIRECTIONS: missing.append("Wind Bearing (direction)")
        if missing or not comments_present:
            msg = ""
            if missing:
                msg += f"Missing / invalid: {', '.join(missing)}. "
            if not comments_present:
                msg += "Enter at least one comment (Swell/Wind/Tide)."
            st.error(msg)
        else:
            # ...existing save logic...
            full_comm = " ".join([d.get("Swell Comments","") or "", d.get("Wind Comments","") or "", d.get("Tide Comments","") or ""]).strip()
            total_score = ((d.get("Final Swell Score",0) or 0) * (d.get("Wind Final Score",0) or 0) * (d.get("Tide Final Score",0) or 0)) / 3
            total_score = round(total_score,1)
            row = {"Date":d.get("Date"),
                   "Time":d.get("Time"),
                   "Break":d.get("Break"),
                   "Zone":d.get("Zone"),
                   "TOTAL SCORE":total_score,
                   "Full Commentary":full_comm,
                   "Wind Bearing": d.get("Wind Bearing") or ""}  # force include bearing
            for f in COLUMNS:
                if f not in row:
                    row[f]=d.get(f)
            new_row = {c: ("" if (c=="Wind Bearing" and (row.get(c) is None or str(row.get(c)).lower()=="nan")) else row.get(c)) for c in COLUMNS}
            surf_df = ensure_columns(surf_df)
            surf_df = pd.concat([surf_df, pd.DataFrame([new_row])], ignore_index=True)
            # normalize after append
            surf_df["Wind Bearing"] = surf_df["Wind Bearing"].fillna("").astype(str).replace({"nan":""})
            save_df(surf_df)
            st.success("Saved")
            st.session_state.creating=False; st.session_state.draft={}; st.rerun()
