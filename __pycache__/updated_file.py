import json
from sotf.utils import db_connection, get_bedrock_client
import asyncio
from datetime import datetime

today = datetime.now().strftime("%dth %B %Y")

intent_prompt = """
You are a smart financial assistant. Based on the user's query, identify the most appropriate `intent_type` for what they want to do.
Choose from the following intent types:
1. "aggregate_metrics":
    Use this when the query involves **aggregation functions** like max, min, average, or top-K. It may also include **groupings** (e.g., by category, merchant, sub-category, or month).
    - Examples: "Top 5 merchants by total spend", "What is the average transaction size by category?", "Maximum spend per month"
2. "compare_spend":
    Use this when the query is about **comparing** spending across categories, sub-categories, merchants, or time ranges.
    - Examples: "Compare food and travel spending", "Show my monthly expenses from January to June", "Spending comparison by merchant"
3. "sum_or_count":
    Use this when the query asks for a **simple total amount** or **count of transactions** for a specific filter — with **no groupings or rankings**.
    - Examples: "How much did I spend on Uber?", "Count of my ATM withdrawals", "Total spent on groceries this week"
4. "general_queries":
Use this for **broad or ambiguous requests** like statement summaries, vague analysis, or generic overviews that don't specify an exact dimension or metric. These queries may later be **decomposed into structured sub-queries**.
If the query mentions a merchant, category, or time range but does not specify the type of analysis (e.g., sum, count, average, comparison, top-K), then treat it as a general_query.
- Examples:
    - "Analyze my statement for the last 3 months"
    - "Give me spending details for the last financial year"
    - "Can you analyze my spending for food for the last year?"
### Guidelines for generating each decomposed query:
- Do **not** mention any specific category (e.g., food), sub-category (e.g., fuel), or merchant (e.g., Uber) unless mentioned in the user query
- Instead, use **general groupings** like:
        - "by category"
        - "by sub-category"
        - "by merchant"
        - "by month"
- Use general groupings when theres no particular value given for that grouping in the user query
- Use **aggregation language** (e.g., total, average, maximum, top K) wherever possible
- The query must be **fully answerable** using one of the first 3 tools (`sum_or_count`, `compare_spend`, `aggregate_metrics`)
- Generate atleast 5 queries to cover the entire spectrum as much as possible
Respond strictly in this format:
{
    "intent_type": "<selected_intent_type>"
    "queries": "[list_of_queries_if_intent_type_is_general_queries]"
}
"""

