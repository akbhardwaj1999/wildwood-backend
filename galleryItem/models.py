import math
import json

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class Category(MPTTModel):
    title = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/images/small/', blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    # TODO: add metatags

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title


class GoogleProductCategory(models.Model):
    title = models.TextField(unique=True)

    def __str__(self):
        return self.title


class Supplier(models.Model):
    name = models.CharField(max_length=255, blank=False)
    website = models.URLField(max_length=255, blank=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Supply(models.Model):
    title = models.CharField(max_length=255, blank=False)
    description = models.TextField(blank=True)
    link = models.URLField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='supply/images/', blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Supplies'


class GalleryItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True, null=True, help_text='SEO-friendly URL (auto-generated from title)')
    description = models.TextField(blank=True)
    default_variant = models.ForeignKey('Variant', null=True, blank=True, on_delete=models.SET_NULL)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    active = models.BooleanField(default=True)
    timeStamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    total_views = models.PositiveIntegerField(default=0)
    metaKeyWords = models.CharField(max_length=255, help_text='comma delimitted set of SEO keywords')
    metaKeyDescription = models.CharField(max_length=255, help_text='content for description meta tag')
    google_product_category = models.ForeignKey(GoogleProductCategory, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Ensure uniqueness
            while GalleryItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product-variant-details", kwargs={'slug': self.slug})

    def get_update_url(self):
        return reverse("staff:product-update", kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse("staff:product-delete", kwargs={'pk': self.pk})

    def get_default_variant(self):
        if self.default_variant is None:
            self.default_variant = self.variant_set.first()
            self.save()
        return self.default_variant

    # Get average rating stars Note: We can also use 'round' instead of 'ceil' but better to show glass half full.
    def rating_stars(self):
        if self.reviews.count() > 0:
            avg_rating = math.ceil(self.reviews.aggregate(Avg('rating'))['rating__avg'])
        else:
            avg_rating = 0

        rating_stars = []
        for i in range(5):
            if i < avg_rating:
                rating_stars.append(True)
            else:
                rating_stars.append(False)
        return rating_stars

    def get_schema_markup(self, variant=None, request=None):
        """
        Generate Schema.org Product markup (JSON-LD) for SEO
        """
        if variant is None:
            variant = self.get_default_variant()
        
        # Calculate average rating
        reviews = self.reviews.all()
        review_count = reviews.count()
        if review_count > 0:
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        else:
            avg_rating = None
        
        # Build absolute URL
        if request:
            product_url = request.build_absolute_uri(self.get_absolute_url())
            image_url = request.build_absolute_uri(variant.image.url) if variant.image else None
        else:
            product_url = self.get_absolute_url()
            image_url = variant.image.url if variant.image else None
        
        # Build schema
        schema = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": self.title,
            "description": self.description if self.description else self.metaKeyDescription,
            "image": image_url,
            "url": product_url,
            "sku": str(variant.id) if variant else str(self.id),
            "brand": {
                "@type": "Brand",
                "name": "Your Store Name"  # TODO: Update with actual store name
            },
            "offers": {
                "@type": "Offer",
                "url": product_url,
                "priceCurrency": "USD",
                "price": str(variant.price) if variant else "0.00",
                "availability": "https://schema.org/InStock" if (variant and variant.in_stock) else "https://schema.org/OutOfStock",
                "priceValidUntil": "2025-12-31",  # TODO: Update with actual price validity
                "seller": {
                    "@type": "Organization",
                    "name": "Your Store Name"  # TODO: Update with actual store name
                }
            }
        }
        
        # Add aggregateRating if reviews exist
        if avg_rating and review_count > 0:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(round(avg_rating, 2)),
                "reviewCount": str(review_count),
                "bestRating": "5",
                "worstRating": "1"
            }
        
        # Add category if available
        if self.category:
            schema["category"] = self.category.title
        
        # Add individual reviews
        if review_count > 0:
            schema["review"] = []
            for review in reviews[:10]:  # Limit to 10 reviews for performance
                review_data = {
                    "@type": "Review",
                    "reviewRating": {
                        "@type": "Rating",
                        "ratingValue": str(review.rating),
                        "bestRating": "5",
                        "worstRating": "1"
                    },
                    "author": {
                        "@type": "Person",
                        "name": review.get_author() if not review.keep_anonymous else "Anonymous"
                    },
                    "datePublished": review.date_added.strftime("%Y-%m-%d") if review.date_added else ""
                }
                if review.content:
                    review_data["reviewBody"] = review.content
                schema["review"].append(review_data)
        
        return json.dumps(schema, ensure_ascii=False)


