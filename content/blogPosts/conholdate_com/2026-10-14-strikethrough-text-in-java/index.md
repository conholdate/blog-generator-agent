---
title: "Strikethrough Text in Java"
seoTitle: "Strikethrough Text in Java"
description: "Add strikethrough text in Java with Conholdate.Total for Java. Follow this concise tutorial for setup, code sample, performance tips, and best practices."
date: Wed, 14 Oct 2026 16:41:08 +0000
lastmod: Wed, 14 Oct 2026 16:41:08 +0000
draft: false
url: /total/strikethrough-text-in-java/
author: "Farhan Raza"
summary: "This guide shows Java developers how to apply strikethrough text in Java using Conholdate.Total for Java. Install the SDK, create a document, style text with strikethrough, and save as DOCX while learning performance tips, configuration options, and advice."
tags: ['java text styling', 'strikethrough formatting', 'document formatting java']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/strikethrough-text-in-java.jpg
   alt: "Strikethrough Text in Java"
   caption: "Strikethrough Text in Java"
steps:
  - "Step 1: Install Conholdate.Total for Java SDK"
  - "Step 2: Create a new Document object"
  - "Step 3: Add a paragraph and append text"
  - "Step 4: Apply strikethrough styling to the text"
  - "Step 5: Save the document as DOCX"
faqs:
  - q: "How do I apply strikethrough text in Java using Conholdate.Total for Java?"
    a: "Use the Font.setStrikeThrough(true) method on a Run object after appending the desired text. The full example in this article demonstrates the exact steps."
  - q: "Can I use strikethrough formatting with other file formats like PDF?"
    a: "Yes, the SDK supports multiple output formats. After applying the style, save the document as PDF or DOCX using the appropriate save method."
  - q: "What are the best practices for strikethrough text in Java?"
    a: "Reuse a single Document instance for multiple operations, apply styles once per Run, and dispose of resources promptly. Review the official documentation for performance tips."
  - q: "Is there an open source alternative for strikethrough text in Java?"
    a: "While open source libraries exist, Conholdate.Total for Java offers comprehensive support, licensing options, and dedicated assistance. Check the pricing page for details."
---

Adding visual cues like crossed‑out words can improve document readability, especially when indicating revisions or deprecated content. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a robust SDK that simplifies text styling within Word documents. In this guide you will learn how to apply strikethrough text in Java, from setting up the library to fine‑tuning performance and handling common pitfalls.

## Apply Strikethrough Text in Java in 5 Steps

The following steps demonstrate how to add strikethrough text in Java using Conholdate.Total for Java.

### Understanding the Document Model

Conholdate.Total models a Word file as a hierarchy of **Document → Section → Paragraph → Run** objects. Each *Run* represents a contiguous run of characters that share the same formatting. By manipulating the `Font` of a `Run`, you can control bold, italic, color, size, and the strike‑through flag.

### Step 1: Create a New Document Instance

This initializes the document object that will hold all content.  
```java
Document document = new Document();
```

### Step 2: Access the First Section

Every Word document starts with a default section where you can add paragraphs.  
```java
Section section = document.getFirstSection();
```

### Step 3: Add a Paragraph to the Section

Paragraphs are containers for runs of text.  
```java
Paragraph paragraph = section.addParagraph();
```

### Step 4: Append Text and Apply Strikethrough

The `Run` object holds the text; its `Font` can be styled with `setStrikeThrough(true)`.  
```java
Run run = paragraph.appendText("This text is displayed with a strikethrough effect.");
run.getFont().setStrikeThrough(true);
```

### Step 5: Save and Clean Up

