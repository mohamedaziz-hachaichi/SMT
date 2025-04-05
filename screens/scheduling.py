from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class SchedulingScreen(Screen):
    total_production_time = NumericProperty(0)
    remaining_time = NumericProperty(0)
    schedule = ListProperty([[False for _ in range(3)] for _ in range(7)])
    optimal_path = ObjectProperty([])
    setup_times = ObjectProperty({})
    production_times = ObjectProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.initialize_data, 0.1)
    def on_kv_post(self, *args):
        self.create_schedule_layout()

    def initialize_data(self, dt):
        if self.optimal_path and self.setup_times and self.production_times:
            from screens.find_shortest_path import get_total_production_time
            self.total_production_time = get_total_production_time(
                self.optimal_path, 
                self.setup_times, 
                self.production_times
            )
            self.remaining_time = self.total_production_time
            self.create_schedule_layout()

    def create_schedule_layout(self):
        grid = self.ids.schedule_grid
        grid.clear_widgets()
        
        # Entêtes avec hauteur fixe
        headers = ["Day", "Shift A", "Shift B", "Shift C"]
        for header in headers:
            lbl = Label(
                text=header, 
                bold=True,
                size_hint_y=None,
                height=40  # Hauteur fixe
            )
            grid.add_widget(lbl)

        # Jours et cases avec dimensions contrôlées
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day_idx, day in enumerate(days):
            # Libellé du jour
            lbl = Label(
                text=day,
                size_hint_y=None,
                height=40  # Hauteur identique aux entêtes
            )
            grid.add_widget(lbl)
            
            # Cases pour chaque shift
            for shift_idx in range(3):
                btn = Button(
                    text="✓" if self.schedule[day_idx][shift_idx] else "",
                    background_color=(0, 0.7, 0, 1) if self.schedule[day_idx][shift_idx] else (0.7, 0, 0, 1),
                    size_hint=(None, None),
                    size=(100, 40)  # Largeur fixe + hauteur
                )
                btn.bind(on_press=lambda instance, x=day_idx, y=shift_idx: self.update_schedule(x, y, instance))
                grid.add_widget(btn)
    def update_schedule(self, day, shift, instance):
        self.schedule[day][shift] = not self.schedule[day][shift]
        instance.text = "✓" if self.schedule[day][shift] else ""
        instance.background_color = (0, 0.7, 0, 1) if self.schedule[day][shift] else (0.7, 0, 0, 1)
        self.calculate_remaining_time()

    def calculate_remaining_time(self):
        total_shifts = sum(sum(row) for row in self.schedule)
        self.remaining_time = max(0, self.total_production_time - (total_shifts * 450))
        self.ids.remaining_label.text = f"Remaining Time: {self.remaining_time} min\nTotal Production Time: {self.total_production_time} min"