class Variant(models.Model):
    product = models.ForeignKey(GalleryItem, on_delete=models.CASCADE)
    supplies = models.ManyToManyField(Supply, related_name='variant_supply', through='VariantSupply')
    image = models.ImageField(height_field=None, width_field=None, max_length=100, upload_to='products/images/small/')
    largeImage = models.ImageField(height_field=None, width_field=None, max_length=100,
                                   upload_to='products/images/large/')
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=30, decimal_places=2)
    quantity = models.IntegerField()
    volume = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
    is_best_seller = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.product.title} ({self.title})'

    def get_price(self):
        return "{:.2f}".format(self.price)

    @property
    def in_stock(self):
        return self.quantity > 0


class VariantImage(models.Model):
    name = models.CharField(max_length=255, blank=False)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/images/')
    featured = models.BooleanField(default=False)
    thumbnail = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return f'{self.variant.product.title} ({self.variant.title})'


class VariantVideo(models.Model):
    title = models.CharField(max_length=255, blank=False)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    video = models.FileField(upload_to='products/videos/')
    thumbnail_image = models.ImageField(upload_to='products/videos/thumbnail_images/')
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return f'{self.variant.product.title}-{self.variant.title}-{self.title}'


class VariantYoutubeVideo(models.Model):
    title = models.CharField(max_length=255, blank=False)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    youtube_video_code = models.CharField(max_length=255)
    thumbnail_image = models.ImageField(upload_to='products/youtube_video/thumbnail_images/')
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return f'{self.variant.product.title}-{self.variant.title}-{self.title}'


class VariantSupply(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['variant', 'supply']
        verbose_name_plural = 'Variant Supply'

    def __str__(self):
        return f'{self.supply.title} for {self.variant.product.title}({self.variant})'

    def get_supply_required_cost_to_manufacturer(self):
        return self.supply.price * self.quantity_required


class SpecialPrice(models.Model):

    class CalculationTypes(models.TextChoices):
        ADDITION = 'addition', 'Addition'
        SUBTRACTION = 'subtraction', 'Subtraction'
        MULTIPLICATION = 'multiplication', 'Multiplication'
        DIVISION = 'division', 'Division'

    product = models.ForeignKey(GalleryItem, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    calculation_type = models.CharField(max_length=100, choices=CalculationTypes.choices)
    value = models.DecimalField(max_digits=30, decimal_places=2)

    def __str__(self):
        return f'{self.name}'

    def get_raw_special_price(self, variant):
        if self.calculation_type == self.CalculationTypes.ADDITION:
            return variant.price + self.value
        if self.calculation_type == self.CalculationTypes.SUBTRACTION:
            return variant.price - self.value
        if self.calculation_type == self.CalculationTypes.MULTIPLICATION:
            return variant.price * self.value
        if self.calculation_type == self.CalculationTypes.DIVISION:
            return variant.price / self.value

    def get_special_price(self, variant):
        return "{:.2f}".format(self.get_raw_special_price(variant))


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    product = models.ForeignKey(GalleryItem, related_name='reviews', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, related_name='reviews', blank=True, null=True, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    date_added = models.DateTimeField()
    featured = models.BooleanField(default=False)
    keep_anonymous = models.BooleanField(default=False)
    is_imported = models.BooleanField(default=False)
    import_order_id = models.IntegerField(null=True)
    import_author = models.CharField(max_length=255, blank=True)

    def __str__(self):
        if self.is_imported:
            return f'{self.product} ({self.import_author})'
        else:
            return f'{self.product} ({self.author})'

    def get_author(self):
        if self.is_imported:
            return self.import_author
        else:
            return self.author


class TransferedReview(models.Model):
    product = models.ForeignKey(GalleryItem, related_name='transfered_reviews', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=50, blank=False)
    rating = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=False)
    featured = models.BooleanField(default=False)


class WishedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(GalleryItem, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_unwished = models.BooleanField(default=False)


class Ranking(models.Model):
    MOST_FAVORITED = 'F'
    MOST_VIEWED = 'V'
    MOST_SOLD = 'S'
    CRITERIA_CHOICES = (
        (MOST_FAVORITED, 'Most Favorited'),
        (MOST_VIEWED, 'Most Viewed'),
        (MOST_SOLD, 'Most Sold'),
    )

    criteria = models.CharField(max_length=1, choices=CRITERIA_CHOICES)
    product = models.ForeignKey(GalleryItem, on_delete=models.CASCADE)
    value = models.PositiveIntegerField()
    rank = models.PositiveIntegerField()
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('criteria', 'product', 'date_added')

    def __str__(self):
        return f"{self.date_added}, {self.get_criteria_display()}, {self.product}, {self.rank}"
