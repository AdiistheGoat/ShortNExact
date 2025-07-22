import gradio as gr

def greet(inputText, noOfWords, option):
    # call procesing function 
    return "ji5op4mpr"
    pass


demo = gr.Blocks()

with demo:
    gr.Markdown(
    """
    # Welcome to the Text Processing App!
    This app allows you to process text by either concisely presenting ideas from a large text or
    shortening text to fit within a specified word count.
    """)
    input = gr.Textbox(label="Input Text", placeholder="Enter your text here...")
    number_of_words = gr.Number(label="Number of Words", step=1)
    option = gr.Radio(["Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)",
                 "Shorten text (choose if you want to slightly shorten text to fix it within a word count)"], 
                 label="Options")
    
    clear_button = gr.ClearButton()
    submit_button = gr.Button("Submit")

    output = gr.Textbox(label="Output Text", placeholder="Your processed text will appear here...")

    submit_button.click(
        fn=greet,
        inputs=[input, number_of_words, option],
        outputs=[output]
    )


demo.launch()