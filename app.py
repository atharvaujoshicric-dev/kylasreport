import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Excel Master Dashboard", layout="wide")

st.title("📂 Deal & Notes Auto-Formatter")
st.markdown("Upload your 3 files. The downloaded Excel will have **Merged & Centered** rows with **Full Borders**.")

# File Uploaders
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
    # --- DATA PROCESSING ---
    df_deals = load_data(deals_file)
    df_contacts = load_data(contacts_file)
    df_notes = load_data(notes_file)

    # Standardize IDs
    df_deals['ID'] = df_deals['ID'].astype(str).str.strip()
    df_notes['Associated entity id'] = df_notes['Associated entity id'].astype(str).str.strip()
    df_contacts['ID'] = df_contacts['ID'].astype(str).str.strip()
    
    # Extract Contact ID from Deals string (e.g., "12345: Name")
    df_deals['Contact_Link'] = df_deals['Contacts'].str.extract('(\d+)').fillna('')

    # Merge Logic
    df_merged = pd.merge(df_deals, df_notes[['Associated entity id', 'Content']], 
                         left_on='ID', right_on='Associated entity id', how='left')
    
    df_merged = pd.merge(df_merged, df_contacts[['ID', 'Phone Numbers']], 
                         left_on='Contact_Link', right_on='ID', how='left')

    # Construct Report Table
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

    # Sort to keep groups together
    report = report.sort_values(by=['Name', 'Contact Number']).reset_index(drop=True)

    # --- EXCEL GENERATION ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        report.to_excel(writer, index=False, sheet_name='Deal Report')
        
        workbook  = writer.book
        worksheet = writer.sheets['Deal Report']

        # FORMATS
        # 1. General format for all cells (Center/Middle Align + Borders)
        base_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True
        })

        # 2. Header format (Bold + Colored + Center + Borders)
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        # Apply header format
        for col_num, value in enumerate(report.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Apply base format (borders and alignment) to every cell in the data range
        for r in range(1, len(report) + 1):
            for c in range(len(report.columns)):
                # We write the existing value with the base_format to apply borders
                worksheet.write(r, c, report.iloc[r-1, c], base_format)

        # 3. VERTICAL MERGE LOGIC
        # Identify chunks of the same Lead to merge columns A through J
        unique_leads = report.groupby(['Name', 'Contact Number', 'CP'], sort=False)
        
        current_row = 1 
        for _, group in unique_leads:
            start_row = current_row
            count = len(group)
            end_row = start_row + count - 1
            
            if count > 1:
                # Merge columns 0 to 9 (Name up to Lead Budget)
                for col in range(0, 10):
                    val = group.iloc[0, col]
                    worksheet.merge_range(start_row, col, end_row, col, val, base_format)
            
            current_row += count

        # Set column widths for readability
        worksheet.set_column('A:J', 22) # Lead Info
        worksheet.set_column('K:K', 60) # Notes

    processed_data = output.getvalue()

    st.success("✅ Excel File Ready!")
    st.download_button(
        label="📥 Download Formatted Excel Report",
        data=processed_data,
        file_name="Property_Deal_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("Please upload all three files (Deals, Contacts, Notes) to generate the report.")
