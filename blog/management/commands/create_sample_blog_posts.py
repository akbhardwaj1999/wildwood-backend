"""
Django management command to create sample blog posts for testing
Usage: python manage.py create_sample_blog_posts
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from blog.models import BlogPost

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 4 sample blog posts for testing'

    def handle(self, *args, **options):
        # Get or create a default author
        author, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@wildwud.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            author.set_password('admin123')
            author.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {author.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing user: {author.username}'))

        # Sample blog posts data
        blog_posts = [
            {
                'title': 'Wildwud Website Updates: Hand-Carved Wooden Sculptures Made Easier to Find',
                'slug': 'wildwud-website-updates',
                'excerpt': 'We are excited to announce major updates to our website that make it easier than ever to discover and purchase our beautiful hand-carved wooden sculptures.',
                'content': '''<p>We are thrilled to announce some exciting updates to the Wildwud website! Our team has been working hard to improve your shopping experience and make it easier to discover our beautiful hand-carved wooden sculptures.</p>

<h2>What's New?</h2>
<p>Our website now features:</p>
<ul>
<li><strong>Enhanced Search Functionality:</strong> Find exactly what you're looking for with our improved search feature that filters by category, price, and more.</li>
<li><strong>Better Category Navigation:</strong> Browse our extensive collection of wooden sculptures organized by themes like animals, nature, and abstract designs.</li>
<li><strong>Improved Product Pages:</strong> Each product now has detailed descriptions, multiple images, and customer reviews to help you make informed decisions.</li>
<li><strong>Mobile-Friendly Design:</strong> Shop seamlessly on any device with our responsive design.</li>
</ul>

<h2>Our Commitment to Quality</h2>
<p>At Wildwud, we take pride in creating unique, hand-crafted wooden sculptures that bring warmth and character to any space. Each piece is carefully carved by skilled artisans using sustainably sourced wood.</p>

<p>Whether you're looking for a statement piece for your living room or a thoughtful gift for a loved one, our updated website makes it easier than ever to find the perfect wooden sculpture.</p>

<p>Happy shopping!</p>''',
                'published_date': timezone.now() - timedelta(days=5),
                'is_published': True,
                'meta_title': 'Wildwud Website Updates - Hand-Carved Wooden Sculptures',
                'meta_description': 'Discover the latest updates to Wildwud website. Find hand-carved wooden sculptures easier than ever with our improved navigation and search features.'
            },
            {
                'title': 'About our Hardwoods',
                'slug': 'about-our-hardwoods',
                'excerpt': 'Learn about the premium hardwoods we use in our hand-carved sculptures, including oak, walnut, mahogany, and more.',
                'content': '''<p>At Wildwud, we believe that the quality of our wooden sculptures starts with the quality of the wood itself. That's why we carefully select only the finest hardwoods for our hand-carved pieces.</p>

<h2>Types of Hardwoods We Use</h2>

<h3>Oak</h3>
<p>Oak is one of the most popular hardwoods for furniture and sculptures. Known for its strength and durability, oak has a beautiful grain pattern that adds character to any piece. We use both red oak and white oak, each with its unique characteristics.</p>

<h3>Walnut</h3>
<p>Walnut is prized for its rich, dark brown color and beautiful grain. It's a favorite among woodworkers for its workability and stunning appearance. Our walnut sculptures have a luxurious feel and timeless elegance.</p>

<h3>Mahogany</h3>
<p>Mahogany is known for its reddish-brown color and fine grain. It's a durable hardwood that resists warping and shrinking, making it perfect for detailed carvings. Our mahogany pieces have a classic, sophisticated look.</p>

<h3>Maple</h3>
<p>Maple is a light-colored hardwood with a subtle grain pattern. It's extremely hard and durable, making it ideal for intricate carvings. Our maple sculptures have a clean, modern appearance.</p>

<h2>Sustainability</h2>
<p>We are committed to using sustainably sourced hardwoods. All our wood comes from responsibly managed forests, ensuring that we're not contributing to deforestation. We work with suppliers who share our commitment to environmental stewardship.</p>

<h2>Why Hardwoods?</h2>
<p>Hardwoods offer several advantages over softwoods:</p>
<ul>
<li><strong>Durability:</strong> Hardwoods are more resistant to wear and damage</li>
<li><strong>Beautiful Grain:</strong> Each piece of hardwood has a unique grain pattern</li>
<li><strong>Workability:</strong> Hardwoods hold fine details better in carvings</li>
<li><strong>Longevity:</strong> Hardwood sculptures can last for generations</li>
</ul>

<p>When you purchase a Wildwud sculpture, you're investing in a piece that will bring beauty and joy to your home for many years to come.</p>''',
                'published_date': timezone.now() - timedelta(days=10),
                'is_published': True,
                'meta_title': 'About Our Hardwoods - Premium Wood Selection',
                'meta_description': 'Learn about the premium hardwoods used in Wildwud hand-carved sculptures, including oak, walnut, mahogany, and maple.'
            },
            {
                'title': 'Hardwood vs Engineered Wood',
                'slug': 'hardwood-vs-engineered-wood',
                'excerpt': 'Understanding the differences between solid hardwood and engineered wood to help you make the best choice for your wooden sculptures.',
                'content': '''<p>When shopping for wooden sculptures, you may come across both solid hardwood and engineered wood options. Understanding the differences can help you make an informed decision about which is right for you.</p>

<h2>What is Solid Hardwood?</h2>
<p>Solid hardwood is made from a single piece of wood, cut directly from a tree. It's the traditional material used in fine woodworking and sculpture. At Wildwud, all our sculptures are made from solid hardwood.</p>

<h3>Advantages of Solid Hardwood:</h3>
<ul>
<li><strong>Authenticity:</strong> Each piece is unique with natural grain patterns</li>
<li><strong>Durability:</strong> Can last for generations with proper care</li>
<li><strong>Repairability:</strong> Can be sanded and refinished multiple times</li>
<li><strong>Natural Beauty:</strong> The grain and color variations are natural and beautiful</li>
<li><strong>Value:</strong> Tends to appreciate in value over time</li>
</ul>

<h2>What is Engineered Wood?</h2>
<p>Engineered wood is made by binding together wood fibers, particles, or veneers with adhesives. Common types include plywood, MDF (Medium Density Fiberboard), and particle board.</p>

<h3>Characteristics of Engineered Wood:</h3>
<ul>
<li><strong>Consistency:</strong> More uniform appearance</li>
<li><strong>Cost:</strong> Generally less expensive</li>
<li><strong>Stability:</strong> Less prone to warping</li>
<li><strong>Limited Repairability:</strong> Cannot be refinished as easily</li>
<li><strong>Less Unique:</strong> More uniform appearance</li>
</ul>

<h2>Why We Choose Solid Hardwood</h2>
<p>At Wildwud, we exclusively use solid hardwood for our sculptures because:</p>

<ol>
<li><strong>Quality:</strong> Solid hardwood allows for more detailed and intricate carvings</li>
<li><strong>Durability:</strong> Our sculptures are meant to be heirloom pieces that last generations</li>
<li><strong>Beauty:</strong> The natural grain patterns and color variations make each piece unique</li>
<li><strong>Tradition:</strong> We honor the traditional craft of wood carving</li>
<li><strong>Value:</strong> Solid hardwood sculptures hold their value better over time</li>
</ol>

<h2>Making the Right Choice</h2>
<p>If you're looking for a unique, hand-crafted piece that will last for generations, solid hardwood is the right choice. While it may cost more initially, the quality, durability, and beauty make it a worthwhile investment.</p>

<p>For mass-produced decorative items, engineered wood might be sufficient. But for fine art sculptures that you want to treasure for years to come, solid hardwood is the only choice.</p>

<p>At Wildwud, we believe in creating pieces that are not just decorations, but works of art that tell a story and bring warmth to your home.</p>''',
                'published_date': timezone.now() - timedelta(days=15),
                'is_published': True,
                'meta_title': 'Hardwood vs Engineered Wood - Making the Right Choice',
                'meta_description': 'Learn the differences between solid hardwood and engineered wood to make an informed decision when purchasing wooden sculptures.'
            },
            {
                'title': 'Caring for Your Wooden Sculptures',
                'slug': 'caring-for-your-wooden-sculptures',
                'excerpt': 'Essential tips and guidelines for maintaining and preserving your hand-carved wooden sculptures to keep them looking beautiful for years.',
                'content': '''<p>Your Wildwud wooden sculpture is a work of art that, with proper care, will bring beauty to your home for many years. Here are some essential tips for maintaining and preserving your wooden sculptures.</p>

<h2>Regular Cleaning</h2>
<p>Dust your sculptures regularly with a soft, dry cloth. For detailed carvings, use a soft-bristled brush to reach into crevices. Avoid using water or cleaning products directly on the wood, as they can damage the finish.</p>

<h3>Cleaning Steps:</h3>
<ol>
<li>Use a soft, lint-free cloth or microfiber cloth</li>
<li>Gently wipe the surface to remove dust</li>
<li>For intricate details, use a soft brush</li>
<li>Never use harsh chemicals or abrasive materials</li>
</ol>

<h2>Proper Placement</h2>
<p>Where you place your sculpture can significantly impact its longevity:</p>

<ul>
<li><strong>Avoid Direct Sunlight:</strong> UV rays can fade and damage wood over time</li>
<li><strong>Maintain Stable Temperature:</strong> Avoid placing near heating vents or air conditioners</li>
<li><strong>Control Humidity:</strong> Keep humidity levels between 40-60% to prevent cracking or warping</li>
<li><strong>Elevate from Surfaces:</strong> Use a felt pad or stand to prevent scratches</li>
</ul>

<h2>Handling Your Sculpture</h2>
<p>When moving or handling your sculpture:</p>
<ul>
<li>Always lift from the base, not delicate parts</li>
<li>Use both hands to support the piece</li>
<li>Avoid touching carved details with bare hands (oils can damage wood)</li>
<li>Wrap in soft cloth when storing or transporting</li>
</ul>

<h2>Conditioning and Polishing</h2>
<p>Periodically, you may want to condition your wooden sculpture to maintain its luster:</p>

<h3>Recommended Products:</h3>
<ul>
<li>Beeswax polish (for natural finish)</li>
<li>Furniture polish specifically designed for wood</li>
<li>Lemon oil (sparingly, for dry wood)</li>
</ul>

<p><strong>Important:</strong> Always test any product on a small, inconspicuous area first. Apply sparingly and buff gently with a soft cloth.</p>

<h2>Preventing Damage</h2>
<p>To protect your investment:</p>
<ul>
<li>Keep away from pets and children's play areas</li>
<li>Don't place heavy objects on top</li>
<li>Avoid exposure to liquids</li>
<li>Don't use as a coaster or surface for other items</li>
</ul>

<h2>Seasonal Care</h2>
<p>Wood responds to seasonal changes:</p>
<ul>
<li><strong>Winter:</strong> Use a humidifier if air is very dry</li>
<li><strong>Summer:</strong> Protect from excessive heat and humidity</li>
<li><strong>Spring/Fall:</strong> Good time for deep cleaning and conditioning</li>
</ul>

<h2>When to Seek Professional Help</h2>
<p>If your sculpture shows signs of:</p>
<ul>
<li>Deep cracks or splits</li>
<li>Significant warping</li>
<li>Finish damage</li>
<li>Loose parts</li>
</ul>
<p>Consider consulting a professional wood restorer. Early intervention can prevent further damage.</p>

<h2>Long-Term Storage</h2>
<p>If you need to store your sculpture:</p>
<ol>
<li>Clean thoroughly before storing</li>
<li>Wrap in acid-free paper or soft cloth</li>
<li>Store in a climate-controlled environment</li>
<li>Check periodically for signs of damage</li>
</ol>

<p>With proper care, your Wildwud wooden sculpture will remain a beautiful centerpiece in your home for generations to come. Remember, these pieces are not just decorations—they're works of art that deserve to be treated with care and respect.</p>''',
                'published_date': timezone.now() - timedelta(days=2),
                'is_published': True,
                'meta_title': 'Caring for Your Wooden Sculptures - Maintenance Guide',
                'meta_description': 'Essential tips for maintaining and preserving your hand-carved wooden sculptures to keep them looking beautiful for years to come.'
            }
        ]

        created_count = 0
        skipped_count = 0

        for post_data in blog_posts:
            slug = post_data['slug']
            
            # Check if post already exists
            if BlogPost.objects.filter(slug=slug).exists():
                self.stdout.write(self.style.WARNING(f'Blog post "{post_data["title"]}" already exists. Skipping...'))
                skipped_count += 1
                continue

            # Create blog post
            post = BlogPost.objects.create(
                title=post_data['title'],
                slug=slug,
                content=post_data['content'],
                excerpt=post_data['excerpt'],
                author=author,
                published_date=post_data['published_date'],
                is_published=post_data['is_published'],
                meta_title=post_data.get('meta_title', ''),
                meta_description=post_data.get('meta_description', '')
            )

            self.stdout.write(self.style.SUCCESS(
                f'Created blog post: {post.title} (slug: {post.slug})'
            ))
            created_count += 1

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Sample blog posts creation completed!'))
        self.stdout.write('='*60)
        self.stdout.write(f'Posts created: {created_count}')
        self.stdout.write(f'Posts skipped: {skipped_count}')
        self.stdout.write('='*60)
        self.stdout.write('\nYou can now view these posts at:')
        self.stdout.write('Frontend: http://localhost:3000/blog')
        self.stdout.write('API: http://localhost:8000/api/blog/posts/')
        self.stdout.write('='*60)

