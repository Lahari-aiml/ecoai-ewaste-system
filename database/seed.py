import os
import sys
from werkzeug.security import generate_password_hash
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import get_db, init_db
from config import Config

def seed_database(db_path=None):
    """Seed categories, recommendations, default admin, demo user, and demo providers."""
    target_path = db_path or Config.DATABASE
    init_db(target_path)
    conn = get_db(target_path)
    cur = conn.cursor()

    # Temporarily turn off foreign keys during initial seed batch
    conn.execute("PRAGMA foreign_keys = OFF;")

    # 1. Seed Categories
    categories = [
        (1, 'Repair', 'Devices with repairable hardware or software faults like cracked screens, loose ports, or degraded batteries.', 'primary', 'bi-tools'),
        (2, 'Reuse', 'Working, functional, or lightly worn electronic items suitable for donation, resale, or refurbishment.', 'success', 'bi-arrow-repeat'),
        (3, 'Recycle', 'Obsolete, burnt, shattered, or hazardous electronic equipment that must be routed to certified recyclers.', 'danger', 'bi-recycle')
    ]
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO categories (id, category_name, description, badge_color, icon)
            VALUES (?, ?, ?, ?, ?)
        """, categories)
    else:
        for cat in categories:
            cur.execute("""
                UPDATE categories
                SET category_name = ?, description = ?, badge_color = ?, icon = ?
                WHERE id = ?
            """, (cat[1], cat[2], cat[3], cat[4], cat[0]))

    # 2. Seed Recommendations
    recommendations = [
        (
            1, 1,
            'This electronic device shows strong feasibility for repair. Choosing repair prolongs equipment lifespan, conserves raw manufacturing minerals, and keeps functioning parts out of landfills.',
            '1. Consult a certified local repair technician or manufacturer authorized service center.\n2. Request a preliminary diagnostic assessment and cost estimate before proceeding.\n3. Verify whether replacement components (screen, battery, keyboard) meet OEM safety standards.\n4. If repair cost exceeds 60% of replacement value, consider parts donation or safe recycling.',
            'Power off immediately if experiencing unusual heat. If the battery is swollen or leaking, do not attempt to charge or disassemble.'
        ),
        (
            2, 2,
            'Your device is fully functional or easily restorable and can provide tremendous value to schools, charities, students, or secondary buyers.',
            '1. Back up all important files, photos, and documents to cloud storage or an external drive.\n2. Perform a cryptographic factory data reset to permanently erase all personal accounts and passwords.\n3. Remove physical SIM cards, microSD cards, and decouple from cloud accounts (Google, Apple ID, Microsoft).\n4. Clean device exterior gently with an isopropyl alcohol wipe.\n5. Include original charger, cables, and packaging if available to maximize donation utility.',
            'Always verify complete cryptographic data erasure before handing over equipment to protect your privacy.'
        ),
        (
            3, 3,
            'This device has reached end-of-life, is obsolete, or has suffered catastrophic damage. It must be sent to an authorized e-waste recycler for precious metal recovery and environmental decontamination.',
            '1. DO NOT discard in regular municipal household trash bins or incinerators.\n2. Safely isolate and package lithium-ion batteries; never bend, crush, or puncture.\n3. Cover exposed battery terminals with non-conductive electrical tape.\n4. Schedule an authorized doorstep e-waste pickup or drop off at a certified e-waste collection depot.',
            'E-waste contains hazardous toxins like lead, mercury, cadmium, and flame retardants that poison groundwater when sent to landfills.'
        )
    ]
    cur.execute("SELECT COUNT(*) FROM recommendations")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO recommendations (id, category_id, recommendation_text, instructions, safety_guidelines)
            VALUES (?, ?, ?, ?, ?)
        """, recommendations)
    else:
        for rec in recommendations:
            cur.execute("""
                UPDATE recommendations
                SET recommendation_text = ?, instructions = ?, safety_guidelines = ?
                WHERE id = ?
            """, (rec[2], rec[3], rec[4], rec[0]))

    # 3. Seed Reference E-Waste Catalog Items
    ewaste_catalog = [
        ('Smartphone with cracked screen', 'Touch screen is broken but device powers on and rings.', 1),
        ('Laptop with dead battery', 'Laptop works only when plugged into AC adapter; battery does not hold charge.', 1),
        ('Audio Amplifier with loose jack', 'Volume knob crackles and 3.5mm input socket is loose.', 1),
        ('Functional Dell Core i5 Laptop', 'Working laptop in great condition, wiped and ready for student use.', 2),
        ('Functional Kindle E-reader', 'Screen and Wi-Fi work perfectly; upgraded to newer model.', 2),
        ('Working Wi-Fi Router', 'Dual-band gigabit router, works perfectly with original power adapter.', 2),
        ('Burnt Motherboard from Power Surge', 'Severely scorched PCB with burst capacitors and melted solder.', 3),
        ('Shattered CRT Television', 'Ancient glass tube shattered with exposed wiring and toxic lead phosphor.', 3),
        ('Swollen Punctured Li-ion Battery', 'Deformed expanding battery cell leaking chemical odor.', 3),
        ('Ancient 1990s Dot Matrix Printer', 'Completely rusted mechanical gear assembly with severed cables.', 3)
    ]
    cur.execute("SELECT COUNT(*) FROM ewaste_records")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO ewaste_records (item_name, description, category_id)
            VALUES (?, ?, ?)
        """, ewaste_catalog)

    # 4. Seed Default Admin User
    admin_username = 'admin'
    admin_email = 'admin@ecoai.org'
    admin_password = 'Admin@EcoAI2026'
    admin_hash = generate_password_hash(admin_password)

    cur.execute("SELECT id FROM users WHERE username = ? OR email = ?", (admin_username, admin_email))
    existing_admin = cur.fetchone()
    if not existing_admin:
        cur.execute("""
            INSERT INTO users (name, email, username, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, 'admin', 1)
        """, ('System Administrator', admin_email, admin_username, admin_hash))
    else:
        cur.execute("""
            UPDATE users SET password_hash = ?, role = 'admin', is_active = 1
            WHERE username = ?
        """, (admin_hash, admin_username))

    # 5. Seed Demo User
    demo_username = 'demo_user'
    demo_email = 'demo@ecoai.org'
    demo_password = 'User@EcoAI2026'
    demo_hash = generate_password_hash(demo_password)

    cur.execute("SELECT id FROM users WHERE username = ? OR email = ?", (demo_username, demo_email))
    existing_demo = cur.fetchone()
    if not existing_demo:
        cur.execute("""
            INSERT INTO users (name, email, username, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, 'user', 1)
        """, ('Demo Citizen', demo_email, demo_username, demo_hash))
    else:
        cur.execute("""
            UPDATE users SET password_hash = ?, role = 'user', is_active = 1
            WHERE username = ?
        """, (demo_hash, demo_username))

    # 6. Seed Demo Service Providers (Clearly labelled Demo / Sample)
    providers = [
        # Bengaluru
        ('EcoFix Tech Care & Repair', 1, '+91 98450 11223', 'support@ecofixblr.demo', '104 100ft Road, Indiranagar', 'Bengaluru', 12.9784, 77.6408, 1, 1, 'Demo / Sample'),
        ('QuickCircuit Electronics Hospital', 1, '+91 98450 22334', 'info@quickcircuit.demo', '52 5th Block, Koramangala', 'Bengaluru', 12.9352, 77.6245, 1, 1, 'Demo / Sample'),
        ('Bangalore Reuse & Donate Hub', 2, '+91 98450 33445', 'donate@blr-reuse.demo', '88 4th Cross, Jayanagar 4th Block', 'Bengaluru', 12.9299, 77.5824, 1, 1, 'Demo / Sample'),
        ('RenewGadgets Refurbishment Center', 2, '+91 98450 44556', 'renew@renewgadgets.demo', '12 ITPL Main Rd, Whitefield', 'Bengaluru', 12.9856, 77.7289, 1, 1, 'Demo / Sample'),
        ('GreenEarth Authorized E-Waste Recycler', 3, '+91 98450 55667', 'pickup@greenearth-recycle.demo', 'Plot 45, Peenya Industrial Area 2nd Stage', 'Bengaluru', 13.0334, 77.5140, 1, 1, 'Demo / Sample'),
        ('EcoMetal Clean E-Waste Recovery', 3, '+91 98450 66778', 'contact@ecometal.demo', 'Plot 19, Electronic City Phase 1', 'Bengaluru', 12.8452, 77.6602, 1, 1, 'Demo / Sample'),

        # Hyderabad
        ('CyberFix Tech Care Lab', 1, '+91 99890 12345', 'service@cyberfixhyd.demo', 'Shop 14, Silicon Valley Towers, Madhapur', 'Hyderabad', 17.4483, 78.3915, 1, 1, 'Demo / Sample'),
        ('Telangana E-Reuse & Donation Hub', 2, '+91 99890 23456', 'help@tg-reuse.demo', 'Road No. 36, Jubilee Hills', 'Hyderabad', 17.4319, 78.4073, 1, 1, 'Demo / Sample'),
        ('Deccan Green E-Waste Recycling Depot', 3, '+91 99890 34567', 'recycle@deccangreen.demo', 'IDA Mallapur Industrial Zone', 'Hyderabad', 17.4398, 78.5831, 1, 1, 'Demo / Sample'),

        # Delhi NCR
        ('Nehru Place Hardware Repair Consortium', 1, '+91 98110 12345', 'care@np-repair.demo', 'G-12 Hemkunt Chambers, Nehru Place', 'New Delhi', 28.5492, 77.2530, 1, 1, 'Demo / Sample'),
        ('Capital Donate & Refurbish Hub', 2, '+91 98110 23456', 'contact@cap-reuse.demo', 'Block C, Connaught Place', 'New Delhi', 28.6328, 77.2197, 1, 1, 'Demo / Sample'),
        ('Clean Yamuna E-Waste Recyclers', 3, '+91 98110 34567', 'dispatch@cleanyamuna.demo', 'Sector 62, Noida Electronic City', 'Noida', 28.6280, 77.3649, 1, 1, 'Demo / Sample'),

        # Mumbai
        ('MaxRepair Electronics Service Center', 1, '+91 98200 12345', 'service@maxrepairmumbai.demo', 'Near Station, Andheri West', 'Mumbai', 19.1197, 72.8468, 1, 1, 'Demo / Sample'),
        ('Aamchi Mumbai Device Reuse Collective', 2, '+91 98200 23456', 'support@mumbaireuse.demo', 'Linking Road, Bandra West', 'Mumbai', 19.0600, 72.8360, 1, 1, 'Demo / Sample'),
        ('Western India Certified E-Waste Plant', 3, '+91 98200 34567', 'info@west-ewaste.demo', 'MIDC Industrial Estate, Navi Mumbai', 'Navi Mumbai', 19.0988, 73.0152, 1, 1, 'Demo / Sample'),

        # Chennai
        ('Madras Precision Repair Clinic', 1, '+91 98400 12345', 'care@madrasrepair.demo', 'Usman Road, T. Nagar', 'Chennai', 13.0418, 80.2341, 1, 1, 'Demo / Sample'),
        ('Coromandel E-Waste Solutions', 3, '+91 98400 34567', 'cleanup@coromandel.demo', 'OMR IT Highway, Sholinganallur', 'Chennai', 12.9010, 80.2279, 1, 1, 'Demo / Sample'),

        # Pune
        ('Pune TechCare Restoration Lab', 1, '+91 98220 12345', 'contact@punetechcare.demo', 'FC Road, Shivajinagar', 'Pune', 18.5284, 73.8415, 1, 1, 'Demo / Sample'),
        ('Sahyadri Green Recycling Network', 3, '+91 98220 34567', 'recycle@sahyadri.demo', 'Bhosari MIDC, Pimpri-Chinchwad', 'Pune', 18.6279, 73.8427, 1, 1, 'Demo / Sample')
    ]

    cur.execute("SELECT COUNT(*) FROM service_providers")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO service_providers (
                name, category_id, phone, email, address, city, latitude, longitude, offers_pickup, is_active, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, providers)

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.close()

if __name__ == '__main__':
    seed_database()
