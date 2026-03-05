import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Excel Auto-Merger", layout="wide")

st.title("📑 Professional Excel Merger")
st.write("Upload your files to generate an Excel with true **Merge & Center** formatting.")

# File Uploaders
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
    # 1. Load and Process Data
    df_deals = load_data(deals_file)
    df_contacts = load_data(contacts_file)
    df_notes = load_data(notes_file)

    # Clean IDs
    df_deals['ID'] = df_deals['ID'].astype(str).str.strip()
    df_notes['Associated entity id'] = df_notes['Associated entity id'].astype(str).str.strip()
    df_contacts['ID'] = df_contacts['ID'].astype(str).str.strip()
    
    # Extract Contact ID from Deals string
    df_deals['Contact_Link'] = df_deals['Contacts'].str.extract('(\d+)').fillna('')

    # Merge Logic
    df_merged = pd.merge(df_deals, df_notes[['Associated entity id', 'Content']], 
                         left_on='ID', right_on='Associated entity id', how='left')
    
    df_merged = pd.merge(df_merged, df_contacts[['ID', 'Phone Numbers']], 
                         left_on='Contact_Link', right_on='ID', how='left')

    # Prepare Final Table
    report = pd.DataFrame()
    report['Name'] = df_merged['Name']
    report['Contact Number'] = df_merged['Phone Numbers'].fillna("")
    report['Campaigns'] = df_merged['Campaigns'].fillna("")
    report['Source'] = df_merged['Source'].fillna("")
    report['CP'] = df_merged['Channel Partner Name'].fillna("")
    report['CP Phone'] = df_merged['Channel Partner Number'].fillna("")
    report['CP Email'] = df_merged['Channel Partner Email'].fillna("")
    report['CP Company'] = df_merged['Channel Partner Company'].fillna("")
    report['Unit Preference'] = df_merged['Unit Preference'].fillna("")
    report['Lead Budget'] = df_merged['Lead Budget'].fillna("")
    report['Notes'] = df_merged['Content'].fillna("—")

    # Sort by Name to ensure groups are together for merging
    report = report.sort_values(by=['Name', 'Contact Number']).reset_index(drop=True)

    # 2. Excel Generation with Formatting
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        report.to_excel(writer, index=False, sheet_name='Report')
        
        workbook  = writer.book
        worksheet = writer.sheets['Report']

        # Define Formats
        merge_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1,
            'align': 'center'
        })

        # Apply Header Format
        for col_num, value in enumerate(report.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # 3. MERGE LOGIC
        # We iterate through the dataframe to find chunks of the same person
        unique_leads = report.groupby(['Name', 'Contact Number', 'CP'], sort=False)
        
        current_row = 1 # Start after header
        for _, group in unique_leads:
            start_row = current_row
            end_row = start_row + len(group) - 1
            
            # If there's more than one row for this lead, merge the detail columns
            if end_row > start_row:
                # Merge columns 0 to 9 (Name through Lead Budget)
                for col in range(0, 10):
                    val = group.iloc[0, col]
                    worksheet.merge_range(start_row, col, end_row, col, val, merge_format)
            
            current_row += len(group)

        # Auto-adjust column widths
        worksheet.set_column('A:K', 20)
        worksheet.set_column('K:K', 50) # Make Notes column wider

    processed_data = output.getvalue()

    st.success("✅ Report generated successfully!")
    st.download_button(
        label="📥 Download Merged Excel Report",
        data=processed_data,
        file_name="Property_Deal_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload the 3 files to start.")
