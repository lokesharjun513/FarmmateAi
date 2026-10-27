from app.modules.farmer.models import Farmer


def get_next_step(farmer: Farmer | None) -> dict:

    # User has not created a farmer profile yet
    if farmer is None:
        return {
            "step": "language",
            "title": "Welcome to FarmMate AI",
            "message": "Which language do you prefer?",
            "progress": 0,
            "completed": False,
        }

    # Profile started
    if farmer.profile_completion < 20:
        return {
            "step": "language",
            "title": "Welcome to FarmMate AI",
            "message": "Which language do you prefer?",
            "progress": farmer.profile_completion,
            "completed": False,
        }

    # Farm details
    if farmer.profile_completion < 100:
        return {
            "step": "farm",
            "title": "Let's add your first farm",
            "message": "Tell me about your farm.",
            "progress": farmer.profile_completion,
            "completed": False,
        }

    # Completed
    return {
        "step": "completed",
        "title": "You're all set!",
        "message": "Let's start farming.",
        "progress": 100,
        "completed": True,
    }