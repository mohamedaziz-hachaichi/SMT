from kivy.uix.screenmanager import Screen
from kivy.animation import Animation

class HomeScreen(Screen):
    def toggle_nav_drawer(self):
        """Toggle the side navigation bar."""
        nav_drawer = self.ids.nav_drawer
        if nav_drawer.pos_hint['x'] == -0.3:
            # Open the navigation drawer
            Animation(pos_hint={'x': 0}, duration=0.3).start(nav_drawer)
        else:
            # Close the navigation drawer
            Animation(pos_hint={'x': -0.3}, duration=0.3).start(nav_drawer)

    def navigate_to(self, screen_name):
        """Navigate to the specified screen."""
        self.manager.current = screen_name
        # Close the navigation drawer after navigating
        Animation(pos_hint={'x': -0.3}, duration=0.3).start(self.ids.nav_drawer)

    