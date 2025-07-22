import gradio as gr
from ml_layer import ML


# function to validate input text and number of words
def validate_input(input_text,noOfWords,option):
    if not (option):
        return "Please select an option."
    if not input_text.strip():
        return "Input text cannot be empty."
    if noOfWords > len(input_text.split()):
        return "Input text needs to be longer than the number of words you want to shorten it to."
    return ""
    

def greet(inputText, noOfWords, option):

    # validate the input
    validation = validate_input(inputText, noOfWords,option)
    if(validation):
        raise gr.Error(validation)
    
    # Create an instance of the ML class and process the text

    refined_input_text = " ".join(inputText.strip())
    ml_instance = ML(inputText, noOfWords, option)
    processed_text = ml_instance.process_text()
    return processed_text


demo = gr.Blocks()

with demo:
    gr.Markdown(
    """
    # Welcome to the Text Processing App!
    This app allows you to process text by either concisely presenting ideas from a large text or
    shortening text to fit within a specified word count.
    """)
    input = gr.Textbox(label="Input Text", placeholder="Enter your text here...")
    number_of_words = gr.Number(label="Number of Words", step=1,minimum=1,value = 1)
    option = gr.Radio(["Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)",
                 "Shorten text (choose if you want to slightly shorten text to fix it within a word count)"], 
                 label="Options")
    
    clear_button = gr.ClearButton(components=[input, number_of_words, option])
    submit_button = gr.Button("Submit")

    output = gr.Textbox(label="Output Text", placeholder="Your processed text will appear here...")

    submit_button.click(
        fn=greet,
        inputs=[input, number_of_words, option],
        outputs=[output]
    )


demo.launch()