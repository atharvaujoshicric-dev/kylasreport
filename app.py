import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Real Estate Dashboard", layout="wide")

st.title("📊 Consolidated Property Dashboard")

# 1. File Uploaders
col1, col2, col3 = st.columns(3)
with col1:
    deals_file = st.file_uploader("Upload Deals", type=['xlsx', 'csv'])
with col2:
    contacts_file = st.file_uploader("Upload Contacts", type=['xlsx', 'csv'])
with col3:
    notes_file = st.file_uploader("Upload Notes", type=['xlsx', 'csv'])

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

if deals_file and contacts_file and notes_file:
    df_deals = load_data(deals_file)
    df_contacts = load_data(contacts_file)
    df_notes = load_data(notes_file)

    # Convert IDs to strings for robust matching
    df_deals['ID'] = df_deals['ID'].astype(str)
    df_notes['Associated entity id'] = df_notes['Associated entity id'].astype(str)
    
    # Extract Contact ID from Deals (Format often looks like "12345: Name")
    def extract_id(val):
        match = re.search(r'(\d+)', str(val))
        return match.group(1) if match else ""
    
    df_deals['Contact_Link'] = df_deals['Contacts'].apply(extract_id)
    df_contacts['ID'] = df_contacts['ID'].astype(str)

    # Merge 1: Deals + Contacts (to get Phone and verify names)
    df_merged = pd.merge(
        df_deals, 
        df_contacts[['ID', 'Phone Numbers']], 
        left_on='Contact_Link', 
        right_on='ID', 
        how='left'
    )

    # Merge 2: Deals + Notes (This creates the multiple rows for 1 customer)
    final_df = pd.merge(
        df_merged, 
        df_notes[['Associated entity id', 'Content']], 
        left_on='ID_x', 
        right_on='Associated entity id', 
        how='left'
    )

    # Build the required column structure
    report = pd.DataFrame()
    report['Name'] = final_df['Name']
    report['Contact Number'] = final_df['Phone Numbers']
    report['Campaigns'] = final_df['Campaigns']
    report['Source'] = final_df['Source']
    report['CP'] = final_df['Channel Partner Name']
    report['CP Phone'] = final_df['Channel Partner Number']
    report['CP Email'] = final_df['Channel Partner Email']
    report['CP Company'] = final_df['Channel Partner Company']
    report['Unit Preference'] = final_df['Unit Preference']
    report['Lead Budget'] = final_df['Lead Budget']
    report['Notes'] = final_df['Content'].fillna("—")

    # --- THE MERGE LOGIC ---
    # We define all columns EXCEPT 'Notes' as part of the "Merge Group"
    cols_to_fix = [
        'Name', 'Contact Number', 'Campaigns', 'Source', 'CP', 
        'CP Phone', 'CP Email', 'CP Company', 'Unit Preference', 'Lead Budget'
    ]

    # This logic identifies duplicates within each customer group
    # It keeps the first occurrence and clears the rest to simulate a merged cell
    mask = report.duplicated(subset=['Name', 'Contact Number', 'CP'], keep='first')
    styled_report = report.copy()
    styled_report.loc[mask, cols_to_fix] = ""

    # Display
    st.subheader("Unified Lead Report")
    
    # Using st.table for a more "Static/Excel" look or st.dataframe for interactivity
    st.dataframe(styled_report, use_container_width=True, height=800)

    # Export functionality
    csv = report.to_csv(index=False).encode('utf-8')
    st.download_button("Download Full CSV", csv, "report.csv", "text/csv")

else:
    st.info("Please upload all three Excel/CSV files to generate the dashboard.")
