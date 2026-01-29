import traceback

print("Testing imports...")

try:
    import streamlit
    print("✅ streamlit")
except:
    print("❌ streamlit")

try:
    import pandas
    print("✅ pandas")
except:
    print("❌ pandas")

try:
    from document_processor import PDFProcessor
    print("✅ PDFProcessor")
except Exception as e:
    print(f"❌ PDFProcessor: {e}")

try:
    from irs_rules_engine import IRSTaxEngine
    print("✅ IRSTaxEngine")
except Exception as e:
    print(f"❌ IRSTaxEngine: {e}")

try:
    from pdf_filler import PDFFiller
    print("✅ PDFFiller")
except:
    try:
        from pdf_filler import Form1040PDF
        print("✅ Form1040PDF")
    except Exception as e:
        print(f"❌ PDF filler: {e}")

print("\nAll imports tested.")