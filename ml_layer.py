class ML: 

    def __init__(self, input_text, number_of_words, option,endpoint):
        self.input_text = input_text
        self.number_of_words = number_of_words
        self.option = option    
        self.endpoint = endpoint


    def process_text(self):
        # Placeholder for text processing logic
        if self.option == "Concisely present ideas":
            self.process_concisely()

        elif self.option == "Shorten text":
            self.process_short()
        


    def process_concisely(self):
        # Logic to concisely present ideas from a large text
        pass

    def process_short(self):
        # Logic to shorten text to fit within a specified word count
        pass