import customtkinter as ctk
from googletrans import Translator
from CTkListbox import CTkListbox
import json
import os
import re


class StatCalculator:
    def __init__(self, parent, item_stats=None, character_stats=None):
        self.parent = parent
        self.item_stats = item_stats or {}
        self.character_stats = character_stats or {}
        self.percentage_stats = {
            "攻击速度 (Attack Speed)",
            "施法速度 (Casting Speed)",
            "移动速度 (Movement Speed)"
        }
        self.additive_stats = {
            "生命值 (HP)",
            "魔法值 (MP)",
            "力量 (Strength)",
            "智力 (Intelligence)",
            "体力 (Physical Strength)",
            "精神 (Spirit)",
            "火属性强化 (Fire Enhance)",
            "冰属性强化 (Ice Enhance)",
            "光属性强化 (Light Enhance)",
            "暗属性强化 (Dark Enhance)",
            "火属性抗性 (Fire Resistance)",
            "冰属性抗性 (Ice Resistance)",
            "光属性抗性 (Light Resistance)",
            "暗属性抗性 (Dark Resistance)"
        }
        self.special_stats = {
            "物理攻击力 (Physical Attack Power)",
            "魔法攻击力 (Magical Attack Power)"
        }

    def get_item_value(self, stat):
        if stat in self.item_stats:
            return self.item_stats[stat]
        item_index = self.parent.item_index_entry.get()
        if item_index in self.parent.database["items"]:
            return self.parent.database["items"][item_index].get(stat, "")
        return ""

    def get_character_value(self, stat):
        if stat in self.character_stats:
            return self.character_stats[stat]
        char_name = self.parent.char_name_entry.get()
        if char_name in self.parent.database["characters"]:
            return self.parent.database["characters"][char_name].get(stat, "0")
        return "0"

    def calculate_result(self, stat):
        item_value = self.get_item_value(stat)
        char_value = self.get_character_value(stat)
        
        try:
            char_value = float(char_value.replace('%', '')) if '%' in str(char_value) else float(char_value or 0)
        except ValueError:
            char_value = 0

        if not item_value:
            return f"{char_value}%" if stat in self.percentage_stats else int(char_value) if char_value else "N/A"

        if stat in self.special_stats:
            return self.calculate_special_stat(stat, char_value, item_value)
        
        return (self.calculate_percentage_stat(char_value, item_value) if stat in self.percentage_stats 
                else self.calculate_additive_stat(char_value, item_value))

    def calculate_additive_stat(self, char_value, item_value):
        try:
            parts = self._split_item_value(str(item_value).lstrip('+'))
            base, bonus, percentage = 0, 0, 0
            
            for i, part in enumerate(parts):
                if not part:
                    continue
                if '%' in part:
                    percentage = float(part.replace('%', '')) / 100
                elif i == 0:
                    base = float(part)
                elif i == 1 and '%' not in parts[1]:
                    bonus = float(part)
                elif i == 2:
                    bonus = float(part)

            total_base = char_value + base + bonus
            return int(total_base + total_base * percentage)
        except (ValueError, AttributeError):
            return int(char_value) if char_value else "N/A"

    def calculate_percentage_stat(self, char_value, item_value):
        try:
            if not isinstance(char_value, (int, float)):
                char_value = 0.0

            total_item_percent = 0.0
            if item_value:
                item_value = str(item_value).replace('+-', '-')
                parts = re.split(r'(?<=%)[+-]', item_value.lstrip('+'))
                for part in parts:
                    if part:
                        match = self._extract_percentage.search(part)
                        if match:
                            value = float(match.group(1))
                            start_pos = match.start()
                            if start_pos > 0 and part[start_pos - 1] == '-':
                                value = -value
                            total_item_percent += value

            result = char_value + total_item_percent
            return f"{result}%"
        except (AttributeError, ValueError) as e:
            print(f"Error in calculate_percentage_stat: {e}")
            return f"{char_value}%" if char_value else "N/A"

    def calculate_special_stat(self, stat, char_base_value, item_value):
        try:
            parts = self._split_item_value(str(item_value).lstrip('+'))
            total_item_value = 0
            for part in parts:
                if part and part.strip():
                    total_item_value += float(part)

            base_stat = ("力量 (Strength)" if stat == "物理攻击力 (Physical Attack Power)" 
                        else "智力 (Intelligence)")
            total_base_stat = float(self.calculate_result(base_stat))
            
            result = (total_base_stat / 250) * total_item_value + total_item_value
            return int(result)
        except (ValueError, AttributeError) as e:
            print(f"Error in calculate_special_stat for {stat}: {e}")
            return int(char_base_value) if char_base_value else "N/A"

    def calculate_critical_damage(self, base_damage, crit_bonus):
        try:
            base = float(base_damage or 0)
            bonus = float(crit_bonus or 0) / 100
            result = base * (1.5 + bonus)
            return f"{result:.2f}"
        except ValueError:
            return "Invalid input"

    def calculate_damage_difference(self, damage1, damage2):
        try:
            d1 = float(damage1 or 0)
            d2 = float(damage2 or 0)
            if d2 == 0:
                return "N/A" if d1 == 0 else "∞"
            difference = ((d1 - d2) / d2) * 100
            return f"{difference:.2f}%"
        except ValueError:
            return "Invalid input"

    _split_item_value = re.compile(r'\+').split
    _extract_percentage = re.compile(r'(\d+\.?\d*)%')


