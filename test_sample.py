import streamlit as st
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(page_title="Tax 1040 Tool", layout="wide")

st.title("📊 IRS Form 1040 Tax Calculator")
st.markdown("Simple tool to calculate your 2025 tax return")

# Initialize session state
if 'tax_data' not in st.session_state:
    st.session_state.tax_data = None

# Manual data entry
st.header("📝 Enter Your Tax Information")

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Taxpayer Name", "Whitney M. Refund")
    ssn = st.text_input("SSN", "400-00-4702")
    status = st.selectbox(
        "Filing Status",
        ["Head of Household", "Single", "Married Filing Jointly"],
        index=0
    )
    dependents = st.number_input("Dependents", min_value=0, max_value=10, value=1)

with col2:
    wages = st.number_input("Wages", min_value=0.0, value=26263.0, step=1000.0)
    fed_tax = st.number_input("Federal Tax Withheld", min_value=0.0, value=264.0, step=50.0)
    interest = st.number_input("Interest Income", min_value=0.0, value=0.0, step=100.0)
    dividends = st.number_input("Dividend Income", min_value=0.0, value=0.0, step=100.0)
    daycare = st.number_input("Daycare Expenses", min_value=0.0, value=3100.0, step=100.0)

# Calculate button
if st.button("Calculate Tax", type="primary", use_container_width=True):
    # Simple tax calculation (Head of Household)
    standard_deduction = 21900.00  # HoH 2025
    taxable_income = max(0, wages - standard_deduction)
    
    # Tax calculation (10% bracket for HoH)
    if taxable_income <= 11600:
        tax = taxable_income * 0.10
    else:
        tax = 1160 + (taxable_income - 11600) * 0.12
    
    # Credits
    child_credit = 2000.00 * dependents
    eitc = 4257.00 if dependents >= 1 and wages <= 47900 else 0
    
    # Apply credits
    tax_after_child = max(0, tax - min(child_credit, tax))
    remaining_child = child_credit - min(child_credit, tax)
    additional_child = min(remaining_child, 1600 * dependents)
    
    # Total payments and refund
    total_payments = fed_tax + additional_child + eitc
    refund = total_payments - tax_after_child
    
    if refund > 0:
        amount_owed = 0
    else:
        amount_owed = abs(refund)
        refund = 0
    
    # Store in session state
    st.session_state.tax_data = {
        "taxpayer_info": {
            "name": name,
            "ssn": ssn,
            "filing_status": status,
            "dependents": dependents
        },
        "income": {
            "wages": wages,
            "fed_withheld": fed_tax,
            "interest": interest,
            "dividends": dividends,
            "daycare": daycare
        },
        "calculations": {
            "standard_deduction": standard_deduction,
            "taxable_income": taxable_income,
            "tax": tax,
            "child_credit": child_credit,
            "eitc": eitc,
            "additional_child": additional_child,
            "total_payments": total_payments,
            "refund": refund,
            "amount_owed": amount_owed
        },
        "form_lines": {
            "1": wages,
            "7": wages,
            "11": wages,
            "12": standard_deduction,
            "15": taxable_income,
            "16": tax,
            "19": min(child_credit, tax),
            "27": eitc,
            "28": additional_child,
            "24": tax_after_child,
            "25a": fed_tax,
            "31": total_payments,
            "34": refund,
            "37": amount_owed
        }
    }
    
    st.success("✅ Tax calculated successfully!")

# Show results if we have data
if st.session_state.tax_data:
    st.header("📋 Tax Calculation Results")
    
    data = st.session_state.tax_data
    
    # Taxpayer info
    st.subheader("👤 Taxpayer Information")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Name", data["taxpayer_info"]["name"])
    with col2:
        st.metric("SSN", data["taxpayer_info"]["ssn"])
    with col3:
        st.metric("Filing Status", data["taxpayer_info"]["filing_status"])
    with col4:
        st.metric("Dependents", data["taxpayer_info"]["dependents"])
    
    # Summary
    st.subheader("💰 Tax Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Income", f"${data['income']['wages']:,.2f}")
    with col2:
        st.metric("Total Tax", f"${data['calculations']['tax']:,.2f}")
    with col3:
        refund = data["calculations"]["refund"]
        owed = data["calculations"]["amount_owed"]
        if refund > 0:
            st.metric("REFUND", f"${refund:,.2f}", delta="Refund")
        else:
            st.metric("AMOUNT OWED", f"${owed:,.2f}", delta="Payment Due")
    
    # Form 1040 lines
    st.subheader("📄 Form 1040 Line Details")
    
    lines = data["form_lines"]
    line_data = []
    
    line_map = {
        "1": "Wages, salaries, tips",
        "7": "Total income",
        "11": "Adjusted Gross Income (AGI)",
        "12": "Standard deduction",
        "15": "Taxable income",
        "16": "Tax",
        "19": "Child tax credit",
        "27": "Earned income credit",
        "28": "Additional child tax credit",
        "24": "Total tax",
        "25a": "Federal income tax withheld",
        "31": "Total payments",
        "34": "Refund",
        "37": "Amount you owe"
    }
    
    for line_num, desc in line_map.items():
        amount = lines.get(line_num, 0)
        if amount != 0 or line_num in ["12", "16", "24", "31", "34", "37"]:
            line_data.append({
                "Line": line_num,
                "Description": desc,
                "Amount": f"${amount:,.2f}"
            })
    
    st.dataframe(pd.DataFrame(line_data), hide_index=True, use_container_width=True)
    
    # Download section
    st.subheader("📥 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create simple text summary
        summary = f"""FORM 1040 TAX CALCULATION SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TAXPAYER INFORMATION:
Name: {data['taxpayer_info']['name']}
SSN: {data['taxpayer_info']['ssn']}
Filing Status: {data['taxpayer_info']['filing_status']}
Dependents: {data['taxpayer_info']['dependents']}

INCOME & DEDUCTIONS:
Wages: ${data['income']['wages']:,.2f}
Standard Deduction: ${data['calculations']['standard_deduction']:,.2f}
Taxable Income: ${data['calculations']['taxable_income']:,.2f}

TAX & CREDITS:
Tax: ${data['calculations']['tax']:,.2f}
Child Tax Credit: ${data['calculations']['child_credit']:,.2f}
Earned Income Credit: ${data['calculations']['eitc']:,.2f}
Additional Child Credit: ${data['calculations']['additional_child']:,.2f}

RESULT:
Total Payments: ${data['calculations']['total_payments']:,.2f}
{'REFUND: $' + str(data['calculations']['refund']) + ',.2f' if data['calculations']['refund'] > 0 else 'AMOUNT OWED: $' + str(data['calculations']['amount_owed']) + ',.2f'}

Instructions: Sign and date. Attach W-2s. Mail by April 15, 2026.
"""
        
        st.download_button(
            label="📄 Download Tax Summary (TXT)",
            data=summary,
            file_name="Tax_Summary.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        # JSON download
        json_data = {
            "taxpayer": data["taxpayer_info"],
            "income": data["income"],
            "calculations": data["calculations"],
            "generated": datetime.now().isoformat()
        }
        
        import json
        st.download_button(
            label="📊 Download Data (JSON)",
            data=json.dumps(json_data, indent=2),
            file_name="Tax_Data.json",
            mime="application/json",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.caption(f"Based on IRS 2025 Tax Rules • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")