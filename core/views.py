from django.shortcuts import redirect


def home_redirect(request):
    # Redirect anonymous users to login and authenticated users to room list
    if request.user.is_authenticated:
        return redirect('room_list')
    # send next to /rooms/ so after login user lands on rooms list
    return redirect(f"/accounts/login/?next=/rooms/")
