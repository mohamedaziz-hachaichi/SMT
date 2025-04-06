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

        # Calcul du temps total pour déterminer l'unité
        raw_total_time = sum(self.production_times.get(p, 0) for p in self.optimal_path)
        for i in range(len(self.optimal_path) - 1):
            raw_total_time += self.setup_times.get((self.optimal_path[i], self.optimal_path[i + 1]), 0)

        display_in_hours = raw_total_time > 240
        time_unit = "heures" if display_in_hours else "minutes"

        # Fonction de conversion minutes -> heures si nécessaire
        def convert(t):
            return t / 60 if display_in_hours else t

        for idx, product in enumerate(self.optimal_path):
            prod_time = self.production_times.get(product, 0)
            converted_prod_time = convert(prod_time)

            y_labels.append(product)
            tick_vals.append(idx)

            # Ajout de la barre de production
            fig.add_trace(go.Bar(
                x=[converted_prod_time],
                y=[product],
                name=f'Production de {product}',
                orientation='h',
                marker_color='royalblue',
                base=convert(total_time)
            ))

            # Ajout de l'annotation sur la barre de production
            fig.add_annotation(
                x=convert(total_time + (prod_time / 2)),
                y=product,
                text=f"{convert(prod_time):.1f} {'h' if display_in_hours else 'min'}",
                showarrow=False,
                font=dict(size=12, color="white"),
                xanchor="center",
                yanchor="middle"
            )

            projections.append((total_time + prod_time, product))
            total_time += prod_time

            # Ajout du changeover
            if idx < len(self.optimal_path) - 1:
                next_product = self.optimal_path[idx + 1]
                changeover = self.setup_times.get((product, next_product), 0)
                converted_changeover = convert(changeover)

                fig.add_trace(go.Bar(
                    x=[converted_changeover],
                    y=[f'Changeover {idx}'],
                    name=f'Changeover {idx}',
                    orientation='h',
                    marker_color='tomato',
                    base=convert(total_time)
                ))

                projections.append((total_time + changeover, f'Changeover {idx}'))
                total_time += changeover

        # Ajout des lignes de projection
        for end_time, label in projections:
            fig.add_shape(
                type="line",
                x0=convert(end_time),
                y0=-0.5,
                x1=convert(end_time),
                y1=len(self.optimal_path) + 1,
                line=dict(color="black", width=1, dash="dot"),
            )
            fig.add_annotation(
                x=convert(end_time),
                y=-0.5,
                text=f"{convert(end_time):.1f}",
                showarrow=False,
                yshift=-20,
                font=dict(size=10, color="black"),
                xanchor="center",
            )

        # Espacement des ticks dynamiques
        if raw_total_time <= 120:
            dtick = 5
        elif raw_total_time <= 480:
            dtick = 15
        elif raw_total_time <= 1440:
            dtick = 60
        elif raw_total_time <= 2880:
            dtick = 120
        else:
            dtick = 240

        # Mise en page finale
        fig.update_layout(
            title="Séquence de Production Optimale",
            barmode='stack',
            xaxis_title=f"Temps ({time_unit})",
            yaxis_title="Produit / Changeover",
            height=500,
            width=1500,
            plot_bgcolor="white",
            showlegend=True,
            margin=dict(l=100, r=50, t=50, b=80),
            xaxis=dict(tickmode='linear', tick0=0, dtick=convert(dtick)),
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
    prioritized_products = []

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_products())

    def load_products(self):
        products = self._get_products_from_db()
        grid = self.ids.products_container
        grid.clear_widgets()

        for product in products:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)

            lbl = Label(
                text=product,
                size_hint_x=0.6,
                color=(0, 0, 0, 1),
                font_size=18,
                halign='left',
                valign='middle'
            )
            lbl.bind(size=lbl.setter('text_size'))

            cb = CheckBox(size_hint_x=0.2)
            cb.bind(active=lambda instance, value, p=product: self.on_checkbox_active(instance, value, p))

            p_btn = Button(
                text='P',
                size_hint_x=0.2,
                background_color=(1, 0.7, 0.2, 1),
                on_press=lambda instance, p=product: self.toggle_priority(p, instance)
            )

            row.add_widget(lbl)
            row.add_widget(cb)
            row.add_widget(p_btn)
            grid.add_widget(row)

    def toggle_priority(self, product, button):
        if product in self.prioritized_products:
            self.prioritized_products.remove(product)
            button.background_color = (1, 0.7, 0.2, 1)  # orange = désactivé
        else:
            self.prioritized_products.append(product)
            button.background_color = (0, 1, 0, 1)  # vert = prioritaire

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
            goto_btn = Button(
                text="Aller au planning",
                size_hint=(1, None),
                height=50,
                background_color=(0.2, 0.6, 1, 1),
                color=(1, 1, 1, 1),
                font_size=18,
                on_press=self.go_to_scheduling
            )
            self.ids.results_container.add_widget(goto_btn)

            self.create_production_graph(best_path)
        else:
            self._display_message("No valid path found", color=(1, 0, 0, 1))
    def go_to_scheduling(self, instance):
        self.manager.current = 'scheduling'

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

        prioritized = [p for p in self.prioritized_products if p in products]
        best_path = None
        best_time = float('inf')

        for start_product in prioritized or products:
            current_product = start_product
            unvisited = set(products)
            unvisited.remove(current_product)
            path = [current_product]
            total_time = 0
            local_prioritized = prioritized.copy()
            if current_product in local_prioritized:
                local_prioritized.remove(current_product)

            while unvisited:
                candidates = [p for p in unvisited if p in local_prioritized] or list(unvisited)
                next_product = min(
                    candidates,
                    key=lambda p: setup_times.get((current_product, p), float('inf')),
                    default=None
                )
                if not next_product:
                    break
                total_time += setup_times.get((current_product, next_product), 0)
                current_product = next_product
                path.append(current_product)
                unvisited.remove(current_product)
                if current_product in local_prioritized:
                    local_prioritized.remove(current_product)

            print(f"Trying start: {start_product} => Path: {path}, Time: {total_time}")
            if total_time < best_time and len(path) == len(products):
                best_time = total_time
                best_path = path

        print(f"Best path: {best_path}")
        return best_path, best_time if best_path else ([], 0)


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
