import os
import secrets

from scripts.ops.migrate import run_migrations
from src.core.database.database_session import get_db_session
from src.core.database.models import AdapterConfig, Principal, Product, SuperadminConfig, Tenant


def init_db(exit_on_error=False):
    """Initialize database with migrations and populate default data.

    Args:
        exit_on_error: If True, exit process on migration error. If False, raise exception.
                      Default False for test compatibility.
    """
    # Run migrations first
    print("Applying database migrations...")
    run_migrations(exit_on_error=exit_on_error)

    # Now populate default data if needed
    with get_db_session() as session:
        # Initialize super admin configuration from environment variables
        super_admin_emails = os.environ.get("SUPER_ADMIN_EMAILS", "")
        if super_admin_emails:
            # Check if config exists
            existing_config = session.query(SuperadminConfig).filter_by(config_key="super_admin_emails").first()
            if not existing_config:
                # Create new config
                config = SuperadminConfig(
                    config_key="super_admin_emails",
                    config_value=super_admin_emails,
                    description="Super admin email addresses",
                )
                session.add(config)
                session.commit()
                print(f"✅ Initialized super admin emails: {super_admin_emails}")
            else:
                # Update existing config if environment variable is set
                existing_config.config_value = super_admin_emails
                session.commit()
                print(f"✅ Updated super admin emails: {super_admin_emails}")

        # Similarly for super admin domains
        super_admin_domains = os.environ.get("SUPER_ADMIN_DOMAINS", "")
        if super_admin_domains:
            existing_config = session.query(SuperadminConfig).filter_by(config_key="super_admin_domains").first()
            if not existing_config:
                config = SuperadminConfig(
                    config_key="super_admin_domains",
                    config_value=super_admin_domains,
                    description="Super admin email domains",
                )
                session.add(config)
                session.commit()
                print(f"✅ Initialized super admin domains: {super_admin_domains}")
            else:
                existing_config.config_value = super_admin_domains
                session.commit()
                print(f"✅ Updated super admin domains: {super_admin_domains}")

        # Check if we need to create a default tenant
        tenant_count = session.query(Tenant).count()

        if tenant_count == 0:
            # No tenants exist - create a default one for simple use case
            admin_token = secrets.token_urlsafe(32)
            secrets.token_urlsafe(32)

            # Create default tenant
            default_tenant = Tenant(
                tenant_id="default",
                name="Default Publisher",
                subdomain="localhost",  # Works with localhost:8080
                is_active=True,
                billing_plan="standard",
                ad_server="mock",
                max_daily_budget=10000,
                enable_aee_signals=True,
                admin_token=admin_token,
                human_review_required=True,
                auto_approve_formats=["display_300x250", "display_728x90", "display_320x50"],
            )
            session.add(default_tenant)

            # Create adapter config for mock adapter
            adapter_config = AdapterConfig(tenant_id="default", adapter_type="mock", mock_dry_run=False)
            session.add(adapter_config)

            # Always create a demo principal for testing (used by ADK agent)
            demo_principal = Principal(
                tenant_id="default",
                principal_id="demo_advertiser",
                name="Demo Advertiser",
                platform_mappings={
                    "gam_advertiser_id": 99999,
                    "kevel_advertiser_id": "demo-advertiser",
                    "triton_advertiser_id": "ADV-DEMO-001",
                    "mock_advertiser_id": "mock-demo",
                },
                access_token="demo_token_123",
            )
            session.add(demo_principal)

            # Always create basic products for demo/testing
            basic_products = [
                Product(
                    tenant_id="default",
                    product_id="prod_display_premium",
                    name="Premium Display Package",
                    description="Premium display advertising across news and sports sections",
                    formats=[
                        {
                            "format_id": "display_300x250",
                            "name": "Medium Rectangle",
                            "type": "display",
                            "specs": {"width": 300, "height": 250},
                        }
                    ],
                    targeting_template={"geo_country_any_of": ["US"]},
                    delivery_type="guaranteed",
                    is_fixed_price=False,
                    price_guidance={"floor": 10.0, "p50": 15.0, "p75": 20.0},
                    countries=["United States"],
                    implementation_config={
                        "placement_ids": ["premium_300x250"],
                        "ad_unit_path": "/1234/premium/display",
                    },
                ),
                Product(
                    tenant_id="default",
                    product_id="prod_video_sports",
                    name="Sports Video Package",
                    description="Pre-roll video ads for sports content",
                    formats=[
                        {
                            "format_id": "video_preroll",
                            "name": "Pre-roll Video",
                            "type": "video",
                            "specs": {"duration": 30},
                        }
                    ],
                    targeting_template={"content_cat_any_of": ["sports"]},
                    delivery_type="guaranteed",
                    is_fixed_price=True,
                    cpm=25.0,
                    countries=["United States", "Canada"],
                    implementation_config={
                        "placement_ids": ["sports_video_preroll"],
                        "ad_unit_path": "/1234/sports/video",
                    },
                ),
            ]
            for product in basic_products:
                session.add(product)

            # Only create sample advertisers if this is a development environment
            if os.environ.get("CREATE_SAMPLE_DATA", "false").lower() == "true":
                principals_data = [
                    {
                        "principal_id": "acme_corp",
                        "name": "Acme Corporation",
                        "platform_mappings": {
                            "gam_advertiser_id": 67890,
                            "kevel_advertiser_id": "acme-corporation",
                            "triton_advertiser_id": "ADV-ACM-002",
                            "mock_advertiser_id": "mock-acme",
                        },
                        "access_token": "acme_corp_token",
                    },
                    {
                        "principal_id": "purina",
                        "name": "Purina Pet Foods",
                        "platform_mappings": {
                            "gam_advertiser_id": 12345,
                            "kevel_advertiser_id": "purina-pet-foods",
                            "triton_advertiser_id": "ADV-PUR-001",
                            "mock_advertiser_id": "mock-purina",
                        },
                        "access_token": "purina_token",
                    },
                ]

                for p in principals_data:
                    principal = Principal(
                        tenant_id="default",
                        principal_id=p["principal_id"],
                        name=p["name"],
                        platform_mappings=p["platform_mappings"],
                        access_token=p["access_token"],
                    )
                    session.add(principal)

                # Create sample products
                products_data = [
                    {
                        "product_id": "prod_1",
                        "name": "Premium Display - News",
                        "description": "Premium news site display inventory",
                        "formats": [
                            {
                                "format_id": "display_300x250",
                                "name": "Medium Rectangle",
                                "type": "display",
                                "description": "Standard medium rectangle display ad",
                                "specs": {"width": 300, "height": 250},
                                "delivery_options": {"hosted": {}},
                            }
                        ],
                        "targeting_template": {
                            "content_cat_any_of": ["news", "politics"],
                            "geo_country_any_of": ["US"],
                        },
                        "delivery_type": "guaranteed",
                        "is_fixed_price": False,
                        "cpm": None,
                        "price_guidance": {"floor": 5.0, "p50": 8.0, "p75": 10.0},
                        "implementation_config": {
                            "placement_ids": ["news_300x250_atf", "news_300x250_btf"],
                            "ad_unit_path": "/1234/news/display",
                            "key_values": {"section": "news", "tier": "premium"},
                            "targeting": {"content_cat_any_of": ["news", "politics"], "geo_country_any_of": ["US"]},
                        },
                    },
                    {
                        "product_id": "prod_2",
                        "name": "Run of Site Display",
                        "description": "Run of site display inventory",
                        "formats": [
                            {
                                "format_id": "display_728x90",
                                "name": "Leaderboard",
                                "type": "display",
                                "description": "Standard leaderboard display ad",
                                "specs": {"width": 728, "height": 90},
                                "delivery_options": {"hosted": {}},
                            }
                        ],
                        "targeting_template": {"geo_country_any_of": ["US", "CA"]},
                        "delivery_type": "non_guaranteed",
                        "is_fixed_price": True,
                        "cpm": 2.5,
                        "price_guidance": None,
                        "implementation_config": {
                            "placement_ids": ["ros_728x90_all"],
                            "ad_unit_path": "/1234/run_of_site/leaderboard",
                            "key_values": {"tier": "standard"},
                            "targeting": {"geo_country_any_of": ["US", "CA"]},
                        },
                    },
                ]

                for p in products_data:
                    product = Product(
                        tenant_id="default",
                        product_id=p["product_id"],
                        name=p["name"],
                        description=p["description"],
                        formats=p["formats"],
                        targeting_template=p["targeting_template"],
                        delivery_type=p["delivery_type"],
                        is_fixed_price=p["is_fixed_price"],
                        cpm=p.get("cpm"),
                        price_guidance=p.get("price_guidance"),
                        implementation_config=p.get("implementation_config"),
                    )
                    session.add(product)

            # Commit all changes
            session.commit()

            # Update the print statement based on whether sample data was created
            if os.environ.get("CREATE_SAMPLE_DATA", "false").lower() == "true":
                print(
                    f"""
╔══════════════════════════════════════════════════════════════════╗
║                 🚀 ADCP SALES AGENT INITIALIZED                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  A default tenant has been created for quick start:              ║
║                                                                  ║
║  🏢 Tenant: Default Publisher                                    ║
║  🌐 URL: http://localhost:8080                                   ║
║                                                                  ║
║  🔑 Admin Token (x-adcp-auth header):                            ║
║     {admin_token}  ║
║                                                                  ║
║  👤 Sample Advertiser Tokens:                                    ║
║     • Acme Corp: acme_corp_token                                 ║
║     • Purina: purina_token                                       ║
║                                                                  ║
║  💡 To create additional tenants:                                ║
║     python scripts/setup/setup_tenant.py "Publisher Name"        ║
║                                                                  ║
║  📚 To use with a different tenant:                              ║
║     http://[subdomain].localhost:8080                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
                """
                )
            else:
                print(
                    f"""
╔══════════════════════════════════════════════════════════════════╗
║                 🚀 ADCP SALES AGENT INITIALIZED                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  A default tenant has been created for quick start:              ║
║                                                                  ║
║  🏢 Tenant: Default Publisher                                    ║
║  🌐 Admin UI: http://localhost:8001/tenant/default/login         ║
║                                                                  ║
║  🔑 Admin Token (for legacy API access):                         ║
║     {admin_token}  ║
║                                                                  ║
║  ⚡ Next Steps:                                                  ║
║     1. Log in to the Admin UI                                    ║
║     2. Set up your ad server (Ad Server Setup tab)              ║
║     3. Create principals for your advertisers                    ║
║                                                                  ║
║  💡 To create additional tenants:                                ║
║     python scripts/setup/setup_tenant.py "Publisher Name"        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
                """
                )
        else:
            print(f"Database ready ({tenant_count} tenant(s) configured)")


if __name__ == "__main__":
    init_db(exit_on_error=True)
