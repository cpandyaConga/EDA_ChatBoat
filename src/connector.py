import io
from flask import Blueprint, request, abort, jsonify, make_response
import json
import datetime
from openai import AzureOpenAI
import streamlit as st
import re
import pandas as pd
# Make the Snowflake connection
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector
from snowflake.connector import DictCursor
from config import creds
from prompts import get_system_prompt
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import StringIO


def connect() -> snowflake.connector.SnowflakeConnection:
    if 'private_key' in creds:
        if not isinstance(creds['private_key'], bytes):
            p_key = serialization.load_pem_private_key(
                    creds['private_key'].encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
            pkb = p_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption())
            creds['private_key'] = pkb
    return snowflake.connector.connect(**creds)

conn = connect()
messages= []
# Make the API endpoints
connector = Blueprint('connector', __name__)




## Top 10 customers in date range
dateformat = '%Y-%m-%d'

# Initialize the chat messages history
client = AzureOpenAI(
    azure_endpoint="https://svc-openai-poc.openai.azure.com/",
    api_key="4c4927a7c697459ea5896bbed6f4d84a",
    api_version="2024-02-15-preview"
)

@connector.route('/customers/top10')
def customers_top10():
    # Validate arguments
    sdt_str = request.args.get('start_range') or '1995-01-01'
    edt_str = request.args.get('end_range') or '1995-03-31'
    try:
        sdt = datetime.datetime.strptime(sdt_str, dateformat)
        edt = datetime.datetime.strptime(edt_str, dateformat)
    except:
        abort(400, "Invalid start and/or end dates.")
    sql_string = '''
        SELECT
            o_custkey
          , SUM(o_totalprice) AS sum_totalprice
        FROM snowflake_sample_data.tpch_sf10.orders
        WHERE o_orderdate >= '{sdt}'
          AND o_orderdate <= '{edt}'
        GROUP BY o_custkey
        ORDER BY sum_totalprice DESC
        LIMIT 10
    '''
    sql = sql_string.format(sdt=sdt, edt=edt)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        return make_response(jsonify(res.fetchall()))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")

## Monthly sales for a clerk in a year
@connector.route('/clerk/<clerkid>/yearly_sales/<year>')
def clerk_montly_sales(clerkid, year):
    # Validate arguments
    try: 
        year_int = int(year)
    except:
        abort(400, "Invalid year.")
    if not clerkid.isdigit():
        abort(400, "Clerk ID can only contain numbers.")
    clerkid_str = f"Clerk#{clerkid}"
    sql_string = '''
        SELECT
            o_clerk
          ,  Month(o_orderdate) AS month
          , SUM(o_totalprice) AS sum_totalprice
        FROM snowflake_sample_data.tpch_sf10.orders
        WHERE Year(o_orderdate) = {year}
          AND o_clerk = '{clerkid}'
        GROUP BY o_clerk, month
        ORDER BY o_clerk, month
    '''
    sql = sql_string.format(year=year_int, clerkid=clerkid_str)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        return make_response(jsonify(res.fetchall()))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")


## Monthly sales for a clerk in a year
@connector.route('/getsessions')
def getsessions():
   # print("in getsessions: ")
    sql_string = '''
        SELECT distinct 
            SESSIONNAME
        FROM APTTUS_DB.PUBLIC.CHAT_DATA
     '''
    sql = sql_string
   # print("sql:" + sql)
    try:
        res = conn.cursor(DictCursor).execute(sql)
    #    print("in exec:"+ sql)
        return make_response(jsonify(res.fetchall()))
    except Exception as e:
     #   print(e)  # Print the error details for debugging
        abort(500, "Error1 reading from Snowflake. Check the logs for details.")

@connector.route('/getcharts/<session>')
def getchats(session):
   # print("in getsessions: ")
    sql_string = '''
        SELECT
            *
        FROM APTTUS_DB.PUBLIC.CHAT_DATA
        where SESSIONNAME = '{session}'
     '''
    sql = sql_string.format(session=session)
  #  print("sql:" + sql)
    try:
        res = conn.cursor(DictCursor).execute(sql)
   #     print("in exec:"+ sql)
        return make_response(jsonify(res.fetchall()))
    except Exception as e:
    #    print(e)  # Print the error details for debugging
        abort(500, "Error2 reading from Snowflake. Check the logs for details.")
# Fetch data from Snowflake
# def fetch_feedback_from_snowflake():
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM customer_feedback")
#     feedback_data = cursor.fetchall()
#     cursor.close()
#     return feedback_data
def generate_line_chart(data):
    plt.figure(figsize=(8, 4))  # Adjust figure size
    sns.lineplot(x=pd.to_datetime(data[data.columns[0]]), y=data[data.columns[1]])
    plt.xlabel("Dates", fontsize=14, fontweight='bold')  # Customize x-axis label
    plt.ylabel("Values", fontsize=14, fontweight='bold')  # Customize y-axis label
    plt.title("Line Chart", fontsize=16, fontweight='bold')  # Customize title
    plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility
    plt.tight_layout()  # Adjust layout for better appearance
    
    # Save plot to a buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Convert plot to base64 encoded string
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Close the plot
    plt.close()
    
    # Return HTML string for the line chart
    return f'<img src="data:image/png;base64,{image_base64}" alt="Line Chart">'


