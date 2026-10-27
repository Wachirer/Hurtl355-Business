"""
Hurtl355 — Seed Script
Creates the admin user, sample portfolio works, pricing packages
and approved testimonials so the site looks populated on first run.

Usage:
    cd hurtl355
    python seed.py
"""

import os
import sys

# ── Ensure the package is importable ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.work import Work
from app.models.pricing import PricingPackage, PricingFeature
from app.models.testimonial import Testimonial
from app.models.settings import SiteSetting
from dotenv import load_dotenv

load_dotenv()

app = create_app()

with app.app_context():
    db.create_all()

    # ── 1. Admin user ─────────────────────────────────────────────────────────
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_email    = os.getenv('ADMIN_EMAIL', 'admin@hurtl355.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'hurtl355admin')

    if os.getenv('FLASK_ENV') == 'production' and admin_password == 'hurtl355admin':
        sys.exit('Refusing to seed production with the default admin password. Set ADMIN_PASSWORD.')

    if not User.query.filter_by(username=admin_username).first():
        user = User(username=admin_username, email=admin_email)
        user.set_password(admin_password)
        db.session.add(user)
        print(f'✓ Admin user created: {admin_username} (password taken from ADMIN_PASSWORD)')
    else:
        print(f'  Admin user already exists: {admin_username}')

    # ── 2. Default site settings ───────────────────────────────────────────────
    default_settings = {
        'brand_name':       'Hurtl355',
        'hero_tagline':     'Code. Design. Sound. Vision.',
        'hero_subtext':     'IT Support & Web Dev · Graphic Design · Video Editing · Music Production',
        'hero_cta_primary': 'View Work',
        'hero_cta_secondary': 'Hire Us',
        'about_bio': (
            "I'm a Nairobi-based software engineer and multidisciplinary creative operating "
            "under the Hurtl355 brand. I blend technical precision with artistic sensibility "
            "to deliver digital products that look stunning and work flawlessly. Whether you "
            "need a blazing-fast website, a jaw-dropping brand identity, a cinematic edit, or "
            "a radio-ready mix — I've got you covered."
        ),
        'about_skills':    'Python,JavaScript,React,Flask,Next.js,Figma,Adobe Illustrator,Premiere Pro,After Effects,FL Studio,Logic Pro X,Node.js,PostgreSQL,SQLite',
        'whatsapp_number': '+254700000000',
        'contact_email':   'hello@hurtl355.com',
        'instagram_url':   '#',
        'twitter_url':     '#',
        'linkedin_url':    '#',
        'behance_url':     '#',
        'soundcloud_url':  '#',
        'youtube_url':     '#',
        'logo_path':       '',
    }

    for key, value in default_settings.items():
        if not SiteSetting.query.filter_by(key=key).first():
            db.session.add(SiteSetting(key=key, value=value))

    print('✓ Default settings seeded')

    # ── 3. Portfolio works ─────────────────────────────────────────────────────
    sample_works = [
        # Graphic Design
        dict(
            title='Afrobeats EP Cover — "NightCrawl"',
            description='Full album artwork package including front cover, back cover, and social media cuts for an upcoming Afrobeats EP.',
            category='graphic',
            external_url='',
            tech_tags='',
            project_url='',
            featured=True,
            display_order=1,
        ),
        dict(
            title='Streetwear Brand Identity — VoltKE',
            description='Complete brand identity including logo, typography system, color palette, and brand guidelines for a Nairobi streetwear label.',
            category='graphic',
            external_url='',
            tech_tags='',
            project_url='',
            featured=False,
            display_order=2,
        ),
        # Video Editing
        dict(
            title='Corporate Brand Film — TechHub Nairobi',
            description='3-minute brand documentary produced and edited for a co-working space in Westlands. Drone footage, interviews, motion graphics.',
            category='video',
            external_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            tech_tags='',
            project_url='',
            featured=True,
            display_order=1,
        ),
        dict(
            title='Music Video — "Frequency" by DRVK',
            description='Stylised music video with colour grading, VFX overlays and fast-cut editing for an upcoming Kenyan drill artist.',
            category='video',
            external_url='https://youtu.be/dQw4w9WgXcQ',
            tech_tags='',
            project_url='',
            featured=False,
            display_order=2,
        ),
        # Music
        dict(
            title='Midnight Frequency (Beat)',
            description='Trap / Afro-fusion instrumental. 140 BPM. Available for licensing.',
            category='music',
            external_url='https://soundcloud.com',
            tech_tags='',
            project_url='',
            featured=True,
            display_order=1,
        ),
        dict(
            title='Golden Hour EP Mix',
            description='Full-length mix session, mastered and radio-ready. Afro-house / Amapiano.',
            category='music',
            external_url='https://open.spotify.com',
            tech_tags='',
            project_url='',
            featured=False,
            display_order=2,
        ),
        # Web / IT
        dict(
            title='E-Commerce Platform — UrbanShop KE',
            description='Full-stack e-commerce built with Next.js, Stripe payments, and a custom headless CMS. 99/100 Lighthouse score.',
            category='web',
            external_url='',
            tech_tags='Next.js,TypeScript,Stripe,PostgreSQL,Tailwind CSS',
            project_url='https://example.com',
            featured=True,
            display_order=1,
        ),
        dict(
            title='Inventory Management System',
            description='Internal tool for a Nairobi distributor: real-time stock tracking, automated low-stock alerts, PDF reports and role-based access.',
            category='web',
            external_url='',
            tech_tags='Python,Flask,SQLAlchemy,SQLite,Chart.js',
            project_url='',
            featured=False,
            display_order=2,
        ),
    ]

    works_added = 0
    for w_data in sample_works:
        if not Work.query.filter_by(title=w_data['title']).first():
            work = Work(published=True, **w_data)
            db.session.add(work)
            works_added += 1

    print(f'✓ {works_added} portfolio works seeded')

    # ── 4. Pricing packages ────────────────────────────────────────────────────
    pricing_data = {
        # IT & Web Dev
        'web': [
            {
                'tier_name': 'Basic', 'price_kes': 15000, 'price_label': '/ project',
                'is_popular': False, 'display_order': 1,
                'features': [
                    ('Responsive 5-page website', True),
                    ('Contact form', True),
                    ('SEO basics', True),
                    ('1 revision round', True),
                    ('CMS integration', False),
                    ('Custom animations', False),
                ],
            },
            {
                'tier_name': 'Standard', 'price_kes': 35000, 'price_label': '/ project',
                'is_popular': True, 'display_order': 2,
                'features': [
                    ('Responsive 10-page website', True),
                    ('Contact form + email alerts', True),
                    ('Full SEO setup', True),
                    ('3 revision rounds', True),
                    ('CMS integration', True),
                    ('Custom animations', False),
                ],
            },
            {
                'tier_name': 'Premium', 'price_kes': 75000, 'price_label': '/ project',
                'is_popular': False, 'display_order': 3,
                'features': [
                    ('Unlimited pages', True),
                    ('Custom web app / e-commerce', True),
                    ('Advanced SEO + analytics', True),
                    ('Unlimited revisions', True),
                    ('CMS + headless integration', True),
                    ('Custom animations & interactions', True),
                ],
            },
        ],
        # Graphic Design
        'graphic': [
            {
                'tier_name': 'Basic', 'price_kes': 5000, 'price_label': '/ project',
                'is_popular': False, 'display_order': 1,
                'features': [
                    ('Logo (3 concepts)', True),
                    ('PNG + JPG delivery', True),
                    ('2 revision rounds', True),
                    ('Brand guidelines', False),
                    ('Social media kit', False),
                ],
            },
            {
                'tier_name': 'Standard', 'price_kes': 12000, 'price_label': '/ project',
                'is_popular': True, 'display_order': 2,
                'features': [
                    ('Logo (5 concepts)', True),
                    ('PNG + JPG + SVG delivery', True),
                    ('5 revision rounds', True),
                    ('Mini brand guidelines', True),
                    ('Social media kit', False),
                ],
            },
            {
                'tier_name': 'Premium', 'price_kes': 28000, 'price_label': '/ project',
                'is_popular': False, 'display_order': 3,
                'features': [
                    ('Full brand identity', True),
                    ('All file formats', True),
                    ('Unlimited revisions', True),
                    ('Full brand guidelines PDF', True),
                    ('Social media kit (10 templates)', True),
                ],
            },
        ],
        # Video Editing
        'video': [
            {
                'tier_name': 'Basic', 'price_kes': 8000, 'price_label': '/ video',
                'is_popular': False, 'display_order': 1,
                'features': [
                    ('Up to 5 min edited video', True),
                    ('Colour grading', True),
                    ('Licensed background music', True),
                    ('1 revision', True),
                    ('Motion graphics', False),
                    ('VFX', False),
                ],
            },
            {
                'tier_name': 'Standard', 'price_kes': 20000, 'price_label': '/ video',
                'is_popular': True, 'display_order': 2,
                'features': [
                    ('Up to 15 min edited video', True),
                    ('Advanced colour grading', True),
                    ('Custom soundtrack/SFX', True),
                    ('3 revisions', True),
                    ('Motion graphics', True),
                    ('VFX', False),
                ],
            },
            {
                'tier_name': 'Premium', 'price_kes': 45000, 'price_label': '/ video',
                'is_popular': False, 'display_order': 3,
                'features': [
                    ('Unlimited length', True),
                    ('Cinematic colour grade', True),
                    ('Original score', True),
                    ('Unlimited revisions', True),
                    ('Full motion graphics', True),
                    ('Custom VFX', True),
                ],
            },
        ],
        # Music Production
        'music': [
            {
                'tier_name': 'Basic', 'price_kes': 6000, 'price_label': '/ track',
                'is_popular': False, 'display_order': 1,
                'features': [
                    ('Full beat / instrumental', True),
                    ('Mixing (your vocals)', True),
                    ('WAV + MP3 delivery', True),
                    ('2 revision rounds', True),
                    ('Mastering', False),
                    ('Exclusive lease', False),
                ],
            },
            {
                'tier_name': 'Standard', 'price_kes': 15000, 'price_label': '/ track',
                'is_popular': True, 'display_order': 2,
                'features': [
                    ('Full production', True),
                    ('Mixing + Mastering', True),
                    ('All stems + WAV + MP3', True),
                    ('4 revision rounds', True),
                    ('Radio-ready master', True),
                    ('Exclusive lease', False),
                ],
            },
            {
                'tier_name': 'Premium', 'price_kes': 35000, 'price_label': '/ track',
                'is_popular': False, 'display_order': 3,
                'features': [
                    ('Full production from scratch', True),
                    ('Mixing + Mastering (radio)', True),
                    ('All stems + multitracks', True),
                    ('Unlimited revisions', True),
                    ('Exclusive rights', True),
                    ('Cover art included', True),
                ],
            },
        ],
    }

    pkgs_added = 0
    for category, packages in pricing_data.items():
        for pkg_data in packages:
            key = f"{category}_{pkg_data['tier_name']}"
            exists = PricingPackage.query.filter_by(
                category=category, tier_name=pkg_data['tier_name']
            ).first()
            if not exists:
                pkg = PricingPackage(
                    category=category,
                    tier_name=pkg_data['tier_name'],
                    price_kes=pkg_data['price_kes'],
                    price_label=pkg_data['price_label'],
                    is_popular=pkg_data['is_popular'],
                    display_order=pkg_data['display_order'],
                    active=True,
                )
                db.session.add(pkg)
                db.session.flush()  # get pkg.id

                for i, (text, included) in enumerate(pkg_data['features']):
                    feat = PricingFeature(
                        package_id=pkg.id,
                        text=text,
                        included=included,
                        display_order=i,
                    )
                    db.session.add(feat)
                pkgs_added += 1

    print(f'✓ {pkgs_added} pricing packages seeded')

    # ── 5. Sample testimonials ─────────────────────────────────────────────────
    sample_testimonials = [
        dict(
            name='Amina Wanjiku',
            role='CEO, BrightPath Digital',
            rating=5,
            message='Hurtl355 built our company website from scratch and it looks absolutely stunning. The attention to detail and the speed of delivery exceeded our expectations. Highly recommend!',
            status='approved',
        ),
        dict(
            name='Brian Otieno',
            role='Independent Artist',
            rating=5,
            message="Got my EP mixed and mastered here and the quality is insane. My tracks sound like they came straight out of a top-tier studio. Will definitely be back for the next project.",
            status='approved',
        ),
        dict(
            name='Sarah Kamau',
            role='Marketing Manager, RetailKE',
            rating=5,
            message='The graphic design work for our rebrand was on another level. Very creative, responsive to feedback, and delivered everything on time. Our new brand identity is getting so many compliments!',
            status='approved',
        ),
    ]

    testimonials_added = 0
    for t_data in sample_testimonials:
        if not Testimonial.query.filter_by(name=t_data['name']).first():
            t = Testimonial(**t_data)
            db.session.add(t)
            testimonials_added += 1

    print(f'✓ {testimonials_added} testimonials seeded')

    db.session.commit()
    print('\n✅  Seed complete! You can now run the app.')
    print(f'   Admin login: {admin_username} / {admin_password}')
    print('   Open: http://127.0.0.1:5000  (site)')
    print('   Open: http://127.0.0.1:5000/admin  (admin panel)')
