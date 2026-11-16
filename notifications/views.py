from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def toasts(request):
    new = list(request.user.notifications.filter(is_toast_shown=False)[:5])
    Notification.objects.filter(pk__in=[n.pk for n in new]).update(is_toast_shown=True)

    return render(request, "notifications/_toasts.html", {
        "new_notifications": new,
        "unread_notifications_count": request.user.notifications.filter(is_read=False).count(),
    })


@login_required
def notification_list(request):
    notifications = list(request.user.notifications.all()[:50])
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "notifications/list.html", {"notifications": notifications})


@login_required
def notification_open(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    Notification.objects.filter(pk=notification.pk).update(is_read=True)
    return redirect(notification.url or "notification_list")