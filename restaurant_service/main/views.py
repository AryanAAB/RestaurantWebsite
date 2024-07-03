from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import MenuItem, Cart

user = None

def homepage(request):
    return render(request, 'main/homepage.html')

def login_view(request):
    global user
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('menu')
        else:
            return render(request, 'main/login.html', {'invalid_credentials': True})
    else:
        return render(request, 'main/login.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        print(form)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main/signup.html', {'form': form})

@login_required
def logout_view(request):
    global user
    logout(request)
    user = None
    return redirect('homepage')

@login_required
def menu(request):
    if(not user):
        return redirect("homepage")
    menu_items = MenuItem.objects.all()
    return render(request, 'main/menu.html', {'menu_items': menu_items})

@login_required
def search_results(request):
    query = request.GET.get('query')
    menu_items = MenuItem.objects.filter(name__icontains=query)
    context = {
        'menu_items': menu_items,
        'query': query,
    }
    return render(request, 'main/search_results.html', context)

@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, item=item)

    messages.success(request, f"{item.name} added to cart!")

    return redirect('menu')

@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        action = request.POST.get("action")
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        
        if action == "increase":
            cart_item.quantity += 1
        elif action == "decrease" and cart_item.quantity > 1:
            cart_item.quantity -= 1
        cart_item.save()

        messages.success(request, "Cart updated successfully!")
        return redirect('view_cart')
    
    return render(request, 'main/cart.html', {'cart_items': cart_items})

@login_required
def remove_from_cart(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        cart_item.delete()
        messages.success(request, "Item removed from cart successfully!")
    return redirect('view_cart')