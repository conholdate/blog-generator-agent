---
title: "XPS to PDF Conversion in Java"
seoTitle: "XPS to PDF Conversion in Java"
description: "Learn how to convert XPS files to PDF in Java using Conholdate.Total for Java SDK. Step-by-step guide, Maven setup, code example, and performance tips."
date: Sat, 21 Nov 2026 04:39:18 +0000
lastmod: Sat, 21 Nov 2026 04:39:18 +0000
draft: false
url: /total/xps-to-pdf-conversion-in-java/
author: "Farhan Raza"
summary: "This tutorial shows Java developers how to use Conholdate.Total for Java to convert XPS documents to PDF. It covers Maven and Gradle dependency setup, a complete runnable example, key conversion options, and tips for benchmarking and optimizing performance."
tags: ['java xps pdf conversion', 'pdf conversion benchmark', 'java file conversion']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/xps-to-pdf-conversion-in-java.jpg
   alt: "XPS to PDF Conversion in Java"
   caption: "XPS to PDF Conversion in Java"
steps:
  - "Step 1: Add Conholdate.Total Maven or Gradle dependency to your project."
  - "Step 2: Write Java code that loads the XPS file with XpsLoadOptions."
  - "Step 3: Configure PdfConvertOptions for PDF/A compliance and page settings."
  - "Step 4: Execute the conversion and handle any exceptions."
  - "Step 5: Verify the generated PDF file and measure conversion time."
faqs:
  - q: "How can I perform XPS to PDF conversion in Java using Conholdate.Total?"
    a: "Use the [Conholdate.Total for Java](https://products.conholdate.com/total/java/) SDK. Load the XPS file with XpsLoadOptions, set PdfConvertOptions, and call Converter.convert()."
  - q: "What Maven dependency is required for XPS to PDF conversion in Java?"
    a: "Add the Conholdate Maven repository and the conholdate-total artifact as shown in the setup section. See the [official documentation](https://docs.conholdate.com/java/) for details."
  - q: "Can I run the conversion from the command line without writing Java code?"
    a: "Yes, the SDK provides a CLI tool that can be invoked with appropriate arguments to convert XPS to PDF. Refer to the CLI documentation on the product page."
  - q: "How do I benchmark XPS to PDF conversion performance in Java?"
    a: "Measure the elapsed time using java.time.Instant before and after the conversion call. The sample code prints the duration in milliseconds. For large batches, consider streaming and adjusting PdfRenderMode."
---

