import customtkinter as ctk
import threading
import asyncio
from logic.telegram_client_manager import TelegramClientManager
from telethon.tl.types import Channel, Chat
from telethon.errors import (
    ChatAdminRequiredError,
    UserPrivacyRestrictedError,

)
from telethon.tl.functions.channels import InviteToChannelRequest


class ScrapeGroupsTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager, gui_queue):
        super().__init__(parent)
        self.db = db_manager
        self.gui_queue = gui_queue

        # Fetch all credentials
        self.credentials = self.db.get_all_credentials()

        # Initialize StringVar variables
        self.selected_account_scrape = ctk.StringVar(value="")
        self.selected_target_group_scrape = ctk.StringVar(value="")
        self.selected_existing_table_scrape = ctk.StringVar(value="")

        # Create GUI Elements
        self.create_widgets()

    def create_widgets(self):
        self.setup_scrape_tab()

    def setup_scrape_tab(self):
        # Select Account Label and Dropdown
        self.label_select_account_scrape = ctk.CTkLabel(self, text="Select Account:")
        self.label_select_account_scrape.pack(pady=(20, 5))

        # Initialize dropdown menu for Scrape Groups tab
        account_options = self.get_account_options()
        self.selected_account_scrape.set("No accounts available" if not account_options else account_options[0])

        self.dropdown_accounts_scrape = ctk.CTkOptionMenu(
            self,
            dynamic_resizing=True,
            values=account_options,
            variable=self.selected_account_scrape
        )
        self.dropdown_accounts_scrape.pack(pady=(0, 20))

        # Refresh Accounts Button
        self.button_refresh_accounts_scrape = ctk.CTkButton(
            self,
            text="Refresh Accounts",
            command=self.refresh_accounts
        )
        self.button_refresh_accounts_scrape.pack(pady=(10, 10))

        # Dropdown for Target Groups
        self.dropdown_target_groups_scrape = ctk.CTkOptionMenu(
            self,
            dynamic_resizing=True,
            values=[],
            variable=self.selected_target_group_scrape
        )
        self.dropdown_target_groups_scrape.pack(pady=(0, 10))

        # Get Groups Button
        self.button_get_groups_scrape = ctk.CTkButton(
            self,
            text="Get Groups",
            command=self.get_groups_scrape
        )
        self.button_get_groups_scrape.pack(pady=(5, 20))

        # Save on Table Label and Entry
        self.label_save_table_scrape = ctk.CTkLabel(self, text="Save on Table:")
        self.label_save_table_scrape.pack(pady=(10, 5))

        self.entry_save_table_scrape = ctk.CTkEntry(self, width=300)
        self.entry_save_table_scrape.pack(pady=(0, 20))


        # Existing Tables Dropdown
        self.label_existing_tables_scrape = ctk.CTkLabel(self, text="Select Existing Table:")
        self.label_existing_tables_scrape.pack(pady=(10, 5))

        existing_tables = self.db.get_table_names()  # Fetch table names from the database
        existing_tables = [""] + existing_tables  # Add an empty option at the beginning

        self.dropdown_existing_tables_scrape = ctk.CTkOptionMenu(
            self,
            dynamic_resizing=True,
            values=existing_tables,
            variable=self.selected_existing_table_scrape,
            command=self.on_table_select_scrape  # Bind a callback on selection
        )
        self.dropdown_existing_tables_scrape.pack(pady=(0, 20))

        # Extract Users Button
        self.button_extract_scrape = ctk.CTkButton(
            self,
            text="Extract Users",
            command=self.start_extraction_scrape
        )
        self.button_extract_scrape.pack(pady=(10, 10))

        # Status Label
        self.label_status_scrape = ctk.CTkLabel(self, text="", text_color="green")
        self.label_status_scrape.pack(pady=(10, 10))

    def get_account_options(self):
        """
        Generate dropdown options for accounts from the credentials list.
        """
        if not self.credentials:
            return ["No accounts available"]
        return [f"ID: {cred[0]} | API_ID: {cred[1]}" for cred in self.credentials]

    def refresh_accounts(self):
        """
        Refresh accounts from the database and update dropdown menus.
        """
        try:
            # Disable the refresh buttons to prevent multiple clicks
            self.button_refresh_accounts_scrape.configure(state="disabled")

            # Update the status to indicate refresh
            self.update_status_scrape("Refreshing accounts...", "blue")

            # Refresh accounts in a new thread
            threading.Thread(target=self.run_refresh_accounts, daemon=True).start()

        except Exception as e:
            self.update_status_scrape(f"Error refreshing accounts: {e}", "red")

    def run_refresh_accounts(self):
        """
        Fetch accounts from the database and update GUI elements.
        """
        try:
            # Fetch credentials from the database
            self.credentials = self.db.get_all_credentials()

            # Update dropdown menus in the main thread
            self.gui_queue.put(("update_dropdowns_scrape",))
            self.gui_queue.put(("status_scrape", "Accounts refreshed successfully.", "green"))
        except Exception as e:
            self.gui_queue.put(("status_scrape", f"Error refreshing accounts: {e}", "red"))
        finally:
            # Re-enable the refresh buttons
            self.gui_queue.put(("enable_refresh_buttons",))

    def update_account_dropdowns(self):
        """
        Update the dropdown menus in the GUI for account selection.
        """
        account_options = self.get_account_options()
        self.dropdown_accounts_scrape.configure(values=account_options)

        if account_options:
            self.selected_account_scrape.set(account_options[0])
        else:
            self.selected_account_scrape.set("No accounts available")

    def update_target_groups_scrape(self, groups):
        """
        Update the target groups dropdown with fetched groups.
        """
        self.dropdown_target_groups_scrape.configure(values=groups)  # Update dropdown options
        if groups:
            self.selected_target_group_scrape.set(groups[0])  # Set default value to the first group
        else:
            self.selected_target_group_scrape.set("")  # Clear selection if no groups

    def update_status_scrape(self, message, color):
        self.label_status_scrape.configure(text=message, text_color=color)

    def get_groups_scrape(self):
        selected_account_text = self.selected_account_scrape.get()
        if "No accounts available" in selected_account_text:
            self.update_status_scrape("No accounts available. Please add an account.", "red")
            return

        try:
            cred_id = int(selected_account_text.split("|")[0].split(":")[1].strip())
        except (IndexError, ValueError):
            self.update_status_scrape("Invalid account selection.", "red")
            return

        # Disable the button to prevent multiple clicks
        # self.button_get_groups_scrape.configure(state="disabled")
        self.update_status_scrape("Fetching groups...", "blue")

        # Start fetching groups in a new thread
        threading.Thread(
            target=self.run_get_groups_scrape,
            args=(cred_id,),
            daemon=True
        ).start()

    def run_get_groups_scrape(self, cred_id):
        asyncio.run(self.fetch_groups_scrape(cred_id))

    async def fetch_groups_scrape(self, cred_id):
        try:
            # Initialize TelegramClientManager with credentials
            cred = self.db.get_credentials_by_id(cred_id)
            if not cred:
                self.gui_queue.put(("status_scrape", "Selected account not found.", "red"))
                self.gui_queue.put(("enable_get_groups_button",))
                return

            api_id, api_hash, session_data = cred
            client_manager = TelegramClientManager(api_id, api_hash, session_data)
            await client_manager.connect()

            if not await client_manager.is_authorized():
                self.gui_queue.put(("status_scrape", "Session is not authorized.", "red"))
                self.gui_queue.put(("enable_get_groups_button",))
                await client_manager.disconnect()
                return

            # Fetch all groups (channels and chats)
            try:
                client = client_manager.get_client()
                dialogs = await client.get_dialogs()
                groups = []
                for dialog in dialogs:
                    if isinstance(dialog.entity, Channel) and dialog.entity.megagroup:
                        group_id = dialog.entity.id
                        # Use getattr to safely access 'username' and skip if None
                        group_name = getattr(dialog.entity, "username", None)
                        if not group_name:  # Skip if username is None or empty
                            continue
                        groups.append(f"{group_id} | {group_name}")
                    elif isinstance(dialog.entity, Chat):
                        group_id = dialog.entity.id
                        group_name = dialog.name
                        groups.append(f"{group_id} | {group_name}")

                if not groups:
                    self.gui_queue.put(("status_scrape", "No groups found for the selected account.", "red"))
                else:
                    self.gui_queue.put(("update_target_groups_scrape", groups))
                    self.gui_queue.put(("status_scrape", f"Fetched {len(groups)} groups.", "green"))

            except Exception as e:
                self.gui_queue.put(("status_scrape", f"Error fetching groups: {e}", "red"))

            await client_manager.disconnect()

        except Exception as e:
            self.gui_queue.put(("status_scrape", f"Unexpected error: {e}", "red"))
        finally:
            self.gui_queue.put(("enable_get_groups_button",))

    def refresh_tables(self):
        # Fetch updated table names from the database
        updated_tables = self.db.get_table_names()
        updated_tables = [""] + updated_tables  # Add an empty option at the beginning

        # Update existing tables dropdown
        self.dropdown_existing_tables_scrape.configure(values=updated_tables)
        if self.selected_existing_table_scrape.get() not in updated_tables:
            self.selected_existing_table_scrape.set("")  # Reset selection if no longer valid

    def on_table_select_scrape(self, selected_table):
        """
        Callback function when a table is selected from the dropdown.
        Overwrites the 'Save on Table' entry with the selected table name.
        If the empty option is selected, clears the 'Save on Table' entry.
        """
        if selected_table:
            self.entry_save_table_scrape.delete(0, ctk.END)  # Clear existing text
            self.entry_save_table_scrape.insert(0, selected_table)  # Insert selected table name
        else:
            self.entry_save_table_scrape.delete(0, ctk.END)  # Clear the entry if no table is selected

    def start_extraction_scrape(self):
        selected_account_text = self.selected_account_scrape.get()
        if "No accounts available" in selected_account_text:
            self.update_status_scrape("No accounts available. Please add an account.", "red")
            return

        try:
            cred_id = int(selected_account_text.split("|")[0].split(":")[1].strip())
        except (IndexError, ValueError):
            self.update_status_scrape("Invalid account selection.", "red")
            return

        selected_group = self.selected_target_group_scrape.get()
        if selected_group:
            group_username = selected_group.split("|")[1].strip()

        save_table = self.entry_save_table_scrape.get().strip()

        if not group_username:
            self.update_status_scrape("Please select the Target Group.", "red")
            return

        if not save_table:
            self.update_status_scrape("Please specify a table to save users.", "red")
            return

        # Validate table name
        if not save_table.isidentifier():
            self.update_status_scrape("Invalid table name. Use only letters, numbers, and underscores.", "red")
            return

        # Disable the button to prevent multiple clicks
        self.button_extract_scrape.configure(state="disabled")
        self.update_status_scrape("Starting extraction...", "blue")

        # Start extraction in a new thread
        threading.Thread(
            target=self.run_extraction_scrape,
            args=(cred_id, group_username, save_table),
            daemon=True
        ).start()

    def run_extraction_scrape(self, cred_id, target_group, save_table):
        asyncio.run(self.extract_users_scrape(cred_id, target_group, save_table))

    async def extract_users_scrape(self, cred_id, target_group, save_table):
        try:
            self.gui_queue.put(("status_scrape", "Connecting to Telegram...", "blue"))

            # Initialize TelegramClientManager with credentials
            cred = self.db.get_credentials_by_id(cred_id)
            if not cred:
                self.gui_queue.put(("status_scrape", "Selected account not found.", "red"))
                self.gui_queue.put(("enable_scrape_button",))
                return

            api_id, api_hash, session_data = cred
            client_manager = TelegramClientManager(api_id, api_hash, session_data)
            await client_manager.connect()

            if not await client_manager.is_authorized():
                self.gui_queue.put(("status_scrape", "Session is not authorized.", "red"))
                self.gui_queue.put(("enable_scrape_button",))
                await client_manager.disconnect()
                return

            # Fetch target group entity by name
            try:
                client = client_manager.get_client()
                group = await client.get_entity(target_group)
            except ValueError:
                self.gui_queue.put(("status_scrape", f"Group '{target_group}' does not exist.", "red"))
                self.gui_queue.put(("enable_scrape_button",))
                await client_manager.disconnect()
                return
            except Exception as e:
                self.gui_queue.put(("status_scrape", f"Error fetching group '{target_group}': {e}", "red"))
                self.gui_queue.put(("enable_scrape_button",))
                await client_manager.disconnect()
                return

            # Check if the entity is a channel or group
            if not isinstance(group, (Channel, Chat)):
                self.gui_queue.put(("status_scrape", f"Entity '{target_group}' is not a group or channel.", "red"))
                self.gui_queue.put(("enable_scrape_button",))
                await client_manager.disconnect()
                return

            # Insert group into the database
            try:
                group_id = group.id
                group_name = group.title or "N/A"
                group_type = "Channel" if isinstance(group, Channel) else "Group"

                self.db.add_group(group_id, group_name, group_type)
                self.gui_queue.put(("status_scrape", f"Processing group: {group_name} (ID: {group_id})", "blue"))
            except Exception as e:
                self.gui_queue.put(("status_scrape", f"Error inserting group into database: {e}", "red"))
                self.gui_queue.put(("enable_scrape_button",))
                await client_manager.disconnect()
                return

            # Fetch and store group users
            try:
                participants = await client.get_participants(group)
                if not participants:
                    self.gui_queue.put(("status_scrape", f"No participants found in group '{group_name}'.", "red"))
                    self.gui_queue.put(("enable_scrape_button",))
                    await client_manager.disconnect()
                    return

                # Counter for successfully saved users
                saved_count = 0
                # Save participants to the specified table
                for user in participants:
                    user_id = user.id
                    username = user.username or "N/A"
                    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

                    # Skip users with username as 'N/A'
                    if username == "N/A":
                        continue

                    self.db.add_user(user_id, username, full_name, group_id, save_table)
                    saved_count += 1
                # After successfully extracting and saving users
                self.gui_queue.put(("update_tables",))
                
                self.gui_queue.put(("status_scrape", f"Successfully extracted and saved {saved_count} users to table '{save_table}'.", "green"))
            except ChatAdminRequiredError:
                self.gui_queue.put(("status_scrape", f"Cannot fetch users for group '{group_name}' (ID: {group_id}): Admin privileges required.", "red"))
            except UserPrivacyRestrictedError:
                self.gui_queue.put(("status_scrape", f"Cannot fetch some users in group '{group_name}' due to privacy settings.", "red"))
            except Exception as e:
                self.gui_queue.put(("status_scrape", f"Error fetching users for group '{group_name}': {e}", "red"))

        except Exception as e:
            self.gui_queue.put(("status_scrape", f"Unexpected error: {e}", "red"))
        finally:
            if 'client_manager' in locals() and client_manager.get_client().is_connected():
                await client_manager.disconnect()
            self.gui_queue.put(("enable_scrape_button",))
