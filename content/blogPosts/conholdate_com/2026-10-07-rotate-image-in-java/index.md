---
title: "Rotate Image in Java"
seoTitle: "Rotate Image in Java"
description: "Learn how to rotate PNG and JPG images in Java with Conholdate.Total for Java. This guide walks through setup, code example, and rotation options."
date: Wed, 07 Oct 2026 17:53:30 +0000
lastmod: Wed, 07 Oct 2026 17:53:30 +0000
draft: false
url: /total/rotate-image-in-java/
author: "Farhan Raza"
summary: "Rotate PNG and JPG images in Java with Conholdate.Total for Java. This guide explains environment setup, Maven dependency, a step-by-step code example, rotation options such as angle and background color, and how to preserve metadata for quality output."
tags: ['java image processing', 'image rotation', 'image format handling']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/rotate-image-in-java.jpg
   alt: "Rotate Image in Java"
   caption: "Rotate Image in Java"
steps:
  - "Step 1: Add Conholdate Maven repository and dependency."
  - "Step 2: Prepare input PNG or JPG file."
  - "Step 3: Write Java code to configure rotation."
  - "Step 4: Execute the program and verify output."
  - "Step 5: Adjust rotation options as needed."
faqs:
  - q: "How do I rotate an image file in Java using Conholdate.Total?"
    a: "Use the ImageConvertOptions class to set the rotation angle and then call the convert method of [Conholdate.Total for Java](https://products.conholdate.com/total/java/)."
  - q: "Can I rotate both PNG and JPG images with the same code?"
    a: "Yes, the SDK automatically detects the source format. Just provide the appropriate file extension in the input path."
  - q: "What options are available to customize the rotation process?"
    a: "You can set the angle, background color, output quality, and preserve metadata. See the API reference for [ImageConvertOptions](https://reference.conholdate.com/java/com/groupdocs/conversion/options/convert/ImageConvertOptions.html)."
  - q: "Do I need a license to use this feature in production?"
    a: "A valid license is required for production use. You can obtain a temporary license at https://purchase.conholdate.com/temporary-license/ or view pricing at https://purchase.conholdate.com/pricing/total/family/."
---

