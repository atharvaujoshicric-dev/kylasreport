import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Excel Master Dashboard", layout="wide")

st.title("📂 Professional Deal Report Generator")
st.markdown("Upload your files to get a **Merged & Centered** Excel with cleaned phone numbers and notes.")

# --- CLEANING FUNCTIONS ---
def clean_notes(text):
    if pd.isna(text) or not isinstance(text, str):
        return text
    # Removes broken encoding characters like Â and non-breaking spaces
    text = text.replace('\xa0', ' ').replace('Â', '')
    text = re.sub(r'\s+', ' ', text) # Remove extra spaces
    return text.strip()

def clean_phone(val):
    if pd.isna(val) or val == "":
        return ""
    val = str(val)
    # Removes "MOBILE:", "+91", and any spaces or dashes
    cleaned = val.replace("MOBILE:", "").replace("+91", "")
    cleaned = re.sub(r'[^0-9]', '', cleaned) # Keep only digits
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
    
    # Extract Contact ID from Deals string
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
        report.to_excel(writer, index=False, sheet_name='Report')
        
        workbook  = writer.book
        worksheet = writer.sheets['Report']

        # Format Definitions
        base_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center', 'valign': 'vcenter'
        })

        # Format Headers
        for col_num, value in enumerate(report.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Apply basic formatting (borders/alignment) to all cells
        for r in range(1, len(report) + 1):
            for c in range(len(report.columns)):
                worksheet.write(r, c, report.iloc[r-1, c], base_format)

        # Apply Merge and Center logic
        unique_leads = report.groupby(['Name', 'Contact Number', 'CP'], sort=False)
        current_row = 1 
        for _, group in unique_leads:
            start_row = current_row
            end_row = start_row + len(group) - 1
            if len(group) > 1:
                for col in range(0, 10): # Merge Name through Lead Budget
                    val = group.iloc[0, col]
                    worksheet.merge_range(start_row, col, end_row, col, val, base_format)
            current_row += len(group)

        # Column widths
        worksheet.set_column('A:J', 20)
        worksheet.set_column('K:K', 60)

    st.success("✅ Cleaned & Formatted Excel is ready!")
    st.download_button(
        label="📥 Download Final Excel Report",
        data=output.getvalue(),
        file_name="Cleaned_Lead_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
