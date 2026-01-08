"""Product registry for managing and querying products across blogs."""

import logging
from typing import Dict, List, Optional

from ..models import Blog, Platform, Product
from .loader import ConfigLoader

logger = logging.getLogger(__name__)


class ProductRegistry:
    """
    Central registry for all blogs, products, and platforms.
    Provides convenient methods to query and filter configurations.
    """

    def __init__(self, config_dir: str = "config"):
        self.config_loader = ConfigLoader(config_dir)
        self.blogs: Dict[str, Blog] = {}
        self.products: Dict[str, Dict[str, Product]] = (
            {}
        )  # blog_name -> {product_name -> Product}

        self._load_all()

    def _load_all(self) -> None:
        """Load all configurations."""
        self.blogs = self.config_loader.load_blogs()
        self.products = self.config_loader.load_all_products()

        logger.info(f"ProductRegistry initialized with {len(self.blogs)} blogs")
        for blog_name, products in self.products.items():
            logger.info(f"  {blog_name}: {len(products)} products")

    def get_blog(self, name: str) -> Optional[Blog]:
        """Get blog by name."""
        return self.blogs.get(name)

    def get_enabled_blogs(self) -> List[Blog]:
        """Get all enabled blogs."""
        return [blog for blog in self.blogs.values() if blog.enabled]

    def get_product(self, blog: str, product: str) -> Optional[Product]:
        """Get a specific product."""
        blog_products = self.products.get(blog, {})
        return blog_products.get(product)

    def get_products_for_blog(self, blog: str) -> Dict[str, Product]:
        """Get all products for a blog."""
        return self.products.get(blog, {})

    def get_enabled_products_for_blog(self, blog: str) -> Dict[str, Product]:
        """Get all enabled products for a blog."""
        products = self.get_products_for_blog(blog)
        return {name: prod for name, prod in products.items() if prod.enabled}

    def get_all_products(self) -> Dict[str, Dict[str, Product]]:
        """Get all products across all blogs."""
        return self.products

    def get_platform(
        self, blog: str, product: str, platform: str
    ) -> Optional[Platform]:
        """Get a specific platform configuration."""
        prod = self.get_product(blog, product)
        if prod:
            return prod.get_platform(platform)
        return None

    def list_blogs(self) -> List[str]:
        """List all blog names."""
        return list(self.blogs.keys())

    def list_products(self, blog: Optional[str] = None) -> List[str]:
        """List product names, optionally filtered by blog."""
        if blog:
            return list(self.products.get(blog, {}).keys())

        # List all products across all blogs
        all_products = set()
        for products in self.products.values():
            all_products.update(products.keys())
        return sorted(list(all_products))

    def list_platforms(self, blog: str, product: str) -> List[str]:
        """List platform names for a product."""
        prod = self.get_product(blog, product)
        if prod:
            return [p.name for p in prod.platforms]
        return []

    def get_analysis_targets(self, blog: Optional[str] = None) -> List[tuple]:
        """
        Get list of (blog, product, platform) tuples to analyze.

        Args:
            blog: If specified, only targets for this blog. If None, all blogs.

        Returns:
            List of (blog_name, product_name, platform_name) tuples
        """
        targets = []

        blogs_to_analyze = [blog] if blog else self.list_blogs()

        for blog_name in blogs_to_analyze:
            blog_obj = self.get_blog(blog_name)
            if not blog_obj or not blog_obj.enabled:
                continue

            products = self.get_enabled_products_for_blog(blog_name)
            for product_name, product in products.items():
                for platform in product.get_enabled_platforms():
                    targets.append((blog_name, product_name, platform.name))

        return targets

    def get_product_platform_groups(self, blog: Optional[str] = None) -> List[tuple]:
        """
        Get list of (blog, product, [platforms]) tuples for batch analysis.

        Args:
            blog: If specified, only for this blog. If None, all blogs.

        Returns:
            List of (blog_name, product_name, [platform_names]) tuples
        """
        groups = []

        blogs_to_analyze = [blog] if blog else self.list_blogs()

        for blog_name in blogs_to_analyze:
            blog_obj = self.get_blog(blog_name)
            if not blog_obj or not blog_obj.enabled:
                continue

            products = self.get_enabled_products_for_blog(blog_name)
            for product_name, product in products.items():
                platform_names = [p.name for p in product.get_enabled_platforms()]
                if platform_names:
                    groups.append((blog_name, product_name, platform_names))

        return groups

    def get_statistics(self) -> Dict:
        """Get statistics about the registry."""
        stats = {
            "total_blogs": len(self.blogs),
            "enabled_blogs": len(self.get_enabled_blogs()),
            "total_products": 0,
            "enabled_products": 0,
            "total_platforms": 0,
            "enabled_platforms": 0,
            "by_blog": {},
        }

        for blog_name in self.list_blogs():
            products = self.get_products_for_blog(blog_name)
            enabled_products = self.get_enabled_products_for_blog(blog_name)

            total_platforms = sum(len(p.platforms) for p in products.values())
            enabled_platforms = sum(
                len(p.get_enabled_platforms()) for p in enabled_products.values()
            )

            stats["total_products"] += len(products)
            stats["enabled_products"] += len(enabled_products)
            stats["total_platforms"] += total_platforms
            stats["enabled_platforms"] += enabled_platforms

            stats["by_blog"][blog_name] = {
                "total_products": len(products),
                "enabled_products": len(enabled_products),
                "total_platforms": total_platforms,
                "enabled_platforms": enabled_platforms,
            }

        return stats

    def validate_all(self) -> List[str]:
        """Validate all configurations. Returns list of errors."""
        return self.config_loader.validate_config()

    def reload(self) -> None:
        """Reload all configurations."""
        logger.info("Reloading all configurations")
        self._load_all()
