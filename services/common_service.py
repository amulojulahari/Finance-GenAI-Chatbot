import re
import pandas as pd
import streamlit as st

from services import openai_service as ois


def get_active_ai_service():
    return ois


def get_embeddings():
    return None


@st.cache_resource(show_spinner=False)
def get_gemini_client():
    return ois.get_gemini_client()


class LocalCSVAgent:

    def __init__(self, files):
        self.dataframes = []

        for file in files:
            try:
                filename = file.name.lower()

                if filename.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(file)
                elif filename.endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    continue

                df = df.dropna(how="all")
                df = df.dropna(axis=1, how="all")

                self.dataframes.append(df)

            except Exception as e:
                print("File reading error:", e)

        if self.dataframes:
            self.df = pd.concat(
                self.dataframes,
                ignore_index=True
            )
        else:
            self.df = pd.DataFrame()

    def get_data_context(self):
        if self.df.empty:
            return "No financial data available."

        return self.df.to_string(index=False)

    def calculate_basic_result(self, question):

        if self.df.empty:
            return "No financial data available."

        df = self.df
        q = question.lower()

        # Normalize column names
        columns = {str(c).lower(): c for c in df.columns}

        # ---------------- YEAR ----------------
        year_match = re.search(r"\b(20\d{2})\b", q)
        year = int(year_match.group(1)) if year_match else None

        # ---------------- YEAR-SPECIFIC DATA ----------------
        if year is not None and "year" in columns:
            year_col = columns["year"]
            row = df[df[year_col] == year]

            if not row.empty:
                row = row.iloc[0]

                revenue = row.get(columns.get("revenue"), None)
                expenses = row.get(columns.get("expenses"), None)
                profit = row.get(columns.get("net profit"), None)

                # Loss
                if "loss" in q:
                    if revenue is not None and expenses is not None:
                        loss = float(expenses) - float(revenue)

                        if loss > 0:
                            return (
                                f"In {year}, the company had a loss of "
                                f"₹{loss:,.0f}."
                            )
                        else:
                            actual_profit = float(revenue) - float(expenses)
                            return (
                                f"There was no loss in {year}. "
                                f"The company made a profit of "
                                f"₹{actual_profit:,.0f}."
                            )

                # Profit
                if "profit" in q:
                    if profit is not None:
                        return (
                            f"Net profit in {year} was "
                            f"₹{float(profit):,.0f}."
                        )

                    if revenue is not None and expenses is not None:
                        result = float(revenue) - float(expenses)
                        return (
                            f"Profit in {year} was "
                            f"₹{result:,.0f}."
                        )

                # Revenue
                if "revenue" in q:
                    if revenue is not None:
                        return (
                            f"Revenue in {year} was "
                            f"₹{float(revenue):,.0f}."
                        )

                # Expenses
                if "expense" in q or "expenses" in q:
                    if expenses is not None:
                        return (
                            f"Expenses in {year} were "
                            f"₹{float(expenses):,.0f}."
                        )

                # Assets
                if "asset" in q:
                    asset_col = columns.get("assets")

                    if asset_col:
                        return (
                            f"Assets in {year} were "
                            f"₹{float(row[asset_col]):,.0f}."
                        )

                # Liabilities
                if "liabilit" in q:
                    liability_col = columns.get("liabilities")

                    if liability_col:
                        return (
                            f"Liabilities in {year} were "
                            f"₹{float(row[liability_col]):,.0f}."
                        )

        # ---------------- TOTALS ----------------

        if "total revenue" in q:
            col = columns.get("revenue")
            if col:
                return f"Total revenue was ₹{df[col].sum():,.0f}."

        if "total expense" in q:
            col = columns.get("expenses")
            if col:
                return f"Total expenses were ₹{df[col].sum():,.0f}."

        if "total profit" in q or "total net profit" in q:
            col = columns.get("net profit")

            if col:
                return f"Total net profit was ₹{df[col].sum():,.0f}."

        # ---------------- HIGHEST / LOWEST ----------------

        if "highest revenue" in q:
            col = columns.get("revenue")

            if col:
                row = df.loc[df[col].idxmax()]
                return (
                    f"The highest revenue was "
                    f"₹{row[col]:,.0f} in {int(row['Year'])}."
                )

        if "lowest revenue" in q:
            col = columns.get("revenue")

            if col:
                row = df.loc[df[col].idxmin()]
                return (
                    f"The lowest revenue was "
                    f"₹{row[col]:,.0f} in {int(row['Year'])}."
                )

        if "highest profit" in q:
            col = columns.get("net profit")

            if col:
                row = df.loc[df[col].idxmax()]
                return (
                    f"The highest net profit was "
                    f"₹{row[col]:,.0f} in {int(row['Year'])}."
                )

        if "lowest profit" in q:
            col = columns.get("net profit")

            if col:
                row = df.loc[df[col].idxmin()]
                return (
                    f"The lowest net profit was "
                    f"₹{row[col]:,.0f} in {int(row['Year'])}."
                )

        # ---------------- LOSS YEARS ----------------

        if "loss" in q and "year" in q:

            if "Revenue" in df.columns and "Expenses" in df.columns:

                loss_rows = df[df["Expenses"] > df["Revenue"]]

                if loss_rows.empty:
                    return "There were no loss-making years in the uploaded data."

                years = loss_rows["Year"].tolist()

                return (
                    "Loss occurred in these years: "
                    + ", ".join(str(int(y)) for y in years)
                )

        # ---------------- PROFIT MARGIN ----------------

        if "profit margin" in q:

            if "Revenue" in df.columns and "Net Profit" in df.columns:

                revenue = df["Revenue"].sum()
                profit = df["Net Profit"].sum()

                if revenue != 0:
                    margin = (profit / revenue) * 100

                    return (
                        f"Overall profit margin was "
                        f"{margin:.2f}%."
                    )

        # ---------------- DATA ----------------

        if (
            "show data" in q
            or "show the data" in q
            or "complete table" in q
            or "all data" in q
        ):
            return df.to_string(index=False)

        return None

    def invoke(self, prompt):

        if self.df.empty:
            return "No financial data was found in the uploaded file."

        # First try direct calculation
        direct_answer = self.calculate_basic_result(prompt)

        if direct_answer:
            return direct_answer

        # ---------------- GEMINI ----------------

        try:

            client = get_gemini_client()

            if client is None:
                return "Gemini API is not configured."

            data_context = self.get_data_context()

            gemini_prompt = f"""
You are a Finance GPT assistant.

Answer the user's question using ONLY the uploaded financial data.

Do not invent numbers.

If the user asks about loss:
- Calculate loss as Expenses - Revenue when Expenses are greater than Revenue.
- If Expenses are not greater than Revenue, clearly say there was no loss and give the profit.

If the user asks about profit:
- Use the Net Profit column when available.
- Otherwise calculate Revenue - Expenses.

If the user asks for comparison, compare the actual values from the data.

Give a clear, simple answer.
Use ₹ for Indian currency.
Use commas for large numbers.

Financial data:

{data_context}

User question:
{prompt}
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=gemini_prompt
            )

            return response.text

        except Exception as e:

            print("Gemini error:", e)

            return (
                "I couldn't process that question. "
                "Please try another finance question."
            )


def get_csv_agent(_llm, files):
    return LocalCSVAgent(files)
import re
import pandas as pd
import streamlit as st

from services import openai_service as ois


def get_active_ai_service():
    return ois


def get_embeddings():
    return None


@st.cache_resource
def get_gemini_client():
    try:
        return ois.get_gemini_client()
    except Exception:
        return None


class LocalCSVAgent:

    def __init__(self, files):
        self.files = files
        self.df = self.load_data()

    def load_data(self):
        frames = []

        for file in self.files:
            try:
                file_name = file.name.lower()

                if file_name.endswith(".csv"):
                    df = pd.read_csv(file)
                elif file_name.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(file)
                else:
                    continue

                df.columns = [
                    str(col).strip().lower()
                    for col in df.columns
                ]

                # Clean text columns
                for col in df.select_dtypes(include="object").columns:
                    df[col] = df[col].astype(str).str.strip()

                frames.append(df)

            except Exception as e:
                st.error(f"Could not read {file.name}: {e}")

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)

        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")

        return df

    # --------------------------------------------------
    # BASIC BANKING ANALYSIS
    # --------------------------------------------------

    def calculate_basic_result(self, question):

        if self.df.empty:
            return "No banking data is loaded."

        df = self.df
        q = question.lower().strip()

        # ----------------------------------------------
        # TOTAL CUSTOMERS
        # ----------------------------------------------

        if (
            ("how many" in q or
             "number of" in q or
             "count" in q or
             "total" in q)
            and "customer" in q
        ):

            customer_columns = [
                col for col in df.columns
                if "customer" in col and "id" in col
            ]

            if customer_columns:
                count = df[customer_columns[0]].nunique()
            else:
                count = len(df)

            return f"👥 Total customers: {count:,}"

        # ----------------------------------------------
        # TOTAL RECORDS
        # ----------------------------------------------

        if (
            ("how many" in q or "number of" in q)
            and ("records" in q or "rows" in q)
        ):
            return f"📋 Total records: {len(df):,}"

        # ----------------------------------------------
        # AVERAGE BALANCE
        # ----------------------------------------------

        if "average" in q and "balance" in q:

            if "balance" in df.columns:

                value = pd.to_numeric(
                    df["balance"],
                    errors="coerce"
                ).mean()

                return f"💰 Average account balance: {value:,.2f}"

        # ----------------------------------------------
        # TOTAL BALANCE
        # ----------------------------------------------

        if (
            ("total" in q or "sum" in q)
            and "balance" in q
        ):

            if "balance" in df.columns:

                value = pd.to_numeric(
                    df["balance"],
                    errors="coerce"
                ).sum()

                return f"💰 Total account balance: {value:,.2f}"

        # ----------------------------------------------
        # HIGHEST BALANCE
        # ----------------------------------------------

        if (
            ("highest" in q or
             "maximum" in q or
             "max" in q)
            and "balance" in q
        ):

            if "balance" in df.columns:

                values = pd.to_numeric(
                    df["balance"],
                    errors="coerce"
                )

                return f"🏆 Highest balance: {values.max():,.2f}"

        # ----------------------------------------------
        # LOWEST BALANCE
        # ----------------------------------------------

        if (
            ("lowest" in q or
             "minimum" in q or
             "min" in q)
            and "balance" in q
        ):

            if "balance" in df.columns:

                values = pd.to_numeric(
                    df["balance"],
                    errors="coerce"
                )

                return f"📉 Lowest balance: {values.min():,.2f}"

        # ----------------------------------------------
        # HOUSING LOAN
        # ----------------------------------------------

        if (
            "housing" in q
            and "loan" in q
        ):

            if "housing" in df.columns:

                count = (
                    df["housing"]
                    .astype(str)
                    .str.lower()
                    .eq("yes")
                    .sum()
                )

                return f"🏠 Customers with housing loans: {count:,}"

        # ----------------------------------------------
        # PERSONAL LOAN
        # ----------------------------------------------

        if (
            "personal loan" in q
            or (
                "loan" in q
                and "personal" in q
            )
        ):

            if "loan" in df.columns:

                count = (
                    df["loan"]
                    .astype(str)
                    .str.lower()
                    .eq("yes")
                    .sum()
                )

                return f"💳 Customers with personal loans: {count:,}"

        # ----------------------------------------------
        # DEFAULT
        # ----------------------------------------------

        if "default" in q:

            if "default" in df.columns:

                count = (
                    df["default"]
                    .astype(str)
                    .str.lower()
                    .eq("yes")
                    .sum()
                )

                return f"⚠️ Customers with default: {count:,}"

        # ----------------------------------------------
        # TERM DEPOSIT
        # ----------------------------------------------

        if (
            "term deposit" in q
            or "deposit" in q
            or "subscribed" in q
        ):

            if "y" in df.columns:

                yes_count = (
                    df["y"]
                    .astype(str)
                    .str.lower()
                    .eq("yes")
                    .sum()
                )

                total = len(df)

                percentage = (
                    yes_count / total * 100
                    if total > 0
                    else 0
                )

                return (
                    f"🎯 Term deposit subscribers: "
                    f"{yes_count:,} / {total:,} "
                    f"({percentage:.2f}%)"
                )

        # ----------------------------------------------
        # YES / NO DISTRIBUTION
        # ----------------------------------------------

        if (
            "yes" in q
            and "no" in q
            and "deposit" in q
        ):

            if "y" in df.columns:

                result = df["y"].value_counts()

                return (
                    f"🎯 Subscription distribution:\n\n"
                    f"Yes: {result.get('yes', 0):,}\n"
                    f"No: {result.get('no', 0):,}"
                )

        # ----------------------------------------------
        # JOB ANALYSIS
        # ----------------------------------------------

        if (
            "job" in q
            and (
                "most" in q
                or "highest" in q
                or "popular" in q
            )
        ):

            if "job" in df.columns:

                job = df["job"].value_counts().idxmax()
                count = df["job"].value_counts().max()

                return (
                    f"💼 Most common job category: "
                    f"{job} ({count:,} customers)"
                )

        # ----------------------------------------------
        # EDUCATION
        # ----------------------------------------------

        if (
            "education" in q
            and (
                "most" in q
                or "highest" in q
                or "popular" in q
            )
        ):

            if "education" in df.columns:

                education = (
                    df["education"]
                    .value_counts()
                    .idxmax()
                )

                count = (
                    df["education"]
                    .value_counts()
                    .max()
                )

                return (
                    f"🎓 Most common education level: "
                    f"{education} ({count:,} customers)"
                )

        # ----------------------------------------------
        # AGE
        # ----------------------------------------------

        if (
            "average age" in q
            or "mean age" in q
        ):

            if "age" in df.columns:

                value = pd.to_numeric(
                    df["age"],
                    errors="coerce"
                ).mean()

                return f"👤 Average customer age: {value:.2f}"

        # ----------------------------------------------
        # CAMPAIGN
        # ----------------------------------------------

        if (
            "campaign" in q
            and (
                "average" in q
                or "mean" in q
            )
        ):

            if "campaign" in df.columns:

                value = pd.to_numeric(
                    df["campaign"],
                    errors="coerce"
                ).mean()

                return (
                    f"📞 Average campaign contacts: "
                    f"{value:.2f}"
                )

        # ----------------------------------------------
        # CONTACT METHOD
        # ----------------------------------------------

        if (
            "contact" in q
            and (
                "most" in q
                or "common" in q
            )
        ):

            if "contact" in df.columns:

                contact = (
                    df["contact"]
                    .value_counts()
                    .idxmax()
                )

                count = (
                    df["contact"]
                    .value_counts()
                    .max()
                )

                return (
                    f"📞 Most common contact method: "
                    f"{contact} ({count:,})"
                )

        # ----------------------------------------------
        # HIGH RISK INDICATORS
        # ----------------------------------------------

        if (
            "risk" in q
            or "risky" in q
            or "high risk" in q
        ):

            risk_count = 0

            if "loan" in df.columns:
                risk_count += (
                    df["loan"]
                    .astype(str)
                    .str.lower()
                    .eq("yes")
                    .sum()
                )

            if "default" in df.columns:
                risk_count += (
                    df["default"]
                    .astype(str)
                    .str.lower()
                    .eq("yes")
                    .sum()
                )

            return (
                "⚠️ Banking Risk Indicators\n\n"
                f"Customers with loan: "
                f"{risk_count:,} or fewer depending on overlapping records.\n\n"
                "Note: These are warning indicators, "
                "not confirmed fraud or credit decisions."
            )

        # ----------------------------------------------
        # SHOW DATA
        # ----------------------------------------------

        if (
            "show data" in q
            or "display data" in q
            or "sample data" in q
        ):

            return df.head(10).to_string(index=False)

        return None

    # --------------------------------------------------
    # GEMINI
    # --------------------------------------------------

    def ask_gemini(self, question):

        client = get_gemini_client()

        if client is None:
            return None

        try:

            sample = self.df.head(100).to_string(
                index=False
            )

            prompt = f"""
You are a Banking Data Analysis Assistant.

The user uploaded a banking dataset.

Answer the user's question using ONLY the
provided dataset context.

Do not invent numbers.

If the question requires calculation,
use the dataset values.

Explain the answer in simple language.

Dataset columns:
{list(self.df.columns)}

Dataset sample:
{sample}

User question:
{question}
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return response.text

        except Exception as e:

            print("GEMINI ERROR:", repr(e))

            return None

    # --------------------------------------------------
    # MAIN INVOKE
    # --------------------------------------------------

    def invoke(self, question):

        # First try direct banking analysis
        answer = self.calculate_basic_result(
            question
        )

        if answer:
            return answer

        # Then Gemini
        answer = self.ask_gemini(question)

        if answer:
            return answer

        return (
            "I couldn't process that question. "
            "Please try another banking question."
        )


def get_csv_agent(_llm, files):

    return LocalCSVAgent(files)