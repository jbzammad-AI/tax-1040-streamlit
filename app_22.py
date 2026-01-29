import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
import json
import base64

# Page config
st.set_page_config(page_title="Tax 1040 Tool", layout="wide")

st.title("📊 Complete IRS Form 1040 Automation")

# Import modules
try:
    from document_processor import PDFProcessor
    from irs_rules_engine import IRSTaxEngine
    from pdf_filler import PDFFiller
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"Missing modules: {e}")
    st.info("Install: pip install fpdf2 reportlab pypdf")
    MODULES_AVAILABLE = False

# Initialize session state
for key in ['extracted_data', 'tax_calculations', 'form_1040_path', 'manual_mode']:
    if key not in st.session_state:
        st.session_state[key] = None

# Sidebar
with st.sidebar:
    st.header("📋 Navigation")
    
    tab = st.radio("Choose Mode:", 
                   ["Manual Entry", "PDF Upload", "Form 1040 Generator"])
    
    st.header("⚙️ Settings")
    filing_status = st.selectbox(
        "Filing Status",
        ["Head of Household", "Single", "Married Filing Jointly", 
         "Married Filing Separately", "Qualifying Surviving Spouse"],
        index=0
    )
    
    st.header("💡 Quick Data")
    if st.button("Load Whitney Example"):
        st.session_state.manual_mode = True
        st.session_state.prefilled_data = {
            "name": "Whitney M. Refund",
            "ssn": "400-00-4702",
            "status": "Head of Household",
            "dependents": 1,
            "wages": 26263.0,
            "fed_tax": 264.0,
            "interest": 0.0,
            "dividends": 0.0,
            "daycare": 3100.0
        }

# MAIN CONTENT BASED ON SELECTED TAB
if tab == "Manual Entry":
    st.header("📝 Manual Data Entry")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Taxpayer Name", 
                           st.session_state.get('prefilled_data', {}).get('name', ''))
        ssn = st.text_input("SSN", 
                          st.session_state.get('prefilled_data', {}).get('ssn', ''))
        status = st.selectbox(
            "Filing Status",
            ["Head of Household", "Single", "Married Filing Jointly"],
            index=["Head of Household", "Single", "Married Filing Jointly"].index(
                st.session_state.get('prefilled_data', {}).get('status', 'Head of Household')
            )
        )
        dependents = st.number_input("Dependents", 
                                   value=st.session_state.get('prefilled_data', {}).get('dependents', 1),
                                   min_value=0, max_value=10)
    
    with col2:
        wages = st.number_input("Wages", 
                              value=st.session_state.get('prefilled_data', {}).get('wages', 26263.0),
                              min_value=0.0, step=1000.0)
        fed_tax = st.number_input("Federal Tax Withheld", 
                                value=st.session_state.get('prefilled_data', {}).get('fed_tax', 264.0),
                                min_value=0.0, step=50.0)
        interest = st.number_input("Interest Income", 
                                 value=st.session_state.get('prefilled_data', {}).get('interest', 0.0),
                                 min_value=0.0, step=100.0)
        dividends = st.number_input("Dividend Income", 
                                  value=st.session_state.get('prefilled_data', {}).get('dividends', 0.0),
                                  min_value=0.0, step=100.0)
        daycare = st.number_input("Daycare Expenses", 
                                value=st.session_state.get('prefilled_data', {}).get('daycare', 3100.0),
                                min_value=0.0, step=100.0)
    
    if st.button("Calculate & Generate Form 1040", type="primary", use_container_width=True):
        if MODULES_AVAILABLE:
            manual_data = {
                "taxpayer_name": name,
                "taxpayer_ssn": ssn,
                "filing_status": status.lower().replace(" ", "_"),
                "dependent_count": dependents,
                "wages": wages,
                "federal_tax_withheld": fed_tax,
                "interest_income": interest,
                "dividends": dividends,
                "daycare_expenses": daycare
            }
            
            # Calculate tax
            engine = IRSTaxEngine()
            engine.filing_status = manual_data["filing_status"]
            
            st.session_state.tax_calculations = engine.calculate_tax(manual_data)
            st.session_state.extracted_data = manual_data
            
            # Generate Form 1040 PDF
            filler = PDFFiller()
            st.session_state.form_1040_path = filler.create_form_1040_pdf(
                st.session_state.tax_calculations,
                st.session_state.extracted_data
            )
            
            st.success("✅ Form 1040 generated successfully!")
            
            # Show results immediately
            st.rerun()
        else:
            st.error("Required modules not available.")

