import sqlite3
import datetime
import platform
import keyboard  # pip install keyboard
from plyer import notification

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDSwitch
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock

# Настройка звука
try:
    if platform.system() == "Windows":
        import winsound
    else: winsound = None
except: winsound = None

Window.size = (450, 800)

class SubscriptionApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"
        
        # 1. Работа с БД
        self.init_db()

        # 2. Хоткей Alt + Win + Shift + F
        try:
            keyboard.add_hotkey('alt+windows+shift+f', self.open_promo_dialog)
        except: pass

        self.screen = MDScreen()
        self.main_layout = MDBoxLayout(orientation="vertical")

        # --- ВЕРХНЯЯ ПАНЕЛЬ ---
        self.top_bar = MDBoxLayout(orientation="horizontal", size_hint_y=None, height="60dp", padding="15dp")
        self.title_label = MDLabel(text="SubTracker Ultra 💎", font_style="H6", bold=True)
        self.top_bar.add_widget(self.title_label)
        
        # Кнопка PRO
        self.pro_btn = MDIconButton(icon="crown-outline", on_release=self.buy_pro_dialog)
        self.top_bar.add_widget(self.pro_btn)
        self.top_bar.add_widget(MDIconButton(icon="key-star", on_release=self.open_promo_dialog))
        
        # --- БЛОК ВВОДА ---
        self.inputs = MDBoxLayout(orientation="vertical", padding="15dp", spacing="10dp", size_hint_y=None)
        self.inputs.bind(minimum_height=self.inputs.setter('height'))

        self.name_in = MDTextField(hint_text="Название сервиса", mode="rectangle")
        self.price_in = MDTextField(hint_text="Цена (₽)", input_filter="float", mode="rectangle")
        self.date_in = MDTextField(hint_text="Число списания", mode="rectangle")
        
        # Переключатель триала
        t_row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing="10dp")
        t_row.add_widget(MDLabel(text="БЕЗ ТРИАЛА (сразу платно):", theme_text_color="Hint"))
        self.t_switch = MDSwitch(active=False)
        t_row.add_widget(self.t_switch)

        self.inputs.add_widget(self.name_in)
        self.inputs.add_widget(self.price_in)
        self.inputs.add_widget(self.date_in)
        self.inputs.add_widget(t_row)

        add_btn = MDFillRoundFlatButton(
            text="ДОБАВИТЬ В СПИСОК", 
            pos_hint={"center_x": 0.5}, size_hint_x=1, on_release=self.add_sub
        )
        self.inputs.add_widget(add_btn)

        # --- СПИСОК ---
        self.scroll = ScrollView()
        self.list_layout = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None, padding="15dp")
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)

        # --- НИЖНИЙ БАР ---
        self.bottom_bar = MDBoxLayout(size_hint_y=None, height="75dp", md_bg_color=(0.15, 0.1, 0.2, 1), padding="15dp")
        self.total_label = MDLabel(text="Итого: 0 ₽", font_style="Subtitle1", bold=True)
        self.bottom_bar.add_widget(self.total_label)
        
        self.main_layout.add_widget(self.top_bar)
        self.main_layout.add_widget(self.inputs)
        self.main_layout.add_widget(self.scroll)
        self.main_layout.add_widget(self.bottom_bar)
        
        self.screen.add_widget(self.main_layout)
        self.load_subs()
        self.check_pro_status()
        return self.screen

    def init_db(self):
        self.conn = sqlite3.connect("ultra_subs.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY, name TEXT, price REAL, date TEXT, start_date TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, is_pro INTEGER)")
        self.cursor.execute("SELECT is_pro FROM settings WHERE id=1")
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO settings (id, is_pro) VALUES (1, 0)")
        self.conn.commit()

    def play_sound(self):
        if winsound: winsound.Beep(1500, 400)

    # --- СЕКРЕТКА ---
    def open_promo_dialog(self, *args):
        Clock.schedule_once(self._show_promo)

    def _show_promo(self, dt):
        self.p_field = MDTextField(hint_text="Введите промокод, если знаете какой-нибудь")
        btn = MDRaisedButton(text="ОК", on_release=self.apply_promo)
        self.dialog = MDDialog(title="Секретка 🔑", type="custom", content_cls=self.p_field, buttons=[btn])
        self.dialog.open()

    def apply_promo(self, *args):
        if self.p_field.text.upper() == "KILLTRIAL":
            # Используем 1900 год как флаг завершенного триала
            self.cursor.execute("UPDATE subs SET start_date = '1900-01-01'")
            self.conn.commit()
            self.dialog.dismiss()
            self.load_subs()
            self.play_sound()

    # --- PRO СТАТУС ---
    def buy_pro_dialog(self, *args):
        b1 = MDRaisedButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss())
        b2 = MDRaisedButton(text="КУПИТЬ", on_release=self.activate_pro)
        self.dialog = MDDialog(title="Tracker PRO? 👑", text="Открыть все функции за 99₽?", buttons=[b1, b2])
        self.dialog.open()

    def activate_pro(self, *args):
        self.cursor.execute("UPDATE settings SET is_pro = 1 WHERE id=1")
        self.conn.commit()
        self.dialog.dismiss()
        self.check_pro_status()
        self.play_sound()

    def check_pro_status(self):
        self.cursor.execute("SELECT is_pro FROM settings WHERE id=1")
        if self.cursor.fetchone()[0] == 1:
            self.title_label.text = "SubTracker PRO 👑"
            self.pro_btn.icon = "crown"
            self.pro_btn.icon_color = (1, 0.8, 0, 1)

    # --- ЛОГИКА ТРИАЛА ---
    def add_sub(self, *args):
        if self.name_in.text and self.price_in.text:
            s_date = "1900-01-01" if self.t_switch.active else datetime.datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO subs (name, price, date, start_date) VALUES (?,?,?,?)",
                               (self.name_in.text, float(self.price_in.text), self.date_in.text, s_date))
            self.conn.commit()
            self.name_in.text = self.price_in.text = self.date_in.text = ""
            self.play_sound()
            self.load_subs()

    def load_subs(self):
        self.list_layout.clear_widgets()
        self.cursor.execute("SELECT id, name, price, date, start_date FROM subs")
        total = 0
        now = datetime.datetime.now()
        for sid, name, price, date, s_date in self.cursor.fetchall():
            # ЗАЩИТА: Если в базе старая метка 'PAID', превращаем её в 1900 год
            if s_date == "PAID":
                s_date = "1900-01-01"
            
            try:
                s_dt = datetime.datetime.strptime(s_date, "%Y-%m-%d")
                passed = (now - s_dt).days
                is_trial = passed < 30
            except:
                is_trial = False
                passed = 99
            
            p_now = 0 if is_trial else price
            total += p_now
            
            card = MDCard(padding="12dp", size_hint_y=None, height="110dp", radius=[15,], md_bg_color=(0.12, 0.12, 0.15, 1))
            box = MDBoxLayout(orientation="vertical")
            box.add_widget(MDLabel(text=name.upper(), font_style="H6", bold=True))
            status = f"[ТРИАЛ: {30-passed} дн.]" if is_trial else f"АКТИВНА ({date}-е число)"
            box.add_widget(MDLabel(text=status, theme_text_color="Hint", font_style="Caption"))
            
            r_box = MDBoxLayout(orientation="vertical", size_hint_x=None, width="100dp")
            r_box.add_widget(MDLabel(text=f"{int(p_now)} ₽", bold=True, halign="center"))
            r_box.add_widget(MDIconButton(icon="delete", theme_text_color="Error", on_release=lambda x, i=sid: self.delete_sub(i)))
            
            card.add_widget(box); card.add_widget(r_box); self.list_layout.add_widget(card)
        self.total_label.text = f"Итого к оплате: {int(total)} ₽"

    def delete_sub(self, sid):
        self.cursor.execute("DELETE FROM subs WHERE id=?", (sid,))
        self.conn.commit(); self.load_subs()

if __name__ == "__main__":
    SubscriptionApp().run()