Persist the document as [DOCX](https://docs.fileformat.com/word-processing/docx/) and release resources.  
```java
document.save("output.docx");
document.dispose();
```

### Performance Tip: Reuse Document Objects

If you need to generate many documents in a loop, create a single `Document` instance and clone sections or paragraphs instead of constructing a new object each time. This reduces native memory allocations and improves overall throughput.

For detailed class information, refer to the [API Reference](https://reference.conholdate.com/java/).

## Full Working Example for Adding Strikethrough Formatting

The following code shows a complete implementation of strikethrough text in Java with Conholdate.Total for Java.

```java
import com.groupdocs.wordprocessing.Document;
import com.groupdocs.wordprocessing.Section;
import com.groupdocs.wordprocessing.Paragraph;
import com.groupdocs.wordprocessing.text.Run;
import com.groupdocs.wordprocessing.font.Font;

public class StrikethroughExample {
    public static void main(String[] args) {
        Document document = null;
        try {
            // Create a new empty document
            document = new Document();

            // Access the first (and only) section
            Section section = document.getFirstSection();

            // Add a new paragraph to the section
            Paragraph paragraph = section.addParagraph();

            // Append text that will be formatted with strikethrough
            Run run = paragraph.appendText("This text is displayed with a strikethrough effect.");

            // Apply strikethrough styling
            Font font = run.getFont();
            font.setStrikeThrough(true);

            // Save the document to a DOCX file
            document.save("output.docx");
        } finally {
            // Ensure resources are released
            if (document != null) {
                document.dispose();
            }
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Installing and Configuring Conholdate.Total for Java

Add the Conholdate Maven repository to your `pom.xml` and include the SDK dependency. The download package is also available directly from the official site.

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

You can download the latest JAR files from the [download page](https://releases.conholdate.com/total/java/). The SDK requires Java 8 or higher. After adding the dependency, refresh your Maven project so the classes become available on the classpath.

## Configuring Strikethrough Styling Options

In this section we explore how to apply strikethrough text in Java with additional styling options. The SDK offers a **Java Library for Strikethrough Formatting** that lets you control several text attributes. The primary option for a strike‑through effect is `setStrikeThrough(true)` on the `Font` object, as shown in the step‑by‑step guide.

### Advanced Font Customization

Beyond the strike‑through flag, you can adjust:

- **Font size** - keep visual hierarchy consistent across headings and body text.  
- **Font color** - a different color can highlight the struck‑through portion while preserving readability.  
- **Bold/Italic** - combine with other styles for richer formatting, useful in revision tracking scenarios.

All these properties are available on the same `Font` instance, so you only need a single call chain.

### Combining Multiple Text Decorations

Conholdate.Total allows you to layer decorations such as underline, double‑underline, and strike‑through simultaneously. This is especially handy when generating legal documents where deleted clauses must remain visible. Simply set the corresponding flags on the `Font` object:

```java
font.setStrikeThrough(true);
font.setUnderline(true);
```

For a full list of properties, see the [official documentation](https://docs.conholdate.com/java/).

## Conclusion

Applying strikethrough text in Java becomes straightforward with Conholdate.Total for Java. The SDK's fluent API lets you create documents, style runs, and export to DOCX with minimal code, while offering performance‑focused best practices such as reusing document objects and disposing of resources promptly. For production use, acquire a proper license; you can explore the flexible pricing options on the [pricing page](https://purchase.conholdate.com/pricing/total/family/) or obtain a temporary license for evaluation from the [temporary license page](https://purchase.conholdate.com/temporary-license/). Incorporating strikethrough formatting improves the clarity of revision histories and highlights deprecated content, making your generated documents more professional and easier to audit.

## Common Questions

**How do I apply strikethrough text in Java using Conholdate.Total for Java?**  
Use the `Font.setStrikeThrough(true)` method on a `Run` after appending the desired text. The full example in this article demonstrates the exact steps, and the same approach works for DOCX, [PDF](https://docs.fileformat.com/pdf), and other supported formats.

**Are there open source alternatives for strikethrough text in Java?**  
Open source libraries exist, but they often lack the comprehensive document handling, OpenXML Text Styling support, and dedicated support that Conholdate.Total for Java provides. When you need reliable Word Document Formatting across many file types, the commercial SDK is usually the safer choice.

**What are the best practices for strikethrough text in Java?**  
Follow these recommendations:  
1. Reuse a single `Document` instance when processing multiple paragraphs to reduce memory churn.  
2. Apply the strike‑through flag once per `Run` and avoid resetting it repeatedly.  
3. Dispose of the `Document` object as soon as you finish to free native resources.  
4. Combine strike‑through with other decorations only when necessary to keep the output clean.  
Consult the [official documentation](https://docs.conholdate.com/java/) for additional performance recommendations.

**Can I combine strikethrough with other text styles?**  
Yes, the `Font` class lets you set bold, italic, color, size, underline, and strike‑through together. This flexibility enables you to create rich Rich Text Format ([RTF](https://docs.fileformat.com/word-processing/rtf/)) or DOCX content that meets complex styling requirements.

## Read More
- [Rotate Image in Java](https://blog.conholdate.com/total/rotate-image-in-java/)
- [Add Text to PDF in Java](https://blog.conholdate.com/total/add-text-to-pdf-in-java/)
- [Convert PDF to PNG in Java](https://blog.conholdate.com/total/convert-pdf-to-png-in-java/)