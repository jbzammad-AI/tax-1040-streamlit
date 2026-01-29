import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
import json
import traceback

# Page config
st.set_page_config(page_title="Tax 1040 Tool", layout="wide")

st.title("📊 Complete IRS Form 1040 Automation")

# Import modules - FIXED IMPORT
try:
    from document_processor import PDFProcessor
    from irs_rules_engine import IRSTaxEngine
    # Try importing Form1040PDF (correct class name)
    from pdf_filler import Form1040PDF
    # Create alias for compatibility
    PDFFiller = Form1040PDF
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"Import error: {e}")
    traceback.print_exc()
    MODULES_AVAILABLE = False

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'tax_calculations' not in st.session_state:
    st.session_state.tax_calculations = None
if 'form_1040_path' not in st.session_state:
    st.session_state.form_1040_path = None
if 'manual_mode' not in st.session_state:
    st.session_state.manual_mode = None
if 'prefilled_data' not in st.session_state:
    st.session_state.prefilled_data = {}  # Initialize as empty dict

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
        st.success("Example data loaded! Go to Manual Entry tab.")

# MAIN CONTENT
if tab == "Manual Entry":
    st.header("📝 Manual Data Entry")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Use prefilled data if available - SIMPLIFIED FIX
        # Get prefilled data with default empty dict
        prefilled = st.session_state.prefilled_data
        
        # Provide default empty string if prefilled is None or key doesn't exist
        name_default = prefilled.get('name', '') if prefilled else ''
        ssn_default = prefilled.get('ssn', '') if prefilled else ''
        dependents_default = prefilled.get('dependents', 0) if prefilled else 0
        
        name = st.text_input("Taxpayer Name", value=name_default)
        ssn = st.text_input("SSN", value=ssn_default)
        status = st.selectbox(
            "Filing Status",
            ["Head of Household", "Single", "Married Filing Jointly"],
            index=0
        )
        dependents = st.number_input("Dependents", 
                                   value=dependents_default,
                                   min_value=0, max_value=10)
    
    with col2:
        # Get numeric defaults with safe access
        wages_default = prefilled.get('wages', 0.0) if prefilled else 0.0
        fed_tax_default = prefilled.get('fed_tax', 0.0) if prefilled else 0.0
        interest_default = prefilled.get('interest', 0.0) if prefilled else 0.0
        dividends_default = prefilled.get('dividends', 0.0) if prefilled else 0.0
        daycare_default = prefilled.get('daycare', 0.0) if prefilled else 0.0
        
        wages = st.number_input("Wages", 
                              value=float(wages_default),
                              min_value=0.0, step=1000.0)
        fed_tax = st.number_input("Federal Tax Withheld", 
                                value=float(fed_tax_default),
                                min_value=0.0, step=50.0)
        interest = st.number_input("Interest Income", 
                                 value=float(interest_default),
                                 min_value=0.0, step=100.0)
        dividends = st.number_input("Dividend Income", 
                                  value=float(dividends_default),
                                  min_value=0.0, step=100.0)
        daycare = st.number_input("Daycare Expenses", 
                                value=float(daycare_default),
                                min_value=0.0, step=100.0)
    
    if st.button("Calculate & Generate Form 1040", type="primary", use_container_width=True):
        if MODULES_AVAILABLE:
            try:
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
                filler = Form1040PDF()
                st.session_state.form_1040_path = filler.create_form_1040(
                    st.session_state.tax_calculations,
                    st.session_state.extracted_data
                )
                
                st.success("✅ Form 1040 generated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                traceback.print_exc()
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
        st.info("Upload blank Form 1040 PDF for template filling")
        blank_form = st.file_uploader(
            "Upload blank Form 1040 PDF",
            type=['pdf'],
            key="blank_form"
        )
    
    if uploaded_files and st.button("Process & Generate Form 1040", type="primary"):
        if MODULES_AVAILABLE:
            with st.spinner("Processing documents..."):
                try:
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
                        current_status = filing_status
                        if st.session_state.extracted_data.get("filing_status"):
                            status_map = {
                                "head_of_household": "Head of Household",
                                "married_joint": "Married Filing Jointly",
                                "single": "Single"
                            }
                            pdf_status = st.session_state.extracted_data["filing_status"]
                            if pdf_status in status_map:
                                current_status = status_map[pdf_status]
                                st.info(f"Using filing status from PDF: {current_status}")
                        
                        # Calculate tax
                        engine = IRSTaxEngine()
                        status_map = {
                            "Head of Household": "head_of_household",
                            "Single": "single",
                            "Married Filing Jointly": "married_joint"
                        }
                        engine.filing_status = status_map.get(current_status, "single")
                        
                        st.session_state.tax_calculations = engine.calculate_tax(
                            st.session_state.extracted_data
                        )
                        
                        # Generate Form 1040
                        filler = Form1040PDF()
                        
                        # Always create new form (simplified)
                        st.session_state.form_1040_path = filler.create_form_1040(
                            st.session_state.tax_calculations,
                            st.session_state.extracted_data
                        )
                        
                        st.success("✅ Form 1040 generated from uploaded documents!")
                        st.rerun()
                    else:
                        st.error("Could not extract data from PDFs. Try manual entry.")
                        
                except Exception as e:
                    st.error(f"Processing error: {str(e)}")
                    traceback.print_exc()
        else:
            st.error("Required modules not available.")

elif tab == "Form 1040 Generator":
    st.header("🎯 Generate Form 1040")
    
    if not st.session_state.tax_calculations:
        st.warning("No tax data available. Please use Manual Entry or PDF Upload first.")
        st.info("Try: 1) Click 'Load Whitney Example' in sidebar, 2) Go to Manual Entry tab, 3) Click 'Calculate & Generate Form 1040'")
    else:
        # ===== TAXPAYER INFORMATION =====
        st.subheader("👤 Taxpayer Information")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            name = st.session_state.extracted_data.get("taxpayer_name", "Not Provided")
            st.metric("Taxpayer Name", name)
        
        with col2:
            ssn = st.session_state.extracted_data.get("taxpayer_ssn", "Not Provided")
            st.metric("SSN", ssn)
        
        with col3:
            status = st.session_state.tax_calculations.get("filing_status", "single")
            status_display = status.replace("_", " ").title()
            st.metric("Filing Status", status_display)
        
        with col4:
            deps = st.session_state.extracted_data.get("dependent_count", 0)
            st.metric("Dependents", deps)
        
        # ===== TAX CALCULATION SUMMARY =====
        st.subheader("📊 Tax Calculation Summary")
        
        calc = st.session_state.tax_calculations
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Income", f"${calc.get('total_income', 0):,.2f}")
        
        with col2:
            st.metric("Total Tax", f"${calc.get('total_tax', 0):,.2f}")
        
        with col3:
            refund = calc.get("refund", 0)
            owed = calc.get("amount_owed", 0)
            if refund > 0:
                st.metric("REFUND", f"${refund:,.2f}", delta="Refund", delta_color="off")
            else:
                st.metric("AMOUNT OWED", f"${owed:,.2f}", delta="Payment Due", delta_color="inverse")
        
        # ===== FORM 1040 LINE DETAILS =====
        st.subheader("📋 Form 1040 Line Details")
        
        lines = calc.get("form_1040_lines", {})
        
        # Create table
        line_data = []
        line_map = {
            "1": "Wages, salaries, tips",
            "7": "Total income",
            "11": "Adjusted Gross Income (AGI)",
            "12": "Standard deduction",
            "15": "Taxable income",
            "16": "Tax",
            "19": "Child tax credit (non-refundable)",
            "27": "Earned income credit (EITC)",
            "28": "Additional child tax credit",
            "24": "Total tax",
            "25a": "Federal income tax withheld",
            "31": "Total payments",
            "34": "Refund",
            "37": "Amount you owe"
        }
        
        for line_num, desc in line_map.items():
            if line_num in lines:
                amount = lines[line_num]
                if amount != 0 or line_num in ["12", "16", "24", "31", "34", "37"]:
                    line_data.append({
                        "Line": line_num,
                        "Description": desc,
                        "Amount": f"${amount:,.2f}"
                    })
        
        st.dataframe(pd.DataFrame(line_data), hide_index=True, use_container_width=True)
        
        # ===== DOWNLOAD SECTION =====
        st.subheader("📥 Download Form 1040")
        
        if MODULES_AVAILABLE and st.session_state.form_1040_path and os.path.exists(st.session_state.form_1040_path):
            try:
                # Read PDF
                with open(st.session_state.form_1040_path, "rb") as f:
                    pdf_bytes = f.read()
                
                # Download buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        label="📄 Download Form 1040 (PDF)",
                        data=pdf_bytes,
                        file_name=f"Form_1040_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                
                with col2:
                    # Create complete package
                    try:
                        filler = Form1040PDF()
                        package_path = filler.create_filing_package(
                            st.session_state.tax_calculations,
                            st.session_state.extracted_data
                        )
                        
                        with open(package_path, "rb") as f:
                            package_bytes = f.read()
                        
                        st.download_button(
                            label="📦 Complete Filing Package",
                            data=package_bytes,
                            file_name=f"Tax_Package_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        # Clean up
                        os.remove(package_path)
                    except Exception as e:
                        st.info("Simple PDF only available")
                
                with col3:
                    # JSON data
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
                
                # Clean up main PDF
                os.remove(st.session_state.form_1040_path)
                
                # Preview
                with st.expander("👀 What's in the Form 1040 PDF?", expanded=True):
                    st.markdown(f"""
                    ### Your Form 1040 includes:
                    
                    **Taxpayer Information:**
                    - Name: **{name}**
                    - SSN: **{ssn}**
                    - Filing Status: **{status_display}**
                    - Dependents: **{deps}**
                    
                    **Income & Deductions:**
                    - Wages: **${lines.get('1', 0):,.2f}**
                    - Standard Deduction: **${lines.get('12', 0):,.2f}**
                    - Taxable Income: **${lines.get('15', 0):,.2f}**
                    
                    **Tax & Credits:**
                    - Tax: **${lines.get('16', 0):,.2f}**
                    - Child Tax Credit: **${lines.get('19', 0):,.2f}**
                    - Earned Income Credit: **${lines.get('27', 0):,.2f}**
                    - Additional Child Tax Credit: **${lines.get('28', 0):,.2f}**
                    
                    **Result:**
                    - Total Payments: **${lines.get('31', 0):,.2f}**
                    - ✅ **REFUND: ${refund:,.2f}** (highlighted in green)
                    
                    **Ready to File:**
                    - Signature section with today's date
                    - Filing instructions
                    - Professional formatting
                    """)
                    
            except Exception as e:
                st.error(f"Error reading PDF: {str(e)}")
        else:
            st.info("Generate Form 1040 in Manual Entry or PDF Upload tab first")
        
        # ===== FILING INSTRUCTIONS =====
        with st.expander("📋 Filing Instructions", expanded=True):
            st.markdown(f"""
            **Before Filing (for {name}):**
            
            1. **Review** all information above
            2. **Sign and date** the Form 1040 on page 2
            3. **Attach** required documents:
               - Copy B of all W-2 forms
               - Forms 1099 if tax was withheld
               - Any schedules mentioned
            
            **Mailing Address:**
            Find your state's IRS address: [Where to File Paper Returns](https://www.irs.gov/filing/where-to-file-paper-tax-returns-with-or-without-a-payment)
            
            **Important Numbers to Record:**
            - Adjusted Gross Income (AGI): **${calc.get('agi', 0):,.2f}**
            - Total Tax: **${calc.get('total_tax', 0):,.2f}**
            - Refund Amount: **${refund:,.2f}**
            
            **Deadline:** April 15, 2026
            
            **Need Help?**
            - IRS Website: [IRS.gov](https://www.irs.gov)
            - IRS Phone: 1-800-829-1040
            - Taxpayer Assistance Centers: [Find Local Help](https://www.irs.gov/help/contact-us)
            """)

# Footer
st.markdown("---")
st.caption(f"IRS 2025 Tax Rules • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Debug info
with st.sidebar.expander("🔧 Debug Info"):
    st.write("Modules available:", MODULES_AVAILABLE)
    if st.session_state.extracted_data:
        st.write("Extracted data keys:", list(st.session_state.extracted_data.keys()))
    if st.session_state.tax_calculations:
        st.write("Has form lines:", "form_1040_lines" in st.session_state.tax_calculations)
    st.write("Prefilled data type:", type(st.session_state.prefilled_data))
    st.write("Prefilled data:", st.session_state.prefilled_data)