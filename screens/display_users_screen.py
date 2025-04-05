# screens/display_users.py
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from db.database_config import create_connection
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # This will log debug messages to the console

class DisplayUsersScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        # Create a ScrollView to display all emails
        scroll_view = ScrollView(size_hint=(1, 1))

        # Create a layout inside the scroll view to add email labels
        email_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        email_layout.bind(minimum_height=email_layout.setter('height'))

        # Fetch and display emails from the database
        emails = self.get_user_emails()
        for email in emails:
            email_label = Label(text=email, size_hint_y=None, height=40)
            email_layout.add_widget(email_label)

        # Add email layout to scroll view
        scroll_view.add_widget(email_layout)

        # Add scroll view to main layout
        layout.add_widget(scroll_view)

        self.add_widget(layout)

    def get_user_emails(self):
        """Fetches emails from the database."""
        emails = []
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = "SELECT email FROM users"  # Get all user emails
                cursor.execute(query)
                result = cursor.fetchall()
                conn.close()

                # Extract email from the result tuple and return it as a list
                emails = [email[0] for email in result]
                logging.debug(f"Fetched {len(emails)} emails from the database.")
            except Exception as e:
                logging.error(f"Error fetching emails from the database: {e}")
                emails = []
        else:
            logging.error("Failed to create database connection.")
        
        return emails