@connector.route('/getAnswers/<sessionname>/<userText>')
def getAnswers(sessionname,userText):
  try:
    global messages
    if not messages:
        print("In MEssages")
        messages.append({"role": "system", "content": get_system_prompt()})
    messages.append({"role": "user", "content": userText})
    response = ""
    for delta in client.chat.completions.create(
                model="gpt-35-turbo",
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                stream=True,
            ):
                if delta.choices:
                    response += (delta.choices[0].delta.content or "")
                else:
                    response += ""
            #   resp_container.markdown(response)
    message = {"role": "assistant", "content": response}
    #  print("sql:" + sql)
    sql_query_pattern = r'```sql\n(.*?)```'
    sample_questions_pattern = r'```SampleQuestion\n(.*?)```'
    # Extract SQL query
    sql_query_match = re.search(sql_query_pattern, response, re.DOTALL)
    sql_query = sql_query_match.group(1).strip() if sql_query_match else 'null'
    sql_querytoExecute = sql_query_match.group(1).strip() if sql_query_match else 'null'

    # Extract sample questions
    sample_questions_match = re.search(sample_questions_pattern, response, re.DOTALL)
    sample_questions = sample_questions_match.group(1).strip() if sample_questions_match else 'null'
    if response is not None:
        response = response.replace("'", "''")
    if sample_questions is not None:
        sample_questions = sample_questions.replace("'", "''")
    sql = sql_query
    print("Query to execute: " + sql)
    html_chart = ""
    html_table = ""
    try:
        res = conn.cursor(DictCursor).execute(sql)
        result = res.fetchall()
        if len(result) > 0:
            df = pd.DataFrame(result)  
            html_table = df.to_html(index=False)

            if "trend" in userText.lower():
                # html_chart = """
                #             <canvas id="myChart" width="400" height="400"></canvas>
                #             <script>
                #                 var ctx = document.getElementById('myChart').getContext('2d');
                #                 var myChart = new Chart(ctx, {
                #                     type: "line",
                #                     data: {
                #                         labels: %s,
                #                         datasets: [{
                #                             label: "Value",
                #                             data: %s,
                #                             borderColor: "rgb(75, 192, 192)",
                #                             tension: 0.1
                #                         }]
                #                     }
                #                 });
                #             </script>
                #             """ %(df.iloc[:, 0].to_json(), df.iloc[:, 1].to_json())
            # Combine HTML table and chart
                html_chart = '<button class="showChartButton" onclick="showChart(1)">Show Chart</button>'
                html_table = f'<div style="max-height: 500px; overflow-y: auto;"> {html_table}</div><div>{html_chart}</div>'
        else:
            df = pd.DataFrame(columns=[''])
            df.loc[0] = ['No Data Found']
            html_table = df.to_html(index=False)
    # print("HTML Table : " + html_table)
    except Exception as e:
        df = pd.DataFrame(columns=[''])
        df.loc[0] = ['No Data Found']
        html_table = df.to_html(index=False)
    try:
        sql_string = """
            INSERT INTO 
            APTTUS_DB.PUBLIC.CHAT_DATA
            (SessionId, UserName, SessionName,  Question,Timestamp,Answer,Query,SAMPLEQUESTION) VALUES
            ('1', 'Cheta Pandya', '{SessionName}', '{Question}',CURRENT_TIMESTAMP,'{Answer}','{sql_query}','{SampleQuestion}')
        """
        sql = sql_string.format(SessionName=sessionname,Question=userText,Answer=response,sql_query=html_table,SampleQuestion=sample_questions)
        #sql = sql_string.format(sessionname=sessionname,question=userText,answer=response,query=sql_query,samplequestion=sample_questions)
        #values = ('1', 'Cheta Pandya', sessionname, userText)
        cursor = conn.cursor(DictCursor)
        print("Insert Query  " + sql)
        res = cursor.execute(sql)
        return  jsonify({"role": "assistant", "content": response})
    
    except Exception as e:
       abort(500, "Error2 reading from Snowflake. Check the logs for details.") 
    return  jsonify({"role": "assistant", "content": response})
  except Exception as e:
    #    print(e)  # Print the error details for debugging
        abort(500, "Error2 reading from Snowflake. Check the logs for details.")


@connector.route('/getDataframe/<session>')
def getDataframe(session):
   # print("in getsessions: ")
    print("in exec:"+ session)
    sql = session
  #  print("sql:" + sql)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        print("in exec:"+ sql)
        result= res.fetchall()
        print(result)
            # Format the result into an HTML table
        html_table = "<table>"
        for row in result:
            html_table += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        html_table += "</table>"
        print(html_table)
    # Return the HTML table as the response
        return html_table
    except Exception as e:
    #    print(e)  # Print the error details for debugging
        abort(500, "Error4 reading from Snowflake. Check the logs for details.")