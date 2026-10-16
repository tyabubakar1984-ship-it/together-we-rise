from app import app, db, User

with app.app_context():
    # Show all members
    all_members = User.query.all()
    print(f"Found {len(all_members)} members:")
    for m in all_members:
        print(f"- {m.name} | {m.email}")

    # Keep only YOU (admin)
    admin_email = "hm3516674@gmail.com"
    deleted = 0
    for m in all_members:
        if m.email != admin_email:
            db.session.delete(m)
            deleted += 1
    
    db.session.commit()
    print(f"✅ Deleted {deleted} fake members!")
    print(f"Now only {User.query.count()} member left - YOU!")