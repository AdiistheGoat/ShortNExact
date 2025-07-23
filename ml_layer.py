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
            return self.process_concisely(self.input_text)

        elif self.option == "Shorten text (choose if you want to slightly shorten text to fix it within a word count)":
            return self.process_short(self.input_text)
        

    """
    My logic for processign concisley is that 
    -- seprate the text into differen parts to clearly demarcate it 
    -- then for each core idea, present it in a slightly concise manner such that it doesnt chnage the core sematic menaing, wording and flow

    then use the process_short function to shorten the text to fit within the word count
    divide the rquired word count for every chunk wrt to their length
    """
    def process_concisely(self,input_text):
        """
        Step 1: Ask LLM to segment the text into meaningful idea-based chunks.
        Step 2: For each chunk, ask the LLM to make it more concise while preserving meaning and tone.
        Step 3: Rejoin the refined chunks.
        """

        # Step 1: Ask LLM to break input into coherent idea-level chunks
        system_prompt_segment = (
            "You are an intelligent document segmenter.\n"
            "Given a large block of text, break it into meaningful idea-based chunks or logical units.\n"
            "Each chunk should focus on a distinct concept or thought.\n"
            "Separate each chunk with: <CHUNK_END>\n"
            "**Do not summarize, rephrase, or alter the content — only seprate the given text into different parts.****"
        )

        segment_response = self.client.responses.create(
            model="gpt-4.1",
            input=input_text,
            top_p=0.3,
            instructions=system_prompt_segment
        )

        segmented_text = segment_response.output[0].content[0].text.strip()
        curr_blobs = [b.strip() for b in segmented_text.split("<CHUNK_END>") if b.strip()]

        print(f"Segmented into {len(curr_blobs)} chunks.")




        final_output = input_text
        target_word_count = self.number_of_words
        print('Target word count:', target_word_count)

        curr_no_of_words = len(final_output.split())
        to_reduce = curr_no_of_words - target_word_count
        to_reduce_percentage = (to_reduce)/ curr_no_of_words
         
        print('Current word count:', curr_no_of_words)
        print('Words to reduce:', to_reduce)
        print('Percentage to reduce:', to_reduce_percentage)
        print("\n")

  
        count = 0
        while(to_reduce_percentage > 0.1) and count<5:

            # Step 2: Concisely rewrite each chunk
            system_prompt_concise = f"""
                You are a concise and intelligent editor.

                Your task is to take a given paragraph and reduce its length by at least {to_reduce_percentage*100}% while preserving all core ideas, meaning, and tone.

                Guidelines:
                - Eliminate redundant words, repetitive phrasing, and filler language.
                - Merge sentences or phrases where possible without losing clarity.
                - Keep the structure logically coherent and easy to read.
                - Avoid generic summaries — keep all specific details and reasoning intact.
                - Do NOT remove any key idea or supporting detail.
                - Use natural, human-like language — not robotic or overly compressed.
                - Remove lines only if they do not contribute to the core meaning and are outliers. 
                - If the word count is not yet met, start removing lines that are not the most essential 
                **ensure to make progress towards reducing the word count by at least {to_reduce_percentage*100}%***

                Return ONLY the revised **shortened paragraph**. Do not explain anything.
            """

            for index in  range(len(curr_blobs)):
                refine_response = self.client.responses.create(
                    model="gpt-4.1",
                    input=curr_blobs[index],
                    top_p=0.3,
                    instructions=system_prompt_concise
                )
                refined = refine_response.output[0].content[0].text.strip()
                curr_blobs[index] = refined

            # Step 3: Combine all refined chunks
            final_output = "\n\n".join(curr_blobs).strip()
            curr_no_of_words = len(final_output.split())
            delta =  to_reduce+target_word_count - curr_no_of_words 

            # hardocoded condition to ensure decent progress
            if(delta<=10):
                count+=1
            else:
                count = 0

            to_reduce = curr_no_of_words - target_word_count
            to_reduce_percentage = (to_reduce)/ curr_no_of_words

            print('Current word count:', curr_no_of_words)
            print('Words to reduce:', to_reduce)
            print('Percentage to reduce:', to_reduce_percentage)
            print("\n")

        final_output = self.process_short(final_output)

        return final_output
    
    """
    Iterate through each line of the input text. For every line, provide the previous, current, and next lines to the LLM,
    asking it to shorten the current line without changing its meaning or tone. Accept the shortened version only if it
    reduces the word count. Stop once the total number of reduced words reaches the target.
    """
    def process_short(self,input_text):

        # Logic to shorten text to fit within a specified word count
        target_word_count = self.number_of_words
        original_no_of_words = len(input_text.split())
        to_reduce = original_no_of_words - target_word_count

        print(f"Original word count: {original_no_of_words}, Target word count: {target_word_count}, Words to reduce: {to_reduce}")

        lines = input_text.split(".")
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

        count = 0
        curr_no_of_words = len(input_text.split())
        while(to_reduce > 0) and count<10:

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

            # hardocded condition to ensure decent progress. We need to intergate this so that the
            # LLM does not get stuck in a generation loop when it is unable to reduce the text further
            temp_text = ". ".join(optimized_lines).strip()
            if(curr_no_of_words- len(temp_text.split()) < 1):
                count += 1
            else:
                count = 0


            

        final_text = ". ".join(optimized_lines).strip()
        print(f"length of Final text after shortening: {len(final_text.split())}")
        return final_text