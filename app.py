import streamlit as st
import pandas as pd

st.set_page_config(page_title="Real Estate Deal Dashboard", layout="wide")

st.title("📂 Deal & Notes Integrator")
st.write("Upload your Deals, Contacts, and Notes excels to generate the unified report.")

# 1. File Uploaders
col1, col2, col3 = st.columns(3)
with col1:
    deals_file = st.file_uploader("Upload Deals Excel", type=['xlsx', 'csv'])
with col2:
    contacts_file = st.file_uploader("Upload Contacts Excel", type=['xlsx', 'csv'])
with col3:
    notes_file = st.file_uploader("Upload Notes Excel", type=['xlsx', 'csv'])

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

if deals_file and contacts_file and notes_file:
    # Load Data
    df_deals = load_data(deals_file)
    df_contacts = load_data(contacts_file)
    df_notes = load_data(notes_file)

    # Data Cleaning (Removing whitespace from IDs)
    df_deals['ID'] = df_deals['ID'].astype(str)
    df_contacts['ID'] = df_contacts['ID'].astype(str)
    df_notes['Associated entity id'] = df_notes['Associated entity id'].astype(str)

    # 1. Prepare Contacts (Combine First + Last Name)
    df_contacts['Name'] = df_contacts['First Name'].fillna('') + ' ' + df_contacts['Last Name'].fillna('')
    
    # 2. Merge Deals with Contacts 
    # (Using 'Contacts' column in Deals or 'ID' link)
    # Based on your file samples: Deals.ID links to Notes.Associated entity id
    # Deals also contains CP info directly in the columns.
    
    # 3. Merge with Notes (Left join to keep all deals, even those without notes)
    merged_df = pd.merge(
        df_deals, 
        df_notes[['Associated entity id', 'Content']], 
        left_on='ID', 
        right_on='Associated entity id', 
        how='left'
    )

    # 4. Final Column Selection & Renaming
    # Column format: Name (firstname+lastname), Source, CP, CP phone number, Cp email, CP company, Unit Preference, Lead Budget, Notes
    final_report = pd.DataFrame()
    final_report['Name'] = merged_df['Name'] # From Deals table if present, else merge from Contacts
    final_report['Source'] = merged_df['Source']
    final_report['CP'] = merged_df['Channel Partner Name']
    final_report['CP Phone Number'] = merged_df['Channel Partner Number']
    final_report['CP Email'] = merged_df['Channel Partner Email']
    final_report['CP Company'] = merged_df['Channel Partner Company']
    final_report['Unit Preference'] = merged_df['Unit Preference']
    final_report['Lead Budget'] = merged_df['Lead Budget']
    final_report['Notes'] = merged_df['Content'].fillna("No Notes Found")

    # 5. Display with Styling
    st.subheader("Generated Report")
    
    # Function to hide repeating values (Visual Merge effect)
    def make_pretty(df):
        # Identify columns that should not repeat
        dup_cols = ['Name', 'Source', 'CP', 'CP Phone Number', 'CP Email', 'CP Company', 'Unit Preference', 'Lead Budget']
        mask = df.duplicated(subset=dup_cols, keep='first')
        df_display = df.copy()
        df_display.loc[mask, dup_cols] = ""
        return df_display

    styled_df = make_pretty(final_report)
    
    st.dataframe(styled_df, use_container_width=True, height=600)

    # Download Button
    csv = final_report.to_csv(index=False).encode('utf-8')
    st.download_button("Download Full Report as CSV", csv, "deal_report.csv", "text/csv")

else:
    st.info("Please upload all three files to see the report.")
