"""Publisher routes blueprint for simple publisher management."""

import logging
import secrets
from flask import Blueprint, flash, redirect, render_template, request
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, Product

logger = logging.getLogger(__name__)

# Create blueprint
publisher_bp = Blueprint("publisher", __name__)


@publisher_bp.route("/test")
def test_route():
    """Test route to see if the publisher blueprint is working."""
    return "Publisher blueprint is working!"


@publisher_bp.route("/<tenant_id>/products")
def publisher_products(tenant_id):
    """Simple publisher products page - no authentication required."""
    logger.info(f"publisher_products called for tenant: {tenant_id}")
    
    try:
        import os
        logger.info(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT SET')}")
        
        # Create a new engine with the correct database URL
        db_url = 'sqlite:////Users/harvingupta/.adcp/adcp.db'
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db_session:
            logger.info("Database session created successfully")
            
            # Test with raw SQL first
            result = db_session.execute(text("SELECT tenant_id, name FROM tenants WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            raw_tenant = result.fetchone()
            logger.info(f"Raw SQL query result: {raw_tenant}")
            
            if not raw_tenant:
                logger.error(f"Raw SQL query found no tenant: {tenant_id}")
                return f"Publisher not found (raw SQL): {tenant_id}", 404
            
            logger.info(f"Raw SQL found tenant: {raw_tenant[1]}")
            
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            logger.info(f"SQLAlchemy query result: {tenant}")
            
            if not tenant:
                logger.error(f"SQLAlchemy query found no tenant: {tenant_id}")
                return f"Publisher not found (SQLAlchemy): {tenant_id}", 404
            
            logger.info(f"Found tenant: {tenant.name}")
            
            products = db_session.query(Product).filter_by(tenant_id=tenant_id).all()
            logger.info(f"Found {len(products)} products for tenant {tenant_id}")
            
            return render_template(
                "publisher_products.html",
                tenant=tenant,
                tenant_id=tenant_id,
                products=products
            )
            
    except Exception as e:
        logger.error(f"Error loading publisher products: {e}", exc_info=True)
        return f"Error: {str(e)}", 500


@publisher_bp.route("/<tenant_id>/add_product", methods=["GET", "POST"])
def add_product(tenant_id):
    """Add a product to a publisher - no authentication required."""
    logger.info(f"add_product called for tenant: {tenant_id}, method: {request.method}")
    
    try:
        # Create a new engine with the correct database URL
        db_url = 'sqlite:////Users/harvingupta/.adcp/adcp.db'
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db_session:
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                logger.error(f"Tenant not found: {tenant_id}")
                flash("Publisher not found", "error")
                return redirect("/select_publisher")
            
            logger.info(f"Found tenant: {tenant.name}")
            
            if request.method == "POST":
                # Debug: print form data
                logger.info(f"Form data: {request.form}")
                
                try:
                    # Create new product
                    product = Product(
                        product_id=f"prod_{secrets.token_hex(8)}",
                        tenant_id=tenant_id,
                        name=request.form.get("name"),
                        description=request.form.get("description", ""),
                        formats=request.form.get("formats", "").split(",") if request.form.get("formats") else [],
                        targeting_template={},
                        delivery_type=request.form.get("delivery_type", "non_guaranteed"),
                        is_fixed_price=True,
                        cpm=float(request.form.get("price_cpm", 0)),
                        price_guidance={},
                        is_custom=False,
                        countries=[],
                        implementation_config={}
                    )
                    
                    logger.info(f"Created product: {product.name} with ID: {product.product_id}")
                    
                    db_session.add(product)
                    db_session.commit()
                    logger.info("Product committed to database successfully")
                    flash("Product added successfully!", "success")
                    return redirect(f"/publisher/{tenant_id}/products")
                    
                except Exception as db_error:
                    logger.error(f"Database error: {db_error}", exc_info=True)
                    db_session.rollback()
                    flash(f"Database error: {str(db_error)}", "error")
                    return redirect(f"/publisher/{tenant_id}/products")
            
            return render_template("add_product.html", tenant=tenant, tenant_id=tenant_id)
            
    except Exception as e:
        logger.error(f"Error adding product: {e}", exc_info=True)
        flash(f"Error adding product: {str(e)}", "error")
        return redirect(f"/publisher/{tenant_id}/products")


@publisher_bp.route("/<tenant_id>/products/<product_id>/delete", methods=["POST"])
def delete_product(tenant_id, product_id):
    """Delete a product - no authentication required."""
    logger.info(f"delete_product called for tenant: {tenant_id}, product: {product_id}")
    
    try:
        # Create a new engine with the correct database URL
        db_url = 'sqlite:////Users/harvingupta/.adcp/adcp.db'
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db_session:
            # Verify tenant exists
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                flash("Publisher not found", "error")
                return redirect("/select_publisher")
            
            # Find and delete the product
            product = db_session.query(Product).filter_by(tenant_id=tenant_id, product_id=product_id).first()
            if not product:
                flash("Product not found", "error")
                return redirect(f"/publisher/{tenant_id}/products")
            
            product_name = product.name
            db_session.delete(product)
            db_session.commit()
            
            flash(f"Product '{product_name}' deleted successfully!", "success")
            return redirect(f"/publisher/{tenant_id}/products")
            
    except Exception as e:
        logger.error(f"Error deleting product: {e}", exc_info=True)
        flash(f"Error deleting product: {str(e)}", "error")
        return redirect(f"/publisher/{tenant_id}/products")


@publisher_bp.route("/<tenant_id>/products/delete_all", methods=["POST"])
def delete_all_products(tenant_id):
    """Delete all products for a tenant - no authentication required."""
    logger.info(f"delete_all_products called for tenant: {tenant_id}")
    
    try:
        # Create a new engine with the correct database URL
        db_url = 'sqlite:////Users/harvingupta/.adcp/adcp.db'
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db_session:
            # Verify tenant exists
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                flash("Publisher not found", "error")
                return redirect("/select_publisher")
            
            # Count products before deletion
            products_count = db_session.query(Product).filter_by(tenant_id=tenant_id).count()
            
            if products_count == 0:
                flash("No products to delete", "info")
                return redirect(f"/publisher/{tenant_id}/products")
            
            # Delete all products for this tenant
            db_session.query(Product).filter_by(tenant_id=tenant_id).delete()
            db_session.commit()
            
            flash(f"Deleted {products_count} products successfully!", "success")
            return redirect(f"/publisher/{tenant_id}/products")
            
    except Exception as e:
        logger.error(f"Error deleting all products: {e}", exc_info=True)
        flash(f"Error deleting products: {str(e)}", "error")
        return redirect(f"/publisher/{tenant_id}/products")
