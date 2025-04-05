from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from db.database_config import create_connection
import bcrypt

class LoginScreen(Screen):
    def validate_login(self):
        """Validate the email and password against the database."""
        # Access the email and password inputs using their IDs
        email = self.ids.email_input.text
        password = self.ids.password_input.text.encode('utf-8')  # Encode password to bytes

        # Connect to the database
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Fetch the hashed password for the given email
                query = "SELECT password FROM users WHERE email = %s"
                cursor.execute(query, (email,))
                result = cursor.fetchone()

                if result:
                    # Retrieve the hashed password from the database
                    hashed_password = result[0].encode('utf-8')  # Encode hashed password to bytes

                    # Verify the input password against the hashed password
                    if bcrypt.checkpw(password, hashed_password):
                        # Login successful, navigate to the success screen
                        self.manager.current = 'home'
                    else:
                        # Login failed, show error popup
                        self.show_error_popup("Invalid email or password")
                else:
                    # No user found with the given email
                    self.show_error_popup("Invalid email or password")

            except Exception as e:
                print(f"Error: {e}")
                self.show_error_popup(f"Something went wrong: {e}")

            finally:
                conn.close()
        else:
            self.show_error_popup("Failed to connect to the database")

    def show_error_popup(self, message):
        """Display a popup with an error message."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(text=message, color=(1, 0, 0, 1)))

        close_button = Button(text="Close")
        popup = Popup(title="Error", content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup_layout.add_widget(close_button)

        popup.open()