---
title: "Excel to JSON Conversion in Java"
seoTitle: "Excel to JSON Conversion in Java"
description: "Learn how to perform excel to JSON conversion in Java using Conholdate.Total for Java SDK. Follow step-by-step setup, code walkthrough, and configuration tips."
date: Tue, 15 Sep 2026 20:32:21 +0000
lastmod: Tue, 15 Sep 2026 20:32:21 +0000
draft: false
url: /total/excel-to-json-conversion-in-java/
author: "Farhan Raza"
summary: "This guide shows Java developers how to convert Excel spreadsheets to JSON using Conholdate.Total for Java SDK. It covers prerequisites, Maven installation, step-by-step implementation, a full code example, and conversion options like date and number formatting."
tags: ['excel to json', 'java data processing', 'json export']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/excel-to-json-conversion-in-java.jpg
   alt: "Excel to JSON Conversion in Java"
   caption: "Excel to JSON Conversion in Java"
steps:
  - "Step 1: Add Conholdate.Total Maven dependency"
  - "Step 2: Prepare Excel input file"
  - "Step 3: Configure JsonConvertOptions"
  - "Step 4: Run the conversion code"
  - "Step 5: Verify generated JSON output"
faqs:
  - q: "How do I perform excel to JSON conversion in Java with Conholdate.Total?"
    a: "Use the Conholdate.Total for Java SDK. The library provides a simple API to load an XLSX file, configure JsonConvertOptions, and call the convert method. See the [official documentation](https://docs.conholdate.com/java/) for detailed usage."
  - q: "Can I customize date and number formats during excel to JSON conversion in Java?"
    a: "Yes. JsonConvertOptions lets you set custom date and number patterns via setCustomDateFormat and setCustomNumberFormat. Refer to the [API reference](https://reference.conholdate.com/java/) for the full list of options."
  - q: "What licensing options are available for Conholdate.Total for Java?"
    a: "You can obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or view pricing details on the [pricing page](https://purchase.conholdate.com/pricing/total/family/)."
  - q: "Is batch processing supported for large Excel files?"
    a: "The SDK includes a rowsPerBatch setting that allows you to process large worksheets in chunks, enabling efficient batch conversion."
---

