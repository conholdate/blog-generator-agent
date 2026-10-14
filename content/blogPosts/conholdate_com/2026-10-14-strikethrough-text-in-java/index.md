---
title: "Strikethrough Text in Java"
seoTitle: "Strikethrough Text in Java"
description: "Learn how to add strikethrough text in Java using Conholdate.Total for Java. This guide shows setup, a code walkthrough, key configuration and performance tips."
date: Wed, 14 Oct 2026 17:04:45 +0000
lastmod: Wed, 14 Oct 2026 17:04:45 +0000
draft: false
url: /total/strikethrough-text-in-java/
author: "Farhan Raza"
summary: "This tutorial teaches Java developers how to add strikethrough formatting to DOCX files using Conholdate.Total for Java. The guide covers Maven setup, a code sample that writes and detects strikethrough text, configuration options, performance tips, and a runnable example."
tags: ['java text styling', 'strikethrough formatting', 'document processing java']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/strikethrough-text-in-java.jpg
   alt: "Strikethrough Text in Java"
   caption: "Strikethrough Text in Java"
steps:
  - "Step 1: Add Maven dependency and import classes"
  - "Step 2: Load or create a document"
  - "Step 3: Write normal and strikethrough paragraphs"
  - "Step 4: Apply conditional strikethrough based on content"
  - "Step 5: Save the document"
faqs:
  - q: "How can I apply strikethrough text in Java using Conholdate.Total?"
    a: "Use the DocumentBuilder API to set Font.setStrikeThrough(true) before writing the text. See the full example in this guide."
  - q: "Is there a way to automatically strike through words that contain a specific keyword?"
    a: "Yes, iterate through Run objects, check the text, and set Font.setStrikeThrough(true) when the condition matches."
  - q: "What file formats support strikethrough styling with Conholdate.Total for Java?"
    a: "DOCX, DOC, RTF, and other rich‑text formats preserve strikethrough styling. Refer to the [official documentation](https://docs.conholdate.com/java/)."
  - q: "Does applying strikethrough affect performance when processing large documents?"
    a: "Impact is minimal; reuse the Document object and avoid redundant style changes. Performance tips are covered in the article."
---

Strikethrough formatting is often required to indicate deletions, revisions, or completed tasks within generated documents. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a robust SDK that lets you manipulate Word documents programmatically. In this guide you will learn how to add strikethrough text in Java, explore configuration options, see performance best practices, and run a complete example that you can adapt to your own projects.

## Before You Start: Prerequisites and Installation

To follow this tutorial you need:

- Java 17 or newer installed on your development machine.
- Maven 3.6+ for dependency management.
- An IDE such as IntelliJ IDEA or Eclipse.

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