class ResultWindow(ctk.CTkToplevel):
    def __init__(self, parent, item_stats, character_stats, language):
        super().__init__(parent)
        self.title("Result")
        self.geometry("1200x700")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.current_language = language
        self.item_stats = item_stats
        self.character_stats = character_stats
        self.parent = parent
        self.calculator = StatCalculator(parent, item_stats, character_stats)
        self.accent_color = "#00B4D8"

        self.configure(fg_color="#1C2526")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Define fonts
        self.chinese_label_font = ctk.CTkFont(family="Microsoft YaHei", size=13)  # Không bold, size 13
        self.label_font = ctk.CTkFont(family="Poppins", size=15)  # Tiêu đề size 15, không bold
        self.entry_font = ctk.CTkFont(family="Poppins", size=13)  # Size 13, không bold

        # --- Top Frame (Language Switch) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.lang_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.lang_frame.grid(row=0, column=1, sticky="e")

        self.lang_toggle = ctk.CTkSwitch(self.lang_frame, text="CN", command=self.toggle_language,
                                         font=self.entry_font, onvalue=1, offvalue=0,
                                         fg_color="#6B7280", progress_color=self.accent_color)
        self.lang_toggle.grid(row=0, column=0, padx=10, pady=5)
        self.lang_toggle.select() if self.current_language == "zh-cn" else self.lang_toggle.deselect()

        # --- Main Frame ---
        self.frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2B3031")
        self.frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.create_result_ui()

    def create_result_ui(self):
        headers = [("", "Item Stat", "Result", "", "Item Stat", "Result")]
        for col, text in enumerate(headers[0]):
            header_label = ctk.CTkLabel(self.frame, text=text, font=self.label_font,
                                        text_color=self.accent_color if col in (1, 4) else "#22C55E" if col in (2, 5) else "#FFFFFF")
            header_label.grid(row=0, column=col, padx=5, pady=(10, 5), sticky="n")

        stats_layout = [
            ("生命值 (HP)", "魔法值 (MP)"),
            ("力量 (Strength)", "智力 (Intelligence)"),
            ("体力 (Physical Strength)", "精神 (Spirit)"),
            ("物理攻击力 (Physical Attack Power)", "魔法攻击力 (Magical Attack Power)"),
            ("物理防御力 (Physical Defense)", "魔法防御力 (Magical Defense)"),
            ("物理暴击 (Physical Critical Hit)", "魔法暴击 (Magical Critical Hit)"),
            ("攻击速度 (Attack Speed)", "施法速度 (Casting Speed)"),
            ("移动速度 (Movement Speed)", None),
            ("火属性强化 (Fire Enhance)", "火属性抗性 (Fire Resistance)"),
            ("光属性强化 (Light Enhance)", "冰属性抗性 (Ice Resistance)"),
            ("冰属性强化 (Ice Enhance)", "光属性抗性 (Light Resistance)"),
            ("暗属性强化 (Dark Enhance)", "暗属性抗性 (Dark Resistance)")
        ]

        stat_display_map = {s[0]: (s[1], s[2]) for s in App.stats}
        results = {stat: self.calculator.calculate_result(stat) for stat in stat_display_map}
        item_values = {stat: self.calculator.get_item_value(stat) for stat in stat_display_map}

        widgets = []
        for row, (stat1, stat2) in enumerate(stats_layout, start=1):
            if stat1:
                display_stat1 = stat_display_map[stat1][0 if self.current_language == "zh-cn" else 1]
                item_border_color1 = self.accent_color if item_values[stat1] else "#6B7280"
                result_border_color1 = self.accent_color if stat1 in self.item_stats and results[stat1] != "N/A" else "#6B7280"
                widgets.extend([
                    (ctk.CTkLabel, {"text": display_stat1, "font": self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font, "text_color": "#D9D9D9"}, 
                     {"row": row, "column": 0, "padx": 5, "pady": 8, "sticky": "w"}, None),
                    (ctk.CTkEntry, {"width": 120, "placeholder_text": "", "fg_color": "#3A3A40", "border_color": item_border_color1, "text_color": "#FFFFFF", "font": self.entry_font}, 
                     {"row": row, "column": 1, "padx": 5, "pady": 8}, item_values[stat1]),
                    (ctk.CTkEntry, {"width": 120, "placeholder_text": "", "fg_color": "#3A3A40", "border_color": result_border_color1, "text_color": "#FFFFFF", "font": self.entry_font}, 
                     {"row": row, "column": 2, "padx": 5, "pady": 8}, results[stat1])
                ])

            if stat2:
                display_stat2 = stat_display_map[stat2][0 if self.current_language == "zh-cn" else 1]
                item_border_color2 = self.accent_color if item_values[stat2] else "#6B7280"
                result_border_color2 = self.accent_color if stat2 in self.item_stats and results[stat2] != "N/A" else "#6B7280"
                widgets.extend([
                    (ctk.CTkLabel, {"text": display_stat2, "font": self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font, "text_color": "#D9D9D9"}, 
                     {"row": row, "column": 3, "padx": 5, "pady": 8, "sticky": "w"}, None),
                    (ctk.CTkEntry, {"width": 120, "placeholder_text": "", "fg_color": "#3A3A40", "border_color": item_border_color2, "text_color": "#FFFFFF", "font": self.entry_font}, 
                     {"row": row, "column": 4, "padx": 5, "pady": 8}, item_values[stat2]),
                    (ctk.CTkEntry, {"width": 120, "placeholder_text": "", "fg_color": "#3A3A40", "border_color": result_border_color2, "text_color": "#FFFFFF", "font": self.entry_font}, 
                     {"row": row, "column": 5, "padx": 5, "pady": 8}, results[stat2])
                ])

        for widget_cls, kwargs, grid_kwargs, value in widgets:
            widget = widget_cls(self.frame, **kwargs)
            widget.grid(**grid_kwargs)
            if widget_cls == ctk.CTkEntry and value is not None:  
                widget.insert(0, str(value) if value else "")
                widget.configure(state="disabled")

    def toggle_language(self):
        self.current_language = "zh-cn" if self.lang_toggle.get() else "en"
        self.lang_toggle.configure(text="CN" if self.current_language == "zh-cn" else "EN")
        self.update_labels()

    def show_tooltip(self, event, message):
        self.tooltip = ctk.CTkLabel(self, text=message, fg_color="#4a4a4a", text_color="white",
                                    corner_radius=5, padx=5, pady=2, font=self.entry_font)
        self.tooltip.place(x=event.widget.winfo_rootx() - self.winfo_rootx() + 10,
                          y=event.widget.winfo_rooty() - self.winfo_rooty() + 30)

    def hide_tooltip(self, event):
        if hasattr(self, "tooltip"):
            self.tooltip.destroy()
            del self.tooltip

    def translate_stat(self, stat):
        for listbox_stat, cn_stat, en_stat in App.stats:
            if listbox_stat == stat:
                return cn_stat if self.current_language == "zh-cn" else en_stat
        return stat

    def update_labels(self):
        for widget in self.frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") not in ("Item Stat", "Result", ""):
                current_text = widget.cget("text")
                for listbox_stat, cn_stat, en_stat in App.stats:
                    if current_text in (cn_stat, en_stat):
                        widget.configure(text=self.translate_stat(listbox_stat), 
                                        font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font)
                        break


