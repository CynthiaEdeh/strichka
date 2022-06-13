from typing import Any

from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.base import View
from django_filters.views import FilterView

from common.views import BaseView
from movies.models import Cast, Collection, Movie
from movies.services import services
from movies.services.filters import MovieFilter


class MoviesBaseView(BaseView):
    """
    The main page of the "Search Movies" site, only the most important is displayed.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            "index_slider_movies": services.get_movies_slider(limit=12),
            "best_movies": services.get_top_fantasy(limit=5),
            "last_movies": services.get_new_movies_and_series(limit=18),
            "new_releases": services.get_recent_premieres(limit=18),
            "popular_movies": services.get_popular_movies(limit=18),
            "popular_series": services.get_popular_series(limit=18),
            "cinema_movies": services.get_cinema_movies(limit=6),
            "collections": services.get_collections(),
        }
        return render(request, "movies/index.html", context)


class MovieDetailsView(BaseView):
    """
    Detailed information about the movie.
    """

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        movie = get_object_or_404(Movie, pk=pk)
        context = services.GetMovieDetail.execute({"movie": movie.id})
        return render(request, "movies/movie_detail.html", context)


class CastMemberDetailsView(BaseView):
    """
    Detailed information about cast members.
    """

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        cast_member = get_object_or_404(Cast, pk=pk)
        context = services.GetCastDetail.execute({"member": cast_member.id})
        return render(request, "movies/cast_member.html", context)


class FilteredListView(FilterView):
    """
    Base view for specific movie collection pages.
    """

    page_title = ""
    filterset_class = MovieFilter
    paginate_by = 32
    template_name = "movies/movie_list.html"

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class MoviesByYearView(FilteredListView):
    """
    List of movies released in specific year or in the range of years.
    """

    page_title = "Movies by Year"

    def get_queryset(self) -> QuerySet:
        year = self.kwargs["year"].split("-")
        if (len(year[0]) and len(year[-1])) != 4:
            raise Http404()
        try:
            queryset = services.get_movies_list_by_years(year)
        except ValueError:
            raise Http404()

        return queryset


class MoviesByCountryView(FilteredListView):
    """
    List of movies released in specific country.
    """

    page_title = "Movies by Country"

    def get_queryset(self) -> QuerySet:
        try:
            queryset = services.get_movies_list_by_country(self.kwargs["country"])
        except ValueError:
            raise Http404()

        return queryset


class MoviesByGenreView(FilteredListView):
    """
    List of movies in specific genre.
    """

    page_title = "Movies by Genre"

    def get_queryset(self) -> QuerySet:
        try:
            queryset = services.get_movies_list_by_genre(self.kwargs["slug"])
        except ValueError:
            raise Http404()

        return queryset


class MoviesByImdbRatingView(FilteredListView):
    """
    Top list of movies and series according to IMDB.
    """

    page_title = "Movies by IMDB Rate"
    queryset = services.get_imdb_top()


class ClassicMoviesView(FilteredListView):
    """
    Top classic movies.
    """

    page_title = "TOP Classic movies"
    queryset = services.get_top_classics()


class PopularMoviesView(FilteredListView):
    """
    List of popular movies.
    """

    page_title = "Popular movies"
    queryset = services.get_popular_movies()


class PopularSeriesView(FilteredListView):
    """
    List of popular series.
    """

    page_title = "Popular series"
    queryset = services.get_popular_series()


class RecentPremieresView(FilteredListView):
    """
    Recent movie and series premieres.
    """

    page_title = "Recent premieres"
    queryset = services.get_recent_premieres()


class NewMoviesSeriesView(FilteredListView):
    """
    New movies and series.
    """

    page_title = "New movies"
    queryset = services.get_new_movies_and_series()


class MoviesMonthView(FilteredListView):
    """
    List movies of the month.
    """

    page_title = "Movies of the month"
    queryset = services.get_movie_of_month()


def get_filter_countries(request: HttpRequest) -> JsonResponse:
    """
    Get all the countries from the DB.
    """

    if request.method == "GET" and request.is_ajax():
        countries = services.DataFilters.get_countries()
        data = {"countries": countries}
        return JsonResponse(data, status=200)


def get_filter_categories(request: HttpRequest) -> JsonResponse:
    """
    Get all the categories from the DB.
    """

    if request.method == "GET" and request.is_ajax():
        categories = services.DataFilters.get_categories()
        data = {"categories": categories}
        return JsonResponse(data, status=200)


def get_filter_year(request: HttpRequest) -> JsonResponse:
    """
    Get all the years from the DB.
    """

    if request.method == "GET" and request.is_ajax():
        years = services.DataFilters.get_years()
        data = {"years": years}
        return JsonResponse(data, status=200)


def get_filter_genres(request: HttpRequest) -> JsonResponse:
    """
    Get all the genres from the DB.
    """

    if request.method == "GET" and request.is_ajax():
        genres = services.DataFilters.get_genres()
        data = {"genres": genres}
        return JsonResponse(data, status=200)


class CommentView(View):
    """
    Adding comments to movies and series
    """

    model = None

    def post(self, request, pk: int) -> HttpResponse:

        _mutable = request.POST._mutable  # noqa: WPS122, WPS437
        request.POST._mutable = True  # noqa: WPS437
        request.POST["user"] = request.user
        request.POST._mutable = _mutable  # noqa: WPS121, WPS437

        obj = get_object_or_404(self.model, pk=pk)
        services.add_comment(request_post=request.POST, content_object=obj)
        return redirect(f"{obj.get_absolute_url()}#comments")


class VoteView(View):
    """
    Like/Dislike system
    """

    model = None
    vote_type = None

    def post(self, request, pk: int) -> HttpResponse:
        obj = get_object_or_404(self.model, pk=pk)
        if request.is_ajax():
            context = services.add_vote(
                user=request.user, vote_type=self.vote_type, obj=obj
            )
            return JsonResponse(context)


class MoviesOfCollectionView(FilterView):
    """
    Displaying a list of movies of a certain collection.
    """

    filterset_class = MovieFilter
    paginate_by = 32
    template_name = "movies/collection.html"

    def get_collection(self):
        return get_object_or_404(Collection, pk=self.kwargs["pk"])

    def get_queryset(self) -> QuerySet:
        collection = self.get_collection()
        queryset = services.get_movies_of_collection(collection=collection)
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        collection = self.get_collection()
        context["name_collection"] = collection.name
        return context
