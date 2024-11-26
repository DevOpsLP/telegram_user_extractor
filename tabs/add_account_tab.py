import customtkinter as ctk
import threading
import asyncio
import random
import string
import queue
from logic.telegram_client_manager import TelegramClientManager
from logic.database_manager import DatabaseManager
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)


class AddAccountTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager: DatabaseManager, gui_queue):
        super().__init__(parent)
        self.db_manager = db_manager
        self.gui_queue = gui_queue
        self.input_queue = queue.Queue()  # For receiving user input from the main thread

        # Initialize StringVar variables for input fields
        self.api_id_var = ctk.StringVar()
        self.api_hash_var = ctk.StringVar()
        self.phone_number_var = ctk.StringVar()

        # Create GUI Elements
        self.setup_add_account_tab()

    def setup_add_account_tab(self):
        # Instruction Label
        self.label_instruction_add_account = ctk.CTkLabel(
            self,
            text="Enter your Telegram API credentials and phone number to add a new account.",
            justify="center",
            wraplength=400
        )
        self.label_instruction_add_account.pack(pady=(20, 10))

        # API ID Entry
        self.label_api_id = ctk.CTkLabel(self, text="API ID:")
        self.label_api_id.pack(pady=(10, 5))
        self.entry_api_id = ctk.CTkEntry(self, width=300, textvariable=self.api_id_var)
        self.entry_api_id.pack(pady=(0, 10))

        # API Hash Entry
        self.label_api_hash = ctk.CTkLabel(self, text="API Hash:")
        self.label_api_hash.pack(pady=(10, 5))
        self.entry_api_hash = ctk.CTkEntry(self, width=300, textvariable=self.api_hash_var, show="*")
        self.entry_api_hash.pack(pady=(0, 10))

        # Phone Number Entry
        self.label_phone_number = ctk.CTkLabel(self, text="Phone Number (with country code):")
        self.label_phone_number.pack(pady=(10, 5))
        self.entry_phone_number = ctk.CTkEntry(self, width=300, textvariable=self.phone_number_var)
        self.entry_phone_number.pack(pady=(0, 10))

        # Add Account Button
        self.button_add_account = ctk.CTkButton(
            self,
            text="Add New Account",
            command=self.add_new_account
        )
        self.button_add_account.pack(pady=(10, 10))

        # Status Label
        self.label_status_add_account = ctk.CTkLabel(self, text="", text_color="green", wraplength=400)
        self.label_status_add_account.pack(pady=(10, 10))

    def add_new_account(self):
        # Retrieve input values
        api_id = self.api_id_var.get().strip()
        api_hash = self.api_hash_var.get().strip()
        phone_number = self.phone_number_var.get().strip()

        # Input validation
        if not api_id.isdigit():
            self.update_status_add_account("API ID must be a numeric value.", "red")
            return
        if not api_hash:
            self.update_status_add_account("API Hash cannot be empty.", "red")
            return
        if not phone_number:
            self.update_status_add_account("Phone number cannot be empty.", "red")
            return

        # Disable the add account button to prevent multiple clicks
        self.button_add_account.configure(state="disabled")
        self.update_status_add_account("Starting account setup...", "blue")

        # Start the account creation process in a new thread
        threading.Thread(
            target=self.run_add_account,
            args=(int(api_id), api_hash, phone_number),
            daemon=True
        ).start()

    def run_add_account(self, api_id, api_hash, phone_number):
        asyncio.run(self.create_and_store_session(api_id, api_hash, phone_number))

    async def create_and_store_session(self, api_id, api_hash, phone_number):
        try:
            # Initialize TelegramClientManager
            client_manager = TelegramClientManager(api_id, api_hash)
            await client_manager.connect()

            if not await client_manager.is_authorized():
                # Send code request to the phone number
                await client_manager.client.send_code_request(phone_number)

                # Prompt user for the verification code
                self.gui_queue.put(("prompt_input", "Enter the code you received:", False))
                code = self.input_queue.get()  # Wait for the user input

                try:
                    await client_manager.client.sign_in(phone_number, code)
                except SessionPasswordNeededError:
                    # Prompt user for the 2FA password
                    self.gui_queue.put(("prompt_input", "Enter your 2FA password:", True))
                    password = self.input_queue.get()  # Wait for the user input
                    await client_manager.client.sign_in(password=password)
                except PhoneCodeInvalidError:
                    self.gui_queue.put(("status_add_account", "Invalid verification code.", "red"))
                    await client_manager.disconnect()
                    self.gui_queue.put(("enable_add_account_button",))
                    return
                except Exception as e:
                    self.gui_queue.put(("status_add_account", f"Error during sign-in: {e}", "red"))
                    await client_manager.disconnect()
                    self.gui_queue.put(("enable_add_account_button",))
                    return

            # Session is now authorized
            session_string = client_manager.client.session.save()

            # Fetch user information
            user = await client_manager.client.get_me()
            user_id = user.id
            username = user.username or ""

            # If the user doesn't have a username, set a random one
            if not username:
                random_username = self.generate_random_username()
                try:
                    result = await client_manager.client(UpdateUsernameRequest(random_username))
                    if result:
                        username = random_username
                except Exception as e:
                    print(f"Error setting username: {e}")

            # Store the credentials in the database
            self.db_manager.add_credentials(api_id, api_hash, session_string, user_id, username)
            self.gui_queue.put(("status_add_account", "Account added successfully.", "green"))

        except Exception as e:
            print(e)
            self.gui_queue.put(("status_add_account", f"Error: {e}", "red"))
        finally:
            await client_manager.disconnect()
            # Re-enable the add account button
            self.gui_queue.put(("enable_add_account_button",))

    def refresh_tables(self):
        # Fetch updated table names from the database
        updated_tables = self.db.get_table_names()
        updated_tables = [""] + updated_tables  # Add an empty option at the beginning

        # Update existing tables dropdown
        self.dropdown_existing_tables_scrape.configure(values=updated_tables)
        if self.selected_existing_table_scrape.get() not in updated_tables:
            self.selected_existing_table_scrape.set("")  # Reset selection if no longer valid

    async def prompt_user_input(self, prompt_text, hide_input=False):
        """
        Creates a modal dialog to prompt the user for input.

        :param prompt_text: The message to display to the user.
        :param hide_input: Whether to hide the user's input (useful for passwords).
        :return: The user's input as a string.
        """
        # Run the dialog in the main thread's event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.show_input_dialog, prompt_text, hide_input)

    def show_input_dialog(self, prompt_text, hide_input):
        """
        Synchronously creates and shows an input dialog.

        :param prompt_text: The message to display to the user.
        :param hide_input: Whether to hide the user's input.
        :return: The user's input as a string.
        """
        # Create a new top-level window
        input_dialog = ctk.CTkToplevel(self)
        input_dialog.title("Input Required")
        input_dialog.geometry("400x200")
        input_dialog.grab_set()  # Make the dialog modal

        # Instruction Label
        label = ctk.CTkLabel(input_dialog, text=prompt_text, wraplength=380)
        label.pack(pady=(20, 10))

        # Entry Widget
        input_var = ctk.StringVar()
        entry = ctk.CTkEntry(input_dialog, textvariable=input_var, width=300, show="*" if hide_input else "")
        entry.pack(pady=(0, 20))
        entry.focus()

        # Variable to store the user's input
        user_input = {'value': None}

        # Submit Button
        def on_submit():
            user_input['value'] = input_var.get().strip()
            input_dialog.destroy()

        submit_button = ctk.CTkButton(
            input_dialog,
            text="Submit",
            command=on_submit
        )
        submit_button.pack(pady=(0, 10))

        # Wait for the dialog to close
        self.wait_window(input_dialog)

        return user_input['value']

    def update_status_add_account(self, message, color):
        self.label_status_add_account.configure(text=message, text_color=color)

    def generate_random_username(self, length=8):
        """Generate a random username that adheres to Telegram's requirements."""
        # Ensure the username starts and ends with a letter, and is 5-32 characters long
        if length < 5:
            length = 5
        if length > 32:
            length = 32

        start = random.choice(string.ascii_letters)  # Ensure it starts with a letter
        middle = ''.join(random.choices(string.ascii_letters + string.digits + '_', k=length - 2))
        end = random.choice(string.ascii_letters + string.digits)  # Ensure it ends with a letter or digit

        return f"{start}{middle}{end}"
