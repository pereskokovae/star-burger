from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from places.views import fetch_coordinates

from foodcartapp.models import Order, Product, Restaurant, RestaurantMenuItem

from geopy import distance

from django.conf import settings


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.with_total_price().prefetch_related(
        'items__product').select_related('restaurant')

    for order in orders:
        if not order.restaurant:
            product_ids = order.items.values_list('product_id', flat=True)
            aviable_restaurants = Restaurant.objects.filter(
                menu_items__product_id__in=product_ids,
                menu_items__availability=True
            )
      
            for aviable_restaurant in aviable_restaurants:
                address = aviable_restaurant.address

                client_address = list(fetch_coordinates(
                    settings.YANDEX_API_KEY,
                    order.address
                ))

                restaurant_address = list(fetch_coordinates(
                    settings.YANDEX_API_KEY,
                    address
                ))
                try:
                    distance_to_restaurant = (distance.distance(
                        client_address,
                        restaurant_address
                    ).km)
                except Exception:
                    order.aviable_restaurants = f'Адрес не найден'
                    continue

                order.available_restaurants = [
                    f'{aviable_restaurant.name} - {distance_to_restaurant} км'
                    ]

    return render(request, 'order_items.html', {'orders': orders})
