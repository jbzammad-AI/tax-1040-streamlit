import os
import tempfile
from datetime import datetime
from typing import Dict, Any
from fpdf import FPDF
import json

class Form1040PDF:
    """Creates a professional-looking Form 1040 PDF."""
    
    def _sanitize_text(self, text):
        """Replace unsupported Unicode characters with ASCII equivalents."""
        if not isinstance(text, str):
            return text
        
        replacements = {
            "—": "-",    # em-dash to hyphen
            "–": "-",    # en-dash to hyphen
            "’": "'",    # curly apostrophe
            "‘": "'",    # opening curly quote
            "“": '"',    # opening double curly quote
            "”": '"',    # closing double curly quote
            "•": "*",    # bullet point
            "…": "...",  # ellipsis
            "°": "deg",  # degree symbol
            "±": "+/-",  # plus-minus
            "€": "EUR",  # Euro symbol
            "£": "GBP",  # Pound symbol
            "¥": "JPY",  # Yen symbol
            "©": "(c)",  # Copyright
            "®": "(R)",  # Registered trademark
            "™": "(TM)", # Trademark
            "☑": "[X]",  # Checked box
            "☐": "[ ]",  # Unchecked box
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def create_form_1040(self, tax_data: Dict[str, Any], 
                        extracted_data: Dict[str, Any]) -> str:
        """
        Create a complete, professional Form 1040 PDF.
        
        Returns:
            Path to generated PDF file
        """
        print("\n" + "="*50)
        print("GENERATING FORM 1040")
        print("="*50)
        
        # Print status and results
        self._print_tax_summary(tax_data, extracted_data)
        
        # Create PDF
        pdf = FPDF(orientation='P', unit='mm', format='Letter')
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # ===== PAGE 1 =====
        pdf.add_page()
        
        # Header
        self._add_header(pdf)
        
        # Filing Status Section
        self._add_filing_status(pdf, tax_data)
        
        # Personal Information
        self._add_personal_info(pdf, extracted_data)
        
        # Income Section
        self._add_income_section(pdf, tax_data)
        
        # Adjusted Gross Income
        self._add_agi_section(pdf, tax_data)
        
        # Deductions
        self._add_deductions_section(pdf, tax_data)
        
        # Taxable Income and Tax
        self._add_tax_section(pdf, tax_data)
        
        # ===== PAGE 2 =====
        pdf.add_page()
        
        # Page 2 Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, '2025 Form 1040 (Page 2)', 0, 1, 'C')
        pdf.ln(5)
        
        # Credits
        self._add_credits_section(pdf, tax_data)
        
        # Payments
        self._add_payments_section(pdf, tax_data)
        
        # Refund or Amount You Owe
        self._add_refund_section(pdf, tax_data)
        
        # Third Party Designee
        self._add_third_party_section(pdf)
        
        # Signatures
        self._add_signature_section(pdf)
        
        # Paid Preparer
        self._add_preparer_section(pdf)
        
        # Save PDF
        output_path = tempfile.mktemp(suffix='_Form1040.pdf')
        pdf.output(output_path)
        
        print(f"\n✓ Form 1040 generated: {output_path}")
        print("="*50)
        return output_path
    
    def _print_tax_summary(self, tax_data, extracted_data):
        """Print tax calculation summary to console."""
        print(f"\n📊 TAX CALCULATION SUMMARY")
        print(f"   {'─'*40}")
        
        # Personal Info
        name = extracted_data.get("taxpayer_name", "N/A")
        ssn = extracted_data.get("taxpayer_ssn", "N/A")
        status = tax_data.get("filing_status", "single").replace("_", " ").title()
        dependents = extracted_data.get("dependent_count", 0)
        
        print(f"   Taxpayer: {name}")
        print(f"   SSN: {ssn}")
        print(f"   Filing Status: {status}")
        print(f"   Dependents: {dependents}")
        print(f"   {'─'*40}")
        
        # Income
        lines = tax_data.get("form_1040_lines", {})
        print(f"   INCOME:")
        print(f"     Wages: ${lines.get('1', 0):,.2f}")
        print(f"     Total Income: ${lines.get('7', 0):,.2f}")
        print(f"     AGI: ${lines.get('11', 0):,.2f}")
        print(f"   {'─'*40}")
        
        # Deductions & Taxable Income
        print(f"   DEDUCTIONS & TAX:")
        print(f"     Standard Deduction: ${lines.get('12', 0):,.2f}")
        print(f"     Taxable Income: ${lines.get('15', 0):,.2f}")
        print(f"     Tax: ${lines.get('16', 0):,.2f}")
        print(f"   {'─'*40}")
        
        # Credits
        print(f"   CREDITS:")
        print(f"     Child Tax Credit: ${lines.get('19', 0):,.2f}")
        print(f"     EITC: ${lines.get('27', 0):,.2f}")
        print(f"     Additional Child Tax Credit: ${lines.get('28', 0):,.2f}")
        print(f"     Total Tax: ${lines.get('24', 0):,.2f}")
        print(f"   {'─'*40}")
        
        # Payments & Results
        print(f"   PAYMENTS:")
        print(f"     Federal Tax Withheld: ${lines.get('25a', 0):,.2f}")
        print(f"     Total Payments: ${lines.get('31', 0):,.2f}")
        print(f"   {'─'*40}")
        
        # Final Result
        refund = tax_data.get("refund", 0)
        owed = tax_data.get("amount_owed", 0)
        
        if refund > 0:
            print(f"   🎉 RESULT: REFUND of ${refund:,.2f}")
            print(f"     Line 34: ${lines.get('34', 0):,.2f}")
        else:
            print(f"   💰 RESULT: AMOUNT OWED ${owed:,.2f}")
            print(f"     Line 37: ${lines.get('37', 0):,.2f}")
        
        print(f"   {'─'*40}")
    
    def _add_header(self, pdf):
        """Add Form 1040 header."""
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, 'Form 1040', 0, 1, 'C')
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, 'U.S. Individual Income Tax Return', 0, 1, 'C')
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 6, 'Department of the Treasury - Internal Revenue Service (99)', 0, 1, 'C')
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, '2025', 0, 1, 'C')
        pdf.ln(5)
        
        # OMB No.
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 5, 'OMB No. 1545-0074', 0, 1, 'R')
        
        # IRS Use Only
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(40, 6, 'IRS Use Only-Do not write or staple in this space.', 1, 1, 'C', fill=True)
        pdf.ln(2)
    
    def _add_filing_status(self, pdf, tax_data):
        """Add filing status checkboxes."""
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'Filing Status', 0, 1)
        
        status = tax_data.get("filing_status", "single")
        status_options = [
            ("single", "1   Single"),
            ("married_joint", "2   Married filing jointly (even if only one had income)"),
            ("married_separate", "3   Married filing separately"),
            ("head_of_household", "4   Head of household (see instructions)"),
            ("surviving_spouse", "5   Qualifying surviving spouse")
        ]
        
        pdf.set_font('Arial', '', 10)
        for status_key, label in status_options:
            checkbox = "[X]" if status_key == status else "[ ]"  # Changed from Unicode to ASCII
            pdf.cell(10, 6, checkbox, 0, 0)
            pdf.cell(0, 6, label, 0, 1)
            pdf.ln(1)
        
        pdf.ln(5)
    
    def _add_personal_info(self, pdf, extracted_data):
        """Add taxpayer personal information."""
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'Personal Information', 0, 1)
        
        # Name and SSN
        pdf.set_font('Arial', '', 10)
        
        # First Name
        pdf.cell(30, 6, 'First name and initial', 0, 0)
        name = extracted_data.get("taxpayer_name", "")
        # Sanitize name
        name = self._sanitize_text(name)
        if " " in name:
            first_part = name.split(" ")[0]
            pdf.cell(50, 6, first_part, 'B', 0)
        else:
            pdf.cell(50, 6, name, 'B', 0)
        
        pdf.cell(20, 6, '', 0, 0)
        
        # Last Name
        pdf.cell(25, 6, 'Last name', 0, 0)
        if " " in name:
            last_part = name.split(" ")[-1]
            pdf.cell(50, 6, last_part, 'B', 1)
        else:
            pdf.cell(50, 6, '', 'B', 1)
        
        pdf.ln(2)
        
        # SSN
        pdf.cell(45, 6, 'Your social security number', 0, 0)
        ssn = extracted_data.get("taxpayer_ssn", "___-__-____")
        ssn = self._sanitize_text(ssn)
        pdf.cell(40, 6, ssn, 'B', 0)
        
        pdf.cell(20, 6, '', 0, 0)
        
        # Spouse SSN
        pdf.cell(60, 6, "Spouse's social security number", 0, 0)
        pdf.cell(0, 6, '', 'B', 1)
        
        pdf.ln(2)
        
        # Address
        pdf.cell(25, 6, 'Home address', 0, 0)
        pdf.cell(0, 6, '', 'B', 1)
        
        pdf.ln(2)
        
        pdf.cell(60, 6, 'City, town or post office, state, and ZIP code', 0, 0)
        pdf.cell(0, 6, '', 'B', 1)
        
        pdf.ln(10)
    
    def _add_income_section(self, pdf, tax_data):
        """Add income section lines."""
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Income', 0, 1)
        
        lines = tax_data.get("form_1040_lines", {})
        
        # Line 1: Wages
        self._add_form_line(pdf, "1", "Wages, salaries, tips, etc.", lines.get("1", 0))
        
        # Line 1b: Federal income tax withheld
        self._add_form_line(pdf, "1b", "Federal income tax withheld", lines.get("25a", 0))
        
        # Line 2b: Taxable interest
        self._add_form_line(pdf, "2b", "Taxable interest", lines.get("2b", 0))
        
        # Line 3b: Qualified dividends
        self._add_form_line(pdf, "3b", "Qualified dividends", lines.get("3b", 0))
        
        # Line 7: Total income
        pdf.set_font('Arial', 'B', 10)
        self._add_form_line(pdf, "7", "Add lines 1 through 6b", lines.get("7", 0))
        
        pdf.ln(5)
    
    def _add_agi_section(self, pdf, tax_data):
        """Add Adjusted Gross Income section."""
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Adjusted Gross Income', 0, 1)
        
        lines = tax_data.get("form_1040_lines", {})
        
        # Line 11: AGI
        pdf.set_font('Arial', 'B', 10)
        self._add_form_line(pdf, "11", "Adjusted gross income (AGI)", lines.get("11", 0))
        
        pdf.ln(5)
    
    def _add_deductions_section(self, pdf, tax_data):
        """Add deductions section."""
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Deductions', 0, 1)
        
        lines = tax_data.get("form_1040_lines", {})
        
        # Standard deduction checkbox
        pdf.set_font('Arial', '', 10)
        pdf.cell(10, 6, "[X]", 0, 0)  # Changed from Unicode
        pdf.cell(40, 6, "Standard deduction", 0, 0)
        pdf.cell(100, 6, "", 0, 0)
        pdf.cell(30, 6, f"${lines.get('12', 0):,.2f}", 0, 1, 'R')
        
        pdf.ln(2)
        
        # Or itemized deductions checkbox
        pdf.cell(10, 6, "[ ]", 0, 0)  # Changed from Unicode
        pdf.cell(60, 6, "Itemized deductions (from Schedule A)", 0, 1)
        
        pdf.ln(5)
        
        # Line 15: Taxable income
        pdf.set_font('Arial', 'B', 10)
        self._add_form_line(pdf, "15", "Taxable income", lines.get("15", 0))
        
        pdf.ln(10)
    
    def _add_tax_section(self, pdf, tax_data):
        """Add tax calculation section."""
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Tax', 0, 1)
        
        lines = tax_data.get("form_1040_lines", {})
        
        # Line 16: Tax
        self._add_form_line(pdf, "16", "Tax", lines.get("16", 0))
        
        pdf.ln(5)
    
    def _add_credits_section(self, pdf, tax_data):
        """Add credits section on page 2."""
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Credits', 0, 1)
        
        lines = tax_data.get("form_1040_lines", {})
        
        # Line 19: Child tax credit
        self._add_form_line(pdf, "19", "Child tax credit", lines.get("19", 0))
        
        # Line 27: Earned income credit (EITC)
        self._add_form_line(pdf, "27", "Earned income credit (EITC)", lines.get("27", 0))
        
        # Line 28: Additional child tax credit
        if lines.get("28", 0) > 0:
            self._add_form_line(pdf, "28", "Additional child tax credit", lines.get("28", 0))
        
        pdf.ln(5)
        
        # Line 24: Total tax
        pdf.set_font('Arial', 'B', 10)
        self._add_form_line(pdf, "24", "Total tax", lines.get("24", 0))
        
        pdf.ln(10)
    
    def _add_payments_section(self, pdf, tax_data):
        """Add payments section."""
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Payments', 0, 1)
        
        lines = tax_data.get("form_1040_lines", {})
        
        # Line 25a: Federal income tax withheld
        self._add_form_line(pdf, "25a", "Federal income tax withheld", lines.get("25a", 0))
        
        pdf.ln(5)
        
        # Line 31: Total payments
        pdf.set_font('Arial', 'B', 10)
        self._add_form_line(pdf, "31", "Total payments", lines.get("31", 0))
        
        pdf.ln(10)
    
    def _add_refund_section(self, pdf, tax_data):
        """Add refund or amount owed section."""
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Refund or Amount You Owe', 0, 1)
        
        lines = tax_data.get("form_1040_lines", {})
        refund = tax_data.get("refund", 0)
        owed = tax_data.get("amount_owed", 0)
        
        if refund > 0:
            # Line 34: Refund
            pdf.set_text_color(0, 128, 0)  # Green for refund
            pdf.set_font('Arial', 'B', 11)
            self._add_form_line(pdf, "34", "REFUND", lines.get("34", 0))
            pdf.set_text_color(0, 0, 0)  # Reset to black
            
            # Line 37: Amount you owe (0)
            pdf.set_font('Arial', '', 10)
            self._add_form_line(pdf, "37", "Amount you owe", 0)
        else:
            # Line 34: Refund (0)
            pdf.set_font('Arial', '', 10)
            self._add_form_line(pdf, "34", "Refund", 0)
            
            # Line 37: Amount you owe
            pdf.set_text_color(255, 0, 0)  # Red for amount owed
            pdf.set_font('Arial', 'B', 11)
            self._add_form_line(pdf, "37", "AMOUNT YOU OWE", lines.get("37", 0))
            pdf.set_text_color(0, 0, 0)  # Reset to black
        
        pdf.ln(15)
    
    def _add_third_party_section(self, pdf):
        """Add third party designee section."""
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'Third Party Designee', 0, 1)
        pdf.set_font('Arial', '', 9)
        pdf.multi_cell(0, 5, "Do you want to allow another person to discuss this return with the IRS? See instructions.")
        
        pdf.ln(2)
        pdf.cell(10, 6, "[ ]", 0, 0)  # Changed from Unicode
        pdf.cell(0, 6, "Yes. Complete below.", 0, 1)
        
        pdf.ln(2)
        pdf.cell(10, 6, "[X]", 0, 0)  # Changed from Unicode
        pdf.cell(0, 6, "No.", 0, 1)
        
        pdf.ln(10)
    
    def _add_signature_section(self, pdf):
        """Add signature section."""
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'Sign Here', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, "Under penalties of perjury, I declare that I have examined this return and accompanying schedules and statements, and to the best of my knowledge and belief, they are true, correct, and complete.")
        
        pdf.ln(10)
        
        # Your signature
        pdf.cell(60, 8, "Your signature", 0, 0)
        pdf.cell(40, 8, "", 'B', 0)
        pdf.cell(20, 8, "Date", 0, 0)
        pdf.cell(30, 8, datetime.now().strftime("%m/%d/%Y"), 'B', 0)
        pdf.cell(20, 8, "Your occupation", 0, 0)
        pdf.cell(0, 8, "", 'B', 1)
        
        pdf.ln(5)
        
        # Spouse signature (if applicable)
        pdf.cell(60, 8, "Spouse's signature", 0, 0)
        pdf.cell(40, 8, "", 'B', 0)
        pdf.cell(20, 8, "Date", 0, 0)
        pdf.cell(30, 8, "", 'B', 0)
        pdf.cell(20, 8, "Spouse's occupation", 0, 0)
        pdf.cell(0, 8, "", 'B', 1)
        
        pdf.ln(15)
    
    def _add_preparer_section(self, pdf):
        """Add paid preparer section."""
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'Paid Preparer Use Only', 0, 1)
        
        pdf.set_font('Arial', '', 9)
        pdf.cell(40, 6, "Preparer's name", 0, 0)
        pdf.cell(0, 6, "", 'B', 1)
        
        pdf.cell(40, 6, "Preparer's signature", 0, 0)
        pdf.cell(0, 6, "", 'B', 1)
        
        pdf.cell(40, 6, "Date", 0, 0)
        pdf.cell(30, 6, "", 'B', 0)
        pdf.cell(30, 6, "PTIN", 0, 0)
        pdf.cell(0, 6, "", 'B', 1)
        
        pdf.cell(40, 6, "Firm's name", 0, 0)
        pdf.cell(0, 6, "", 'B', 1)
        
        pdf.cell(40, 6, "EIN", 0, 0)
        pdf.cell(0, 6, "", 'B', 1)
        
        pdf.cell(40, 6, "Phone no.", 0, 0)
        pdf.cell(0, 6, "", 'B', 1)
    
    def _add_form_line(self, pdf, line_num, description, amount):
        """Helper to add a form line with number, description, and amount."""
        # Line number
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(10, 6, line_num, 0, 0)
        
        # Description
        pdf.set_font('Arial', '', 10)
        pdf.cell(100, 6, description, 0, 0)
        
        # Amount (right aligned)
        pdf.cell(30, 6, f"${amount:,.2f}", 0, 1, 'R')
    
    def create_filing_package(self, tax_data: Dict[str, Any], 
                            extracted_data: Dict[str, Any]) -> str:
        """Create complete filing package with instructions."""
        print("\n📦 Creating complete filing package...")
        
        # Create Form 1040
        form_path = self.create_form_1040(tax_data, extracted_data)
        
        # Create instructions
        instructions_path = self._create_instructions_pdf(tax_data, extracted_data)
        
        print(f"✓ Filing package created")
        
        # Merge (for now, just return form)
        return form_path
    
    def _create_instructions_pdf(self, tax_data, extracted_data):
        """Create filing instructions (simplified for now)."""
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Form 1040 Filing Instructions', 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Important Filing Information', 0, 1)
        
        instructions = [
            "1. Review all information on Form 1040 for accuracy",
            "2. Sign and date the form on page 2",
            "3. Attach all required documents:",
            "   * Copy B of all W-2 forms",
            "   * Forms 1099 if tax was withheld",
            "   * Any schedules referenced",
            "4. Mail to the correct IRS address for your state",
            "5. Keep copies for at least 3 years",
            "",
            f"Filing Deadline: April 15, 2026",
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            "",
            "Need help? Visit IRS.gov or call 1-800-829-1040"
        ]
        
        pdf.set_font('Arial', '', 11)
        for line in instructions:
            if line.strip():
                pdf.multi_cell(0, 6, line)
                pdf.ln(2)
        
        # Save
        output_path = tempfile.mktemp(suffix='_Instructions.pdf')
        pdf.output(output_path)
        
        return output_path