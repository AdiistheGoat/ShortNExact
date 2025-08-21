import openai
import re
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize
from collections import defaultdict

#ToDo (ML):
# store the current least text and least no of words
# integrate different starting points always
# fix the multiple .... issue 

#ToDo (Load Testing):
# deep dive into load testing and see how i am able to create > 10000 request in past 24 hours when it should have stopped me.
# How does locust load test. what do the metrics mean. what qualifies as a correct response for locust and what issues could be 
# there because of which that error is coming

#ToDo
#Host on EC2

#ToDo
# create frontend for generating api key 

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



    async def llm_orchestrator(self,input_text):
        """
        Iteratively reduces or adjusts the word count of input text to match the desired target using LLM-guided tool invocation.

        The function uses a loop where an LLM selects the most appropriate rewriting tool (e.g., concise rewriting, shortening, word expansion)
        based on the current and target word counts, as well as tool call history. It continues calling tools until the word goal is met.

        Args:
            input_text (str): Original text input provided by the user.

        Returns:
            str: Final rewritten version of the text adjusted to the desired word count.
        """
        curr_input_text = input_text
        word_count_goal = self.number_of_words
        curr_count = self.count_words(input_text)


        tools = [

        {
            "type": "function",
            "name": "process_concisely",
            "description": "Use this tool when the user wants to restructure and condense large blocks of text into a concise form while preserving key ideas. Best for aggressive"
            "length reduction."
        },

        {
            "type": "function",
            "name": "process_short",
            "description": "Use this tool to reduce word count while keeping sentence structure and paragraph flow unchanged. Preferred when the content "
            "is slightly over the word budget. "
        },

        {
            "type": "function",
            "name": "increase_words",
            "description": "Use this to gently expand a response that just slightly falls short of the word limit by enriching examples or using more expressive language."
            "and meaning should remain unchanged."
        },

        {
            "type": "function",
            "name": "decrease_words",
            "description": "Use this to shave off extra words from a response that just slightly goes over the word limit, focusing on cutting modifiers or redundant examples.",
        }
        ]


        system_prompt_segment = """
            You are an intelligent rewriting assistant tasked with reducing a block of text to a specified target word count. 
            You must select and call the most appropriate tools from the available list to meet the word count goal. 

            If the same tool has been called multiple times already 
            -select the next best tool.
            -sometimes selecting tools that doesnt make sense get you to the right path

            You are given-:
            1) Current word count of the text 
            2) Goal word count
            3) History of tools called 
        """

        dic_history = defaultdict(int)
        while(curr_count!=word_count_goal):

            message = f"""
               Current word count: {curr_count}
               Goal word count: {word_count_goal }
               History of tools called: {dic_history}
            """

            response = await self.client.responses.create(
                model="gpt-4.1",
                input = message,
                top_p=0.3,
                instructions=system_prompt_segment,
                tools = tools
            )

            tool_call = response.output[0]
            function_str = str(tool_call.name)

            dic_history[function_str] += 1

            print(f"Calling {function_str}")

            curr_input_text = await self.call_function(function_str,curr_input_text)
            curr_count = self.count_words(curr_input_text)

            liste = [True if dic_history[i]>3 else False for i in dic_history ]
            if True in liste:
                return "Current iteration failed!"


        return curr_input_text
        
        

    async def call_function(self,function_name,input_text):
        """
        Dynamically calls the appropriate text rewriting function based on the function name.

        Args:
            function_name (str): Name of the function to invoke. Must be one of:
                                'process_concisely', 'process_short', 'increase_words', 'decrease_words'.
            input_text (str): The text to process using the selected function.

        Returns:
            str: The transformed text after applying the specified function.
        """
        if(function_name=="process_concisely"):
            return await self.process_concisely(input_text)

        elif(function_name=="process_short"):
            return await self.process_short(input_text)

        elif(function_name=="increase_words"):
            return await self.increase_words(input_text)

        elif(function_name=="decrease_words")  :
            return await self.decrease_words(input_text)



    def count_words(self,text):
        """
        Counts the number of words in a given text.

        Args:
            text (str): The input string to analyze.

        Returns:
            int: Total number of words detected, including abbreviations, hyphenated words, and numbers.
        """
        pattern = r"\b(?:\w+(?:[-.']\w+)*)\b"
        matches = re.findall(pattern, text)
        return len(matches)

    async def process_text(self):
        """
        Main entry point for processing the input text to match a target word count while preserving meaning and readability.

        This method first performs grammar and punctuation correction on the raw input text.
        It then delegates rewriting to an LLM-based orchestrator, which dynamically selects the most suitable rewriting tools
        (e.g., concise rewriting, shortening, word expansion) to reach the desired word count.

        Returns:
            Tuple[str, int]: A tuple containing the rewritten text and its final word count.
        """

        try: 
            input_text = await self.fix_syntax_and_grammar(self.input_text)

            while(True):
                processed_text = await self.llm_orchestrator(input_text)
                if(processed_text != "Current iteration failed!"):
                    break
        except Exception as e:
            return f"Error during processing: {str(e)}",self.count_words(e)

        return processed_text, self.count_words(processed_text)


    async def fix_syntax_and_grammar(self,input_text):
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

        segment_response = await self.client.responses.create(
            model="gpt-4.1",
            input=input_text,
            top_p=0.3,
            instructions=system_prompt_segment
        )

        segmented_text = segment_response.output[0].content[0].text.strip()

        return segmented_text 


    async def process_concisely(self,input_text):
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
            "Pls dont chnage the word count of the text. Just divide the text into different parts"
        )

        segment_response = await self.client.responses.create(
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

                Your task is to take a given paragraph and reduce its length by at least { (to_reduce_percentage*100) + 10}% while preserving all core ideas, meaning, and tone.

                Guidelines:
                - Eliminate redundant words, repetitive phrasing, and filler language.
                - Merge sentences or phrases where possible without losing clarity.
                - Keep the structure logically coherent and easy to read.
                - Avoid generic summaries — keep all specific details and reasoning intact.
                - Do NOT remove any key idea or supporting detail.
                - Use natural, human-like language — not robotic or overly compressed.
                - Remove lines only if they do not contribute to the core meaning and are outliers. 
                - If the word count is not yet met, start removing lines that are not the most essential 
                **ensure to make progress towards reducing the word count by at least {(to_reduce_percentage*100) + 10}%***

                Return ONLY the revised **shortened paragraph**. Do not explain anything.
            """

            for index in  range(len(curr_blobs)):
                refine_response = await self.client.responses.create(
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

        final_output = await self.process_short(final_output)

        return final_output
    


    async def process_short(self,input_text):
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

                response = await self.client.responses.create(
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
            return await self.decrease_words(final_text)
        else:
            return await self.increase_words(final_text) 

    
    """
    Slightly increases the no of words to the desired word count by increasing content examples
    """
    async def increase_words(self,input_text):
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
        curr_no_of_words = self.count_words(curr_text)
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

                response = await self.client.responses.create(
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

            if( self.count_words(curr_text) - curr_no_of_words ) < 1:
                count += 1
            else:
                count = max(0,count-1)

            curr_no_of_words = self.count_words(curr_text)
            print(f"Current word count: {curr_no_of_words}, Words to increase: {to_increase}")


        final_text = ". ".join(optimized_lines).strip()
        print(f"length of Final text after increasing: {self.count_words(final_text)}")
        return final_text
        



    """
    Slightly increases the no of words to the desired word count by decreasing some content examples
    """
    async def decrease_words(self,input_text):
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

                response = await self.client.responses.create(
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