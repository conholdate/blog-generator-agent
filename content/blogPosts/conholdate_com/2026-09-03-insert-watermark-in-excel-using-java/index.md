---
title: "Insert Watermark in Excel using Java"
seoTitle: "Insert Watermark in Excel using Java"
description: "Insert Watermark in Excel in Java with Conholdate.Total for Java. Follow this concise guide for setup, code and essential options to protect your spreadsheets."
date: Thu, 03 Sep 2026 13:20:14 +0000
lastmod: Thu, 03 Sep 2026 13:20:14 +0000
draft: false
url: /total/insert-watermark-in-excel-using-java/
author: "Farhan Raza"
summary: "This tutorial shows Java developers how to insert a watermark into XLSX or XLS workbooks using Conholdate.Total for Java. You will learn to set font, opacity, rotation and alignment, handle large files with streaming, and save the workbook with an API call."
tags: ['java excel watermark', 'excel watermarking', 'spreadsheet automation java']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/insert-watermark-in-excel-using-java.jpg
   alt: "Insert Watermark in Excel using Java"
   caption: "Insert Watermark in Excel using Java"
steps:
  - "Step 1: Add the Conholdate.Total Maven dependency to your project"
  - "Step 2: Load the workbook and create a text watermark"
  - "Step 3: Apply the watermark to all worksheets"
  - "Step 4: Save the watermarked workbook"
  - "Step 5: Release resources"
faqs:
  - q: "Can I insert Watermark in Excel in Java using an image instead of text?"
    a: "Yes, the SDK supports image watermarks. Use the ImageWatermark class as described in the [official documentation](https://docs.conholdate.com/java/)."
  - q: "Is the watermark visible after converting the workbook to PDF?"
    a: "The watermark persists in the workbook and will appear in any format you later convert, including PDF, when you use [Conholdate.Total for Java](https://products.conholdate.com/total/java/)."
  - q: "What Excel file formats are supported for watermarking?"
    a: "Both XLS and XLSX are fully supported. The library automatically detects the format during loading."
  - q: "Do I need a license to use the watermark feature in production?"
    a: "A valid license is required for production use. You can obtain a temporary license at the [temporary license page](https://purchase.conholdate.com/temporary-license/) or view pricing options at the [pricing page](https://purchase.conholdate.com/pricing/total/family/)."
---


Embedding a watermark in a spreadsheet helps protect sensitive data and signals document ownership. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a straightforward API that lets you insert Watermark in Excel in Java with just a few lines of code. This guide walks you through the required setup, the complete implementation, and key configuration options so you can secure your Excel workbooks efficiently.

## How to Insert Watermark in Excel in Java - Step by Step
### Load the Workbook with ExcelLoadOptions
1. **Load the Excel workbook**: Use `Watermarker` together with `ExcelLoadOptions` to open the file.  
   <!--[CODE_SNIPPET_START]-->
