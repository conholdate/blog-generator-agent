---
title: "Add Shapes to PDF in Java"
seoTitle: "Add Shapes to PDF in Java"
description: "Learn how to add shapes to PDF in Java using Conholdate.Total for Java. Follow this step‑by‑step guide with code, setup, and best practices for vector graphics."
date: Fri, 05 Jun 2026 18:38:01 +0000
lastmod: Fri, 05 Jun 2026 18:38:01 +0000
draft: false
url: /total/add-shapes-to-pdf-in-java/
author: "Farhan Raza"
summary: "Learn how Java developers can add shapes like rectangles, ellipses, and lines to PDF files using Conholdate.Total for Java. This guide covers installation, implementation, shape configuration, performance tips, and best practices creating PDFs programmatically."
tags: ['conholdate total', 'java pdf shapes', 'pdf shape manipulation']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/add-shapes-to-pdf-in-java.jpg
   alt: "Add Shapes to PDF in Java"
   caption: "Add Shapes to PDF in Java"
steps:
  - "Step 1: Add Maven repository and dependency"
  - "Step 2: Load the PDF document"
  - "Step 3: Create and configure shape objects"
  - "Step 4: Add shapes to the page"
  - "Step 5: Save the updated PDF"
faqs:
  - q: "How do I add shapes to a PDF document in Java?"
    a: "Use the [Conholdate.Total for Java](https://products.conholdate.com/total/java/) SDK. Load a PDF with PdfDocument, create shape objects via ShapeFactory, set their properties, add them to a page, and save the file."
  - q: "Can I customize the color and line width of shapes?"
    a: "Yes. The Shape object exposes methods such as setFillColor, setStrokeColor, and setLineWidth. Refer to the [API reference](https://reference.conholdate.com/java/) for full details."
  - q: "Is there a performance impact when adding many shapes?"
    a: "Adding a large number of vector shapes can affect rendering time. Optimize by grouping shapes, reusing graphics state, and avoiding unnecessary transformations. See the performance section below."
  - q: "Do I need a license to use Conholdate.Total for Java in production?"
    a: "A valid license is required for production use. You can obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or view pricing options on the [pricing page](https://purchase.conholdate.com/pricing/total/family/)."
---


