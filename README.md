Download student timetable from loughborough uni learn website.

## Usage:

```sh
python -m pip install -r requirements.txt
python download.py <semester: 1,2> <learn username> <learn password>
```

This writes `timetable.ics` as output.

This has only been tested with in person events, other event types such as online events might be formatted differently and be unable to be parsed.

If you have any problems drop an issue.
