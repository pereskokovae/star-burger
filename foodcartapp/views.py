from django.http import JsonResponse
from django.templatetags.static import static
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import Product
from .models import Order
from .models import OrderItem

import logging
import re 


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

        first_name = payload.get('firstname')
        last_name = payload.get('lastname') if payload.get('lastname') else ''
        phone_number = payload.get('phonenumber')
        address = payload.get('address')
        raw_products = payload.get('products', [])

        formatted_number = re.match(
            r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            phone_number
            )

        if not first_name or isinstance(first_name, list):
            return Response({
                "error: firstname key not presented or not str"},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif not phone_number or not address:
            return Response({
                "error: This field cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif not formatted_number:
            return Response({
                "error: an incorrect phone nose was introduced"},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif not raw_products or isinstance(raw_products, str):
            return Response(
                {"error: product key not presented or not list"},
                status=status.HTTP_400_BAD_REQUEST
                )

        product_list = []
        for product_item in raw_products:
            product_id = int(product_item['product'])
            try:
                product = Product.objects.get(id=product_id)
                product_list.append(product)
            except ObjectDoesNotExist:
                return Response({
                    "error: Product not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address
        )

        for product in product_list:
            OrderItem.objects.create(
                order=order,
                product=product
            )

    except Exception as error:
        logging.error(error)
    return Response({})