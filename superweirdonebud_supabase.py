import streamlit as st
import pandas as pd
import numpy as np
import datetime
from supabase import create_client, Client
from typing import Optional

st.set_page_config(page_title="Rottnest Island Conditions Tracker", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# SUPABASE INITIALIZATION
# ============================================================
@st.cache_resource
def init_supabase() -> Client:
    """Initialize and return Supabase client using secrets."""
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"❌ Failed to connect to Supabase: {str(e)}")
        st.error("**Configuration needed:** Add SUPABASE_URL and SUPABASE_KEY to .streamlit/secrets.toml")
        st.stop()

supabase: Client = init_supabase()

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'session' not in st.session_state:
    st.session_state.session = None
if 'creating' not in st.session_state:
    st.session_state.creating = False
if 'c_page' not in st.session_state:
    st.session_state.c_page = 0
if 'draft' not in st.session_state:
    st.session_state.draft = {}
if 'detail' not in st.session_state:
    st.session_state.detail = None
if 'editing' not in st.session_state:
    st.session_state.editing = False
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None
if 'edit_cache' not in st.session_state:
    st.session_state.edit_cache = {}
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = None
if 'filter_break' not in st.session_state:
    st.session_state.filter_break = "All"
if 'filter_zone' not in st.session_state:
    st.session_state.filter_zone = "All"
if 'sort_col' not in st.session_state:
    st.session_state.sort_col = "Date"
if 'sort_desc' not in st.session_state:
    st.session_state.sort_desc = True
if 'summary_page' not in st.session_state:
    st.session_state.summary_page = 0

# ============================================================
# AUTHENTICATION FUNCTIONS
# ============================================================
def sign_up(email: str, password: str, full_name: str = "") -> bool:
    """Sign up a new user."""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        
        if response.user:
            st.session_state.user = response.user
            st.session_state.session = response.session
            return True
        return False
    except Exception as e:
        st.error(f"Sign up failed: {str(e)}")
        return False

