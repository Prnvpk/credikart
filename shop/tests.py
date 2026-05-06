from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser

from .models import Product


class ProductListViewTests(TestCase):
    def setUp(self):
        self.customer = CustomUser.objects.create_user(
            username='customer1',
            password='testpass123',
            user_type='customer',
            phone='9999999999',
        )
        self.shopkeeper_one = CustomUser.objects.create_user(
            username='shopkeeper1',
            password='testpass123',
            user_type='shopkeeper',
            phone='8888888881',
        )
        self.shopkeeper_two = CustomUser.objects.create_user(
            username='shopkeeper2',
            password='testpass123',
            user_type='shopkeeper',
            phone='8888888882',
        )
        self.shopkeeper_without_products = CustomUser.objects.create_user(
            username='shopkeeper3',
            password='testpass123',
            user_type='shopkeeper',
            phone='8888888883',
        )

        self.product_one = Product.objects.create(
            shopkeeper=self.shopkeeper_one,
            name='Rice Bag',
            price='1200.00',
            stock_quantity=5,
        )
        self.product_two = Product.objects.create(
            shopkeeper=self.shopkeeper_two,
            name='Cooking Oil',
            price='450.00',
            stock_quantity=9,
        )

    def test_customer_sees_products_from_all_shopkeepers_with_products(self):
        self.client.login(username='customer1', password='testpass123')

        response = self.client.get(reverse('product_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rice Bag')
        self.assertContains(response, 'Cooking Oil')
        self.assertContains(response, 'shopkeeper1')
        self.assertContains(response, 'shopkeeper2')
        self.assertNotContains(response, 'shopkeeper3')

    def test_customer_can_filter_products_by_shopkeeper(self):
        self.client.login(username='customer1', password='testpass123')

        response = self.client.get(
            reverse('product_list'),
            {'shopkeeper': str(self.shopkeeper_one.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rice Bag')
        self.assertNotContains(response, 'Cooking Oil')
        self.assertEqual(response.context['selected_shopkeeper_id'], str(self.shopkeeper_one.id))

    def test_product_list_is_paginated_by_twelve_items(self):
        self.client.login(username='customer1', password='testpass123')

        for index in range(3, 15):
            Product.objects.create(
                shopkeeper=self.shopkeeper_one,
                name=f'Extra Product {index}',
                price='100.00',
                stock_quantity=2,
            )

        response = self.client.get(reverse('product_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.per_page, 12)
        self.assertEqual(len(response.context['products']), 12)
        self.assertTrue(response.context['page_obj'].has_next())
        self.assertContains(response, 'Page 1 of 2')

    def test_pagination_keeps_shopkeeper_filter(self):
        self.client.login(username='customer1', password='testpass123')

        for index in range(3, 16):
            Product.objects.create(
                shopkeeper=self.shopkeeper_one,
                name=f'Filtered Product {index}',
                price='150.00',
                stock_quantity=4,
            )

        response = self.client.get(
            reverse('product_list'),
            {'shopkeeper': str(self.shopkeeper_one.id), 'page': 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_shopkeeper_id'], str(self.shopkeeper_one.id))
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertContains(response, f'shopkeeper={self.shopkeeper_one.id}&amp;page=1', html=False)
