import gradio as gr
from ml_layer import ML
import openai
import gradio.themes
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts


class frontend:

    # intializing the frontend class
    def __init__(self):
        self.client = None

    # function to validate input text and number of words
    def validate_input(self,input_text,noOfWords,option):
        if not (option):
            return "Please select an option."
        if not input_text.strip():
            return "Input text cannot be empty."
        if noOfWords > len(input_text.split()):
            return "Input text needs to be longer than the number of words you want to shorten it to."
        return ""
    
    # function to process the endpoint
    def process_endpoint(self,endpoint):
        try:
            client = openai.OpenAI(api_key=endpoint)
            self.client = client

        except Exception as e:
            raise gr.Error(f"{e}")


    # function to process the input text
    def process(self,inputText, noOfWords, option):

        # validate the input
        validation = self.validate_input(inputText, noOfWords,option)
        if(validation):
            raise gr.Error(validation)
        
        # Create an instance of the ML class and process the text
        refined_input_text = " ".join(inputText.split())
        ml_instance = ML(refined_input_text, noOfWords, option,self.client)
        processed_text = ml_instance.process_text()
        return processed_text,len(processed_text.split())
    

    # function to create the Gradio interface and launch the app
    def demo(self):

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