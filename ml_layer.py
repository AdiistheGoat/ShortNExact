import openai
class ML: 

    def __init__(self, input_text, number_of_words, option,client):
        """
        Initialize the ML class with input parameters.

        Args:
            input_text (str): The raw input text to be processed.
            number_of_words (int): The target word count for the output.
            option (str): Mode of processing — either concise summarization or slight shortening.
            client (OpenAI client): OpenAI-compatible client to call language model API.
        """
        self.input_text = input_text
        self.number_of_words = number_of_words
        self.option = option    
        self.client = client


    def process_text(self):
        """
        Main entry point to process the input text based on the specified option.

        First, it performs grammar and punctuation correction on the input text.
        Then it either:
            - Concisely rephrases it while maintaining ideas (if option is 'concisely present ideas'), or
            - Slightly shortens it to fit within a word limit (if option is 'shorten text').

        Returns:
            Tuple[str, int]: A tuple of processed text and the number of words in the final output.
        """
        input_text = self.fix_syntax_and_grammar(self.input_text)
        print(input_text)

        # Placeholder for text processing logic
        if self.option == "Concisely present ideas(choose if want to concisely present ideas from a large text within a word count)":
            processed_text = self.process_concisely(input_text)
            return processed_text, len(processed_text.split())

        elif self.option == "Shorten text (choose if you want to slightly shorten text to fix it within a word count)":
            processed_text = self.process_short(input_text)
            return processed_text, len(processed_text.split())


    def fix_syntax_and_grammar(self,input_text):
        """
        Fixes grammar and punctuation issues in the input text using an LLM.
        Args:
            input_text (str): Raw input text with potential grammar issues.

        Returns:
            str: Cleaned-up version of the input with corrected grammar and punctuation.
        """

        system_prompt_segment = (
            "You are an intelligent grammatical fixer.\n"
            "Given a large block of text, fix its grammar.\n"
            "You may only fix punctuation if it is clearly incorrect.\n"
            "**Do not summarize, rephrase, or alter the content****"
            "Do not summarize or rewrite the text in any way."
            "Return ONLY the revised **gramatically corrected paragraph**. Do not explain anything."
        )

        segment_response = self.client.responses.create(
            model="gpt-4.1",
            input=input_text,
            top_p=0.3,
            instructions=system_prompt_segment
        )

        segmented_text = segment_response.output[0].content[0].text.strip()

        return segmented_text 


    def process_concisely(self,input_text):
        """
        Creates a semantically concise version of the input text.

        Logic:
            1. Splits text into idea-based segments using an LLM.
            2. Iteratively reduces each chunk's length while preserving meaning and tone.
            3. Stops once the overall word count is close to or below the target.
            4. Applies fine-grained line-by-line shortening at the end for final polishing.

        Returns:
            str: Final version of the text, concisely rewritten to match the word budget.
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
        while(to_reduce_percentage > 0.2):

            if(count>=5):
                count = 0
                new_blobs = []
                for index in range(0,len(curr_blobs),2):
                    cumulative_blob = ""
                    for j in range(index,min(index+2,len(curr_blobs))):
                        cumulative_blob += curr_blobs[j]
                    new_blobs.append(cumulative_blob)
                if(len(new_blobs)==curr_blobs):
                    break
                curr_blobs = new_blobs


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
            # ToDo: fix this clean variables workflow
            final_output = "\n\n".join(curr_blobs).strip()
            curr_no_of_words = len(final_output.split())
            delta =  to_reduce+target_word_count - curr_no_of_words 

            # hardocoded condition to ensure decent progress
            if(delta/to_reduce<=0.1):
                count+=2
            else:
                count = max(0,count-1)

            to_reduce = curr_no_of_words - target_word_count
            to_reduce_percentage = (to_reduce)/ curr_no_of_words


            print('Current word count:', curr_no_of_words)
            print('Words to reduce:', to_reduce)
            print('Percentage to reduce:', to_reduce_percentage)
            print("\n")

        final_output = self.process_short(final_output)

        return final_output
    


    def process_short(self,input_text):
        """
        Slightly shortens the input text to fit within the specified word count.

        Logic:
            - Split text into lines.
            - Use LLM to shorten each line while preserving meaning.
            - Accept only if it reduces word count.
            - Repeat until target is met or no progress seems possible.

        Returns:
            str: Slightly shortened text, preserving semantics and readability.
        """
        # Logic to shorten text to fit within a specified word count
        target_word_count = self.number_of_words

        # System prompt
        system_prompt = (
            "You are a text shortener"

            "**Shorten the line plsss*"
            "**ensure to make progress towards reducing the word count by some words**"
            "- Try to maintain the core meaning while shortening as many words as possible should be the first priority"
            "- Keep the tone , tense(present tense, past tense, future tense) the voice(passive voice, active voice) same.\n"
            "The max no of words you can reduce the sentence by is given to you as well"
            "Dont comprompise on grammar rules"

            "Dont keep a full stop at the end of the line.\n"
            "Only return the improved version of the **CURRENT line** — nothing else."
            
            
        )

        curr_text = input_text.strip()
        curr_no_of_words = len(curr_text.split())
        optimized_lines = curr_text.split(".")
        for i in range(len(optimized_lines)):
            optimized_lines[i] = optimized_lines[i].strip()


        for i in range(len(optimized_lines)):
            line = optimized_lines[i]
            if not(line):
                optimized_lines.pop(i)


        to_reduce = curr_no_of_words - target_word_count

        print(f"Original word count: {curr_no_of_words}, Target word count: {target_word_count}, Words to reduce: {to_reduce}")



        """ hardocded condition to ensure decent progress. We need to intergate this so that the
        LLM does not get stuck in a generation loop when it is unable to reduce the text further"""
        count = 0
        while(to_reduce > 0) and count<10:

            for i, line in enumerate(optimized_lines):
                if to_reduce <= 0:
                    break  # Stop if target met

                # prev_line = optimized_lines[i - 1] if i > 0 else ""
                # next_line = optimized_lines[i + 1] if i < len(optimized_lines) - 1 else ""

                user_input = (
                    f"Current line:\n{line}\n\n"
                    f"Max no words you can reduce: {to_reduce}"
                )

                response = self.client.responses.create(
                    model="gpt-4.1",
                    input = f"{user_input}",
                    top_p = 0.3,
                    instructions = system_prompt
                )

                shortened = response.output[0].content[0].text.strip()
                # print(shortened)

                # Update word budget
                old_len = len(line.split())
                new_len = len(shortened.split())
                delta = old_len - new_len
                # print("Line: " + line)
                # print("Shortened: " + shortened)
                # print(to_reduce)
                # print(delta)
                # print("\n\n")

                if delta > 0:
                    optimized_lines[i] = shortened
                    to_reduce -= delta


            curr_text = ". ".join(optimized_lines).strip()

            if(curr_no_of_words - len(curr_text.split()) < 1):
                count += 1
            else:
                count = max(0,count-3)

            curr_no_of_words = len(curr_text.split())
            print(f"Current word count: {curr_no_of_words}, Words to reduce: {to_reduce}")


        final_text = ". ".join(optimized_lines).strip()
        # print(f"length of Final text after shortening: {len(final_text.split())}")
        return final_text
    
    def increase_words(self,input_text):
        pass
    

# ToDo:
# implement logic to icnrease the no fo words in case
# implement fallback logic to tell the user 
# the llm is probably hallucinating casue in the slightly shorten logic, it is icnreasing the no fo words drasticallly 





# Note:
# set threshold of how much we can actually trim  by...we actually want to trim as much as its possible
# tell the user if it would be possible or not.

# gramatical and syntax fix

# concise - tool to make cocnise output...have to ensure that the end blob doesnt become like one line 
# put 2 blobs at once to make the text greater until the blob is the complete text

# shorten - tool to slightly shorten...

# tool to icnrease the no of words if required


# i think the no of blobs taken at once should increment by 1 every time you reach the threshold


# Iterative thoughts on the ML workflow: 

# I think these two functions should be thought of as tools 
# one concises , the other slightly shortens , and the other icnreases soem words

# I think having concised more is not the problem , the problem would be if we are far away from concising

# which is better to give to the llm for cocnsie fucntion: i think we should put percentage only and not max no of words since you need to 
# tell how much to be concise...