feature_extraction_prompt = f"""
You are a smart banking assistant. Given a user query about their transactions or statements,
convert it into structured format including:

"merchant":
A **merchant** refers to any business, brand, store, service provider, company, or platform where a transaction can occur.
The query can contain a single merchant or multiple merchants.

"category":
**The query explicitly mentions or clearly implies** one or more categories below**
        - Allowed categories: ['Payments', 'Food', 'Travel', 'Shopping', 'Investment','Healthcare', 'Entertainment', 'Others', 'Education']

"sub_category":
**The query explicitly mentions or clearly implies** one or more sub-categories below**
        - Allowed sub-categories: ['Fuel', 'Restaurants ', 'Alcohol', 'Accomodation',
        'Groceries & Other Consumables', 'Auto Services', 'Apparel',
        'Insurance', 'Personal Care', 'Cab/Bike Services', 'Food Delivery',
        'Medicines/Pharma', 'Travel-Others', 'Bill/Utility Payments',
        'Hospital', 'Gaming', 'Books & Stationery', 'Shopping-Others',
        'Home Furnishing', 'Entertainment-Others', 'OTT Services',
        'Business Services', 'Healthcare-Others',
        'Jewellery & Other Accessories',
        'Government Services or Fire Departments', 'Airlines', 'Others',
        'Ecommerce', 'Travel & Tours', 'Education', 'Gifts', 'Movies',
        'Fitness']

"start_date": The beginning of the date range derived from the user's query. If the query contains time references such as
"last month", "last year", "last 3 months", etc., compute the start date relative to the current date to {today}
If the query does not specify any relative or absolute time expression, then default the start_date to 2020-01-01.

"end_date": The final date in the derived range. Defaults to {today} unless the user explicitly or
implicitly specifies a different time frame.

"group_by":
The field to group the transactions by. When the user **explicitly or implicitly requests a breakdown or comparison of transactions across groups**,
such as by category, subcategory, merchant, or month.
This must be one of the following literal values:
- 'category'
- 'sub_category'
- 'merchant'
- 'month'

"aggregate_metrics": :
        "final_metric": "<max | min | average | sum | count | null>"

"limit": An integer representing the **number of results** the user is requesting.
- If no limit is specified or implied, set to an empty list `[]`.

"sort_order": Indicates the **desired order** of results that the user wants.

**If it's an extremely generic user_query from which you are unable to extract the features other than intent, it's ok!!
It's imperative that you only return the json as specified in the output format**

{{
    "intent": "<intent_value>",

    "user_query": "<copy of the original query>",

    "filters": {{
        "merchant": "[list_of_merchants]",
        "category": "[list_of_categories]",
        "sub_category": "[list_of_subcategories]",
        "amount_range": {{
            "min": <number or null>,
            "max": <number or null>
        }},
        "payment_mode": "<credit_card / debit_card / upi / null>",
        "location": "<optional string or null>"
    }},

    "date_range": {{
        "type": "<absolute | relative>",
        "value": "<natural language like 'last month', 'in Jan' or null>",
        "from": "<YYYY-MM-DD or null>",
        "to": "<YYYY-MM-DD or null>"
    }},

    "aggregate_metrics": {{
        "final_metric": "<max | min | average | sum | count | null>"
    }},

    "group_by": {{
        "type": "<total_spend | group_by_category | group_by_merchant | monthly_trend | charge_summary | top_n_merchants | subscription_list | null>",
        "group_by": "<category | merchant | month | null>"
    }},

    "sorting_and_limiting": {{
        "order_by": "<ascending | descending | null>",
        "limit": "<topN or null>"
    }},

    "output": {{
        "requires_chart": <true | false>,
        "chart_type": "<pie_chart | bar_chart | line_chart | table | summary_text | donut_chart | null>",
        "requires_comparison": <true | false>,
        "requires_recommendation": <true | false>
    }},

    "confidence": <Your_internal_confidence_score_for_the_json_output>,
    "next_action": "<query_db | ask_clarification | show_summary | show_chart>"
}}
"""

sql_query_prompt = """
Based on the following schema and example data, you will be asked to generate SQL queries.\nGenerate only the SQL query. Wrap the query with 'SQL_START' and 'SQL_END'.\n\n
For matching string in where clause always use lower(lhs) like %lower("rhs")%

You will be provided with the table name and the user_id.

You are given a database with the following schema:

- `user_id` : TEXT - e.g., "ue475639ds"
- `month`: TEXT — e.g., "January"
- `category`: TEXT — e.g., "Food"
- `sub_category`: TEXT — e.g., "Restaurants"
- `merchant`: TEXT — e.g., "Dominos"
- `amount`: INTEGER — e.g., 1200
- `date`: DATE — e.g., "2025-01-15"

Example rows:
1. {
        "user_id" : "67tr63746",
        "month": "January",
        "category": "Food",
        "sub_category": "Restaurants",
        "merchant": "Dominos",
        "amount": 1200,
        "date": "2025-01-15"
}
2. {
        "user_id" : "67tr63746",
        "month": "January",
        "category": "Fuel",
        "sub_category": "Petrol",
        "merchant": "Indian Oil",
        "amount": 3000,
        "date": "2025-01-18"
}

Based on the schema and example data above, you will be asked to generate SQL queries.
Generate only the SQL query. Wrap the query with 'SQL_START' and 'SQL_END'.
"""

insights_prompt = """
You will be provided with:

An array of information regarding one user query, where each information contains:
- "intent and user_query": The original user query and its corresponding intent.
- "database_results": The results fetched from the database based on the SQL query generated for that user query.
- "chart_dict": A dictionary containing chart data which corresponds to the answer of the user's question (if applicable).
Refer to the chart_tag to identify the type of chart for giving better insights to the user

Your task is to generate insightful answers for each user question based on the corresponding database result.
Do not mention the questions, use the questions to create headings

Formatting Guidelines:
-Respond in markdown format and use headlines.
-Consider the money amount in Indian Rupees.
-Convert the questions into headers.
-Only in case a chart is required corresponding to one information dictionary in that case, put a placeholder like [chart_n] where n is for n-th infromation dictionary, use 0-based indexing.
-Use the user query for the heading for each section
-If a question has no result (e.g., empty list or None), leave that part.
-For results that include numbers, ensure the units (like currency or count) are clearly stated and the values are easy to read.
-If applicable, summarize comparisons, averages, or top values with a brief interpretation (e.g., which category had the highest fees).
-Keep your tone clear, concise, and user-friendly, like explaining insights to a customer.
"""

