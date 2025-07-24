import ML
from fastapi import FastAPI
from pydantic import BaseModel
import openai

# Define request model
class Item(BaseModel):
    end_point: str
    option: bool = int
    input_text: float
    no_of_words: str


# function to process the endpoint
def process_endpoint(endpoint: str):
    try:
        client = openai.OpenAI(api_key=endpoint)
        return client

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


# Home route
@app.get("/")
def read_root(endpoint:str,option:int, input_text:str, no_of_words:int):

    client = openai.OpenAI(api_key=endpoint)
    if not (client):
        return {"error": "endpoint not valid"}

    validation_msg = validate_input(option, input_text, no_of_words)
    if validation_msg:
        return {"error": validation_msg}
    

    if(option==0):
        option_string = "Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)"

    else:
        option_string = "Shorten text (choose if you want to slightly shorten text to fix it within a word count)"
    
    refined_input_text = " ".join(input_text.split())
    ml_instance = ML(refined_input_text, no_of_words, option_string,client)
    processed_text,processed_text_length = ml_instance.process_text()
    return {"processed_text": processed_text, "processed_text_length": processed_text_length}
    

    