class App(ctk.CTk):
    stats = [
        ("生命值 (HP)", "生命值", "HP"),
        ("魔法值 (MP)", "魔法值", "MP"),
        ("力量 (Strength)", "力量", "Strength"),
        ("智力 (Intelligence)", "智力", "Intelligence"),
        ("体力 (Physical Strength)", "体力", "Physical Strength"),
        ("精神 (Spirit)", "精神", "Spirit"),
        ("物理攻击力 (Physical Attack Power)", "物理攻击力", "Physical Attack Power"),
        ("魔法攻击力 (Magical Attack Power)", "魔法攻击力", "Magical Attack Power"),
        ("物理防御力 (Physical Defense)", "物理防御力", "Physical Defense"),
        ("魔法防御力 (Magical Defense)", "魔法防御力", "Magical Defense"),
        ("物理暴击 (Physical Critical Hit)", "物理暴击", "Physical Critical Hit"),
        ("魔法暴击 (Magical Critical Hit)", "魔法暴击", "Magical Critical Hit"),
        ("攻击速度 (Attack Speed)", "攻击速度", "Attack Speed"),
        ("施法速度 (Casting Speed)", "施法速度", "Casting Speed"),
        ("移动速度 (Movement Speed)", "移动速度", "Movement Speed"),
        ("火属性强化 (Fire Enhance)", "火属性强化", "Fire Enhance"),
        ("冰属性强化 (Ice Enhance)", "冰属性强化", "Ice Enhance"),
        ("光属性强化 (Light Enhance)", "光属性强化", "Light Enhance"),
        ("暗属性强化 (Dark Enhance)", "暗属性强化", "Dark Enhance"),
        ("火属性抗性 (Fire Resistance)", "火属性抗性", "Fire Resistance"),
        ("冰属性抗性 (Ice Resistance)", "冰属性抗性", "Ice Resistance"),
        ("光属性抗性 (Light Resistance)", "光属性抗性", "Light Resistance"),
        ("暗属性抗性 (Dark Resistance)", "暗属性抗性", "Dark Resistance")
    ]

    def __init__(self):
        super().__init__()
        self.title("Stat Calculator")
        self.geometry("1100x600")
        self.resizable(True, True)
        self.minsize(1000, 550)

        ctk.set_appearance_mode("Dark")
        self.configure(fg_color="#1C2526")
        self.accent_color = "#00B4D8"

        # --- Initialize Data ---
        self.translator = Translator()
        self.current_language = "zh-cn"
        self.calculator = StatCalculator(self)
        self.item_stats_data = {}
        self.character_stats_data = {}

        self.database_file = "config.json"
        if os.path.exists(self.database_file):
            with open(self.database_file, "r", encoding='utf-8') as f:
                self.database = json.load(f)
        else:
            self.database = {"items": {}, "characters": {}}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Define fonts
        self.chinese_label_font = ctk.CTkFont(family="Microsoft YaHei", size=13)  # Không bold, size 13
        self.label_font = ctk.CTkFont(family="Poppins", size=15)  # Tiêu đề size 15, không bold
        self.entry_font = ctk.CTkFont(family="Poppins", size=13)  # Size 13, không bold
        self.button_font = ctk.CTkFont(family="Poppins", size=13)  # Size 13 cho nút, không bold
        self.tab_font = ctk.CTkFont(family="Poppins", size=15)  # Tab size 15, không bold

        # --- Top Frame (Language Switch) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.lang_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.lang_frame.grid(row=0, column=1, sticky="e")
        self.lang_toggle = ctk.CTkSwitch(self.lang_frame, text="CN", command=self.toggle_language,
                                         font=self.entry_font, text_color="#D9D9D9",
                                         fg_color="#6B7280", progress_color=self.accent_color)
        self.lang_toggle.grid(row=0, column=0, padx=10, pady=5)
        self.lang_toggle.select()

        # --- Center Frame (Tabs) ---
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(
            self.center_frame,
            height=500,
            fg_color="#1C2526",
            corner_radius=10,
            segmented_button_fg_color="#2B3031",
            segmented_button_selected_color=self.accent_color,
            segmented_button_selected_hover_color="#0284C7",
            segmented_button_unselected_color="#3A3A40",
            segmented_button_unselected_hover_color="#4B4B50",
            text_color="#FFFFFF"
        )
        self.tab_view.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.tab_view.add("Default")
        self.tab_view.add("Damage")

        for btn in self.tab_view._segmented_button._buttons_dict.values():
            btn.configure(font=self.tab_font)

        self.selected_stats = []
        self.create_default_tab()
        self.create_damage_tab()

    def create_default_tab(self):
        tab_frame = self.tab_view.tab("Default")
        tab_frame.grid_columnconfigure(0, weight=0)
        tab_frame.grid_columnconfigure(1, weight=1)
        tab_frame.grid_columnconfigure(2, weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)

        # Side 1: Stat Selection
        self.side_1_frame = ctk.CTkFrame(tab_frame, corner_radius=10, fg_color="#2B3031")
        self.side_1_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        title = ctk.CTkLabel(self.side_1_frame, text="Stat Selection", font=self.label_font, text_color=self.accent_color)
        title.grid(row=0, column=0, pady=(10, 5), padx=10)

        self.filter_entry = ctk.CTkEntry(self.side_1_frame, placeholder_text="Filter Stats...", width=220,
                                         border_width=1, corner_radius=8, fg_color="#3A3A40", border_color="#6B7280", text_color="#FFFFFF", font=self.entry_font)
        self.filter_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.filter_entry.bind("<KeyRelease>", self.filter_stats)

        self.listbox = CTkListbox(self.side_1_frame, multiple_selection=True, height=300, width=220,
                                  font=self.entry_font, border_width=1, corner_radius=8, fg_color="#3A3A40", border_color="#6B7280", text_color="#D9D9D9")
        self.listbox.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        for i, (listbox_stat, _, _) in enumerate(self.stats):
            self.listbox.insert(i, listbox_stat)

        self.side_1_frame.grid_rowconfigure(2, weight=1)

        button_frame = ctk.CTkFrame(self.side_1_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.add_button = ctk.CTkButton(button_frame, text="Add \u2795", width=100, command=self.on_add,
                                        font=self.button_font, corner_radius=8, fg_color=self.accent_color, hover_color="#0284C7", text_color="#FFFFFF")
        self.add_button.grid(row=0, column=0, padx=5)

        self.refresh_btn = ctk.CTkButton(button_frame, text="Reset \u21BB", width=100, command=self.unselect_all,
                                         font=self.button_font, corner_radius=8, fg_color="#6B7280", hover_color="#4B4B50", text_color="#FFFFFF")
        self.refresh_btn.grid(row=0, column=1, padx=5)

        # Side 2: Item Stats
        self.side_2_frame = ctk.CTkScrollableFrame(tab_frame, corner_radius=10, fg_color="#2B3031")
        self.side_2_frame.grid(row=0, column=1, padx=(10, 5), pady=10, sticky="nsew")

        title_item = ctk.CTkLabel(self.side_2_frame, text="Item Stats", font=self.label_font, text_color=self.accent_color)
        title_item.grid(row=0, column=0, columnspan=3, pady=(0, 5), padx=10)

        self.item_index_entry = ctk.CTkEntry(self.side_2_frame, placeholder_text="Enter Item Index", width=220,
                                             border_width=1, corner_radius=8, fg_color="#3A3A40", border_color="#6B7280", text_color="#FFFFFF", font=self.entry_font)
        self.item_index_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.item_load_btn = ctk.CTkButton(self.side_2_frame, text="OK", width=30, command=self.load_item_stats,
                                           font=self.button_font, corner_radius=8, fg_color=self.accent_color, hover_color="#0284C7", text_color="#FFFFFF")
        self.item_load_btn.grid(row=1, column=2, padx=10, pady=5)

        # Side 3: Character Stats
        self.side_3_frame = ctk.CTkScrollableFrame(tab_frame, corner_radius=10, fg_color="#2B3031")
        self.side_3_frame.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")

        title_char = ctk.CTkLabel(self.side_3_frame, text="Character Stats", font=self.label_font, text_color=self.accent_color)
        title_char.grid(row=0, column=0, columnspan=3, pady=(0, 5), padx=10)

        self.char_name_entry = ctk.CTkEntry(self.side_3_frame, placeholder_text="Enter Character Name", width=220,
                                            border_width=1, corner_radius=8, fg_color="#3A3A40", border_color="#6B7280", text_color="#FFFFFF", font=self.entry_font)
        self.char_name_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.char_load_btn = ctk.CTkButton(self.side_3_frame, text="OK", width=30, command=self.load_character_stats,
                                           font=self.button_font, corner_radius=8, fg_color=self.accent_color, hover_color="#0284C7", text_color="#FFFFFF")
        self.char_load_btn.grid(row=1, column=2, padx=10, pady=5)

        # Result Frame
        self.side_4_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
        self.side_4_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=(5, 10), sticky="nsew")
        self.side_4_frame.grid_columnconfigure(0, weight=1)
        self.side_4_frame.grid_columnconfigure((1, 2), weight=0)

        self.result_label = ctk.CTkLabel(self.side_4_frame, text="", font=self.entry_font, text_color="#D9D9D9")
        self.result_label.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        self.save_btn = ctk.CTkButton(self.side_4_frame, text="Save", width=100, command=self.save_database,
                                      font=self.button_font, corner_radius=8, fg_color=self.accent_color, hover_color="#0284C7", text_color="#FFFFFF")
        self.save_btn.grid(row=0, column=1, padx=5, pady=10)

        self.result_btn = ctk.CTkButton(self.side_4_frame, text="Result", width=100, command=self.show_result,
                                        font=self.button_font, corner_radius=8, fg_color=self.accent_color, hover_color="#0284C7", text_color="#FFFFFF")
        self.result_btn.grid(row=0, column=2, padx=5, pady=10)

        self.item_stats_entries = []
        self.item_stat_labels = []
        self.item_remove_buttons = []
        self.character_stats_entries = []
        self.character_stat_labels = []
        self.character_remove_buttons = []

    def create_damage_tab(self):
        tab_frame = self.tab_view.tab("Damage")
        tab_frame.grid_columnconfigure((0, 1), weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)

        # Side 1: Critical Damage
        self.critical_frame = ctk.CTkFrame(tab_frame, corner_radius=15, fg_color="#2B3031")
        self.critical_frame.grid(row=0, column=0, padx=(15, 7.5), pady=15, sticky="nsew")

        critical_title = ctk.CTkLabel(self.critical_frame, text="Critical Damage", font=self.label_font, text_color=self.accent_color)
        critical_title.grid(row=0, column=0, columnspan=2, pady=(15, 10))

        base_damage_label = ctk.CTkLabel(self.critical_frame, text="Base Damage", font=self.entry_font, text_color="#D9D9D9")
        base_damage_label.grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.base_damage_entry = ctk.CTkEntry(self.critical_frame, width=150, placeholder_text="e.g., 100",
                                              font=self.entry_font, border_color="#6B7280", fg_color="#3A3A40", text_color="#FFFFFF", corner_radius=8)
        self.base_damage_entry.grid(row=1, column=1, padx=15, pady=10)
        self.base_damage_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter the base damage value"))
        self.base_damage_entry.bind("<Leave>", self.hide_tooltip)

        crit_bonus_label = ctk.CTkLabel(self.critical_frame, text="Critical Bonus (%)", font=self.entry_font, text_color="#D9D9D9")
        crit_bonus_label.grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.crit_bonus_entry = ctk.CTkEntry(self.critical_frame, width=150, placeholder_text="e.g., 20",
                                             font=self.entry_font, border_color="#6B7280", fg_color="#3A3A40", text_color="#FFFFFF", corner_radius=8)
        self.crit_bonus_entry.grid(row=2, column=1, padx=15, pady=10)
        self.crit_bonus_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter bonus as percentage (e.g., 20 for 20%)"))
        self.crit_bonus_entry.bind("<Leave>", self.hide_tooltip)

        crit_result_label = ctk.CTkLabel(self.critical_frame, text="Result", font=self.entry_font, text_color="#D9D9D9")
        crit_result_label.grid(row=3, column=0, padx=15, pady=10, sticky="w")
        self.crit_result_entry = ctk.CTkEntry(self.critical_frame, width=150, placeholder_text="N/A", state="disabled",
                                              font=self.entry_font, border_color=self.accent_color, fg_color="#3A3A40", text_color="#FFFFFF", corner_radius=8)
        self.crit_result_entry.grid(row=3, column=1, padx=15, pady=10)

        button_frame_crit = ctk.CTkFrame(self.critical_frame, fg_color="transparent")
        button_frame_crit.grid(row=4, column=0, columnspan=2, pady=15)
        crit_calc_button = ctk.CTkButton(button_frame_crit, text="Calculate", command=self.calculate_critical_damage,
                                         font=self.button_font, width=100, fg_color=self.accent_color, hover_color="#0284C7", text_color="#FFFFFF", corner_radius=8)
        crit_calc_button.grid(row=0, column=0, padx=5)
        crit_reset_button = ctk.CTkButton(button_frame_crit, text="Reset \u21BB", command=self.reset_critical_damage,
                                          font=self.button_font, width=100, fg_color="#6B7280", hover_color="#4B4B50", text_color="#FFFFFF", corner_radius=8)
        crit_reset_button.grid(row=0, column=1, padx=5)

        # Side 2: Damage Difference
        self.damage_frame = ctk.CTkFrame(tab_frame, corner_radius=15, fg_color="#2B3031")
        self.damage_frame.grid(row=0, column=1, padx=(7.5, 15), pady=15, sticky="nsew")

        damage_title = ctk.CTkLabel(self.damage_frame, text="Damage Difference", font=self.label_font, text_color=self.accent_color)
        damage_title.grid(row=0, column=0, columnspan=2, pady=(15, 10))

        damage_item1_label = ctk.CTkLabel(self.damage_frame, text="Damage Item 1", font=self.entry_font, text_color="#D9D9D9")
        damage_item1_label.grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.damage_item1_entry = ctk.CTkEntry(self.damage_frame, width=150, placeholder_text="e.g., 120",
                                               font=self.entry_font, border_color="#6B7280", fg_color="#3A3A40", text_color="#FFFFFF", corner_radius=8)
        self.damage_item1_entry.grid(row=1, column=1, padx=15, pady=10)
        self.damage_item1_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter damage for Item 1"))
        self.damage_item1_entry.bind("<Leave>", self.hide_tooltip)

        damage_item2_label = ctk.CTkLabel(self.damage_frame, text="Damage Item 2", font=self.entry_font, text_color="#D9D9D9")
        damage_item2_label.grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.damage_item2_entry = ctk.CTkEntry(self.damage_frame, width=150, placeholder_text="e.g., 100",
                                               font=self.entry_font, border_color="#6B7280", fg_color="#3A3A40", text_color="#FFFFFF", corner_radius=8)
        self.damage_item2_entry.grid(row=2, column=1, padx=15, pady=10)
        self.damage_item2_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter damage for Item 2"))
        self.damage_item2_entry.bind("<Leave>", self.hide_tooltip)

        damage_diff_label = ctk.CTkLabel(self.damage_frame, text="Difference (%)", font=self.entry_font, text_color="#D9D9D9")
        damage_diff_label.grid(row=3, column=0, padx=15, pady=10, sticky="w")
        self.damage_diff_entry = ctk.CTkEntry(self.damage_frame, width=150, placeholder_text="N/A", state="disabled",
                                              font=self.entry_font, border_color=self.accent_color, fg_color="#3A3A40", text_color="#FFFFFF", corner_radius=8)
        self.damage_diff_entry.grid(row=3, column=1, padx=15, pady=10)

        button_frame_diff = ctk.CTkFrame(self.damage_frame, fg_color="transparent")
        button_frame_diff.grid(row=4, column=0, columnspan=2, pady=15)
        damage_calc_button = ctk.CTkButton(button_frame_diff, text="Calculate", command=self.calculate_damage_difference,
                                           font=self.button_font, width=100, fg_color=self.accent_color, hover_color="#0284C7", text_color="#FFFFFF", corner_radius=8)
        damage_calc_button.grid(row=0, column=0, padx=5)
        damage_reset_button = ctk.CTkButton(button_frame_diff, text="Reset \u21BB", command=self.reset_damage_difference,
                                            font=self.button_font, width=100, fg_color="#6B7280", hover_color="#4B4B50", text_color="#FFFFFF", corner_radius=8)
        damage_reset_button.grid(row=0, column=1, padx=5)

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

    def show_tooltip(self, event, message):
        self.tooltip = ctk.CTkLabel(self, text=message, fg_color="#4B4B50", text_color="#FFFFFF",
                                    corner_radius=5, padx=5, pady=2, font=self.entry_font)
        self.tooltip.place(x=event.widget.winfo_rootx() - self.winfo_rootx() + 10,
                          y=event.widget.winfo_rooty() - self.winfo_rooty() + 30)

    def hide_tooltip(self, event):
        if hasattr(self, "tooltip"):
            self.tooltip.destroy()
            del self.tooltip

    def filter_stats(self, event=None):
        if not self.winfo_exists():
            return
        
        filter_text = self.filter_entry.get().lower()
        current_selected_indices = self.listbox.curselection()
        current_selected_stats = {self.listbox.get(i) for i in current_selected_indices}

        for _ in range(self.listbox.size()):
            self.listbox.delete(0)

        filtered_stats = [
            (listbox_stat, cn, en) for listbox_stat, cn, en in self.stats 
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
                self.listbox.deselect(i)
            self.update_idletasks()
        except Exception as e:
            print(f"Error in unselect_all: {e}")

    def on_add(self):
        if not self.winfo_exists():
            return
        try:
            selected_indices = self.listbox.curselection()
            selected_stats = [self.listbox.get(i) for i in selected_indices]
            
            for stat in selected_stats:
                if stat not in self.selected_stats:
                    self.selected_stats.append(stat)
                    self.add_stat_to_ui(stat, len(self.selected_stats) - 1)
        except Exception as e:
            print(f"Error in on_add: {e}")

    def add_stat_to_ui(self, stat, index):
        if not self.winfo_exists():
            return
        row = index + 2
        listbox_stat, cn_stat, en_stat = next((l, c, e) for l, c, e in self.stats if l == stat)
        display_stat = cn_stat if self.current_language == "zh-cn" else en_stat

        # Item side
        item_label = ctk.CTkLabel(self.side_2_frame, text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font, text_color="#D9D9D9")
        item_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        item_entry = ctk.CTkEntry(self.side_2_frame, width=120, border_width=1, corner_radius=8, fg_color="#3A3A40", border_color="#6B7280", text_color="#FFFFFF", font=self.entry_font)
        item_entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        if stat in self.item_stats_data:
            item_entry.insert(0, self.item_stats_data[stat])
        item_entry.bind("<KeyRelease>", lambda e, s=stat: self.update_item_data(s, e.widget.get()))
        
        item_remove = ctk.CTkButton(self.side_2_frame, text="−", width=30, command=lambda: self.remove_stat(index),
                                    fg_color="#EF4444", hover_color="#B91C1C", text_color="#FFFFFF", corner_radius=8, font=self.button_font)
        item_remove.grid(row=row, column=2, padx=10, pady=5)

        # Character side
        char_label = ctk.CTkLabel(self.side_3_frame, text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font, text_color="#D9D9D9")
        char_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        char_entry = ctk.CTkEntry(self.side_3_frame, width=120, border_width=1, corner_radius=8, fg_color="#3A3A40", border_color="#6B7280", text_color="#FFFFFF", font=self.entry_font)
        char_entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        if stat in self.character_stats_data:
            char_entry.insert(0, self.character_stats_data[stat])
        char_entry.bind("<KeyRelease>", lambda e, s=stat: self.update_character_data(s, e.widget.get()))
        
        char_remove = ctk.CTkButton(self.side_3_frame, text="−", width=30, command=lambda: self.remove_stat(index),
                                    fg_color="#EF4444", hover_color="#B91C1C", text_color="#FFFFFF", corner_radius=8, font=self.button_font)
        char_remove.grid(row=row, column=2, padx=10, pady=5)

        self.item_stat_labels.append(item_label)
        self.item_stats_entries.append(item_entry)
        self.item_remove_buttons.append(item_remove)
        self.character_stat_labels.append(char_label)
        self.character_stats_entries.append(char_entry)
        self.character_remove_buttons.append(char_remove)

    def update_item_data(self, stat, value):
        if value:
            self.item_stats_data[stat] = value
        elif stat in self.item_stats_data:
            del self.item_stats_data[stat]

    def update_character_data(self, stat, value):
        if value:
            self.character_stats_data[stat] = value
        elif stat in self.character_stats_data:
            del self.character_stats_data[stat]

    def remove_stat(self, index):
        if not self.winfo_exists():
            return
        if 0 <= index < len(self.selected_stats):
            removed_stat = self.selected_stats.pop(index)
            
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

    def toggle_language(self):
        if not self.winfo_exists():
            return
        self.current_language = "zh-cn" if self.lang_toggle.get() else "en"
        self.lang_toggle.configure(text="CN" if self.current_language == "zh-cn" else "EN")
        self.update_labels()

    def update_labels(self):
        if not self.winfo_exists():
            return
        for i, stat in enumerate(self.selected_stats):
            _, cn_stat, en_stat = next((l, c, e) for l, c, e in self.stats if l == stat)
            display_stat = cn_stat if self.current_language == "zh-cn" else en_stat
            
            self.item_stat_labels[i].configure(text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font)
            self.character_stat_labels[i].configure(text=display_stat, font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font)

        for frame in [self.side_1_frame, self.side_2_frame, self.side_3_frame, self.side_4_frame, self.critical_frame, self.damage_frame]:
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel):
                    if widget.cget("text") in ("Stat Selection", "Item Stats", "Character Stats", "Critical Damage", "Damage Difference"):
                        widget.configure(font=self.label_font)
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
                    self.item_stats_entries[-1].insert(0, str(value))
            self.result_label.configure(text=f"Loaded Item Index: {index}")
        else:
            self.result_label.configure(text=f"Item Index '{index}' not found in database.")

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
                    loaded_count += 1
            self.result_label.configure(text=f"Loaded {loaded_count} stats for Character: {name}")
        else:
            self.result_label.configure(text=f"Character '{name}' not found in database.")

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
        
        self.result_label.configure(text="Database saved successfully.")

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
        self.result_label.configure(text="Result window opened.")

    def destroy(self):
        self.listbox = None
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()