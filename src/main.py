import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import calculations

class HullApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Otoczka Wypukła - Algorytm Grahama")
        self.root.geometry("1100x750")
        # self.root.resizable(False, False)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Stylizacja
        self.style = ttk.Style()
        self.style.theme_use('clam')
        bg_color = "#f0f0f0"
        self.root.configure(bg=bg_color)
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabelframe", background=bg_color, font=("Segoe UI", 9, "bold"))
        self.style.configure("TLabelframe.Label", background=bg_color)
        
        # Dane
        self.points = []        
        self.hull_points = []   
        self.bbox = None        

        # Konfiguracja wykresu
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor('#f0f0f0')

        # --- ZMIENNE KONFIGURACYJNE ---
        # 1. Punkty
        self.pt_color = "#0000FF"
        self.pt_size = tk.DoubleVar(value=20.0)
        self.pt_shape = tk.StringVar(value="Okrąg")
        self.pt_show_labels = tk.BooleanVar(value=True)

        # 2. Otoczka
        self.hull_color = "#808080"
        self.hull_width = tk.DoubleVar(value=2.0)
        self.hull_style = tk.StringVar(value="Ciągła")
        self.hull_visible = tk.BooleanVar(value=True)

        # 3. Prostokąt (BBox)
        self.bbox_color = "#000000"
        self.bbox_width = tk.DoubleVar(value=1.0)
        self.bbox_style = tk.StringVar(value="Przerywana")
        self.bbox_visible = tk.BooleanVar(value=True)

        # Budowa interfejsu
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_panel = ttk.Frame(self.main_frame, width=350)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._init_left_panel()
        self._init_right_panel()

    def _init_left_panel(self):
        # 1. WCZYTYWANIE I LISTA PUNKTÓW
        # Używamy expand=True, ale ograniczymy wysokość tabeli, żeby nie wypychała reszty
        frame_data = ttk.LabelFrame(self.left_panel, text="Wykaz punktów", padding=5)
        frame_data.pack(fill=tk.BOTH, expand=True, pady=(0, 5)) 

        btn_load = ttk.Button(frame_data, text="Wczytaj wykaz punktów", command=self.load_points)
        btn_load.pack(fill=tk.X, pady=(0, 5))

        # --- KONTENER NA TABELĘ I SCROLLBAR ---
        # Dzięki temu tabela i pasek są w jednym pudełku, a przyciski będą pod nimi
        list_container = ttk.Frame(frame_data)
        list_container.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "X", "Y")
        # Zmniejszamy height do 5-6 wierszy, żeby zaoszczędzić miejsce w pionie dla reszty interfejsu
        self.tree = ttk.Treeview(list_container, columns=cols, show='headings', height=5)
        self.tree.heading("ID", text="Nr")
        self.tree.heading("X", text="X")
        self.tree.heading("Y", text="Y")
        self.tree.column("ID", width=30)
        self.tree.column("X", width=60)
        self.tree.column("Y", width=60)
        
        scroll = ttk.Scrollbar(list_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- PRZYCISKI USUWANIA (POD TABELĄ) ---
        frame_del = ttk.Frame(frame_data)
        frame_del.pack(fill=tk.X, pady=(5, 0))
        
        frame_del.columnconfigure(0, weight=1)
        frame_del.columnconfigure(1, weight=1)

        ttk.Button(frame_del, text="Usuń wybrane", command=self.delete_selected_point)\
            .grid(row=0, column=0, sticky="ew", padx=(0, 2))
            
        ttk.Button(frame_del, text="Wyczyść wszystko", command=self.delete_all_points)\
            .grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # --- STATYSTYKI ---
        self.lbl_stats = ttk.Label(self.left_panel, text="Liczba punktów: 0", font=("Segoe UI", 8))
        self.lbl_stats.pack(anchor="w", pady=(0, 5))

        # 2. RĘCZNE DODAWANIE
        frame_manual = ttk.LabelFrame(self.left_panel, text="Sprawdzenie pojedynczego punktu", padding=5)
        frame_manual.pack(fill=tk.X, pady=(0, 5))

        row_in = ttk.Frame(frame_manual)
        row_in.pack(fill=tk.X)
        
        # Rejestracja funkcji walidującej w systemie Tkinter
        vcmd = (self.root.register(self.validate_float_input), '%P')

        ttk.Label(row_in, text="X:").pack(side=tk.LEFT)
        # Dodano validate i validatecommand
        self.entry_x = ttk.Entry(row_in, width=6, validate="key", validatecommand=vcmd)
        self.entry_x.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row_in, text="Y:").pack(side=tk.LEFT)
        # Dodano validate i validatecommand
        self.entry_y = ttk.Entry(row_in, width=6, validate="key", validatecommand=vcmd)
        self.entry_y.pack(side=tk.LEFT, padx=5)

        ttk.Button(row_in, text="Dodaj punkt", command=self.add_manual_point).pack(side=tk.RIGHT)

        # 3. AKCJE OTOCZKI
        frame_actions = ttk.LabelFrame(self.left_panel, text="Budowanie otoczki wypukłej", padding=5)
        frame_actions.pack(fill=tk.X, pady=(0, 5))

        row_act = ttk.Frame(frame_actions)
        row_act.pack(fill=tk.X)
        
        btn_build = ttk.Button(row_act, text="Zbuduj otoczkę", command=self.build_hull)
        btn_build.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        btn_save = ttk.Button(row_act, text="Zapisz otoczkę", command=self.save_hull)
        btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # 4. PARAMETRY RYSUNKU
        frame_params = ttk.LabelFrame(self.left_panel, text="Parametry rysunku", padding=5)
        frame_params.pack(fill=tk.X, pady=(0, 5))

        # A. Punkty
        p_frame = ttk.LabelFrame(frame_params, text="Wykaz punktów", padding=2)
        p_frame.pack(fill=tk.X, pady=2)
        
        row_p = ttk.Frame(p_frame)
        row_p.pack(fill=tk.X)
        self.btn_col_pt = tk.Button(row_p, text=" ", bg=self.pt_color, width=3, command=lambda: self.pick_color('pt_color', self.btn_col_pt))
        self.btn_col_pt.pack(side=tk.LEFT)
        ttk.Label(row_p, text="Wielkość").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(row_p, from_=1, to=100, textvariable=self.pt_size, width=4, command=self.draw_plot).pack(side=tk.LEFT)
        
        shapes = ["Okrąg", "Kwadrat", "Trójkąt", "X"]
        cb_shape = ttk.Combobox(row_p, values=shapes, textvariable=self.pt_shape, state="readonly", width=8)
        cb_shape.pack(side=tk.LEFT, padx=5)
        cb_shape.bind("<<ComboboxSelected>>", lambda e: self.draw_plot())
        
        ttk.Checkbutton(p_frame, text="Widoczność numerów punktów", variable=self.pt_show_labels, command=self.draw_plot).pack(anchor='w')

        # B. Otoczka
        h_frame = ttk.LabelFrame(frame_params, text="Otoczka", padding=2)
        h_frame.pack(fill=tk.X, pady=2)
        
        row_h = ttk.Frame(h_frame)
        row_h.pack(fill=tk.X)
        self.btn_col_hull = tk.Button(row_h, text=" ", bg=self.hull_color, width=3, command=lambda: self.pick_color('hull_color', self.btn_col_hull))
        self.btn_col_hull.pack(side=tk.LEFT)
        ttk.Label(row_h, text="Grubość").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(row_h, from_=1, to=10, textvariable=self.hull_width, width=4, command=self.draw_plot).pack(side=tk.LEFT)
        styles = ["Ciągła", "Przerywana", "Kropkowana", "Kreska-kropka"]
        cb_h_style = ttk.Combobox(row_h, values=styles, textvariable=self.hull_style, state="readonly", width=9)
        cb_h_style.pack(side=tk.LEFT, padx=5)
        cb_h_style.bind("<<ComboboxSelected>>", lambda e: self.draw_plot())

        # C. Prostokąt
        b_frame = ttk.LabelFrame(frame_params, text="Prostokąt ograniczający", padding=2)
        b_frame.pack(fill=tk.X, pady=2)
        
        row_b = ttk.Frame(b_frame)
        row_b.pack(fill=tk.X)
        self.btn_col_bbox = tk.Button(row_b, text=" ", bg=self.bbox_color, width=3, command=lambda: self.pick_color('bbox_color', self.btn_col_bbox))
        self.btn_col_bbox.pack(side=tk.LEFT)
        ttk.Label(row_b, text="Grubość").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(row_b, from_=1, to=10, textvariable=self.bbox_width, width=4, command=self.draw_plot).pack(side=tk.LEFT)
        cb_b_style = ttk.Combobox(row_b, values=styles, textvariable=self.bbox_style, state="readonly", width=9)
        cb_b_style.pack(side=tk.LEFT, padx=5)
        cb_b_style.bind("<<ComboboxSelected>>", lambda e: self.draw_plot())

        # PRZYCISK KONIEC
        # Używamy fill=None lub pack side=BOTTOM, ale ważne żeby ramki wyżej nie zajmowały 100% miejsca jeśli nie muszą.
        bottom_frame = ttk.Frame(self.left_panel)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        ttk.Button(bottom_frame, text="Koniec", command=self.on_closing).pack(side=tk.TOP, fill=tk.X)

    def _init_right_panel(self):
        # Frame na wykres - zabiera większość miejsca
        frame_plot = ttk.Frame(self.right_panel, borderwidth=1, relief="sunken")
        frame_plot.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_plot)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # --- INFO O AUTORZE ---
        # Umieszczone w prawym panelu, na dole, wyrównane do prawej
        lbl_author = ttk.Label(self.right_panel, text="Autor: Adam Szczęśniak", font=("Segoe UI", 8, "italic"), foreground="gray")
        lbl_author.pack(side=tk.BOTTOM, anchor="e", padx=10, pady=(0, 5))

    # --- LOGIKA ---
    def validate_float_input(self, new_value):
        """Sprawdza, czy wprowadzany tekst jest poprawną liczbą (lub jej początkiem)"""
        if new_value == "": return True            # Pozwól na puste pole (kasowanie)
        if new_value in ["-", ".", ","]: return True  # Pozwól na wpisanie minusa lub kropki/przecinka na początku
        if new_value in ["-.", "-,"]: return True  # Pozwól na minus z kropką
        
        try:
            # Zamień przecinek na kropkę i spróbuj konwersji
            float(new_value.replace(',', '.'))
            return True
        except ValueError:
            return False
    
    def parse_float(self, txt):
        return float(txt.replace(',', '.'))

    def pick_color(self, var_name, btn_widget):
        color = colorchooser.askcolor()[1]
        if color:
            setattr(self, var_name, color)
            btn_widget.configure(bg=color)
            self.draw_plot()

    def get_mpl_style(self, style_name):
        map_style = {
            "Ciągła": "-", 
            "Przerywana": "--", 
            "Kropkowana": ":", 
            "Kreska-kropka": "-."
        }
        return map_style.get(style_name, "-")

    def get_mpl_marker(self, marker_name):
        map_marker = {
            "Okrąg": "o",
            "Kwadrat": "s",
            "Trójkąt": "^",
            "X": "x"
        }
        return map_marker.get(marker_name, "o")

    def update_tree(self):
        # Czyści tabelę i wypełnia na nowo
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, p in enumerate(self.points):
            self.tree.insert("", "end", values=(i+1, p[0], p[1]))
        
        self.lbl_stats.config(text=f"Liczba punktów: {len(self.points)}")

    def load_points(self):
        file_path = filedialog.askopenfilename(filetypes=[("Pliki tekstowe", "*.txt")])
        if not file_path:
            return
        
        new_points = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            x = self.parse_float(parts[0])
                            y = self.parse_float(parts[1])
                            new_points.append((x, y))
                        except ValueError:
                            continue
            
            if new_points:
                self.points = new_points
                self.hull_points = [] # Reset otoczki po wczytaniu nowych
                self.bbox = calculations.get_bounding_box(self.points)
                self.update_tree()
                self.draw_plot()
                messagebox.showinfo("Sukces", f"Wczytano {len(new_points)} punktów.")
            else:
                messagebox.showwarning("Błąd", "Nie znaleziono poprawnych danych w pliku.")

        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def add_manual_point(self):
        try:
            x = self.parse_float(self.entry_x.get())
            y = self.parse_float(self.entry_y.get())
            
            self.points.append((x, y))
            # Aktualizacja bboxa
            self.bbox = calculations.get_bounding_box(self.points)
            # Jeśli dodajemy punkt, otoczka może być nieaktualna
            self.hull_points = [] 
            
            self.update_tree()
            self.draw_plot()
            
            self.entry_x.delete(0, tk.END)
            self.entry_y.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Błąd", "Podaj poprawne współrzędne liczbowe.")

    def build_hull(self):
        if len(self.points) < 3:
            messagebox.showwarning("Ostrzeżenie", "Potrzeba co najmniej 3 punktów do budowy otoczki.")
            return
        
        try:
            self.hull_points = calculations.graham_scan(list(self.points))
            self.draw_plot()
            # messagebox.showinfo("Info", "Otoczka została zbudowana.")
        except Exception as e:
            messagebox.showerror("Błąd obliczeń", str(e))

    def save_hull(self):
        if not self.hull_points:
            messagebox.showwarning("Błąd", "Brak otoczki do zapisania. Najpierw kliknij 'Zbuduj otoczkę'.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Pliki tekstowe", "*.txt")])
        if not file_path: return
        
        try:
            with open(file_path, 'w') as f:
                f.write("X\tY\n")
                # Zapisujemy bez ostatniego punktu duplikującego start, chyba że użytkownik chce zamkniętą
                # Standardowo w pliku podaje się unikalne wierzchołki
                unique_hull = self.hull_points[:-1] if len(self.hull_points) > 1 and self.hull_points[0] == self.hull_points[-1] else self.hull_points
                
                for p in unique_hull:
                    f.write(f"{p[0]}\t{p[1]}\n")
            messagebox.showinfo("Sukces", "Zapisano punkty otoczki.")
        except Exception as e:
            messagebox.showerror("Błąd zapisu", str(e))

    def on_closing(self):
        """Funkcja wywoływana przy zamykaniu okna krzyżykiem lub przyciskiem Koniec"""
        if messagebox.askokcancel("Wyjście", "Czy na pewno chcesz zamknąć program?"):
            self.root.quit()
            self.root.destroy()

    def delete_all_points(self):
        if not self.points:
            return
        
        if messagebox.askyesno("Potwierdzenie", "Czy na pewno usunąć wszystkie punkty?"):
            self.points = []
            self.hull_points = []
            self.bbox = None
            self.update_tree()
            self.draw_plot()

    def delete_selected_point(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Zaznacz punkt w tabeli, aby go usunąć.")
            return

        # Pobieramy indeksy zaznaczonych elementów
        # Treeview zwraca ID, ale ponieważ dodajemy je w pętli, index w treeview pokrywa się z self.points
        # Najbezpieczniej jest iterować od końca, żeby nie zaburzyć indeksów przy usuwaniu wielu
        indices_to_delete = []
        for item in selected_items:
            index = self.tree.index(item)
            indices_to_delete.append(index)
        
        # Sortujemy malejąco
        indices_to_delete.sort(reverse=True)
        
        for idx in indices_to_delete:
            if 0 <= idx < len(self.points):
                del self.points[idx]
        
        # Resetujemy wyniki obliczeń po zmianie danych
        self.hull_points = []
        if self.points:
            self.bbox = calculations.get_bounding_box(self.points)
        else:
            self.bbox = None
            
        self.update_tree()
        self.draw_plot()
    
    def draw_plot(self):
        self.ax.clear()
        
        # Ustawienia osi
        self.ax.set_aspect('equal', adjustable='datalim')
        self.ax.grid(True, linestyle=':', alpha=0.6)
        
        # W układzie geodezyjnym X jest pionowo (tradycyjnie Y na wykresie), 
        # a Y jest poziomo (tradycyjnie X na wykresie).
        self.ax.set_xlabel("Y") 
        self.ax.set_ylabel("X")

        # 1. Rysowanie PROSTOKĄTA (BBOX)
        if self.points and self.bbox:
            min_x, min_y, max_x, max_y = self.bbox
            bx = [min_x, max_x, max_x, min_x, min_x]
            by = [min_y, min_y, max_y, max_y, min_y]
            
            # Zamiana bx i by miejscami dla układu geodezyjnego
            self.ax.plot(by, bx, 
                         color=self.bbox_color,
                         linewidth=self.bbox_width.get(),
                         linestyle=self.get_mpl_style(self.bbox_style.get()),
                         label='Prostokąt Ograniczający')

        # 2. Rysowanie OTOCZKI
        if self.hull_points:
            hx, hy = zip(*self.hull_points)
            # Zamiana hx i hy miejscami
            self.ax.plot(hy, hx,
                         color=self.hull_color,
                         linewidth=self.hull_width.get(),
                         linestyle=self.get_mpl_style(self.hull_style.get()),
                         label='Otoczka Wypukła',
                         zorder=2)

        # 3. Rysowanie PUNKTÓW
        if self.points:
            px, py = zip(*self.points)
            # Zamiana px i py miejscami
            self.ax.scatter(py, px, 
                            c=self.pt_color, 
                            s=self.pt_size.get(), 
                            marker=self.get_mpl_marker(self.pt_shape.get()),
                            zorder=3)
            
            # Etykiety punktów (również zamienione współrzędne)
            if self.pt_show_labels.get():
                for i, p in enumerate(self.points):
                    # Annotate (x_ekranowe, y_ekranowe) -> (p[1], p[0])
                    self.ax.annotate(str(i+1), (p[1], p[0]), xytext=(3, 3), textcoords='offset points', fontsize=8)

        # Skalowanie widoku
        if self.points:
            self.ax.relim()
            self.ax.autoscale_view()

        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = HullApp(root)
    root.mainloop()