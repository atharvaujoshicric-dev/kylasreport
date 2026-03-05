import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Excel Master Dashboard", layout="wide")

st.title("📂 Professional Deal Report Generator")
st.markdown("Download an Excel with **Sr. No.**, **Merged Cells**, **Full Borders**, and **Cleaned Data**.")

# --- CLEANING FUNCTIONS ---
def clean_notes(text):
    if pd.isna(text) or not isinstance(text, str):
        return text
    # Removes broken encoding characters like Â and non-breaking spaces
    text = text.replace('\xa0', ' ').replace('Â', '')
    text = re.sub(r'\s+', ' ', text) 
    return text.strip()

def clean_phone(val):
    if pd.isna(val) or val == "":
        return ""
    val = str(val)
    # Remove MOBILE:, +91, and all non-numeric characters
    cleaned = val.replace("MOBILE:", "").replace("+91", "")
    cleaned = re.sub(r'[^0-9]', '', cleaned) 
    return cleaned

# --- FILE UPLOADERS ---
col1, col2, col3 = st.columns(3)
with col1:
    deals_file = st.file_uploader("1. Upload Deals", type=['xlsx', 'csv'])
with col2:
    contacts_file = st.file_uploader("2. Upload Contacts", type=['xlsx', 'csv'])
with col3:
    notes_file = st.file_uploader("3. Upload Notes", type=['xlsx', 'csv'])

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file, encoding='utf-8-sig')
    return pd.read_excel(file)

if deals_file and contacts_file and notes_file:
    # 1. Load Data
    df_deals = load_data(deals_file)
    df_contacts = load_data(contacts_file)
    df_notes = load_data(notes_file)

    # Standardize IDs
    df_deals['ID'] = df_deals['ID'].astype(str).str.strip()
    df_notes['Associated entity id'] = df_notes['Associated entity id'].astype(str).str.strip()
    df_contacts['ID'] = df_contacts['ID'].astype(str).str.strip()
    
    # Extract Contact ID
    df_deals['Contact_Link'] = df_deals['Contacts'].str.extract('(\d+)').fillna('')

    # 2. Merge Data
    df_merged = pd.merge(df_deals, df_notes[['Associated entity id', 'Content']], 
                         left_on='ID', right_on='Associated entity id', how='left')
    
    df_merged = pd.merge(df_merged, df_contacts[['ID', 'Phone Numbers']], 
                         left_on='Contact_Link', right_on='ID', how='left')

    # 3. Build Final Report and Clean
    report = pd.DataFrame()
    report['Name'] = df_merged['Name']
    report['Contact Number'] = df_merged['Phone Numbers'].apply(clean_phone)
    report['Campaigns'] = df_merged['Campaigns'].fillna("")
    report['Source'] = df_merged['Source'].fillna("")
    report['CP'] = df_merged['Channel Partner Name'].fillna("")
    report['CP Phone'] = df_merged['Channel Partner Number'].apply(clean_phone)
    report['CP Email'] = df_merged['Channel Partner Email'].fillna("")
    report['CP Company'] = df_merged['Channel Partner Company'].fillna("")
    report['Unit Preference'] = df_merged['Unit Preference'].fillna("")
    report['Lead Budget'] = df_merged['Lead Budget'].fillna("")
    report['Notes'] = df_merged['Content'].apply(clean_notes).fillna("—")

    # Sort to group same leads together
    report = report.sort_values(by=['Name', 'Contact Number']).reset_index(drop=True)

    # 4. Generate Formatted Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Start writing data from column B (index 1) to leave room for Sr. No. in column A
        report.to_excel(writer, index=False, sheet_name='Report', startcol=1)
        
        workbook  = writer.book
        worksheet = writer.sheets['Report']

        # Format Definitions
        base_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center', 'valign': 'vcenter'
        })

        # Write Sr. No. Header
        worksheet.write(0, 0, "Sr. No.", header_format)

        # Apply general formatting to all data cells and borders
        for r in range(1, len(report) + 1):
            worksheet.write(r, 0, "", base_format) # Sr No Column Borders
            for c in range(len(report.columns)):
                worksheet.write(r, c + 1, report.iloc[r-1, c], base_format)

        # 5. MERGE LOGIC WITH SERIAL NUMBER
        # Group by Name/Contact/CP to find unique leads
        unique_leads = report.groupby(['Name', 'Contact Number', 'CP'], sort=False)
        
        current_row = 1 
        sr_no = 1
        for _, group in unique_leads:
            start_row = current_row
            count = len(group)
            end_row = start_row + count - 1
            
            # Merge Sr. No. Column (Column 0)
            if count > 1:
                worksheet.merge_range(start_row, 0, end_row, 0, sr_no, base_format)
                # Merge Name (Col 1) through Lead Budget (Col 10)
                for col in range(1, 11):
                    val = group.iloc[0, col-1]
                    worksheet.merge_range(start_row, col, end_row, col, val, base_format)
            else:
                worksheet.write(start_row, 0, sr_no, base_format)
            
            sr_no += 1
            current_row += count

        # Column widths
        worksheet.set_column('A:A', 8)   # Sr. No.
        worksheet.set_column('B:K', 20)  # Customer/CP Details
        worksheet.set_column('L:L', 60)  # Notes

    st.success("✅ Cleaned Report with Sr. No. is ready!")
    st.download_button(
        label="📥 Download Formatted Excel",
        data=output.getvalue(),
        file_name="Final_Property_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
