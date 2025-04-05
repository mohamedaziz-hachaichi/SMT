from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from models.product import Product
from kivy.clock import Clock

class AddProductScreen(Screen):
    def on_enter(self):
        """Load products when screen appears"""
        Clock.schedule_once(lambda dt: self._refresh_products())
    
    def toggle_add_form(self):
        """Toggle visibility of add product form"""
        form = self.ids.add_form_container
        if form.height == 0:
            # Opening form
            Animation(height=250, opacity=1, duration=0.3).start(form)
            Clock.schedule_once(lambda dt: self._scroll_to_bottom())
        else:
            # Closing form (cancel action)
            Animation(height=0, opacity=0, duration=0.3).start(form)
            # Clear fields
            self.ids.name_input.text = ""
            self.ids.cycle_input.text = ""
            self.ids.ligne_spinner.text = "Select Production Line"

    def _scroll_to_bottom(self):
        """Scroll to bottom of the page"""
        scroll_view = self.ids.main_scroll
        scroll_view.scroll_y = 0

    def _refresh_products(self):
        """Refresh product list display"""
        products = Product.get_products_by_ligne()
        container = self.ids.products_container
        container.clear_widgets()
        
        if not products:
            container.add_widget(
                self._create_label("No products found", color=(0.5, 0.5, 0.5, 1)))
            return
            
        for ligne, items in products.items():
            container.add_widget(
                self._create_label(f"{ligne}:", bold=True))
            
            for product in items:
                container.add_widget(
                    self._create_label(f"  • {product['name']} (CT: {product['cycle_time']}s)"))

    def _create_label(self, text, bold=False, color=(0, 0, 0, 1)):
        """Helper to create consistent labels"""
        from kivy.uix.label import Label
        return Label(
            text=text,
            size_hint_y=None,
            height=30,
            bold=bold,
            color=color
        )

    def add_product(self):
        """Handle new product addition"""
        name = self.ids.name_input.text.strip()
        cycle = self.ids.cycle_input.text.strip()
        ligne = self.ids.ligne_spinner.text
        
        if not all([name, cycle, ligne != 'Select Ligne']):
            return
            
        try:
            if Product.add_product(name, int(cycle), ligne):
                self.ids.name_input.text = ""
                self.ids.cycle_input.text = ""
                self._refresh_products()
                self.toggle_add_form()  # Hide form after successful addition
        except ValueError:
            pass

    def go_back(self):
        self.manager.current = 'home'