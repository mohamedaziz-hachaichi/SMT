from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from screens.login_screen import LoginScreen
from screens.success_screen import SuccessScreen
from screens.Home_screen import HomeScreen
from screens.add_product_screen import AddProductScreen
from screens.find_shortest_path import FindPathScreen
from screens.scheduling import SchedulingScreen
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle



# Load the .kv file manually
Builder.load_file('interface.kv')

class SMTApp(App):
    def build(self):
        # Create a ScreenManager to handle multiple screens
        sm = ScreenManager()

        # Set the background color of the ScreenManager to white
        with sm.canvas.before:
            Color(1, 1, 1, 1)  # White color (R, G, B, A)
            self.rect = Rectangle(size=sm.size, pos=sm.pos)
        
        sm.bind(size=self._update_rect, pos=self._update_rect)

        # Add the LoginScreen and SuccessScreen to the ScreenManager
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(SuccessScreen(name='success'))
        sm.add_widget(AddProductScreen(name='add_product'))
        sm.add_widget(FindPathScreen(name='find_shortest_path'))  
        sm.add_widget(SchedulingScreen(name='scheduling')) 

        return sm

    def _update_rect(self, instance, value):
        # Update the size and position of the rectangle when the window is resized
        self.rect.size = instance.size
        self.rect.pos = instance.pos

if __name__ == '__main__':
    SMTApp().run()
