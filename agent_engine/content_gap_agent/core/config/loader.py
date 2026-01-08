"""Configuration loader for YAML-based product and blog definitions."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from ..models import Blog, Platform, Product

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and parses YAML configuration files."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Configuration directory not found: {config_dir}")

        self.blogs_file = self.config_dir / "blogs.yaml"
        # Products are now loaded from brand subdirectories (e.g., config/aspose/cells.yaml)

        logger.info(f"ConfigLoader initialized with config_dir: {config_dir}")

    def load_blogs(self) -> Dict[str, Blog]:
        """Load all blog configurations."""
        if not self.blogs_file.exists():
            raise FileNotFoundError(
                f"Blogs configuration not found: {self.blogs_file}"
            )

        with open(self.blogs_file, "r") as f:
            data = yaml.safe_load(f)

        blogs = {}
        for name, config in data.get("blogs", {}).items():
            blogs[name] = Blog(
                name=name,
                display_name=config["display_name"],
                blog_repo=config["blog_repo"],
                blog_branch=config.get("blog_branch", "master"),
                website=config["website"],
                search_patterns=config.get("search_patterns", []),
                enabled=config.get("enabled", True),
            )

        logger.info(f"Loaded {len(blogs)} blog configurations")
        return blogs

    def load_products_for_blog(self, blog_name: str) -> Dict[str, Product]:
        """Load all products for a specific blog from individual product YAML files.
        
        Products are loaded from config/{blog_name}/ directory.
        Each YAML file represents one product (e.g., cells.yaml for Aspose.Cells).
        """
        brand_dir = self.config_dir / blog_name

        if not brand_dir.exists() or not brand_dir.is_dir():
            logger.warning(f"No products directory found for blog: {blog_name}")
            return {}

        products = {}
        
        # Find all YAML files in the brand directory
        for product_file in brand_dir.glob("*.yaml"):
            product_name = product_file.stem  # e.g., "cells" from "cells.yaml"
            
            try:
                product = self._load_product_from_file(product_file, blog_name, product_name)
                if product:
                    products[product_name] = product
            except Exception as e:
                logger.error(f"Error loading product {product_name} for {blog_name}: {e}")

        logger.info(f"Loaded {len(products)} products for blog: {blog_name}")
        return products

    def load_single_product(self, blog_name: str, product_name: str) -> Optional[Product]:
        """Load a single product configuration.
        
        Args:
            blog_name: Brand/blog key (e.g., 'aspose')
            product_name: Product key (e.g., 'cells')
            
        Returns:
            Product object if found, None otherwise
        """
        product_file = self.config_dir / blog_name / f"{product_name}.yaml"
        
        if not product_file.exists():
            logger.warning(f"Product file not found: {product_file}")
            return None
            
        return self._load_product_from_file(product_file, blog_name, product_name)

    def _load_product_from_file(
        self, product_file: Path, blog_name: str, product_name: str
    ) -> Optional[Product]:
        """Load a single product from a YAML file."""
        with open(product_file, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Load platform definitions if they exist
        platform_definitions = data.get("platform_definitions", {})

        platforms = []
        
        # Get product-level repo URLs (shared across platforms)
        product_doc_repo = data.get("doc_repo")
        product_doc_branch = data.get("doc_branch", "master")
        product_api_repo = data.get("api_repo")
        product_api_branch = data.get("api_branch", "main")
        product_tut_repo = data.get("tut_repo")
        product_tut_branch = data.get("tut_branch", "main")

        for platform_config in data.get("platforms", []):
            # Platform config can be a dict with a single key
            if isinstance(platform_config, dict):
                platform_name = list(platform_config.keys())[0]
                platform_data = platform_config[platform_name]
            else:
                continue

            # Get definition if referenced
            definition_name = platform_data.get("definition")
            if definition_name and definition_name in platform_definitions:
                definition = platform_definitions[definition_name]
                display_name = definition.get("display_name", platform_name)
                keywords = definition.get("keywords", [])
            else:
                display_name = platform_data.get("display_name", platform_name)
                keywords = platform_data.get("keywords", [])

            # Use platform-level repo URLs if provided, otherwise use product-level
            platform = Platform(
                name=platform_name,
                display_name=display_name,
                doc_repo=platform_data.get("doc_repo", product_doc_repo),
                doc_branch=platform_data.get("doc_branch", product_doc_branch),
                doc_path=platform_data.get("doc_path", ""),
                api_repo=platform_data.get("api_repo", product_api_repo),
                api_branch=platform_data.get("api_branch", product_api_branch),
                api_path=platform_data.get("api_path", ""),
                tut_repo=platform_data.get("tut_repo", product_tut_repo),
                tut_branch=platform_data.get("tut_branch", product_tut_branch),
                tut_path=platform_data.get("tut_path"),
                keywords=keywords,
                enabled=platform_data.get("enabled", True),
            )
            platforms.append(platform)

        product = Product(
            name=product_name,
            display_name=data.get("display_name", product_name),
            blog=blog_name,
            description=data.get("description", ""),
            platforms=platforms,
            enabled=data.get("enabled", True),
        )
        
        return product

    def load_all_products(self) -> Dict[str, Dict[str, Product]]:
        """Load all products for all blogs."""
        blogs = self.load_blogs()
        all_products = {}

        for blog_name in blogs.keys():
            products = self.load_products_for_blog(blog_name)
            if products:
                all_products[blog_name] = products

        logger.info(f"Loaded products for {len(all_products)} blogs")
        return all_products

    def validate_config(self, blog_name: Optional[str] = None) -> List[str]:
        """
        Validate configuration files.
        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Validate blogs.yaml
        try:
            blogs = self.load_blogs()
            if not blogs:
                errors.append("No blogs defined in blogs.yaml")
        except Exception as e:
            errors.append(f"Error loading blogs.yaml: {e}")
            return errors

        # Validate specific blog or all blogs
        blogs_to_validate = [blog_name] if blog_name else blogs.keys()

        for blog in blogs_to_validate:
            try:
                products = self.load_products_for_blog(blog)

                if not products:
                    errors.append(f"No products defined for blog: {blog}")
                    continue

                for product_name, product in products.items():
                    # Validate product has at least one platform
                    if not product.platforms:
                        errors.append(f"{blog}.{product_name}: No platforms defined")

                    # Validate each platform
                    for platform in product.platforms:
                        # Check required fields
                        if not platform.doc_repo:
                            errors.append(
                                f"{blog}.{product_name}.{platform.name}: doc_repo is required"
                            )
                        if not platform.api_repo:
                            errors.append(
                                f"{blog}.{product_name}.{platform.name}: api_repo is required"
                            )
                        if not platform.doc_path:
                            errors.append(
                                f"{blog}.{product_name}.{platform.name}: doc_path is required"
                            )
                        if not platform.api_path:
                            errors.append(
                                f"{blog}.{product_name}.{platform.name}: api_path is required"
                            )

            except Exception as e:
                errors.append(f"Error loading products for {blog}: {e}")

        return errors


class ConfigValidator:
    """Validates configuration files and provides helpful error messages."""

    @staticmethod
    def validate_yaml_syntax(file_path: Path) -> Optional[str]:
        """Validate YAML syntax. Returns error message if invalid."""
        try:
            with open(file_path, "r") as f:
                yaml.safe_load(f)
            return None
        except yaml.YAMLError as e:
            return f"YAML syntax error in {file_path}: {e}"
        except Exception as e:
            return f"Error reading {file_path}: {e}"

    @staticmethod
    def validate_required_fields(
        config: dict, required: List[str], context: str
    ) -> List[str]:
        """Validate required fields exist in config."""
        errors = []
        for field in required:
            if field not in config:
                errors.append(f"{context}: Missing required field '{field}'")
        return errors
