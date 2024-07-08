from django.contrib import admin
from .models import MenuItem, Cart, Order

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price')
    search_fields = ('name', 'description')
    list_filter = ('price',)

admin.site.register(MenuItem, MenuItemAdmin)

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'quantity')
    list_filter = ('user', 'item')

admin.site.register(Cart, CartAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_cost', 'created_at')

admin.site.register(Order, OrderAdmin)
