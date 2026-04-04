from fastmcp import FastMCP

from cover_generator import generate_cover_image

mcp = FastMCP("cover_image_generator")


@mcp.tool()
async def generate_blog_image(
    product_family: str,
    main_Heading: str,
    product_label_alignment: str,
    output_path: str,
):
    output_file_path = generate_cover_image(
        product_family=product_family,
        main_Heading=main_Heading,
        product_label_alignment=product_label_alignment,
        output_path=output_path,
    )
    return {"output_path": output_file_path}


if __name__ == "__main__":
    mcp.run()
