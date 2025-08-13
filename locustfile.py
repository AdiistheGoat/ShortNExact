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