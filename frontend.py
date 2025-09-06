import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class frontend:

    def __init__(self):
        """Frontend class for handling the UI and backend interaction."""
        self.client = None
        self.providers_data = None

    def get_providers_data(self):
        """
        Fetch supported providers and models from the backend.
        
        Returns:
            dict: Providers data or default fallback
        """
        try:
            response = requests.get("http://lb:4000/providers")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch providers: {response.status_code}")
                return self.get_fallback_providers()
        except Exception as e:
            print(f"Error fetching providers: {e}")
            return self.get_fallback_providers()

    def get_fallback_providers(self):
        """
        Fallback provider data in case backend is unavailable.
        
        Returns:
            dict: Default providers configuration
        """
        return {
            "supported_providers": ["openai", "gemini"],
            "recommended_models": {
                "openai": ["gpt-4.1"],
                "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
            }
        }

    def update_models_for_provider(self, provider):
        """
        Update the model dropdown based on selected provider.
        
        Args:
            provider (str): Selected provider name
            
        Returns:
            gr.Dropdown: Updated dropdown with models for the provider
        """
        if not self.providers_data:
            self.providers_data = self.get_providers_data()
        
        models = self.providers_data.get("recommended_models", {}).get(provider, [])
        return gr.Dropdown(choices=models, value=models[0] if models else None)

    def update_api_key_label(self, provider):
        """
        Update API key label based on selected provider.
        
        Args:
            provider (str): Selected provider name
            
        Returns:
            gr.Textbox: Updated textbox with provider-specific label
        """
        provider_labels = {
            "openai": "Enter OpenAI API key",
            "gemini": "Enter Gemini API key"
        }
        label = provider_labels.get(provider, f"Enter {provider.title()} API key")
        return gr.Textbox(label=label, placeholder=f"Enter your {provider} api key here...", type="password")

    def process(self, provider: str, model: str, endpoint_ai: str, endpoint_app: str, inputText: str, noOfWords: int, option: int, request: gr.Request):
        """
        Process and validate the input text using the selected option via ML class.

        Args:
            provider (str): Selected LLM provider.
            model (str): Selected model.
            endpoint_ai (str): API key for the LLM provider.
            endpoint_app (str): App API key.
            inputText (str): The text to process.
            noOfWords (int): Desired word count.
            option (str): Selected processing option.

        Returns:
            tuple: Processed text and its word count.
        """
        if request:
            print("Client IP address:", request.client.host)

        if option == "Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)":
            option = 1

        elif option == "Shorten text (choose if you want to slightly shorten text to fix it within a word count)":
            option = 2

        item = {
            "llm_api_key": endpoint_ai,
            "llm_provider": provider,
            "llm_model": model,
            "app_key": endpoint_app,
            "option": option,
            "input_text": inputText,
            "no_of_words": noOfWords
        }
    
        output = requests.get(
                "http://lb:4000/",
                json = item,
                headers={"ip_address": request.client.host},
        )

        output = output.json()
        if("error" in output):
            return output["error"],len(output["error"].split())
        processed_text = output["processed_text"]
        processed_text_length = output["processed_text_length"]
        return processed_text,processed_text_length
    


    def generate_api_key(self,name: str,email: str,validity: int,request: gr.Request):
        """
        Generate a new API key by sending user details to a backend API.

        Parameters:
        - name (str): Name of the user requesting the key.
        - email (str): Email of the user.
        - validity (int): Duration (in days) for which the key is valid.
        - request (gr.Request): Gradio request object containing client metadata like IP address.

        Returns:
        - str: The generated API key, or an error message (duplicated across 2 outputs if needed).
        """
        if request:
            print("Client IP address:", request.client.host)

        item = {
            "name": name,
            "email": email,
            "validity": validity
        }

        output = requests.get(
                "http://lb:4000/api_key",
                json=item,
                headers={"X-Forwarded-For": request.client.host}
        )
        # switched to using the standard XFF header since its supported in many stacks including haproxy
        
        output = output.json()
        if("error" in output):
            return output["error"]
        api_key = output["api_key"]
        return api_key
    

    def show_details_page(self):
        # switch to details page
        return gr.update(visible=False), gr.update(visible=True)

    def show_key_page(self):
        # switch back to home page
        return gr.update(visible=True), gr.update(visible=False)



    def demo(self):
        """
        Build and launch the Gradio user interface.

        Creates interactive components for input, configuration,
        and displaying processed output.
        """
        # Initialize providers data
        self.providers_data = self.get_providers_data()
        supported_providers = self.providers_data.get("supported_providers", ["openai", "gemini"])
        default_provider = supported_providers[0] if supported_providers else "openai"
        default_models = self.providers_data.get("recommended_models", {}).get(default_provider, ["gpt-4.1"])
        
        demo = gr.Blocks(theme=gr.themes.Soft())

        with demo:

            with gr.Column(visible=True) as details_page:
                gr.Markdown(
                """
                # Welcome to the Text Processing App!
                This app allows you to process text by either concisely presenting ideas from a large text or
                shortening text to fit within a specified word count.
                """)
                endpoint_app = gr.Textbox(label="Enter ShortAndEXACT app API key", placeholder="Enter your app api endpoint here...", type="password")

                btn_generate_key = gr.Button("Go to Generate API Key (if you don't have one)")

                # Provider selection
                provider_dropdown = gr.Dropdown(
                    choices=supported_providers,
                    value=default_provider,
                    label="LLM Provider",
                    info="Select your preferred language model provider"
                )

                # Model selection (will be updated based on provider)
                model_dropdown = gr.Dropdown(
                    choices=default_models,
                    value=default_models[0] if default_models else None,
                    label="Model",
                    info="Select the specific model to use"
                )

                # API key input (label will update based on provider)
                endpoint_ai = gr.Textbox(label="Enter OpenAI API key", placeholder="Enter your OpenAI api key here...", type="password")

                input = gr.Textbox(label="Input Text", placeholder="Enter your text here...")

                number_of_words = gr.Number(label="Number of Words you want to reduce to", step=1,minimum=1,value = 1)

                option = gr.Radio(["Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)",
                            "Shorten text (choose if you want to slightly shorten text to fix it within a word count)"], 
                            label="Options")
                
                clear_button = gr.ClearButton(components=[input, number_of_words, option])

                submit_button_text = gr.Button("Submit")

                output_text = gr.Textbox(label="Output Text", placeholder="Your processed text will appear here...")
                output_no_of_words = gr.Textbox(label="Output Word Count", placeholder="Word count of the processed text will appear here...")
            

            with gr.Column(visible=False) as key_page:
                name = gr.Textbox(label="Name", placeholder="Enter your name here...")
                email = gr.Textbox(label="Email", placeholder="Enter your email here...", type="email")
                validity = gr.Number(label="Validity (The no of days you want to keep your api valid for)",step=1,minimum=1,value = 1)
                generate_button_text = gr.Button("Generate API Key")
                output_key = gr.Textbox(label="Your Api Key", placeholder="Save the key securely, it will not be shown again!")
                btn_back_details = gr.Button("Go to Text Processing App")

            # wiring
            btn_generate_key.click(
                fn=self.show_key_page,
                outputs=[key_page,details_page],
            )

            btn_back_details .click(
                fn=self.show_details_page,
                outputs=[key_page,details_page],
           )

            # Update model dropdown when provider changes
            provider_dropdown.change(
                fn=self.update_models_for_provider,
                inputs=[provider_dropdown],
                outputs=[model_dropdown]
            )

            # Update API key label when provider changes
            provider_dropdown.change(
                fn=self.update_api_key_label,
                inputs=[provider_dropdown],
                outputs=[endpoint_ai]
            )

            submit_button_text.click(
                fn=self.process,
                inputs=[provider_dropdown, model_dropdown, endpoint_ai, endpoint_app, input, number_of_words, option],
                outputs=[output_text,output_no_of_words]
            )

            generate_button_text.click(
                fn=self.generate_api_key,
                inputs=[name, email, validity],
                outputs=[output_key]
            )

        demo.queue().launch(server_name="0.0.0.0", server_port=3000)

