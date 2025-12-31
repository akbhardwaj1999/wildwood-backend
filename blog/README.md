# Blog App

## Running Tests

To run all blog tests:

```bash
python manage.py test blog
```

To run specific test files:

```bash
# Run API tests
python manage.py test blog.tests_api

# Run model tests
python manage.py test blog.tests
```

## Creating Sample Blog Posts

To create 4 sample blog posts for testing:

```bash
python manage.py create_sample_blog_posts
```

This will create:
1. Wildwud Website Updates
2. About our Hardwoods
3. Hardwood vs Engineered Wood
4. Caring for Your Wooden Sculptures

All posts will be published and ready to view on the frontend.

## Test Coverage

The test suite covers:
- ✅ Blog post listing API
- ✅ Blog post detail API
- ✅ Published/Unpublished filtering
- ✅ Slug-based retrieval
- ✅ Author information
- ✅ Date formatting
- ✅ Model creation and validation
- ✅ Auto-slug generation
- ✅ Permissions (public access)
- ✅ Field validation
- ✅ Ordering (newest first)