Converting Excel spreadsheets to [JSON](https://docs.fileformat.com/web/json/) is a frequent requirement when building data‑exchange pipelines or feeding APIs. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) is a powerful SDK that simplifies this task for Java developers. In this guide you will learn how to set up the library, walk through a complete implementation, and fine‑tune the conversion options to match your project's needs.

## Prerequisites and Setup for Conholdate.Total for Java

Before you start, make sure you have:

- Java 17 or newer installed.
- Maven 3.6+ for dependency management.
- An Excel file (`.xlsx`) you want to convert.

Add the Conholdate.Total Maven repository and dependency to your `pom.xml`:

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

You can also download the latest JARs directly from the [download page](https://releases.conholdate.com/total/java/). With the SDK in place, you are ready to start the excel to JSON conversion in Java.

## Excel to JSON Conversion in Java: Step-by-Step Walkthrough

### Step 1: Load the Source Excel Document

First, specify the path to the source [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/) file and create a `Conversion` instance. The `try‑with‑resources` block ensures the conversion object is disposed properly.

```java
String inputFile = "sample.xlsx";
try (Conversion conversion = new Conversion(inputFile)) {
    // conversion object ready
}
```

### Step 2: Configure JSON Conversion Options

Create a `JsonConvertOptions` object and adjust settings such as pretty‑print, header inclusion, custom date and number formats, and batch size. These options control how the excel to JSON conversion in Java shapes the final output.

```java
JsonConvertOptions jsonOptions = new JsonConvertOptions();
jsonOptions.setPrettyPrint(true);
jsonOptions.setIncludeHeaders(true);
jsonOptions.setDateFormat(JsonConvertOptions.DateFormat.CUSTOM);
jsonOptions.setCustomDateFormat("yyyy-MM-dd");
jsonOptions.setNumberFormat(JsonConvertOptions.NumberFormat.CUSTOM);
jsonOptions.setCustomNumberFormat("#.##");
jsonOptions.setRowsPerBatch(5000);
```

### Step 3: Execute the Conversion

Provide the target JSON file name and invoke the `convert` method. The SDK handles the transformation internally.

```java
String outputFile = "sample.json";
conversion.convert(outputFile, jsonOptions);
```

### Step 4: Handle the Result and Cleanup

After conversion, output a confirmation message. Any exceptions are caught and printed to the console.

```java
System.out.println("Conversion completed successfully. JSON saved to: " + outputFile);
} catch (Exception e) {
    System.err.println("Error during Excel to JSON conversion:");
    e.printStackTrace();
}
```

With these steps, the excel to JSON conversion in Java is complete, and you can integrate the generated JSON into your API or data‑processing workflow.

## Full Implementation: Java Excel to JSON Conversion

The following example demonstrates how to perform excel to JSON conversion in Java using Conholdate.Total for Java.

```java
import com.groupdocs.conversion.Conversion;
import com.groupdocs.conversion.options.convert.JsonConvertOptions;
import com.groupdocs.conversion.options.convert.JsonConvertOptions.DateFormat;
import com.groupdocs.conversion.options.convert.JsonConvertOptions.NumberFormat;

public class ExcelToJsonDemo {
    public static void main(String[] args) {
        // Input Excel file (generic path)
        String inputFile = "sample.xlsx";
        // Desired JSON output file
        String outputFile = "sample.json";

        // Perform conversion inside try‑with‑resources to ensure proper cleanup
        try (Conversion conversion = new Conversion(inputFile)) {

            // Configure JSON conversion options
            JsonConvertOptions jsonOptions = new JsonConvertOptions();

            // Pretty‑print the JSON for readability
            jsonOptions.setPrettyPrint(true);

            // Include column headers as JSON property names
            jsonOptions.setIncludeHeaders(true);

            // Define how dates and numbers should be formatted in the JSON output
            jsonOptions.setDateFormat(DateFormat.CUSTOM);
            jsonOptions.setCustomDateFormat("yyyy-MM-dd");
            jsonOptions.setNumberFormat(NumberFormat.CUSTOM);
            jsonOptions.setCustomNumberFormat("#.##");

            // Optional performance tweak: limit rows processed per batch (useful for very large sheets)
            jsonOptions.setRowsPerBatch(5000);

            // Execute the conversion
            conversion.convert(outputFile, jsonOptions);

            System.out.println("Conversion completed successfully. JSON saved to: " + outputFile);
        } catch (Exception e) {
            // Basic error handling – in production code you might want more sophisticated logging
            System.err.println("Error during Excel to JSON conversion:");
            e.printStackTrace();
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Conversion Options and Settings

The SDK offers several options to tailor the JSON output:

- **Pretty Print** - Improves readability by adding indentation.  
  ```java
  jsonOptions.setPrettyPrint(true);
  ```
- **Include Headers** - Uses the first row of the worksheet as property names.  
  `setIncludeHeaders(true)` (see the [API reference](https://reference.conholdate.com/java/)).
- **Custom Date Format** - Define a date pattern, e.g., `"yyyy-MM-dd"`.  
  `setCustomDateFormat("yyyy-MM-dd")`.
- **Custom Number Format** - Control numeric precision, e.g., `"#.##"`.  
  `setCustomNumberFormat("#.##")`.

Adjusting these settings lets you align the generated JSON with the expectations of downstream services or databases.

## Conclusion

You now have a working excel to JSON conversion in Java implementation powered by [Conholdate.Total for Java](https://products.conholdate.com/total/java/). The SDK handles the heavy lifting, while the configurable options give you control over formatting and performance. Remember to obtain a proper license for production use; you can request a [temporary license page](https://purchase.conholdate.com/temporary-license/) to evaluate the library or review the full [pricing page](https://purchase.conholdate.com/pricing/total/family/) for commercial terms. Happy coding!

## FAQs

- **How do I perform excel to JSON conversion in Java with Conholdate.Total?**  
  Use the `Conversion` class together with `JsonConvertOptions` as shown in the code example. The SDK abstracts file handling and provides a single `convert` call.

- **Can I customize date and number formats during excel to JSON conversion in Java?**  
  Yes. The `setCustomDateFormat` and `setCustomNumberFormat` methods let you define patterns that match your target system's expectations.

- **What licensing options are available for Conholdate.Total for Java?**  
  You can obtain a temporary evaluation license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or purchase a full license via the [pricing page](https://purchase.conholdate.com/pricing/total/family/).

- **Is batch processing supported for large Excel files?**  
  The `setRowsPerBatch` option allows you to process worksheets in chunks, which is ideal for batch conversion scenarios.

## Read More
- [Insert Watermark in Excel using Java](https://blog.conholdate.com/total/insert-watermark-in-excel-using-java/)
- [Convert Excel to Image in Java](https://blog.conholdate.com/total/convert-excel-to-image-in-java/)
- [Convert JSON to XML in C#](https://blog.conholdate.com/total/convert-json-to-xml-in-csharp/)