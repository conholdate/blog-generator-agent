---
title: "Add Watermark to PDF in Java"
seoTitle: "Add Watermark to PDF in Java"
description: "Learn how to add a watermark to PDF files in Java using Conholdate.Total for Java. This step‑by‑step guide includes full code, setup, and configuration tips."
date: Mon, 07 Sep 2026 03:41:37 +0000
lastmod: Mon, 07 Sep 2026 03:41:37 +0000
draft: false
url: /total/add-watermark-to-pdf-in-java/
author: "Farhan Raza"
summary: "This tutorial shows Java developers how to add Watermark to PDF in Java with Conholdate.Total for Java. Follow the complete code example, learn each line, set up Maven dependencies, and tweak opacity, rotation, and alignment to create PDF watermarks."
tags: ['java pdf', 'pdf watermark', 'pdf manipulation']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/add-watermark-to-pdf-in-java.jpg
   alt: "Add Watermark to PDF in Java"
   caption: "Add Watermark to PDF in Java"
steps:
  - "Step 1: Add Conholdate.Total dependency to your Maven project"
  - "Step 2: Create a Java class that loads the source PDF"
  - "Step 3: Define a TextWatermark with desired font, color, and opacity"
  - "Step 4: Apply the watermark to every page of the PDF"
  - "Step 5: Save the watermarked document to a new file"
faqs:
  - q: "How do I add Watermark to PDF in Java using Conholdate.Total?"
    a: "Use the Watermark class from [Conholdate.Total for Java](https://products.conholdate.com/total/java/). Create a TextWatermark, configure its properties, load the source PDF with PdfLoadOptions, and call watermark.add(). Finally, save with PdfSaveOptions."
  - q: "Can I customize the appearance of the text watermark?"
    a: "Yes. You can change the font, size, color, opacity, rotation angle, and alignment. All these properties are available on the TextWatermark object as shown in the code example."
  - q: "Do I need a license to run this code in production?"
    a: "A valid license is required for production use. You can obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or view pricing options at the [pricing page](https://purchase.conholdate.com/pricing/total/family/)."
  - q: "Is it possible to add an image watermark instead of text?"
    a: "Conholdate.Total also supports image watermarks via the ImageWatermark class. The workflow is similar: create the watermark, set its properties, and add it to the PDF."
---


