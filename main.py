from pydantic import BaseModel
from fastapi import FastAPI, Depends, File, UploadFile
import openai
import json
import time
from PyPDF2 import PdfReader
import io


openai.api_key = "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"
MAX_RETRIES = 50
RETRY_DELAY = 30  # Delay in seconds between retries


class TestText(BaseModel):
    num_questions: int = 5
    num_answers: int = 4
    language: str = "English"
    format: str = '    "questions": [\
      {\
        "question": "Question1",\
        "answers": [\
          "Answer1",\
          "Answer2",\
          "Answer3",\
          "Answer4"\
        ],\
        "correct_answer": 1\
      }\
      ...\
      ]'
    comment: str = "Answers should have 100 symbols."

def ask_question(question):
    prompt = f"{question}\n"
    MODEL = "gpt-3.5-turbo"
    for _ in range(MAX_RETRIES):
        print(_)
        try:
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                ],
                temperature=0.99,
                max_tokens=3000,
            )
            message = response["choices"][0]["message"]["content"]
            return message
        except openai.error.APIError as e:
            # if response.status_code == 502:  # Bad gateway error
            #     print("Received a 502 Bad Gateway error. Retrying...")
            #     time.sleep(RETRY_DELAY)
            #     continue
            # else:
            #     raise e
            # print("Received a 502 Bad Gateway error. Retrying...")
            print("Received a error. Retrying...")
            # raise e
            time.sleep(RETRY_DELAY)
            continue
        except openai.error.RateLimitError as e:
            retry_time = e.retry_after if hasattr(e, 'retry_after') else 30
            print(f"Rate limit exceeded. Retrying in {retry_time} seconds...")
            time.sleep(retry_time)
            continue
        except openai.error.ServiceUnavailableError as e:
            retry_time = 10  # Adjust the retry time as needed
            print(f"Service is unavailable. Retrying in {retry_time} seconds...")
            time.sleep(retry_time)
            continue
        except openai.error.APIError as e:
            retry_time = e.retry_after if hasattr(e, 'retry_after') else 30
            print(f"API error occurred. Retrying in {retry_time} seconds...")
            time.sleep(retry_time)
            continue
        except OSError as e:
            retry_time = 5  # Adjust the retry time as needed
            print(f"Connection error occurred: {e}. Retrying in {retry_time} seconds...")
            time.sleep(retry_time)
            continue
    raise Exception("Exceeded maximum retries without a successful response.")

def ask_question0(question):
    prompt = f"{question}\n"
    MODEL = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model = MODEL,
        messages=[
        {"role": "system", "content": prompt},
        ],
        temperature = 0.5,
        max_tokens = 2500,
    )
    message = response["choices"][0]["message"]["content"]
    return message

def split_prompt(text, split_length, question):
    if split_length <= 0:
        raise ValueError("Max length must be greater than 0.")
    num_parts = -(-len(text) // split_length)
    file_data = []
    for i in range(num_parts):
        start = i * split_length
        end = min((i + 1) * split_length, len(text))
        if i == num_parts - 1:
            content = f'[START PART {i + 1}/{num_parts}]\n' + text[start:end] + f'\n[END PART {i + 1}/{num_parts}]'
            content += '\nALL PARTS of "text for creating the questions" SENT. Now you can continue processing the request: ' + question
        else:
            content = f'Do not answer yet. This is just another part of the "text for creating the questions" I want to send you. Just receive and acknowledge as "Part {i + 1}/{num_parts} received" and wait for the next part.\n[START PART {i + 1}/{num_parts}]\n' + text[
                                                                                                                                                                                                                                            start:end] + f'\n[END PART {i + 1}/{num_parts}]'
            content += f'\nRemember not answering yet. Just acknowledge you received this part with the message "Part {i + 1}/{num_parts} received" and wait for the next part.'
        file_data.append({
            'name': f'split_{str(i + 1).zfill(3)}_of_{str(num_parts).zfill(3)}.txt',
            'content': content
        })
    return file_data


app = FastAPI()

@app.post('/testtext')
async def create_testtext(item: TestText = Depends(), file: UploadFile = File(...)):
    file_extension = file.filename.split('.')[-1].lower()
    extracted_text = None
    if file_extension == 'txt':
        extracted_text_bytes = await file.read()
        extracted_text = extracted_text_bytes.decode('utf-8')
    elif file_extension == 'pdf':
        pdf_data = await file.read()
        pdf_reader = PdfReader(io.BytesIO(pdf_data))
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text()

    question = """Please write according to the text """ + str(item.num_questions) + """ test questions in """ + item.language + """ language . Each should have """ + str(item.num_answers) + """ answer options. After the answers to the question write the number of the correct answer. Comment:""" + item.comment + """.  Give me json format""" + item.format + """ Please start. """
    file_data = split_prompt(extracted_text, 1500, question)
    for i in range(len(file_data)):
        quest = file_data[i]['content']
        print(i)
        print(quest)
        answer = ask_question(quest)
        print(answer)

    print(answer)
    answer_json = json.loads(answer)
    print(answer_json)
    return {"item":item, "question":question, "answer_txt":answer, "answer_json":answer_json}


