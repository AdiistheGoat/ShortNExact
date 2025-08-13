# Import necessary modules and libraries
from ml_layer import ML
from fastapi import FastAPI
from pydantic import BaseModel
import openai
import redis
import time
from fastapi import Request
from datetime import datetime,timedelta
from sqlalchemy import create_engine,MetaData,Table, Column,DateTime,Integer,Text,select,text,func, inspect
import sqlalchemy as db
import secrets
import time
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg # ocnnects to a prosgres driver like postgres db or postgres bouncer

# Initialize FastAPI application
app = FastAPI()

# Initialize Redis for rate limiting
r = redis.Redis(host='redis', port=6379, db=0)

# Rate limit config: 100 requests per 60 seconds per IP
MAX_API_KEYS_LAST_24_HOURS = 10000

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


async def validate_api_key(name,email,validity):
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
    query = select(func.count()).where(app.state.api_keys.c.name == name,app.state.api_keys.c.email==email,app.state.api_keys.c.time>=time_now-one_day_time)
    async with app.state.engine.begin() as conn:
        output = await conn.execute(query)
    count = int(output.fetchall()[0][0])
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
        client = openai.AsyncOpenAI(api_key=key)
        client.models.list()
        return client

    except Exception as e:
        print(e)


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
    """
    Enforces rate limiting using a sliding window algorithm via Redis.

    Args:
        request (Request): Incoming HTTP request.

    Returns:
        dict | None: Error message if limit exceeded, else None.
    """

    ip =  request.headers.get('X-Forwarded-For')
    key = f"{ip}"
    now = time.time()
    # print(f"ip : {ip}")
    # print(f"current time: {now}")

    # Remove timestamps outside the sliding window
    timestamps = r.lrange(key, 0, -1)
    valid_timestamps = [float(ts) for ts in timestamps if now - float(ts) <= WINDOW_SIZE]
    # print(f"Prev timestamps: {valid_timestamps}")

    if len(valid_timestamps) == RATE_LIMIT:
        raise Exception("Rate limit exceeded")

    r.delete(key)
    for ts in valid_timestamps:
        r.rpush(key, ts)

    r.rpush(key, now)  # Add current timestamp

    # timestamps = r.lrange(key, 0, -1)
    # print(f"Final timestamps: {timestamps}")

    r.expire(key, WINDOW_SIZE)  # Auto-expire key after window



@app.on_event("startup")
async def startup():

    # Getting the api_keys stuff for sqlalchemy queries
    # DEFINE THE DATABASE CREDENTIALS
    user = 'Aditya Goyal'
    password = 'cold feather'
    host = 'db'
    port = 5432
    database = 'short_and_exact'

    meta = MetaData()

    try:
        engine = create_async_engine(url="postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, database),pool_size=40, max_overflow=20)
    except Exception as e:
        print("Connection could not be made due to the following error: \n", e)


    async with engine.begin() as conn:
        api_keys = await conn.run_sync(lambda sync_conn: db.Table('api_keys',meta, autoload_with=sync_conn))

    app.state.api_keys = api_keys
    app.state.engine = engine


    user = 'Aditya Goyal'
    password = 'cold feather33'
    host = "pgbouncer"
    port = 6432
    database = 'short_and_exact'
    POOL_DSN = "postgresql://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port,database)

    connection_pool = await asyncpg.connect(POOL_DSN)

    app.state.pool = connection_pool


@app.on_event("shutdown")
async def shutdown():
    await app.state.engine.dispose()
    await app.state.pool.close()


"""
Health check endpoint for the API.

Args:
    request (Request): FastAPI request object.

Returns:
    dict: A simple status message indicating the API is healthy.
"""
@app.get("/healthy")
def health_check(request: Request):
    return {"status": "healthy"}



@app.get("/")
async def reduce_content(item: Item,request: Request):
    """
    API endpoint that processes input text based on selected option.

    Args:
        item (Item): Input data including API key, text, and config.
        request (Request): FastAPI request object (for rate limiting).

    Returns:
        dict: Processed text and word count, or error message.
    """

    RATE_LIMIT = 2
    WINDOW_SIZE = 60

    try:
        rate_limiter(request,RATE_LIMIT=RATE_LIMIT,WINDOW_SIZE=WINDOW_SIZE)
    except Exception as e:
        return {"error": e.args}

    llm_api_key = item.llm_api_key
    option = item.option
    input_text = item.input_text
    no_of_words = item.no_of_words
    app_key = item.app_key

    query = select(app.state.api_keys).where(app.state.api_keys.c.api_key == app_key)

    async with app.state.engine.begin() as conn:
        output_coroutine = await conn.execute(query)
    
    output = output_coroutine.fetchall()

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
    processed_text,processed_text_length = await ml_instance.process_text()
    return {"processed_text": processed_text, "processed_text_length": processed_text_length}


# gets the name, email , and validity 
# store the time the api key was requested 
# when user provides an api key, 
@app.get("/api_key")
async def generate_key(item: Auth,request: Request):
    """
    Endpoint to generate and return a new API key for valid user input.

    Args:
        item (Auth): User input containing name, email, and desired validity (in days).
        request (Request): FastAPI request object (used for optional rate limiting).

    Returns:
        dict: A dictionary containing either the generated API key or an error message.
    """

    RATE_LIMIT = 3000
    WINDOW_SIZE = 60

    try:
        time1 = time.perf_counter()
        rate_limiter(request,RATE_LIMIT=RATE_LIMIT,WINDOW_SIZE=WINDOW_SIZE)
        time2=time.perf_counter()
    except Exception as e:
        return {"error_msg": e.args}

    name = item.name.strip()
    email = item.email.strip()
    validity = item.validity # in days

    # time3 = time.perf_counter()
    error_message = await validate_api_key(name,email,validity)
    # time4 = time.perf_counter()
    if(error_message):
        return {"error_msg": error_message}
    
    time_current = datetime.now()

    # time5 = time.perf_counter()
    api_key = generate_api_key()
    # time6 = time.perf_counter()

    time7 =  time.perf_counter()
    query = db.insert(app.state.api_keys).values(api_key=api_key,name=name,email=email,time=time_current,validity=validity)
    async with app.state.engine.begin() as conn:
        await conn.execute(query)
        await conn.commit()
    # time8 = time.perf_counter()

    # print(f"time for rate limiter: {time2-time1}")
    # print(f"validating api key {time4-time3}")
    # print(f"geenrate api key {time6-time5}")
    # print(f"inserting api key {time8-time7}")

    return {"api_key": api_key}



# async with handles resource management automatically


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


# time for rate limiter: 0.005319374999089632


# validating api key 0.015565874997264473


# geenrate api key 0.00042491700151003897


# inserting api key 0.004656332999729784

# need async for uploading to db