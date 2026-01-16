from django.test import TransactionTestCase
from django.core.management import call_command
from django.db import connections
from insider.models import Incidence
from insider.settings import settings as insider_settings


class DatabaseRoutingTest(TransactionTestCase):
    serialized_rollback = True
    databases = {"default", insider_settings.DB_ALIAS}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        target_db = insider_settings.DB_ALIAS
    
        # ensure the next command actually runs the SQL
        call_command('migrate', 'insider', 'zero', database=target_db, verbosity=0)
        call_command('migrate', 'insider', database=target_db, verbosity=0)
        
        tables = connections[target_db].introspection.table_names()
        if 'insider_incidence' in tables:
            print("✅ Table 'insider_incidence' created successfully.")
        else:
            print("❌ WARNING: Table still missing after migration!")


    def test_incidence_writes_to_correct_db(self):
        target_db = insider_settings.DB_ALIAS

        incidence = Incidence.objects.create(
            title="500 error at /test-routing",
            fingerprint="e4d909c290d0fb1ca068ffaddf22cbd0",
        )

        # Assert it exists in the routed DB
        self.assertTrue(
            Incidence.objects.using(target_db)
            .filter(id=incidence.id)
            .exists(),
            f"Object not found in the '{target_db}' database."
        )

        # Assert isolation by checking TABLE absence, not row absence
        if target_db != "default":
            default_tables = connections['default'].introspection.table_names()

            self.assertNotIn(
                'insider_incidence',
                default_tables,
                "insider_incidence table should NOT exist in default database"
            )

        print("Routing Verified: Data landed correctly.")



    def test_router_enforcement(self):
        """
        Directly test the router logic to ensure it's loaded and active.
        """
        
        from insider.db_router import InsiderRouter
        router = InsiderRouter()
        
        # Check Write decision
        db_for_write = router.db_for_write(Incidence)
        self.assertEqual(db_for_write, insider_settings.DB_ALIAS)
        
        # Check Read decision
        db_for_read = router.db_for_read(Incidence)
        self.assertEqual(db_for_read, insider_settings.DB_ALIAS)