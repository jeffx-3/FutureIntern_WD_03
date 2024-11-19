from django.shortcuts import render,get_object_or_404,redirect
from .models import Category, Product, Cart, CartItem, Order
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

#home view
def home(request):
    return render(request, 'home.html')

#discover view
def discover(request):
    products = Product.objects.all()
    context = {
        'products': products
    }
    return render(request, 'discover.html',context)

#search view
def search(request):
    query = request.GET.get('q', '') # Get the search term from the query parameters
    if query:
        results = Product.objects.filter(name__icontains=query)
    else:
        results = Product.objects.none() # No search results if no query
        
    context = {
        'results': results,
        'query': query,
    }
    return render(request, 'product_search.html', context)


#cart views
def cart(request):
    return render(request, 'cart.html')


# Product List View
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'product_list.html', {'category': category, 'categories': categories, 'products': products})

# Product Detail View
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    return render(request, 'product_detail.html', {'product': product})

# Cart View
@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')  # Optimized query to include product details
    return render(request, 'cart_detail.html', {
        'cart': cart,
        'items': items,
    })

# Add to Cart View
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()

    return redirect('cart_detail')

# Remove from Cart View
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart_detail')

# Checkout View
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    order = Order.objects.create(user=request.user, total_price=calculate_cart_total(cart))
    cart.delete()  
    return render(request, 'checkout.html', {'order': order})

def calculate_cart_total(cart):
    return sum(item.product.price * item.quantity for item in cart.items.all())


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']
        if password == password_confirm:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
            else:
                user = User.objects.create_user(username=username, password=password)
                user.save()
                messages.success(request, 'Account created successfully')
                return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
    return render(request, 'accounts/register.html')



# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        product_id = request.POST.get('product_id')  # Retrieve product_id from POST data
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if product_id:
                return redirect('add_to_cart', product_id=product_id)
            # Fallback
            return redirect('cart_detail')  # Or another suitable default page
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'accounts/login.html')

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')