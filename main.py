from datetime import datetime, timedelta
import re
import uuid

try:
    from icalendar import Calendar, Event, vText

    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions
    from selenium.webdriver.support.select import Select
    from selenium.webdriver.support.ui import WebDriverWait

    from webdriver_manager.chrome import ChromeDriverManager

except ImportError:
    print("You need to install requirements, run:")
    print("python -m pip install icalendar selenium webdriver-manager")
    exit(1)


# fill in your account details here
USERNAME = ""
PASSWORD = ""


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get("https://lucas.lboro.ac.uk/its_apx/f?p=student_timetable")

username_field = driver.find_element(By.ID, "username")
username_field.clear()
username_field.send_keys(USERNAME)

password_field = driver.find_element(By.ID, "password")
password_field.clear()
password_field.send_keys(PASSWORD)

username_field.send_keys(Keys.ENTER)

# trust-browser-button
while True:
    try:
        submit = driver.find_element(By.ID, "trust-browser-button")
        submit.click()
        break

    except NoSuchElementException:
        continue

select_field = WebDriverWait(driver, 5).until(
    expected_conditions.presence_of_element_located((By.ID, "P2_MY_PERIOD"))
)
selection = Select(select_field)
opts = list(
    filter(
        lambda x: x.startswith("Sem "),
        [i.text for i in select_field.find_elements(By.TAG_NAME, "option")],
    )
)


urls = dict(zip(opts, [[] for _ in opts]))

for opt in opts:
    # select timetable
    select_field = WebDriverWait(driver, 5).until(
        expected_conditions.presence_of_element_located((By.ID, "P2_MY_PERIOD"))
    )
    selection = Select(select_field)
    selection.select_by_index([i.text for i in selection.options].index(opt))
    driver.refresh()

    try:
        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "tt_cell")
            )
        )

    except TimeoutException:
        # probably empty table or just didnt load ¯\_(ツ)_/¯
        continue

    timetable = driver.find_element(By.ID, "timetable_details")

    for entry in timetable.find_elements(By.CLASS_NAME, "tt_cell"):
        # open and read details card to get urls
        entry.click()
        urls[opt].append(
            WebDriverWait(driver, 5)
            .until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[@id='action_div']/div/div[@id='event_details']/object[@id='action_page'][@data]",
                    )
                )
            )
            .get_attribute("data")
        )

        # close card
        WebDriverWait(driver, 5).until(
            expected_conditions.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[@id='action_div']/div/div[@class='top_band']/table/tbody/tr/td[@class='close_overlay']/span",
                )
            )
        ).click()

cal = Calendar()
cal.add("version", "2.0")
cal.add("prodid", "-//Lboro Timetable//User Timetable//")

months = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
]

months = dict(zip(months, [str(i).zfill(2) for i in range(1, 13)]))

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


for week, events in urls.items():
    for idx, event in enumerate(events):
        driver.get(event)

        try:
            event_details = driver.find_element(By.CLASS_NAME, "event_details")
            details = {
                "name": event_details.find_element(By.TAG_NAME, "div").text
            }

            keys = [
                i.text for i in event_details.find_elements(By.TAG_NAME, "dt")
            ]
            values = [
                i.text for i in event_details.find_elements(By.TAG_NAME, "dd")
            ]
            details.update(dict(zip(keys, values)))

            week_date = re.match(
                r"Sem \d - Wk \d+ \(starting (\d+-\w+-\d+)\)", week
            ).groups()[0]

            for k, v in months.items():
                week_date = week_date.replace(k, v)

            week_date = datetime.strptime(week_date, "%d-%m-%Y")

            day, time = details["Day: Time"].split(": ")
            start_time, end_time = [
                [int(j) for j in i.split(":")] for i in time.split(" - ")
            ]

            start_time = week_date + timedelta(
                days=days.index(day), hours=start_time[0], minutes=start_time[1]
            )

            end_time = week_date + timedelta(
                days=days.index(day), hours=end_time[0], minutes=end_time[1]
            )

            cal_event = Event()
            cal_event.add("summary", details["name"])
            cal_event.add("description", f"Lecturers: {details['Lecturers']}")
            cal_event.add("dtstamp", datetime.now())
            cal_event.add("dtstart", start_time)
            cal_event.add("dtend", end_time)
            cal_event["location"] = vText(details["Rooms"])
            cal_event["uid"] = str(uuid.uuid4())

            cal.add_component(cal_event)

        except NoSuchElementException:
            print(f"Failed to fetch event {idx+1} of '{week}'")

with open("timetable.ics", "wb+") as fp:
    fp.write(cal.to_ical())
