import streamlit as st
import pandas as pd

# Set Page Config
st.set_page_config(page_title="Real Estate Dashboard", layout="wide")

# Custom CSS for better table aesthetics
st.markdown("""
    <style>
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 10px; }
    th { background-color: #f8f9fa !important; text-align: center !important; }
    td { vertical-align: middle !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 Deal & Notes Consolidation Dashboard")
st.info("Upload your Excel files to generate the grouped report with consolidated notes.")

# 1. File Uploaders
col1, col2, col3 = st.columns(3)
with col1:
    deals_file = st.file_uploader("1. Upload Deals", type=['xlsx', 'csv'])
with col2:
    contacts_file = st.file_uploader("2. Upload Contacts", type=['xlsx', 'csv'])
with col3:
    notes_file = st.file_uploader("3. Upload Notes", type=['xlsx', 'csv'])

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

if deals_file and contacts_file and notes_file:
    # Load Data
    df_deals = load_data(deals_file)
    df_contacts = load_data(contacts_file)
    df_notes = load_data(notes_file)

    # Clean IDs to ensure matching works
    df_deals['ID'] = df_deals['ID'].astype(str).str.strip()
    df_notes['Associated entity id'] = df_notes['Associated entity id'].astype(str).str.strip()
    
    # Extract Contact ID from the 'Contacts' column in Deals (Format: "12345: Name")
    df_deals['Contact_Link_ID'] = df_deals['Contacts'].str.extract('(\d+)').fillna('')

    # 2. Merge Deals with Notes (One row per note)
    merged_df = pd.merge(
        df_deals, 
        df_notes[['Associated entity id', 'Content']], 
        left_on='ID', 
        right_on='Associated entity id', 
        how='left'
    )

    # 3. Merge with Contacts to get Customer Phone Number
    df_contacts['ID'] = df_contacts['ID'].astype(str).str.strip()
    merged_df = pd.merge(
        merged_df,
        df_contacts[['ID', 'Phone Numbers']],
        left_on='Contact_Link_ID',
        right_on='ID',
        how='left',
        suffixes=('', '_contact_file')
    )

    # 4. Construct Final Columns
    final_report = pd.DataFrame()
    final_report['Name'] = merged_df['Name']
    final_report['Customer Contact'] = merged_df['Phone Numbers'].fillna("N/A")
    final_report['Campaigns'] = merged_df['Campaigns']
    final_report['Source'] = merged_df['Source']
    final_report['CP'] = merged_df['Channel Partner Name']
    final_report['CP Phone'] = merged_df['Channel Partner Number']
    final_report['CP Email'] = merged_df['Channel Partner Email']
    final_report['CP Company'] = merged_df['Channel Partner Company']
    final_report['Unit Preference'] = merged_df['Unit Preference']
    final_report['Lead Budget'] = merged_df['Lead Budget']
    final_report['Notes'] = merged_df['Content'].fillna("—")

    # 5. Visual Merge Logic
    # We define which columns should "merge" (blank out on repeat rows)
    merge_cols = [
        'Name', 'Customer Contact', 'Campaigns', 'Source', 
        'CP', 'CP Phone', 'CP Email', 'CP Company', 
        'Unit Preference', 'Lead Budget'
    ]
    
    # This identifies duplicates across all these columns and empties them for rows 2-N
    mask = final_report.duplicated(subset=merge_cols, keep='first')
    display_df = final_report.copy()
    display_df.loc[mask, merge_cols] = ""

    # 6. Display Dashboard
    st.subheader("📋 Consolidated Deal Report")
    st.dataframe(display_df, use_container_width=True, height=700, hide_index=True)

    # Download Option
    csv = final_report.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Final Report (Excel Compatible CSV)", csv, "deal_report.csv", "text/csv")

else:
    st.warning("Waiting for all 3 files to be uploaded...")
