from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.backend_brokers.models import UserData

class Command(BaseCommand):
    help = "Tworzy konta Django dla istniejących UserData"

    def handle(self, *args, **kwargs):
        for userdata in UserData.objects.all():
            user, created = User.objects.get_or_create(
                username=userdata.email,
                defaults={
                    "first_name": userdata.first_name,
                    "last_name": userdata.last_name,
                    "email": userdata.email,
                }
            )

            if created:
                user.set_password("Test1234!")
                user.save()

            
            if not hasattr(userdata, 'user') or userdata.user is None:
                userdata.user = user
                userdata.save()

        self.stdout.write(self.style.SUCCESS("Konta Django zostały utworzone!"))
