---
title: "Convert TIFF to JPG in Java"
seoTitle: "Convert TIFF to JPG in Java"
description: "Discover how to convert TIFF to JPG in Java with Conholdate.Total for Java. This step‑by‑step guide covers code, high‑resolution settings, and best practices."
date: Wed, 21 Oct 2026 19:48:01 +0000
lastmod: Wed, 21 Oct 2026 19:48:01 +0000
draft: false
url: /total/convert-tiff-to-jpg-in-java/
author: "Farhan Raza"
summary: "This tutorial shows Java developers how to convert TIFF to JPG in Java using Conholdate.Total for Java. Follow the step‑by‑step implementation, learn to handle multi‑page TIFFs, configure high‑resolution output, and integrate the conversion utility into your applications."
tags: ['java image conversion', 'tiff to jpg', 'high resolution output']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/convert-tiff-to-jpg-in-java.jpg
   alt: "Convert TIFF to JPG in Java"
   caption: "Convert TIFF to JPG in Java"
steps:
  - "Add Maven dependency for Conholdate.Total"
  - "Initialize the ConversionHandler"
  - "Load the TIFF file and retrieve page count"
  - "Configure JPG conversion options (quality, resolution, page number)"
  - "Execute conversion loop and validate output"
faqs:
  - q: "Can I convert a multi‑page TIFF to separate JPG files in Java?"
    a: "Yes. Using [Conholdate.Total for Java](https://products.conholdate.com/total/java/) you can iterate over each page of a TIFF and produce an individual JPG. The SDK exposes the page count via the file‑info API, allowing you to set the page number in the conversion options."
  - q: "What is the best way to achieve high‑resolution TIFF to JPG conversion in Java?"
    a: "Set the resolution property on the JpgConvertOptions object. A value of 300 DPI is commonly used for print‑quality output. This approach is part of the [TIFF to JPG conversion utility in Java](https://products.conholdate.com/total/java/) and works for any image size."
  - q: "Is there a batch TIFF to JPG conversion utility in Java?"
    a: "The same SDK can be used in a loop to process a folder of TIFF files, effectively creating a batch conversion tool. Combine the code sample with standard Java file‑system APIs to automate the workflow."
  - q: "Where can I find licensing information for Conholdate.Total for Java?"
    a: "Licensing details are available on the [pricing page](https://purchase.conholdate.com/pricing/total/family/) and you can obtain a temporary license for testing from the [temporary license page](https://purchase.conholdate.com/temporary-license/)."
---