```java
Watermarker watermarker = new Watermarker(inputPath, new ExcelLoadOptions());
```
<!--[CODE_SNIPPET_END]-->  
   The `Watermarker` class is documented in the [API reference](https://reference.conholdate.com/java/). Loading with `ExcelLoadOptions` gives you control over memory usage, which is essential for large workbooks.

### Create a Text Watermark with Styling
2. **Create a text watermark**: Define font, color, opacity, rotation, and alignment.  
   <!--[CODE_SNIPPET_START]-->
```java
Font font = new Font("Arial", 36);
TextWatermark watermark = new TextWatermark("CONFIDENTIAL", font);
watermark.setColor(Color.RED);
watermark.setOpacity(0.3);
watermark.setRotationAngle(45);
watermark.setHorizontalAlignment(HorizontalAlignment.Center);
watermark.setVerticalAlignment(VerticalAlignment.Center);
```
<!--[CODE_SNIPPET_END]-->  
   Setting `opacity` to 0.3 makes the watermark semi‑transparent, while a 45‑degree rotation places it diagonally across the sheet. You can adjust these values to meet branding guidelines or compliance requirements.

### Apply the Watermark to All Worksheets
3. **Add the watermark to the workbook**: The `add` method applies it to every worksheet in a single call.  
   <!--[CODE_SNIPPET_START]-->
```java
watermarker.add(watermark);
```
<!--[CODE_SNIPPET_END]-->  
   If you need per‑worksheet control, you can retrieve individual worksheets via `watermarker.getWorksheets()` and call `add` on each one separately.

### Save the Watermarked Workbook
4. **Save the watermarked workbook**: Choose `ExcelSaveOptions` to control the output format and preserve original metadata.  
   <!--[CODE_SNIPPET_START]-->
```java
watermarker.save(outputPath, new ExcelSaveOptions());
```
<!--[CODE_SNIPPET_END]-->  
   The `ExcelSaveOptions` object lets you specify whether to keep the original file version or upgrade to the latest [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/) standard.

### Release Resources to Avoid Memory Leaks
5. **Close the Watermarker**: Release resources to avoid memory leaks, especially when processing many files in a batch.  
   <!--[CODE_SNIPPET_START]-->
```java
watermarker.close();
```
<!--[CODE_SNIPPET_END]-->  
   Closing the `Watermarker` also flushes any pending write operations, ensuring the output file is not corrupted.

These steps illustrate how to insert Watermark in Excel in Java while giving you control over appearance and performance.

## Complete Code Example: Insert Watermark in Excel in Java - Full Java Watermark
The following code demonstrates the entire process from loading the workbook to saving the result.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.groupdocs.watermark.Watermarker;
import com.groupdocs.watermark.contents.TextWatermark;
import com.groupdocs.watermark.common.Font;
import com.groupdocs.watermark.common.Color;
import com.groupdocs.watermark.contents.HorizontalAlignment;
import com.groupdocs.watermark.contents.VerticalAlignment;
import com.groupdocs.watermark.options.load.ExcelLoadOptions;
import com.groupdocs.watermark.options.save.ExcelSaveOptions;

public class ExcelWatermarkExample {
    public static void main(String[] args) {
        String inputPath = "input.xlsx";
        String outputPath = "output_watermarked.xlsx";

        Watermarker watermarker = null;
        try {
            // Load the Excel workbook (works for both XLS and XLSX)
            ExcelLoadOptions loadOptions = new ExcelLoadOptions();
            // For very large workbooks you can enable streaming mode:
            // loadOptions.setLoadAllWorksheets(false);
            watermarker = new Watermarker(inputPath, loadOptions);

            // Create a text watermark with desired appearance
            Font font = new Font("Arial", 36);
            TextWatermark watermark = new TextWatermark("CONFIDENTIAL", font);
            watermark.setColor(Color.RED);
            watermark.setOpacity(0.3);               // 30% opacity
            watermark.setRotationAngle(45);          // diagonal
            watermark.setHorizontalAlignment(HorizontalAlignment.Center);
            watermark.setVerticalAlignment(VerticalAlignment.Center);

            // Apply the watermark to all worksheets
            watermarker.add(watermark);

            // Save the watermarked workbook
            ExcelSaveOptions saveOptions = new ExcelSaveOptions();
            watermarker.save(outputPath, saveOptions);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (watermarker != null) {
                watermarker.close();
            }
        }
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.xlsx`, `output_watermarked.xlsx`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Getting the Environment Ready
### Add Maven Repository and Dependency
Add the Conholdate Maven repository and the SDK dependency to your `pom.xml`:

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

You can also download the latest JARs directly from the [download page](https://releases.conholdate.com/total/java/). The SDK requires Java 8 or higher, and a compatible IDE such as IntelliJ IDEA or Eclipse will make debugging easier.

### Configure Licensing (Production Use)
Before running the watermark code in a production environment, apply your license file:

<!--[CODE_SNIPPET_START]-->
```java
import com.groupdocs.watermark.License;

License license = new License();
license.setLicense("path/to/Conholdate.Total.Java.lic");
```
<!--[CODE_SNIPPET_END]-->  

A temporary license is available for evaluation at the [temporary license page](https://purchase.conholdate.com/temporary-license/). For long‑term projects, review the [pricing page](https://purchase.conholdate.com/pricing/total/family/) to choose the right plan.

## What Makes Conholdate.Total for Java Suitable for Excel Watermarking
### Comprehensive XLS/XLSX Support
The library handles both legacy [XLS](https://docs.fileformat.com/spreadsheet/xls/) and modern XLSX formats without requiring conversion, preserving formulas, charts, and macros.

### Efficient Streaming Mode for Large Workbooks
When working with workbooks that contain thousands of rows, enable streaming by setting `loadOptions.setLoadAllWorksheets(false)`. This reduces memory consumption dramatically.

### Rich Watermark Styling Options
You can control font family, size, color, opacity, rotation angle, and alignment. The table below summarizes the most commonly tweaked properties:

| Property                | Example Value | Impact                                                               |
|-------------------------|---------------|----------------------------------------------------------------------|
| Font                    | `new Font("Arial", 36)` | Determines the visual style of the watermark text. |
| Color                   | `Color.RED`   | Sets the watermark color; any RGB value is accepted. |
| Opacity                 | `0.3` (30%)   | Controls transparency; lower values make the watermark less intrusive. |
| Rotation Angle          | `45` degrees  | Positions the watermark diagonally for better coverage. |
| Horizontal Alignment    | `HorizontalAlignment.Center` | Places the watermark horizontally. |
| Vertical Alignment      | `VerticalAlignment.Center`   | Places the watermark vertically. |

### Automatic Worksheet Coverage
A single call to `watermarker.add(watermark)` propagates the watermark to every sheet, saving you from writing repetitive loops.

### Simple Save Options
`ExcelSaveOptions` lets you keep the original file format or upgrade to the latest XLSX version, and you can also specify whether to preserve macros.

All these capabilities are described in detail in the [official documentation](https://docs.conholdate.com/java/).

## Conclusion
In this tutorial you learned how to insert Watermark in Excel in Java using the powerful features of [Conholdate.Total for Java](https://products.conholdate.com/total/java/). By following the step‑by‑step guide, you can protect your spreadsheets with custom text, control appearance, and handle large files efficiently. For production deployments you'll need a licensed version; explore pricing on the [pricing page](https://purchase.conholdate.com/pricing/total/family/) and obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) to evaluate the SDK.

## FAQs
- **How do I add an image watermark instead of text?**  
  Use the `ImageWatermark` class, set its opacity and alignment, and add it to the `Watermarker` instance just like the text example. The image can be a [PNG](https://docs.fileformat.com/image/png/), [JPEG](https://docs.fileformat.com/image/jpeg/), or [BMP](https://docs.fileformat.com/image/bmp/), and you can also scale it to fit the worksheet. See the [API reference](https://reference.conholdate.com/java/) for details.

- **Will the watermark be visible after converting the workbook to [PDF](https://docs.fileformat.com/pdf)?**  
  Yes. The watermark is embedded in the workbook and will appear in any format you later convert, such as PDF, when using [Conholdate.Total for Java](https://products.conholdate.com/total/java/). The conversion process retains all visual elements, including watermarks.

- **Can I control the watermark on a per‑worksheet basis?**  
  The SDK applies the watermark to all worksheets by default, but you can load individual worksheets using `watermarker.getWorksheets().get_Item(index)` and call `add` on each one selectively. This gives you fine‑grained control for reports that require different branding per sheet.

- **Do I need a license for development and testing?**  
  A temporary license is available for evaluation at the [temporary license page](https://purchase.conholdate.com/temporary-license/). For commercial use, purchase a full license via the [pricing page](https://purchase.conholdate.com/pricing/total/family/). The license file must be loaded at runtime as shown in the Setup section.

## Read More
- [Convert Excel to Image in Java](https://blog.conholdate.com/total/convert-excel-to-image-in-java/)
- [AutoFit Rows or Columns in Excel using Java](https://blog.conholdate.com/total/autofit-rows-or-columns-in-excel-using-java/)
- [Convert Image to Grayscale in Java](https://blog.conholdate.com/total/convert-image-to-grayscale-in-java/)