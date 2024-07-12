# ToDo-app
# Advanced ToDo & Second Brain Planner

## Description
This project is an advanced ToDo and Second Brain Planner application built with Streamlit. It offers a comprehensive set of features for task management, note-taking, knowledge organization, and productivity tracking.

## Features

### 1. User Authentication
- User registration and login functionality
- Secure password hashing using bcrypt

### 2. Task Management
- Add, edit, and delete tasks
- Set task priorities (Low, Medium, High)
- Add tags to tasks
- Set due dates for tasks
- Create recurring tasks (Daily, Weekly, Monthly)
- Filter tasks by priority and tags
- View upcoming tasks

### 3. Note Taking
- Create, edit, and delete notes
- Rich text editing using Quill editor
- Add tags to notes
- Attach files to notes
- Filter notes by tags

### 4. Knowledge Graph
- Visualize connections between tasks and notes
- Add internal and external links between items
- Interactive graph visualization using Plotly

### 5. Analytics
- View task completion rate
- Analyze task and note creation over time
- Identify most connected items in the knowledge graph
- Generate a tag cloud for visual representation of frequently used tags

### 6. Pomodoro Timer
- Built-in Pomodoro timer for focused work sessions
- Customizable session duration
- Select tasks to work on during Pomodoro sessions

### 7. Goal Tracking
- Set and track long-term goals
- Assign target dates to goals
- Mark goals as completed

### 8. Calendar View
- Visualize tasks and goals in a calendar format
- Navigate through different months and years
- View task and goal details for selected months

## Technologies Used
- Python
- Streamlit
- SQLite
- Plotly
- NetworkX
- WordCloud
- Streamlit-Quill
- Streamlit-Tags
- Streamlit-Calendar

## Setup and Installation
1. Clone the repository
2. Install required dependencies:

## Usage
1. Register a new account or log in to an existing one
2. Navigate through different sections using the sidebar
3. Add tasks, notes, and goals as needed
4. Use the Pomodoro timer for focused work sessions
5. Explore the knowledge graph to visualize connections
6. Check analytics for insights into your productivity

## Database Schema
The application uses SQLite with the following tables:
- users: Store user information
- tasks: Store task details
- notes: Store note information
- links: Store connections between items
- goals: Store user goals
- subtasks: Store subtasks for main tasks
- note_attachments: Store file attachments for notes

## Contributing
Contributions to improve the application are welcome. Please follow these steps:
1. Fork the repository
2. Create a new branch
3. Make your changes and commit them
4. Create a pull request with a description of your changes

## License
[Specify the license here, e.g., MIT License]

## Contact
[Your contact information or project maintainer's contact]
