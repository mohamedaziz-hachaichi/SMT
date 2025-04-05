from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.core.image import Image as CoreImage
from io import BytesIO
import plotly.graph_objects as go
from kivy.clock import Clock
from db.database_config import create_connection
from mysql.connector import Error
import logging
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock


class ProductionGraph(BoxLayout):
    def __init__(self, optimal_path, setup_times, production_times, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.optimal_path = optimal_path
        self.setup_times = setup_times
        self.production_times = production_times
        self.draw_graph()
        Clock.schedule_once(lambda dt: self.draw_graph())

    def draw_graph(self):
        total_time = 0
        fig = go.Figure()
        y_labels = []
        tick_vals = []
        projections = []

        for idx, product in enumerate(self.optimal_path):
            prod_time = self.production_times.get(product, 0)
            y_labels.append(product)
            tick_vals.append(idx)

            # Ajout de la barre de production
            fig.add_trace(go.Bar(
                x=[prod_time],
                y=[product],
                name=f'Production de {product}',
                orientation='h',
                marker_color='royalblue',
                base=total_time
            ))

            # Ajout du temps de production SUR la barre bleue
            fig.add_annotation(
                x=total_time + (prod_time / 2),  # Position au centre du bâton
                y=product,
                text=f"{prod_time:.1f} min",  # Texte avec le temps
                showarrow=False,
                font=dict(size=12, color="white"),  # Texte blanc pour contraster avec le bleu
                xanchor="center",
                yanchor="middle"
            )

            projections.append((total_time + prod_time, product))
            total_time += prod_time

            # Ajout du changeover
            if idx < len(self.optimal_path) - 1:
                next_product = self.optimal_path[idx + 1]
                changeover = self.setup_times.get((product, next_product), 0)

                fig.add_trace(go.Bar(
                    x=[changeover],
                    y=[f'Changeover {idx}'],
                    name=f'Changeover {idx}',
                    orientation='h',
                    marker_color='tomato',
                    base=total_time
                ))

                projections.append((total_time + changeover, f'Changeover {idx}'))
                total_time += changeover

        # Ajout des projections de fin
        for end_time, label in projections:
            fig.add_shape(
                type="line",
                x0=end_time,
                y0=-0.5,
                x1=end_time,
                y1=len(self.optimal_path) + 1,
                line=dict(color="black", width=1, dash="dot"),
            )
            fig.add_annotation(
                x=end_time,
                y=-0.5,
                text=f"{end_time:.1f}",
                showarrow=False,
                yshift=-20,
                font=dict(size=10, color="black"),
                xanchor="center",
            )

        # Mise en page du graphe
        fig.update_layout(
            title="Séquence de Production Optimale",
            barmode='stack',
            xaxis_title="Temps (minutes)",
            yaxis_title="Produit / Changeover",
            height=500,
            width=1500,
            plot_bgcolor="white",
            showlegend=True,
            margin=dict(l=100, r=50, t=50, b=80),
            xaxis=dict(tickmode='linear', tick0=0, dtick=5),
        )

        # Affichage dans Kivy
        self.clear_widgets()
        img_bytes = fig.to_image(format='png')
        core_image = CoreImage(BytesIO(img_bytes), ext='png')

        scroll_view = ScrollView(size_hint=(1, None), height=core_image.height)
        img_widget = Widget(size_hint=(None, None), size=(core_image.width, core_image.height))

        with img_widget.canvas:
            Color(1, 1, 1, 1)
            img_widget.rect = Rectangle(texture=core_image.texture, size=img_widget.size, pos=img_widget.pos)

        scroll_view.add_widget(img_widget)
        self.add_widget(scroll_view)



class FindPathScreen(Screen):
    selected_products = []

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_products())

    def load_products(self):
        products = self._get_products_from_db()
        grid = self.ids.products_container
        grid.clear_widgets()

        for product in products:
            lbl = Label(
                text=product,
                size_hint_x=0.8,
                color=(0, 0, 0, 1),
                font_size=18,
                halign='left',
                valign='middle'
            )
            lbl.bind(size=lbl.setter('text_size'))

            cb = CheckBox(
                size_hint_x=0.2,
                color=(0.2, 0.5, 0.8, 1)
            )
            cb.bind(active=lambda instance, value, p=product: self.on_checkbox_active(instance, value, p))

            grid.add_widget(lbl)
            grid.add_widget(cb)

    def on_checkbox_active(self, instance, value, product):
        if value:
            if product not in self.selected_products:
                self.selected_products.append(product)
        else:
            if product in self.selected_products:
                self.selected_products.remove(product)

    def _get_products_from_db(self):
        conn = create_connection()
        products = []
        if conn is None:
            return products

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT from_product FROM change_over
                UNION
                SELECT DISTINCT to_product FROM change_over
            """)
            raw_products = [row[0].replace("er ", "") for row in cursor.fetchall()]
            products = list(set(raw_products))
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Database error: {e}")

        return products

    def calculate_optimal_path(self):
        if len(self.selected_products) < 2:
            self._display_message("Select at least two products", color=(1, 0, 0, 1))
            return

        setup_times = self._get_setup_times_from_db()
        filtered_setup_times = {
            key: value for key, value in setup_times.items()
            if key[0] in self.selected_products and key[1] in self.selected_products
        }

        if not filtered_setup_times:
            self._display_message("No setup data found", color=(1, 0, 0, 1))
            return

        best_path, best_time = self._nearest_neighbor_path(filtered_setup_times)
        self.ids.results_container.clear_widgets()

        if best_path:
            path_label = Label(
                text=f"[b]Optimal Path:[/b] {' → '.join(best_path)}",
                markup=True,
                font_size=20,
                color=(0, 0, 0, 1))
            time_label = Label(
                text=f"[b]Total Changeover Time:[/b] {best_time} minutes",
                markup=True,
                font_size=18,
                color=(0, 0, 0, 1))
            

            self.ids.results_container.add_widget(path_label)
            self.ids.results_container.add_widget(time_label)
            self.create_production_graph(best_path)
            self.manager.current = 'scheduling'
        else:
            self._display_message("No valid path found", color=(1, 0, 0, 1))

    def create_production_graph(self, best_path):
        conn = create_connection()
        production_times = {}
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name, quantity, panel, cycle_time FROM products")
                for row in cursor.fetchall():
                    product_name, quantity, panel, cycle_time = row
                    try:
                        qty = int(quantity) if quantity not in [None, "NULL"] else 0
                        pnl = int(panel) if panel not in [None, "NULL"] else 1
                        cyc = float(cycle_time)
                        production_time = (qty / pnl) * (cyc/60) if pnl != 0 else 0
                        production_times[product_name] = int(production_time)
                    except (ValueError, TypeError):
                        print(f"Invalid data for {product_name}")
                cursor.close()
                conn.close()
            except Error as e:
                print(f"Production time error: {e}")

        setup_times = {}
        for i in range(len(best_path)-1):
            from_p = best_path[i]
            to_p = best_path[i+1]
            setup_times[(from_p, to_p)] = self._get_setup_times_from_db().get((from_p, to_p), 0)

        self.manager.get_screen('scheduling').optimal_path = best_path
        self.manager.get_screen('scheduling').setup_times = setup_times
        self.manager.get_screen('scheduling').production_times = production_times
        self.ids.graph_container.clear_widgets()
        graph = ProductionGraph(best_path, setup_times, production_times)
        graph.size_hint = (1, 1)
        self.ids.graph_container.add_widget(graph)
        self.manager.get_screen('scheduling').initialize_data(0)

    def _display_message(self, message, color):
        self.ids.results_container.clear_widgets()
        self.ids.results_container.add_widget(Label(text=message, color=color, font_size=18))

    def _get_setup_times_from_db(self):
        setup_times = {}
        conn = create_connection()
        if conn is None:
            return setup_times

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT from_product, to_product, change_time FROM change_over")
            for from_product, to_product, change_time in cursor.fetchall():
                clean_from = from_product.replace("er ", "")
                clean_to = to_product.replace("er ", "")
                setup_times[(clean_from, clean_to)] = int(change_time)
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Database error: {e}")

        return setup_times

    def _nearest_neighbor_path(self, setup_times):
        products = list({key[0] for key in setup_times.keys()})
        if not products:
            return [], 0

        best_path = None
        best_time = float('inf')

        for start_product in products:
            current_product = start_product
            unvisited = set(products)
            unvisited.remove(current_product)
            path = [current_product]
            total_time = 0

            while unvisited:
                next_product = min(
                    unvisited,
                    key=lambda p: setup_times.get((current_product, p), float('inf')))
                total_time += setup_times.get((current_product, next_product), 0)
                current_product = next_product
                path.append(current_product)
                unvisited.remove(current_product)

            if total_time < best_time:
                best_time = total_time
                best_path = path

        return best_path, best_time
   

    def go_back(self):
        self.manager.current = 'home'

def get_total_production_time(optimal_path, setup_times, production_times):
    total_time = 0
    for idx, product in enumerate(optimal_path):
        # Calcul du temps de production pour chaque produit
        production_time = production_times.get(product, 0)
        total_time += production_time
        
        # Ajout du temps de changeover pour chaque transition entre produits
        if idx < len(optimal_path) - 1:
            next_product = optimal_path[idx + 1]
            changeover_time = setup_times.get((product, next_product), 0)
            total_time += changeover_time

    return total_time
