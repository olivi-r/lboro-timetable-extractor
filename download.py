import datetime
import icalendar
import requests
import re
import sys


assert len(sys.argv) in [3, 5], "Usage: <Username> <Password> [<Start Date> <End Date>]"

if len(sys.argv) == 5:
    regex = re.compile(r"\d{4}-\d{2}-\d{2}")
    assert regex.match(sys.argv[3]), "Start Date must be in YYYY-MM-DD format"
    assert regex.match(sys.argv[4]), "End Date must be in YYYY-MM-DD format"
    start = sys.argv[3] + "T00:00:00.000Z"
    end = sys.argv[4] + "T23:59:59.000Z"

else:
    today = datetime.date.today()
    start = today.strftime("%Y-%m-%dT00:00:00.000Z")
    end = datetime.date(today.year, 12, 31).strftime("%Y-%m-%dT23:59:59.999Z")

with requests.Session() as session:
    resp = session.post(
        "https://my.lboro.ac.uk/campusm/sso/ldap/2548",
        data={"username": sys.argv[1], "password": sys.argv[2]},
    )
    assert resp.ok, "Login failed"

    today = datetime.date.today()
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
