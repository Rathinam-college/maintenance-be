import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Category, Tag

categories = [
    ("Employee Cost (Technician, Contract, Admin & Executive)", 500000),
    ("AC Maintenance", 150000),
    ("Electrical Maintenance", 200000),
    ("Plumbing Maintenance", 100000),
    ("Carpentry Maintenance", 80000),
    ("Fabrication Maintenance", 90000),
    ("Painting Maintenance", 70000),
    ("Civil Maintenance", 120000),
    ("Other Maintenance", 60000),
    ("Fire Extinguisher Maintenance", 40000),
    ("Pest Control", 30000),
    ("Infrastructure / Improvement (Capex)", 1000000),
]

tags = [
    "Salt Purchase",
    "Rewinding",
    "Admin/Pantry/Pooja/Stores",
    "Imprest Cash",
    "Festivals & Safety Gear (Diwali/Pongal/Shoes)"
]

for name, amount in categories:
    Category.objects.get_or_create(name=name, defaults={'sanctioned_amount': amount})

for t in tags:
    Tag.objects.get_or_create(name=t)

print("Seed data successfully created!")