if __name__ == "__main__":
    print("Starting demo")
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

# Modular logic ensures initialization only happens when explicitly called — not by accident during import.


# A Worker Service is a long-running background service designed for tasks that do not
# require direct user interaction. It is ideal for scenarios where actions need to be
# performed continuously, at intervals, or in response to events, such as listening to
# message queues, processing data, or scheduling tasks.
    

# •	A PR can include multiple commits related to a single feature or fix.
# •	Create a new branch for every feature or bugfix — even for small changes.
# •	Always branch off the latest main to ensure you’re working on up-to-date code.
# •	Keep branches short-lived — delete them after the PR is merged.
# •	Do not reuse branches across features or fixes to avoid confusion and merge conflicts.
# •	Before opening a PR, pull the latest changes from main and resolve any conflicts.
# •	Collaborators work on separate branches, ensuring isolation and easier code reviews.
# •	Merged branches’ commits remain in main, even after the branch is deleted.

# Git does not discard or overwrite your teammate’s changes from main. Instead, it:
# 	1.	Replays your commits (from your feature branch) on top of the latest main, which already includes your teammate’s changes.
# 	2.	If both of you edited the same lines, you’ll get a conflict — which Git will ask you to manually resolve.
# 	3.	If you touched different files or lines, Git will auto-merge safely.

# Rebase moves your feature branch’s commits to the tip of another branch (usually main), so your changes appear 
# as if they were made on top of the latest mainline code.

# Remote-tracking branches are **read-only references** in your local Git repo that **mirror the state of branches 
# in a remote repository** (like GitHub or GitLab).




# blackscoles
# ito calculus
