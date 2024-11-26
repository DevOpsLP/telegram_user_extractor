# Telegram User Extractor Setup Guide

## Overview
The Telegram Manager is a desktop application designed to manage Telegram accounts, scrape group data, and add users to Telegram channels or groups. The user interface is built with `customtkinter`, which is a modern and customizable UI framework based on Tkinter, and it leverages Telethon for Telegram API interactions. The application includes tabs for managing different tasks, like scraping groups, adding users, and adding new accounts, while ensuring a seamless experience using a threaded architecture for smooth UI updates.

## Prerequisites
- Python 3.12 is required to run this project. Please ensure it is installed on your system.

## Installation Steps
1. **Clone the repository**
   ```bash
   git clone github.com/devopslp/telegram_user_extractor
   cd telegram_user_extractor
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**
   Install the dependencies listed in the `requirements.txt` file. We will create this file now.

   Create a `requirements.txt` file and add the following dependencies:
   ```
   customtkinter==5.1.3  # For modern Tkinter GUI components
   telethon==1.30.0      # For Telegram API integration
   sqlite3               # Database for storing account credentials and group information
   asyncio               # For asynchronous programming
   queue                 # Thread-safe queue for handling GUI tasks
   ```

   Then run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

## Features
- **Scrape Groups**: Extract information from Telegram groups and save it to a local SQLite database.
- **Add Users**: Add users to Telegram channels or groups using the saved data.
- **Add New Account**: Add new Telegram accounts for managing multiple Telegram sessions.

## Technical Details
The project is divided into several modules to handle different parts of the application:
- **Main Application (`main.py`)**: Handles the user interface and general flow of the application.
- **Tabs**: The application has multiple tabs to manage the different functionalities: scraping groups, adding users, and managing accounts.
- **Logic Layer (`logic/`)**: Handles the communication with the Telegram API using Telethon and manages the SQLite database.
- **Database Manager (`database_manager.py`)**: A module for managing the SQLite database that stores credentials and scraped group data.

## Notes
- Ensure that you have valid Telegram credentials (API ID, API Hash) for each account you want to use.
- Be mindful of Telegram's rate limits to avoid getting accounts temporarily blocked.
- If you encounter "FloodWaitError", it means you need to wait for some time before retrying the same action.

## Next Steps
For a detailed description of each feature, visit the [Wiki](#) section. We will continue to document every aspect of this project as we proceed, including individual components and their usage.

