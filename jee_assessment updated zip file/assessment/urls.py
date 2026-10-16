from django.urls import path

from .views import (
    get_questions,
    evaluate_answers,
    generate_test,
    generate_adaptive_test,
    get_history
)

urlpatterns = [
    path(
        "questions/",
        get_questions
    ),

    path(
        "generate-test/",
        generate_test
    ),

    path(
        "evaluate/",
        evaluate_answers
    ),

    path(
        "adaptive-test/",
        generate_adaptive_test
    ),

    path("performance-history/",
          get_history
    )
]