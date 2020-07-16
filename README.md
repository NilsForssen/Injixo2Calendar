# Injixo2Calendar

## About
Script to automatically fetch a schedule from a subdomain h1.me of injixo.com and schedule it as events in Google Calendar. 

No more Tedious logging in to injixo, browsing upcoming shifts and manually creating calendar events for each upcoming shift with correct time, location and lunchbreaks.

The schedule is parsed into Google Calendar events using an OAuth Client ID credentials file in working directory. Script is built in python utilizing the Google Calendar API and compiled to executable with pyinstaller.

## Usage
To use the executable your personal Google Calendar API must be enabled through a personal project in the [Google Developer Console](https://console.developers.google.com/).

1. Open the Google Developer Console found above and navigate to "Dashboard" found in menu to the left.
2. Enable the Google Calendar API: 
Create Project->Create->Enable APIs and Services->"Google Calendar API"->Enable
3. Navigate back to the Project Page and download your Client ID: 
Credentials->Create Credentials->OAuth Client ID->Configure Consent Screen->External->Name and Image->Save->Credentials->Create Credentials->OAuth Client ID->Desktop app->Create
Now you should see a your client in the Client IDs, next to it should be a download symbol where you can download your credentials file.
4. Rename the downloaded file to "credentials" (keep the .json format) and put it in the same working directory as the downloaded Injixo2Calendar executable. 

Now the script will have access to only your Google Calendar events as seen in source-code. 

The script can be executed just by running the file, but can also be automated by running it via command prompt or a task in Windows Task Scheduler and passing the username and passwords as plain arguments.

Injixo2Calendar.exe \[username\] \[password\]

A token.pickle file will be created in the working directory when the script is first run. This file holds your approved permission for access to the Google Calendar. You will be taken to the Google consent screen every time the script is run without this file present in working directory.

## Issues
Here are some common issues you can have running the executable:
* "Failed to execute script Injixo2Calendar" - This is most likely caused by the script not detecting the credentials.json downloaded in the usage section. Follow the steps carefully, once completed, try running the script again, you should be redirected to a Google consent screen in your browser.
* "Login Unsuccesfull" - Login to h1.me.injixo.com failed. Double Check your username and password. Also try logging in to Injixo manually since this issue can also be related to your account being suspended.
* Same shifts are stacking in Google Calendar every time script is run. - This should only be an issue if the events created by the script are manually adjusted somehow. Normally the script searches for every event in your calendar within the time period of upcoming shifts. If the found event's description ends with "H1 Arbetspass" that event is recognized as a shift and is replaced with the same shift directly from Injixo, preventing stacking.

If any issues remain or additional issues are found, contact me either by email or by commenting on this repository.

## Additional Notes
I personally use this with Windows Task Scheduler running once a day and love it, saves me lots of time.

However, as youve probably already noticed the project is not very user-friendly, having the user manually downloading the credentials file and all that. From what I've understood I would need to host this aplication on an authorized domain to be able to submit the application for verification, and only then I could be able to have users redirected to a consent screen for Google Calendar permissions automatically instead of downloading the credentials file. This negates the ability to automate the process locally and i would also need to do some website integration with the application, something I am not very comfortable with. 

May be a future project, but for now I'll stick to this poor but functional solution.

Thanks for downloading!

/Nils Forssén
