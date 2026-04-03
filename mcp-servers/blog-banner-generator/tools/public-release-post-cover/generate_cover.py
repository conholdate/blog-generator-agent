import argparse

from cover_generator import generate_cover_image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cover image for blog post")
    parser.add_argument(
        "--family",
        default="Aspose.PDF Cloud SDK for .NET",
        help="Product Family name, e.g. 'GroupDocs.Conversion Cloud SDK for Python'",
    )
    parser.add_argument(
        "--heading",
        default="PDF to HTML conversion",
        help="Cover title, e.g. 'JPG to PDF Conversion in .NET'",
    )
    parser.add_argument(
        "--alignment",
        default="Left",
        help="Product Family label positioning, e.g. 'Left, Right'",
    )
    parser.add_argument("--output", default="", help="Output file path (JPG)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = generate_cover_image(
        product_family=args.family,
        main_Heading=args.heading,
        product_label_alignment=args.alignment,
        output_path=args.output,
    )
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
