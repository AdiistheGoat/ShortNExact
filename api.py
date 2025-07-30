# Import necessary modules and libraries
from ml_layer import ML
from fastapi import FastAPI,Depends,HTTPException
from pydantic import BaseModel
import openai
import redis
import time
from fastapi import Request
from datetime import datetime,timedelta
from sqlalchemy import create_engine,MetaData,Table, Column,DateTime,Integer,Text,select,text,func, inspect
import sqlalchemy as db
import secrets

# DEFINE THE DATABASE CREDENTIALS
user = 'Aditya Goyal'
password = 'cold feather'
host = 'db'
port = 5432
database = 'short_and_exact'

# Establish a connection to the PostgreSQL database
try: 
    engine = create_engine(url="postgresql://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, database))
    conn = engine.connect()
except Exception as e:
    print("Connection could not be made due to the following error: \n", e)


# Create inspector
inspector = inspect(engine)

# Get table names
tables = inspector.get_table_names()
print("Tables in the database:", tables)

# Reflect existing 'api_keys' table from the database
meta = MetaData()
api_keys = db.Table('api_keys', meta,autoload_with=engine) #Table object

# Initialize FastAPI application
app = FastAPI()

# Initialize Redis for rate limiting
r = redis.Redis(host='redis', port=6379, db=0)

# Rate limit config: 100 requests per 60 seconds per IP
MAX_API_KEYS_LAST_24_HOURS = 10

# Define request schema for main API functionality
class Item(BaseModel):
    llm_api_key: str       # API key for the language model (e.g., OpenAI)
    app_key: str           # User-provided application-specific key
    option: int            # Option to select processing type or mode
    input_text: str        # Text input to be processed
    no_of_words: int       # Word count limit for processing output

# Define request schema for API key generation
class Auth(BaseModel):
    name: str              # User's name
    email: str             # User's email address
    validity: int          # Requested validity of the API key (in days)


def validate_api_key(name,email,validity):
    """
    Validates the API key creation request based on input constraints.

    Args:
        name (str): Name of the user.
        email (str): Email address of the user.
        validity (int): Requested validity duration in days.

    Returns:
        str or None: Returns an error message string if validation fails, else None.
    """
    if not(name):
        return "Name not Found"
    
    if not(email) or "@" not in email:
        return "Valid email not found"
    
    if(validity>31):
        return "You cannot get an api key with validity for more than 31 days"
    
    one_day_time = timedelta(days=1)
    time_now = datetime.now()
    query = select(func.count()).where(api_keys.c.name == name,api_keys.c.email==email,api_keys.c.time>=time_now-one_day_time)
    count = int(conn.execute(query).fetchall()[0][0])
    if(count==MAX_API_KEYS_LAST_24_HOURS):
        return "You have exhausted your limit for the creation of the api_keys. Pls try again tomorrow"
    return None


def generate_api_key(length_bytes=40):
    """Generates a random API key using URL-safe Base64 encoding."""
    random_bytes = secrets.token_urlsafe(length_bytes)
    return random_bytes

def process_endpoint(key: str):
    """
    Validates and initializes OpenAI client using the given API key.

    Args:
        key (str): OpenAI API key.

    Returns:
        openai.OpenAI: Initialized client if key is valid, otherwise None.
    """
    try:
        client = openai.OpenAI(api_key=key)
        client.models.list()
        return client

    except Exception as e:
        return None


def validate_input(option:int, input_text:str, no_of_words:int):
    """
    Validates the text processing input parameters.

    Args:
        option (int): Processing mode.
        input_text (str): Input text to validate.
        no_of_words (int): Target word count.

    Returns:
        str | None: Validation error message or None if valid.
    """
    if(option <=0) or (option>2):
        return "Please select an option."
    if not input_text.strip():
        return "Input text cannot be empty."
    if no_of_words > len(input_text.split()):
        return "Input text needs to be longer than the number of words you want to shorten it to."
    return None


def rate_limiter(request: Request,WINDOW_SIZE,RATE_LIMIT):
    print(WINDOW_SIZE)
    print(RATE_LIMIT)
    """
    Enforces rate limiting using a sliding window algorithm via Redis.

    Args:
        request (Request): Incoming HTTP request.

    Returns:
        dict | None: Error message if limit exceeded, else None.
    """
    ip = request.client.host
    key = f"{ip}"
    now = time.time()

    r.rpush(key, now)  # Add current timestamp
    r.expire(key, WINDOW_SIZE)  # Auto-expire key after window

    # Remove timestamps outside the sliding window
    timestamps = r.lrange(key, 0, -1)
    valid_timestamps = [float(ts) for ts in timestamps if now - float(ts) <= WINDOW_SIZE]

    for ts in valid_timestamps:
        r.rpush(key, ts)
    r.expire(key, WINDOW_SIZE)

    if len(valid_timestamps) > RATE_LIMIT:
        return {"error": "Rate Limit Exceeded"}


@app.get("/")
def reduce_content(item: Item,request: Request):
    """
    API endpoint that processes input text based on selected option.

    Args:
        item (Item): Input data including API key, text, and config.
        request (Request): FastAPI request object (for rate limiting).

    Returns:
        dict: Processed text and word count, or error message.
    """

    # RATE_LIMIT = 100
    # WINDOW_SIZE = 60
    # rate_limiter(request,RATE_LIMIT=RATE_LIMIT,WINDOW_SIZE=WINDOW_SIZE)

    llm_api_key = item.llm_api_key
    option = item.option
    input_text = item.input_text
    no_of_words = item.no_of_words
    app_key = item.app_key

    query = select(api_keys).where(api_keys.c.api_key == app_key)
    output = conn.execute(query).fetchall()

    if(len(output)==0):
        return {"error": "App key authentication failed. Pls use correct key"}
    
    api_key_list = output[0]
    time_created = api_key_list.time
    validity = api_key_list.validity

    duration1 = timedelta(days=validity)
    time_expired = time_created + duration1

    if(time_expired<datetime.now()):
        return {"error": "app Api Key has expired"}
    

    client = process_endpoint(key=llm_api_key)
    if not (client):
        return {"error": "endpoint not valid"}

    validation_msg = validate_input(option, input_text, no_of_words)
    if validation_msg:
        return {"error": validation_msg}
    
    if(option==1):
        option_string = "Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)"

    else:
        option_string = "Shorten text (choose if you want to slightly shorten text to fix it within a word count)"
    
    refined_input_text = " ".join(input_text.split())
    ml_instance = ML(refined_input_text, no_of_words, option_string,client)
    processed_text,processed_text_length = ml_instance.process_text()
    return {"processed_text": processed_text, "processed_text_length": processed_text_length}


# gets the name, email , and validity 
# store the time the api key was requested 
# when user provides an api key, 
@app.get("/api_key")
def generate_key(item: Auth,request: Request):
    """
    Endpoint to generate and return a new API key for valid user input.

    Args:
        item (Auth): User input containing name, email, and desired validity (in days).
        request (Request): FastAPI request object (used for optional rate limiting).

    Returns:
        dict: A dictionary containing either the generated API key or an error message.
    """

    # RATE_LIMIT = 1
    # WINDOW_SIZE = 60
    # rate_limiter(request,RATE_LIMIT=RATE_LIMIT,WINDOW_SIZE=WINDOW_SIZE)

    name = item.name.strip()
    email = item.email.strip()
    validity = item.validity # in days

    error_message = validate_api_key(name,email,validity)
    if(error_message):
        return {"error_msg": error_message}
    
    time = datetime.now()
    api_key = generate_api_key()
    query = db.insert(api_keys).values(api_key=api_key,name=name,email=email,time=time,validity=validity)
    conn.execute(query)
    conn.commit()
    return {"api_key": api_key}




# meta = MetaData()
# # api_keys = db.Table('api_keys', meta,autoload_with=engine) #Table object
# # api_keys.drop(engine, checkfirst=True)

# table_to_delete = meta.tables['api_keys']
# # Remove the table from metadata
# meta.remove(table_to_delete)

# meta.create_all(engine)
# conn.commit()

# table_to_delete = meta.tables['api_keys']
# # Remove the table from metadata
# meta.remove(table_to_delete)

# api_keys = Table(
#     'api_keys', meta,
#     Column('api_key',Text, primary_key=True),
#     Column('name', Text),
#     Column('email', Text),
#     Column('time', DateTime),
#     Column('validity',Integer),
# )


# meta.create_all(engine)
# conn.commit()


# # Create inspector
# inspector = inspect(engine)

# # Get column information
# columns = inspector.get_columns("api_keys")

# # Print schema details
# for column in columns:
#     print(f"Name: {column['name']}, Type: {column['type']}, Nullable: {column['nullable']}, Default: {column.get('default')}")



# Questions

# we have to ensure the data stays in the postgres db , we cant initialise a new one every time..old data will be lose
# so, i dont think we can use a ready made image 

# i feel the same for redis , rate limiting as well although its a very shorter time frame 

# soln:
# use volumes


# we have a seprate frontend, and another backend....we have soem backend logic in frontend obvisously...
# but in prod and in industry, is frotnend and api sperate but some processing and validation logic could be similar

# What about rate limiting for frontend?

# soln:
# for fronted, go through api_gateway 


# You would need intialisation files like init.sql apart from the docker images as well, right? 