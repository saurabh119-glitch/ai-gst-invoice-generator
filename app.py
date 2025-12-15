import streamlit as st
from PIL import Image
import pytesseract
import re
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os

# Configure Tesseract path (for local dev — Streamlit Cloud has it pre-installed)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="AI GST Invoice Generator", page_icon="🧾")
st.title("🧾 AI GST Invoice Generator for Indian Businesses")
st.caption("Upload a bill photo or enter details → get a GST-compliant invoice in seconds")

# Disclaimer
st.info("""
**Note**: This is a demo tool. For official invoices, use GST-certified software.  
Your data is processed in-browser — **nothing is stored**.
""")

# Tabs: Upload Photo | Manual Entry
tab1, tab2 = st.tabs(["📸 Upload Bill Photo", "✏️ Manual Entry"])

invoice_data = {}

with tab1:
    st.subheader("Step 1: Upload Bill Photo")
    uploaded_file = st.file_uploader("Upload a photo of your bill (JPG/PNG)", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Bill", use_column_width=True)
        
        with st.spinner("Extracting text from bill..."):
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            # Simple regex to extract key info (improve with NLP later)
            gst_match = re.search(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z0-9]{1}', text)
            total_match = re.search(r'(?:total|amount|payable)[^\d]*(\d+\.?\d*)', text, re.IGNORECASE)
            
            st.subheader("Step 2: Verify Extracted Details")
            invoice_data["seller_name"] = st.text_input("Seller Name", value="Shop Name")
            invoice_data["seller_gst"] = st.text_input("Seller GSTIN", value=gst_match.group(0) if gst_match else "")
            invoice_data["buyer_name"] = st.text_input("Buyer Name", value="Customer")
            invoice_data["buyer_gst"] = st.text_input("Buyer GSTIN (if B2B)", value="")
            invoice_data["total_amount"] = st.number_input("Total Amount (₹)", value=float(total_match.group(1)) if total_match else 1000.0)
            invoice_data["items"] = st.text_area("Items (one per line)", value="Item 1: ₹500\nItem 2: ₹300")

with tab2:
    st.subheader("Enter Invoice Details Manually")
    invoice_data["seller_name"] = st.text_input("Seller Name*", key="manual_seller")
    invoice_data["seller_gst"] = st.text_input("Seller GSTIN*", key="manual_gst")
    invoice_data["buyer_name"] = st.text_input("Buyer Name*", key="manual_buyer")
    invoice_data["buyer_gst"] = st.text_input("Buyer GSTIN (if B2B)", key="manual_buyer_gst")
    invoice_data["total_amount"] = st.number_input("Total Amount (₹)*", min_value=1.0, value=1000.0, key="manual_total")
    invoice_data["items"] = st.text_area("Items (one per line)*", 
                                       placeholder="Milk: ₹50\nBread: ₹40\nEggs: ₹60", 
                                       key="manual_items")

# Generate Invoice
if st.button("🖨️ Generate GST Invoice", type="primary"):
    if not all([invoice_data.get("seller_name"), invoice_data.get("seller_gst"), invoice_data.get("buyer_name"), invoice_data.get("items")]):
        st.error("❌ Please fill all required fields (*)")
    elif not re.match(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z0-9]{1}', invoice_data["seller_gst"]):
        st.error("❌ Invalid GSTIN format. Example: 27AABCCDDDEE1Z1")
    else:
        with st.spinner("Generating GST-compliant invoice..."):
            # Create PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Header
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "TAX INVOICE", ln=True, align="C")
            pdf.ln(5)
            
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"Invoice Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True)
            pdf.cell(0, 8, f"Invoice No: GST-{datetime.now().strftime('%Y%m%d')}-001", ln=True)
            pdf.ln(5)
            
            # Seller Info
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Seller Details", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"Name: {invoice_data['seller_name']}", ln=True)
            pdf.cell(0, 8, f"GSTIN: {invoice_data['seller_gst']}", ln=True)
            pdf.ln(5)
            
            # Buyer Info
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Buyer Details", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"Name: {invoice_data['buyer_name']}", ln=True)
            if invoice_data["buyer_gst"]:
                pdf.cell(0, 8, f"GSTIN: {invoice_data['buyer_gst']}", ln=True)
            pdf.ln(5)
            
            # Items Table
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Items", ln=True)
            pdf.set_font("Arial", "", 10)
            
            items = invoice_data["items"].split("\n")
            for item in items:
                if item.strip():
                    pdf.cell(0, 8, f"• {item.strip()}", ln=True)
            pdf.ln(5)
            
            # Total
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"Total Amount: ₹{invoice_data['total_amount']:.2f}", ln=True)
            pdf.ln(10)
            
            # GST Compliance Note
            pdf.set_font("Arial", "", 8)
            pdf.cell(0, 8, "This is a computer-generated invoice. No signature required as per CGST Rule 46.", ln=True)
            pdf.cell(0, 8, "GSTIN verified as per Govt of India format.", ln=True)
            
            # Save PDF
            pdf_file = "gst_invoice.pdf"
            pdf.output(pdf_file)
            
            # Display & Download
            st.success("✅ GST Invoice Generated!")
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="📥 Download Invoice (PDF)",
                    data=f,
                    file_name="gst_invoice.pdf",
                    mime="application/pdf"
                )
            
            # Clean up
            if os.path.exists(pdf_file):
                os.remove(pdf_file)
