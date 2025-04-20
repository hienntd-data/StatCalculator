import customtkinter as ctk
from CTkListbox import CTkListbox
import json
import os
from color_config import ColorConfig
from stat_calculator import StatCalculator
from result_window import ResultWindow
from constants import stats

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Stat Calculator")
        self.geometry("1120x600")
        self.resizable(False, False)
        
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=ColorConfig.FG)

        # Initialize Data
        self.current_language = "zh-cn"
        self.calculator = StatCalculator(self)
        self.item_stats_data = {}
        self.character_stats_data = {}
        self.history = []
        self.redo_stack = []
        self.max_history = 50

        self.database_file = "config.json"
        self.session_file = "session.json"
        if os.path.exists(self.database_file):
            with open(self.database_file, "r", encoding='utf-8') as f:
                self.database = json.load(f)
        else:
            self.database = {"items": {}, "characters": {}}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Define fonts
        self.chinese_label_font = ctk.CTkFont(family="DengXian", size=13, weight="bold")
        self.label_font = ctk.CTkFont(family="Poppins", size=15)
        self.entry_font = ctk.CTkFont(family="Poppins", size=13)
        self.desc_font = ctk.CTkFont(family="Poppins", size=13)
        self.button_font = ctk.CTkFont(family="Poppins", size=13)
        self.tab_font = ctk.CTkFont(family="Poppins", size=15)

        # Keyboard Shortcuts
        self.bind("<Control-z>", lambda event: self.undo())
        self.bind("<Control-y>", lambda event: self.redo())
        self.bind("<Control-s>", lambda event: self.save_database())
        self.bind("<Return>", lambda event: self.show_result())

        # Top Frame (Language Switch and Tab Buttons)
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.top_frame.grid_columnconfigure(0, weight=1)

        # Language Frame (Spans Top Frame, Contains Language Menu and Tab Buttons)
        self.lang_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.lang_frame.grid(row=0, column=0, sticky="ew")
        self.lang_frame.grid_columnconfigure(0, weight=1)  
        self.lang_frame.grid_columnconfigure(1, weight=0)  
        self.lang_frame.grid_columnconfigure(2, weight=1)  

        self.tab_button_frame = ctk.CTkFrame(self.lang_frame, fg_color="transparent")
        self.tab_button_frame.grid(row=0, column=1, padx=5, pady=5)

        self.lang_option = ctk.CTkOptionMenu(
            self.lang_frame,
            values=["Chinese (ZH-CN)", "English (EN)"],
            command=self.toggle_language_option,
            font=self.entry_font,
            fg_color=ColorConfig.SECONDARY_FG,
            button_color=ColorConfig.ACCENT,
            button_hover_color=ColorConfig.HOVER,
            dropdown_fg_color=ColorConfig.SECONDARY_FG,
            dropdown_hover_color=ColorConfig.LISTBOX_HOVER,
            dropdown_text_color= ColorConfig.TEXT,
            text_color=ColorConfig.TEXT,
            width=150
        )
        self.lang_option.grid(row=0, column=2, padx=(0, 20), pady=5, sticky="e")
        self.lang_option.set("Chinese (ZH-CN)")

        self.default_tab_btn = ctk.CTkButton(
            self.tab_button_frame,
            text="Default",
            font=self.tab_font,
            width=100,
            corner_radius=15,
            fg_color=ColorConfig.ACCENT,
            hover_color=ColorConfig.HOVER,
            text_color=ColorConfig.TEXT_BUTTON,
            command=lambda: self.switch_tab("Default")
        )
        self.default_tab_btn.pack(side="left", padx=(150,5))

        self.damage_tab_btn = ctk.CTkButton(
            self.tab_button_frame,
            text="Damage",
            font=self.tab_font,
            width=100,
            corner_radius=15,
            fg_color= ColorConfig.DIM,
            hover_color=ColorConfig.HOVER,
            text_color=ColorConfig.TEXT_BUTTON,
            command=lambda: self.switch_tab("Damage")
        )
        self.damage_tab_btn.pack(side="left", padx=5)

        # Center Frame (Tab Content)
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)

        self.tab_container = ctk.CTkFrame(self.center_frame, fg_color="transparent", corner_radius=10)
        self.tab_container.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)

        self.default_tab_frame = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.damage_tab_frame = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        
        self.current_tab = "Default"
        self.default_tab_frame.grid(row=0, column=0, sticky="nsew")

        self.selected_stats = []
        self.create_default_tab()
        self.create_damage_tab()

        self.label_column_minsize = 200

        # Load session after UI is created
        self.load_session()

    def switch_tab(self, tab_name):
        if not self.winfo_exists() or self.current_tab == tab_name:
            return
        self.current_tab = tab_name
        if tab_name == "Default":
            self.damage_tab_frame.grid_remove()
            self.default_tab_frame.grid(row=0, column=0, sticky="nsew")
            self.default_tab_btn.configure(fg_color=ColorConfig.ACCENT)
            self.damage_tab_btn.configure(fg_color= ColorConfig.DIM)
        else:  # Damage
            self.default_tab_frame.grid_remove()
            self.damage_tab_frame.grid(row=0, column=0, sticky="nsew")
            self.default_tab_btn.configure(fg_color=ColorConfig.DIM)
            self.damage_tab_btn.configure(fg_color=ColorConfig.ACCENT)
        self.status_label.configure(text=f"Switched to {tab_name} tab")

    def create_default_tab(self):
        tab_frame = self.default_tab_frame
        tab_frame.grid_columnconfigure(0, weight=0)
        tab_frame.grid_columnconfigure(1, weight=1)
        tab_frame.grid_columnconfigure(2, weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(1, weight=0)

        max_label_width = 0
        for _, cn_stat, en_stat in stats:
            cn_width = self.chinese_label_font.measure(cn_stat)
            en_width = self.entry_font.measure(en_stat)
            max_label_width = max(max_label_width, cn_width, en_width)
        self.label_column_minsize = max_label_width + 20

        # Side 1: Stat Selection
        self.side_1_frame = ctk.CTkFrame(tab_frame, corner_radius=10, fg_color=ColorConfig.SECONDARY_FG)
        self.side_1_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        title = ctk.CTkLabel(self.side_1_frame, text="Stat Selection", font=(self.label_font, 16, "bold"), text_color=ColorConfig.ACCENT)
        title.grid(row=0, column=0, pady=(10, 0), padx=10)
        desc = ctk.CTkLabel(self.side_1_frame, text="Choose stats to calculate from the list below.", font=self.entry_font, text_color=ColorConfig.TEXT)
        desc.grid(row=1, column=0, pady=(0, 5), padx=10)

        self.filter_entry = ctk.CTkEntry(self.side_1_frame, placeholder_text="Filter Stats...", width=220, height=30,
                                         border_width=1, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, font=self.entry_font)
        self.filter_entry.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.filter_entry.bind("<FocusIn>", lambda e: self.filter_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        self.filter_entry.bind("<FocusOut>", lambda e:self.filter_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))
        self.filter_entry.bind("<KeyRelease>", self.filter_stats)

        self.listbox = CTkListbox(self.side_1_frame, multiple_selection=True, height=500, width=220,
                                  font=self.entry_font, border_width=1, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT,
                                  hover_color=ColorConfig.LISTBOX_HOVER, highlight_color=ColorConfig.LISTBOX_HIGHLIGHT)
        self.listbox.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        for i, (listbox_stat, _, _) in enumerate(stats):
            self.listbox.insert(i, listbox_stat)

        self.side_1_frame.grid_rowconfigure(3, weight=1)

        button_frame = ctk.CTkFrame(self.side_1_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, pady=10, padx=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.add_button = ctk.CTkButton(button_frame, text="Add \u2795", width=100, command=self.on_add,
                                        font=self.button_font, corner_radius=15, fg_color=ColorConfig.ACCENT, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON)
        self.add_button.grid(row=0, column=0, padx=2, sticky="ew")

        self.refresh_btn = ctk.CTkButton(button_frame, text="Reset \u21BB", width=100, command=self.unselect_all,
                                         font=self.button_font, corner_radius=15, fg_color=ColorConfig.DIM, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON)
        self.refresh_btn.grid(row=0, column=1, padx=2, sticky="ew")

        # Side 2: Item Stats
        self.side_2_frame = ctk.CTkScrollableFrame(tab_frame, corner_radius=10, fg_color=ColorConfig.SECONDARY_FG)
        self.side_2_frame.grid(row=0, column=1, padx=(10, 5), pady=10, sticky="nsew")

        self.title_item = ctk.CTkLabel(self.side_2_frame, text="Item Stats", font=(self.label_font, 16, "bold"), text_color=ColorConfig.ACCENT)
        self.title_item.grid(row=0, column=0, columnspan=3, pady=(0, 2), padx=10)
        self.desc_item = ctk.CTkLabel(self.side_2_frame, text="Enter stats for your item or load from database.", font=self.entry_font, text_color=ColorConfig.TEXT)
        self.desc_item.grid(row=1, column=0, columnspan=3, pady=(0, 2), padx=10)

        self.item_index_entry = ctk.CTkEntry(self.side_2_frame, placeholder_text="Enter Item Index", width=220, height=30,
                                             border_width=1, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, font=self.entry_font)
        self.item_index_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.item_index_entry.bind("<FocusIn>", lambda e: self.item_index_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        self.item_index_entry.bind("<FocusOut>", lambda e:self.item_index_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))

        self.item_load_btn = ctk.CTkButton(self.side_2_frame, text="Load", width=30, command=self.load_item_stats,
                                           font=self.button_font, corner_radius=15, fg_color=ColorConfig.ACCENT, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON)
        self.item_load_btn.grid(row=2, column=2, padx=10, pady=5)

        # Side 3: Character Stats
        self.side_3_frame = ctk.CTkScrollableFrame(tab_frame, corner_radius=10, fg_color=ColorConfig.SECONDARY_FG)
        self.side_3_frame.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")

        title_char = ctk.CTkLabel(self.side_3_frame, text="Character Stats", font=self.label_font, text_color=ColorConfig.ACCENT)
        title_char.grid(row=0, column=0, columnspan=3, pady=(0, 2), padx=10)
        desc_char = ctk.CTkLabel(self.side_3_frame, text="Enter stats for your character or load from database.", font=self.entry_font, text_color=ColorConfig.TEXT)
        desc_char.grid(row=1, column=0, columnspan=3, pady=(0, 2), padx=10)

        self.char_name_entry = ctk.CTkEntry(self.side_3_frame, placeholder_text="Enter Character Name", width=220, height=30,
                                            border_width=1, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, font=self.entry_font)
        self.char_name_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.char_name_entry.bind("<FocusIn>", lambda e: self.char_name_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        self.char_name_entry.bind("<FocusOut>", lambda e:self.char_name_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))

        self.char_load_btn = ctk.CTkButton(self.side_3_frame, text="Load", width=30, command=self.load_character_stats,
                                           font=self.button_font, corner_radius=15, fg_color=ColorConfig.ACCENT, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON)
        self.char_load_btn.grid(row=2, column=2, padx=10, pady=5)

        # Result Frame
        self.side_4_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
        self.side_4_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=(10, 10), sticky="ew")
        self.side_4_frame.grid_columnconfigure(0, weight=1)
        self.side_4_frame.grid_columnconfigure((1, 2), weight=0)

        self.status_label = ctk.CTkLabel(self.side_4_frame, text="Ready", font=self.entry_font, text_color=ColorConfig.TEXT,
                                         fg_color=ColorConfig.SECONDARY_FG, padx=5, pady=2, corner_radius=5)
        self.status_label.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        self.save_btn = ctk.CTkButton(self.side_4_frame, text="Save", width=100, command=self.save_database,
                                      font=self.button_font, corner_radius=15, fg_color=ColorConfig.ACCENT, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON)
        self.save_btn.grid(row=0, column=1, padx=5, pady=10)

        self.result_btn = ctk.CTkButton(self.side_4_frame, text="Result", width=100, command=self.show_result,
                                        font=self.button_font, corner_radius=15, fg_color=ColorConfig.ACCENT, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON)
        self.result_btn.grid(row=0, column=2, padx=5, pady=10)

        self.item_stats_entries = []
        self.item_stat_labels = []
        self.item_remove_buttons = []
        self.character_stats_entries = []
        self.character_stat_labels = []
        self.character_remove_buttons = []

    def create_damage_tab(self):
        tab_frame = self.damage_tab_frame
        tab_frame.grid_columnconfigure(0, weight=1)  
        tab_frame.grid_columnconfigure(1, weight=0)  
        tab_frame.grid_columnconfigure(2, weight=0)  
        tab_frame.grid_columnconfigure(3, weight=1)  
        tab_frame.grid_rowconfigure(0, weight=0)

        
        damage_labels = ["Base Damage", "Critical Bonus (%)", "Result", "Damage Item 1", "Damage Item 2", "Difference (%)"]
        max_label_width = max(self.entry_font.measure(label) for label in damage_labels) + 10
        label_minsize = max_label_width

        # Side 1: Critical Damage
        self.critical_frame = ctk.CTkFrame(tab_frame, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, width=200, height=250)
        self.critical_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.critical_frame.grid_columnconfigure(0, minsize=label_minsize, weight=0)
        self.critical_frame.grid_columnconfigure(1, weight=1)
        self.critical_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        critical_title = ctk.CTkLabel(self.critical_frame, text="Critical Damage", font=(self.label_font, 16, "bold"), text_color=ColorConfig.ACCENT, anchor="center")
        critical_title.grid(row=0, column=0, columnspan=2, pady=(20, 10), padx=10, sticky="ew")

        base_damage_label = ctk.CTkLabel(self.critical_frame, text="Base Damage", font=self.entry_font, text_color=ColorConfig.TEXT)
        base_damage_label.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")
        self.base_damage_entry = ctk.CTkEntry(self.critical_frame, width=140, placeholder_text="e.g., 100",
                                            font=self.entry_font, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, corner_radius=15)
        self.base_damage_entry.grid(row=1, column=1, padx=(10, 0), pady=10, sticky="w")
        self.base_damage_entry.bind("<FocusIn>", lambda e: self.base_damage_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        self.base_damage_entry.bind("<FocusOut>", lambda e:self.base_damage_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))

        crit_bonus_label = ctk.CTkLabel(self.critical_frame, text="Critical Bonus (%)", font=self.entry_font, text_color=ColorConfig.TEXT)
        crit_bonus_label.grid(row=2, column=0, padx=(20, 10), pady=10, sticky="w")
        self.crit_bonus_entry = ctk.CTkEntry(self.critical_frame, width=140, placeholder_text="e.g., 20",
                                            font=self.entry_font, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, corner_radius=15)
        self.crit_bonus_entry.grid(row=2, column=1, padx=(10, 0), pady=10, sticky="w")
        self.crit_bonus_entry.bind("<FocusIn>", lambda e: self.crit_bonus_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        self.crit_bonus_entry.bind("<FocusOut>", lambda e:self.crit_bonus_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))

        crit_result_label = ctk.CTkLabel(self.critical_frame, text="Result", font=self.entry_font, text_color=ColorConfig.TEXT)
        crit_result_label.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="w")
        self.crit_result_entry = ctk.CTkEntry(self.critical_frame, width=140, placeholder_text="N/A", state="disabled",
                                            font=self.entry_font, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, corner_radius=15)
        self.crit_result_entry.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="w")
        

        button_frame_crit = ctk.CTkFrame(self.critical_frame, fg_color="transparent")
        button_frame_crit.grid(row=4, column=0, columnspan=2, pady=(20, 20), sticky="ew")
        button_frame_crit.grid_columnconfigure((0, 1), weight=1)
        crit_calc_button = ctk.CTkButton(button_frame_crit, text="Calculate", command=self.calculate_critical_damage,
                                        font=self.button_font, width=120, fg_color=ColorConfig.ACCENT, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON, corner_radius=15)
        crit_calc_button.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="e")
        crit_reset_button = ctk.CTkButton(button_frame_crit, text="Reset \u21BB", command=self.reset_critical_damage,
                                        font=self.button_font, width=120, fg_color=ColorConfig.DIM, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON, corner_radius=15)
        crit_reset_button.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="w")

        # Side 2: Damage Difference
        self.damage_frame = ctk.CTkFrame(tab_frame, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, width=400, height=350)
        self.damage_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.damage_frame.grid_columnconfigure(0, minsize=label_minsize, weight=0)
        self.damage_frame.grid_columnconfigure(1, weight=1)
        self.damage_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        damage_title = ctk.CTkLabel(self.damage_frame, text="Damage Difference", font=(self.label_font, 16, "bold"), text_color=ColorConfig.ACCENT, anchor="center")
        damage_title.grid(row=0, column=0, columnspan=2, pady=(20, 10), padx=10, sticky="ew")

        damage_item1_label = ctk.CTkLabel(self.damage_frame, text="Damage Item 1", font=self.entry_font, text_color=ColorConfig.TEXT)
        damage_item1_label.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")  
        self.damage_item1_entry = ctk.CTkEntry(self.damage_frame, width=140, placeholder_text="e.g., 120",
                                            font=self.entry_font, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, corner_radius=15)
        self.damage_item1_entry.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="w")  
        self.damage_item1_entry.bind("<FocusIn>", lambda e: self.damage_item1_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        self.damage_item1_entry.bind("<FocusOut>", lambda e:self.damage_item1_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))

        damage_item2_label = ctk.CTkLabel(self.damage_frame, text="Damage Item 2", font=self.entry_font, text_color=ColorConfig.LABEL_TEXT)
        damage_item2_label.grid(row=2, column=0, padx=(20, 10), pady=10, sticky="w")
        self.damage_item2_entry = ctk.CTkEntry(self.damage_frame, width=140, placeholder_text="e.g., 100",
                                            font=self.entry_font, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, corner_radius=15)
        self.damage_item2_entry.grid(row=2, column=1, padx=(10, 20), pady=10, sticky="w")
        self.damage_item2_entry.bind("<FocusIn>", lambda e: self.damage_item2_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        self.damage_item2_entry.bind("<FocusOut>", lambda e:self.damage_item2_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))
        

        damage_diff_label = ctk.CTkLabel(self.damage_frame, text="Difference (%)", font=self.entry_font, text_color=ColorConfig.LABEL_TEXT)
        damage_diff_label.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="w")
        self.damage_diff_entry = ctk.CTkEntry(self.damage_frame, width=140, placeholder_text="N/A", state="disabled",
                                            font=self.entry_font, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, corner_radius=15)
        self.damage_diff_entry.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="w")

        button_frame_diff = ctk.CTkFrame(self.damage_frame, fg_color="transparent")
        button_frame_diff.grid(row=4, column=0, columnspan=2, pady=(20, 20), sticky="ew")
        button_frame_diff.grid_columnconfigure((0, 1), weight=1)
        damage_calc_button = ctk.CTkButton(button_frame_diff, text="Calculate", command=self.calculate_damage_difference,
                                        font=self.button_font, width=120, fg_color=ColorConfig.ACCENT, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON, corner_radius=15)
        damage_calc_button.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="ew")
        damage_reset_button = ctk.CTkButton(button_frame_diff, text="Reset \u21BB", command=self.reset_damage_difference,
                                            font=self.button_font, width=120, fg_color=ColorConfig.DIM, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON, corner_radius=15)
        damage_reset_button.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="ew")

    def calculate_critical_damage(self):
        base_damage = self.base_damage_entry.get()
        crit_bonus = self.crit_bonus_entry.get()
        result = self.calculator.calculate_critical_damage(base_damage, crit_bonus)
        self.crit_result_entry.configure(state="normal")
        self.crit_result_entry.delete(0, "end")
        self.crit_result_entry.insert(0, result)
        self.crit_result_entry.configure(state="disabled")

    def calculate_damage_difference(self):
        damage1 = self.damage_item1_entry.get()
        damage2 = self.damage_item2_entry.get()
        difference = self.calculator.calculate_damage_difference(damage1, damage2)
        self.damage_diff_entry.configure(state="normal")
        self.damage_diff_entry.delete(0, "end")
        self.damage_diff_entry.insert(0, difference)
        self.damage_diff_entry.configure(state="disabled")

    def reset_critical_damage(self):
        self.base_damage_entry.delete(0, "end")
        self.crit_bonus_entry.delete(0, "end")
        self.crit_result_entry.configure(state="normal")
        self.crit_result_entry.delete(0, "end")
        self.crit_result_entry.insert(0, "N/A")
        self.crit_result_entry.configure(state="disabled")

    def reset_damage_difference(self):
        self.damage_item1_entry.delete(0, "end")
        self.damage_item2_entry.delete(0, "end")
        self.damage_diff_entry.configure(state="normal")
        self.damage_diff_entry.delete(0, "end")
        self.damage_diff_entry.insert(0, "N/A")
        self.damage_diff_entry.configure(state="disabled")

    def filter_stats(self, event=None):
        if not self.winfo_exists():
            return
        
        filter_text = self.filter_entry.get().lower()
        current_selected_indices = self.listbox.curselection()
        current_selected_stats = {self.listbox.get(i) for i in current_selected_indices}

        for _ in range(self.listbox.size()):
            self.listbox.delete(0)

        filtered_stats = [
            (listbox_stat, cn, en) for listbox_stat, cn, en in stats 
            if filter_text in listbox_stat.lower()
        ]
        
        for i, (listbox_stat, _, _) in enumerate(filtered_stats):
            self.listbox.insert(i, listbox_stat)
        
        for i, (listbox_stat, _, _) in enumerate(filtered_stats):
            if listbox_stat in current_selected_stats:
                self.listbox.select(i)

    def unselect_all(self):
        if not self.winfo_exists():
            return
        try:
            for i in range(self.listbox.size()):
                self.listbox.delete(0)
            for i, (listbox_stat, _, _) in enumerate(stats):
                self.listbox.insert(i, listbox_stat)

            self.selected_stats.clear()
            self.item_stats_data.clear()
            self.character_stats_data.clear()
            self.item_index_entry.delete(0, "end")
            self.char_name_entry.delete(0, "end")
            self.filter_entry.delete(0, "end")
            self.rebuild_ui()
            self.reset_critical_damage()
            self.reset_damage_difference()
            self.history.clear()
            self.redo_stack.clear()
            self.status_label.configure(text="App reset to initial state")
            self.update_idletasks()
        except Exception as e:
            print(f"Error in unselect_all: {e}")
            self.status_label.configure(text="Reset failed")

    def on_add(self):
        if not self.winfo_exists():
            return
        try:
            selected_indices = self.listbox.curselection()
            selected_stats = [self.listbox.get(i) for i in selected_indices]
            added_stats = []
            
            for stat in selected_stats:
                if stat not in self.selected_stats:
                    self.selected_stats.append(stat)
                    index = len(self.selected_stats) - 1
                    self.add_stat_to_ui(stat, index)
                    added_stats.append({"stat": stat, "index": index})
            
            if added_stats:
                self._record_action("add_stats", {"stats": added_stats})
                added_names = ", ".join([stat["stat"] for stat in added_stats])
                self.status_label.configure(text=f"Added: {added_names}")
                
        except Exception as e:
            print(f"Error in on_add: {e}")

    def add_stat_to_ui(self, stat, index):
        if not self.winfo_exists():
            return
        row = index + 3
        listbox_stat, cn_stat, en_stat = next((l, c, e) for l, c, e in stats if l == stat)
        display_stat = cn_stat if self.current_language == "zh-cn" else en_stat
        current_font = self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font
        label_width = current_font.measure(display_stat) + 10

        # Item side
        item_label = ctk.CTkLabel(self.side_2_frame, text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font, text_color=ColorConfig.TEXT)
        item_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        item_entry = ctk.CTkEntry(self.side_2_frame, width=120, border_width=1, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, font=self.entry_font)
        item_entry.bind("<FocusIn>", lambda e: item_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        item_entry.bind("<FocusOut>", lambda e:item_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))
        item_entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        if stat in self.item_stats_data:
            item_entry.insert(0, self.item_stats_data[stat])
        item_entry.bind("<KeyRelease>", lambda e, s=stat: self.update_item_data(s, e.widget.get()))
        
        item_remove = ctk.CTkButton(self.side_2_frame, text="−", width=30, command=lambda: self.remove_stat(index),
                                    fg_color=ColorConfig.DIM, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON, corner_radius=8, font=self.button_font)
        item_remove.grid(row=row, column=2, padx=10, pady=5)

        # Character side
        char_label = ctk.CTkLabel(self.side_3_frame, text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font, text_color=ColorConfig.TEXT)
        char_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        char_entry = ctk.CTkEntry(self.side_3_frame, width=120, border_width=1, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG, text_color=ColorConfig.TEXT, font=self.entry_font)
        char_entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        char_entry.bind("<FocusIn>", lambda e: char_entry.configure(border_color=ColorConfig.BORDER_FOCUS))
        char_entry.bind("<FocusOut>", lambda e:char_entry.configure(border_color=ColorConfig.BORDER_DEFAULT))
        if stat in self.character_stats_data:
            char_entry.insert(0, self.character_stats_data[stat])
        char_entry.bind("<KeyRelease>", lambda e, s=stat: self.update_character_data(s, e.widget.get()))
        
        char_remove = ctk.CTkButton(self.side_3_frame, text="−", width=30, command=lambda: self.remove_stat(index),
                                    fg_color=ColorConfig.DIM, hover_color=ColorConfig.HOVER, text_color=ColorConfig.TEXT_BUTTON, corner_radius=8, font=self.button_font)
        char_remove.grid(row=row, column=2, padx=10, pady=5)

        self.item_stat_labels.append(item_label)
        self.item_stats_entries.append(item_entry)
        self.item_remove_buttons.append(item_remove)
        self.character_stat_labels.append(char_label)
        self.character_stats_entries.append(char_entry)
        self.character_remove_buttons.append(char_remove)

    def update_item_data(self, stat, value):
        if not self.winfo_exists():
            return
        previous_value = self.item_stats_data.get(stat, "")
        if value:
            self.item_stats_data[stat] = value
        elif stat in self.item_stats_data:
            del self.item_stats_data[stat]
        self._record_action("update_item", {"stat": stat, "value": value, "previous_value": previous_value})

    def update_character_data(self, stat, value):
        if not self.winfo_exists():
            return
        previous_value = self.character_stats_data.get(stat, "")
        self._record_action("update_character", {"stat": stat, "value": value, "previous_value": previous_value})
        if value:
            self.character_stats_data[stat] = value
        elif stat in self.character_stats_data:
            del self.character_stats_data[stat]

    def remove_stat(self, index):
        if not self.winfo_exists():
            return
        if 0 <= index < len(self.selected_stats):
            removed_stat = self.selected_stats[index]
            item_value = self.item_stats_entries[index].get()
            char_value = self.character_stats_entries[index].get()
            self._record_action("remove_stat", {
                "stat": removed_stat,
                "index": index,
                "item_value": item_value,
                "char_value": char_value
            })
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"Removed: {removed_stat}")
            self.selected_stats.pop(index)
            
            self.item_stat_labels[index].grid_forget()
            self.item_stats_entries[index].grid_forget()
            self.item_remove_buttons[index].grid_forget()
            self.character_stat_labels[index].grid_forget()
            self.character_stats_entries[index].grid_forget()
            self.character_remove_buttons[index].grid_forget()
            
            self.item_stat_labels.pop(index)
            self.item_stats_entries.pop(index)
            self.item_remove_buttons.pop(index)
            self.character_stat_labels.pop(index)
            self.character_stats_entries.pop(index)
            self.character_remove_buttons.pop(index)

            self.rebuild_ui()
            

    def rebuild_ui(self):
        if not self.winfo_exists():
            return
        for label in self.item_stat_labels:
            label.grid_forget()
        for entry in self.item_stats_entries:
            entry.grid_forget()
        for button in self.item_remove_buttons:
            button.grid_forget()
        for label in self.character_stat_labels:
            label.grid_forget()
        for entry in self.character_stats_entries:
            entry.grid_forget()
        for button in self.character_remove_buttons:
            button.grid_forget()
        
        self.item_stat_labels.clear()
        self.item_stats_entries.clear()
        self.item_remove_buttons.clear()
        self.character_stat_labels.clear()
        self.character_stats_entries.clear()
        self.character_remove_buttons.clear()

        for i, stat in enumerate(self.selected_stats):
            self.add_stat_to_ui(stat, i)

    def toggle_language_option(self, choice):
        if not self.winfo_exists():
            return
        self.current_language = "zh-cn" if choice == "Chinese (ZH-CN)" else "en"
        self.update_labels()
        self.status_label.configure(text=f"Language switched to {choice}")

    def update_labels(self):
        if not self.winfo_exists():
            return
        for i, stat in enumerate(self.selected_stats):
            _, cn_stat, en_stat = next((l, c, e) for l, c, e in stats if l == stat)
            display_stat = cn_stat if self.current_language == "zh-cn" else en_stat
            
            
            self.item_stat_labels[i].configure(text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font)
            self.character_stat_labels[i].configure(text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font)

        for frame in [self.side_1_frame, self.side_2_frame, self.side_3_frame, self.side_4_frame, self.critical_frame, self.damage_frame]:
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel):
                    text = widget.cget("text")

                    if text in ("Stat Selection", "Item Stats", "Character Stats", "Critical Damage", "Damage Difference"):
                        widget.configure(font=self.label_font)
                    elif text in (
                        "Enter stats for your item or load from database.",
                        "Choose stats to calculate from the list below.",
                        "Enter stats for your character or load from database."
                    ):
                        widget.configure(font=self.desc_font)
                    elif text == self.status_label.cget("text"):
                        widget.configure(font=self.desc_font)
                    else:
                        widget.configure(font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font)
                elif isinstance(widget, ctk.CTkButton):
                    widget.configure(font=self.button_font)
                elif isinstance(widget, ctk.CTkEntry):
                    widget.configure(font=self.entry_font)

    def load_item_stats(self):
        if not self.winfo_exists():
            return
        index = self.item_index_entry.get()
        if index in self.database["items"]:
            self.selected_stats.clear()
            self.rebuild_ui()
            for stat, value in self.database["items"][index].items():
                if stat not in self.selected_stats:
                    self.selected_stats.append(stat)
                    self.add_stat_to_ui(stat, len(self.selected_stats) - 1)
                    self.item_stats_entries[-1].delete(0, "end")
                    self.item_stats_entries[-1].insert(0, str(value))
                    self.item_stats_data[stat] = str(value)
                    self._record_action("add_stat", {"stat": stat, "index": len(self.selected_stats) - 1})
            self.status_label.configure(text=f"Loaded Item Index: {index}")
        else:
            self.status_label.configure(text=f"Item Index '{index}' not found in database.")

    def load_character_stats(self):
        if not self.winfo_exists():
            return
        name = self.char_name_entry.get()
        if name in self.database["characters"]:
            current_item_stats = set(self.selected_stats)
            loaded_count = 0
            for stat, value in self.database["characters"][name].items():
                if stat in current_item_stats:
                    index = self.selected_stats.index(stat)
                    self.character_stats_entries[index].delete(0, "end")
                    self.character_stats_entries[index].insert(0, str(value))
                    self._record_action("update_character", {
                        "stat": stat,
                        "value": str(value),
                        "previous_value": self.character_stats_data.get(stat, "")
                    })
                    loaded_count += 1
            self.status_label.configure(text=f"Loaded {loaded_count} stats for Character: {name}")
        else:
            self.status_label.configure(text=f"Character '{name}' not found in database.")

    def save_database(self):
        item_index, char_name = self.item_index_entry.get(), self.char_name_entry.get()
        
        if item_index and self.item_stats_entries:
            self.database["items"][item_index] = {
                stat: (int(val) if val.isdigit() else val)
                for stat, val in zip(self.selected_stats, (e.get() for e in self.item_stats_entries))
                if val
            }
        
        if char_name and self.character_stats_entries:
            existing_char_stats = self.database["characters"].get(char_name, {})
            new_char_stats = {
                stat: (int(val) if val.isdigit() else val)
                for stat, val in zip(self.selected_stats, (e.get() for e in self.character_stats_entries))
                if val
            }
            updated_char_stats = {**existing_char_stats, **new_char_stats}
            self.database["characters"][char_name] = updated_char_stats

        with open(self.database_file, "w", encoding='utf-8') as f:
            json.dump(self.database, f, indent=4, ensure_ascii=False)
        
        self.status_label.configure(text="Database saved successfully.")

    def show_result(self):
        if not self.winfo_exists():
            return
        item_stats = {}
        character_stats = {}
        for i, stat in enumerate(self.selected_stats):
            item_value = self.item_stats_entries[i].get()
            char_value = self.character_stats_entries[i].get()
            if item_value:
                item_stats[stat] = item_value
            if char_value:
                character_stats[stat] = char_value

        ResultWindow(self, item_stats, character_stats, self.current_language)
        self.status_label.configure(text="Result window opened.")

    def _record_action(self, action_type, action_data):
        if not self.winfo_exists():
            return
        if len(self.history) >= self.max_history:
            self.history.pop(0)
        self.history.append({"type": action_type, "data": action_data})
        self.redo_stack.clear()
        

    def undo(self):
        if not self.winfo_exists() or not self.history:
            self.status_label.configure(text="Nothing to undo")
            return
        try:
            action = self.history.pop()
            self.redo_stack.append(action)
            action_type = action["type"]
            action_data = action["data"]

            if action_type == "add_stats":
                for stat_data in reversed(action_data["stats"]):
                    stat = stat_data["stat"]
                    index = stat_data["index"]
                    if stat in self.selected_stats and self.selected_stats[index] == stat:
                        self.remove_stat(index)
            elif action_type == "add_stat":
                stat = action_data["stat"]
                index = action_data["index"]
                if stat in self.selected_stats and self.selected_stats[index] == stat:
                    self.remove_stat(index)
            elif action_type == "remove_stat":
                stat = action_data["stat"]
                index = action_data["index"]
                item_value = action_data["item_value"]
                char_value = action_data["char_value"]
                self.selected_stats.insert(index, stat)
                self.add_stat_to_ui(stat, index)
                if item_value:
                    self.item_stats_entries[index].insert(0, item_value)
                    self.item_stats_data[stat] = item_value
                if char_value:
                    self.character_stats_entries[index].insert(0, char_value)
                    self.character_stats_data[stat] = char_value
            elif action_type == "update_item":
                stat = action_data["stat"]
                previous_value = action_data["previous_value"]
                index = self.selected_stats.index(stat)
                self.item_stats_entries[index].delete(0, "end")
                if previous_value:
                    self.item_stats_entries[index].insert(0, previous_value)
                    self.item_stats_data[stat] = previous_value
                else:
                    self.item_stats_data.pop(stat, None)
            elif action_type == "update_character":
                stat = action_data["stat"]
                previous_value = action_data["previous_value"]
                index = self.selected_stats.index(stat)
                self.character_stats_entries[index].delete(0, "end")
                if previous_value:
                    self.character_stats_entries[index].insert(0, previous_value)
                    self.character_stats_data[stat] = previous_value
                else:
                    self.character_stats_data.pop(stat, None)

            self.status_label.configure(text=f"Undid last action: {action_type}")
        except Exception as e:
            print(f"Error in undo: {e}")
            self.status_label.configure(text="Undo failed")

    def redo(self):
        if not self.winfo_exists() or not self.redo_stack:
            self.status_label.configure(text="Nothing to redo")
            return
        try:
            action = self.redo_stack.pop()
            self.history.append(action)
            action_type = action["type"]
            action_data = action["data"]

            if action_type == "add_stat":
                stat = action_data["stat"]
                index = action_data["index"]
                if stat not in self.selected_stats:
                    self.selected_stats.append(stat)
                    self.add_stat_to_ui(stat, index)
            elif action_type == "remove_stat":
                index = action_data["index"]
                if 0 <= index < len(self.selected_stats):
                    self.remove_stat(index)
            elif action_type == "update_item":
                stat = action_data["stat"]
                value = action_data["value"]
                index = self.selected_stats.index(stat)
                self.item_stats_entries[index].delete(0, "end")
                if value:
                    self.item_stats_entries[index].insert(0, value)
                    self.item_stats_data[stat] = value
                else:
                    self.item_stats_data.pop(stat, None)
            elif action_type == "update_character":
                stat = action_data["stat"]
                value = action_data["value"]
                index = self.selected_stats.index(stat)
                self.character_stats_entries[index].delete(0, "end")
                if value:
                    self.character_stats_entries[index].insert(0, value)
                    self.character_stats_data[stat] = value
                else:
                    self.character_stats_data.pop(stat, None)

            self.status_label.configure(text=f"Redid action: {action_type}")
        except Exception as e:
            print(f"Error in redo: {e}")
            self.status_label.configure(text="Redo failed")

    def save_session(self):
        if not self.winfo_exists():
            return
        session_data = {
            "selected_stats": self.selected_stats,
            "item_stats_data": self.item_stats_data,
            "character_stats_data": self.character_stats_data,
            "current_language": self.current_language,
            "item_index": self.item_index_entry.get(),
            "char_name": self.char_name_entry.get(),
            "filter_text": self.filter_entry.get(),
            "critical_damage": {
                "base_damage": self.base_damage_entry.get(),
                "crit_bonus": self.crit_bonus_entry.get(),
                "result": self.crit_result_entry.get()
            },
            "damage_difference": {
                "damage1": self.damage_item1_entry.get(),
                "damage2": self.damage_item2_entry.get(),
                "result": self.damage_diff_entry.get()
            },
            "current_tab": self.current_tab
        }
        try:
            with open(self.session_file, "w", encoding='utf-8') as f:
                json.dump(session_data, f, indent=4, ensure_ascii=False)
            self.status_label.configure(text="Session saved")
        except Exception as e:
            print(f"Error saving session: {e}")
            self.status_label.configure(text="Failed to save session")

    def load_session(self):
        if not self.winfo_exists() or not os.path.exists(self.session_file):
            return
        try:
            with open(self.session_file, "r", encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.current_language = session_data.get("current_language", "zh-cn")
            self.lang_option.set("Chinese (ZH-CN)" if self.current_language == "zh-cn" else "English (EN)")
            self.update_labels()

            self.selected_stats = session_data.get("selected_stats", [])
            for i, stat in enumerate(self.selected_stats):
                self.add_stat_to_ui(stat, i)

            self.item_stats_data = session_data.get("item_stats_data", {})
            self.character_stats_data = session_data.get("character_stats_data", {})
            for i, stat in enumerate(self.selected_stats):
                if stat in self.item_stats_data:
                    self.item_stats_entries[i].insert(0, self.item_stats_data[stat])
                if stat in self.character_stats_data:
                    self.character_stats_entries[i].insert(0, self.character_stats_data[stat])

            self.item_index_entry.insert(0, session_data.get("item_index", ""))
            self.char_name_entry.insert(0, session_data.get("char_name", ""))
            self.filter_entry.insert(0, session_data.get("filter_text", ""))
            self.filter_stats()

            crit_data = session_data.get("critical_damage", {})
            self.base_damage_entry.insert(0, crit_data.get("base_damage", ""))
            self.crit_bonus_entry.insert(0, crit_data.get("crit_bonus", ""))
            if crit_data.get("result", "") != "N/A":
                self.crit_result_entry.configure(state="normal")
                self.crit_result_entry.delete(0, "end")
                self.crit_result_entry.insert(0, crit_data.get("result", ""))
                self.crit_result_entry.configure(state="disabled")

            diff_data = session_data.get("damage_difference", {})
            self.damage_item1_entry.insert(0, diff_data.get("damage1", ""))
            self.damage_item2_entry.insert(0, diff_data.get("damage2", ""))
            if diff_data.get("result", "") != "N/A":
                self.damage_diff_entry.configure(state="normal")
                self.damage_diff_entry.delete(0, "end")
                self.damage_diff_entry.insert(0, diff_data.get("result", ""))
                self.damage_diff_entry.configure(state="disabled")

            # Load current tab
            saved_tab = session_data.get("current_tab", "Default")
            self.switch_tab(saved_tab)

            self.status_label.configure(text="Session loaded")
        except Exception as e:
            print(f"Error loading session: {e}")
            self.status_label.configure(text="Failed to load session")

    def destroy(self):
        self.save_session()
        self.listbox = None
        super().destroy()