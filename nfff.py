import streamlit as st
import re
from PyPDF2 import PdfReader

st.set_page_config(page_title="Compliance Analyzer", layout="wide")

st.title("📄 Advanced Labour + MRT Compliance Analyzer")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded = st.file_uploader("Upload Document (TXT / PDF)", type=["txt", "pdf"])

# -----------------------------
# TEXT EXTRACTION
# -----------------------------
def extract_text(file):
    if file.type == "application/pdf":
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.lower()
    else:
        return file.read().decode("utf-8", errors="ignore").lower()

# -----------------------------
# KEYWORD CHECK FUNCTION
# -----------------------------
def check_presence(text, keywords):
    return any(k in text for k in keywords)

# -----------------------------
# VALUE EXTRACTION
# -----------------------------
def extract_amount(keywords, text):
    for k in keywords:
        match = re.search(k + r"\s*[:\-]?\s*(\d+)", text)
        if match:
            return int(match.group(1))
    return 0

# -----------------------------
# MAIN LOGIC
# -----------------------------
if uploaded:

    text = extract_text(uploaded)

    st.subheader("🔍 Document Preview")
    st.text(text[:500])

    # -----------------------------
    # DOCUMENT TYPE
    # -----------------------------
    if "payslip" in text or "earnings" in text:
        doc_type = "Payslip"
    elif "appointment" in text:
        doc_type = "Appointment Letter"
    elif "register" in text:
        doc_type = "Register"
    else:
        doc_type = "Unknown"

    st.success(f"📌 Detected Document: {doc_type}")

    # -----------------------------
    # COMPLIANCE RULES
    # -----------------------------
    st.header("⚖️ Labour Code Compliance")

    compliance_rules = {
        "Employee Identity": ["employee name", "emp id", "designation"],
        "Wage Period": ["wage period", "salary period"],
        "Earnings": ["earnings", "gross", "allowance", "salary"],
        "Deductions": ["deduction", "pf", "tax", "esi"],
        "Net Pay": ["net pay", "take home"],
        "Payment Timing": ["payment date", "credited"]
    }

    legal_reason = {
        "Employee Identity": "Required for identification under labour compliance",
        "Wage Period": "Mandatory to define salary cycle",
        "Earnings": "Ensures wage transparency",
        "Deductions": "Prevents illegal deductions",
        "Net Pay": "Employee must know final payable amount",
        "Payment Timing": "Ensures timely wage payment"
    }

    present = []
    missing = []

    for rule, keywords in compliance_rules.items():
        if check_presence(text, keywords):
            st.success(f"✔ {rule}")
            present.append(rule)
        else:
            st.error(f"❌ {rule}")
            st.caption(legal_reason[rule])
            missing.append(rule)

    score = (len(present) / len(compliance_rules)) * 100

    st.metric("📊 Compliance Score", f"{score:.0f}%")

    # -----------------------------
    # DISCLAIMER
    # -----------------------------
    st.header("⚠️ Disclaimer")

    if missing:
        st.write("Missing elements as per labour compliance:")
        for m in missing:
            st.write(f"- {m}")
    else:
        st.success("Document appears compliant")

    st.info("This is a preliminary rule-based compliance check.")

    # -----------------------------
    # WAGE RATIO
    # -----------------------------
    st.header("📊 Wage Ratio (Labour Code)")

    basic = extract_amount(["basic salary", "basic"], text)
    da = extract_amount(["dearness allowance", "da"], text)
    hra = extract_amount(["hra"], text)
    allowances = extract_amount(["allowance"], text)
    bonus = extract_amount(["bonus", "variable pay"], text)

    total_salary = basic + da + hra + allowances + bonus

    if total_salary > 0:
        wage_ratio = ((basic + da) / total_salary) * 100
        st.metric("Wages % (Basic + DA)", f"{wage_ratio:.1f}%")

        if wage_ratio >= 50:
            st.success("✔ Compliant with wage rule")
        else:
            st.error("❌ Below 50% requirement")

    # -----------------------------
    # MRT ANALYSIS
    # -----------------------------
    st.header("🏦 MRT Analysis")

    fixed_pay = extract_amount(["fixed pay"], text) or (basic + da)
    variable_pay = bonus
    esop = extract_amount(["esop"], text)
    esu = extract_amount(["esu"], text)
    stock = extract_amount(["stock"], text)
    non_cash = esop + esu + stock
    deferred = extract_amount(["deferred"], text)

    if fixed_pay > 0 and variable_pay > 0:

        var_ratio = (variable_pay / fixed_pay) * 100
        non_cash_ratio = (non_cash / variable_pay) * 100
        deferred_ratio = (deferred / variable_pay) * 100

        st.subheader("📈 MRT Ratios")

        col1, col2, col3 = st.columns(3)
        col1.metric("Variable %", f"{var_ratio:.0f}%")
        col2.metric("Non-Cash %", f"{non_cash_ratio:.0f}%")
        col3.metric("Deferred %", f"{deferred_ratio:.0f}%")

        # -----------------------------
        # VARIABLE DISTRIBUTION
        # -----------------------------
        st.subheader("💰 Variable Pay Distribution")

        cash = variable_pay - non_cash

        cash_pct = (cash / variable_pay) * 100
        esop_pct = (esop / variable_pay) * 100 if variable_pay else 0
        esu_pct = (esu / variable_pay) * 100 if variable_pay else 0

        st.write(f"Cash: {cash_pct:.1f}%")
        st.write(f"ESOPs: {esop_pct:.1f}%")
        st.write(f"ESUs: {esu_pct:.1f}%")

        # -----------------------------
        # MRT COMPLIANCE
        # -----------------------------
        st.subheader("⚖️ MRT Compliance")

        issues = []

        if var_ratio > 300:
            issues.append("Variable pay exceeds 300% cap")

        if var_ratio <= 200 and non_cash_ratio < 50:
            issues.append("Non-cash below 50%")

        if var_ratio > 200 and non_cash_ratio < 67:
            issues.append("Non-cash below 67%")

        if deferred_ratio < 60:
            issues.append("Deferred below 60%")

        if issues:
            for i in issues:
                st.error(i)
        else:
            st.success("✔ MRT Compensation Compliant")

    else:
        st.warning("⚠ Not enough MRT data")

    # -----------------------------
    # FINAL INSIGHT
    # -----------------------------
    st.header("🧠 Final Insight")

    if score >= 80 and (basic + da) > 0:
        st.success("✔ Strong compliance + balanced compensation")
    elif score >= 50:
        st.warning("⚠ Moderate compliance gaps")
    else:
        st.error("❌ High compliance risk")
