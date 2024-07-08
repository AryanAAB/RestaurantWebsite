from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import MenuItem, Cart, Order, OrderItem
from django.http import JsonResponse
from .forms import UserUpdateForm, CustomPasswordChangeForm

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
    if request.method == 'POST':
        item = get_object_or_404(MenuItem, pk=item_id)
        cart_item, created = Cart.objects.get_or_create(user=request.user, item=item)
        
        if created:
            message = f"{item.name} added to cart!"
        else:
            message = f"{item.name} is already in your cart."

        response_data = {
            'message': message,
            'item_id': item_id,
            'item_name': item.name,
        }

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.item.price * item.quantity for item in cart_items)
    return render(request, 'main/cart.html', {'cart_items': cart_items, 'total_amount': total_amount})

@login_required
def update_cart(request):
    item_id = request.POST.get("item_id")
    action = request.POST.get("action")
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    
    if action == "increase":
        cart_item.quantity += 1
    elif action == "decrease" and cart_item.quantity > 1:
        cart_item.quantity -= 1
    elif action == "decrease":
        raise Exception("Cannot decrease quantity. Remove the item instead.")
    cart_item.save()

    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.item.price * item.quantity for item in cart_items)

    return JsonResponse({'quantity': cart_item.quantity, 'total_amount': total_amount, 'message': "Cart updated successfully!"})

@login_required
def remove_from_cart(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        cart_item.delete()
    return redirect('view_cart')

@login_required
def confirm(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.item.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, 'main/confirm.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        if cart_items.exists():
            with transaction.atomic():
                order = Order.objects.create(user=request.user, total_cost=0)
                total_cost = 0
                
                order_items = []
                for cart_item in cart_items:
                    order_items.append(OrderItem(
                        order=order,
                        menu_item=cart_item.item,
                        quantity=cart_item.quantity,
                        price=cart_item.item.price,
                        total=cart_item.item.price * cart_item.quantity,
                    ))
                    total_cost += cart_item.item.price * cart_item.quantity
                
                OrderItem.objects.bulk_create(order_items)
                
                order.total_cost = total_cost
                order.save()
                cart_items.delete()
            return redirect('order_list')
        else:
            return redirect('cart')
    else:
        return redirect('cart')

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/order_history.html', {'orders': orders})

@login_required
def profile(request):
    success = False
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

        if user_form.is_valid() and password_form.is_valid():
            user_form.save()
            user = password_form.save()
            update_session_auth_hash(request, user)
            success = True
    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'main/profile.html', {
        'user_form': user_form,
        'password_form': password_form,
        'success': success
    })