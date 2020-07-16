import requests
from bs4 import BeautifulSoup
import googleCalendar
import datetime
import sys
import os
import locale
import pkg_resources.py2_warn


"""
Python Script for adding h1.injixo shifts to Google Calendar. (should work for other injixo domains aswell?)

credentials.json from Google API project is to be located in working directory.

A token.pickle file will be created in Working Directory.
Deleting this file will result in you having to approve
access to Google Calendar.

Script can be executed:
-> Manually by running executable(.py) and using GUI
-> Automatically by CMD passing fogis credentials as arguments
e.g script.exe(.py) myUser myPass

The latter can be used with Windows task scheduler to schedule calendar updates.

Author: Nils Forssén, Jämtland County, Sweden
"""

# Make sure the datetime %p works like AM/PM
locale.setlocale(locale.LC_ALL, "en_US")

# Global event-details
LOCATION = "H1 Communication AB"


class Shift():
    """
    Node to store shift-details such as date, start and ending times and the shift summary
    Shift can be merged with other shifts and converted to Google Calendar event format
    """

    def __init__(self, date, startTime, endTime, summary):
        """
        Initialize shitf with shift-date, starttime, endtime and summary 
        """

        self.summary = summary
        self.start = datetime.datetime.strptime(
            date + startTime, "%B %d, %Y%I:%M %p")
        self.end = datetime.datetime.strptime(
            date + endTime, "%B %d, %Y%I:%M %p")
        self.length = self.end - self.start

        self.description = "Ingen lunchrast!"

    def mergeShift(self, shift):
        """
        Merge shift with other shift, changing the ending time and adding a lunchbreak in event description
        """

        self.end = shift.end

        if shift.summary == "Lunch":
            self.description = str(int(
                shift.length.seconds / 60)) + " minuter lunchrast!"

    def getEvent(self):
        """
        Get a the shift in a Google Calendar event format
        """

        event = {
            "summary": "H1 " + self.summary,
            "location": LOCATION,
            # The H1 tag "classifies" event as a shift
            "description": self.description + "\n\nH1 Communication arbetspass",
            "start": {
                "dateTime": "{0}T{1}+02:00".format(self.start.date(), self.start.time())
            },
            "end": {
                "dateTime": "{0}T{1}+02:00".format(self.end.date(), self.end.time())
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {
                        "method": "popup",
                        "minutes": 720          # 12 hours
                    }
                ]
            },
            "colorId": googleCalendar.EVENT_COLORIDS["yellow"]

        }
        return event


def resource_path(relative_path):
    """
    Get pyinstaller resource
    """

    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)

    return os.path.join(os.path.abspath("."), relative_path)


def getDataPage(uName, pWord):
    """
    Login to fogis and return the datapage.
    If not accessible, return None.
    """

    with requests.Session() as session:

        # Data to post to loginPage
        payload = {
            "username": uName,
            "password": pWord,
            "locale": "en",
            "commit": "Login"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"
        }

        # Log in page
        loginPage = session.get("https://h1.me.injixo.com/login")

        # Soup the necesary login information from the login website
        soup = BeautifulSoup(loginPage.text, features="lxml")

        # The crsf-token was renamed with a crsf-param
        token = soup.select_one("meta[name='csrf-token']")["content"]
        tokenName = soup.select_one("meta[name='csrf-param']")["content"]
        payload[tokenName] = token

        # Post with the login credentials and additional required information in payload
        session.post("https://h1.me.injixo.com/login",
                     data=payload, headers=headers)

        # Agenda is located on the dashboard
        dataPage = session.get("https://h1.me.injixo.com/dashboard")

        if b"injixo Me | Login" in dataPage.content:

            # Login unsuccessfull, access to dataPage url was not granted.
            # e.g. username or password incorrect, account locked/banned etc.
            return None

        else:

            # Login successfull
            return dataPage


