import gradio as gr

def greet(inputText, noOfWords, option):
    # call fu
    pass

demo = gr.Interface(
    fn=greet,
    inputs=[
        gr.Textbox(label="Input Text", placeholder="Enter your text here..."),
        gr.Number(value=100, label="Number of Words", step=1),
       gr.Radio(["Concisely present ideas(choose if want to concisely present ideas from a large text)",
                 "Shorten text (choose if you want to slightly shorten text to fix it within a word count)"], 
                 label="Options"),
       
    ],
    outputs=["textbox"],
)

demo.launch()