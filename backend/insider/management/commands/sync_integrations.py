from django.core.management.base import BaseCommand
from django.conf import settings
from insider.models import InsiderIntegration, InsiderIntegrationKey
from insider.registry import INTEGRATION_REGISTRY


class Command(BaseCommand):
    help = 'Syncs integration definitions (names, logos, config keys) from code to the DB.'

    def add_arguments(self, parser):
        parser.add_argument('--database', type=str, help='Target database alias')

    def handle(self, *args, **options):
        insider_cfg = getattr(settings, "INSIDER", {})
        db_alias = options['database'] or insider_cfg.get("DB_ALIAS", "default")
        
        self.stdout.write(f"Syncing integrations to database: '{db_alias}'...")

        count = 0
        for identifier, integration_class in INTEGRATION_REGISTRY.items():
            logo = getattr(integration_class, 'logo_url', None)

            obj, created = InsiderIntegration.objects.using(db_alias).update_or_create(
                identifier=identifier,
                defaults={
                    'name': identifier.capitalize(),
                    'logo_url': logo,
                    # preserve the 'is_active' field
                }
            )
            
            action = "Created" if created else "Updated"
            self.stdout.write(f"   [{action}] Integration: {identifier}")

            # Sync Config Keys
            defined_configs = getattr(integration_class, 'config_definition', {})

            for key, meta in defined_configs.items():
                key_obj, k_created = InsiderIntegrationKey.objects.using(db_alias).get_or_create(
                    integration=obj,
                    key=key,
                    defaults={
                        'label': meta.get('label', key),
                        'field_type': meta.get('type', 'STRING'),
                        'is_required': meta.get('required', False),
                        'value': meta.get('default', ''),
                        'help_text': meta.get('help_text', '')
                        # preserve the values
                    }
                )

                # Update the DB incase of developer change
                if not k_created:
                    key_obj.label = meta.get('label', key)
                    key_obj.help_text = meta.get('help_text', '')
                    key_obj.field_type = meta.get('type', 'STRING')
                    key_obj.is_required = meta.get('required', False)
                    key_obj.save(using=db_alias)

            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {count} integrations."))