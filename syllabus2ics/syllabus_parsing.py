import google.generativeai as genai
import os
from ics import Calendar, Event
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

SAFE = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

def parse_syllabus(syllabus):
    model = genai.GenerativeModel(model_name="gemini-1.0-pro")
    chat = model.start_chat(history=[])
    response = chat.send_message(f"""Below is the syllabus                              
###
{syllabus}
###
We will provide additional questions that you should answer based on syllabus given. Respond with 'I understand' if you understand.
"""
    )

    code = find_code(chat)
    times = find_lecture_time(chat)
    days = find_lecture_days(chat)
    location = find_lecture_location(chat)

    print(code)
    print(times)
    print(days)
    print(location)

    return get_ics(code, times, days, location)


def get_ics(class_name, class_hours, class_days, location):

    c = Calendar()

    pattern = r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b'

    # Find all matches of the pattern in the input string
    matches = re.findall(pattern, class_hours, re.MULTILINE)
    start_time = datetime.fromisoformat(matches[0]+"-07:00")
    end_time = datetime.fromisoformat(matches[1]+"-07:00")
    # start_time = datetime.fromisoformat(class_hours.split(";")[0]+"-07:00")
    # end_time = datetime.fromisoformat(class_hours.split(";")[1]+"-07:00")

    list_days = class_days.strip('][').split(', ')
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_map = {day: i for i, day in enumerate(days)}

    int_days = []
    for day in list_days:
        int_days.append(day_map[day])

    differences = []
    for i in range(1, len(int_days)):
        differences.append(int_days[i] - int_days[i-1])

    init_classes = [(start_time, end_time)]
    for diff in differences:
        start_time = start_time + timedelta(days=diff)
        end_time = end_time + timedelta(days=diff)
        init_classes.append((start_time, end_time))


    for i in range(10):
        new_classes = []
        for curr_class in init_classes:
            e = Event()
            e.name = class_name
            e.description = location
            e.begin = curr_class[0]
            e.end = curr_class[1]
            c.events.add(e)
            new_class = (curr_class[0] + timedelta(days=7), curr_class[1] + timedelta(days=7))
            new_classes.append(new_class)
        init_classes = new_classes
        
    ics_string = c.serialize()
        
    print(ics_string)

    # with open('my.ics', 'w') as my_file:
    #     my_file.writelines(c.serialize_iter())

    return ics_string

def find_code(chat):
    codes = {}
    for x in range(5):
        response = chat.send_message(
            "What is the course code? An example of course codes would be CS8B, PSYC192, LIHL118. Just output the course code.",
            safety_settings=SAFE,
        )
        if response.text not in codes.keys():
            codes[response.text] = 0
        codes[response.text] += 1
    code = max(codes, key=codes.get)
    return code

def find_lecture_time(chat):
    times = chat.send_message("What are the class hours? Output the the start and end time (in military time) in the following format 'YYYY-MM-DDTHH:MM:SS;YYYY-MM-DDTHH:MM:SS' with 'T' being a separator between date and time. An example of the format is '2024-04-01T00:00:00;2024-04-01T02:00:00;'", safety_settings=SAFE)
    return times.text

def find_lecture_location(chat):
    location = chat.send_message("Where are the class lectures held?", safety_settings=SAFE)
    return location.text

def find_lecture_days(chat):
    days = chat.send_message("What days are the class lectures on? Valid responses include the 3 character day abbreviation, [Mon, Tue, Wed, Thu, Fri, Sat, Sun]. Respond with a list of the days found. An example of the desired format is '[Mon, Tue]'", safety_settings=SAFE)
    return days.text
