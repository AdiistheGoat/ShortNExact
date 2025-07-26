import openai
import re
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

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


    def count_words(self,text):
        # Match words, abbreviations, hyphenated terms, numbers, etc.
        pattern = r"\b(?:\w+(?:[-.']\w+)*)\b"
        matches = re.findall(pattern, text)
        return len(matches)

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
            return processed_text, self.count_words(processed_text)

        elif self.option == "Shorten text (choose if you want to slightly shorten text to fix it within a word count)":
            processed_text = self.process_short(input_text)
            return processed_text, self.count_words(processed_text)


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

        curr_no_of_words = self.count_words(final_output)

        to_reduce = curr_no_of_words - target_word_count
        to_reduce_percentage = (to_reduce)/ curr_no_of_words
         
        print('Current word count:', curr_no_of_words)
        print('Words to reduce:', to_reduce)
        print('Percentage to reduce:', to_reduce_percentage)
        print("\n")

        count = 0
        while(True):

            if(count>=3):
                if(len(curr_blobs)==1):
                    break
                count = 0
                new_blobs = []
                for index in range(0,len(curr_blobs),2):
                    cumulative_blob = ""
                    for j in range(index,min(index+2,len(curr_blobs))):
                        cumulative_blob += curr_blobs[j]
                    new_blobs.append(cumulative_blob)
                print(len(curr_blobs))
                print(len(new_blobs))
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
            final_output = "\n\n".join(curr_blobs).strip()
            curr_no_of_words = self.count_words(final_output)

            delta =  to_reduce+target_word_count - curr_no_of_words 

            # hardocoded condition to ensure decent progress
            if(delta/to_reduce<=0.1):
                count+=1
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
        curr_no_of_words = self.count_words(curr_text)

        optimized_lines = sent_tokenize(curr_text)
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
        while(to_reduce > 0) and count<3:

            for i, line in enumerate(optimized_lines):
                if to_reduce <= 0:
                    print("breaking before")
                    break  # Stop if target met

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

                # Update word budget
                old_len = self.count_words(line)
                new_len = self.count_words(shortened)
                delta = old_len - new_len

                if delta > 0:
                    optimized_lines[i] = shortened
                    to_reduce -= delta


            curr_text = ". ".join(optimized_lines).strip()

            if(curr_no_of_words - self.count_words(curr_text) < 1):
                count += 1
            else:
                count = max(0,count-1)

            curr_no_of_words = self.count_words(curr_text)
            print(f"Current word count: {curr_no_of_words}, Words to reduce: {to_reduce}")


        final_text = ". ".join(optimized_lines).strip()
        final_no_of_words = self.count_words(final_text)

        print("Final no of words: " + str(final_no_of_words))

        if(final_no_of_words==self.number_of_words):
            return final_text
        if(final_no_of_words>self.number_of_words):
            return self.decrease_words(final_text)
        else:
            return self.increase_words(final_text) 

    
    """
    Slightly increases the no of words to the desired word count by increasing content examples
    """
    def increase_words(self,input_text):
        """
        Expands an already input_text to reach a target word count.
        
        The goal is to safely increase the number of words while preserving the original tone, 
        meaning, grammar, tense, and voice. The LLM is guided to use techniques like adding examples, 
        using descriptive synonyms, or elaborating on short phrases.

        Parameters:
            input_text (str): The base text to be expanded.

        Returns:
            str: An expanded version of the input text, closer to the target word count.
        """

        # Logic to shorten text to fit within a specified word count
        target_word_count = self.number_of_words

        # System prompt
        system_prompt = (
            "Your job is to increase the number of words for a line"

            "You may consider using any of the following techniques:\n"
            "- Expand abbreviated phrases (e.g., 'e.g.' → 'for example')\n"
            "- Replace single words with more descriptive phrases (e.g., 'AI' → 'artificial intelligence systems')\n"
            "- Add light clarification or qualifiers (e.g., 'globally' → 'across various parts of the world')\n"
            "- Use synonyms that are longer but equivalent in meaning (e.g., 'help' → 'provide assistance')\n"
            "- Insert non-redundant adjectives or modifiers (e.g., 'growth' → 'rapid technological growth')\n"

            "**ensure to make progress towards reducing the word count by some words**"
            "- Try to maintain the core meaning while increasing the no of words should be the first priority"
            "- Keep the tone , tense(present tense, past tense, future tense) the voice(passive voice, active voice) same.\n"
            "The max no of words you can increase the sentence by is given to you as well"
            "Dont comprompise on grammar rules"

            "Dont keep a full stop at the end of the line.\n"
            "Only return the improved version of the **CURRENT line** — nothing else."   
        )

        curr_text = input_text.strip()
        curr_no_of_words = len(curr_text.split())
        optimized_lines = sent_tokenize(curr_text)

        for i in range(len(optimized_lines)):
            optimized_lines[i] = optimized_lines[i].strip()


        for i in range(len(optimized_lines)):
            line = optimized_lines[i]
            if not(line):
                optimized_lines.pop(i)


        to_increase= target_word_count - curr_no_of_words

        print(f"Original word count: {curr_no_of_words}, Target word count: {target_word_count}, Words to increase: {to_increase}")

        count = 0
        while(to_increase > 0) and count<3:

            for i, line in enumerate(optimized_lines):
                if to_increase <= 0:
                    break  

                user_input = (
                    f"Current line:\n{line}\n\n"
                    f"Max no words you can increase: {to_increase}"
                )

                response = self.client.responses.create(
                    model="gpt-4.1",
                    input = f"{user_input}",
                    top_p = 0.3,
                    instructions = system_prompt
                )

                increased = response.output[0].content[0].text.strip()

                # Update word budget
                old_len = len(line.split())
                new_len = len(increased.split())
                delta = new_len - old_len

                if delta > 0:
                    optimized_lines[i] = increased
                    to_increase -= delta


            curr_text = ". ".join(optimized_lines).strip()

            if( len(curr_text.split() - curr_no_of_words ) < 1):
                count += 1
            else:
                count = max(0,count-1)

            curr_no_of_words = len(curr_text.split())
            print(f"Current word count: {curr_no_of_words}, Words to increase: {to_increase}")


        final_text = ". ".join(optimized_lines).strip()
        print(f"length of Final text after increasing: {len(final_text.split())}")
        return final_text
        



    """
    Slightly increases the no of words to the desired word count by decreasing some content examples
    """
    def decrease_words(self,input_text):
        """
        Further shortens an already condensed input_text to reach a target word count.
        
        This function assumes the input text has already been pre-shortened once.
        It iteratively refines each line using an LLM to reduce examples, modifiers,
        and redundancy while preserving meaning, grammar, and structure.

        Parameters:
            input_text (str): Previously shortened text that still needs to be reduced.

        Returns:
            str: A further optimized, shorter version of the input text.
        """

        # Logic to shorten text to fit within a specified word count
        target_word_count = self.number_of_words

        # System prompt
        system_prompt = (
            "You are a text shortener"

            "The line you are given has already been shortened once.\n"

            "You may consider possibilities such as:\n"
            "- Removing examples if they are non-essential\n"
            "- Eliminating redundant words or phrases\n"
            "- Merging ideas or compressing expressions\n"
            "- Cutting weak modifiers (e.g., very, really) where safe\n\n"

            "Rules: "
            "- **ensure to make progress towards reducing the word count by some words**"
            "- Try to maintain the core meaning while shortening as many words as possible should be the first priority"
            "- Keep the tone , tense(present tense, past tense, future tense) the voice(passive voice, active voice) same.\n"
            "- The max no of words you can reduce the sentence by is given to you as well"
            "- Dont comprompise on grammar rules"
            "- Dont keep a full stop at the end of the line.\n"
            "- Only return the improved version of the **CURRENT line** — nothing else."
        )

        curr_text = input_text.strip()
        curr_no_of_words = self.count_words(curr_text)

        optimized_lines = sent_tokenize(curr_text)
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
        while(to_reduce > 0) and count<3:

            for i, line in enumerate(optimized_lines):
                if to_reduce <= 0:
                    break  

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

                # Update word budget
                old_len = self.count_words(line)
                new_len = self.count_words(shortened)
                delta = old_len - new_len

                if delta > 0:
                    optimized_lines[i] = shortened
                    to_reduce -= delta


            curr_text = ". ".join(optimized_lines).strip()

            if(curr_no_of_words - self.count_words(curr_text) < 1):
                count += 1
            else:
                count = max(0,count-1)

            curr_no_of_words = self.count_words(curr_text)
            print(f"Current word count: {curr_no_of_words}, Words to reduce: {to_reduce}")

        final_text = ". ".join(optimized_lines).strip()

        return final_text
