import streamlit as st
import pandas as pd
import re
from langchain_community.llms import Ollama


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FINANCE GEN AI",
    page_icon="💰",
    layout="centered"
)


# ============================================================
# TITLE
# ============================================================

st.title("💰FINANCE GEN AI")
st.caption("Intelligent Financial Analysis Assistant")

st.write(
    "Ask questions about company financial performance, "
    "revenue, profit, EBITDA, cash flow and financial ratios."
)


# ============================================================
# UPLOAD DATASET
# ============================================================

st.subheader("📂 Upload Financial Dataset")

uploaded_file = st.file_uploader(
    "Upload your Financial Statements CSV file",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Please upload your financial CSV file to start.")
    st.stop()


try:

    df = pd.read_csv(uploaded_file)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

except Exception as e:

    st.error("Could not read the uploaded CSV file.")
    st.write(e)
    st.stop()


# ============================================================
# DATASET VALIDATION
# ============================================================

if "Company" not in df.columns:

    st.error(
        "The dataset must contain a 'Company' column."
    )

    st.stop()


if "Year" not in df.columns:

    st.error(
        "The dataset must contain a 'Year' column."
    )

    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

df["Company"] = (
    df["Company"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["Year"] = pd.to_numeric(
    df["Year"],
    errors="coerce"
)


financial_columns = [

    "Revenue",
    "Gross Profit",
    "Net Income",
    "EBITDA",
    "Cash Flow",
    "Market Cap",
    "ROE",
    "ROA",
    "ROI",
    "Net Profit Margin",
    "Number of Employees"

]


for column in financial_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# Remove rows without company/year

df = df.dropna(
    subset=["Company", "Year"]
).copy()


st.success(
    f"Dataset loaded successfully: {len(df)} rows"
)


# ============================================================
# OLLAMA
# ============================================================

try:

    llm = Ollama(
        model="llama3.2",
        temperature=0
    )

except Exception:

    llm = None


# ============================================================
# COMPANY ALIASES
# ============================================================

company_aliases = {

    "apple": "AAPL",
    "aapl": "AAPL",

    "microsoft": "MSFT",
    "msft": "MSFT",

    "amazon": "AMZN",
    "amazon.com": "AMZN",
    "amzn": "AMZN",

    "google": "GOOG",
    "alphabet": "GOOG",
    "goog": "GOOG",

    "nvidia": "NVDA",
    "nvda": "NVDA",

    "intel": "INTC",
    "intc": "INTC",

    "paypal": "PYPL",
    "pypl": "PYPL",

    "mcdonalds": "MCD",
    "mcdonald's": "MCD",
    "mcd": "MCD",

    "aig": "AIG",
    "bcs": "BCS",
    "pcg": "PCG",
    "shldq": "SHLDQ"

}


# ============================================================
# FIND ALL COMPANIES
# ============================================================

def find_companies(question):

    q = question.lower()

    found = []

    # Check aliases

    for name, ticker in company_aliases.items():

        if re.search(
            r"\b" + re.escape(name) + r"\b",
            q
        ):

            if ticker not in found:
                found.append(ticker)


    # Check actual dataset company codes

    for company in df["Company"].unique():

        company = str(company).upper()

        if re.search(
            r"\b" + re.escape(company.lower()) + r"\b",
            q
        ):

            if company not in found:
                found.append(company)


    return found


# ============================================================
# FIND ONE COMPANY
# ============================================================

def find_company(question):

    companies = find_companies(question)

    if companies:
        return companies[0]

    return None


# ============================================================
# FIND YEAR
# ============================================================

def find_year(question):

    years = re.findall(
        r"\b(20\d{2})\b",
        question
    )

    if years:

        return int(years[0])

    return None


# ============================================================
# FORMAT NUMBER
# ============================================================

def format_number(value):

    if pd.isna(value):
        return "Not available"

    try:

        value = float(value)

        if abs(value) >= 1_000_000_000:

            return (
                f"${value / 1_000_000_000:.2f} billion"
            )

        elif abs(value) >= 1_000_000:

            return (
                f"${value / 1_000_000:.2f} million"
            )

        else:

            return f"${value:,.2f}"

    except:

        return str(value)


# ============================================================
# FIND METRIC
# ============================================================

def find_metric(question):

    q = question.lower()

    metric_aliases = {

        "Revenue": [
            "revenue",
            "sales"
        ],

        "Gross Profit": [
            "gross profit",
            "gross income"
        ],

        "Net Income": [
            "net income",
            "net profit",
            "profit",
            "earnings"
        ],

        "EBITDA": [
            "ebitda"
        ],

        "Cash Flow": [
            "cash flow",
            "cashflow"
        ],

        "Market Cap": [
            "market cap",
            "market capitalization"
        ],

        "ROE": [
            "roe",
            "return on equity"
        ],

        "ROA": [
            "roa",
            "return on assets"
        ],

        "ROI": [
            "roi",
            "return on investment"
        ],

        "Net Profit Margin": [
            "net profit margin",
            "profit margin"
        ],

        "Number of Employees": [
            "employees",
            "employee count",
            "number of employees",
            "workforce"
        ]

    }


    for column, keywords in metric_aliases.items():

        for keyword in keywords:

            if keyword in q:

                return column


    return None


# ============================================================
# CHECK COMPANY CODE QUESTION
# ============================================================

def company_code_answer(question):

    q = question.lower()

    code_words = [

        "company code",
        "stock code",
        "ticker",
        "ticker symbol",
        "stock symbol",
        "code"

    ]

    if not any(
        word in q
        for word in code_words
    ):

        return None


    company = find_company(question)

    if company:

        return (
            f"The company code for {company_name(company)} "
            f"is **{company}**."
        )


    return (
        "Please mention a company name, for example: "
        "**What is Apple's code?**"
    )


# ============================================================
# COMPANY NAME
# ============================================================

def company_name(ticker):

    names = {

        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "AMZN": "Amazon",
        "GOOG": "Google",
        "NVDA": "Nvidia",
        "INTC": "Intel",
        "PYPL": "PayPal",
        "MCD": "McDonald's",
        "AIG": "AIG",
        "BCS": "Barclays",
        "PCG": "PG&E",
        "SHLDQ": "Sears"

    }

    return names.get(
        ticker,
        ticker
    )


# ============================================================
# COMPANY + YEAR + METRIC
# ============================================================

def single_company_answer(
    company,
    year,
    metric
):

    result = df[
        (df["Company"] == company)
        &
        (df["Year"] == year)
    ]


    if result.empty:

        available = sorted(
            df[
                df["Company"] == company
            ]["Year"]
            .astype(int)
            .unique()
            .tolist()
        )

        if available:

            return (
                f"❌ No data is available for "
                f"**{company_name(company)} ({company})** "
                f"in **{year}**.\n\n"
                f"Available years: "
                f"**{min(available)}–{max(available)}**."
            )

        return (
            f"❌ No data is available for "
            f"**{company}**."
        )


    value = result.iloc[0][metric]


    if pd.isna(value):

        return (
            f"❌ {metric} data for "
            f"**{company_name(company)} ({company})** "
            f"in **{year}** is not available."
        )


    if metric in [
        "ROE",
        "ROA",
        "ROI",
        "Net Profit Margin"
    ]:

        formatted = f"{float(value):.2f}%"

    elif metric == "Number of Employees":

        formatted = f"{int(value):,}"

    else:

        formatted = format_number(value)


    return (
        f"**{company_name(company)} ({company})**\n\n"
        f"📅 Year: **{year}**\n\n"
        f"📊 {metric}: **{formatted}**"
    )


# ============================================================
# COMPARE COMPANIES
# ============================================================

def compare_companies_answer(
    companies,
    year,
    metric
):

    if len(companies) < 2:
        return None


    result = df[
        (df["Company"].isin(companies))
        &
        (df["Year"] == year)
    ]


    if result.empty:

        return (
            f"❌ No comparison data is available "
            f"for **{year}**."
        )


    answers = []

    values = []


    for company in companies:

        row = result[
            result["Company"] == company
        ]


        if row.empty:
            continue


        value = row.iloc[0][metric]


        if pd.isna(value):
            continue


        if metric in [
            "ROE",
            "ROA",
            "ROI",
            "Net Profit Margin"
        ]:

            formatted = f"{float(value):.2f}%"

        else:

            formatted = format_number(value)


        answers.append(
            f"• **{company_name(company)} ({company})**: "
            f"**{formatted}**"
        )


        values.append(
            (company, float(value))
        )


    if not answers:

        return (
            f"❌ {metric} data is not available "
            f"for the selected companies in {year}."
        )


    answer = (
        f"### 📊 {metric} Comparison — {year}\n\n"
        + "\n".join(answers)
    )


    # Determine winner

    if values:

        highest = max(
            values,
            key=lambda x: x[1]
        )

        answer += (
            f"\n\n🏆 **Highest:** "
            f"{company_name(highest[0])} "
            f"({highest[0]})"
        )


    return answer


# ============================================================
# GROWTH ANALYSIS
# ============================================================

def growth_answer(
    company,
    metric,
    question
):

    if not company or not metric:

        return None


    years = sorted(
        df[
            df["Company"] == company
        ]["Year"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )


    if len(years) < 2:

        return (
            "Not enough yearly data available "
            "to calculate growth."
        )


    found_years = re.findall(
        r"\b(20\d{2})\b",
        question
    )


    if len(found_years) >= 2:

        year1 = int(found_years[0])
        year2 = int(found_years[1])

    else:

        year1 = years[-2]
        year2 = years[-1]


    row1 = df[
        (df["Company"] == company)
        &
        (df["Year"] == year1)
    ]

    row2 = df[
        (df["Company"] == company)
        &
        (df["Year"] == year2)
    ]


    if row1.empty or row2.empty:

        return (
            f"❌ Growth data is not available "
            f"for {year1} and {year2}."
        )


    old_value = row1.iloc[0][metric]
    new_value = row2.iloc[0][metric]


    if pd.isna(old_value) or pd.isna(new_value):

        return (
            f"❌ {metric} data is incomplete "
            f"for the selected years."
        )


    if float(old_value) == 0:

        return (
            "Growth percentage cannot be calculated "
            "because the earlier value is zero."
        )


    growth = (
        (float(new_value) - float(old_value))
        / abs(float(old_value))
    ) * 100


    direction = (
        "increased"
        if growth >= 0
        else "decreased"
    )


    return (
        f"### 📈 Growth Analysis\n\n"
        f"**{company_name(company)} ({company})**\n\n"
        f"{metric} in {year1}: "
        f"**{format_number(old_value)}**\n\n"
        f"{metric} in {year2}: "
        f"**{format_number(new_value)}**\n\n"
        f"📊 {metric} **{direction} by "
        f"{abs(growth):.2f}%**."
    )


# ============================================================
# HIGHEST / LOWEST
# ============================================================

def ranking_answer(
    metric,
    highest=True
):

    if metric is None:

        metric = "Revenue"


    valid = df[
        ["Company", "Year", metric]
    ].dropna(
        subset=[metric]
    )


    if valid.empty:

        return (
            f"No valid {metric} data is available."
        )


    if highest:

        row = valid.loc[
            valid[metric].idxmax()
        ]

        title = "Highest"

    else:

        row = valid.loc[
            valid[metric].idxmin()
        ]

        title = "Lowest"


    value = row[metric]


    if metric in [
        "ROE",
        "ROA",
        "ROI",
        "Net Profit Margin"
    ]:

        formatted = f"{float(value):.2f}%"

    else:

        formatted = format_number(value)


    return (
        f"🏆 **{title} {metric}**\n\n"
        f"Company: **{company_name(row['Company'])} "
        f"({row['Company']})**\n\n"
        f"Year: **{int(row['Year'])}**\n\n"
        f"{metric}: **{formatted}**"
    )


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

def financial_summary(company):

    company_data = df[
        df["Company"] == company
    ].sort_values("Year")


    if company_data.empty:

        return (
            f"No financial data is available "
            f"for {company}."
        )


    latest = company_data.iloc[-1]

    year = int(latest["Year"])


    lines = [
        f"### 📋 Financial Summary",
        "",
        f"**{company_name(company)} ({company})**",
        f"Latest available year: **{year}**",
        ""
    ]


    metrics = [
        "Revenue",
        "Gross Profit",
        "Net Income",
        "EBITDA",
        "Cash Flow",
        "Market Cap",
        "ROE",
        "ROA",
        "ROI",
        "Net Profit Margin"
    ]


    for metric in metrics:

        if metric not in company_data.columns:
            continue


        value = latest[metric]


        if pd.isna(value):
            continue


        if metric in [
            "ROE",
            "ROA",
            "ROI",
            "Net Profit Margin"
        ]:

            formatted = f"{float(value):.2f}%"

        else:

            formatted = format_number(value)


        lines.append(
            f"• **{metric}:** {formatted}"
        )


    return "\n".join(lines)


# ============================================================
# DATASET QUESTIONS
# ============================================================

def dataset_answer(question):

    q = question.lower()


    if (
        "what companies" in q
        or "which companies" in q
        or "companies available" in q
    ):

        companies = sorted(
            df["Company"]
            .dropna()
            .unique()
            .tolist()
        )


        return (
            "### 🏢 Available Companies\n\n"
            + ", ".join(
                f"**{x}**"
                for x in companies
            )
        )


    if (
        "what years" in q
        or "years available" in q
        or "available years" in q
    ):

        years = sorted(
            df["Year"]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )


        return (
            f"### 📅 Available Years\n\n"
            f"Financial data is available from "
            f"**{min(years)} to {max(years)}**."
        )


    if (
        "how many rows" in q
        or "number of rows" in q
        or q.strip() == "rows"
    ):

        return (
            f"The dataset contains **{len(df)} rows**."
        )


    return None


# ============================================================
# EXACT ANSWER ENGINE
# ============================================================

def calculate_answer(question):

    q = question.lower().strip()


    # --------------------------------------------------------
    # COMPANY CODE
    # --------------------------------------------------------

    answer = company_code_answer(question)

    if answer:
        return answer


    # --------------------------------------------------------
    # DATASET QUESTIONS
    # --------------------------------------------------------

    answer = dataset_answer(question)

    if answer:
        return answer


    # --------------------------------------------------------
    # COMPANIES
    # --------------------------------------------------------

    companies = find_companies(question)

    year = find_year(question)

    metric = find_metric(question)


    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    comparison_words = [
        "compare",
        "comparison",
        "versus",
        " vs ",
        "difference between"
    ]


    if (
        len(companies) >= 2
        and metric
        and year
        and any(
            word in q
            for word in comparison_words
        )
    ):

        return compare_companies_answer(
            companies,
            year,
            metric
        )


    # --------------------------------------------------------
    # GROWTH
    # --------------------------------------------------------

    growth_words = [
        "growth",
        "grew",
        "increase",
        "increased",
        "decrease",
        "decreased",
        "change"
    ]


    if (
        company
        if False
        else False
    ):
        pass


    if (
        len(companies) >= 1
        and metric
        and any(
            word in q
            for word in growth_words
        )
    ):

        return growth_answer(
            companies[0],
            metric,
            question
        )


    # --------------------------------------------------------
    # HIGHEST
    # --------------------------------------------------------

    if (
        "highest" in q
        or "maximum" in q
        or "largest" in q
        or "top company" in q
    ):

        return ranking_answer(
            metric,
            highest=True
        )


    # --------------------------------------------------------
    # LOWEST
    # --------------------------------------------------------

    if (
        "lowest" in q
        or "minimum" in q
        or "smallest" in q
    ):

        return ranking_answer(
            metric,
            highest=False
        )


    # --------------------------------------------------------
    # FINANCIAL SUMMARY
    # --------------------------------------------------------

    if (
        "financial summary" in q
        or "performance summary" in q
        or "overall performance" in q
    ):

        if companies:

            return financial_summary(
                companies[0]
            )


        return (
            "Please mention a company, "
            "for example: "
            "**Give me Apple's financial summary.**"
        )


    # --------------------------------------------------------
    # SINGLE COMPANY + YEAR + METRIC
    # --------------------------------------------------------

    if (
        len(companies) >= 1
        and year
        and metric
    ):

        return single_company_answer(
            companies[0],
            year,
            metric
        )


    # --------------------------------------------------------
    # COMPANY + METRIC
    # Latest available year
    # --------------------------------------------------------

    if (
        len(companies) >= 1
        and metric
        and not year
    ):

        company = companies[0]

        company_data = df[
            df["Company"] == company
        ]


        if company_data.empty:

            return (
                f"No data is available for "
                f"{company}."
            )


        latest_year = int(
            company_data["Year"].max()
        )


        return single_company_answer(
            company,
            latest_year,
            metric
        )


    return None


# ============================================================
# OLLAMA FALLBACK
# ============================================================

def ask_llm(question):

    if llm is None:

        return (
            "I could not use the AI model. "
            "Please make sure Ollama is running."
        )


    companies = find_companies(question)

    year = find_year(question)

    metric = find_metric(question)


    relevant = df.copy()


    if companies:

        relevant = relevant[
            relevant["Company"].isin(
                companies
            )
        ]


    if year:

        relevant = relevant[
            relevant["Year"] == year
        ]


    # Never send unrelated sample rows

    if relevant.empty:

        return (
            "❌ I could not find the requested "
            "information in the uploaded dataset."
        )


    context = relevant.to_string(
        index=False
    )


    prompt = f"""
You are FinInsight AI.

Answer ONLY using the financial data below.

IMPORTANT RULES:

1. Never invent numbers.
2. Never use outside financial information.
3. If the data does not contain the answer, say:
   "The requested information is not available
   in the uploaded dataset."
4. Keep the answer short and professional.
5. Do not interpret "company code" as programming code.
6. Company codes such as AAPL, AMZN and MSFT are stock/company tickers.
7. Do not mention unrelated companies.
8. Do not create financial values that are not present.

FINANCIAL DATA:

{context}

USER QUESTION:

{question}

Answer clearly.
"""


    try:

        response = llm.invoke(
            prompt
        )

        return response.strip()

    except Exception:

        return (
            "I could not generate the AI response. "
            "Please make sure Ollama is running."
        )


# ============================================================
# CHAT HISTORY
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# QUICK QUESTIONS
# ============================================================

st.subheader("💡 Try These Questions")


col1, col2, col3 = st.columns(3)


with col1:

    if st.button(
        "🍎 Apple's code",
        use_container_width=True
    ):

        st.session_state.quick_question = (
            "What is Apple's code?"
        )


with col2:

    if st.button(
        "⚖️ Compare Apple & Microsoft",
        use_container_width=True
    ):

        st.session_state.quick_question = (
            "Compare Apple and Microsoft revenue in 2022"
        )


with col3:

    if st.button(
        "📈 Amazon growth",
        use_container_width=True
    ):

        st.session_state.quick_question = (
            "What was Amazon revenue growth from 2022 to 2023?"
        )


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask a financial question..."
)


# Quick question

if (
    "quick_question" in st.session_state
    and st.session_state.quick_question
):

    question = st.session_state.quick_question

    st.session_state.quick_question = None


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    with st.chat_message("user"):

        st.markdown(question)


    # Exact answer first

    answer = calculate_answer(
        question
    )


    # AI fallback

    if answer is None:

        answer = ask_llm(
            question
        )


    with st.chat_message(
        "assistant"
    ):

        st.markdown(answer)


    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )