from rest_framework.pagination import PageNumberPagination

from api.constants import PAGE_SIZE


class CustomPagePagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = 100
