from typing import Dict, Any
import math

class IRSTaxEngine:
    """Fixed IRS tax calculator with proper 2025 rules and refund logic."""
    
    # 2025 TAX CONSTANTS
    STANDARD_DEDUCTIONS = {
        "single": 14600.00,
        "married_joint": 29200.00,
        "head_of_household": 21900.00,
        "married_separate": 14600.00,
        "surviving_spouse": 29200.00
    }
    
    # 2025 TAX BRACKETS (Head of Household)
    TAX_BRACKETS_HOH = [
        (0, 11600, 0.10),      # 10%
        (11600, 47150, 0.12),  # 12%
        (47150, 100525, 0.22), # 22%
        (100525, 191950, 0.24), # 24%
        (191950, 243725, 0.32), # 32%
        (243725, 609350, 0.35), # 35%
        (609350, float('inf'), 0.37) # 37%
    ]
    
    # 2025 CREDITS
    CHILD_TAX_CREDIT = 2000.00  # per child
    ADDITIONAL_CHILD_TAX_CREDIT_MAX = 1600.00  # refundable portion per child
    EITC_2025 = {  # Earned Income Tax Credit
        0: {"max_income": 17900, "max_credit": 632},
        1: {"max_income": 47900, "max_credit": 4257},
        2: {"max_income": 53900, "max_credit": 7043},
        3: {"max_income": 57900, "max_credit": 7931}
    }
    
    def __init__(self):
        self.filing_status = "single"
    
    def calculate_tax(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate tax with proper IRS 2025 rules and refund logic."""
        print(f"\n=== CALCULATING TAX FOR: {self.filing_status} ===")
        
        # Get data
        wages = extracted_data.get("wages", 0)
        federal_withheld = extracted_data.get("federal_tax_withheld", 0)
        dependents = extracted_data.get("dependent_count", 0)
        
        print(f"Wages: ${wages:,.2f}")
        print(f"Dependents: {dependents}")
        print(f"Federal Withheld: ${federal_withheld:,.2f}")
        
        # ===== 1. STANDARD DEDUCTION =====
        deduction = self.STANDARD_DEDUCTIONS.get(self.filing_status, 14600)
        print(f"Standard Deduction ({self.filing_status}): ${deduction:,.2f}")
        
        # ===== 2. TAXABLE INCOME =====
        taxable_income = max(0, wages - deduction)
        print(f"Taxable Income: ${taxable_income:,.2f}")
        
        # ===== 3. TAX CALCULATION =====
        if self.filing_status == "head_of_household":
            tax = self._calculate_tax_brackets(taxable_income, self.TAX_BRACKETS_HOH)
        else:
            tax = self._calculate_tax_brackets(taxable_income, self.TAX_BRACKETS_HOH)
        
        print(f"Tax Before Credits: ${tax:,.2f}")
        
        # ===== 4. CREDITS CALCULATION =====
        # Total Child Tax Credit available
        total_child_credit = self.CHILD_TAX_CREDIT * dependents
        
        # Non-refundable portion (can only offset tax)
        nonrefundable_child_credit = min(total_child_credit, tax)
        
        # Refundable portion (Additional Child Tax Credit)
        remaining_child_credit = total_child_credit - nonrefundable_child_credit
        additional_child_credit = min(remaining_child_credit, self.ADDITIONAL_CHILD_TAX_CREDIT_MAX * dependents)
        
        # Earned Income Credit (always refundable)
        eitc = self._calculate_eitc(wages, dependents)
        
        print(f"Total Child Tax Credit: ${total_child_credit:,.2f}")
        print(f"Non-refundable Child Credit: ${nonrefundable_child_credit:,.2f}")
        print(f"Additional Child Tax Credit (refundable): ${additional_child_credit:,.2f}")
        print(f"Earned Income Credit: ${eitc:,.2f}")
        
        # ===== 5. TAX AFTER CREDITS =====
        tax_after_nonrefundable = tax - nonrefundable_child_credit
        tax_after_all = max(0, tax_after_nonrefundable)  # Can't go negative with non-refundable credits
        
        print(f"Tax After Non-refundable Credits: ${tax_after_all:,.2f}")
        
        # ===== 6. REFUND CALCULATION =====
        # Refundable credits (can create refund even with $0 tax)
        total_refundable_credits = additional_child_credit + eitc + federal_withheld
        
        # If tax_after_all is $0, all refundable credits become refund
        if tax_after_all == 0:
            refund = total_refundable_credits
            amount_owed = 0
        else:
            # If there's still tax, refundable credits offset it first
            refund_from_credits = max(0, total_refundable_credits - tax_after_all)
            amount_owed = max(0, tax_after_all - total_refundable_credits)
            refund = refund_from_credits
        
        print(f"\n=== FINAL RESULT ===")
        print(f"Total Refundable Amount: ${total_refundable_credits:,.2f}")
        print(f"Final Tax Liability: ${tax_after_all:,.2f}")
        
        if refund > 0:
            print(f"✅ REFUND: ${refund:,.2f}")
        else:
            print(f"⚠️ AMOUNT OWED: ${amount_owed:,.2f}")
        
        # ===== 7. FORM 1040 LINES =====
        form_lines = {
            "1": round(wages, 2),
            "2b": round(extracted_data.get("interest_income", 0), 2),
            "3b": round(extracted_data.get("dividends", 0), 2),
            "7": round(wages, 2),
            "11": round(wages, 2),  # AGI
            "12": round(deduction, 2),
            "15": round(taxable_income, 2),
            "16": round(tax, 2),
            "19": round(nonrefundable_child_credit, 2),  # Line 19: Child tax credit (non-refundable)
            # Line 27: Earned income credit (EITC)
            "27": round(eitc, 2),
            # Line 28: Additional child tax credit (refundable portion)
            "28": round(additional_child_credit, 2),
            "24": round(tax_after_all, 2),
            "25a": round(federal_withheld, 2),
            "31": round(federal_withheld + additional_child_credit + eitc, 2),  # Total payments
        }
        
        if refund > 0:
            form_lines["34"] = round(refund, 2)  # Line 34: Refund
            form_lines["37"] = 0
        else:
            form_lines["34"] = 0
            form_lines["37"] = round(amount_owed, 2)  # Line 37: Amount you owe
        
        print(f"\n=== CALCULATION COMPLETE ===")
        return {
            "total_income": wages,
            "agi": wages,
            "standard_deduction": deduction,
            "taxable_income": taxable_income,
            "tax_amount": tax,
            "total_credits": total_child_credit + eitc,
            "total_tax": tax_after_all,
            "total_payments": form_lines["31"],
            "refund": refund,
            "amount_owed": amount_owed,
            "form_1040_lines": form_lines,
            "filing_status": self.filing_status
        }
    
    def _calculate_tax_brackets(self, income: float, brackets: list) -> float:
        """Calculate tax using bracket system."""
        tax = 0.0
        prev_bracket = 0
        
        for bracket_min, bracket_max, rate in brackets:
            if income > bracket_min:
                taxable_in_bracket = min(income, bracket_max) - max(bracket_min, prev_bracket)
                tax += taxable_in_bracket * rate
                prev_bracket = bracket_max
            else:
                break
        
        return round(tax, 2)
    
    def _calculate_eitc(self, wages: float, dependents: int) -> float:
        """Calculate Earned Income Tax Credit for 2025."""
        if dependents > 3:
            dependents = 3
        
        eitc_info = self.EITC_2025.get(dependents, self.EITC_2025[0])
        
        if wages <= eitc_info["max_income"]:
            return eitc_info["max_credit"]
        else:
            # Simplified phase-out
            excess = wages - eitc_info["max_income"]
            phaseout_rate = 0.1598 if dependents > 0 else 0.0765
            credit = max(0, eitc_info["max_credit"] - (excess * phaseout_rate))
            return round(credit, 2)