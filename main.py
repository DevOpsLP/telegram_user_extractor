import customtkinter as ctk
import queue
from tabs.scrape_groups_tab import ScrapeGroupsTab
from tabs.add_users_tab import AddUsersTab
from tabs.add_account_tab import AddAccountTab
from logic.database_manager import DatabaseManager

class TelegramApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Telegram Manager")
        self.geometry("500x800")  # Adjusted size for better layout
        self.resizable(True, True)

        # Initialize Database Manager
        self.db_manager = DatabaseManager()

        # Fetch all credentials
        self.credentials = self.db_manager.get_all_credentials()

        # Create a queue for thread-safe GUI updates
        self.gui_queue = queue.Queue()

        # Create GUI Elements
        self.create_widgets()

        # Start the GUI queue polling
        self.after(100, self.process_gui_queue)

    def create_widgets(self):
        # Create Tabview
        self.tab_view = ctk.CTkTabview(self, width=800, height=600)
        self.tab_view.pack(expand=True, fill='both', padx=10, pady=10)

        # Add tabs
        self.tab_view.add("Scrape Groups")
        self.tab_view.add("Add Users")
        self.tab_view.add("Add New Account")

        # Scrape Groups Tab
        scrape_tab_frame = self.tab_view.tab("Scrape Groups")
        self.scrape_tab = ScrapeGroupsTab(scrape_tab_frame, self.db_manager, self.gui_queue)
        self.scrape_tab.pack(expand=True, fill='both')

        # Add Users Tab
        add_users_tab_frame = self.tab_view.tab("Add Users")
        self.add_users_tab = AddUsersTab(add_users_tab_frame, self.db_manager, self.gui_queue)
        self.add_users_tab.pack(expand=True, fill='both')

        # Add New Account Tab
        add_account_tab_frame = self.tab_view.tab("Add New Account")
        self.add_account_tab = AddAccountTab(add_account_tab_frame, self.db_manager, self.gui_queue)
        self.add_account_tab.pack(expand=True, fill='both')

    def process_gui_queue(self):
        """
        Process tasks in the GUI queue to update elements safely from other threads.
        """
        try:
            while not self.gui_queue.empty():
                task = self.gui_queue.get_nowait()
                if not task:
                    continue

                if task[0] == "status_scrape":
                    _, message, color = task
                    self.scrape_tab.update_status_scrape(message, color)
                elif task[0] == "status_add":
                    _, message, color = task
                    self.add_users_tab.update_status_add(message, color)
                elif task[0] == "status_add_account":
                    _, message, color = task
                    self.add_account_tab.update_status_add_account(message, color)
                elif task[0] == "enable_add_account_button":
                    self.add_account_tab.button_add_account.configure(state="normal")
                elif task[0] == "enable_refresh_buttons":
                    self.scrape_tab.button_refresh_accounts_scrape.configure(state="normal")
                    self.add_users_tab.button_refresh_accounts_add.configure(state="normal")
                elif task[0] == "update_dropdowns_scrape":
                    self.scrape_tab.update_account_dropdowns()
                elif task[0] == "update_dropdowns_add":
                    self.add_users_tab.update_account_dropdowns()
                elif task[0] == "update_target_groups_scrape":
                    self.scrape_tab.update_target_groups_scrape(task[1])
                elif task[0] == "update_target_groups_add":
                    self.add_users_tab.update_target_groups_add(task[1])
                elif task[0] == "enable_get_groups_button_add":
                    self.add_users_tab.button_get_groups_add.configure(state="normal")
                elif task[0] == "enable_add_users_button":
                    self.add_users_tab.button_add_users.configure(state="normal")
                elif task[0] == "prompt_input":
                    _, prompt_text, hide_input = task
                    # Since we are in the main thread, we can call show_input_dialog directly
                    user_input = self.add_account_tab.show_input_dialog(prompt_text, hide_input)
                    # Send the input back to the background thread
                    self.add_account_tab.input_queue.put(user_input)
                elif task[0] == "refresh_tables":
                    self.scrape_tab.refresh_tables()
                    self.add_users_tab.refresh_tables()
                elif task[0] == "update_tables":
                    # Update table names in the GUI
                    self.scrape_tab.refresh_tables()
                    self.add_users_tab.refresh_source_tables()
                # Add more task handlers as needed
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_gui_queue)

    def on_closing(self):
        self.db_manager.close()
        self.destroy()

if __name__ == "__main__":
    app = TelegramApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
