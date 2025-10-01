from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import Product
from .models import Order
from .models import OrderItem

import logging
import json 


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    try:
        payload = request.data

        order = Order.objects.create(
            first_name=payload.get('firstname'),
            last_name=payload.get('lastname') if payload.get('lastname') else '',
            phone_number=payload.get('phonenumber'),
            address=payload.get('address')
        )

        raw_products = payload.get('products', [])
        if isinstance(raw_products, str):
            return Response(
                {"error: List was expected with values, but 'str' ​​was obtained"},
                status=status.HTTP_400_BAD_REQUEST
                )
        elif not raw_products:
            return Response(
                {"error: This list cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
                )

        for product_item in raw_products:
            product_id = int(product_item['product'])
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product
            )
    except Exception as error:
        logging.error(error)
    return Response({})