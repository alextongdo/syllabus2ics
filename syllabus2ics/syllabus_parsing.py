import google.generativeai as genai
import os
from ics import Calendar, Event
from datetime import datetime, timedelta,date
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

    course_code = find_code(chat)
    possible_events = find_events(chat)

    print(course_code)
    print(possible_events)

    c = Calendar()


    # Define the regex pattern

    # 1. Course code
    # 2. Possible events: lectures, office hours, discussions, midterm, final
    # 3. For each that exists:
    #       start date: 2024-05-07
    #       location
    #       days of the week + times : “mon 10:00-10:50, wed 10:00-10:50, fri 10:00-10:50”

    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    day_map = {day: i for i, day in enumerate(days)}
    all_events = ["lectures", "office", "discussions", "midterm", "final"]
    for event in all_events:
        if event in possible_events:
            if event == "office":
                event = "office hours"
            print("CURR EVENT: " + event)
            # get raw start day
            raw_start_day = find_start_day(chat, event)
            print("RAW START DATE: " + raw_start_day)
            if "none" in raw_start_day:
                print("no start day found skipping" + event)
                continue
            pattern = r"\d{4}-\d{2}-\d{2}"
            match = re.search(pattern, raw_start_day)
            if match:
                raw_start_day = match.group()
            else:
                raise ValueError("Invalid raw start day")

            print("POST START DATE: " + raw_start_day)
            start_date = date.fromisoformat(raw_start_day)
            print(start_date)
            # get location
            location = find_event_location(chat, event)
            if "none" in location:
                location = ""
            print("LOCATION: " + location)
            # get days of the week
            raw_events = find_event_times(chat, event)
            if "none" in raw_events:
                print("none raw_events")
                continue
            print("RAW EVENT INSTANCES: " + raw_events)
            raw_events = [d.strip() for d in raw_events.split(",") if len(d.strip()) > 0]
            prev_day = None
            curr_date = start_date
            init_events = []
            for ev in raw_events:
                day = ev.split()[0]
                curr_day = day_map[day]
                diff = 0
                if prev_day is not None:
                    diff = curr_day - prev_day
                prev_day = curr_day
                curr_date = curr_date + timedelta(days=diff)
                raw_start_time = (ev.split(" ")[1]).split("-")[0] + ":00"
                print("RAW_START_TIME: " + raw_start_time)
                raw_end_time = (ev.split(" ")[1]).split("-")[1] + ":00"
                print("RAW_END_TIME: " + raw_end_time)
                start_time_iso = curr_date.isoformat() + "T" + raw_start_time + "-07:00"
                end_time_iso = curr_date.isoformat() + "T" + raw_end_time + "-07:00"
                print("ISO_START_TIME: " + start_time_iso)
                print("ISO_END_TIME: " + end_time_iso)
                start_time = datetime.fromisoformat(start_time_iso)
                end_time = datetime.fromisoformat(end_time_iso)
                init_events.append((start_time, end_time))

            rep = 10
            if event in "midterm final":
                rep = 1
            for i in range(rep):
                new_events = []
                for curr_class in init_events:
                    e = Event()
                    e.name = course_code + " " + event
                    e.description = location
                    e.begin = curr_class[0]
                    e.end = curr_class[1]
                    c.events.add(e)
                    new_class = (curr_class[0] + timedelta(days=7), curr_class[1] + timedelta(days=7))
                    new_events.append(new_class)
                init_events = new_events

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

def find_events(chat):
    response = chat.send_message(
        "Out of the following possible events, identify which of these events are mentioned in the syllabus.\n`lectures, office hours, discussions, midterm, final`\nPlease respond only with a comma separated list with elements from the possible events.\nAn example response would be: lectures, office hours, final",
        safety_settings=SAFE
    )
    return response.text

def find_event_times(chat, event):
    times = chat.send_message(f"Out of the following possible days of the week, identify which days and time interval on those days are the {event}?\n`mon, tue, wed, thu, fri, sat, sun`\nPlease only respond with a comma separated list with elements from the possible days followed by a 24 hour time interval (HH:MM-HH:MM). An example of the expected response is `mon 10:00-11:00, wed 12:00-13:00, fri 5:30-6:30`.", safety_settings=SAFE)
    return times.text

def find_event_location(chat, event):
    location = chat.send_message(f"What is the location of {event}? Please only respond with a single room code or `none` if no location is mentioned. An example of the expected response is `La Kretz Hall 110` or `none`.", safety_settings=SAFE)
    return location.text

def find_start_day(chat, event):
    day = chat.send_message(f"What is the start date of {event}? Please only respond with the start date in ISO date format `YYYY-MM-DD` or `none` if no start date is mentioned. An example of the expected response is `2024-04-01` or `none`.", safety_settings=SAFE)
    return day.text
