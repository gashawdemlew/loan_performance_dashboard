# ============================================================
# LOAN PERFORMANCE ANALYTICS DASHBOARD
# WITH FULL PDF EXPORT (INCLUDING CHARTS)
# ============================================================
#
# INSTALL:
# pip install streamlit pandas numpy plotly openpyxl reportlab kaleido
#
# RUN:
# streamlit run app.py
#
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from plotly.subplots import make_subplots

# PDF
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

from io import BytesIO
import tempfile

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Loan Performance Dashboard",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Loan Performance Analytics Dashboard")

st.markdown("""
Interactive dashboard for:
- Loan portfolio analysis
- Customer growth analysis
- Product performance
- Gender analysis
- Initial loan = 500 customer filtering
- PDF exporting with charts
""")

# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.sidebar.file_uploader(
    "Upload Loan Dataset",
    type=["csv", "xlsx"]
)

# ============================================================
# MAIN PROCESS
# ============================================================

if uploaded_file is not None:

    # ========================================================
    # LOAD DATA
    # ========================================================

    try:

        if uploaded_file.name.endswith(".csv"):

            raw_df = pd.read_csv(uploaded_file, low_memory=False)

        else:

            raw_df = pd.read_excel(uploaded_file, low_memory=False)

        st.success("✅ File uploaded successfully!")

    except Exception as e:

        st.error(f"Error loading file: {e}")
        st.stop()

    # ========================================================
    # DATA PREVIEW
    # ========================================================

    st.subheader("📁 Raw Data Preview")

    st.dataframe(raw_df.head())

    # ========================================================
    # COLUMN MAPPING
    # ========================================================

    st.sidebar.header("🔗 Column Mapping")

    columns = raw_df.columns.tolist()

    product_col = st.sidebar.selectbox(
        "Product Column",
        columns
    )

    phone_col = st.sidebar.selectbox(
        "Customer Identifier Column",
        columns
    )

    loanid_col = st.sidebar.selectbox(
        "Loan ID Column",
        columns
    )

    principal_col = st.sidebar.selectbox(
        "Principal Column",
        columns
    )

    created_col = st.sidebar.selectbox(
        "Created Date Column",
        columns
    )

    expected_col = st.sidebar.selectbox(
        "Expected Date Column",
        columns
    )

    gender_col = st.sidebar.selectbox(
        "Gender Column",
        columns
    )

    duration_col = st.sidebar.selectbox(
        "Loan Duration Column",
        columns
    )

    # OPTIONAL BRANCH

    branch_exists = st.sidebar.checkbox(
        "Dataset has Branch Column?"
    )

    if branch_exists:

        branch_col = st.sidebar.selectbox(
            "Branch Column",
            columns
        )

    # ========================================================
    # RENAME COLUMNS
    # ========================================================

    rename_dict = {
        product_col: "Product",
        phone_col: "Phone",
        loanid_col: "Loan ID",
        principal_col: "Principal",
        created_col: "Created At",
        expected_col: "Expected At",
        gender_col: "Gender",
        duration_col: "Loan Duration"
    }

    if branch_exists:

        rename_dict[branch_col] = "Branch"

    df = raw_df.rename(columns=rename_dict)

    # ========================================================
    # PREPROCESSING
    # ========================================================

    try:

        df['Created At'] = pd.to_datetime(
            df['Created At']
        )

        df['Expected At'] = pd.to_datetime(
            df['Expected At']
        )

        df['Principal'] = pd.to_numeric(
            df['Principal'],
            errors='coerce'
        )

        df['YearMonth'] = (
            df['Created At']
            .dt.to_period('M')
            .astype(str)
        )

        df = df.sort_values(
            ['Phone', 'Created At']
        )

    except Exception as e:

        st.error(f"Preprocessing Error: {e}")
        st.stop()

    # ========================================================
    # FILTER CUSTOMERS WITH INITIAL LOAN = 500
    # ========================================================

    first_loans = (
        df.groupby('Phone')
        .first()
        .reset_index()
    )

    initial_500_customers = first_loans[
        first_loans['Principal'] == 500
    ]['Phone']

    initial_500_df = df[
        df['Phone'].isin(initial_500_customers)
    ]

    # ========================================================
    # DATASET SELECTION
    # ========================================================

    st.sidebar.header("📌 Analysis Dataset")

    analysis_type = st.sidebar.radio(
        "Select Dataset",
        [
            "All Customers",
            "Initial Loan = 500 Customers"
        ]
    )

    if analysis_type == "Initial Loan = 500 Customers":

        analysis_df = initial_500_df

    else:

        analysis_df = df

    # ========================================================
    # FILTERS
    # ========================================================

    st.sidebar.header("🎯 Filters")

    selected_products = st.sidebar.multiselect(
        "Select Products",
        analysis_df['Product'].dropna().unique(),
        default=analysis_df['Product'].dropna().unique()
    )

    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        analysis_df['Gender'].dropna().unique(),
        default=analysis_df['Gender'].dropna().unique()
    )

    if branch_exists:

        selected_branch = st.sidebar.multiselect(
            "Select Branch",
            analysis_df['Branch'].dropna().unique(),
            default=analysis_df['Branch'].dropna().unique()
        )

    # DATE FILTER

    min_date = analysis_df['Created At'].min().date()

    max_date = analysis_df['Created At'].max().date()

    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date]
    )

    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_df = analysis_df[
        analysis_df['Product'].isin(selected_products)
    ]

    filtered_df = filtered_df[
        filtered_df['Gender'].isin(selected_gender)
    ]

    if branch_exists:

        filtered_df = filtered_df[
            filtered_df['Branch'].isin(selected_branch)
        ]

    if len(date_range) == 2:

        filtered_df = filtered_df[
            (
                filtered_df['Created At'].dt.date >= date_range[0]
            )
            &
            (
                filtered_df['Created At'].dt.date <= date_range[1]
            )
        ]

    # ========================================================
    # KPI METRICS
    # ========================================================

    st.header("📌 Portfolio KPIs")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Loans",
            f"{filtered_df['Loan ID'].nunique():,}"
        )

    with col2:

        st.metric(
            "Total Customers",
            f"{filtered_df['Phone'].nunique():,}"
        )

    with col3:

        st.metric(
            "Total Disbursement",
            f"{filtered_df['Principal'].sum():,.2f}"
        )

    with col4:

        st.metric(
            "Average Loan Size",
            f"{filtered_df['Principal'].mean():,.2f}"
        )

    # ========================================================
    # MONTHLY CUSTOMER GROWTH
    # ========================================================

    st.header("📈 Monthly Customer Growth")

    monthly_customer = (
        filtered_df.groupby('YearMonth')['Phone']
        .nunique()
        .reset_index(name='Customers')
    )

    fig_customer = px.line(
        monthly_customer,
        x='YearMonth',
        y='Customers',
        markers=True,
        title="Monthly Customer Growth"
    )

    st.plotly_chart(
        fig_customer,
        width='stretch'
    )

    # ========================================================
    # MONTHLY DISBURSEMENT
    # ========================================================

    st.header("💰 Monthly Disbursement Trend")

    monthly_disbursement = (
        filtered_df.groupby('YearMonth')['Principal']
        .sum()
        .reset_index(name='Disbursement')
    )

    fig_disbursement = px.bar(
        monthly_disbursement,
        x='YearMonth',
        y='Disbursement',
        title="Monthly Disbursement Trend"
    )

    st.plotly_chart(
        fig_disbursement,
        width='stretch'
    )

    # ========================================================
    # PRODUCT ANALYSIS
    # ========================================================

    st.header("🏦 Product Analysis")

    product_analysis = (
        filtered_df.groupby(
            ['YearMonth', 'Product']
        )['Principal']
        .sum()
        .reset_index()
    )

    fig_product = px.line(
        product_analysis,
        x='YearMonth',
        y='Principal',
        color='Product',
        markers=True,
        title="Product-wise Disbursement Growth"
    )

    st.plotly_chart(
        fig_product,
        width='stretch'
    )

    # ========================================================
    # GENDER ANALYSIS
    # ========================================================

    st.header("👨‍💼 Gender Analysis")

    gender_analysis = (
        filtered_df.groupby('Gender')
        .agg({
            'Principal': 'sum',
            'Phone': 'nunique',
            'Loan ID': 'nunique'
        })
        .reset_index()
    )

    gender_analysis.columns = [
        'Gender',
        'Disbursement',
        'Customers',
        'Loans'
    ]

    fig_gender = make_subplots(
        rows=1,
        cols=2,
        specs=[[{'type': 'pie'}, {'type': 'bar'}]],
        subplot_titles=[
            "Disbursement Share",
            "Customer Count"
        ]
    )

    fig_gender.add_trace(
        go.Pie(
            labels=gender_analysis['Gender'],
            values=gender_analysis['Disbursement']
        ),
        row=1,
        col=1
    )

    fig_gender.add_trace(
        go.Bar(
            x=gender_analysis['Gender'],
            y=gender_analysis['Customers']
        ),
        row=1,
        col=2
    )

    st.plotly_chart(
        fig_gender,
        width='stretch'
    )

    # ========================================================
    # NEW VS REPEAT CUSTOMERS
    # ========================================================

    st.header("🔁 New vs Repeat Customers")

    first_loan_dates = (
        filtered_df.groupby('Phone')['Created At']
        .min()
        .reset_index(name='FirstLoanDate')
    )

    temp_df = filtered_df.merge(
        first_loan_dates,
        on='Phone'
    )

    temp_df['Customer Type'] = np.where(
        temp_df['Created At'] == temp_df['FirstLoanDate'],
        'New',
        'Repeat'
    )

    repeat_analysis = (
        temp_df.groupby(
            ['YearMonth', 'Customer Type']
        )['Phone']
        .nunique()
        .reset_index(name='Customers')
    )

    fig_repeat = px.bar(
        repeat_analysis,
        x='YearMonth',
        y='Customers',
        color='Customer Type',
        barmode='stack',
        title="New vs Repeat Customers"
    )

    st.plotly_chart(
        fig_repeat,
        width='stretch'
    )

    # ========================================================
    # LOAN DURATION ANALYSIS
    # ========================================================

    st.header("⏳ Loan Duration Analysis")

    duration_analysis = (
        filtered_df.groupby('Loan Duration')
        .agg({
            'Principal': 'sum',
            'Loan ID': 'nunique'
        })
        .reset_index()
    )

    fig_duration = px.bar(
        duration_analysis,
        x='Loan Duration',
        y='Principal',
        color='Loan Duration',
        title="Loan Duration Analysis"
    )

    st.plotly_chart(
        fig_duration,
        width='stretch'
    )

    # ========================================================
    # TOP BORROWERS
    # ========================================================

    st.header("🏆 Top Borrowers")

    top_borrowers = (
        filtered_df.groupby('Phone')
        .agg({
            'Principal': 'sum',
            'Loan ID': 'nunique'
        })
        .reset_index()
    )

    top_borrowers.columns = [
        'Phone',
        'Total Borrowed',
        'Loan Count'
    ]

    top_borrowers = top_borrowers.sort_values(
        'Total Borrowed',
        ascending=False
    ).head(10)

    fig_top = px.bar(
        top_borrowers,
        x='Phone',
        y='Total Borrowed',
        hover_data=['Loan Count'],
        title="Top 10 Borrowers"
    )

    st.plotly_chart(
        fig_top,
        width='stretch'
    )

    # ========================================================
    # PORTFOLIO DISTRIBUTION
    # ========================================================

    st.header("📦 Portfolio Distribution")

    portfolio_distribution = (
        filtered_df.groupby('Product')['Principal']
        .sum()
        .reset_index()
    )

    fig_distribution = px.pie(
        portfolio_distribution,
        names='Product',
        values='Principal',
        hole=0.4,
        title="Portfolio Distribution"
    )

    st.plotly_chart(
        fig_distribution,
        width='stretch'
    )

    # ========================================================
    # PDF EXPORT
    # ========================================================

    st.header("📄 Export PDF Report")

    selected_products_text = ", ".join(
        map(str, selected_products)
    )

    selected_gender_text = ", ".join(
        map(str, selected_gender)
    )

    if branch_exists:

        selected_branch_text = ", ".join(
            map(str, selected_branch)
        )

    else:

        selected_branch_text = "N/A"

    report_title = f"""
    Loan Performance Report

    Scenario:
    {analysis_type}

    Products:
    {selected_products_text}

    Gender:
    {selected_gender_text}

    Branch:
    {selected_branch_text}

    Date Range:
    {date_range[0]} to {date_range[1]}
    """

    # CREATE PDF

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    # TITLE

    elements.append(
        Paragraph(
            report_title.replace("\n", "<br/>"),
            styles['Title']
        )
    )

    elements.append(Spacer(1, 20))

    # KPI TABLE

    kpi_data = [
        ["Metric", "Value"],
        ["Total Loans", f"{filtered_df['Loan ID'].nunique():,}"],
        ["Total Customers", f"{filtered_df['Phone'].nunique():,}"],
        ["Total Disbursement", f"{filtered_df['Principal'].sum():,.2f}"],
        ["Average Loan Size", f"{filtered_df['Principal'].mean():,.2f}"]
    ]

    kpi_table = Table(kpi_data)

    kpi_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

            ('GRID', (0, 0), (-1, -1), 1, colors.black),

            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

            ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
        ])
    )

    elements.append(kpi_table)

    elements.append(Spacer(1, 20))

    # ========================================================
    # FUNCTION TO ADD CHARTS TO PDF
    # ========================================================

    def add_chart_to_pdf(fig, title):

        elements.append(
            Paragraph(
                title,
                styles['Heading2']
            )
        )

        elements.append(Spacer(1, 10))

        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) as tmpfile:

            fig.write_image(
                tmpfile.name,
                width=1200,
                height=600
            )

            img = RLImage(
                tmpfile.name,
                width=500,
                height=250
            )

            elements.append(img)

        elements.append(Spacer(1, 20))

    # ========================================================
    # ADD CHARTS
    # ========================================================

    add_chart_to_pdf(
        fig_customer,
        "Monthly Customer Growth"
    )

    add_chart_to_pdf(
        fig_disbursement,
        "Monthly Disbursement Trend"
    )

    add_chart_to_pdf(
        fig_product,
        "Product-wise Disbursement Growth"
    )

    add_chart_to_pdf(
        fig_gender,
        "Gender Analysis"
    )

    add_chart_to_pdf(
        fig_repeat,
        "New vs Repeat Customers"
    )

    add_chart_to_pdf(
        fig_duration,
        "Loan Duration Analysis"
    )

    add_chart_to_pdf(
        fig_top,
        "Top Borrowers"
    )

    add_chart_to_pdf(
        fig_distribution,
        "Portfolio Distribution"
    )

    # ========================================================
    # MONTHLY DISBURSEMENT TABLE
    # ========================================================

    elements.append(PageBreak())

    elements.append(
        Paragraph(
            "Monthly Disbursement Summary",
            styles['Heading2']
        )
    )

    monthly_table_data = [
        ["YearMonth", "Disbursement"]
    ]

    for _, row in monthly_disbursement.iterrows():

        monthly_table_data.append([
            str(row['YearMonth']),
            f"{row['Disbursement']:,.2f}"
        ])

    monthly_table = Table(monthly_table_data)

    monthly_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

            ('GRID', (0, 0), (-1, -1), 1, colors.black),

            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)
        ])
    )

    elements.append(monthly_table)

    # BUILD PDF

    doc.build(elements)

    pdf_data = buffer.getvalue()

    buffer.close()

    # DOWNLOAD BUTTON

    st.download_button(
        label="📥 Download Full PDF Report",
        data=pdf_data,
        file_name="loan_performance_full_report.pdf",
        mime="application/pdf"
    )

    # ========================================================
    # RAW DATA
    # ========================================================

    st.header("🗂 Processed Dataset")

    st.dataframe(filtered_df)

else:

    st.info(
        "👈 Upload a CSV or Excel file to start analysis."
    )