Adding vector graphics to [PDF](https://docs.fileformat.com/pdf) files is a common requirement for generating reports, invoices, and interactive documents. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) is a powerful SDK that simplifies PDF manipulation on the server side. In this guide you will learn how to insert rectangles, ellipses, and lines into a PDF, configure their appearance, and handle performance considerations, all with clear Java code examples.

## Steps to Add Shapes to PDF in Java
1. **Add Maven Repository and Dependency** - Include the Conholdate Maven repository and the `conholdate-total` dependency in your `pom.xml`. This makes the SDK classes such as `PdfDocument` and `ShapeFactory` available.  
   <!--[CODE_SNIPPET_START]-->
   ```xml
   <repositories>
       <repository>
           <id>conholdate-repo</id>
           <name>Conholdate Maven Repository</name>
           <url>https://repository.conholdate.com/repo/</url>
       </repository>
   </repositories>

   <dependency>
       <groupId>com.conholdate</groupId>
       <artifactId>conholdate-total</artifactId>
       <version>24.9</version>
       <type>pom</type>
   </dependency>
   ```
   <!--[CODE_SNIPPET_END]-->

2. **Load the PDF Document** - Create an instance of `PdfDocument` and open the target PDF file. The class is documented in the [API reference](https://reference.conholdate.com/java/).  
   <!--[CODE_SNIPPET_START]-->
   ```java
   PdfDocument pdf = new PdfDocument();
   pdf.open("input.pdf");
   ```

3. **Create Shape Objects** - Use `ShapeFactory` to instantiate rectangles, ellipses, or lines. Set position, size, and visual attributes.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   // Rectangle
   Shape rect = ShapeFactory.createRectangle(100, 150, 200, 100);
   rect.setFillColor(Color.BLUE);
   rect.setStrokeColor(Color.BLACK);
   rect.setLineWidth(2);

   // Ellipse
   Shape ellipse = ShapeFactory.createEllipse(350, 150, 150, 100);
   ellipse.setFillColor(Color.GREEN);
   ellipse.setStrokeColor(Color.DARK_GRAY);
   ellipse.setLineWidth(1.5f);

   // Line
   Shape line = ShapeFactory.createLine(100, 300, 500, 300);
   line.setStrokeColor(Color.RED);
   line.setLineWidth(3);
   ```

4. **Add Shapes to a Page** - Retrieve the desired page from the document and add each shape to its graphics collection.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   Page page = pdf.getPages().get_Item(0); // first page
   page.getGraphics().addShape(rect);
   page.getGraphics().addShape(ellipse);
   page.getGraphics().addShape(line);
   ```

5. **Save the Updated PDF** - After all shapes are added, save the document to a new file.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   pdf.save("output.pdf");
   pdf.close();
   ```

## Adding Shapes to PDF in Java - Complete Code Example
The following example puts all steps together into a single, ready‑to‑run program.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.conholdate.total.pdf.*;
import com.conholdate.total.pdf.shapes.*;
import java.awt.Color;

public class AddShapesDemo {
    public static void main(String[] args) throws Exception {
        // Initialize PDF document
        PdfDocument pdf = new PdfDocument();
        pdf.open("input.pdf");

        // Create rectangle
        Shape rectangle = ShapeFactory.createRectangle(100, 150, 200, 100);
        rectangle.setFillColor(Color.BLUE);
        rectangle.setStrokeColor(Color.BLACK);
        rectangle.setLineWidth(2);

        // Create ellipse
        Shape ellipse = ShapeFactory.createEllipse(350, 150, 150, 100);
        ellipse.setFillColor(Color.GREEN);
        ellipse.setStrokeColor(Color.DARK_GRAY);
        ellipse.setLineWidth(1.5f);

        // Create line
        Shape line = ShapeFactory.createLine(100, 300, 500, 300);
        line.setStrokeColor(Color.RED);
        line.setLineWidth(3);

        // Add shapes to the first page
        Page page = pdf.getPages().get_Item(0);
        page.getGraphics().addShape(rectangle);
        page.getGraphics().addShape(ellipse);
        page.getGraphics().addShape(line);

        // Save the result
        pdf.save("output.pdf");
        pdf.close();
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `output.pdf`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Installation and Setup in Java
To start using Conholdate.Total for Java, download the latest release from the official site and add the Maven dependency shown earlier. The SDK works on any Java 8+ runtime and does not require additional native libraries.

- **Download URL:** [Conholdate.Total for Java Release](https://releases.conholdate.com/total/java/)  
- **Documentation:** Detailed usage instructions are available in the [official documentation](https://docs.conholdate.com/java/).  
- **License:** Obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or view full pricing on the [pricing page](https://purchase.conholdate.com/pricing/total/family/).

## Key Features and Overview
### Add Shapes to PDF in Java with Conholdate.Total
Conholdate.Total for Java provides a unified API for creating and editing PDF content. The shape‑drawing functionality works with vector graphics, ensuring that added elements remain crisp at any zoom level. You can draw basic primitives (rectangle, ellipse, line) as well as complex paths.

### Conholdate.Total Features That Matter For This Task
- **Cross‑platform compatibility:** Works on Windows, Linux, and macOS servers.  
- **High‑performance rendering:** Shapes are rendered using the same engine that generates native PDF content, avoiding rasterization.  
- **Full control over appearance:** Set fill colors, stroke colors, line widths, opacity, and [blend](https://docs.fileformat.com/3d/blend/) modes.  
- **Layered graphics:** Add shapes to specific layers or groups for easier later manipulation.

## Configuring Shape Properties for Optimal Rendering
When adding shapes, consider the following properties to achieve the desired visual result:

- **Position and Size:** Use absolute coordinates (points) or percentages relative to the page size.  
- **Colors:** The SDK accepts `java.awt.Color` objects. For transparency, use `new Color(r, g, b, alpha)`.  
- **Line Width:** Measured in points; a value of `1` equals 1/72 inch.  
- **Opacity and Blend Mode:** Adjust with `setOpacity(float)` and `setBlendMode(BlendMode)`.  
- **Rotation and Skew:** Apply transformations via `setRotation(double)` or `setSkew(double, double)` for advanced layouts.

Example of setting advanced properties:

<!--[CODE_SNIPPET_START]-->
```java
ellipse.setOpacity(0.7f);
ellipse.setBlendMode(BlendMode.MULTIPLY);
ellipse.setRotation(45);
```
<!--[CODE_SNIPPET_END]-->

## Performance Considerations When Adding Shapes to PDFs
Adding many vector objects can increase processing time and memory usage. Follow these guidelines:

- **Batch Drawing:** Group related shapes into a single graphics container before adding them to the page.  
- **Reuse Objects:** If you need identical shapes on multiple pages, clone an existing shape instead of creating new instances.  
- **Avoid Over‑Scaling:** Define shapes at the final display size to prevent costly raster conversions.  
- **Dispose Resources:** Close the `PdfDocument` promptly to free native resources.

## Conclusion
[Conholdate.Total for Java](https://products.conholdate.com/total/java/) gives Java developers a straightforward way to add shapes to PDF documents, enabling the creation of rich, interactive reports and invoices. By following the steps, configuration tips, and performance guidelines in this guide, you can integrate vector graphics into your PDF workflow with confidence. Remember to secure a proper license for production use; a temporary license is available for evaluation, and full pricing details are listed on the [pricing page](https://purchase.conholdate.com/pricing/total/family/).

## FAQs
**How can I add a custom font to shapes in a PDF?**  
You can embed a TrueType font using `pdf.getFonts().addFont("MyFont.ttf")` and then assign it to a shape via `setFont(myFont)`. The SDK ensures the font is embedded in the final PDF.

**Is it possible to insert shapes into an existing PDF without losing existing content?**  
Yes. Opening the PDF with `PdfDocument.open()` preserves all existing pages and objects. Adding shapes to a page's graphics collection only augments the page; it does not overwrite existing content.

**What file formats can I export to after adding shapes?**  
Conholdate.Total for Java supports saving to PDF, PDF/A, PDF/X, and also to image formats such as [PNG](https://docs.fileformat.com/image/png/), [JPEG](https://docs.fileformat.com/image/jpeg/), and BMP. Use `pdf.save("output.pdf")` or `pdf.save("output.png", ImageSaveOptions.Png)` as needed.