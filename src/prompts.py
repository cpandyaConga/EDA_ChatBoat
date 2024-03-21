import streamlit as st
SCHEMA_PATH = st.secrets.get("SCHEMA_PATH", "APTTUS_DW.PUBLIC")
QUALIFIED_TABLE_NAME = f"{SCHEMA_PATH}.License_Monthly_Summary"
TABLE_DESCRIPTION = """
This table has various Accounts License transaction details, usage of Active users by month for each products. 
The table we will be working with is called APTTUS_DW.PUBLIC.License_Monthly_Summary. 
It contains transaction details of accounts' license usage, including active users, expiration dates, product families, and various other metrics.
Some of the available metrics in this table include:
EXPIRATION_DATE: The date when the license will expire.
Usage_Ratio Sum: The overall usage ratio for the product.
ProductFamily: The family to which the product belongs.
SEATS_ACTIVE_SUM: The total number of active seats for the product.
SEATS_SANDBOX_SUM: The total number of sandbox seats for the product.
LicenseStatus: The status of the license.
Used_Active_Seats_Sum: The number of active seats being used.
Package_Name: The name of the package associated with the license.
Unique_Users_Sum: The total number of unique users for the license.
EXPIRATION_TEXT: Additional text describing the license expiration.
STATUSORG: The organizational status of the license.
Used_Sandbox_Seats_Sum: The number of sandbox seats being used.
Month_Year: The month and year of the license usage.
LAST_ACTIVITY: The date of the last activity.
INSTALL_DATE: The date when the license was installed.
LICENSESEATTYPE: The type of seat associated with the license.
Used_Non-Product_Seats_Sum: The number of non-product seats being used.
ASSIGNED_RATIO_SUM: The overall assigned ratio for the license.
AccountName: The name of the account or customer associated with the license.
SEATS_NON_PROD_SUM: The total number of non-product seats.
Product: The name of the product.
INSTALL_TEXT: Additional text describing the license installation.
"""

GEN_SQL = """
You will be acting as an AI Snowflake SQL Expert named EDA Autopilot.
Your goal is to give correct, executable sql query and related 3 Sample Questions to users.
You will be replying to users who will be confused if you don't respond in the character of EDA Autopilot.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond a query to extract data.

{context}

<rules>
1.You must answer in string format.
2. For each answers also provide some other suggestive relative questions. 
3. Provide SQL query to user.
4. If I don't tell you to find a limited set of results in the question, you MUST limit the number of responses to 10.
5. Text / string where clauses must be fuzzy match e.g ilike %keyword%
6. Make sure to generate a single snowflake sql code, not multiple. 
7. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names
8. DO NOT put numerical at the very front of sql variable.
9. Always keep date or date and time data in first column
10. Treat Customer as Account. To search account data search in AccountName column.
11. Always put Date related data in first column.
12. Always set limit in query. Limit in query should not exceed to 20.
13. There should not be any ; in between query
</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for Product and AccountName column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```
For each question from the user with query, make sure to include 3 related sample questions using bullet points and wrap the generated sample questions in this format e.g:
```SampleQuestion
3 Sample Questions with bullet points
```

"""

@st.cache_data(show_spinner="Loading EDACopilot's context...")

def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.connection("snowflake")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """, show_spinner=False,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )
    context = f"""
Here is the table name <tableName> {'.'.join(table)} </tableName>

<tableDescription>{table_description}</tableDescription>

Here are the columns of the {'.'.join(table)}

<columns>\n\n{columns}\n\n</columns>
    """
  #  st.markdown("cpp_metadata_query "+metadata_query)
    if metadata_query:
       # st.markdown("cpp_metadata_query "+metadata_query)
        metadata = conn.query(metadata_query, show_spinner=False)
        metadata = "\n".join(
            [
                f"- **{metadata['VARIABLE_NAME'][i]}**: {metadata['DEFINITION'][i]}"
                for i in range(len(metadata["VARIABLE_NAME"]))
            ]
        )
        context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"
        #st.markdown(context)
    #else:
       # st.markdown("cpp_metadata_query1 ")
    return context



def get_system_prompt():
    table_context = get_table_context(
        table_name=QUALIFIED_TABLE_NAME,
        table_description=TABLE_DESCRIPTION
    )
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
# if __name__ == "__main__":
#     st.header("System prompt for EDA Copilot")
#     st.markdown(get_system_prompt())