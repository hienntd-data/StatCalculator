import customtkinter as ctk
from constants import stats
from color_config import ColorConfig
from stat_calculator import StatCalculator

class ResultWindow(ctk.CTkToplevel):
    def __init__(self, parent, item_stats, character_stats, language):
        super().__init__(parent)
        self.title("Result")
        self.geometry("900x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.current_language = language
        self.item_stats = item_stats
        self.character_stats = character_stats
        self.parent = parent
        self.calculator = StatCalculator(parent, item_stats, character_stats)

        self.configure(fg_color=ColorConfig.FG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Define fonts
        self.chinese_label_font = ctk.CTkFont(family="DengXian", size=13, weight='bold')
        self.label_font = ctk.CTkFont(family="Poppins", size=15)
        self.entry_font = ctk.CTkFont(family="Poppins", size=13)

        # Bind Escape key to close window
        self.bind("<Escape>", lambda event: self.close_window())

        # Top Frame (Language Switch)
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.lang_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.lang_frame.grid(row=0, column=1, sticky="e")

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
        self.lang_option.grid(row=0, column=0, padx=10, pady=5)
        self.lang_option.set("Chinese (ZH-CN)" if self.current_language == "zh-cn" else "English (EN)")

        # Main Frame
        self.frame = ctk.CTkFrame(self, corner_radius=15, fg_color=ColorConfig.SECONDARY_FG)
        self.frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.frame.grid_columnconfigure((0,1,2,3), weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_columnconfigure(3, weight=0)

        self.create_result_ui()

    def close_window(self):
        self.destroy()

    def create_result_ui(self):
        LABEL_STYLE = {
            "text_color": ColorConfig.TEXT,
        }

        # Headers
        headers = ["Stat", "Result", "Stat", "Result"]
        for col, text in enumerate(headers):
            header_label = ctk.CTkLabel(
                self.frame,
                text=text,
                font=self.label_font,
                text_color=ColorConfig.ACCENT if col % 2 == 0 else ColorConfig.ACCENT,
            )
            header_label.grid(row=0, column=col, padx=30, pady=(10, 5), sticky="w")

        # Stat layout
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
            ("暗属性强化 (Dark Enhance)", "暗属性抗性 (Dark Resistance)"),
        ]

        stat_display_map = {s[0]: (s[1], s[2]) for s in stats}
        results = {stat: self.calculator.calculate_result(stat) for stat in stat_display_map}

        for row, (stat1, stat2) in enumerate(stats_layout, start=1):
            for idx, stat in enumerate((stat1, stat2)):
                if stat is None:
                    continue

                col_base = 0 if idx == 0 else 2
                display_stat = stat_display_map[stat][0 if self.current_language == "zh-cn" else 1]
                result_border_color = ColorConfig.ACCENT if stat in self.item_stats and results[stat] != "N/A" else ColorConfig.BORDER_DEFAULT

                label = ctk.CTkLabel(
                    self.frame,
                    text=display_stat,
                    font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font,
                    **LABEL_STYLE
                )
                label.grid(row=row, column=col_base, padx=(30,0), pady=6, sticky="w")

                result_entry = ctk.CTkEntry(
                    self.frame,
                    border_color=result_border_color,
                    fg_color=ColorConfig.SECONDARY_FG,
                    text_color=ColorConfig.TEXT,
                    font=self.entry_font,
                    corner_radius=15
                )
                result_entry.grid(row=row, column=col_base + 1, padx=(0,40), pady=6, sticky="w")
                if results[stat]:
                    result_entry.insert(0, str(results[stat]))
                    result_entry.configure(state="disabled")

    def toggle_language_option(self, choice):
        self.current_language = "zh-cn" if choice == "Chinese (ZH-CN)" else "en"
        self.update_labels()


    def translate_stat(self, stat):
        for listbox_stat, cn_stat, en_stat in stats:
            if listbox_stat == stat:
                return cn_stat if self.current_language == "zh-cn" else en_stat
        return stat

    def update_labels(self):
        for widget in self.frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") not in ("Stat", "Result", ""):
                current_text = widget.cget("text")
                for listbox_stat, cn_stat, en_stat in stats:
                    if current_text in (cn_stat, en_stat):
                        widget.configure(
                            text=self.translate_stat(listbox_stat),
                            font=self.chinese_label_font if self.current_language == "zh-cn" else self.entry_font
                        )
                        break