elif tab == "PDF Upload":
    st.header("📄 Upload Tax Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Client Documents")
        uploaded_files = st.file_uploader(
            "Upload W-2, 1099, etc.",
            type=['pdf'],
            accept_multiple_files=True,
            key="client_docs"
        )
    
    with col2:
        st.subheader("Blank Form 1040 (Optional)")
        st.info("Upload blank Form 1040 PDF for filling")
        blank_form = st.file_uploader(
            "Upload blank Form 1040 PDF",
            type=['pdf'],
            key="blank_form"
        )
    
    if uploaded_files and st.button("Process & Generate Form 1040", type="primary"):
        if MODULES_AVAILABLE:
            with st.spinner("Processing documents..."):
                processor = PDFProcessor()
                client_files = []
                
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        tmp.write(uploaded_file.getvalue())
                        client_files.append(tmp.name)
                
                all_extracted = []
                for file_path in client_files:
                    extracted = processor.process_pdf(file_path)
                    if extracted:
                        all_extracted.append(extracted)
                    os.unlink(file_path)
                
                if all_extracted:
                    st.session_state.extracted_data = processor.combine_extracted_data(all_extracted)
                    
                    # Use filing status from PDF or selected
                    if st.session_state.extracted_data.get("filing_status"):
                        status_map = {
                            "head_of_household": "Head of Household",
                            "married_joint": "Married Filing Jointly",
                            "single": "Single"
                        }
                        pdf_status = st.session_state.extracted_data["filing_status"]
                        if pdf_status in status_map:
                            filing_status = status_map[pdf_status]
                    
                    # Calculate tax
                    engine = IRSTaxEngine()
                    status_map = {
                        "Head of Household": "head_of_household",
                        "Single": "single",
                        "Married Filing Jointly": "married_joint"
                    }
                    engine.filing_status = status_map.get(filing_status, "single")
                    
                    st.session_state.tax_calculations = engine.calculate_tax(
                        st.session_state.extracted_data
                    )
                    
                    # Generate Form 1040
                    filler = PDFFiller()
                    
                    if blank_form:
                        # Save blank form temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                            tmp.write(blank_form.getvalue())
                            blank_path = tmp.name
                        
                        # Fill existing form
                        st.session_state.form_1040_path = filler.fill_existing_form_1040(
                            blank_path,
                            st.session_state.tax_calculations,
                            st.session_state.extracted_data
                        )
                        
                        os.unlink(blank_path)
                    else:
                        # Create new form
                        st.session_state.form_1040_path = filler.create_form_1040_pdf(
                            st.session_state.tax_calculations,
                            st.session_state.extracted_data
                        )
                    
                    st.success("✅ Form 1040 generated from uploaded documents!")
                    
                    # Show results
                    st.rerun()
                else:
                    st.error("Could not extract data. Try manual entry.")
        else:
            st.error("Required modules not available.")