def llm_response(system_prompt, user_prompt):
    bedrock_client = get_bedrock_client()
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    messages = []
    message = {
        "role": "user",
        "content": [{
            "text": user_prompt
        }]
    }
    messages.append(message)
    system_prompt = [{"text": system_prompt}]

    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompt
    )

    return response['output']['message']['content'][0]['text']

def process_sql_text(raw_text):
    start_pos = raw_text.find('SQL_START') + len('SQL_START\n')
    end_pos = raw_text.find('SQL_END') - 2
    sql_text_arr = raw_text[start_pos:end_pos+1]
    return sql_text_arr

def get_intent(user_query):
    intent = llm_response(intent_prompt, user_query)
    try:
        intent_dict = json.loads(intent)
    except Exception as e:
        print({"intent response error": str(e), "raw": intent})
        return {}
    print({"intent response": intent_dict})
    return intent_dict

def get_info_dict(user_query):
    info_dict = llm_response(feature_extraction_prompt, user_query)
    try:
        info_dict = json.loads(info_dict)
    except Exception as e:
        print({"info_dict error": str(e), "raw": info_dict})
        return {}
    print({"info_dict": info_dict})
    return info_dict

def get_sql_query(info_dict, table_name, user_id):
    print({"info_dict_for_sql": info_dict})  # Log info_dict before SQL generation
    if not info_dict:
        return None
    raw_sql_query = llm_response(sql_query_prompt, f"informations: {info_dict}, table name: {table_name}, use_id: {user_id}")
    print({"raw_sql_query": raw_sql_query})  # Log the raw SQL query from LLM
    sql_query = process_sql_text(raw_sql_query)
    print({"processed_sql_query": sql_query})  # Log the processed SQL query
    return sql_query

def get_data(sql_query):
    print({"executing_sql_query": sql_query})  # Log the SQL query being executed
    if not sql_query:
        return None
    try:
        connection = db_connection()
        cursor = connection.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        result = None
    print({"db_result": result})  # Log the DB result
    return result

