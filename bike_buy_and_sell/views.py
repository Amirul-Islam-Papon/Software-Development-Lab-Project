from datetime import timezone

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse  # Add this import at the top

from .cart import Cart
from .forms import *
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from .models import *


@login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    return render(request, 'logout.html')


def about_view(request):
    return render(request, 'about_us.html')


def contact_view(request):
    return render(request, 'contact_us.html')


def index(request):
    bike_buy_and_sell = BikeBuyAndSell.objects.filter(status="Approved").order_by('-id')
    banner = Banner.objects.all().order_by('-id')
    categories = Category.objects.all().order_by('-id')

    # Include seller's listings if the user is authenticated
    seller_bikes = None
    if request.user.is_authenticated:
        seller_bikes = BikeBuyAndSell.objects.filter(user=request.user).order_by('-id')

    context = {
        'bike_buy_and_sell': bike_buy_and_sell,
        'banners': banner,
        'categories': categories,
        'seller_bikes': seller_bikes,
    }
    return render(request, 'index.html', context=context)


def user_login(request):
    if request.user.is_authenticated:
        return redirect('profile')  # Redirect logged-in users

    form = LoginForm()
    context = {'form': form}
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Logged in successfully')
                return redirect('index')
            else:
                messages.error(request, 'Login failed. Please check your username and password.')
    return render(request, 'login.html', context)


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration.html"


@login_required(login_url='/login/')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to maintain user's session
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


@login_required(login_url='/login')
def profile(request):
    user = request.user
    profile = getattr(user, 'profile', None)  # Get the profile if it exists
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='/login')
def update_profile(request):
    user = request.user
    profile = getattr(user, 'profile', None)  # Get the profile if it exists

    # Initialize the form with the user's current data
    form = ProfileUpdateForm(initial={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    })

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            # Update user fields
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.email = form.cleaned_data.get('email')
            user.save()

            # Update or create the profile
            if profile:
                profile.profile_picture = form.cleaned_data.get('profile_picture') or profile.profile_picture
                profile.save()
            else:
                Profile.objects.create(user=user, profile_picture=form.cleaned_data.get('profile_picture'))

            messages.success(request, "Profile updated successfully!")
            return redirect('profile')

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'update_profile.html', context)


@login_required(login_url='/login')
def booking_list(request):
    booking_list = Orders.objects.filter(user=request.user).order_by('-id')
    context = {
        "booking_list": booking_list
    }
    return render(request, 'booking_list.html', context)


def buy_list(request):
    bike_buy_and_sell = BikeBuyAndSell.objects.filter(status='Approved').order_by('-id')
    context = {
        'bike_buy_and_sell': bike_buy_and_sell
    }
    return render(request, 'buy_list.html', context)


@login_required(login_url='/login')
def sell_views(request):
    category = Category.objects.all()
    context = {
        'category': category
    }
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        category = request.POST.get('category')
        category_obj = Category.objects.get(pk=category)
        user = request.user
        bike_buy_and_sell_create = BikeBuyAndSell.objects.create(
            name=name,
            price=price,
            quantity=quantity,
            description=description,
            category=category_obj,
            user=user
        )
        print('bike_buy_and_sell_create = ', bike_buy_and_sell_create)

        image_list = request.FILES.getlist('image')
        print("image_list = ", image_list)
        for image in image_list:
            print("image = ", image)
            BikeBuyAndSellImage.objects.create(
                bike_buy_and_sell=bike_buy_and_sell_create,
                image=image
            )
        return redirect('sell_list')

    return render(request, 'sell.html', context=context)


@login_required(login_url='/login')
def sell_list(request):
    bikes = BikeBuyAndSell.objects.filter(user=request.user)

    # Search and filter functionality
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')

    if search_query:
        bikes = bikes.filter(name__icontains=search_query)
    if category_id:
        bikes = bikes.filter(category_id=category_id)

    categories = Category.objects.all()
    context = {
        'bike_buy_and_sell': bikes,
        'categories': categories,
    }
    return render(request, 'sell_list.html', context)


# any one can add product to cart, no need of signin
def add_to_cart_view(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(BikeBuyAndSell, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'], update_quantity=cd['update'])
    return redirect('cart_detail')


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'update': True})
    return render(request, 'cart_detail.html', {'cart': cart})


def cart_update(request, product_id):
    if request.method == "POST":
        cart = Cart(request)
        product = get_object_or_404(BikeBuyAndSell, id=product_id)
        form = CartAddProductForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            print('cd = ', cd)
            cart.update(product=product, quantity=cd['quantity'], update_quantity=cd['update'])
        return redirect('cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(BikeBuyAndSell, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')


