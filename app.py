import streamlit as st
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import io

# 1. إعداد واجهة التطبيق
st.set_page_config(page_title="مساعد المحاسب الذكي - الجزائر", page_icon="🧾", layout="centered")

st.title("🧾 نظام أتمتة فواتير الشركات الجزائرية")
st.write("ارفع فواتير الموردين (PDF أو صورة) لاستخراج البيانات آلياً وتصديرها لبرامج المحاسبة (مثل PC COMPTA).")

st.divider()

# 2. إعدادات المفاتيح (أضفناها في الواجهة لتسهيل لصقها من الهاتف)
with st.expander("⚙️ إعدادات الربط مع Azure (مطلوب مرة واحدة)"):
    endpoint = st.text_input("رابط Azure (Endpoint):", type="password")
    key = st.text_input("مفتاح Azure (API Key):", type="password")

st.divider()

# 3. رفع الفاتورة
uploaded_file = st.file_uploader("📂 قم برفع الفاتورة هنا (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])

# 4. معالجة الفاتورة واستخراج البيانات
if uploaded_file is not None and st.button("🚀 استخراج البيانات بالذكاء الاصطناعي"):
    if not endpoint or not key:
        st.error("⚠️ الرجاء إدخال رابط ومفتاح Azure في الإعدادات أعلاه أولاً.")
    else:
        with st.spinner("⏳ جاري تحليل الفاتورة وقراءة الأرقام..."):
            try:
                # الاتصال بخوادم الذكاء الاصطناعي
                client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
                file_bytes = uploaded_file.read()
                
                # تحليل المستند
                poller = client.begin_analyze_document("prebuilt-invoice", document=file_bytes)
                invoices = poller.result()
                
                data = []
                for invoice in invoices.documents:
                    # استخراج الحقول بأمان
                    vendor_name = invoice.fields.get("VendorName").value if invoice.fields.get("VendorName") else "غير متوفر"
                    vendor_tax_id = invoice.fields.get("VendorTaxId").value if invoice.fields.get("VendorTaxId") else "غير متوفر"
                    sub_total = invoice.fields.get("SubTotal").value.amount if invoice.fields.get("SubTotal") else 0.0
                    total_tax = invoice.fields.get("TotalTax").value.amount if invoice.fields.get("TotalTax") else 0.0
                    invoice_total = invoice.fields.get("InvoiceTotal").value.amount if invoice.fields.get("InvoiceTotal") else 0.0
                    
                    data.append({
                        "اسم المورد": vendor_name,
                        "الرقم الجبائي (NIF)": vendor_tax_id,
                        "المبلغ الصافي (HT)": sub_total,
                        "الضريبة (TVA)": total_tax,
                        "المبلغ الإجمالي (TTC)": invoice_total
                    })
                
                # 5. عرض البيانات وإتاحة التصدير
                df = pd.DataFrame(data)
                st.success("✅ تم استخراج البيانات بنجاح!")
                
                # عرض البيانات في جدول قابل للتعديل (Data Editor)
                st.write("راجع البيانات وصححها إذا لزم الأمر قبل التصدير:")
                edited_df = st.data_editor(df, use_container_width=True)
                
                # تحويل البيانات إلى ملف CSV للتصدير
                csv = edited_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="💾 تحميل كملف CSV (متوافق مع برامج المحاسبة)",
                    data=csv,
                    file_name="invoices_export.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء المعالجة: {e}")
