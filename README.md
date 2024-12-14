# Whatsaver Project

## Introduction
**Whatsaver** is a comprehensive, web-based application tailored for efficient patient data management. Built with Flask, it provides robust tools for monitoring patient status, handling user authentication, and managing audit trails.

## Features
- **User Authentication:** Secure login and logout.
- **Data Tracking:** Real-time tracking of patient statuses and clinic operations.
- **Audit Trails:** Automated logging of user actions.
- **Medication Safety Errors** Tracking the current status of error resolution, whether pending, in progress, or resolved, to monitor the effectiveness of interventions.

## Medication Safety Errors
This percentage calculation helps practitioners grasp the ratio of unresolved medication errors to the total recorded errors in the medication safety database. Having a list of all medication safety errors in a database. Some are resolved, but others are pending. The percentage indicates how many pending issues exist relative to the total. For instance, if there are 30 unresolved issues out of 100 recorded, the percentage is 30%. This insight guides in monitoring and addressing medication safety, prioritizing patient well-being. If there are no recorded issues, the percentage is 0%.

## Technologies Used
- **Python**
- **Flask**
- **SQLite**
- **HTML/CSS** (Templates)
- **Bootstrap** (Templates)

## Getting Started
To get a local copy up and running follow these simple steps:
1. **Navigate to the project directory:** `cd path/to/whatsaver`
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Run the application:** `python main.py`

## Usage
Access the web application via `localhost:8081` after starting the server. Use the web interface to manage patients and view audit logs.

## Contributing
Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
Distributed under the MIT License. See `LICENSE` for more information.