Download the latest SDK binaries from the [download page](https://releases.conholdate.com/total/java/) if you prefer a manual setup. Once the dependency is resolved, you are ready to start coding. The next section walks through each step of adding strikethrough text in Java.

## Step-by-Step Guide to Strikethrough Text in Java

### Step 1: Load the Source Document

First, create a `Document` instance. If the input file exists the SDK loads it; otherwise a new empty document is created.

```java
String inputPath = "input.docx";
Document doc;
File inputFile = new File(inputPath);
if (inputFile.exists()) {
    doc = new Document(inputPath); // loads existing DOCX
} else {
    doc = new Document();          // creates a new blank document
    doc.removeAllChildren();       // ensure it's empty
}
```

The `Document` class is documented in the [API reference](https://reference.conholdate.com/java/).

### Step 2: Write Normal Paragraph

Use `DocumentBuilder` to add a regular paragraph. This demonstrates that normal text is unaffected by strikethrough settings.

```java
DocumentBuilder builder = new DocumentBuilder(doc);
builder.moveToDocumentEnd();
builder.writeln("This is a normal paragraph.");
```

### Step 3: Apply Strikethrough Formatting

Enable the strike‑through flag on the builder's font before writing the styled text.

```java
builder.getFont().setStrikeThrough(true);
builder.writeln("This text is rendered with strikethrough.");
builder.getFont().setStrikeThrough(false); // reset for subsequent text
```

### Step 4: Search and Apply Conditional Strikethrough

Iterate through all `Run` objects, find the word "strike", and apply the formatting programmatically.

```java
for (Paragraph para : (Iterable<Paragraph>) doc.getChildNodes(NodeType.PARAGRAPH, true)) {
    for (Run run : (Iterable<Run>) para.getChildNodes(NodeType.RUN, true)) {
        String text = run.getText();
        if (text != null && text.toLowerCase().contains("strike")) {
            run.getFont().setStrikeThrough(true);
        }
    }
}
```

### Step 5: Save the Document

Finally, write the modified document to disk in [DOCX](https://docs.fileformat.com/word-processing/docx/) format.

```java
String outputPath = "output.docx";
doc.save(outputPath, SaveFormat.DOCX);
```

With the document saved, you can open `output.docx` to verify that the strikethrough styling appears as expected.

## Full Working Example for Strikethrough Text Java Example

The following code demonstrates the complete workflow for adding strikethrough text in Java using Conholdate.Total.

```java
import com.aspose.words.*;

import java.io.File;

public class StrikethroughExample {
    public static void main(String[] args) {
        String inputPath = "input.docx";
        String outputPath = "output.docx";

        Document doc = null;
        try {
            File inputFile = new File(inputPath);
            if (inputFile.exists()) {
                doc = new Document(inputPath);
            } else {
                doc = new Document();
                doc.removeAllChildren();
            }

            DocumentBuilder builder = new DocumentBuilder(doc);
            builder.moveToDocumentEnd();

            builder.writeln("This is a normal paragraph.");

            builder.getFont().setStrikeThrough(true);
            builder.writeln("This text is rendered with strikethrough.");
            builder.getFont().setStrikeThrough(false);

            for (Paragraph para : (Iterable<Paragraph>) doc.getChildNodes(NodeType.PARAGRAPH, true)) {
                for (Run run : (Iterable<Run>) para.getChildNodes(NodeType.RUN, true)) {
                    String text = run.getText();
                    if (text != null && text.toLowerCase().contains("strike")) {
                        run.getFont().setStrikeThrough(true);
                    }
                }
            }

            doc.save(outputPath, SaveFormat.DOCX);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (doc != null) {
                doc = null;
            }
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Fine-Tuning Strikethrough Styling Options

The SDK lets you control additional font attributes such as color, size, and underline while keeping the strike‑through flag enabled. For example, you can change the color of strikethrough text:

```java
builder.getFont().setColor(java.awt.Color.RED);
builder.getFont().setStrikeThrough(true);
builder.writeln("Important deletion highlighted in red.");
```

If you need to apply the same style to many runs, consider creating a reusable `Font` instance and assigning it to each `Run` to avoid repetitive property setting.

## Performance Considerations for Strikethrough Rendering

1. **Reuse the `Document` object** - loading a document once and performing all modifications in a single session reduces I/O overhead.  
2. **Batch style changes** - apply the strike‑through flag to a `Paragraph` or `Run` collection rather than toggling it for each character.  
3. **Avoid unnecessary traversals** - the conditional loop that searches for the word "strike" should be executed only when you actually need dynamic styling.  
4. **Stream output when possible** - for large documents, use `doc.save(OutputStream, SaveFormat.DOCX)` to write directly to a stream and conserve memory.

These tips help keep memory usage low and execution time fast, especially when processing hundreds of documents in a batch job.

## Final Thoughts

Adding strikethrough text in Java is straightforward with [Conholdate.Total for Java](https://products.conholdate.com/total/java/). The SDK's fluent API lets you mix normal and styled paragraphs, apply conditional formatting, and save results in industry‑standard formats. Remember to configure your Maven dependency, reuse document objects, and apply styles efficiently to achieve optimal performance. For production deployments you will need a valid license; pricing details are available on the [pricing page](https://purchase.conholdate.com/pricing/total/family/) and a temporary license can be obtained from the [temporary license page](https://purchase.conholdate.com/temporary-license/). Happy coding!

## Questions You Might Have

- **How do I apply strikethrough text in Java without manually setting the flag for each run?**  
  Use `DocumentBuilder.getFont().setStrikeThrough(true)` before writing the paragraph. The flag stays active until you reset it, allowing you to write multiple lines with the same style.

- **Can I automatically strike through every occurrence of a keyword?**  
  Yes. Iterate through each `Run` as shown in the walkthrough, check `run.getText()` for the keyword, and call `run.getFont().setStrikeThrough(true)` when a match is found.

- **Which document formats preserve strikethrough when saved?**  
  DOCX, [DOC](https://docs.fileformat.com/word-processing/doc/), [RTF](https://docs.fileformat.com/word-processing/rtf/), and other rich‑text formats retain the strike‑through attribute. Refer to the [official documentation](https://docs.conholdate.com/java/) for a full list of supported formats.

- **Will applying many strikethrough styles slow down processing of large files?**  
  The impact is minimal if you follow the performance tips: reuse the `Document` instance, batch style changes, and avoid redundant traversals. This keeps memory usage low and speeds up processing.

## Related Articles
- [Rotate Image in Java](https://blog.conholdate.com/total/rotate-image-in-java/)
- [Add Text to PDF in Java](https://blog.conholdate.com/total/add-text-to-pdf-in-java/)
- [Convert PDF to PNG in Java](https://blog.conholdate.com/total/convert-pdf-to-png-in-java/)