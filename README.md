# Library-service-project

## How to run:
- Copy `.env.sample` to `.env` and fill in all required environment variables.

- Run:

```bash
docker compose up --build
docker compose exec app python manage.py loaddata data.json
```
Test Users:
Admin: 
 - admin@admin.com 
 - admin123 
User: 
 - user@user.com 
 - user123

## Features

- User registration and authentication
- User profile management
- Create, update and delete books for admin users
- Users can borrow books and pay for the borrowing period
- Administrators receive Telegram notifications about new borrowings
- Administrators can view all borrowings and payments
- Overdue borrowings generate a fine based on a configurable multiplier
- Stripe integration for online payments
- Automated overdue borrower checks using Django Q

## Documentation
Swagger:
http://localhost:8000/doc/swagger/