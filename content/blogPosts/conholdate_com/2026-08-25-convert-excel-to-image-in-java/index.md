---
title: "Convert Excel to Image in Java"
seoTitle: "Convert Excel to Image in Java"
description: "Learn how to convert Excel to image in Java using Conholdate.Total for Java. Step-by-step guide, code example, and configuration tips for PNG output."
date: Tue, 25 Aug 2026 19:13:32 +0000
lastmod: Tue, 25 Aug 2026 19:13:32 +0000
draft: false
url: /total/convert-excel-to-image-in-java/
author: "Farhan Raza"
summary: "This tutorial shows Java developers how to convert Excel to image using Conholdate.Total for Java. You will learn to load workbooks with charts, set PNG conversion options, process each sheet, and generate images ready for reporting or UI display."
tags: ['java excel image', 'excel chart export', 'spreadsheet image generation']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/convert-excel-to-image-in-java.jpg
   alt: "Convert Excel to Image in Java"
   caption: "Convert Excel to Image in Java"
steps:
  - "Add Conholdate.Total Maven repository and dependency"
  - "Create output directory for generated images"
  - "Load Excel workbook with chart and formula support"
  - "Configure PNG image conversion options"
  - "Iterate over worksheets and convert each to an image"
faqs:
  - q: "How can I convert Excel to image in Java?"
    a: "Use [Conholdate.Total for Java](https://products.conholdate.com/total/java/) with the Conversion API. Load the workbook, set ImageConvertOptions, and call convert for each sheet."
  - q: "Can I convert a specific Excel chart to an image?"
    a: "Yes. Enable chart loading in ExcelLoadOptions and specify the chart's page number when configuring ImageConvertOptions."
  - q: "Is it possible to convert only a range of cells to an image?"
    a: "You can define a range in ExcelLoadOptions or use the pageNumber property to target the desired area before conversion."
  - q: "What licensing is required for production use?"
    a: "A commercial license is needed. Review pricing at [Conholdate.Total pricing](https://purchase.conholdate.com/pricing/total/family/) and obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/)."
---


