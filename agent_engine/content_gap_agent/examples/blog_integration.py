"""
Example: Integration with Blog Generator
This module demonstrates how to use the analyzer output with a blog generator agent.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class BlogGeneratorIntegration:
    """
    Example integration showing how to consume analyzer output
    and pass topics to a blog generator.
    """

    def __init__(self, analysis_dir: str = "./output"):
        self.analysis_dir = Path(analysis_dir)

    def get_latest_analysis(self) -> Dict:
        """Get the most recent analysis report."""
        json_files = sorted(
            self.analysis_dir.glob("missing_topics_*.json"), reverse=True
        )

        if not json_files:
            raise FileNotFoundError(
                f"No analysis reports found in {self.analysis_dir}"
            )

        latest_file = json_files[0]
        print(f"Loading analysis from: {latest_file.name}")

        with open(latest_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def filter_high_priority_topics(
        self, analysis: Dict, min_priority: int = 4
    ) -> List[Dict]:
        """Filter topics by priority level."""
        gaps = analysis.get("gaps", [])
        high_priority = [
            gap for gap in gaps if gap.get("priority", 0) >= min_priority
        ]

        print(
            f"Found {len(high_priority)} high-priority topics (priority >= {min_priority})"
        )
        return high_priority

    def filter_by_category(self, topics: List[Dict], category: str) -> List[Dict]:
        """Filter topics by category."""
        filtered = [
            topic
            for topic in topics
            if topic.get("category", "").lower() == category.lower()
        ]

        print(f"Found {len(filtered)} topics in category '{category}'")
        return filtered

    def filter_by_audience(self, topics: List[Dict], audience: str) -> List[Dict]:
        """Filter topics by target audience."""
        filtered = [
            topic
            for topic in topics
            if topic.get("target_audience", "").lower() == audience.lower()
        ]

        print(f"Found {len(filtered)} topics for '{audience}' audience")
        return filtered

    def prepare_blog_request(self, topic: Dict) -> Dict:
        """
        Convert an analyzer topic into a blog generator request format.
        Customize this based on your blog generator's API.
        """
        return {
            "title": topic.get("suggested_title"),
            "outline": topic.get("outline"),
            "keywords": topic.get("keywords", []),
            "target_audience": topic.get("target_audience"),
            "category": topic.get("category"),
            "metadata": {
                "priority": topic.get("priority"),
                "estimated_value": topic.get("estimated_value"),
                "source": "content_gap_agent",
                "generated_at": datetime.now().isoformat(),
            },
        }

    def generate_blog_queue(
        self, topics: List[Dict], max_topics: int = 5
    ) -> List[Dict]:
        """
        Generate a queue of blog posts to create.
        Returns a list ready for your blog generator.
        """
        # Sort by priority
        sorted_topics = sorted(
            topics, key=lambda x: x.get("priority", 0), reverse=True
        )

        # Take top N topics
        selected = sorted_topics[:max_topics]

        # Convert to blog generator format
        blog_queue = [self.prepare_blog_request(topic) for topic in selected]

        print(f"\nGenerated queue of {len(blog_queue)} blog posts")
        return blog_queue

    def save_blog_queue(
        self, blog_queue: List[Dict], output_file: str = "blog_queue.json"
    ) -> Path:
        """Save the blog queue to a file."""
        output_path = self.analysis_dir / output_file

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "total_posts": len(blog_queue),
                    "posts": blog_queue,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"Blog queue saved to: {output_path}")
        return output_path


def example_simple_usage() -> None:
    """Example: Simple usage - get top 5 high-priority topics."""
    print("\n" + "=" * 60)
    print("Example: Simple Usage - Top 5 High-Priority Topics")
    print("=" * 60)

    integration = BlogGeneratorIntegration()

    # Load latest analysis
    analysis = integration.get_latest_analysis()

    # Get high-priority topics
    high_priority = integration.filter_high_priority_topics(analysis, min_priority=4)

    # Generate blog queue
    blog_queue = integration.generate_blog_queue(high_priority, max_topics=5)

    # Save for blog generator
    queue_file = integration.save_blog_queue(blog_queue, "blog_queue_simple.json")

    print("\nReady to pass to blog generator!")
    print(f"   Use: {queue_file}")


def example_filtered_usage() -> None:
    """Example: Filtered by category and audience."""
    print("\n" + "=" * 60)
    print("Example: Filtered by Category and Audience")
    print("=" * 60)

    integration = BlogGeneratorIntegration()

    # Load latest analysis
    analysis = integration.get_latest_analysis()

    # Get all topics
    all_topics = analysis.get("gaps", [])

    # Filter by category (e.g., focus on Charts for this month)
    charts_topics = integration.filter_by_category(
        all_topics, "Charts and Visualization"
    )

    # Filter by audience (e.g., intermediate developers)
    intermediate_topics = integration.filter_by_audience(charts_topics, "intermediate")

    # Generate blog queue
    blog_queue = integration.generate_blog_queue(intermediate_topics, max_topics=3)

    # Save
    queue_file = integration.save_blog_queue(
        blog_queue, "blog_queue_charts_intermediate.json"
    )

    print("\nCategory-specific queue ready!")
    print(f"   Use: {queue_file}")


if __name__ == "__main__":
    try:
        example_simple_usage()
        example_filtered_usage()
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nTip: Run the analyzer first to generate analysis reports:")
        print("   python -m content_gap_agent")
