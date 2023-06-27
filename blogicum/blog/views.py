from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView
)

from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post, User

POSTS_PER_PAGE = 10


class IndexView(ListView):
    model = Post
    template_name = "blog/index.html"
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        return Post.objects.prefetch_related("comments").select_related(
            "author",
            "category",
            "location",
        ).filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True,
        ).annotate(comment_count=Count("comments")).order_by('-pub_date')


class Profile(ListView):
    model = Post
    template_name = 'blog/profile.html'
    ordering = 'id'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User, username=self.kwargs.get(
            'username'
        )
        )
        return context

    def get_queryset(self):
        author = get_object_or_404(User, username=self.kwargs.get('username'))
        instance = author.posts.filter(
            author__username__exact=self.kwargs.get('username')
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
        return instance


'''
class Profile(ListView):
    model = Post
    template_name = "blog/profile.html"
    ordering = "id"
    paginate_by = POSTS_PER_PAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.profile
        return context

    def get_queryset(self):
        post_list = User.objects.prefetch_related(
            Prefetch(
                'posts',
                queryset=(
                    Post.objects.prefetch_related("comments")
                    .select_related(
                        "author",
                        "category",
                        "location",
                    )
                    .filter(
                        pub_date__lt=timezone.now(),
                        is_published=True,
                        category__is_published=True,
                    )
                    .annotate(comment_count=Count("comments"))
                )
            )
        )
        self.profile = get_object_or_404(
            post_list, username=self.kwargs.get("username")
        )
        posts = (
            self.profile.posts.filter(
                author__username=self.kwargs.get("username")
            )
            .annotate(comment_count=Count("comments"))
            .order_by("-pub_date")
        )
        return posts
'''


class CategoryListView(ListView):
    model = Post
    template_name = "blog/category.html"
    paginate_by = POSTS_PER_PAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = get_object_or_404(
            Category,
            slug=self.kwargs["category_slug"],
            is_published=True,
        )
        return context

    def get_queryset(self):
        category_slug = self.kwargs.get("category_slug")
        category = get_object_or_404(
            Category, slug=category_slug, is_published=True
        )

        queryset = (
            category.posts.select_related("category").filter(
                pub_date__lt=timezone.now(),
                is_published=True,
            )
            .annotate(comment_count=Count("comments"))
            .order_by("-pub_date")
        )
        return queryset


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("author")
        return context


class ProfileEdit(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "blog/user.html"
    success_url = reverse_lazy("blog:index")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"
    pk_url_kwarg = "pk"
    post_obj = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs.get("pk"))
        if self.post_obj.author != request.user:
            return redirect("blog:post_detail", self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("blog:post_detail",
                            kwargs={"pk": self.post_obj.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"
    success_url = reverse_lazy("blog:index")
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs.get("pk"))
        if post.author != request.user:
            return redirect("blog:post_detail", self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        comment = get_object_or_404(Post, pk=self.kwargs["pk"])
        form.instance.author = self.request.user
        form.instance.post = comment
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"pk": self.kwargs["pk"]})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = "blog/comment.html"
    form_class = CommentForm
    pk_url_kwarg = "comment_pk"

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs["comment_pk"])
        if comment.author != request.user:
            return redirect("blog:post_detail", comment.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"pk": self.kwargs["pk"]})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "blog/comment.html"
    success_url = reverse_lazy("blog:index")
    pk_url_kwarg = "comment_pk"

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs["comment_pk"])
        if comment.author != request.user:
            return redirect("blog:post_detail", pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)