elif tab == "Form 1040 Generator":
    st.header("🎯 Generate Form 1040")
    
    if not st.session_state.tax_calculations:
        st.warning("No tax data available. Please use Manual Entry or PDF Upload first.")
    else:
        # Display results
        st.subheader("Tax Calculation Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Income", 
                     f"${st.session_state.tax_calculations.get('total_income', 0):,.2f}")
        
        with col2:
            st.metric("Total Tax", 
                     f"${st.session_state.tax_calculations.get('total_tax', 0):,.2f}")
        
        with col3:
            refund = st.session_state.tax_calculations.get("refund", 0)
            owed = st.session_state.tax_calculations.get("amount_owed", 0)
            if refund > 0:
                st.metric("REFUND", f"${refund:,.2f}", delta="Refund")
            else:
                st.metric("AMOUNT OWED", f"${owed:,.2f}", delta="Payment Due")
        
        # Form 1040 Preview
        st.subheader("Form 1040 Preview")
        
        lines = st.session_state.tax_calculations.get("form_1040_lines", {})
        
        # Key lines table
        key_lines = [
            ("1", "Wages, salaries, tips", lines.get("1", 0)),
            ("7", "Total income", lines.get("7", 0)),
            ("11", "Adjusted Gross Income (AGI)", lines.get("11", 0)),
            ("12", "Standard deduction", lines.get("12", 0)),
            ("15", "Taxable income", lines.get("15", 0)),
            ("16", "Tax", lines.get("16", 0)),
            ("19", "Child tax credit", lines.get("19", 0)),
            ("27", "Earned income credit", lines.get("27", 0)),
            ("24", "Total tax", lines.get("24", 0)),
            ("25a", "Federal income tax withheld", lines.get("25a", 0)),
            ("31", "Total payments", lines.get("31", 0)),
            ("34", "Refund", lines.get("34", 0)),
            ("37", "Amount you owe", lines.get("37", 0)),
        ]
        
        lines_data = []
        for line_num, desc, amount in key_lines:
            if amount != 0 or line_num in ["12", "16", "24", "31", "34", "37"]:
                lines_data.append({
                    "Line": line_num,
                    "Description": desc,
                    "Amount": f"${amount:,.2f}"
                })
        
        st.dataframe(pd.DataFrame(lines_data), hide_index=True, use_container_width=True)
        
        # Download Section
        st.subheader("Download Form 1040")
        
        if st.session_state.form_1040_path and os.path.exists(st.session_state.form_1040_path):
            # Read PDF
            with open(st.session_state.form_1040_path, "rb") as f:
                pdf_bytes = f.read()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Download Form 1040
                st.download_button(
                    label="📥 Download Form 1040",
                    data=pdf_bytes,
                    file_name=f"Form_1040_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col2:
                # Create complete package
                if MODULES_AVAILABLE:
                    filler = PDFFiller()
                    package_path = filler.create_filing_package(
                        st.session_state.tax_calculations,
                        st.session_state.extracted_data
                    )
                    
                    with open(package_path, "rb") as f:
                        package_bytes = f.read()
                    
                    st.download_button(
                        label="📦 Complete Filing Package",
                        data=package_bytes,
                        file_name=f"Tax_Filing_Package_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            with col3:
                # Download data as JSON
                json_data = {
                    "taxpayer_info": st.session_state.extracted_data,
                    "tax_calculations": st.session_state.tax_calculations,
                    "generated": datetime.now().isoformat()
                }
                
                st.download_button(
                    label="📊 Download Data (JSON)",
                    data=json.dumps(json_data, indent=2),
                    file_name=f"Tax_Data_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            # Preview (first page)
            st.subheader("Form Preview")
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(st.session_state.form_1040_path, first_page=1, last_page=1)
                if images:
                    # Save as temp file
                    preview_path = tempfile.mktemp(suffix='_preview.jpg')
                    images[0].save(preview_path, 'JPEG')
                    
                    st.image(preview_path, caption="Form 1040 Preview (Page 1)", use_container_width=True)
            except:
                st.info("Preview not available. Download the PDF to view.")
        
        # Filing Instructions
        with st.expander("📋 Filing Instructions", expanded=True):
            st.markdown("""
            **Before Filing:**
            1. **Review** all information on Form 1040
            2. **Sign and date** on page 2 (both spouses if married filing jointly)
            3. **Attach** required documents:
               - Copy B of all W-2 forms
               - Forms 1099 with tax withholding
               - Any schedules mentioned
            
            **Mailing:**
            - Find your state's IRS address: [Where to File](https://www.irs.gov/filing/where-to-file-paper-tax-returns)
            - Use certified mail with tracking
            - Keep copies of everything
            
            **Deadline:** April 15, 2026
            
            **Need Help?**
            - IRS: 1-800-829-1040
            - [IRS.gov](https://www.irs.gov)
            """)

# Footer
st.markdown("---")
st.caption(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Based on IRS 2025 Tax Rules")