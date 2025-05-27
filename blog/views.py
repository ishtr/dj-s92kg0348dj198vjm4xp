from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import Post, Like, Comment
from django import forms
from django.db.models import Sum
from django.shortcuts import redirect
from django.db import IntegrityError, transaction
from .models import ChatMessage
from .forms import ChatForm
from django.shortcuts import render


# Ana sayfa
def home(request):
    posts = Post.objects.all().order_by('-created_at')
    chats = ChatMessage.objects.all().order_by('-timestamp')[:20]

    if request.method == 'POST' and 'chat_submit' in request.POST:
        if request.user.is_authenticated:
            chat_form = ChatForm(request.POST)
            if chat_form.is_valid():
                chat = chat_form.save(commit=False)
                chat.user = request.user
                chat.save()
                return redirect('home')
        else:
            return redirect('login')
    else:
        chat_form = ChatForm()
    return render(request, 'blog/home.html', {'posts': posts, 'chat_form': chat_form, 'chats': chats})

# Kayıt olma
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Kayıt sonrası otomatik giriş
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'blog/register.html', {'form': form})

# Giriş yapma
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'blog/login.html', {'form': form})

# Çıkış yapma
@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# Profil sayfası
@login_required
def profile(request):
    user_posts = Post.objects.filter(author=request.user)  # Bu kullanıcının postlarını al
    post_count = user_posts.count()  # Kaç postu var
    total_score = Like.objects.filter(post__author=request.user).aggregate(total=Sum('vote'))['total'] or 0
    user = request.user
    likes_count = Like.objects.filter(user=user, vote=1).count()
    dislikes_count = Like.objects.filter(user=user, vote=-1).count()
    posts = Post.objects.filter(author=request.user)

    context = {
        'user': user,
        'user_posts': user_posts,
        'post_count': post_count,
        'total_score': total_score,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'posts': posts,  # <== Burası önemli
    }

    return render(request, 'blog/profile.html', context)

# Post detay sayfası - yorum ve beğeni özellikleri ile
def post_detail(request, pk):
    post = Post.objects.get(pk=pk)
    comments = post.comments.all().order_by('-created_at')

    # Postun aldığı toplam oy (beğeni - beğenmeme)
    score = post.likes.aggregate(total=Sum('vote'))['total'] or 0

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('post_detail', pk=pk)
    else:
        form = CommentForm()

    # Kullanıcının bu posta verdiği oy varsa onu al
    user_vote = None
    if request.user.is_authenticated:
        try:
            user_vote = Like.objects.get(user=request.user, post=post).vote
        except Like.DoesNotExist:
            user_vote = None

    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'score': score,
        'user_vote': user_vote,
    }
    return render(request, 'blog/post_detail.html', context)

# Beğen / Beğenme işlemi
@login_required
def like_post(request, pk, action):
    post = Post.objects.get(pk=pk)
    vote_value = 1 if action == 'like' else -1

    like_obj, created = Like.objects.get_or_create(user=request.user, post=post, defaults={'vote': vote_value})

    if not created and like_obj.vote == vote_value:
        # Aynı oyu tekrar vermek isteyince oy kaldırılır
        like_obj.delete()
    else:
        like_obj.vote = vote_value  # Burada atama kesin yapılmalı
        like_obj.save()
    return redirect('post_detail', pk=pk)

# Post oluşturmak için form
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image']

# Yeni post oluşturma view'u
@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)  # Resim için request.FILES gerekiyor
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_create.html', {'form': form})

# Yorum formu
from django import forms
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'placeholder':'Yorumunuzu yazın...'})
        }

@login_required
def chat_room(request):
    messages = ChatMessage.objects.all().order_by('-timestamp')[:30][::-1]  # Son 30 mesajı al, en son gelen üstte
    if request.method == 'POST':
        msg = request.POST.get('message')
        if msg:
            ChatMessage.objects.create(user=request.user, message=msg)
            return redirect('chat_room')

    return render(request, 'blog/chat_room.html', {'messages': messages})