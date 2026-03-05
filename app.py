import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Real Estate Lead Tracker", layout="wide")

st.title("📊 Lead & Notes Dashboard")
st.markdown("Upload your Excel files to generate the consolidated report with merged-style formatting.")

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
    # Load Data
    df_deals = load_data(deals_file)
    df_contacts = load_data(contacts_file)
    df_notes = load_data(notes_file)

    # Convert IDs to string to ensure matching works
    df_deals['ID'] = df_deals['ID'].astype(str)
    df_contacts['Associated Entity Id'] = df_contacts['Associated Entity Id'].astype(str)
    df_notes['Associated entity id'] = df_notes['Associated entity id'].astype(str)

    # 1. Process Contacts: Create Name and Clean Phone
    df_contacts['Full Name'] = df_contacts['First Name'].fillna('') + ' ' + df_contacts['Last Name'].fillna('')
    # Extract phone from "MOBILE: +91..." format
    df_contacts['Customer Phone'] = df_contacts['Phone Numbers'].str.replace('MOBILE: ', '')

    # 2. Merge Deals with Contacts (to get Customer Name and Phone)
    merged_step1 = pd.merge(
        df_deals, 
        df_contacts[['Associated Entity Id', 'Full Name', 'Customer Phone']], 
        left_on='ID', 
        right_on='Associated Entity Id', 
        how='left'
    )

    # 3. Merge with Notes (This creates 5 rows if there are 5 notes)
    final_merged = pd.merge(
        merged_step1, 
        df_notes[['Associated entity id', 'Content']], 
        left_on='ID', 
        right_on='Associated entity id', 
        how='left'
    )

    # 4. Construct Final Columns
    report = pd.DataFrame()
    report['Name'] = final_merged['Full Name']
    report['Customer Phone'] = final_merged['Customer Phone']
    report['Source'] = final_merged['Source']
    report['CP'] = final_merged['Channel Partner Name']
    report['CP Phone Number'] = final_merged['Channel Partner Number']
    report['CP Email'] = final_merged['Channel Partner Email']
    report['CP Company'] = final_merged['Channel Partner Company']
    report['Unit Preference'] = final_merged['Unit Preference']
    report['Lead Budget'] = final_merged['Lead Budget']
    report['Notes'] = final_merged['Content'].fillna("—")

    # 5. Apply "Merge & Center" visual logic
    # We identify duplicates in the lead info columns and replace them with empty strings
    lead_info_cols = ['Name', 'Customer Phone', 'Source', 'CP', 'CP Phone Number', 'CP Email', 'CP Company', 'Unit Preference', 'Lead Budget']
    
    # We keep a copy for downloading (with all data) and a copy for display (with blanks)
    display_df = report.copy()
    mask = display_df.duplicated(subset=['Name', 'Customer Phone', 'Source'], keep='first')
    display_df.loc[mask, lead_info_cols] = ""

    # 6. UI Display
    st.subheader("Final Report")
    st.dataframe(display_df, use_container_width=True, height=600)

    # 7. Download
    towrite = io.BytesIO()
    report.to_excel(towrite, index=False, engine='openpyxl')
    st.download_button(
        label="Download Full Excel Report",
        data=towrite.getvalue(),
        file_name="Consolidated_Lead_Report.xlsx",
        mime="application/vnd.ms-excel"
    )

else:
    st.info("Please upload all three Excel/CSV files to generate the dashboard.")
