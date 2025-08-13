from locust import HttpUser, task,constant

class HelloWorldUser(HttpUser):

    host = "http://127.0.0.1:4000"

    @task
    def api_key(self):
        params={
            "name": "Aditya goyal test 11",
            "email": "adigoyal0807@gmail.com",
            "validity": 23
        }
        self.client.get('/api_key', json = params)


    # @task
    # def reduce_content(self):
    #     params = {
<<<<<<< HEAD
    #         "llm_api_key": "enter_llm_key",

    #         "app_key": "enter_app_key",
=======
    #         "llm_api_key": "Enter_llm_key",

    #         "app_key": "Enter_app_key",
>>>>>>> 42ad4eb (removed keys)
    #         "option": 1,
    #         "input_text": "Artificial Intelligence (AI) has rapidly evolved from a theoretical concept to a transformative force reshaping industries societies and our everyday lives What was once confined to the realms of science fiction is now an integral part of modern technology — from virtual asistants to autonomous vehicels. But what exactly is AI and why has it garnered such global attention Artificial Intelligence refers to the development of computer systems that can perform tasks typically requiring human intellignce. These tasks include problem solving decision making visual perception speech recognition and natural language processing. AI can be broadly classified into • Narrow AI: Specialized systems designed to perform a single task (e.g., Google Search facial recognition) • General AI: Hypothetical systems with the ability to understand and learn any intellectual task a human can do • Superintelligent AI — a speculative future where machines surpass human intelligence across all feilds. The idea of creating intelligent machines dates back to ancient myths and early mechanical invetions. However, the formal discipline of AI began in the 1950's Alan Turing's seminal paper Computing Machinery and Intelligence proposed the question: Can machines think? Milestones in AI development include • 1956: The Dartmouth Conference considered the birthplace of AI • 1997: IBMs Deep Blue defeated world chess champion Garry Kasparov • 2012–Present Deep learning breakthroughts led to rapid progress in image and speech recognition. AI has permeated nearly every domain of modern life."
    #             ,
    #         "no_of_words": 170
    #     }
    #     self.client.get('/', json = params)