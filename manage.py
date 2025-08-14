#!/usr/bin/env python
"""Database management CLI script."""
import click
from database import create_app, init_db, seed_db
from models import db

@click.group()
def cli():
    """Database management commands."""
    pass

@cli.command()
@click.option('--env', default='development', help='Environment to use (development, testing, production)')
def init(env):
    """Initialize the database."""
    app = create_app(env)
    with app.app_context():
        init_db(app)
        click.echo(f"Database initialized for {env} environment!")

@cli.command()
@click.option('--env', default='development', help='Environment to use (development, testing, production)')
def seed(env):
    """Seed the database with initial data."""
    app = create_app(env)
    with app.app_context():
        seed_db(app)
        click.echo(f"Database seeded for {env} environment!")

@cli.command()
@click.option('--env', default='development', help='Environment to use (development, testing, production)')
def reset(env):
    """Reset the database (drop all tables and recreate)."""
    app = create_app(env)
    with app.app_context():
        click.echo("Dropping all tables...")
        db.drop_all()
        click.echo("Creating all tables...")
        db.create_all()
        click.echo("Seeding database...")
        seed_db(app)
        click.echo(f"Database reset complete for {env} environment!")

@cli.command()
@click.option('--env', default='development', help='Environment to use (development, testing, production)')
def status(env):
    """Show database status."""
    app = create_app(env)
    with app.app_context():
        from models.user import User
        from models.job_posting import JobPosting
        from models.visa_sponsorship_data import VisaSponsorshipData
        
        user_count = User.query.count()
        job_count = JobPosting.query.count()
        company_count = VisaSponsorshipData.query.count()
        
        click.echo(f"Database Status ({env} environment):")
        click.echo(f"  Users: {user_count}")
        click.echo(f"  Job Postings: {job_count}")
        click.echo(f"  Companies with Visa Data: {company_count}")

if __name__ == '__main__':
    cli()