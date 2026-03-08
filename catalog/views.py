from django.shortcuts import render, get_object_or_404
from .models import Product, Category, Tag

def home(request):
    featured_products = Product.objects.filter(is_active=True).order_by('?')[:6]
    categories = Category.objects.all()
    return render(request, 'catalog/home.html', {
        'products': featured_products,
        'categories': categories
    })

def product_list(request):
    products = Product.objects.filter(is_active=True)
    
    category_slug = request.GET.get('categoria')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    tag_slug = request.GET.get('tag')
    if tag_slug:
        products = products.filter(tags__slug=tag_slug)
        
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(name__icontains=search_query)
        
    categories = Category.objects.all()
    tags = Tag.objects.all()

    return render(request, 'catalog/product_list.html', {
        'products': products.distinct(),
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'current_tag': tag_slug,
        'tags': tags,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'catalog/product_detail.html', {'product': product})