def generate_chart(info_dict, table_name, user_id, chart_tag):
    group_by_config = info_dict.get("group_by", {})
    filters_config = info_dict.get("filters", {})
    aggregate_metrics_config = info_dict.get("aggregate_metrics", {})

    if not group_by_config.get("group_by") or not aggregate_metrics_config.get("final_metric") or aggregate_metrics_config.get("final_metric") != "sum":
        print("Not pie")
        return None

    metric_map = {
        "sum": "SUM(amount)",
        "count": "COUNT(*)",
        "average": "AVG(amount)",
        "max": "MAX(amount)",
        "min": "MIN(amount)",
        "ascending": 'ASC',
        "descending": 'DESC'
    }

    group_by_query = ""
    select_query = "SELECT "
    group_by_column = ""
    if info_dict['group_by']['group_by']:
        group_by_column = info_dict['group_by']['group_by']
        group_by_query += f"GROUP BY {group_by_column}"
        select_query += group_by_column

    if info_dict['aggregate_metrics']['final_metric']:
        metric = info_dict['aggregate_metrics']['final_metric']
        metric_func = metric_map[metric]
        if select_query == "SELECT ":
            select_query += metric_func + " AS value"
        else:
            select_query += ", " + metric_func + " AS value"

    where_clauses = []
    where_clauses.append(f"user_id = '{user_id}'")

    if info_dict['date_range']['from']:
        where_clauses.append(f"date >= '{info_dict['date_range']['from']}'")

    if info_dict['date_range']['to']:
        where_clauses.append(f"date <= '{info_dict['date_range']['to']}'")

    if info_dict['filters']['category']:
        category_arr = info_dict['filters']['category']
        if len(category_arr) > 0:
            if len(category_arr) > 1:
                where_clauses.append(f"category in {str(tuple(category_arr))}")
            else:
                where_clauses.append(f"category in ('{str(category_arr[0])}')")

    if info_dict['filters']['sub_category']:
        sub_category_arr = info_dict['filters']['sub_category']
        if len(sub_category_arr) > 0:
            if len(sub_category_arr) > 1:
                where_clauses.append(f"sub_category in {str(tuple(sub_category_arr))}")
            else:
                where_clauses.append(f"sub_category in ('{str(sub_category_arr[0])}')")

    if info_dict['filters']['merchant']:
        merchant_arr = info_dict['filters']['merchant']
        if len(merchant_arr) > 0:
            if len(merchant_arr) > 1:
                where_clauses.append(f"merchant in {str(merchant_arr)}")
            else:
                where_clauses.append(f"merchant in ('{str(merchant_arr[0])}')")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    order_by_sql = ""
    if info_dict['sorting_and_limiting']['order_by']:
        sort_order = info_dict['sorting_and_limiting']['order_by']
        order_by_sql += f"ORDER BY value {metric_map[sort_order]}"

    limit_sql = ""
    if info_dict['sorting_and_limiting']['limit']:
        limit = info_dict['sorting_and_limiting']['limit']
        limit_sql += f"LIMIT {limit}"

    sql_query = f"""
    {select_query}
    FROM {table_name}
    {where_sql}
    {group_by_query}
    {order_by_sql}
    {limit_sql};
    """.strip()

    print({"sql_query from generate_chart": sql_query})
    chart_dict = {"tag": chart_tag, "type": "PIE", "data": None}
    try:
        connection = db_connection()
        cursor = connection.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        labels = [row[0] for row in results]
        values = [row[1] for row in results]
        pie_data = {"labels": labels, "values": values}
        if len(labels) >= 8 or group_by_column == "month":
            chart_dict["type"] = "BAR"
        print(pie_data)
        cursor.close()
        connection.close()
        if not values or len(values) == 0:
            return None
    except Exception as e:
        print(e)

    chart_dict["data"] = pie_data
    return chart_dict

# info_dict, db_result, chart_dict
# entry[0]  - info_dict
# entry[1]  - db_result
# entry[2]  - chart_dict
# chart_dict["tag"]
# info_dict["user_query"]
# information json list : {info_dict_list}, corresponding relevant data: {db_result_list}

def get_insights(results):

    # modfying info_dict to only contain user_queries
    for entry in results:
        info_dict = entry[0]
        entry[0] = {
            "user_query": info_dict["user_query"],
            "intent": info_dict["intent"]
            }

    insights = llm_response(insights_prompt, f"{results}")
    print({"insights": insights})  # Log the insights
    return {"type": "TEXT", "data": insights}

def transaction_chat2(user_query, table_name, user_id):
    """Transaction chat function"""
    print({"user_query": user_query, "table_name": table_name, "user_id": user_id})  # Log input params
    intent_json = get_intent(user_query)
    query_list = [user_query]
    query_list += intent_json.get("queries", [])

    # info_dict_list = []
    # db_result_list = []
    # chart_dict_list = []

    async def process_query(position, user_query):
        print({
            "current_query": user_query
        })
        loop = asyncio.get_event_loop()
        info_dict = await loop.run_in_executor(
            None, get_info_dict, user_query
        )
        sql_query = await loop.run_in_executor(
            None, get_sql_query, info_dict, table_name, user_id
        )
        chart_tag = f"chart_{position}"
        chart_dict = await loop.run_in_executor(
            None, generate_chart, info_dict, table_name, user_id, chart_tag
        )
        db_result = await loop.run_in_executor(
            None, get_data, sql_query
        )
        if not db_result or len(db_result) == 0:
            return None, None, None
        return info_dict, db_result, chart_dict


    async def process_all_queries():
        tasks = [
            process_query(position, user_query)
            for position, user_query in enumerate(query_list)
        ]
        results = await asyncio.gather(*tasks)
        return results

    results = asyncio.run(process_all_queries())
    # for info_dict, db_result, chart_dict in results:
    #     info_dict_list.append(info_dict)
    #     db_result_list.append(db_result)
    #     chart_dict_list.append(chart_dict)

    chart_dict_list_return = [entry[2] for entry in results if entry[2]]
    return [get_insights(results)] + chart_dict_list_return