Rotating images programmatically is a frequent need when building preview generators, photo editors, or document workflows. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a robust SDK that makes image manipulation straightforward in Java applications. In this guide you will learn how to rotate [PNG](https://docs.fileformat.com/image/png/) and [JPG](https://docs.fileformat.com/image/jpg/) files, configure rotation parameters, and preserve metadata while keeping image quality high.

## Environment Preparation - Prerequisites and Setup

Before you start, make sure you have the following:

- Java 17 or newer installed.
- An IDE such as IntelliJ IDEA or Eclipse.
- Maven for dependency management.

Add the Conholdate Maven repository and the SDK dependency to your `pom.xml`:

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

Download the latest SDK binaries from the official download page: [Conholdate.Total for Java Download](https://releases.conholdate.com/total/java/). Once the dependencies are resolved, you are ready to write code that rotates images.

## Rotate Image in Java: Step-by-Step Walkthrough

### Step 1: Load Source and Destination Paths
Define the input and output file locations. The SDK works with both PNG and JPG formats.

```java
String inputPath = "input.jpg";
String outputPath = "output_rotated.jpg";
```

### Step 2: Initialise Conversion Handler and Options
Create the core objects that drive the conversion process.

```java
ConversionHandler handler = new ConversionHandler();
ImageConvertOptions options = new ImageConvertOptions();
```

### Step 3: Set Rotation Angle and Background Color
Specify how many degrees to rotate the image and the fill colour for empty corners.

```java
options.setRotateAngle(90);               // Rotate 90 degrees clockwise
options.setBackgroundColor(Color.WHITE);  // Fill empty space with white
```

### Step 4: Configure Additional Parameters
Preserve original metadata and define [JPEG](https://docs.fileformat.com/image/jpeg/) quality when the output is JPG.

```java
options.setPreserveMetadata(true);
options.setQuality(90); // JPEG quality (0‑100)
```

### Step 5: Execute the Rotation
Call the `convert` method to apply the rotation and write the result.

```java
handler.convert(inputPath, outputPath, options);
System.out.println("Image rotated successfully: " + outputPath);
```

For more details on the `ConversionHandler` class, refer to the [official API reference](https://reference.conholdate.com/java/com/groupdocs/conversion/ConversionHandler.html).

## Complete Code Example: Rotate Image in Java Using Conholdate.Total

The following example demonstrates the full workflow for rotating an image file.

This example demonstrates how to rotate a JPG image by 90 degrees and save the result.

```java
import com.groupdocs.conversion.ConversionHandler;
import com.groupdocs.conversion.options.convert.ImageConvertOptions;
import java.awt.Color;

public class RotateImageExample {
    public static void main(String[] args) {
        String inputPath = "input.jpg";
        String outputPath = "output_rotated.jpg";

        try (ConversionHandler handler = new ConversionHandler()) {
            ImageConvertOptions options = new ImageConvertOptions();
            // Rotation angle in degrees (positive = clockwise)
            options.setRotateAngle(90);
            // Background color for empty areas after rotation
            options.setBackgroundColor(Color.WHITE);
            // Preserve original metadata (EXIF, DPI, etc.)
            options.setPreserveMetadata(true);
            // Optional: for large images you can limit memory usage
            options.setQuality(90); // JPEG quality (0-100)

            handler.convert(inputPath, outputPath, options);
            System.out.println("Image rotated successfully: " + outputPath);
        } catch (Exception e) {
            System.err.println("Error during image rotation:");
            e.printStackTrace();
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Rotation Parameters: Options and Settings

The SDK offers several options to fine‑tune the rotation process.

- **Rotate Angle** - Determines how many degrees the image is turned. Positive values rotate clockwise.  
  ```java
  options.setRotateAngle(90);
  ```

- **Background Color** - Sets the fill colour for the empty corners that appear after rotation. Use any `java.awt.Color` value.

- **Preserve Metadata** - When enabled, [EXIF](https://docs.fileformat.com/image/exif/) data, DPI, and other metadata are kept in the output file. See the [ImageConvertOptions API](https://reference.conholdate.com/java/com/groupdocs/conversion/options/convert/ImageConvertOptions.html) for more details.

- **Quality** - Controls JPEG compression quality (0‑100). Higher values retain more detail but increase file size.

Adjust these settings to match the requirements of your application, whether you need lossless PNG output or high‑quality JPG results.

## Conclusion

Rotating images in Java is simple when you use [Conholdate.Total for Java](https://products.conholdate.com/total/java/). This guide walked you through the required setup, a detailed step‑by‑step implementation, and the key configuration options that let you control angle, background, metadata preservation, and output quality. Remember to acquire a proper license for production deployments; you can explore pricing options at https://purchase.conholdate.com/pricing/total/family/ or obtain a temporary license for testing at https://purchase.conholdate.com/temporary-license/. With the SDK integrated, you can add reliable image rotation to any Java‑based workflow.

## FAQs

- **How do I rotate an image file in Java using Conholdate.Total?**  
  Use the `ImageConvertOptions` class to set the desired rotation angle and then call `handler.convert(inputPath, outputPath, options)` as shown in the examples above.

- **Can I rotate both PNG and JPG images with the same code?**  
  Yes, the SDK automatically detects the source format. Provide the correct file extension in the input path and the same code works for both PNG and JPG.

- **What options are available to customize the rotation process?**  
  You can adjust the rotation angle, background color, output quality, and choose whether to preserve metadata. Refer to the [ImageConvertOptions API](https://reference.conholdate.com/java/com/groupdocs/conversion/options/convert/ImageConvertOptions.html) for the full list.

- **Do I need a license to use this feature in production?**  
  A valid license is required for production use. Obtain a temporary license for evaluation at https://purchase.conholdate.com/temporary-license/ or view full pricing details at https://purchase.conholdate.com/pricing/total/family/.

## Read More
- [Convert Onenote to Image in Java](https://blog.conholdate.com/total/convert-onenote-to-image-in-java/)
- [Convert Excel to Image in Java](https://blog.conholdate.com/total/convert-excel-to-image-in-java/)
- [Convert Word to Image in Java](https://blog.conholdate.com/total/convert-word-to-image-in-java/)