If you need to add Watermark to [PDF](https://docs.fileformat.com/pdf) in Java, a visual overlay can protect your documents from unauthorized use. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a powerful SDK that simplifies PDF manipulation on the server side. In this guide you will see a complete, ready‑to‑run example, learn how each line works, set up the Maven dependency, and discover options to fine‑tune opacity, rotation, and alignment for professional results.

## Complete Code Example: Adding a Text Watermark to PDF in Java

The following example demonstrates how to add a text watermark to a PDF using Conholdate.Total for Java.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.groupdocs.watermark.Watermark;
import com.groupdocs.watermark.options.PdfLoadOptions;
import com.groupdocs.watermark.options.PdfSaveOptions;
import com.groupdocs.watermark.watermarks.TextWatermark;
import com.groupdocs.watermark.watermarks.HorizontalAlignment;
import com.groupdocs.watermark.watermarks.VerticalAlignment;
import java.awt.Color;
import java.awt.Font;

public class AddPdfWatermark {
    public static void main(String[] args) {
        String inputFile = "input.pdf";
        String outputFile = "output.pdf";

        // Create a text watermark
        Font font = new Font("Arial", Font.BOLD, 48);
        TextWatermark textWatermark = new TextWatermark("CONFIDENTIAL", font);
        textWatermark.setColor(Color.RED);
        textWatermark.setOpacity(0.3);
        textWatermark.setRotationAngle(45);
        textWatermark.setHorizontalAlignment(HorizontalAlignment.Center);
        textWatermark.setVerticalAlignment(VerticalAlignment.Center);

        // Load options for the source PDF (enable caching for large files)
        PdfLoadOptions loadOptions = new PdfLoadOptions(inputFile);
        loadOptions.setCacheSize(100 * 1024 * 1024); // 100 MB cache

        // Initialize the Watermark processor
        Watermark watermark = new Watermark();

        try {
            // Apply the watermark to every page of the PDF
            watermark.add(textWatermark, loadOptions);

            // Save the watermarked PDF
            PdfSaveOptions saveOptions = new PdfSaveOptions();
            watermark.save(outputFile, saveOptions);
        } catch (Exception e) {
            System.err.println("Failed to add watermark: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `output.pdf`, etc.) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Understanding the Add Watermark to PDF in Java Code

The add Watermark to PDF in Java code follows a clear sequence that you can adapt for any PDF document.

1. **Initialize the Watermark Processor** - `Watermark watermark = new Watermark();` creates the engine that will apply watermarks.  
2. **Create a TextWatermark** - The `TextWatermark` object holds the text, font, color, opacity, and rotation.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   Font font = new Font("Arial", Font.BOLD, 48);
   TextWatermark textWatermark = new TextWatermark("CONFIDENTIAL", font);
   ```
   <!--[CODE_SNIPPET_END]-->  
3. **Configure Appearance** - Methods such as `setColor`, `setOpacity`, and `setRotationAngle` define how the watermark looks on the page.  
4. **Load the Source PDF** - `PdfLoadOptions` loads the input file and enables caching for large documents, which reduces memory pressure.  
5. **Apply and Save** - `watermark.add(textWatermark, loadOptions);` applies the watermark to every page, and `watermark.save(outputFile, saveOptions);` writes the result.

### Loading the Source PDF with Caching

When you work with multi‑megabyte PDFs, enabling a cache prevents the SDK from loading the entire document into memory. The line `loadOptions.setCacheSize(100 * 1024 * 1024);` reserves 100 MB for temporary storage, allowing the processor to stream pages as needed. This approach is especially useful in server environments where many concurrent watermarking jobs may run.

For detailed API information, see the [Java API reference](https://reference.conholdate.com/java/).

## Getting the Environment Ready for PDF Watermarking

The add Watermark to PDF in Java workflow starts with adding the Maven dependency. After that, you need a compatible JDK and a small amount of configuration.

### Prerequisites and Java Version

* Java 8 or higher is required; the SDK uses modern language features and streams.  
* Maven 3.5+ simplifies dependency management.  
* Ensure that your project's `pom.xml` includes the Conholdate repository so Maven can resolve the artifact.

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

You can also obtain the JAR files directly from the [download page](https://releases.conholdate.com/total/java/). After adding the dependency, run `mvn clean install` to verify that the SDK is on your classpath.

### Using the REST API (Optional)

If you prefer a language‑agnostic approach, Conholdate.Total also offers a REST endpoint that can add watermarks without any Java code. A simple `curl` command looks like this:

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.conholdate.com/v1/pdf/watermark" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@input.pdf" \
  -F "text=CONFIDENTIAL" \
  -F "font=Arial" \
  -F "fontSize=48" \
  -F "color=FF0000" \
  -F "opacity=0.3" \
  -F "angle=45" \
  -F "horizontalAlignment=center" \
  -F "verticalAlignment=center" \
  -o output.pdf
```
<!--[CODE_SNIPPET_END]-->

The REST version follows the same logical steps load, configure, apply, and save so you can choose the approach that best fits your architecture.

## Configuring Watermark Appearance and Position

The SDK exposes several properties that let you fine‑tune the watermark. Below are the most frequently adjusted settings.

### Customizing Font and Color

You can replace the default Arial font with any TrueType font available on the server. Changing the color is as simple as passing a different `java.awt.Color` constant or creating a custom RGB value.

```java
Font customFont = new Font("Times New Roman", Font.ITALIC, 36);
textWatermark.setColor(new Color(0, 102, 204)); // Deep blue
textWatermark.setFont(customFont);
```

### Adjusting Opacity and Rotation

Opacity controls how transparent the watermark appears. Values range from `0.0` (completely invisible) to `1.0` (fully opaque). Rotation lets you tilt the text to make it harder to remove.

```java
textWatermark.setOpacity(0.45);      // 45% opacity
textWatermark.setRotationAngle(30); // 30 degrees clockwise
```

### Aligning the Watermark on the Page

Horizontal and vertical alignment properties accept `Left`, `Center`, `Right` and `Top`, `Center`, `Bottom`. Centering is common for confidential stamps, but you can place the watermark in a corner for branding purposes.

```java
textWatermark.setHorizontalAlignment(HorizontalAlignment.Right);
textWatermark.setVerticalAlignment(VerticalAlignment.Bottom);
```

If you want to **add text Watermark to PDF in Java** with a different layout on each page, you can modify these properties inside a loop that processes pages individually. The SDK also supports image watermarks, gradient fills, and multi‑line text if your use case requires more visual complexity.

## Conclusion

Adding a watermark to PDF in Java is straightforward with [Conholdate.Total for Java](https://products.conholdate.com/total/java/). The SDK handles loading, processing, and saving PDFs efficiently, even for large files thanks to built‑in caching. By customizing opacity, rotation, font, color, and alignment you can create professional‑looking watermarks that deter unauthorized distribution. Remember to acquire a proper license for production use; you can request a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or review pricing options on the [pricing page](https://purchase.conholdate.com/pricing/total/family/). With the code and configuration steps covered, you are ready to integrate PDF watermarking into your Java applications.

## FAQs

**How can I add Watermark to PDF in Java without writing low‑level PDF code?**  
Use the `Watermark` class from [Conholdate.Total for Java](https://products.conholdate.com/total/java/). It abstracts the PDF structure, letting you focus on watermark properties such as text, font, and placement.

**What options are available to style the text watermark?**  
You can set the font (`new Font(...)`), size, style (bold, italic), color (`setColor`), opacity (`setOpacity`), rotation (`setRotationAngle`), and alignment (`setHorizontalAlignment`, `setVerticalAlignment`). These options are demonstrated in the complete code example.

**Is the SDK able to process large PDFs efficiently?**  
Yes. By configuring `PdfLoadOptions.setCacheSize`, you enable streaming and caching, which reduces memory consumption for multi‑megabyte PDFs. This makes the add Watermark to PDF in Java workflow suitable for batch processing on servers.

**Do I need to purchase a license to run this example?**  
A license is required for production deployments. Obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or explore the full pricing details at the [pricing page](https://purchase.conholdate.com/pricing/total/family/).

## Read More
- [Add Text to PDF in Java](https://blog.conholdate.com/total/add-text-to-pdf-in-java/)
- [Add Shapes to PDF in Java](https://blog.conholdate.com/total/add-shapes-to-pdf-in-java/)
- [Add Barcode to PDF in Java](https://blog.conholdate.com/total/add-barcode-to-pdf-in-java/)