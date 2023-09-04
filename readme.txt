# TestText
# Api to make test questions from *.txt, *.pdf files
# python+FastApi+docker

# Api Get:
    num_questions: int = 5
    num_answers: int = 4
    language: str = "English"
    format: str = ''
    comment: str = "Answers should have 100 symbols."
    file
# Api Return:
json:
  "questions": [\
      {\
        "question": "Question1",\
        "answers": [\
          "Answer1",\
          "Answer2",\
          "Answer3",\
          "Answer4"\
        ],\
        "correct_answer": 1\
      }
      ...
      ]

# Installation:
git clone https://github.com/dimmastro/TestText.git
# Fill api key in maim.py:
openai.api_key = ""
# Build and run docker:
docker build --tag testtext .
docker run -d -p 8000:8000 --name testtext testtext

# Doc:
http://127.0.0.1:8000/docs
Api:
http://127.0.0.1:8000/testtext

# To stop container:
docker container stop testtext

# To remove container:
docker rm testtext

# To run without docker:
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
# Doc:
http://127.0.0.1:8000/docs
Api:
http://127.0.0.1:8000/testtext