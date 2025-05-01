import re
from constants import stats

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
        return ""

    def calculate_result(self, stat):
        item_value = self.get_item_value(stat)
        char_value = self.get_character_value(stat)
        
        try:
            char_value = float(char_value.replace('%', '')) if '%' in str(char_value) else float(char_value or "")
        except ValueError:
            char_value = ""

        if not item_value:
            return f"" if stat in self.percentage_stats and char_value != "" else int(char_value) if char_value != "" else ""

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

    def search_items(self, selected_stats, selected_class):
        matched_items = []
        
        # Duyệt qua tất cả vật phẩm trong cơ sở dữ liệu
        for item_index, item_data in self.parent.database["items"].items():
            # Lấy class của vật phẩm, mặc định là "All" nếu không có
            item_class = item_data.get("class", "All")
            
            # Kiểm tra class trước: chỉ tiếp tục nếu class hợp lệ
            if selected_class != "All" and item_class != "All" and selected_class != item_class:
                continue  # Bỏ qua vật phẩm nếu class không khớp
            
            # Lấy stats của vật phẩm
            item_stats = item_data.get("stats", {})
            
            # Kiểm tra xem tất cả selected_stats có trong item_stats không
            if all(stat in item_stats for stat in selected_stats):
                matched_items.append((item_index, item_data))
        
        return matched_items

    _split_item_value = re.compile(r'\+').split
    _extract_percentage = re.compile(r'(\d+\.?\d*)%')