def updateCalendar(page):
    """
    Update the calendar with games from given dataPage
    """

    dashboard = BeautifulSoup(page.content, features="lxml")

    # Only search in the agenda portion of the dashboard
    agenda = dashboard.find("div", class_="pane__body agenda-spacer")

    # List to store the all the shift of the next 7 days
    shiftList = []

    # Find all the list-items of the agenda, these may store the date, time or title of the shift
    for item in agenda.find_all("div", class_="list-item"):

        # If the list-item is a header including the current date, the date or none of those
        # In the latter case, the list-item is not a header and instead includes shift details
        # - Stupid HTML class-generalization on the website but that is what I have to work with...
        date = item.find(
            "span", class_="current-day") or item.find("span", class_="") or date

        shiftName = item.find("span", class_="agenda_event_title")

        # If there is something planned (not nothing) and that something is me being "unavailable"
        if shiftName is not None:

            # Both start and end times in 12-hour clock, %I:%M %p - %I:%M %p
            shiftTime = item.find("div", class_="list-item__action")

            # Create a shift node, this stores the details of every shift and can be parsed into events
            newShift = Shift(date.text.strip(), shiftTime.text.strip()[
                             :8], shiftTime.text.strip()[-8:], shiftName.text.strip())

            # If there is a shift on the same day connected to the previous shift, merge them into one event, otherwise create two separate events
            if "Kan Ej" not in newShift.summary:

                try:
                    pastShift = shiftList[-1]
                except IndexError:
                    shiftList.append(newShift)
                else:

                    # If the same day and theres less than 1 hour between the shifts merge them, else just add the new shift as a separate shift
                    # If the newShift is a lunchbreak or shift after lunch they will all be merged as one long shift
                    if pastShift.start.date() == newShift.start.date() and newShift.start - pastShift.end < datetime.timedelta(minutes=60):
                        pastShift.mergeShift(newShift)
                    else:
                        shiftList.append(newShift)
    if shiftList:
        comingEvents = googleCalendar.listEvents(timeMin=shiftList[0].getEvent(
        )["start"]["dateTime"], timeMax=shiftList[-1].getEvent()["end"]["dateTime"])

        for comingEvent in comingEvents:

            try:
                lastLine = comingEvent["description"].splitlines()[-1]

                if "H1 Communication arbetspass" in lastLine:

                    # The event is "classified" as a previously uploaded shift and should thus be updated
                    # All currently active shifts will be readded later
                    # This shift could have e.g. been canceled recently, thus it needs updating

                    googleCalendar.deleteEvent(comingEvent["id"])

            except KeyError:

                # An event without a description was found, this is not a game created by this script
                pass

    for shift in shiftList:

        # Create a Google Calendar event for each parsed shift
        googleCalendar.createEvent(shift.getEvent())
        print("Event created! {0}".format(shift.start))


if __name__ == "__main__":

    if len(sys.argv) < 2:

        # No arguments passed, launch GUI prompt for username and password

        import tkinter as tk

        root = tk.Tk()

        # Make the Entrys expand to fill empty space
        root.grid_columnconfigure(1, weight=1)

        # Window icon
        root.iconbitmap(resource_path("logo.ico"))
        root.title("Injixio2Calendar")

        # GUI elements
        header = tk.Label(
            text="Enter your injixo credentials", font='Helvetica 16')
        uNameLabel = tk.Label(text="Username:", font="Helvetica 10")
        uNameEntry = tk.Entry()
        pWordLabel = tk.Label(text="Password:", font="Helvetica 10")
        pWordEntry = tk.Entry()

        promptString = tk.StringVar()
        promptString.set("")
        promptLabel = tk.Label(textvariable=promptString, font="Helvetica 10")

        def btnUpdateCalendar():
            """
            Comprehensive update calendar function linked to button in GUI 
            """

            page = getDataPage(uNameEntry.get(), pWordEntry.get())

            if page is not None:

                promptString.set("Updated!")
                promptLabel.config(fg="green2")
                updateCalendar(page)

                # "Updated!"

            else:

                promptString.set("Login unsuccesful!")
                promptLabel.config(fg="red2")

        btn = tk.Button(text="Update Calendar", font="Helvetica 10 bold",
                        command=btnUpdateCalendar, bg="green2", activebackground="green2")

        # Grid GUI elements
        header.grid(columnspan=2, row=0, column=0, sticky="NSEW")
        uNameLabel.grid(row=1, sticky="W")
        uNameEntry.grid(row=1, column=1, sticky="EW")
        pWordLabel.grid(row=2, sticky="W")
        pWordEntry.grid(row=2, column=1, sticky="EW")
        promptLabel.grid(columnspan=2, row=3, sticky="NSEW")
        btn.grid(columnspan=2, row=4)

        root.mainloop()

    else:

        # username and password arguments passed, don't launch GUI

        try:
            username = sys.argv[1]
            password = sys.argv[2]
        except IndexError:
            print("Both username and password must be passed as arguments")
            sys.exit()

        page = getDataPage(username, password)

        if page is not None:
            updateCalendar(page)
        else:
            print("Login unsuccessfull")
