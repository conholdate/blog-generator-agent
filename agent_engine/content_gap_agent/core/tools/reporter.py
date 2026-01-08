"""Report generation for analysis results."""

import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List


class ReportGenerator:
    """Generates reports from analysis results."""

    @staticmethod
    def generate_json_report(gaps: List[Dict], output_path: str) -> None:
        """Generate JSON report for programmatic consumption."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_gaps": len(gaps),
            "gaps": gaps,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nJSON report saved to: {output_path}")

    @staticmethod
    def generate_markdown_report(gaps: List[Dict], output_path: str) -> None:
        """Generate human-readable markdown report."""
        # Sort by priority
        sorted_gaps = sorted(gaps, key=lambda x: x.get("priority", 0), reverse=True)

        # Group by category
        by_category = defaultdict(list)
        for gap in sorted_gaps:
            category = gap.get("category", "Uncategorized")
            by_category[category].append(gap)

        # Generate report
        lines = [
            "# Aspose.Cells for .NET - Missing Blog Topics",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n**Total Content Gaps Identified:** {len(gaps)}\n",
            "---\n",
            "## Executive Summary\n",
            f"This report identifies {len(gaps)} potential blog topics based on analysis of:",
            "- Aspose.Cells for .NET Documentation",
            "- Aspose.Cells for .NET API References",
            "- Existing Aspose Blog Posts\n",
            "Topics are prioritized by importance, lack of existing coverage, and potential value to developers.\n",
            "---\n",
        ]

        # Add high priority topics
        high_priority = [g for g in sorted_gaps if g.get("priority", 0) >= 4]
        if high_priority:
            lines.append("## High Priority Topics\n")
            for gap in high_priority:
                lines.extend(ReportGenerator._format_gap_item(gap))
            lines.append("\n---\n")

        # Add by category
        lines.append("## Topics by Category\n")
        for category, items in sorted(by_category.items()):
            lines.append(f"### {category}\n")
            for gap in items:
                lines.extend(ReportGenerator._format_gap_item(gap, compact=True))
            lines.append("")

        # Write report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"Markdown report saved to: {output_path}")

    @staticmethod
    def _format_gap_item(gap: Dict, compact: bool = False) -> List[str]:
        """Format a single gap item for markdown."""
        priority = gap.get("priority", 0)
        priority_label = (
            "HIGH" if priority >= 4 else "MEDIUM" if priority >= 3 else "LOW"
        )

        lines = [
            f"#### {gap.get('topic', 'Unknown Topic')} (Priority: {priority}/5 - {priority_label})\n",
            f"**Suggested Title:** {gap.get('suggested_title', 'TBD')}\n",
            f"**Target Audience:** {gap.get('target_audience', 'All levels')}\n",
        ]

        if not compact:
            lines.extend(
                [
                    f"**Why This Gap Exists:** {gap.get('gap_reason', 'Not documented in blogs')}\n",
                    f"**What to Cover:**\n{gap.get('outline', 'TBD')}\n",
                    f"**Value to Developers:** {gap.get('estimated_value', 'High')}\n",
                    f"**Keywords:** {', '.join(gap.get('keywords', []))}\n",
                ]
            )

        lines.append("")
        return lines