XPS to [PDF](https://docs.fileformat.com/pdf) conversion in Java is essential for many enterprise workflows that need reliable, print‑ready documents. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) is a powerful SDK that simplifies this task for Java developers. In this guide you will learn how to set up the library, run a complete conversion example, explore key options, and apply performance best practices.

## How to Perform XPS to PDF Conversion in Java - Step by Step
1. **Add Maven or Gradle Dependency**: Include Conholdate.Total in your build file so the SDK classes are available.  
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
   

2. **Initialize the Converter**: Load the XPS source using `XpsLoadOptions`.  
   ```java
   LoadOptions loadOptions = new XpsLoadOptions();
   try (Converter converter = new Converter("sample.xps", loadOptions)) {
       // conversion will be performed in the next step
   }
   ```
   

3. **Configure PDF Output**: Set compliance, page size, orientation, and render mode via `PdfConvertOptions`.  
   ```java
   PdfConvertOptions pdfOptions = new PdfConvertOptions();
   pdfOptions.setCompliance(PdfConvertOptions.PdfCompliance.PDF_A_1B);
   pdfOptions.setPageSize(PdfPageSize.A4);
   pdfOptions.setPageOrientation(PdfPageOrientation.PORTRAIT);
   pdfOptions.setRenderMode(PdfRenderMode.FAST);
   ```
   

4. **Execute the Conversion**: Call `converter.convert` with the output path and options.  
   ```java
   converter.convert("sample_converted.pdf", pdfOptions);
   ```
   

5. **Benchmark the Process**: Record start and end times with `Instant` to evaluate performance.  
   ```java
   Instant start = Instant.now();
   // conversion code here
   Instant end = Instant.now();
   System.out.println("Conversion completed in " + 
       Duration.between(start, end).toMillis() + " ms");
   ```
   

For more details on each class, refer to the [API reference](https://reference.conholdate.com/java/).

## XPS to PDF Sample - Complete Code Example
The following code demonstrates the core functionality of XPS to PDF conversion in Java using Conholdate.Total.

```java
import com.groupdocs.conversion.Converter;
import com.groupdocs.conversion.options.load.LoadOptions;
import com.groupdocs.conversion.options.load.XpsLoadOptions;
import com.groupdocs.conversion.options.convert.PdfConvertOptions;
import com.groupdocs.conversion.options.convert.PdfConvertOptions.PdfCompliance;
import com.groupdocs.conversion.options.PdfPageSize;
import com.groupdocs.conversion.options.PdfPageOrientation;
import com.groupdocs.conversion.options.PdfRenderMode;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.Instant;

public class XpsToPdfDemo {
    public static void main(String[] args) {
        // Input XPS file and desired PDF output
        String inputPath = "sample.xps";
        String outputPath = "sample_converted.pdf";

        // Start timing for benchmarking
        Instant start = Instant.now();

        // Load options (can be extended with password, etc.)
        LoadOptions loadOptions = new XpsLoadOptions();

        // Conversion options with PDF-specific settings
        PdfConvertOptions pdfOptions = new PdfConvertOptions();
        pdfOptions.setCompliance(PdfCompliance.PDF_A_1B);               // PDF/A-1b compliance
        pdfOptions.setPageSize(PdfPageSize.A4);                         // A4 page size
        pdfOptions.setPageOrientation(PdfPageOrientation.PORTRAIT);    // Portrait orientation
        pdfOptions.setRenderMode(PdfRenderMode.FAST);                  // Faster rendering, lower memory

        // Perform conversion inside try‑with‑resources to ensure proper cleanup
        try (Converter converter = new Converter(inputPath, loadOptions)) {
            converter.convert(outputPath, pdfOptions);
        } catch (Exception e) {
            System.err.println("XPS to PDF conversion failed: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // End timing and report duration
        Instant end = Instant.now();
        Duration elapsed = Duration.between(start, end);
        System.out.println("Conversion completed in " + elapsed.toMillis() + " ms");

        // Verify that the PDF file was created
        if (Files.exists(Paths.get(outputPath))) {
            System.out.println("PDF file successfully created at: " + outputPath);
        } else {
            System.err.println("PDF file was not created.");
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Conholdate.Total for Java - Prerequisites and Setup
To start converting XPS to PDF, you need Java 8 or higher and a valid Conholdate.Total license. Download the SDK from the [download page](https://releases.conholdate.com/total/java/). After adding the Maven dependency shown earlier, you can also use Gradle:

```gradle
repositories {
    maven {
        url "https://repository.conholdate.com/repo/"
    }
}
implementation 'com.conholdate:conholdate-total:24.9'
```

Make sure to place your license file in the application directory or set the license programmatically as described in the documentation.

## Key Features of Conholdate.Total for Java for XPS to PDF
- **PDF/A‑1b Compliance** - Guarantees long‑term archiving compatibility.  
- **Fast Rendering Mode** - Optimizes memory usage for large XPS files.  
- **Page Size and Orientation Control** - Adjust output to A4, Letter, portrait, or landscape.  
- **Extensible Load Options** - Future‑proof handling of password‑protected XPS files.  
- **Comprehensive API** - Full access to conversion settings via the Java SDK.  

For a deeper dive, see the [official documentation](https://docs.conholdate.com/java/).

## Conversion Options: Tuning PDF Output
The `PdfConvertOptions` class offers several properties you can tweak:

- **Compliance** - Choose between PDF/A‑1b, PDF/A‑2b, etc. (already set in the sample).  
- **PageSize** - Options include `A4`, `LETTER`, `LEGAL`.  
- **PageOrientation** - `PORTRAIT` or `LANDSCAPE`.  
- **RenderMode** - `FAST` for speed, `HIGH_QUALITY` for better visual fidelity.

You can modify any of these directly in the code snippet shown in the steps section.

## Performance Considerations for XPS to PDF Conversion
1. **Render Mode** - Using `PdfRenderMode.FAST` reduces CPU load and speeds up conversion, which is useful for batch processing.  
2. **Stream vs File** - For large documents, consider using streams instead of file paths to lower I/O overhead.  
3. **Benchmarking** - The sample measures elapsed time with `Instant`. Run the conversion multiple times and calculate average duration to get a reliable benchmark.  
4. **Thread Safety** - Create a separate `Converter` instance per thread; the SDK is not thread‑safe for shared instances.

Applying these tips helps you achieve consistent conversion times, especially when integrating the SDK into a servlet or a Spring Boot service.

## Conclusion
XPS to PDF conversion in Java becomes straightforward with [Conholdate.Total for Java](https://products.conholdate.com/total/java/). By following the steps, configuring the options, and applying performance best practices, you can generate PDF/A‑1b compliant documents efficiently. Remember to obtain a proper license for production use; you can explore pricing details on the [pricing page](https://purchase.conholdate.com/pricing/total/family/) or request a [temporary license](https://purchase.conholdate.com/temporary-license/) to evaluate the SDK.

## Common Questions
**How do I perform XPS to PDF conversion in Java using Conholdate.Total?**  
Use the `Converter` class with `XpsLoadOptions` and `PdfConvertOptions`. The sample code in this article shows the exact sequence of calls.

**What Maven dependency is required for XPS to PDF conversion in Java?**  
Add the Conholdate Maven repository and the `conholdate-total` artifact as demonstrated in the setup section. The same coordinates work for Gradle.

**Can I run the conversion from the command line without writing Java code?**  
Yes, the SDK provides a CLI tool that accepts input and output file paths along with option flags. Refer to the CLI documentation on the product page.

**How can I benchmark XPS to PDF conversion performance in Java?**  
Wrap the conversion call with `Instant.now()` before and after execution, then calculate the duration. For more accurate results, run the conversion multiple times and average the timings.

## Related Articles
- [STL to PDF Conversion in Java](https://blog.conholdate.com/total/stl-to-pdf-conversion-in-java/)
- [MPP to PDF Conversion in Java](https://blog.conholdate.com/total/mpp-to-pdf-conversion-in-java/)
- [XPS to DOCX Conversion in Java](https://blog.conholdate.com/total/xps-to-docx-conversion-in-java/)