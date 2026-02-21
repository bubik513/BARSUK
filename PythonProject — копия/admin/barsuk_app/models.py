from django.db import models
from django.contrib.auth.models import User
import json
from django.utils import timezone


# Статусы пользователей
class UserStatus(models.TextChoices):
    NEW = 'NEW', 'Новый'
    AGE_PENDING = 'AGE_PENDING', 'Ожидает подтверждения 18+'
    ACTIVE = 'ACTIVE', 'Активный'
    BLOCKED_UNDERAGE = 'BLOCKED_UNDERAGE', 'Заблокирован (младше 18)'
    BLOCKED_ADMIN = 'BLOCKED_ADMIN', 'Заблокирован администратором'
    DELETED = 'DELETED', 'Удален'


class TelegramUser(models.Model):
    """Пользователь Telegram"""
    telegram_id = models.BigIntegerField(unique=True, db_index=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=100, null=True, blank=True, verbose_name="Username")
    first_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Фамилия")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    language_code = models.CharField(max_length=10, default='ru', verbose_name="Язык")

    # Статусы
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.NEW,
        verbose_name="Статус"
    )
    is_18_confirmed = models.BooleanField(default=False, verbose_name="18+ подтверждено")
    consent_accepted = models.BooleanField(default=False, verbose_name="Согласие принято")
    consent_version = models.CharField(max_length=50, null=True, blank=True, verbose_name="Версия согласия")
    consent_accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Время принятия согласия")

    # Дополнительные данные
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    city = models.CharField(max_length=100, default='Тюмень', verbose_name="Город")
    source = models.CharField(max_length=100, null=True, blank=True, verbose_name="Источник")

    # Лояльность
    points = models.IntegerField(default=0, verbose_name="Баллы")
    level = models.CharField(max_length=20, default='Bronze', verbose_name="Уровень")

    # Даты
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    last_activity = models.DateTimeField(default=timezone.now, verbose_name="Последняя активность")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']

    def __str__(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        if name:
            return f"{name} (@{self.username})" if self.username else name
        return f"Пользователь {self.telegram_id}"

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def get_status_color(self):
        colors = {
            UserStatus.NEW: 'gray',
            UserStatus.AGE_PENDING: 'orange',
            UserStatus.ACTIVE: 'green',
            UserStatus.BLOCKED_UNDERAGE: 'red',
            UserStatus.BLOCKED_ADMIN: 'darkred',
            UserStatus.DELETED: 'lightgray',
        }
        return colors.get(self.status, 'gray')


class Event(models.Model):
    """События пользователей"""
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='events', verbose_name="Пользователь")
    event_type = models.CharField(max_length=100, verbose_name="Тип события")
    event_data = models.JSONField(null=True, blank=True, verbose_name="Данные события")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Время события")

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user}"

    def get_event_data_display(self):
        if self.event_data:
            return json.dumps(self.event_data, ensure_ascii=False, indent=2)
        return ""


class Request(models.Model):
    """Заявки (трансфер, менеджер)"""
    REQUEST_TYPES = [
        ('transfer', 'Трансфер'),
        ('manager', 'Менеджер'),
    ]

    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('done', 'Выполнена'),
        ('cancel', 'Отменена'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='requests',
                             verbose_name="Пользователь")
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name="Тип заявки")
    data = models.JSONField(verbose_name="Данные заявки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    manager_notes = models.TextField(null=True, blank=True, verbose_name="Заметки менеджера")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_requests', verbose_name="Ответственный", db_column='assigned_to')

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['request_type']),
        ]

    def __str__(self):
        return f"Заявка #{self.id} - {self.get_request_type_display()}"

    def get_data_display(self):
        """Красивое отображение данных заявки"""
        if not self.data:
            return ""

        display = []

        if self.request_type == 'transfer':
            display.append(f"📍 Адрес: {self.data.get('address', 'Не указан')}")
            display.append(f"📅 Дата: {self.data.get('date', 'Не указана')}")
            display.append(f"🕐 Время: {self.data.get('time', 'Не указано')}")
            display.append(f"👥 Гостей: {self.data.get('guests', 'Не указано')}")
            if self.data.get('comment'):
                display.append(f"💬 Комментарий: {self.data['comment']}")

        elif self.request_type == 'manager':
            display.append(f"💬 Сообщение: {self.data.get('message', 'Не указано')}")

        return "\n".join(display)

    def get_status_color(self):
        colors = {
            'new': 'orange',
            'in_progress': 'blue',
            'done': 'green',
            'cancel': 'red',
        }
        return colors.get(self.status, 'gray')

    @property
    def is_new(self):
        return self.status == 'new'

    @property
    def user_info(self):
        """Информация о пользователе из данных заявки"""
        return self.data.get('user_info', {})

    def request_type_display(self):
        icons = {
            'transfer': '🚖 Трансфер',
            'manager': '💬 Менеджер',
        }
        return icons.get(self.request_type, self.request_type)

    request_type_display.short_description = 'Тип заявки'

    def status_colored(self):
        colors = {
            'new': 'orange',
            'in_progress': 'blue',
            'done': 'green',
            'cancel': 'red',
        }
        color = colors.get(self.status, 'gray')
        from django.utils.html import format_html
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            self.get_status_display()
        )

    status_colored.short_description = 'Статус'

    def is_new_badge(self):
        if self.status == 'new':
            from django.utils.html import format_html
            return format_html(
                '<span style="background-color: orange; color: white; padding: 2px 6px; border-radius: 10px; font-size: 12px;">НОВАЯ</span>'
            )
        return ''

    is_new_badge.short_description = 'Новая?'


# Модель для контента (меню/программы)
class ContentCategory(models.Model):
    """Категории контента"""
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Категория контента"
        verbose_name_plural = "Категории контента"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ContentItem(models.Model):
    """Позиции контента (меню)"""
    category = models.ForeignKey(ContentCategory, on_delete=models.CASCADE, related_name='items',
                                 verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена")
    image = models.ImageField(upload_to='content/', null=True, blank=True, verbose_name="Изображение")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Позиция контента"
        verbose_name_plural = "Позиции контента"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def price_display(self):
        if self.price:
            return f"{self.price} ₽"
        return "Цена по запросу"