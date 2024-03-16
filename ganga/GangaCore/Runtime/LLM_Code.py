# ----------------------------------------------------------------------
#  LLM_Code.py
#
# This is a conversation with an LLM. At the prompt type your questions in plain english
# By Kalbhavi Vadhiraj <raj.31@iitj.ac.in>

# ----------------------------------------------------------------------





import string
import re
import random
import subprocess
import google.generativeai as genai
import json
import os

class LLM_Code:

    def __init__(self, api_key, model_name):
        self.api_key = api_key
        self.model_name = model_name

        # To check if the file has been written
        self.written = False

    # ----------------------------------------------------------------------
    #  respond: take a string, a set of regexps, and a corresponding
    #    set of response lists; find a match, and return a randomly
    #    chosen response from the corresponding list.
    # ----------------------------------------------------------------------
    def respond(self, str):

        genai.configure(api_key=self.api_key)

        model = genai.GenerativeModel(self.model_name)

        response = model.generate_content(str)

        return response.text
    
    # ----------------------------------------------------------------------
    #  generate_pyf: take a string and creates a python file with the response
    # ----------------------------------------------------------------------

    def generate_pyf(self,str,directory):
        response = self.respond(str)

        if (response[0:10] == "```python\n" and response[-3:] == "```"):
            filename = f"{directory}/LLM_Code_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + ".py"
            
            with open(filename, "w") as file:
                file.write(response[10:-3])
                self.written = True

            return filename

# This function would take a filename and run the python file using Ganga
def run_pyf(filename):
    
    command = f'ganga {filename}'
    output = subprocess.run(command, shell=True)

    return output 
    


    

def command_interface():
    print("Ganga LLM_Code Help\n\n")
    print("Ask your questions by typing them in plain English, using normal upper-")
    print('and lower-case letters and punctuation.  Enter "quit" when done.')
    print('=' * 72)
    print("Hello.  What is your problem?\n")
    s = ""

    file_path = os.path.abspath(__file__)

    # Assuming config.json is in the same directory as LLM_Code.py
    config_path = os.path.join(os.path.dirname(file_path), "config.json")

    config = json.load(open(config_path))

    GOOGLE_API_KEY = config["API_KEY"]
    Model = config["Model_Name"]
    directory = config["Code_Folder_Path"]

    therapist = LLM_Code(GOOGLE_API_KEY, Model)

    while s != "quit":
        try:
            s = input(">")
        except EOFError:
            s = "quit"
            print(s)
        while s[-1] in "!.":
            s = s[:-1]
        print(therapist.respond(s))
        
        address_py = therapist.generate_pyf(s,directory)

        if therapist.written:
            print(run_pyf(address_py))
            




if __name__ == "__main__":
    command_interface()
