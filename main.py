import requests
import time
import json
from datetime import datetime
from add_functions import generate_functions_info
from response_with_tools import generate_response_with_tools
from dotenv import load_dotenv
import os

load_dotenv()
# Canvas API URL and token
API_URL = os.getenv('API_URL')
API_TOKEN = os.getenv('API_TOKEN')
COURSE_ID = os.getenv('COURSE_ID')
ASSIGNMENT_ID = os.getenv('ASSIGNMENT_ID')


# Header with authorization token
headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_submissions(course_id, assignment_id):
    url = f'{API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print('Failed to retrieve submissions')
        print(response.status_code, response.text)
        return None

def grade_submission(student_id, grade, comment):
    """
    Grade a submission for a student
    param: student_id: The Canvas user ID of the student
    param: grade: The grade to assign to the submission its a number between 0 and 100
    param: comment: The comment to add to the submission
    """
    url = f'{API_URL}/courses/{COURSE_ID}/assignments/{ASSIGNMENT_ID}/submissions/{student_id}'
    if grade == 0:
        grade = 1 # Ensure grade is at least 1
    
    payload = {
        'submission': {
            'posted_grade': grade
        },
        'comment': {
            'text_comment': comment
        }
    }
    response = requests.put(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        print(f'Graded and commented on submission for student {student_id}')
    else:
        print(f'Failed to grade and comment on submission for student {student_id}')
        print(response.status_code, response.text)
    return json.dumps({"data":"Graded and commented on submission for the student"})

def main():
    submissions = get_submissions(COURSE_ID, ASSIGNMENT_ID)
    callables = [grade_submission]
    functions_json_array, available_functions = generate_functions_info(callables)
    # system_msg = "The user is going to submit an assignment and your goal is to grade it."
    system_msg = ""
    with open('prompt.txt', 'r') as file:
        system_msg = file.read().strip()
    messages = list()
    messages.append({"role": "system", "content": system_msg})

    if submissions:
        for submission in submissions:
            student_id = submission['user_id']
            submission_text = submission.get('body', '')
            submission_date = submission.get('submitted_at')
            graded_at = submission.get('graded_at')

            # Ensure submission_text is a string
            if not isinstance(submission_text, str):
                submission_text = ''

            # Convert submission and graded dates to datetime objects
            submission_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00')) if submission_date else None
            graded_at = datetime.fromisoformat(graded_at.replace('Z', '+00:00')) if graded_at else None

            # Check if the submission has been graded since the last submission
            if graded_at and submission_date and graded_at >= submission_date:
                print(f'Submission for student {student_id} has already been graded and not resubmitted.')
                continue

            # Only call the AI if the submission is new or resubmitted
            if not graded_at or (submission_date and submission_date > graded_at):
                prompt = f"Grade the submission for student the student: {student_id}: \n{submission_text}" 
                print(prompt)
                messages.append({"role": "user", "content": prompt})
                response = generate_response_with_tools(messages, "gpt-4o", functions_json_array, available_functions)
                response_message = response.choices[0].message.content
                # messages.append({"role": "assistant", "content": response_message})
                print(response_message)

if __name__ == '__main__':
    main()