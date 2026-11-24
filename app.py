import os
import io
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# --------------------------- PAGE CONFIG ---------------------------
st.set_page_config(
    page_title="AI Inventory & Supply Chain Assistant",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------- THEME / CSS ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp { background: radial-gradient(circle at 20% 0%, #172d4b 0, #0b1424 45%, #08111f 100%); color: #f8fafc; }
.block-container { padding-top: 1.35rem; padding-bottom: 2rem; max-width: 1500px; }
section[data-testid="stSidebar"] { background: #08111f; border-right: 1px solid rgba(148,163,184,.18); }
section[data-testid="stSidebar"] * { color: #e5eefc !important; }
.hero { padding: 1.35rem 1.6rem; border-radius: 20px; background: linear-gradient(120deg, rgba(24,50,83,.96), rgba(9,116,147,.72)); border: 1px solid rgba(148,210,235,.25); margin-bottom: 1rem; box-shadow: 0 14px 35px rgba(0,0,0,.18); }
.hero h1 { margin: 0; font-size: 1.9rem; color: white; font-weight: 800; letter-spacing: -.5px; }
.hero p { margin: .45rem 0 0; color: #d8efff; }
.kpi { background: linear-gradient(145deg, rgba(26,44,68,.96), rgba(16,29,48,.96)); border: 1px solid rgba(148,163,184,.17); border-radius: 16px; padding: 16px 18px; min-height: 112px; box-shadow: 0 6px 20px rgba(0,0,0,.12); }
.kpi-label { color: #a9bfd9; font-size: .82rem; font-weight: 600; margin-bottom: 8px; }
.kpi-value { color: #f8fafc; font-size: 1.55rem; font-weight: 800; }
.kpi-note { color: #89d9ee; font-size: .76rem; margin-top: 5px; }
.panel { background: rgba(16,29,48,.72); border: 1px solid rgba(148,163,184,.16); border-radius: 16px; padding: 14px 16px; }
section[data-testid="stTabs"] button { color: #dbeafe; }
.stButton button, .stDownloadButton button { border-radius: 10px; border: 1px solid rgba(56,189,248,.3); background: linear-gradient(120deg,#2563eb,#0891b2); color: white; font-weight: 650; }
.stButton button:hover, .stDownloadButton button:hover { border-color: #67e8f9; color: white; }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
[data-testid="stMetric"] { background: rgba(15,31,52,.75); padding: 12px; border-radius: 12px; border: 1px solid rgba(148,163,184,.15); }
[data-testid="stMetricLabel"] { color: #b8cbe0 !important; }
[data-testid="stMetricValue"] { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------- HELPERS ---------------------------
@st.cache_data(show_spinner=False)
def get_sample_data():
    data = [
        ["P-1001", "Wireless Mouse", "Electronics", "TechSource", 120, 25, 799, 18],
        ["P-1002", "Mechanical Keyboard", "Electronics", "TechSource", 32, 20, 2499, 12],
        ["P-1003", "USB-C Hub", "Electronics", "Global Gadgets", 18, 15, 1299, 9],
        ["P-1004", "Office Chair", "Furniture", "Comfort Supplies", 14, 8, 5499, 4],
        ["P-1005", "Desk Lamp", "Furniture", "Comfort Supplies", 55, 15, 899, 8],
        ["P-1006", "Notebook A5", "Stationery", "Paper House", 200, 50, 65, 30],
        ["P-1007", "Gel Pen Pack", "Stationery", "Paper House", 42, 40, 120, 22],
        ["P-1008", "Monitor 24-inch", "Electronics", "Global Gadgets", 9, 10, 8999, 5],
        ["P-1009", "Power Strip", "Electronics", "TechSource", 75, 20, 499, 16],
        ["P-1010", "Storage Rack", "Furniture", "Comfort Supplies", 6, 8, 3299, 3],
        ["P-1011", "Printer Paper Box", "Stationery", "Paper House", 28, 25, 399, 12],
        ["P-1012", "Webcam HD", "Electronics", "Global Gadgets", 23, 10, 1599, 7],
    ]
    return pd.DataFrame(data, columns=["Product ID", "Product Name", "Category", "Supplier", "Quantity", "Reorder Level", "Unit Price", "Monthly Demand"])


COLUMN_ALIASES = {
    "Product ID": ["product id", "sku", "item id", "product code", "item code"],
    "Product Name": ["product name", "product", "item name", "name", "item"],
    "Category": ["category", "product category", "type"],
    "Supplier": ["supplier", "vendor", "supplier name", "vendor name"],
    "Quantity": ["quantity", "stock", "stock quantity", "available stock", "inventory", "units"],
    "Reorder Level": ["reorder level", "minimum stock", "min stock", "reorder point", "threshold"],
    "Unit Price": ["unit price", "price", "cost", "rate", "purchase price"],
    "Monthly Demand": ["monthly demand", "demand", "monthly sales", "sales per month"],
}


def normalize_columns(df):
    df = df.copy()
    original_cols = list(df.columns)
    rename = {}
    lowered = {str(c).strip().lower(): c for c in original_cols}
    for standard, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                rename[lowered[alias]] = standard
                break
    df = df.rename(columns=rename)
    # Required fields fallback so dashboard remains usable with partial data
    if "Product Name" not in df.columns:
        df["Product Name"] = [f"Product {i+1}" for i in range(len(df))]
    if "Quantity" not in df.columns:
        df["Quantity"] = 0
    for col in ["Category", "Supplier"]:
        if col not in df.columns:
            df[col] = "Unspecified"
    if "Reorder Level" not in df.columns:
        df["Reorder Level"] = 10
    if "Unit Price" not in df.columns:
        df["Unit Price"] = 0
    if "Monthly Demand" not in df.columns:
        df["Monthly Demand"] = 0
    for col in ["Quantity", "Reorder Level", "Unit Price", "Monthly Demand"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Stock Value"] = df["Quantity"] * df["Unit Price"]
    df["Stock Status"] = df.apply(
        lambda r: "Out of Stock" if r["Quantity"] <= 0 else ("Low Stock" if r["Quantity"] <= r["Reorder Level"] else "Healthy"), axis=1
    )
    return df


def money(v):
    return f"₹{v:,.0f}"


def kpi_card(label, value, note=""):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)


def inventory_context(df):
    if df.empty:
        return "Inventory data is empty."
    status = df["Stock Status"].value_counts().to_dict()
    top = df.nlargest(5, "Stock Value")[["Product Name", "Category", "Quantity", "Stock Value"]].to_dict("records")
    low = df[df["Stock Status"].isin(["Low Stock", "Out of Stock"])][["Product Name", "Supplier", "Quantity", "Reorder Level", "Stock Status"]].to_dict("records")
    suppliers = df.groupby("Supplier")["Stock Value"].sum().sort_values(ascending=False).head(5).to_dict()
    return f"Inventory summary: {len(df)} products, total units {df['Quantity'].sum():,.0f}, stock value ₹{df['Stock Value'].sum():,.2f}. Stock status counts: {status}. Top stock-value products: {top}. Low/out-of-stock items: {low}. Supplier stock values: {suppliers}."

# --------------------------- SIDEBAR & DATA SOURCE ---------------------------
st.sidebar.markdown("## 📦 Inventory Suite")
st.sidebar.caption("Inventory intelligence & replenishment")

# Start with no dataset selected. User must explicitly choose a source.
source_mode = st.sidebar.selectbox(
    "Choose Data Source",
    ["-- Select a data source --", "Upload Excel / CSV", "Use Sample Dataset"],
    index=0,
)

uploaded_file = None
raw_df = None
sheet_name = None

if source_mode == "Upload Excel / CSV":
    uploaded_file = st.sidebar.file_uploader(
        "Upload inventory file", type=["csv", "xlsx", "xls"],
        help="Supported formats: CSV, Excel (.xlsx, .xls)."
    )
    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                raw_df = pd.read_csv(uploaded_file)
            else:
                excel_file = pd.ExcelFile(uploaded_file)
                if len(excel_file.sheet_names) > 1:
                    sheet_name = st.sidebar.selectbox("Choose Excel sheet", excel_file.sheet_names)
                else:
                    sheet_name = excel_file.sheet_names[0]
                raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        except Exception as ex:
            st.sidebar.error(f"Could not read uploaded file: {ex}")
            raw_df = None
elif source_mode == "Use Sample Dataset":
    raw_df = get_sample_data()

# Gemini key: secrets/env or sidebar entry
secret_key = ""
try:
    secret_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    pass
secret_key = secret_key or os.getenv("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Gemini API Key (optional)", value=secret_key, type="password",
    help="Set GEMINI_API_KEY in Streamlit secrets or enter it here to enable AI chat."
)
st.sidebar.caption("Tip: store your key in .streamlit/secrets.toml for local projects.")

# --------------------------- HEADER ---------------------------
st.markdown(f"""
<div class="hero">
  <h1>📦 AI Inventory & Supply Chain Assistant</h1>
  <p>Intelligent inventory analytics · AI-powered insights · Smart replenishment planning</p>
  <p style="font-size:12px; margin-top:10px; color:#bcecff;">PYTHON • STREAMLIT • PLOTLY • GOOGLE GEMINI AI</p>
</div>
""", unsafe_allow_html=True)

# If no source is selected or no file has been uploaded, show a welcome/source-selection page.
if source_mode == "-- Select a data source --" or (source_mode == "Upload Excel / CSV" and raw_df is None):
    st.markdown("## 👋 Welcome to your Inventory Analytics Workspace")
    st.write("Choose how you want to begin. The dashboard will remain hidden until you select a dataset.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📁 Upload your own inventory file")
        st.write("Use your business inventory data in CSV or Excel format (.csv, .xlsx, .xls).")
        st.info("Select **Upload Excel / CSV** in the sidebar, then choose your file. For Excel workbooks with multiple sheets, you can select the sheet to analyze.")
    with c2:
        st.markdown("### 🧪 Explore with sample data")
        st.write("Use a demo inventory dataset to explore the dashboard and its features.")
        st.info("Select **Use Sample Dataset** in the sidebar. Sample data will only load after you choose it.")
    st.markdown("### Expected columns (recognized automatically)")
    st.caption("Product Name, Quantity, Category, Supplier, Reorder Level, Unit Price, Monthly Demand. Column names may have common variations. Missing optional columns are filled with sensible defaults.")
    st.stop()

if source_mode == "Upload Excel / CSV" and raw_df is not None:
    st.sidebar.success(f"Loaded {len(raw_df):,} rows from {uploaded_file.name}")
elif source_mode == "Use Sample Dataset":
    st.sidebar.success("Sample dataset selected")

# Navigation appears only after a dataset is selected.
page = st.sidebar.radio("Navigate", ["Dashboard", "Inventory Explorer", "Supplier Analytics", "AI Assistant", "About"], index=0)

# Normalize data only after user explicitly selected and loaded a source.
df = normalize_columns(raw_df)

# --------------------------- FILTERS ---------------------------
with st.expander("🔎 Dashboard Filters", expanded=(page == "Dashboard")):
    f1, f2, f3 = st.columns([1, 1, 1.4])
    cats = ["All"] + sorted(df["Category"].dropna().astype(str).unique().tolist())
    sups = ["All"] + sorted(df["Supplier"].dropna().astype(str).unique().tolist())
    selected_category = f1.selectbox("Category", cats, key="category_filter")
    selected_supplier = f2.selectbox("Supplier", sups, key="supplier_filter")
    search_term = f3.text_input("Search product", placeholder="Type a product name or SKU", key="product_filter")

filtered_df = df.copy()
if selected_category != "All":
    filtered_df = filtered_df[filtered_df["Category"].astype(str) == selected_category]
if selected_supplier != "All":
    filtered_df = filtered_df[filtered_df["Supplier"].astype(str) == selected_supplier]
if search_term.strip():
    filtered_df = filtered_df[filtered_df["Product Name"].astype(str).str.contains(search_term.strip(), case=False, na=False)]

# --------------------------- PAGE: DASHBOARD ---------------------------
if page == "Dashboard":
    st.subheader("📊 Overview")
    total_products = len(filtered_df)
    total_units = filtered_df["Quantity"].sum()
    inventory_value = filtered_df["Stock Value"].sum()
    low_stock = int((filtered_df["Stock Status"] == "Low Stock").sum())
    out_stock = int((filtered_df["Stock Status"] == "Out of Stock").sum())
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: kpi_card("Total Products", f"{total_products:,}", "Products in current selection")
    with k2: kpi_card("Available Units", f"{total_units:,.0f}", "Units currently in stock")
    with k3: kpi_card("Inventory Value", money(inventory_value), "Current stock × unit price")
    with k4: kpi_card("Low Stock", f"{low_stock:,}", "Below / at reorder threshold")
    with k5: kpi_card("Out of Stock", f"{out_stock:,}", "Needs immediate attention")

    st.markdown("### Inventory Insights")
    chart1, chart2 = st.columns(2)
    with chart1:
        category_data = filtered_df.groupby("Category", as_index=False)["Quantity"].sum().sort_values("Quantity", ascending=False)
        fig = px.bar(category_data, x="Category", y="Quantity", color="Category", text_auto=True, title="Stock Quantity by Category")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with chart2:
        status_data = filtered_df["Stock Status"].value_counts().rename_axis("Status").reset_index(name="Products")
        fig = px.pie(status_data, names="Status", values="Products", hole=.58, title="Inventory Health", color="Status", color_discrete_map={"Healthy":"#22c55e", "Low Stock":"#f59e0b", "Out of Stock":"#ef4444"})
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)

    chart3, chart4 = st.columns(2)
    with chart3:
        top_value = filtered_df.nlargest(8, "Stock Value")
        fig = px.bar(top_value, x="Stock Value", y="Product Name", orientation="h", color="Category", title="Top Products by Inventory Value", hover_data=["Quantity", "Unit Price"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder":"total ascending"}, margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with chart4:
        supplier_data = filtered_df.groupby("Supplier", as_index=False)["Stock Value"].sum().sort_values("Stock Value", ascending=False)
        fig = px.bar(supplier_data, x="Supplier", y="Stock Value", color="Supplier", title="Supplier-wise Inventory Value", text_auto=".2s")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🚨 Items Requiring Attention")
    alert_df = filtered_df[filtered_df["Stock Status"].isin(["Low Stock", "Out of Stock"])].sort_values(["Stock Status", "Quantity"])
    if alert_df.empty:
        st.success("All filtered products are above their reorder threshold.")
    else:
        st.dataframe(alert_df[["Product Name", "Category", "Supplier", "Quantity", "Reorder Level", "Stock Status", "Stock Value"]], use_container_width=True, hide_index=True)

    st.markdown("### 📋 Inventory Snapshot")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download filtered inventory CSV", filtered_df.to_csv(index=False).encode("utf-8-sig"), "filtered_inventory.csv", "text/csv")

# --------------------------- PAGE: INVENTORY EXPLORER ---------------------------
elif page == "Inventory Explorer":
    st.subheader("📦 Inventory Explorer")
    status_choice = st.multiselect("Filter by stock status", ["Healthy", "Low Stock", "Out of Stock"], default=["Healthy", "Low Stock", "Out of Stock"])
    explorer_df = filtered_df[filtered_df["Stock Status"].isin(status_choice)]
    st.dataframe(explorer_df, use_container_width=True, hide_index=True)
    st.download_button("Download inventory view", explorer_df.to_csv(index=False).encode("utf-8-sig"), "inventory_explorer.csv", "text/csv")
    st.markdown("#### Suggested Reorder Quantities")
    reorder = explorer_df[explorer_df["Stock Status"].isin(["Low Stock", "Out of Stock"])].copy()
    reorder["Suggested Order Qty"] = (reorder["Monthly Demand"] * 1.2 - reorder["Quantity"]).clip(lower=0).round().astype(int)
    st.caption("Basic estimate = 120% of monthly demand minus current stock. Validate lead times and safety stock before purchasing.")
    st.dataframe(reorder[["Product Name", "Supplier", "Quantity", "Monthly Demand", "Reorder Level", "Suggested Order Qty", "Stock Status"]], use_container_width=True, hide_index=True)

# --------------------------- PAGE: SUPPLIER ANALYTICS ---------------------------
elif page == "Supplier Analytics":
    st.subheader("🚚 Supplier Analytics")
    sup = filtered_df.groupby("Supplier", as_index=False).agg(Products=("Product Name", "count"), Units=("Quantity", "sum"), Inventory_Value=("Stock Value", "sum"), Low_Stock_Items=("Stock Status", lambda s: int(s.isin(["Low Stock", "Out of Stock"]).sum())))
    a, b, c = st.columns(3)
    a.metric("Suppliers", len(sup))
    b.metric("Supplier Inventory Value", money(sup["Inventory_Value"].sum()))
    c.metric("Supplier Low-stock Items", int(sup["Low_Stock_Items"].sum()))
    fig = px.bar(sup.sort_values("Inventory_Value", ascending=False), x="Supplier", y="Inventory_Value", color="Supplier", title="Inventory Value by Supplier", text_auto=".2s")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(sup, use_container_width=True, hide_index=True)

# --------------------------- PAGE: AI ASSISTANT ---------------------------
elif page == "AI Assistant":
    st.subheader("🤖 Gemini Inventory Assistant")
    st.write("Ask questions about stock, reorder risks, suppliers, product mix and inventory value.")
    suggested = ["Which products need immediate reordering?", "Which products have the highest inventory value?", "Summarize inventory risks", "How can I reduce inventory holding cost?", "Compare suppliers based on inventory value"]
    st.markdown("**Quick questions**")
    qcols = st.columns(2)
    chosen_q = None
    for i, q in enumerate(suggested):
        if qcols[i % 2].button(q, key=f"quick_{i}"):
            chosen_q = q
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if st.button("🧹 Clear chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])
    user_q = st.chat_input("Ask your inventory question...")
    question = chosen_q or user_q
    if question:
        st.session_state.chat_history.append({"role":"user", "content":question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            if not api_key:
                answer = "**Gemini API key not configured.** Add your key in the sidebar or set `GEMINI_API_KEY` in `.streamlit/secrets.toml` to enable AI responses. Your dashboard and analytics are still available without AI."
                st.info(answer)
            else:
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    context = inventory_context(filtered_df)
                    prompt = f"You are a practical inventory and supply-chain analyst. Use the data context below. Be concise, give actionable insights, do not invent data, and clearly label assumptions.\n\nDATA CONTEXT:\n{context}\n\nUSER QUESTION:\n{question}"
                    with st.spinner("Gemini is analyzing the inventory..."):
                        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                    answer = response.text or "Gemini returned an empty response. Please try again."
                    st.markdown(answer)
                except Exception as err:
                    answer = f"AI request failed: `{err}`. Check your API key, model availability, and internet connection."
                    st.error(answer)
        st.session_state.chat_history.append({"role":"assistant", "content":answer})

# --------------------------- PAGE: ABOUT ---------------------------
else:
    st.subheader("ℹ️ About this application")
    st.markdown("""\n    **AI Inventory & Supply Chain Assistant** is a demo analytics app built with Python, Streamlit and Plotly, with optional Google Gemini AI support.

    **Capabilities**
    - Inventory overview and KPIs
    - Category, supplier and product filters
    - Stock health and reorder alerts
    - Supplier inventory-value analysis
    - CSV upload and export
    - AI-powered inventory Q&A (requires Gemini API key)

    **Stock status rule:** Out of Stock = quantity 0 or less; Low Stock = quantity at or below reorder level; otherwise Healthy.
    **Reorder estimate:** The explorer uses 120% of monthly demand less current stock as a simple estimate. It is not a purchase-order recommendation and should be validated with lead time, safety stock and supplier constraints.
    """)
    st.caption(f"Current data: {len(df):,} rows · Updated in app session {datetime.now().strftime('%d %b %Y, %H:%M')}")