@login_required(login_url='/login')
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = User.objects.get(username=request.user)
            order = Orders.objects.create(
                user=user,
                email=cd['email'],
                mobile=cd['mobile'],
                address=cd['address'],
                total_price=cart.get_total_price()
            )

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    bike_buy_and_sell=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            cart.clear()
            return render(request, 'order_created.html', {'order': order})
    else:
        form = OrderCreateForm()
    return render(request, 'checkout_create.html', {'form': form})


def search_view(request):
    # whatever user write in search box we get in query
    query = request.GET['query']
    products = BikeBuyAndSell.objects.all().filter(name__icontains=query)

    # word variable will be shown in html when user click on search button
    word = "Searched Result : {}".format(query)

    context = {
        'bike_buy_and_sell': products,
        'word': word,
    }

    return render(request, 'index.html', context)


def order_details(request, order_id):
    orders = Orders.objects.get(user=request.user, id=order_id)
    products = OrderItem.objects.filter(order__id=order_id)
    return render(request, 'order_details.html', {'order': orders, "products": products})


def product_detail(request, id):
    product = get_object_or_404(BikeBuyAndSell, id=id)
    seller = product.user  # Get the seller's user object
    cart_product_form = CartAddProductForm()
    context = {
        'product': product,
        'seller': seller,  # Pass the seller's information to the template
        'cart_product_form': cart_product_form,
    }
    return render(request, 'detail.html', context)


def category_based_bike(request, category_id):
    bike_buy_and_sell = BikeBuyAndSell.objects.filter(category__id=category_id)
    context = {
        'bike_buy_and_sell': bike_buy_and_sell,
    }
    return render(request, 'category_based_bike.html', context)


@login_required
def chat_support(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            ChatMessage.objects.create(
                user=request.user,
                message=message,
                is_admin=request.user.is_staff
            )

    # Fetch all messages for the current user
    messages_list = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'chat_support.html', {'messages': messages_list})


@login_required
def user_chat_support(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            ChatMessage.objects.create(
                user=request.user,
                message=message,
                is_admin=False
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect('chat_support')
            
    # Remove parent=None filter so that admin replies (child messages) are included
    messages_list = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'chat_support.html', {'messages': messages_list})


@login_required(login_url='/login/')
def edit_bike(request, bike_id):
    bike = get_object_or_404(BikeBuyAndSell, id=bike_id, user=request.user)
    if request.method == 'POST':
        bike.name = request.POST.get('name')
        bike.price = request.POST.get('price')
        bike.description = request.POST.get('description')
        bike.quantity = request.POST.get('quantity')
        bike.category_id = request.POST.get('category')
        bike.save()
        messages.success(request, "Bike listing updated successfully!")
        return redirect('index')
    categories = Category.objects.all()
    return render(request, 'edit_bike.html', {'bike': bike, 'categories': categories})


@login_required(login_url='/login/')
def delete_bike(request, bike_id):
    bike = get_object_or_404(BikeBuyAndSell, id=bike_id, user=request.user)
    bike.delete()
    messages.success(request, "Bike listing deleted successfully!")
    return redirect('index')


@login_required
def admin_chat_support(request):
    if not request.user.is_staff:
        return redirect('index')  # Restrict access to admins only

    if request.method == 'POST':
        message = request.POST.get('message')
        user_id = request.POST.get('user_id')
        parent_id = request.POST.get('parent_id')  # Optional parent message id

        if parent_id:
            parent_msg = ChatMessage.objects.filter(id=parent_id).first()
            user = parent_msg.user if parent_msg else User.objects.get(id=user_id)
        else:
            parent_msg = None
            user = User.objects.get(id=user_id)

        if message:
            ChatMessage.objects.create(
                user=user,
                message=message,
                is_admin=True,
                parent=parent_msg
            )
            if parent_msg:
                parent_msg.status = 'resolved'
                parent_msg.save()
    # Fetch all users with messages
    users_with_messages = User.objects.filter(chat_messages__isnull=False).distinct()
    selected_user_id = request.GET.get('user_id', users_with_messages.first().id if users_with_messages else None)
    selected_user = User.objects.get(id=selected_user_id) if selected_user_id else None
    # Order messages to group thread conversations
    messages_list = ChatMessage.objects.filter(user=selected_user).order_by('timestamp') if selected_user else []
    return render(request, 'admin_chat_support.html', {
        'users': users_with_messages,
        'selected_user': selected_user,
        'messages': messages_list
    })

