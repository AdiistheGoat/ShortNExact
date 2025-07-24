from ml_layer import ML
from fastapi import FastAPI
from pydantic import BaseModel
import openai

# Define request model
class Item(BaseModel):
    api_key: str
    option: int
    input_text: str
    no_of_words: int


# function to process the endpoint
def process_endpoint(key: str):
    try:
        client = openai.OpenAI(api_key=key)
        client.models.list()

    except Exception as e:
        return ""


# function to validate input text and number of words
def validate_input(option:int, input_text:str, no_of_words:int):
    if(option <=0) or (option>2):
        return "Please select an option."
    if not input_text.strip():
        return "Input text cannot be empty."
    if no_of_words > len(input_text.split()):
        return "Input text needs to be longer than the number of words you want to shorten it to."
    return ""

app = FastAPI()

# Home route
@app.get("/")
def read_root(item: Item):
    api_key = item.api_key
    option = item.option
    input_text = item.input_text
    no_of_words = item.no_of_words

    client = process_endpoint(key=api_key)
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
    

    

