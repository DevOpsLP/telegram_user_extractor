import customtkinter as ctk
import threading
import asyncio
from logic.telegram_client_manager import TelegramClientManager
from logic.database_manager import DatabaseManager
from telethon.errors import (
    FloodWaitError,
    UserPrivacyRestrictedError,
    UserNotMutualContactError,
    UserChannelsTooMuchError,
    UserKickedError,
    UserBannedInChannelError,
    InputUserDeactivatedError,
    UserDeactivatedError,
    PeerFloodError,
    ChatWriteForbiddenError,
    RPCError,
)
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl import types
import sqlite3
from telethon.tl.types import Channel
import time

class AddUsersTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager: DatabaseManager, gui_queue):
        super().__init__(parent)
        self.db = db_manager
        self.gui_queue = gui_queue

        # Initialize StringVar variables
        self.selected_account_add = ctk.StringVar(value="")
        self.selected_source_table_add = ctk.StringVar(value="")
        self.selected_target_group_add = ctk.StringVar(value="")

        # Fetch all credentials
        self.credentials = self.db.get_all_credentials()

        # Create GUI Elements
        self.create_widgets()

    def create_widgets(self):
        self.setup_add_users_tab()

    ##########################
    # Add Users Tab Setup    #
    ##########################

    def setup_add_users_tab(self):
        # Select Account Label and Dropdown
        self.label_select_account_add = ctk.CTkLabel(self, text="Select Account:")
        self.label_select_account_add.pack(pady=(20, 5))

        # Initialize dropdown menu for Add Users tab
        account_options = self.get_account_options()
        if account_options:
            self.selected_account_add.set(account_options[0])  # Set default value
        else:
            self.selected_account_add.set("No accounts available")

        self.dropdown_accounts_add = ctk.CTkOptionMenu(
            self,
            dynamic_resizing=True,
            values=account_options,
            variable=self.selected_account_add
        )
        self.dropdown_accounts_add.pack(pady=(0, 20))

        # Refresh Accounts Button
        self.button_refresh_accounts_add = ctk.CTkButton(
            self,
            text="Refresh Accounts",
            command=self.refresh_accounts
        )
        self.button_refresh_accounts_add.pack(pady=(10, 10))

        # Source Tables Dropdown
        self.label_select_source_table_add = ctk.CTkLabel(self, text="Select Source Table:")
        self.label_select_source_table_add.pack(pady=(10, 5))

        # Fetch initial table names
        self.source_tables = self.db.get_table_names()  # Fetch table names from the database
        self.source_tables = [""] + self.source_tables  # Add an empty option at the beginning

        self.selected_source_table_add = ctk.StringVar(value="")  # Initialize StringVar

        self.dropdown_source_tables_add = ctk.CTkOptionMenu(
            self,
            dynamic_resizing=True,
            values=self.source_tables,
            variable=self.selected_source_table_add,
            command=self.on_source_table_select_add  # Bind a callback on selection
        )
        self.dropdown_source_tables_add.pack(pady=(0, 10))

        # Refresh Tables Button
        self.button_refresh_source_tables = ctk.CTkButton(
            self,
            text="Refresh Tables",
            command=self.refresh_source_tables
        )
        self.button_refresh_source_tables.pack(pady=(5, 20))

        # Select Target Group Dropdown
        self.label_select_target_group_add = ctk.CTkLabel(self, text="Select Target Group:")
        self.label_select_target_group_add.pack(pady=(20, 0))

        self.selected_target_group_add = ctk.StringVar(value="")  # Initialize StringVar

        self.dropdown_target_groups_add = ctk.CTkOptionMenu(
            self,
            dynamic_resizing=True,
            values=[],  # Initially empty; will be populated after clicking "Get Groups"
            variable=self.selected_target_group_add
        )
        self.dropdown_target_groups_add.pack(pady=(0, 20))

        # Get Groups Button
        self.button_get_groups_add = ctk.CTkButton(
            self,
            text="Get Groups",
            command=self.get_groups_add
        )
        self.button_get_groups_add.pack(pady=(5, 20))

        # **New Inputs: Duration and Message (Placed Above Other Elements)**
        
        # Pause Duration Input
        self.label_duration = ctk.CTkLabel(self, text="Pause Duration (minutes):")
        self.label_duration.pack(pady=(10, 5), anchor='center')  # Center the label

        self.entry_duration = ctk.CTkEntry(
            self,
            width=200,
            placeholder_text="60"
        )
        self.entry_duration.insert(0, "60")  # Set default value to 60 minutes
        self.entry_duration.pack(pady=(0, 20))

        # Not Found Message Input
        self.label_message = ctk.CTkLabel(self, text="Not Found Message:")
        self.label_message.pack(pady=(10, 5), anchor='center')  # Center the label

        self.entry_message = ctk.CTkEntry(
            self,
            width=400,
            placeholder_text="Hey!"
        )
        self.entry_message.insert(0, "Hey!")  # Set default message
        self.entry_message.pack(pady=(0, 20), padx=20)

        # Add Users Button
        self.button_add_users = ctk.CTkButton(
            self,
            text="Add Users",
            command=self.start_add_users,
        )
        self.button_add_users.pack(pady=(20, 20))

        # Status Label
        self.label_status_add = ctk.CTkLabel(self, text="", text_color="green")
        self.label_status_add.pack(pady=(10, 10))

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
            self.button_refresh_accounts_add.configure(state="disabled")

            # Update the status to indicate refresh
            self.update_status_add("Refreshing accounts...", "blue")

            # Refresh accounts in a new thread
            threading.Thread(target=self.run_refresh_accounts, daemon=True).start()

        except Exception as e:
            self.update_status_add(f"Error refreshing accounts: {e}", "red")

    def run_refresh_accounts(self):
        """
        Fetch accounts from the database and update GUI elements.
        """
        try:
            # Fetch credentials from the database
            self.credentials = self.db.get_all_credentials()

            # Update dropdown menus in the main thread
            self.gui_queue.put(("update_dropdowns_add",))
            self.gui_queue.put(("status_add", "Accounts refreshed successfully.", "green"))
        except Exception as e:
            self.gui_queue.put(("status_add", f"Error refreshing accounts: {e}", "red"))
        finally:
            # Re-enable the refresh buttons
            self.gui_queue.put(("enable_refresh_buttons",))

    def update_account_dropdowns(self):
        """
        Update the dropdown menus in the GUI for account selection.
        """
        account_options = self.get_account_options()
        self.dropdown_accounts_add.configure(values=account_options)

        if account_options:
            self.selected_account_add.set(account_options[0])
        else:
            self.selected_account_add.set("No accounts available")

    def refresh_source_tables(self):
        try:
            # Fetch updated table names from the database
            updated_tables = self.db.get_table_names()
            updated_tables = [""] + updated_tables  # Add an empty option at the beginning

            # Update source tables dropdown in the add_users_tab
            self.dropdown_source_tables_add.configure(values=updated_tables)
            if self.selected_source_table_add.get() not in updated_tables:
                self.selected_source_table_add.set("")  # Reset selection if no longer valid

            # Notify user
            self.update_status_add("Tables updated successfully.", "green")
        except Exception as e:
            # Handle any errors that occur during refresh
            self.update_status_add(f"Failed to refresh tables: {e}", "red")

    def get_groups_add(self):
        selected_account_text = self.selected_account_add.get()
        if "No accounts available" in selected_account_text:
            self.update_status_add("No accounts available. Please add an account.", "red")
            return

        try:
            cred_id = int(selected_account_text.split("|")[0].split(":")[1].strip())
        except (IndexError, ValueError):
            self.update_status_add("Invalid account selection.", "red")
            return

        # Disable the button to prevent multiple clicks
        self.button_get_groups_add.configure(state="disabled")
        self.update_status_add("Fetching groups...", "blue")

        # Start fetching groups in a new thread
        threading.Thread(
            target=self.run_get_groups_add,
            args=(cred_id,),
            daemon=True
        ).start()

    def run_get_groups_add(self, cred_id):
        asyncio.run(self.fetch_groups_add(cred_id))

    async def fetch_groups_add(self, cred_id):
        try:
            # Initialize TelegramClientManager with credentials
            cred = self.db.get_credentials_by_id(cred_id)
            if not cred:
                self.gui_queue.put(("status_add", "Selected account not found.", "red"))
                self.gui_queue.put(("enable_get_groups_button_add",))
                return

            api_id, api_hash, session_data = cred[0], cred[1], cred[2]
            client_manager = TelegramClientManager(api_id, api_hash, session_data)
            await client_manager.connect()
            if not await client_manager.is_authorized():
                self.gui_queue.put(("status_add", "Session is not authorized.", "red"))
                self.gui_queue.put(("enable_get_groups_button_add",))
                await client_manager.disconnect()
                return

            # Fetch all groups (channels and chats)
            try:
                client = client_manager.get_client()
                dialogs = await client.get_dialogs()
                groups = []
                for dialog in dialogs:
                    if isinstance(dialog.entity, types.Channel):
                        group_id = dialog.entity.id
                        group_name = dialog.name
                        groups.append(f"{group_id} | {group_name}")
                    elif isinstance(dialog.entity, types.Chat):
                        group_id = dialog.entity.id
                        group_name = dialog.name
                        groups.append(f"{group_id} | {group_name}")

                if not groups:
                    self.gui_queue.put(("status_add", "No groups found for the selected account.", "red"))
                else:
                    self.gui_queue.put(("update_target_groups_add", groups))
                    self.gui_queue.put(("status_add", f"Fetched {len(groups)} groups.", "green"))

            except Exception as e:
                self.gui_queue.put(("status_add", f"Error fetching groups: {e}", "red"))

            await client_manager.disconnect()

        except Exception as e:
            self.gui_queue.put(("status_add", f"Unexpected error: {e}", "red"))
        finally:
            self.gui_queue.put(("enable_get_groups_button_add",))

    def update_target_groups_add(self, groups):
        """
        Update the 'Select Target Group' dropdown with the fetched groups.

        Parameters:
            groups (List[str]): A list of group identifiers and names.
        """
        self.dropdown_target_groups_add.configure(values=groups)
        if groups:
            self.selected_target_group_add.set(groups[0])
        else:
            self.selected_target_group_add.set("")

    def on_source_table_select_add(self, selected_table):
        """
        Callback function when a source table is selected from the dropdown.
        Currently, no additional actions are required.
        """
        # You can add any additional actions here if needed
        pass

    def start_add_users(self):
        selected_account_text = self.selected_account_add.get()
        if "No accounts available" in selected_account_text:
            self.update_status_add("No accounts available. Please add an account.", "red")
            return

        try:
            cred_id = int(selected_account_text.split("|")[0].split(":")[1].strip())
        except (IndexError, ValueError):
            self.update_status_add("Invalid account selection.", "red")
            return

        source_table = self.selected_source_table_add.get().strip()
        target_group = self.selected_target_group_add.get().strip()

        if not source_table or not target_group:
            self.update_status_add("Please select a source table and target group.", "red")
            return

        # Validate table name
        if not source_table.isidentifier():
            self.update_status_add("Invalid source table name. Use only letters, numbers, and underscores.", "red")
            return

        # Parse target_group to extract group_id
        if "|" in target_group:
            try:
                group_name = target_group.split("|")[1].strip()
            except ValueError:
                self.update_status_add("Invalid Target Group selected.", "red")
                return
        else:
            self.update_status_add("Invalid Target Group format.", "red")
            return

        # Disable the button to prevent multiple clicks
        self.button_add_users.configure(state="disabled")
        self.update_status_add("Starting to add users...", "blue")

        # Start adding users in a new thread
        threading.Thread(
            target=self.run_add_users,
            args=(cred_id, group_name, source_table),
            daemon=True
        ).start()

    def run_add_users(self, cred_id, group_name, source_table):
        asyncio.run(self.add_users(cred_id, group_name, source_table))

    async def add_users(self, cred_id, group_name, source_table):
        try:
            pause_duration = self.entry_duration.get().strip()
            message = self.entry_message.get().strip()
            print(f"Pause duration: {pause_duration}")
            
            # Input Validation
            try:
                if not pause_duration:  # Check if the sanitized input is empty
                    raise ValueError("Pause duration must contain numeric characters.")
                
                pause_duration = int(pause_duration)  # Convert to integer
                if pause_duration <= 0:
                    raise ValueError("Pause duration must be a positive integer.")

                if not message:  # Ensure message is not empty
                    raise ValueError("Message cannot be empty.")

            except ValueError as e:
                self.gui_queue.put(("status_add", f"Invalid input: {e}", "red"))
                return
            
            self.gui_queue.put(("status_add", "Connecting to Telegram...", "blue"))
            print(f"DEBUG: Starting add_users for Group: {group_name}, Source table {source_table}")

            # Fetch all users from the source table
            try:
                print(f"DEBUG: Fetching users from source_table={source_table}")
                users = self.db.get_users_from_table(source_table)
                print(f"DEBUG: Fetched {len(users)} users")
            except sqlite3.OperationalError as e:
                print(f"ERROR: Source table does not exist: {e}")
                self.gui_queue.put(("status_add", "Source table does not exist.", "red"))
                self.gui_queue.put(("enable_add_users_button",))
                return

            if not users:
                print("DEBUG: No users found in the source table")
                self.gui_queue.put(("status_add", "No users found in the source table.", "red"))
                self.gui_queue.put(("enable_add_users_button",))
                return

            # Fetch all credentials
            print("DEBUG: Fetching credentials from database")
            all_credentials = self.credentials  # Already fetched in __init__
            print(f"DEBUG: Fetched {len(all_credentials)} credentials")
            if not all_credentials:
                print("DEBUG: No credentials available")
                self.gui_queue.put(("status_add", "No accounts available for adding users.", "red"))
                self.gui_queue.put(("enable_add_users_button",))
                return

            self.gui_queue.put(("status_add", "Adding users in batches...", "blue"))

            # Initialize indices and total users
            cred_index = 0
            current_user_index = 0
            total_users = len(users)
            num_credentials = len(all_credentials)
            cycle_count = 0  

            while current_user_index < total_users:
                cred = all_credentials[cred_index % num_credentials]
                print(f"DEBUG: Processing credential index {cred_index % num_credentials}: {cred}")

                if len(cred) < 6:
                    print(f"WARNING: Incomplete credential: {cred}")
                    self.gui_queue.put(("status_add", f"Credential ID {cred[0]} is incomplete. Skipping.", "red"))
                    cred_index += 1
                    # Check if a full cycle has been completed
                    if cred_index % num_credentials == 0 and cred_index != 0:
                        cycle_count += 1
                        print(f"DEBUG: Completed {cycle_count} full cycle(s) of admins. Waiting for {pause_duration} minutes before next cycle.")
                        self.gui_queue.put(("status_add", f"Waiting for {pause_duration} minutes before next cycle of admins.", "yellow"))
                        await asyncio.sleep(pause_duration * 60)  # Convert minutes to seconds
                    continue

                cred_id_account, api_id_account, api_hash_account, session_data_account, user_id, username = cred

                # Initialize the Telegram client for the current admin
                print(f"DEBUG: Initializing Telegram client for credential ID={cred_id_account}")
                client_manager = TelegramClientManager(api_id_account, api_hash_account, session_data_account)
                await client_manager.connect()
                client_account = client_manager.get_client()

                if not await client_manager.is_authorized():
                    print(f"ERROR: Credential ID '{cred_id_account}' not authorized")
                    self.gui_queue.put(("status_add", f"Account ID '{cred_id_account}' is not authorized. Skipping.", "red"))
                    await client_manager.disconnect()
                    cred_index += 1
                    # Check for full cycle
                    if cred_index % num_credentials == 0 and cred_index != 0:
                        cycle_count += 1
                        print(f"DEBUG: Completed {cycle_count} full cycle(s) of admins. Waiting for {pause_duration} minutes before next cycle.")
                        self.gui_queue.put(("status_add", f"Waiting for {pause_duration} minutes before next cycle of admins.", "yellow"))
                        await asyncio.sleep(pause_duration * 60)  # 60 minutes
                    continue

                # Resolve the target group
                group_id = await self.get_group_id(client_account, group_name)
                print(f"DEBUG: Resolving target group_id={group_id}")
                target_entity = await self.resolve_target_group(client_account, group_id)

                print(f"DEBUG: Resolved target_entity={target_entity}")
                if not target_entity:
                    print("ERROR: Failed to resolve target group")
                    self.gui_queue.put(("status_add", "Failed to resolve target group. Aborting.", "red"))
                    await client_manager.disconnect()
                    self.gui_queue.put(("enable_add_users_button",))
                    return

                # Determine the next admin index (circular)
                next_cred_index = (cred_index + 1) % num_credentials
                next_cred = all_credentials[next_cred_index]
                next_username = next_cred[5]
                next_cred_id = next_cred[0]

                # Add and promote the next admin
                try:
                    print(f"DEBUG: Adding admin ID {next_cred_id} ({next_username}) to group using current admin")
                    # Get user entity of next admin
                    user_entity = await client_account.get_input_entity(next_username)
                    # Invite next admin to the group
                    await client_account(InviteToChannelRequest(
                        channel=target_entity,
                        users=[user_entity]
                    ))

                    await client_account.edit_admin(
                        entity=target_entity,
                        user=user_entity,
                        change_info=True,
                        post_messages=True,
                        edit_messages=True,
                        delete_messages=True,
                        ban_users=True,
                        invite_users=True,
                        pin_messages=True,
                        add_admins=True,
                        manage_call=True,
                        anonymous=False,
                        is_admin=True,  # Grant admin privileges
                        title='admin'    # Set the rank or title for the admin
                    )
                    print(f"INFO: Added and promoted admin ID {next_cred_id} ({next_username})")
                    self.gui_queue.put(("status_add", f"Added and promoted admin '{next_username}' (ID: {next_cred_id})", "green"))
                except Exception as e:
                    print(f"ERROR: Failed to add and promote admin '{next_username}': {e}")
                    self.gui_queue.put(("status_add", f"Failed to add and promote admin '{next_username}': {e}", "red"))
                    # Optionally handle the error or decide to continue

                # Now, use current admin to add users
                batch_size = 4
                users_added = 0
                while current_user_index < total_users and users_added < batch_size:
                    user = users[current_user_index]
                    print(f"DEBUG: Processing user={user}")
                    _, username_user, _ = user[0], user[1], user[2]

                    try:
                        # Invite the user to the group using client_account
                        user_entity = await client_account.get_input_entity(username_user)
                        print(f"DEBUG: Resolved user_entity for '{username_user}': {user_entity}")

                        await client_account(InviteToChannelRequest(
                            channel=target_entity,
                            users=[user_entity]
                        ))
                        found = False
                        await asyncio.sleep(3)  # Replace time.sleep(3) with asyncio.sleep
                        async for participant in client_account.iter_participants(entity=target_entity, search=username_user):
                            found = True
                            print(f"User ID: {participant.id}, Username: {participant.username}, Name: {participant.first_name} {participant.last_name}")

                        # If no user is found, send a message to the username
                        if not found:
                            print(f"No user found matching '{username_user}'. Sending a message...")
                            # await client_account.send_message(username_user, message)
                            print(f"Message sent to {username_user}")

                        print(f"INFO: Added user={username_user} with account ID={cred_id_account}")
                        self.gui_queue.put(("status_add", f"Added user '{username_user}' using account ID '{cred_id_account}'.", "green"))
                        await asyncio.sleep(10)  # Replace time.sleep(10) with asyncio.sleep
                        users_added += 1
                        current_user_index += 1
                    except FloodWaitError as e:
                        print(f"ERROR: Flood wait error for account ID '{cred_id_account}': {e}")
                        self.gui_queue.put(("status_add", f"Flood wait of {e.seconds} seconds for account ID '{cred_id_account}'. Switching account.", "red"))
                        await client_manager.disconnect()
                        cred_index += 1
                        # Check for full cycle
                        if cred_index % num_credentials == 0 and cred_index != 0:
                            cycle_count += 1
                        break  # Switch to the next credential
                    except UserPrivacyRestrictedError:
                        print(f"ERROR: Cannot add user '{username_user}': Privacy settings restricted.")
                        self.gui_queue.put(("status_add", f"Cannot add user '{username_user}': Privacy settings restricted.", "red"))
                        current_user_index += 1
                        continue
                    except UserNotMutualContactError:
                        print(f"ERROR: Cannot add user '{username_user}': Not a mutual contact.")
                        self.gui_queue.put(("status_add", f"Cannot add user '{username_user}': Not a mutual contact.", "red"))
                        current_user_index += 1
                        continue
                    except UserChannelsTooMuchError:
                        print(f"ERROR: Cannot add user '{username_user}': User is in too many channels.")
                        self.gui_queue.put(("status_add", f"Cannot add user '{username_user}': User is in too many channels.", "red"))
                        # Delete user from the database
                        self.db.delete_user_from_table(source_table, username_user)
                        current_user_index += 1
                        continue
                    except (UserKickedError, UserBannedInChannelError):
                        print(f"ERROR: Cannot add user '{username_user}': User is banned or kicked from the channel.")
                        self.gui_queue.put(("status_add", f"Cannot add user '{username_user}': User is banned or kicked from the channel.", "red"))
                        current_user_index += 1
                        continue
                    except (InputUserDeactivatedError, UserDeactivatedError):
                        print(f"ERROR: Cannot add user '{username_user}': User account is deactivated.")
                        self.gui_queue.put(("status_add", f"Cannot add user '{username_user}': User account is deactivated.", "red"))
                        current_user_index += 1
                        continue
                    except PeerFloodError:
                        print(f"ERROR: Peer flood error with account ID '{cred_id_account}'. Switching account.")
                        self.gui_queue.put(("status_add", f"Peer flood error with account ID '{cred_id_account}'. Switching account.", "red"))
                        await client_manager.disconnect()
                        cred_index += 1
                        # Check for full cycle
                        if cred_index % num_credentials == 0 and cred_index != 0:
                            cycle_count += 1
                            print(f"DEBUG: Completed {cycle_count} full cycle(s) of admins. Waiting for {pause_duration} minutes before next cycle.")
                            self.gui_queue.put(("status_add", f"Waiting for {pause_duration} minutes before next cycle of admins.", "yellow"))
                            await asyncio.sleep(pause_duration * 60)  # Convert minutes to seconds
                        break  # Switch to the next credential
                    except ChatWriteForbiddenError:
                        print(f"ERROR: Cannot write to chat (maybe need admin rights).")
                        self.gui_queue.put(("status_add", f"Cannot write to chat (maybe need admin rights).", "red"))
                        await client_manager.disconnect()
                        cred_index += 1
                        # Check for full cycle
                        if cred_index % num_credentials == 0 and cred_index != 0:
                            cycle_count += 1
                            print(f"DEBUG: Completed {cycle_count} full cycle(s) of admins. Waiting for {pause_duration} minutes before next cycle.")
                            self.gui_queue.put(("status_add", f"Waiting for {pause_duration} minutes before next cycle of admins.", "yellow"))
                            await asyncio.sleep(pause_duration * 60)  # Convert minutes to seconds
                        break  # Switch to the next credential
                    except RPCError as e:
                        print(f"ERROR: RPC error for user '{username_user}': {e}")
                        self.gui_queue.put(("status_add", f"RPC error for user '{username_user}': {e}", "red"))
                        current_user_index += 1
                        continue
                    except Exception as e:
                        print(f"ERROR: Failed to add user='{username_user}' with exception={e}")
                        self.gui_queue.put(("status_add", f"Failed to add user '{username_user}': {e}", "red"))
                        current_user_index += 1
                        continue

                await client_manager.disconnect()
                print(f"DEBUG: Finished with account ID '{cred_id_account}'. Moving to next credential.")
                cred_index += 1

                # Check if a full cycle has been completed
                if cred_index % num_credentials == 0 and cred_index != 0:
                    cycle_count += 1
                    print(f"DEBUG: Completed {cycle_count} full cycle(s) of admins. Waiting for {pause_duration} minutes before next cycle.")
                    self.gui_queue.put(("status_add", f"Waiting for {pause_duration} minutes before next cycle of admins.", "yellow"))
                    await asyncio.sleep(pause_duration * 60)  # Convert minutes to seconds

        except Exception as e:
            print(f"FATAL ERROR: {e}")
            self.gui_queue.put(("status_add", f"Error: {e}", "red"))
        finally:
            self.gui_queue.put(("enable_add_users_button",))

    async def get_group_id(self, client, channel_name):
            try:
                dialogs = await client.get_dialogs()
                for dialog in dialogs:
                    if isinstance(dialog.entity, Channel) and dialog.name == channel_name:
                        return dialog.entity.id
            except Exception as e:
                print(f"Failed to get group ID: {e}")
                    
                
    # Helper function to resolve the target group as a class method
    async def resolve_target_group(self, client, target_group_id):
        try:
            # Fetch all dialogs to match the group ID or username
            dialogs = await client.get_dialogs()
            for dialog in dialogs:
                entity = dialog.entity
                if isinstance(entity, types.Channel):
                    if str(entity.id) == str(target_group_id) or (hasattr(entity, 'username') and entity.username == target_group_id):
                        print(f"Resolved target group: {dialog.name} (ID: {entity.id})")
                        return types.InputPeerChannel(channel_id=entity.id, access_hash=entity.access_hash)
                elif isinstance(entity, types.Chat):
                    if str(entity.id) == str(target_group_id) or dialog.name == target_group_id:
                        print(f"Resolved target chat: {dialog.name} (ID: {entity.id})")
                        return types.InputPeerChat(chat_id=entity.id)
            raise ValueError("Target group not found in dialogs")
        except Exception as e:
            print(f"Failed to resolve target group: {e}")
            return None

    def update_status_add(self, message, color):
        self.label_status_add.configure(text=message, text_color=color)
