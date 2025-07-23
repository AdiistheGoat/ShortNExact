import openai
class ML: 

    def __init__(self, input_text, number_of_words, option,client):
        self.input_text = input_text
        self.number_of_words = number_of_words
        self.option = option    
        self.client = client


    def process_text(self):
        # Placeholder for text processing logic
        if self.option == "Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)":
            return self.process_concisely()

        elif self.option == "Shorten text (choose if you want to slightly shorten text to fix it within a word count)":
            return self.process_short()
        

    def process_concisely(self):
        # Logic to concisely present ideas from a large text
        pass


    """
    Iterate through each line of the input text. For every line, provide the previous, current, and next lines to the LLM,
    asking it to shorten the current line without changing its meaning or tone. Accept the shortened version only if it
    reduces the word count. Stop once the total number of reduced words reaches the target.
    """
    def process_short(self):

        # Logic to shorten text to fit within a specified word count
        target_word_count = self.number_of_words
        original_no_of_words = len(self.input_text.split())
        to_reduce = original_no_of_words - target_word_count

        print(f"Original word count: {original_no_of_words}, Target word count: {target_word_count}, Words to reduce: {to_reduce}")

        lines = self.input_text.split(".")
        optimized_lines = lines.copy()

        # System prompt
        system_prompt = (
            "You are a precise text editor.\n"
            "Your job is to shorten the CURRENT line **only** by a few words while preserving its original meaning and tone.\n"
            "You are also provided the previous and next lines to help you understand the context and keep the flow natural.\n"
            "- Do NOT change the meaning.\n"
            "- Make small improvements: remove redundancy, merge phrases, trim unnecessary words.\n"
            "- Keep the tone consistent with surrounding lines.\n"
            "Dont keep a full stop at the end of the line.\n"
            "Only return the improved version of the CURRENT line — nothing else."
        )

        while(to_reduce > 0):

            for i, line in enumerate(optimized_lines):
                if to_reduce <= 0:
                    break  # Stop if target met

                prev_line = optimized_lines[i - 1] if i > 0 else ""
                next_line = optimized_lines[i + 1] if i < len(optimized_lines) - 1 else ""

                user_input = (
                    f"Previous line:\n{prev_line}\n\n"
                    f"Current line:\n{line}\n\n"
                    f"Next line:\n{next_line}\n\n"
                    f"Return an improved and shorter version of the CURRENT line only."
                )

                response = self.client.responses.create(
                    model="gpt-4.1",
                    input = f"{user_input}",
                    top_p = 0.3,
                    instructions = system_prompt
                )

                shortened = response.output[0].content[0].text.strip()

                # Update word budget
                old_len = len(line.split())
                new_len = len(shortened.split())
                delta = old_len - new_len

                if delta > 0:
                    to_reduce -= delta
                    optimized_lines[i] = shortened

        final_text = ". ".join(optimized_lines).strip()
        print(f"length of Final text after shortening: {len(final_text)}")
        return final_text