def sign_in(email: str, password: str) -> bool:
    """Sign in an existing user."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            st.session_state.user = response.user
            st.session_state.session = response.session
            return True
        return False
    except Exception as e:
        st.error(f"Sign in failed: {str(e)}")
        return False

def sign_out():
    """Sign out the current user."""
    try:
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.session = None
    except Exception as e:
        st.error(f"Sign out failed: {str(e)}")

# ============================================================
# DATABASE FUNCTIONS
# ============================================================
def load_user_records(publicity_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Load all records visible to the current user from Supabase.
    This includes:
    - User's own private records
    - All public records (from any user)
    - Community records (if user is a member)
    
    RLS policies handle the access control automatically.
    """
    if not st.session_state.user:
        return pd.DataFrame()
    
    try:
        # Query all records - RLS policies will filter based on user permissions
        query = supabase.table('records').select('*')
        
        if publicity_filter:
            query = query.eq('publicity', publicity_filter)
        
        response = query.order('date', desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Convert column names from snake_case to match original format
            column_mapping = {
                'surfline_primary_swell_size_m': 'Surfline Primary Swell Size (m)',
                'seabreeze_swell_m': 'Seabreeze Swell (m)',
                'swell_period_s': 'Swell Period (s)',
                'swell_direction': 'Swell Direction',
                'suitable_swell': 'Suitable Swell?',
                'swell_score': 'Swell Score',
                'final_swell_score': 'Final Swell Score',
                'swell_comments': 'Swell Comments',
                'wind_bearing': 'Wind Bearing',
                'wind_speed_kn': 'Wind Speed (kn)',
                'suitable_wind': 'Suitable Wind?',
                'wind_score': 'Wind Score',
                'wind_final_score': 'Wind Final Score',
                'wind_comments': 'Wind Comments',
                'tide_reading_m': 'Tide Reading (m)',
                'tide_direction': 'Tide Direction',
                'tide_suitable': 'Tide Suitable?',
                'tide_score': 'Tide Score',
                'tide_final_score': 'Tide Final Score',
                'tide_comments': 'Tide Comments',
                'full_commentary': 'Full Commentary',
                'total_score': 'TOTAL SCORE',
                'date': 'Date',
                'time': 'Time',
                'break': 'Break',
                'zone': 'Zone'
            }
            df = df.rename(columns=column_mapping)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to load records: {str(e)}")
        return pd.DataFrame()

def save_record(record_data: dict) -> bool:
    """Save a new surf session record to Supabase."""
    if not st.session_state.user:
        st.error("You must be logged in to save records")
        return False
    
    try:
        # Ensure user profile exists first
        user_id = st.session_state.user.id
        profile_check = supabase.table('profiles').select('id').eq('id', user_id).execute()
        
        if not profile_check.data:
            # Create profile if it doesn't exist
            supabase.table('profiles').insert({
                'id': user_id,
                'email': st.session_state.user.email,
                'full_name': st.session_state.user.user_metadata.get('full_name', '')
            }).execute()
        
        # Convert from display format to database snake_case format
        db_record = {
            'user_id': user_id,
            'publicity': record_data.get('publicity', 'Private'),
            'date': str(record_data.get('Date')),
            'time': str(record_data.get('Time')),
            'break': record_data.get('Break'),
            'zone': record_data.get('Zone'),
            'total_score': float(record_data.get('TOTAL SCORE', 0)),
            'surfline_primary_swell_size_m': float(record_data.get('Surfline Primary Swell Size (m)', 0)),
            'seabreeze_swell_m': float(record_data.get('Seabreeze Swell (m)', 0)),
            'swell_period_s': int(record_data.get('Swell Period (s)', 0)),
            'swell_direction': float(record_data.get('Swell Direction', 0)) if record_data.get('Swell Direction') else None,
            'suitable_swell': record_data.get('Suitable Swell?'),
            'swell_score': int(record_data.get('Swell Score', 0)),
            'final_swell_score': int(record_data.get('Final Swell Score', 0)),
            'swell_comments': record_data.get('Swell Comments'),
            'wind_bearing': record_data.get('Wind Bearing'),
            'wind_speed_kn': int(record_data.get('Wind Speed (kn)', 0)),
            'suitable_wind': record_data.get('Suitable Wind?'),
            'wind_score': int(record_data.get('Wind Score', 0)),
            'wind_final_score': int(record_data.get('Wind Final Score', 0)),
            'wind_comments': record_data.get('Wind Comments'),
            'tide_reading_m': float(record_data.get('Tide Reading (m)', 0)),
            'tide_direction': record_data.get('Tide Direction'),
            'tide_suitable': record_data.get('Tide Suitable?'),
            'tide_score': int(record_data.get('Tide Score', 0)),
            'tide_final_score': float(record_data.get('Tide Final Score', 0)),
            'tide_comments': record_data.get('Tide Comments'),
            'full_commentary': record_data.get('Full Commentary')
        }
        
        response = supabase.table('records').insert(db_record).execute()
        
        if response.data:
            return True
        return False
    except Exception as e:
        st.error(f"Failed to save record: {str(e)}")
        return False

def update_record(record_id: str, record_data: dict) -> bool:
    """Update an existing record in Supabase."""
    if not st.session_state.user:
        return False
    
    try:
        # Convert from display format to database format (similar to save_record)
        db_record = {
            'date': str(record_data.get('Date')),
            'time': str(record_data.get('Time')),
            'break': record_data.get('Break'),
            'zone': record_data.get('Zone'),
            'total_score': float(record_data.get('TOTAL SCORE', 0)),
            'surfline_primary_swell_size_m': float(record_data.get('Surfline Primary Swell Size (m)', 0)),
            'seabreeze_swell_m': float(record_data.get('Seabreeze Swell (m)', 0)),
            'swell_period_s': int(record_data.get('Swell Period (s)', 0)),
            'swell_direction': float(record_data.get('Swell Direction', 0)) if record_data.get('Swell Direction') else None,
            'suitable_swell': record_data.get('Suitable Swell?'),
            'swell_score': int(record_data.get('Swell Score', 0)),
            'final_swell_score': int(record_data.get('Final Swell Score', 0)),
            'swell_comments': record_data.get('Swell Comments'),
            'wind_bearing': record_data.get('Wind Bearing'),
            'wind_speed_kn': int(record_data.get('Wind Speed (kn)', 0)),
            'suitable_wind': record_data.get('Suitable Wind?'),
            'wind_score': int(record_data.get('Wind Score', 0)),
            'wind_final_score': int(record_data.get('Wind Final Score', 0)),
            'wind_comments': record_data.get('Wind Comments'),
            'tide_reading_m': float(record_data.get('Tide Reading (m)', 0)),
            'tide_direction': record_data.get('Tide Direction'),
            'tide_suitable': record_data.get('Tide Suitable?'),
            'tide_score': int(record_data.get('Tide Score', 0)),
            'tide_final_score': float(record_data.get('Tide Final Score', 0)),
            'tide_comments': record_data.get('Tide Comments'),
            'full_commentary': record_data.get('Full Commentary')
        }
        
        response = supabase.table('records').update(db_record).eq('id', record_id).eq('user_id', st.session_state.user.id).execute()
        
        return True if response.data else False
    except Exception as e:
        st.error(f"Failed to update record: {str(e)}")
        return False

def delete_record(record_id: str) -> bool:
    """Delete a record from Supabase."""
    if not st.session_state.user:
        return False
    
    try:
        response = supabase.table('records').delete().eq('id', record_id).eq('user_id', st.session_state.user.id).execute()
        return True
    except Exception as e:
        st.error(f"Failed to delete record: {str(e)}")
        return False

# ============================================================
# HELPER FUNCTIONS
# ============================================================
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

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
body {background:#0e1117;}
.block-container {
  max-width:100% !important;
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

.auth-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
  background: linear-gradient(145deg, #162127 0%, #121b20 100%);
  border: 2px solid #2e6f75;
  border-radius: 18px;
  box-shadow: 0 4px 18px -4px rgba(0,0,0,0.55);
}

.final-score-box {
  background:linear-gradient(135deg,#143b3f 0%,#0f2b30 60%); 
  border:2px solid #2e6f75; 
  padding:0.9rem 1.1rem; 
  border-radius:14px; 
  box-shadow:0 0 0 1px #1a474d, 0 4px 10px -2px rgba(0,0,0,0.55); 
  font-size:0.95rem;
}
.final-score-box h4{margin:0 0 .4rem 0; color:#2eecb5;}
.final-score-val{font-weight:700; color:#fff; font-size:1.05rem;}
.final-score-label{color:#7fc9c5; font-size:.75rem; letter-spacing:.07em;}

.stButton>button {
  width: 100%;
  background: #0f3d3d;
  border: 2px solid #2e6f75;
  color: #2eecb5;
  font-weight: 600;
  padding: 0.75rem;
  border-radius: 10px;
}

.stButton>button:hover {
  background: #145252;
  border-color: #33a9b3;
  color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# Constants
COMPASS_DIRECTIONS = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]

UNIT_LABELS = {
    "Surfline Primary Swell Size (m)": "Surfline Swell (m)",
    "Seabreeze Swell (m)": "Seabreeze Swell (m)",
    "Swell Period (s)": "Swell Period (s)",
    "Wind Speed (kn)": "Wind Speed (kn)",
    "Tide Reading (m)": "Tide Reading (m)"
}

# ============================================================
# AUTHENTICATION UI
# ============================================================
if not st.session_state.user:
    st.title("🏄 Super Weird One Bud")
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        st.subheader("Sign In")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", key="signin_btn"):
            if login_email and login_password:
                if sign_in(login_email, login_password):
                    st.success("✅ Signed in successfully!")
                    st.rerun()
            else:
                st.warning("Please enter both email and password")
    
    with tab2:
        st.subheader("Create Account")
        signup_name = st.text_input("Full Name (optional)", key="signup_name")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
        
        if st.button("Sign Up", key="signup_btn"):
            if signup_email and signup_password:
                if signup_password == signup_password_confirm:
                    if len(signup_password) >= 6:
                        if sign_up(signup_email, signup_password, signup_name):
                            st.success("✅ Account created! Please check your email to verify your account.")
                            st.info("After verification, you can sign in.")
                    else:
                        st.warning("Password must be at least 6 characters long")
                else:
                    st.warning("Passwords do not match")
            else:
                st.warning("Please enter email and password")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================
# MAIN APPLICATION (Only visible when logged in)
# ============================================================

# User info and logout button in sidebar
with st.sidebar:
    st.write(f"👤 **{st.session_state.user.email}**")
    if st.button("Sign Out"):
        sign_out()
        st.rerun()

st.title("🏄 Rottnest Island Conditions Tracker")

# Load user records (needed for both views and for populating dropdowns in create)
records_df = load_user_records()

# SUMMARY / LIST VIEW
if not st.session_state.creating:
    # Create button (floating style will be applied via CSS)
    st.markdown('<div class="create-float">', unsafe_allow_html=True)
    if st.button("➕ Create New Session", key="create_new"):
        st.session_state.creating = True
        st.session_state.c_page = 0
        st.session_state.draft = {}
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("## Your Sessions")
    
    if records_df.empty:
        st.info("No sessions recorded yet. Click 'Create New Session' to add your first one!")
    else:
        # Filters
        filter_cols = st.columns(3)
        
        # Break filter
        all_breaks = sorted([b for b in records_df["Break"].dropna().unique() if str(b).strip()])
        break_options = ["All"] + all_breaks
        with filter_cols[0]:
            st.session_state.filter_break = st.selectbox(
                "Filter by Break", 
                break_options, 
                index=break_options.index(st.session_state.filter_break) if st.session_state.filter_break in break_options else 0
            )
        
        # Zone filter
        all_zones = sorted([z for z in records_df["Zone"].dropna().unique() if str(z).strip()])
        zone_options = ["All"] + all_zones
        with filter_cols[1]:
            st.session_state.filter_zone = st.selectbox(
                "Filter by Zone", 
                zone_options, 
                index=zone_options.index(st.session_state.filter_zone) if st.session_state.filter_zone in zone_options else 0
            )
        
        # Apply filters
        surf_df = records_df.copy()
        if st.session_state.filter_break != "All":
            surf_df = surf_df[surf_df["Break"] == st.session_state.filter_break]
        if st.session_state.filter_zone != "All":
            surf_df = surf_df[surf_df["Zone"] == st.session_state.filter_zone]
        
        if surf_df.empty:
            st.info("No records match the current filters.")
        else:
            # Sort
            if st.session_state.sort_col in surf_df.columns:
                surf_df = surf_df.sort_values(by=st.session_state.sort_col, ascending=not st.session_state.sort_desc)
            
            # Pagination
            rows_per_page = 20
            total_rows = len(surf_df)
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page
            current_page = min(st.session_state.summary_page, total_pages - 1) if total_pages > 0 else 0
            start = current_page * rows_per_page
            end = start + rows_per_page
            page_view = surf_df.iloc[start:end]
            
            # Summary table header
            cols_show = ["Date", "Break", "Zone", "TOTAL SCORE", "Visibility", "Full Commentary"]
            widths = [1, 1.5, 1, 1, 0.8, 2, 0.8]
            sortable = ["Date", "Break", "Zone", "TOTAL SCORE"]
            
            st.markdown('<div class="summary-header">', unsafe_allow_html=True)
            header_cols = st.columns(widths)
            for i, h in enumerate(cols_show):
                display_h = h
                if h in sortable:
                    arrow = "▼" if (st.session_state.sort_col == h and st.session_state.sort_desc) else ("▲" if st.session_state.sort_col == h else "")
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
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display rows
            for idx, row in page_view.iterrows():
                st.markdown('<div class="summary-row">', unsafe_allow_html=True)
                row_cols = st.columns(widths)
                for i, c in enumerate(cols_show):
                    val = row.get(c)
                    if c == "TOTAL SCORE" and pd.notna(val):
                        try:
                            val = round(float(val), 1)
                        except:
                            pass
                    elif c == "Visibility":
                        # Show publicity with emoji
                        publicity = row.get('publicity', 'Private')
                        is_owner = row.get('user_id') == st.session_state.user.id
                        if publicity == 'Public':
                            val = "🌍 Public" + (" (yours)" if is_owner else "")
                        elif publicity == 'Community':
                            val = "👥 Community" + (" (yours)" if is_owner else "")
                        else:
                            val = "🔒 Private"
                    elif c == "Full Commentary":
                        # Truncate long commentary
                        val_str = str(val) if pd.notna(val) else ""
                        if len(val_str) > 60:
                            val = val_str[:60] + "..."
                        else:
                            val = val_str
                    row_cols[i].write(val)
                
                # Store the record ID for details view
                record_id = row.get('id')
                if row_cols[-1].button("See details", key=f"d_{idx}"):
                    st.session_state.detail = record_id
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Pagination controls
            if total_pages > 1:
                pc1, pc2, pc3 = st.columns([1, 1, 4])
                with pc1:
                    if st.button("← Prev", disabled=current_page == 0):
                        st.session_state.summary_page = current_page - 1
                        st.rerun()
                with pc2:
                    if st.button("Next →", disabled=current_page >= total_pages - 1):
                        st.session_state.summary_page = current_page + 1
                        st.rerun()
                with pc3:
                    st.write(f"Page {current_page + 1} / {total_pages} (rows {start + 1}-{min(end, total_rows)} of {total_rows})")
            
            # DETAILS VIEW
            if st.session_state.detail is not None:
                # Find the record in the original dataframe
                detail_record = records_df[records_df['id'] == st.session_state.detail]
                
                if not detail_record.empty:
                    r = detail_record.iloc[0]
                    record_id = r['id']
                    is_owner = r.get('user_id') == st.session_state.user.id
                    publicity = r.get('publicity', 'Private')
                    
                    with st.expander(f"📋 Details for {r.get('Break', 'Record')}", expanded=True):
                        # Show ownership and visibility status
                        if publicity == 'Public':
                            vis_badge = "🌍 Public Record"
                        elif publicity == 'Community':
                            vis_badge = "👥 Community Record"
                        else:
                            vis_badge = "🔒 Private Record"
                        
                        if not is_owner:
                            st.info(f"{vis_badge} - Shared by another user (view only)")
                        else:
                            st.info(f"{vis_badge} - Your record")
                        
                        factor_map = {"Yes": 1, "Ok": 0.5, "No": 0, "Too Big": 0}
                        key_fields = [
                            "Surfline Primary Swell Size (m)", "Seabreeze Swell (m)", 
                            "Swell Period (s)", "Swell Direction", "Wind Speed (kn)", 
                            "Wind Bearing", "Tide Reading (m)", "Tide Direction"
                        ]
                        
                        if not (st.session_state.editing and st.session_state.edit_index == record_id):
                            # READ-ONLY DISPLAY MODE
                            if is_owner:
                                hdr_cols = st.columns([6, 1])
                                with hdr_cols[0]:
                                    st.markdown("### Session Details")
                                with hdr_cols[1]:
                                    if st.button("✏️ Edit", key=f"edit_{record_id}"):
                                        st.session_state.editing = True
                                        st.session_state.edit_index = record_id
                                        st.session_state.edit_cache = r.to_dict()
                                        st.rerun()
                            else:
                                st.markdown("### Session Details")
                            
                            # Key metrics at top
                            kvals = {k: r.get(k) for k in key_fields if k in r}
                            top_cols = st.columns(4)
                            for i, (k, v) in enumerate(kvals.items()):
                                label = UNIT_LABELS.get(k, k)
                                with top_cols[i % 4]:
                                    st.metric(label, v if pd.notna(v) else "N/A")
                            
                            st.markdown("---")
                            
                            # All other fields
                            detail_cols = st.columns(2)
                            all_fields = [
                                "Date", "Time", "Break", "Zone",
                                "Suitable Swell?", "Swell Score", "Final Swell Score", "Swell Comments",
                                "Suitable Wind?", "Wind Score", "Wind Final Score", "Wind Comments",
                                "Tide Suitable?", "Tide Score", "Tide Final Score", "Tide Comments",
                                "TOTAL SCORE"
                            ]
                            
                            for i, c in enumerate(all_fields):
                                if c in key_fields:
                                    continue
                                label = UNIT_LABELS.get(c, c)
                                val = r.get(c)
                                if c == "Full Commentary":
                                    with detail_cols[0]:
                                        st.markdown(f"**{label}:**")
                                        st.write(val if pd.notna(val) else "N/A")
                                else:
                                    with detail_cols[i % 2]:
                                        if "Comments" in c:
                                            st.markdown(f"**{label}:**")
                                            st.write(val if pd.notna(val) else "N/A")
                                        else:
                                            st.write(f"**{label}:** {val if pd.notna(val) else 'N/A'}")
                            
                            # Full Commentary
                            st.markdown("---")
                            st.markdown("**Full Commentary:**")
                            st.write(r.get("Full Commentary", "N/A"))
                            
                            if st.button("Close details"):
                                st.session_state.detail = None
                                st.rerun()
                        
                        else:
                            # EDIT MODE
                            ec = st.session_state.edit_cache
                            st.markdown("### ✏️ Edit Record")
                            
                            # Editable fields (exclude computed finals & TOTAL SCORE initially)
                            edit_fields = [
                                "Date", "Time", "Break", "Zone",
                                "Surfline Primary Swell Size (m)", "Seabreeze Swell (m)", "Swell Period (s)", 
                                "Swell Direction", "Suitable Swell?", "Swell Score", "Swell Comments",
                                "Wind Bearing", "Wind Speed (kn)", "Suitable Wind?", "Wind Score", "Wind Comments",
                                "Tide Reading (m)", "Tide Direction", "Tide Suitable?", "Tide Score", "Tide Comments"
                            ]
                            
                            # Display editable fields
                            for f in edit_fields:
                                label = UNIT_LABELS.get(f, f)
                                
                                if f == "Date":
                                    try:
                                        date_val = pd.to_datetime(ec.get(f)).date() if pd.notna(ec.get(f)) else datetime.date.today()
                                    except:
                                        date_val = datetime.date.today()
                                    ec[f] = st.date_input(label, date_val, key=f"edit_{f}")
                                
                                elif f == "Time":
                                    try:
                                        time_str = str(ec.get(f, "08:00:00"))
                                        if isinstance(ec.get(f), datetime.time):
                                            time_val = ec.get(f)
                                        else:
                                            tparts = time_str.split(":")
                                            time_val = datetime.time(int(tparts[0]), int(tparts[1]))
                                    except:
                                        time_val = datetime.time(8, 0)
                                    ec[f] = st.time_input(label, time_val, key=f"edit_{f}")
                                
                                elif f == "Wind Bearing":
                                    idx_opt = COMPASS_DIRECTIONS.index(ec.get(f)) if ec.get(f) in COMPASS_DIRECTIONS else 0
                                    ec[f] = st.selectbox(label, COMPASS_DIRECTIONS, index=idx_opt, key=f"edit_{f}")
                                
                                elif f == "Tide Direction":
                                    tide_opts = ["High", "Low", "Falling", "Rising"]
                                    cur_val = ec.get(f)
                                    if cur_val == "Dropping":  # legacy value
                                        cur_val = "Falling"
                                    idx = tide_opts.index(cur_val) if cur_val in tide_opts else 0
                                    ec[f] = st.selectbox(label, tide_opts, index=idx, key=f"edit_{f}")
                                
                                elif f == "Zone":
                                    # Get existing zones from user's records
                                    existing_zones = sorted([z for z in records_df["Zone"].dropna().unique() if str(z).strip()])
                                    z_opts = existing_zones + ["Add new..."]
                                    cur_z = ec.get(f, "")
                                    z_idx = z_opts.index(cur_z) if cur_z in z_opts else 0
                                    z_sel = st.selectbox("Zone (existing or new)", z_opts, index=z_idx, key=f"edit_{f}")
                                    if z_sel == "Add new...":
                                        ec[f] = st.text_input("New Zone Name", "", key="edit_new_zone").strip()
                                    else:
                                        ec[f] = z_sel
                                
                                elif f == "Break":
                                    # Get existing breaks
                                    existing_breaks = sorted([b for b in records_df["Break"].dropna().unique() if str(b).strip()])
                                    b_opts = existing_breaks + ["Add new..."]
                                    cur_b = ec.get(f, "")
                                    b_idx = b_opts.index(cur_b) if cur_b in b_opts else 0
                                    b_sel = st.selectbox("Break (existing or new)", b_opts, index=b_idx, key=f"edit_{f}")
                                    if b_sel == "Add new...":
                                        ec[f] = st.text_input("New Break Name", "", key="edit_new_break").strip()
                                    else:
                                        ec[f] = b_sel
                                
                                elif "Suitable" in f:
                                    opts = ["Yes", "No", "Ok", "Too Big"] if "Swell" in f else ["Yes", "No", "Ok"]
                                    cur_val = ec.get(f, "Yes")
                                    idx = opts.index(cur_val) if cur_val in opts else 0
                                    ec[f] = st.selectbox(label, opts, index=idx, key=f"edit_{f}")
                                
                                elif "Comments" in f:
                                    val = ec.get(f, "")
                                    if pd.isna(val):
                                        val = ""
                                    ec[f] = st.text_area(label, val, key=f"edit_{f}")
                                
                                elif f in ["Swell Period (s)", "Swell Direction", "Wind Speed (kn)"]:
                                    ec[f] = st.number_input(label, value=safe_int(ec.get(f)), step=1, format="%d", key=f"edit_{f}")
                                
                                elif f in ["Swell Score", "Wind Score", "Tide Score"]:
                                    ec[f] = st.number_input(label, min_value=0, max_value=10, 
                                                          value=safe_int(ec.get(f)), step=1, format="%d", key=f"edit_{f}")
                                
                                elif f in ["Surfline Primary Swell Size (m)", "Seabreeze Swell (m)", "Tide Reading (m)"]:
                                    ec[f] = st.number_input(label, value=safe_float(ec.get(f)), step=0.1, format="%.1f", key=f"edit_{f}")
                                
                                else:
                                    ec[f] = st.text_input(label, str(ec.get(f) or ""), key=f"edit_{f}")
                            
                            # Recompute final scores
                            final_swell = round((ec.get("Swell Score") or 0) * factor_map.get(ec.get("Suitable Swell?"), 0), 1)
                            final_wind = round((ec.get("Wind Score") or 0) * factor_map.get(ec.get("Suitable Wind?"), 0), 1)
                            final_tide = round((ec.get("Tide Score") or 0) * factor_map.get(ec.get("Tide Suitable?"), 0), 1)
                            total_score = (final_swell * final_wind * final_tide) / 3 if all(v is not None for v in [final_swell, final_wind, final_tide]) else 0
                            total_score = round(total_score, 1)
                            
                            st.markdown(f"**Live Final Scores:** Swell `{final_swell}` | Wind `{final_wind}` | Tide `{final_tide}` | Total `{total_score:.1f}`")
                            
                            # Action buttons
                            st.markdown("---")
                            ac1, ac2, ac3, ac4 = st.columns(4)
                            
                            if ac1.button("❌ Cancel"):
                                st.session_state.editing = False
                                st.session_state.edit_index = None
                                st.session_state.confirm_delete = None
                                st.rerun()
                            
                            save_clicked = ac2.button("💾 Save Changes")
                            
                            if save_clicked:
                                # Build full commentary from component comments
                                full_comm = " ".join([
                                    ec.get("Swell Comments", "") or "", 
                                    ec.get("Wind Comments", "") or "", 
                                    ec.get("Tide Comments", "") or ""
                                ]).strip()
                                
                                # Ensure Swell Direction is an integer
                                if "Swell Direction" in ec and ec.get("Swell Direction") not in (None, ""):
                                    try:
                                        ec["Swell Direction"] = int(float(ec["Swell Direction"]))
                                    except:
                                        pass
                                
                                # Build update record
                                update_data = {
                                    'Date': ec.get("Date"),
                                    'Time': ec.get("Time"),
                                    'Break': ec.get("Break"),
                                    'Zone': ec.get("Zone"),
                                    'Surfline Primary Swell Size (m)': ec.get("Surfline Primary Swell Size (m)"),
                                    'Seabreeze Swell (m)': ec.get("Seabreeze Swell (m)"),
                                    'Swell Period (s)': ec.get("Swell Period (s)"),
                                    'Swell Direction': ec.get("Swell Direction"),
                                    'Suitable Swell?': ec.get("Suitable Swell?"),
                                    'Swell Score': ec.get("Swell Score"),
                                    'Final Swell Score': final_swell,
                                    'Swell Comments': ec.get("Swell Comments"),
                                    'Wind Bearing': ec.get("Wind Bearing"),
                                    'Wind Speed (kn)': ec.get("Wind Speed (kn)"),
                                    'Suitable Wind?': ec.get("Suitable Wind?"),
                                    'Wind Score': ec.get("Wind Score"),
                                    'Wind Final Score': final_wind,
                                    'Wind Comments': ec.get("Wind Comments"),
                                    'Tide Reading (m)': ec.get("Tide Reading (m)"),
                                    'Tide Direction': ec.get("Tide Direction"),
                                    'Tide Suitable?': ec.get("Tide Suitable?"),
                                    'Tide Score': ec.get("Tide Score"),
                                    'Tide Final Score': final_tide,
                                    'Tide Comments': ec.get("Tide Comments"),
                                    'TOTAL SCORE': total_score,
                                    'Full Commentary': full_comm
                                }
                                
                                if update_record(record_id, update_data):
                                    st.success("✅ Record updated successfully!")
                                    st.session_state.editing = False
                                    st.session_state.edit_index = None
                                    st.session_state.detail = None
                                    st.rerun()
                            
                            # DELETE workflow
                            if ac3.button("🗑️ Delete Record", key=f"del_{record_id}"):
                                st.session_state.confirm_delete = record_id if st.session_state.confirm_delete != record_id else None
                            
                            if st.session_state.confirm_delete == record_id:
                                st.warning("⚠️ Confirm delete? This cannot be undone.")
                                dc1, dc2 = st.columns(2)
                                if dc1.button("✓ Yes, delete now", key=f"del_yes_{record_id}"):
                                    if delete_record(record_id):
                                        st.success("✅ Record deleted successfully!")
                                        st.session_state.detail = None
                                        st.session_state.editing = False
                                        st.session_state.edit_index = None
                                        st.session_state.confirm_delete = None
                                        st.rerun()
                                if dc2.button("✗ Cancel delete", key=f"del_no_{record_id}"):
                                    st.session_state.confirm_delete = None
                                    st.rerun()
                            
                            if ac4.button("Close"):
                                st.session_state.detail = None
                                st.session_state.editing = False
                                st.session_state.edit_index = None
                                st.session_state.confirm_delete = None
                                st.rerun()
                else:
                    st.session_state.detail = None
                    st.rerun()

else:
    # MULTI-PAGE CREATE WIZARD
    st.markdown("### New Record")
    if st.button("← Back to List"):
        st.session_state.creating = False
        st.session_state.draft = {}
        st.rerun()
    
    # Define pages
    P1 = ["Visibility","Zone","Break","Date","Time"]
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
            
            if f=="Visibility":
                visibility_opts = ["Public", "Private", "Community"]
                prev_visibility = st.session_state.draft.get("Visibility", "Public")
                vis_idx = visibility_opts.index(prev_visibility) if prev_visibility in visibility_opts else 0
                st.session_state.draft["Visibility"] = st.selectbox(
                    "Record Visibility",
                    visibility_opts,
                    index=vis_idx,
                    help="Public: Everyone can see | Private: Only you | Community: Your community members"
                )
            
            elif f=="Zone":
                # Get existing zones from user's records
                existing_zones = []
                if not records_df.empty and 'Zone' in records_df.columns:
                    existing_zones = sorted([z for z in records_df["Zone"].dropna().unique() if str(z).strip()])
                z_opts = existing_zones + ["Add new..."]
                prev_z = st.session_state.draft.get("Zone","")
                z_idx = z_opts.index(prev_z) if prev_z in z_opts else 0
                z_sel = st.selectbox("Zone (existing or new)", z_opts, index=z_idx)
                if z_sel == "Add new...":
                    new_zone = st.text_input("New Zone Name","", key="new_zone_name", placeholder="Enter new zone").strip()
                    st.session_state.draft["Zone"] = new_zone
                else:
                    st.session_state.draft["Zone"] = z_sel
                    
            elif f=="Break":
                # Get existing breaks, filtered by zone if selected
                chosen_zone = st.session_state.draft.get("Zone","")
                if not records_df.empty and 'Break' in records_df.columns:
                    if chosen_zone and chosen_zone != "Add new..." and 'Zone' in records_df.columns:
                        zone_filtered = records_df[records_df["Zone"]==chosen_zone]
                        breaks_exist = sorted([b for b in zone_filtered["Break"].dropna().unique() if str(b).strip()])
                    else:
                        breaks_exist = sorted([b for b in records_df["Break"].dropna().unique() if str(b).strip()])
                else:
                    breaks_exist = []
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
                st.session_state.draft[f] = st.date_input(label, st.session_state.draft.get(f, datetime.date.today()))
                
            elif f=="Time":
                st.session_state.draft[f] = st.time_input(label, st.session_state.draft.get(f, datetime.time(8,0)))
                
            elif f=="Wind Bearing":
                existing = st.session_state.draft.get(f,"")
                idx_dir = COMPASS_DIRECTIONS.index(existing) if existing in COMPASS_DIRECTIONS else 0
                st.session_state.draft[f] = st.selectbox(label, COMPASS_DIRECTIONS, index=idx_dir)
                
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
                st.session_state.draft[f] = st.text_area(label, ("" if pd.isna(st.session_state.draft.get(f)) else st.session_state.draft.get(f,"")))
                
            elif "Suitable" in f:
                st.session_state.draft[f] = st.selectbox(
                    label, ["Yes","No","Ok","Too Big"] if "Swell" in f else ["Yes","No","Ok"],
                    index=["Yes","No","Ok","Too Big"].index(st.session_state.draft.get(f,"Yes"))
                        if st.session_state.draft.get(f,"Yes") in ["Yes","No","Ok","Too Big"] else 0
                )
            else:
                cur = st.session_state.draft.get(f)
                if f in int_scores:
                    st.session_state.draft[f] = st.number_input(label, min_value=0, max_value=10,
                                                              value=safe_int(cur), step=1, format="%d")
                elif f in whole_int:
                    st.session_state.draft[f] = st.number_input(label, value=safe_int(cur), step=1, format="%d")
                elif f in one_dp:
                    st.session_state.draft[f] = st.number_input(label, value=safe_float(cur), step=0.1, format="%.1f")
                else:
                    st.session_state.draft[f] = st.number_input(label, value=safe_float(cur), step=0.1)
    
    # Compute final scores AFTER inputs so they reflect latest changes
    d = st.session_state.draft
    fs = (d.get("Swell Score") or 0)*factor_map.get(d.get("Suitable Swell?"),0)
    fw = (d.get("Wind Score") or 0)*factor_map.get(d.get("Suitable Wind?"),0)
    ft = (d.get("Tide Score") or 0)*factor_map.get(d.get("Tide Suitable?"),0)
    d["Final Swell Score"] = round(fs,1)
    d["Wind Final Score"] = round(fw,1)
    d["Tide Final Score"] = round(ft,1)
    total_live = (fs*fw*ft)/3 if all(v is not None for v in [fs,fw,ft]) else 0
    total_live = round(total_live,1)
    
    if "Swell Direction" in d and d.get("Swell Direction") not in (None,""):
        try: 
            d["Swell Direction"] = int(float(d["Swell Direction"]))
        except: 
            pass
    
    # Display live scores in right column
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
    
    # Navigation buttons
    c1, c2, c3, c4 = st.columns(4)
    
    if c1.button("Cancel"):
        st.session_state.creating = False
        st.session_state.draft = {}
        st.rerun()
        
    if p > 0 and c2.button("← Prev"):
        st.session_state.c_page -= 1
        st.rerun()
    
    if p < len(PAGES)-1:
        if c3.button("Next →"):
            d = st.session_state.draft
            block_reason = None
            
            # Validation for each page
            if p == 0:  # Session page
                if not (d.get("Break","") or "").strip():
                    block_reason = "Please enter a Break before continuing."
            elif p == 1:  # Swell page
                sps = d.get("Surfline Primary Swell Size (m)") or 0
                sbs = d.get("Seabreeze Swell (m)") or 0
                if (sps is None or sps <= 0) and (sbs is None or sbs <= 0):
                    block_reason = "Enter at least one positive swell size (Surfline or Seabreeze)."
            elif p == 2:  # Wind page
                wb = d.get("Wind Bearing","")
                if wb not in COMPASS_DIRECTIONS:
                    block_reason = "Select a Wind Bearing direction."
                    
            if block_reason:
                st.error(block_reason)
            else:
                st.session_state.c_page += 1
                st.rerun()
    
    if p == len(PAGES)-1 and c4.button("✓ Submit"):
        d = st.session_state.draft
        comments_present = has_any_comment(d)
        missing = []
        
        # Final validation
        if not (d.get("Break","") or "").strip():
            missing.append("Break")
        sps = d.get("Surfline Primary Swell Size (m)") or 0
        sbs = d.get("Seabreeze Swell (m)") or 0
        if (sps is None or sps <= 0) and (sbs is None or sbs <= 0):
            missing.append("Surfline or Seabreeze Swell (>0)")
        wind_bearing = d.get("Wind Bearing")
        if wind_bearing not in COMPASS_DIRECTIONS:
            missing.append("Wind Bearing (direction)")
            
        if missing or not comments_present:
            msg = ""
            if missing:
                msg += f"Missing / invalid: {', '.join(missing)}. "
            if not comments_present:
                msg += "Enter at least one comment (Swell/Wind/Tide)."
            st.error(msg)
        else:
            # Build full commentary from component comments
            full_comm = " ".join([
                d.get("Swell Comments","") or "", 
                d.get("Wind Comments","") or "", 
                d.get("Tide Comments","") or ""
            ]).strip()
            
            # Calculate total score
            total_score = ((d.get("Final Swell Score",0) or 0) * (d.get("Wind Final Score",0) or 0) * (d.get("Tide Final Score",0) or 0)) / 3
            total_score = round(total_score,1)
            
            # Build record
            record = {
                'Date': d.get("Date"),
                'Time': d.get("Time"),
                'Break': d.get("Break"),
                'Zone': d.get("Zone"),
                'TOTAL SCORE': total_score,
                'publicity': d.get("Visibility", "Public"),  # Use the selected visibility
                'Surfline Primary Swell Size (m)': d.get("Surfline Primary Swell Size (m)", 0),
                'Seabreeze Swell (m)': d.get("Seabreeze Swell (m)", 0),
                'Swell Period (s)': d.get("Swell Period (s)", 0),
                'Swell Direction': d.get("Swell Direction"),
                'Suitable Swell?': d.get("Suitable Swell?", "Yes"),
                'Swell Score': d.get("Swell Score", 0),
                'Final Swell Score': d.get("Final Swell Score", 0),
                'Swell Comments': d.get("Swell Comments", ""),
                'Wind Bearing': d.get("Wind Bearing", "N"),
                'Wind Speed (kn)': d.get("Wind Speed (kn)", 0),
                'Suitable Wind?': d.get("Suitable Wind?", "Yes"),
                'Wind Score': d.get("Wind Score", 0),
                'Wind Final Score': d.get("Wind Final Score", 0),
                'Wind Comments': d.get("Wind Comments", ""),
                'Tide Reading (m)': d.get("Tide Reading (m)", 0),
                'Tide Direction': d.get("Tide Direction", "High"),
                'Tide Suitable?': d.get("Tide Suitable?", "Yes"),
                'Tide Score': d.get("Tide Score", 0),
                'Tide Final Score': d.get("Tide Final Score", 0),
                'Tide Comments': d.get("Tide Comments", ""),
                'Full Commentary': full_comm
            }
            
            if save_record(record):
                st.success("✅ Session saved successfully!")
                st.session_state.creating = False
                st.session_state.draft = {}
                st.session_state.c_page = 0
                st.rerun()