Converting [TIFF](https://docs.fileformat.com/image/tiff/) to [JPG](https://docs.fileformat.com/image/jpg/) in Java is a frequent requirement when developers need to display high‑resolution images on the web or embed them in reports. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a powerful SDK that simplifies this task with just a few lines of code. In this guide you will see a complete, ready‑to‑run example, learn how to handle multi‑page TIFF files, and discover options for controlling quality and resolution. By the end you'll be able to integrate TIFF to JPG conversion into any Java application with confidence.

## The Convert TIFF to JPG in Java Requirements

Java applications that process scanned documents, medical images, or satellite photography often receive input as multi‑page TIFF files. The conversion must preserve detail, support high‑resolution output, and generate a separate JPG for each page to simplify downstream processing. Manual conversion tools cannot be scripted and do not scale, making an automated library essential for batch or real‑time scenarios.

## How Conholdate.Total for Java Fits Convert TIFF to JPG in Java

Conholdate.Total for Java offers a dedicated conversion engine that understands the TIFF format, including multi‑page images, and can produce high‑quality JPG output. The SDK lets you set output quality, DPI resolution, and page selection, which addresses the need for precise control over image fidelity. Documentation and API references are available to guide you through each feature: see the [official documentation](https://docs.conholdate.com/java/) and the [API reference](https://reference.conholdate.com/java/). With a simple Maven dependency, the library integrates seamlessly into any Java project.

## Implementing TIFF to JPG Conversion in Java

The following steps walk you through setting up the project, initializing the SDK, and performing the conversion.

### Add Maven Dependency for Conholdate.Total

Include the Conholdate Maven repository and the SDK dependency in your `pom.xml`. This ensures the library is available at compile time.

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

You can download the latest release from the [download page](https://releases.conholdate.com/total/java/).

### Initialise the ConversionHandler

Create an instance of `ConversionHandler`. The SDK assumes a valid license is set elsewhere in your application.

```java
ConversionHandler conversionHandler = new ConversionHandler();
```

Refer to the [ConversionHandler class](https://reference.conholdate.com/java/com/conholdate/ConversionHandler.html) for additional initialization options.

### Load the TIFF File and Retrieve Page Count

Use `LoadOptions` and `getFileInfo` to obtain information about the source TIFF, including the number of pages.

```java
LoadOptions loadOptions = new LoadOptions();
FileInfo fileInfo = conversionHandler.getFileInfo("sample.tif", loadOptions);
TiffFileInfo tiffInfo = (TiffFileInfo) fileInfo;
int pageCount = tiffInfo.getPages().size();
```

This step is essential for the **TIFF to JPG conversion utility in Java**, as it enables per‑page processing.

### Configure JPG Conversion Options

Set the desired quality, resolution, and the specific page to convert. These settings are part of the **High‑Resolution TIFF to JPG conversion in Java** workflow.

```java
JpgConvertOptions jpgOptions = new JpgConvertOptions();
jpgOptions.setQuality(90);          // 0‑100
jpgOptions.setResolution(300);      // DPI
jpgOptions.setPageNumber(i + 1);    // 1‑based page index
```

### Execute Conversion Loop and Validate Output

Iterate over each page, perform the conversion, and verify that the resulting JPG file exists.

```java
for (int i = 0; i < pageCount; i++) {
    jpgOptions.setPageNumber(i + 1);
    String outputPath = Paths.get("output", "page_" + (i + 1) + ".jpg").toString();
    conversionHandler.convert("sample.tif", loadOptions, jpgOptions, outputPath);

    File resultFile = new File(outputPath);
    if (resultFile.exists() && resultFile.length() > 0) {
        System.out.println("Successfully converted page " + (i + 1));
    } else {
        System.err.println("Conversion failed for page " + (i + 1));
    }
}
```

This demonstrates **Batch TIFF to JPG Conversion in Java** with minimal code.

## Complete Code Example: Convert TIFF to JPG with High Resolution Output

The following code shows the full implementation described above.

```java
import com.groupdocs.conversion.ConversionHandler;
import com.groupdocs.conversion.filetypes.FileInfo;
import com.groupdocs.conversion.filetypes.tiff.TiffFileInfo;
import com.groupdocs.conversion.options.load.LoadOptions;
import com.groupdocs.conversion.options.convert.JpgConvertOptions;
import java.io.File;
import java.nio.file.Paths;

public class TiffToJpgConverter {
    public static void main(String[] args) {
        // Input TIFF file (can be multi‑page)
        String inputPath = "sample.tif";

        // Directory where JPG files will be written
        String outputDir = "output";

        // Desired output quality and resolution
        int outputQuality = 90;      // 0‑100
        int outputResolution = 300; // DPI

        // Ensure the output directory exists
        File outFolder = new File(outputDir);
        if (!outFolder.exists()) {
            outFolder.mkdirs();
        }

        try {
            // Initialise the conversion handler (license is assumed to be set elsewhere)
            ConversionHandler conversionHandler = new ConversionHandler();

            // Load options – can be left empty for default behaviour
            LoadOptions loadOptions = new LoadOptions();

            // Retrieve file information to know how many pages the TIFF contains
            FileInfo fileInfo = conversionHandler.getFileInfo(inputPath, loadOptions);
            if (!(fileInfo instanceof TiffFileInfo)) {
                System.err.println("The provided file is not a TIFF image.");
                return;
            }
            TiffFileInfo tiffInfo = (TiffFileInfo) fileInfo;
            int pageCount = tiffInfo.getPages().size();

            // Convert each page of the TIFF to a separate JPG
            for (int i = 0; i < pageCount; i++) {
                JpgConvertOptions jpgOptions = new JpgConvertOptions();
                jpgOptions.setQuality(outputQuality);
                jpgOptions.setResolution(outputResolution);
                jpgOptions.setPageNumber(i + 1); // pages are 1‑based

                String outputPath = Paths.get(outputDir, "page_" + (i + 1) + ".jpg").toString();

                // Perform the conversion
                conversionHandler.convert(inputPath, loadOptions, jpgOptions, outputPath);

                // Simple validation of the result
                File resultFile = new File(outputPath);
                if (resultFile.exists() && resultFile.length() > 0) {
                    System.out.println("Successfully converted page " + (i + 1) + " to " + outputPath);
                } else {
                    System.err.println("Conversion failed for page " + (i + 1));
                }
            }
        } catch (Exception ex) {
            System.err.println("Error during TIFF to JPG conversion: " + ex.getMessage());
            ex.printStackTrace();
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Fine-Tuning High‑Resolution Output Settings

Several options let you control the quality and size of the generated JPG files.

- **Quality** - Determines [JPEG](https://docs.fileformat.com/image/jpeg/) compression level (0‑100). Higher values keep more detail.  
  ```java
  jpgOptions.setQuality(90);
  ```
- **Resolution** - Sets the DPI of the output image. A value of 300 DPI is standard for print‑ready graphics.  
  ```java
  jpgOptions.setResolution(300);
  ```
- **PageNumber** - Specifies which page of a multi‑page TIFF to convert. Changing this value inside a loop enables batch processing.  
  ```java
  jpgOptions.setPageNumber(i + 1);
  ```

You can also explore additional properties such as `setColorMode` or `setCompressionLevel` in the API reference for more advanced scenarios.

## Key Takeaways

Converting TIFF to JPG in Java becomes straightforward with [Conholdate.Total for Java](https://products.conholdate.com/total/java/). The SDK handles multi‑page TIFFs, lets you fine‑tune quality and resolution, and integrates cleanly into Maven‑based projects. Remember to obtain a proper license for production use; pricing details are on the [pricing page](https://purchase.conholdate.com/pricing/total/family/) and a temporary license is available from the [temporary license page](https://purchase.conholdate.com/temporary-license/). With the code and configuration tips provided, you can now add reliable image conversion to any Java application.

## Questions You Might Have

**How do I convert a multi‑page TIFF to separate JPG files in Java?**  
Use the `ConversionHandler` to retrieve the page count, then loop through each page while setting `JpgConvertOptions.setPageNumber`. The SDK will generate one JPG per page, as shown in the complete example.

**What performance considerations should I keep in mind for TIFF to JPG conversion in Java?**  
Processing large, high‑resolution TIFFs can consume memory. Reusing a single `ConversionHandler` instance and writing each output file immediately helps keep the memory footprint low. Adjusting the `resolution` and `quality` values can also reduce processing time.

**Is there a way to perform stream‑based TIFF to JPG conversion without intermediate files?**  
Yes. The SDK supports stream input and output via overloads of the `convert` method that accept `InputStream` and `OutputStream`. Refer to the [API reference](https://reference.conholdate.com/java/) for the exact signatures.

**Where can I find more examples and support for Conholdate.Total for Java?**  
The official [documentation](https://docs.conholdate.com/java/) contains detailed guides, and the community [forums](https://forum.conholdate.com/c/total/5) are a great place to ask questions and share solutions.

## Keep Exploring
- [Convert JPG to TIFF in Java](https://blog.conholdate.com/total/convert-jpg-to-tiff-in-java/)
- [Convert JPG to PNG in Java](https://blog.conholdate.com/total/convert-jpg-to-png-in-java/)
- [Convert Markdown to JPG in Java](https://blog.conholdate.com/total/convert-markdown-to-jpg-in-java/)