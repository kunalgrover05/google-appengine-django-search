from django.core.management.base import BaseCommand
from searchApp.models import IndexModel


class Command(BaseCommand):
    help = 'Sets all indexes as not processed to allow reindex'

    def handle(self, *args, **options):
        IndexModel.objects.filter(deleted=False).filter(processed=True).update(processed=False)
        self.stdout.write(self.style.SUCCESS('Successfully set all for reindexing'))
