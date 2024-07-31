import requests
import os
import re
import json
from dotenv import load_dotenv

# Load .env file first
load_dotenv('.env')

# Override with .env.local if it exists
if os.path.exists('.env.local'):
    load_dotenv('.env.local', override=True)


CHATPDF_KEY = os.getenv('CHATPDF_KEY')

print(os.getcwd())

"""
Provide a short sumamry: What is the paper about (abstract)?
What problem did they want to solve?
What Methodology did they use?
What is the main contribution of the paper?
What are limitations?
Although Limitations, why is it still considerably good?
"""


### LOADER
if False:
    
    PATH = "./Reading"

    pdf_files = []

    # Traverse the specified directory and its subdirectories
    for root, dirs, files in os.walk(PATH):
        for file in files:
            if file.lower().endswith(".pdf"):
                # Check if the file is a PDF (case-insensitive)
                file_path = os.path.join(root, file)
                pdf_files.append(file_path)

    # Print the dictionary
    for pdf_path in pdf_files:
        files = [
            ('file', ('file', open(pdf_path, 'rb'), 'application/octet-stream'))
        ]
        headers = {
            'x-api-key': CHATPDF_KEY
        }

        response = requests.post(
            'https://api.chatpdf.com/v1/sources/add-file', headers=headers, files=files)

        if response.status_code == 200:
            print('Source ID:', response.json()['sourceId'])
            with open('ids.txt', 'a') as f:
                filename = pdf_path.split("/")[-1]
                match = re.search(r'(\d+)-', filename)
                if match:
                    number = match.group(1)
                else:
                    number = None
                
                f.write(f"{number} - {filename} : {response.json()['sourceId']} \n")
        else:
            print('Status:', response.status_code)
            print('Error:', response.text)
        


# Define a dictionary to store the extracted data
data_dict = {}

# Open and read the text file
with open("ids.txt", "r") as file:
    for line in file:
        # Split each line by ":" to separate the file information from the ID
        parts = line.strip().split(" : ")
        if len(parts) == 2:
            file_info, src_id = parts
            # Further split the file information to extract the file name and number
            number, file_name = file_info.split(" - ")
            data_dict[int(number)] = {"file_name": file_name, "src_id": src_id}

# Print the extracted data
for number, info in data_dict.items():
    continue
    print(f"Number: {number}")
    print(f"File Name: {info['file_name']}")
    print(f"Source ID: {info['src_id']}")
    

for i in range(1, 21, 1):
    print(f"{i}: {data_dict[i]['file_name']} - {data_dict[i]['src_id']}")
    
    headers = {
        'x-api-key': CHATPDF_KEY,
        "Content-Type": "application/json",
    }

    data = {
        'sourceId': data_dict[i]['src_id'],
        'messages': [
            {
                'role': "user",
                'content': "Provide a short sumamry: What is the paper about (abstract)?",
            },
            {
                'role': "user",
                'content': "What problem did they want to solve?",
            },
            {
                'role': "user",
                'content': "What Methodology did they use?",
            },
            {
                'role': "user",
                'content': "What is the main contribution of the paper?",
            },
            {
                'role': "user",
                'content': "What are limitations?",
            },
            {
                'role': "user",
                'content': "Although Limitations, why is it still considerably good?",
            },
        ]
    }

    output_folder = "./Summary"

    response = requests.post(
        'https://api.chatpdf.com/v1/chats/message', headers=headers, json=data)

    if response.status_code == 200:
        print('Result:', response.json()['content'])
        # Split the response at each newline character and save it to the corresponding question
        response_text = response.json()['content']
        responses = response_text.split('\n')

        # Create a dictionary to store responses for each question
        responses_dict = {
            "Provide a short sumamry: What is the paper about (abstract)?": "",
            "What problem did they want to solve?": "",
            "What Methodology did they use?": "",
            "What is the main contribution of the paper?": "",
            "What are limitations?": "",
            "Although Limitations, why is it still considerably good?": ""
        }

        # Define keywords for each question to identify the corresponding section in the response
        keywords = {
            "Provide a short sumamry: What is the paper about (abstract)?": "Summary of the Paper",
            "What problem did they want to solve?": "Problem Addressed",
            "What Methodology did they use?": "Methodology",
            "What is the main contribution of the paper?": "Main Contribution",
            "What are limitations?": "Limitations",
            "Although Limitations, why is it still considerably good?": "Value Despite Limitations"
        }

        # Split the response text by sections using keywords
        for question, keyword in keywords.items():
            start_idx = response_text.find(keyword)
            if start_idx != -1:
                end_idx = response_text.find("###", start_idx + len(keyword))
                if end_idx == -1:
                    end_idx = len(response_text)
                responses_dict[question] = response_text[start_idx:end_idx].strip()

        # Save the responses to a JSON file in the specified output folder
        output_path = os.path.join(output_folder, data_dict[i]['file_name'] + ".json")
        with open(output_path, 'w') as json_file:
            json.dump(responses_dict, json_file, indent=4)

        print(f"JSON response saved to {output_path}")
    else:
        print('Status:', response.status_code)
        print('Error:', response.text)

