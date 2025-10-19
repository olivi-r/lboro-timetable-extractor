import datetime
import getpass
import icalendar
import requests
import re
import sys

assert len(sys.argv) in [1, 3], "Usage: [<Start Date> <End Date>]"

if len(sys.argv) == 3:
    regex = re.compile(r"\d{4}-\d{2}-\d{2}")
    assert regex.match(sys.argv[1]), "Start Date must be in YYYY-MM-DD format"
    assert regex.match(sys.argv[2]), "End Date must be in YYYY-MM-DD format"
    start = sys.argv[1] + "T00:00:00.000Z"
    end = sys.argv[2] + "T23:59:59.000Z"

else:
    start = datetime.datetime.combine(
        datetime.datetime.today(), datetime.time()
    ).astimezone().isoformat(timespec="milliseconds").replace("+00:00", "Z")
    end = datetime.datetime.combine(
        datetime.date(datetime.datetime.today().year + 1, 12, 31), datetime.time(23, 59, 59, 999999)
    ).astimezone().isoformat(timespec="milliseconds").replace("+00:00", "Z")

username = input("Username: ")
password = getpass.getpass()

with requests.Session() as session:
    resp = session.post(
        "https://my.lboro.ac.uk/campusm/sso/ldap/2548",
        data={"username": username, "password": password},
    )
    assert resp.ok, "Login failed"

    resp = session.get(
        "https://my.lboro.ac.uk/campusm/sso/cal2/course_timetable",
        params={"start": start, "end": end},
    )
    assert resp.ok, "Failed to get timetable"

    cal = icalendar.Calendar()
    cal.add("version", "2.0")
    cal.add("prodid", "-//Lboro Timetable//User Timetable//")

    # create events
    for event in resp.json()["events"]:
        cal_event = icalendar.Event()

        cal_event.add("summary", event["desc1"])
        cal_event.add("dtstamp", datetime.datetime.now())
        cal_event.add("dtend", datetime.datetime.fromisoformat(event["end"]))

        dtstart = datetime.datetime.fromisoformat(event["start"])
        cal_event.add("dtstart", dtstart)
        cal_event.add("uid", int(dtstart.timestamp()))

        if "teacherName" in event:
            cal_event.add("description", event["teacherName"])

        if "locAdd1" in event:
            cal_event.add("location", event["locAdd1"])

        cal.add_component(cal_event)

    with open("timetable.ics", "wb") as f:
        f.write(cal.to_ical())
