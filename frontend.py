import gradio as gr
from ml_layer import ML
import openai
import gradio.themes
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts

class frontend:

    def __init__(self):
        """Frontend class for handling the UI and backend interaction."""
        self.client = None

    def validate_input(self,input_text,noOfWords,option):
        """
        Validate the user's input parameters.

        Args:
            input_text (str): The input paragraph.
            noOfWords (int): Desired word count.
            option (str): Processing mode selected by user.

        Returns:
            str: Empty string if valid, else an error message.
        """
        if not (option):
            return "Please select an option."
        if not input_text.strip():
            return "Input text cannot be empty."
        if noOfWords > len(input_text.split()):
            return "Input text needs to be longer than the number of words you want to shorten it to."
        return ""
    

    def process_endpoint(self,endpoint):
        """
        Set up the OpenAI API client with the given endpoint.

        Args:
            endpoint (str): OpenAI API key.

        Raises:
            gr.Error: If the client initialization fails.
        """
        try:
            client = openai.OpenAI(api_key=endpoint)
            self.client = client

        except Exception as e:
            raise gr.Error(f"{e}")


    def process(self,inputText, noOfWords, option):
        """
        Process and validate the input text using the selected option via ML class.

        Args:
            inputText (str): The text to process.
            noOfWords (int): Desired word count.
            option (str): Selected processing option.

        Returns:
            tuple: Processed text and its word count.
        """

        # validate the input
        validation = self.validate_input(inputText, noOfWords,option)
        if(validation):
            raise gr.Error(validation)
        
        # Create an instance of the ML class and process the text
        refined_input_text = " ".join(inputText.split())
        ml_instance = ML(refined_input_text, noOfWords, option,self.client)
        processed_text,processed_text_length = ml_instance.process_text()
        return processed_text,processed_text_length
    

    def demo(self):
        """
        Build and launch the Gradio user interface.

        Creates interactive components for input, configuration,
        and displaying processed output.
        """
        demo = gr.Blocks(theme=gr.themes.Soft())

        with demo:
            gr.Markdown(
            """
            # Welcome to the Text Processing App!
            This app allows you to process text by either concisely presenting ideas from a large text or
            shortening text to fit within a specified word count.
            """)

            endpoint = gr.Textbox(label="Enter OpenAI API key", placeholder="Enter your open api endpoint here...")
            submit_button_endpoint = gr.Button("Submit Key")

            submit_button_endpoint.click(
                fn=self.process_endpoint,
                inputs=endpoint
            )

            input = gr.Textbox(label="Input Text", placeholder="Enter your text here...")
            number_of_words = gr.Number(label="Number of Words", step=1,minimum=1,value = 1)
            option = gr.Radio(["Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)",
                        "Shorten text (choose if you want to slightly shorten text to fix it within a word count)"], 
                        label="Options")
            
            clear_button = gr.ClearButton(components=[input, number_of_words, option])
            submit_button_text = gr.Button("Submit")

            output_text = gr.Textbox(label="Output Text", placeholder="Your processed text will appear here...")
            output_no_of_words = gr.Textbox(label="Output Word Count", placeholder="Word count of the processed text will appear here...")

            submit_button_text.click(
                fn=self.process,
                inputs=[input, number_of_words, option],
                outputs=[output_text,output_no_of_words]
            )


        demo.launch()

if __name__ == "__main__":
    frontend_instance = frontend()
    frontend_instance.demo()

# semantic chunking
# integrate functionality for pdf upload an text extracting from it - pdf uploader, integrate correct db , pdf text extractor
# create an api endpoint for the applicaton
# containerize the entire app, deploy on heroku or vercel(provides server infra layer) from docker image
# hit the endpoint multiple times (load testing) and intergate logic to handle it using library or redis

# 🚫 GitHub-based deploys run in preconfigured containers
# 	•	These might not have required system packages
# 	•	You might not even have permission to install them
# 	•	The base image may lack things like build-essential or gcc

# in most real-world setups, the frontend (React) and backend (Flask/FastAPI) are hosted separately, unless you’re building a monolithic app.
# 	•	Frontend (React) → hosted on Vercel, Netlify, or S3 + CloudFront
# 	•	Backend (Flask) → hosted on Render, Railway, Heroku, or EC2

# If you use a prebuilt in-process library (like cachetools, ratelimit, or flask-limiter without Redis backend), here’s what happens:
# 	•	It stores limits in memory, local to that Python process
# 	•	If you have multiple API files, or multiple FastAPI/Flask instances (e.g., via Gunicorn workers, Docker containers),
# → Each has its own memory, so:
# 	•	API calls from the same IP won’t be counted together
# 	•	Rate limits won’t sync
# 	•	Caching will be inconsistent



# No need to expose ports for inter-container communication!

# A Docker container itself doesn’t run on a port — rather, the applications inside the container open ports
# (like FastAPI on 8000), and Docker optionally maps those to ports on your host machin


# If you have built a Docker image of your application and:
# 	•	Pushed it to Docker Hub (or any registry), or
# 	•	Sent the .tar file (via docker save),

# then your friend can recreate and run your full app — with all dependencies, environment, and setup — just by running that image.



#  A web API deployed at scale (multiple users, frequent updates) will hit race conditions and lock errors quickly.
# Concurrent access = Multiple processes or threads attempting to access the DB before the previous operation completes.
# 	•	Not a client-server database: SQLite is just a file accessed via a library, not a server process. You can’t connect to it over a network like PostgreSQL or MySQL.
# 	•	No separation of concerns: It runs inside your application process — you can’t run it in a separate container or scale it independently.
# 	•	Scaling limitation: If you scale your API (e.g. multiple Docker containers), each gets its own copy of the database file — leading to data inconsistency and concurrent write issues.
# 	•	No true multi-user concurrency: SQLite handles limited concurrent access, making it unsuitable for high-throughput or multi-user production systems.


# •	All your DB data lives inside the container’s writable layer, which is ephemeral.
# •	So if the container stops or is deleted — you lose all your data, including schema and records.
# therefore you need to use volumes
# you need to have acess to the actual db and hsot it in a containerized enviroment , otherwise its just the data at the 
# container layer and you will lose it. 

# Avoid: 
# 	•	Running init logic unconditionally every time app starts.
# 	•	Deleting init scripts after execution manually (makes containers non-reproducible).


# database Migrations = version control for your database schema.
    
# make your application reproducible
# concentrate your logic in only one place. make systems decoupled
# get off local, thinkign baout things like latency per user, load testing is really improtnat as u scale your application

# blackscoles
# ito calculus
