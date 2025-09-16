from os import getenv

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

print(getenv("SUPABASE_URI"))
print(getenv("OPENROUTER_API_KEY"))
print(getenv("OPENROUTER_API_URL"))


MODEL_NAME = "mistralai/mistral-small-3.1-24b-instruct"

db = SQLDatabase.from_uri(getenv("SUPABASE_URI"))

llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=getenv("OPENROUTER_API_KEY"),
    base_url=getenv("OPENROUTER_API_URL"),
    temperature=0,
)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

tools = toolkit.get_tools()

print(f"Dialect: {db.dialect}")
print(f"Available tables: {db.get_usable_table_names()}")


system_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
""".format(
    dialect=db.dialect,
    top_k=5,
)

agent = create_react_agent(
    llm,
    tools,
    prompt=system_prompt,
)

question = "What city are your buyers most often from?"

for step in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()
