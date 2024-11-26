from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)
import sys

class TelegramClientManager:
    def __init__(self, api_id, api_hash, session_data=None):
        """
        Initialize the TelegramClientManager with API credentials and optional session data.
        
        :param api_id: Your Telegram API ID.
        :param api_hash: Your Telegram API Hash.
        :param session_data: Optional session string for existing sessions.
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_data = session_data
        self.client = TelegramClient(
            StringSession(session_data) if session_data else StringSession(),
            api_id,
            api_hash
        )

    async def connect(self):
        """
        Connect to the Telegram client.
        """
        await self.client.connect()

    async def disconnect(self):
        """
        Disconnect from the Telegram client.
        """
        await self.client.disconnect()

    async def is_authorized(self):
        """
        Check if the client is authorized.
        
        :return: True if authorized, False otherwise.
        """
        return await self.client.is_user_authorized()

    async def create_session(self):
        """
        Create a new session by authenticating the user via phone number and code.
        
        :return: The session string upon successful authentication.
        """
        await self.connect()
        if not await self.is_authorized():
            try:
                phone = input("Enter your phone number (with country code): ").strip()
                await self.client.send_code_request(phone)
                code = input("Enter the code you received: ").strip()
                try:
                    await self.client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = input("Enter your 2FA password: ").strip()
                    await self.client.sign_in(password=password)
            except PhoneNumberInvalidError:
                print("Invalid phone number.")
                await self.disconnect()
                sys.exit(1)
            except PhoneCodeInvalidError:
                print("Invalid code.")
                await self.disconnect()
                sys.exit(1)
            except Exception as e:
                print(f"Error during sign-in: {e}")
                await self.disconnect()
                sys.exit(1)

        print("Session created successfully.")
        session_string = self.client.session.save()
        await self.disconnect()
        return session_string

    def get_client(self):
        """
        Retrieve the Telegram client instance.
        
        :return: The TelegramClient instance.
        """
        return self.client

    async def create_session_interactive(self, phone_number, prompt_callback):
        """
        Handles interactive session creation within the application.
        
        :param phone_number: The user's phone number with country code.
        :param prompt_callback: A callable that takes a prompt message and a boolean indicating if input should be hidden.
        :return: The session string upon successful authentication.
        """
        try:
            await self.client.send_code_request(phone_number)
            code = await prompt_callback("Enter the code you received:", hide_input=False)
            try:
                await self.client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                password = await prompt_callback("Enter your 2FA password:", hide_input=True)
                await self.client.sign_in(password=password)
        except PhoneNumberInvalidError:
            raise Exception("Invalid phone number.")
        except PhoneCodeInvalidError:
            raise Exception("Invalid code.")
        except Exception as e:
            raise Exception(f"Error during sign-in: {e}")

        print("Session created successfully.")
        return self.client.session.save()