Generating visual previews of spreadsheet data is a frequent requirement when building reporting dashboards or email summaries. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a robust SDK that simplifies the process of converting Excel to image in Java applications. In this guide you will see how to load an [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/) workbook, configure [PNG](https://docs.fileformat.com/image/png/) output, and produce image files for entire worksheets, charts, or specific ranges. By the end you'll have a ready‑to‑run code sample that you can adapt to your own projects.

## What Convert Excel Files to Image Demands from Your Application

Developers often need to turn spreadsheet content into static images for web previews, [PDF](https://docs.fileformat.com/pdf) reports, or mobile thumbnails. The requirement typically includes preserving [cell](https://docs.fileformat.com/spreadsheet/cell/) formatting, rendering embedded charts, and optionally limiting the conversion to a single range. Handling these tasks manually by opening Excel, taking screenshots, and saving them does not scale and can lead to inconsistent results.

Technical constraints for a reliable solution are: support for XLSX files, ability to include charts and formulas, configurable image resolution, and batch processing of multiple worksheets. The conversion must run on a server or desktop environment without requiring Microsoft Office.

## Choosing Conholdate.Total for Java for the Job

[Conholdate.Total for Java](https://products.conholdate.com/total/java/) offers a unified API that covers all the needed capabilities. Its **ExcelLoadOptions** let you load charts and formulas, while **ImageConvertOptions** give fine‑grained control over format, quality, and dimensions. The SDK works on any Java runtime, requires only the Maven dependency, and handles large workbooks efficiently.

For detailed API usage see the [official documentation](https://docs.conholdate.com/java/). The full reference for classes such as `Conversion`, `ExcelLoadOptions`, and `ImageConvertOptions` is available in the [API reference](https://reference.conholdate.com/java/). You can download the latest library from the [release page](https://releases.conholdate.com/total/java/).

## Implementing Excel To Image Conversion in Java

The conversion process can be broken down into a few clear steps. The following sections walk you through each part, with short code excerpts taken directly from the full example.

### Install Conholdate.Total for Java via Maven

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

### Load Excel File with Chart and Formula Support

Create an `ExcelLoadOptions` instance, enable chart and formula loading, and initialise the `Conversion` object with a file stream:

<!--[CODE_SNIPPET_START]-->
```java
ExcelLoadOptions loadOptions = new ExcelLoadOptions();
loadOptions.setLoadCharts(true);
loadOptions.setLoadFormulas(true);

Conversion conversion = new Conversion(new FileInputStream("input.xlsx"), loadOptions);
```
<!--[CODE_SNIPPET_END]-->

### Configure Image Output Options for PNG

Set the desired image format, quality, and dimensions. Width is fixed while height preserves the aspect ratio:

<!--[CODE_SNIPPET_START]-->
```java
ImageConvertOptions imgOptions = new ImageConvertOptions();
imgOptions.setFormat(ImageConvertOptions.ImageFormat.PNG);
imgOptions.setQuality(90);
imgOptions.setWidth(1200);
imgOptions.setHeight(0); // preserve aspect ratio
```
<!--[CODE_SNIPPET_END]-->

### Convert Each Worksheet or Range to PNG Images

Iterate over the workbook pages (sheets) and convert each one. You can also target a specific range by adjusting the `pageNumber` or using additional load options:

<!--[CODE_SNIPPET_START]-->
```java
int pageCount = conversion.getPageCount();
for (int i = 1; i <= pageCount; i++) {
    imgOptions.setPageNumber(i);
    String outputPath = "output_images/sheet_" + i + ".png";
    conversion.convert(outputPath, imgOptions);
}
```
<!--[CODE_SNIPPET_END]-->

### Verify Output and Handle Exceptions

Wrap the conversion logic in a try‑catch block and ensure the output directory exists before starting:

<!--[CODE_SNIPPET_START]-->
```java
try {
    Files.createDirectories(Paths.get("output_images"));
    // conversion code here
    System.out.println("Excel to image conversion completed successfully.");
} catch (Exception ex) {
    System.err.println("Conversion failed: " + ex.getMessage());
    ex.printStackTrace();
}
```
<!--[CODE_SNIPPET_END]-->

The steps above demonstrate how to **convert Excel to image** using the Conholdate.Total SDK while giving you flexibility to handle charts, ranges, and full worksheets.

## Complete Code Example: Convert Excel to Image with Full Sheet Support

The following code shows the complete, ready‑to‑run implementation described in the steps above.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import java.io.FileInputStream;
import java.nio.file.Files;
import java.nio.file.Paths;

import com.groupdocs.conversion.Conversion;
import com.groupdocs.conversion.options.load.ExcelLoadOptions;
import com.groupdocs.conversion.options.convert.ImageConvertOptions;
import com.groupdocs.conversion.options.convert.ImageConvertOptions.ImageFormat;

public class ExcelToImageConverter {
    public static void main(String[] args) {
        String inputFile = "input.xlsx";
        String outputFolder = "output_images";

        try {
            // Create output directory if it does not exist
            Files.createDirectories(Paths.get(outputFolder));

            // Load options: include charts and formulas during conversion
            ExcelLoadOptions loadOptions = new ExcelLoadOptions();
            loadOptions.setLoadCharts(true);
            loadOptions.setLoadFormulas(true);

            // Initialize conversion with the Excel file and load options
            try (Conversion conversion = new Conversion(new FileInputStream(inputFile), loadOptions)) {

                // Determine how many pages (sheets) the workbook has
                int pageCount = conversion.getPageCount();

                // Configure image output options
                ImageConvertOptions imgOptions = new ImageConvertOptions();
                imgOptions.setFormat(ImageFormat.PNG);   // Output format
                imgOptions.setQuality(90);               // Quality (relevant for JPEG)
                imgOptions.setWidth(1200);               // Desired width, height will keep aspect ratio
                imgOptions.setHeight(0);                 // 0 means preserve original aspect ratio

                // Convert each sheet to a separate image file
                for (int i = 1; i <= pageCount; i++) {
                    imgOptions.setPageNumber(i);
                    String outputPath = outputFolder + "/sheet_" + i + ".png";
                    conversion.convert(outputPath, imgOptions);
                }
            }

            System.out.println("Excel to image conversion completed successfully.");
        } catch (Exception ex) {
            System.err.println("Conversion failed: " + ex.getMessage());
            ex.printStackTrace();
        }
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.xlsx`, `output_images`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Conclusion

Converting Excel to image in Java becomes straightforward when you leverage [Conholdate.Total for Java](https://products.conholdate.com/total/java/). The SDK handles chart rendering, formula evaluation, and high‑quality PNG output with minimal code. By following the step‑by‑step guide you can integrate this capability into reporting tools, email generators, or any application that needs visual spreadsheet representations. Remember that production deployments require a commercial license; you can explore pricing options on the [Conholdate.Total pricing](https://purchase.conholdate.com/pricing/total/family/) page and obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) while evaluating.

## FAQs

- **How can I convert Excel to image in Java?**  
  Use the `Conversion` class from [Conholdate.Total for Java](https://products.conholdate.com/total/java/), configure `ExcelLoadOptions` and `ImageConvertOptions`, then call `convert` for each worksheet.

- **Can I convert an Excel chart to an image?**  
  Yes. Enable chart loading with `loadOptions.setLoadCharts(true)` and specify the chart's page number when setting `imgOptions.setPageNumber`.

- **Is it possible to convert only a specific range of cells?**  
  You can define a range in the load options or select the appropriate page number that corresponds to the desired range before conversion.

- **What licensing is required for production use?**  
  A commercial license is required. Review the costs on the [Conholdate.Total pricing](https://purchase.conholdate.com/pricing/total/family/) page and obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/).

## Read More
- [Convert Word to Image in Java](https://blog.conholdate.com/total/convert-word-to-image-in-java/)
- [Convert Image to Grayscale in Java](https://blog.conholdate.com/total/convert-image-to-grayscale-in-java/)
- [Convert CDR to PNG in Java](https://blog.conholdate.com/total/convert-cdr-to-png-in-java/)