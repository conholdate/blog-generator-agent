---
title: "Add Text to PDF in Java"
seoTitle: "Add Text to PDF in Java"
description: "Learn how to add text to PDF in Java using Conholdate.Total for Java. This step-by-step guide covers setup, code walkthrough, and a full example for developers."
date: Sun, 30 Aug 2026 18:53:10 +0000
lastmod: Sun, 30 Aug 2026 18:53:10 +0000
draft: false
url: /total/add-text-to-pdf-in-java/
author: "Farhan Raza"
summary: "Learn how to add text to PDF in Java with Conholdate.Total for Java. This guide shows SDK installation, font configuration, Unicode paragraph insertion, and saving the updated PDF, providing a clear step-by-step code example and best practices."
tags: ['java pdf manipulation', 'pdf text insertion', 'unicode pdf handling']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/add-text-to-pdf-in-java.jpg
   alt: "Add Text to PDF in Java"
   caption: "Add Text to PDF in Java"
steps:
  - "Step 1: Add Conholdate.Total Maven repository and dependency."
  - "Step 2: Load the source PDF with DocumentEditor."
  - "Step 3: Create a paragraph and configure font."
  - "Step 4: Insert the paragraph into the desired page."
  - "Step 5: Save the modified PDF."
faqs:
  - q: "How do I add text to PDF in Java using Conholdate.Total?"
    a: "Use the DocumentEditor class from [Conholdate.Total for Java](https://products.conholdate.com/total/java/) to load the PDF, create a Paragraph with a TextRun, configure font properties, insert it into a Page, and save with PdfSaveOptions."
  - q: "Can I insert Unicode characters when adding text to PDF in Java?"
    a: "Yes. The SDK fully supports Unicode. In the example we use the string \"Привет, 世界!\" which demonstrates Cyrillic and CJK characters."
  - q: "What licensing is required for production use?"
    a: "A valid license is needed. You can obtain a temporary license at the [temporary license page](https://purchase.conholdate.com/temporary-license/) or view pricing options at the [pricing page](https://purchase.conholdate.com/pricing/total/family/)."
  - q: "Where can I find more API details for PDF manipulation?"
    a: "The full API reference is available at the [API reference](https://reference.conholdate.com/java/)."
---

Adding custom notes or watermarks often requires you to add text to [PDF](https://docs.fileformat.com/pdf) in Java applications. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) is a powerful SDK that enables developers to edit PDF files programmatically. This guide walks you through the prerequisites, a detailed code walkthrough, and a complete example so you can overlay custom text on existing PDFs with ease.

## Prerequisites and Setup

Before you start, make sure you have the following:

- Java 8 or higher installed.
- Maven for dependency management.
- An IDE such as IntelliJ IDEA or Eclipse.
- A valid Conholdate.Total for Java license for production use (see the licensing section later).

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

Download the latest SDK binaries from the [download page](https://releases.conholdate.com/total/java/). After the Maven build succeeds, you are ready to start coding. The next section shows exactly how to load a PDF and insert text.

## Add Text to PDF in Java: Step-by-Step Walkthrough

Below is a concise walkthrough of each logical step. The full source code is reproduced later in the **Complete Code Example** section.

### Step 1: Load the Source PDF

First, create a `DocumentEditor` instance pointing to the input PDF. The editor loads the document for editing.

<!--[CODE_SNIPPET_START]-->
```java
String inputPdfPath = "input.pdf";
try (DocumentEditor editor = new DocumentEditor(inputPdfPath)) {
    // Load the PDF for editing
    EditableDocument editable = editor.edit();
```
<!--[CODE_SNIPPET_END]-->

The `DocumentEditor` class is documented in the [API reference](https://reference.conholdate.com/java/).

### Step 2: Create a Paragraph with Unicode Text

Construct a `Paragraph` and add a `TextRun` containing the text you want to overlay. This Java code example for inserting text into PDF demonstrates handling Unicode characters.

<!--[CODE_SNIPPET_START]-->
```java
Paragraph paragraph = new Paragraph();
TextRun textRun = new TextRun("Привет, 世界! – Added via Conholdate.Total");
```
<!--[CODE_SNIPPET_END]-->

### Step 3: Configure Font Properties

Set the font name, size, and style to ensure the text appears correctly across viewers.

<!--[CODE_SNIPPET_START]-->
```java
textRun.getFont().setName("Arial Unicode MS");
textRun.getFont().setSize(12);
textRun.getFont().setBold(true);
paragraph.getElements().add(textRun);
```
<!--[CODE_SNIPPET_END]-->

### Step 4: Insert Paragraph into Page

Add the paragraph to the first page (or create a new page if the document is empty). This demonstrates basic PDF page coordinates handling.

<!--[CODE_SNIPPET_START]-->
```java
if (!editable.getPages().isEmpty()) {
    Page firstPage = editable.getPages().get(0);
    firstPage.getElements().add(paragraph);
} else {
    Page newPage = new Page();
    newPage.getElements().add(paragraph);
    editable.getPages().add(newPage);
}
```
<!--[CODE_SNIPPET_END]-->

### Step 5: Save the Modified PDF

Finally, specify the output path and save the document using `PdfSaveOptions`.

<!--[CODE_SNIPPET_START]-->
```java
PdfSaveOptions saveOptions = new PdfSaveOptions();
saveOptions.setFilePath("output.pdf");
editor.save(editable, saveOptions);
} catch (Exception e) {
    e.printStackTrace();
}
```
<!--[CODE_SNIPPET_END]-->

With these steps, you have completed the PDF text insertion workflow.

## Complete Code Example: Insert Text to PDF in Java

The following example demonstrates the entire process from loading the source file to saving the updated PDF.

This example demonstrates how to add text to an existing PDF using Conholdate.Total for Java.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.groupdocs.editor.DocumentEditor;
import com.groupdocs.editor.document.EditableDocument;
import com.groupdocs.editor.document.elements.Page;
import com.groupdocs.editor.document.elements.Paragraph;
import com.groupdocs.editor.document.elements.TextRun;
import com.groupdocs.editor.options.PdfSaveOptions;

public class AddTextToPdf {
    public static void main(String[] args) {
        String inputPdfPath = "input.pdf";
        String outputPdfPath = "output.pdf";

        try (DocumentEditor editor = new DocumentEditor(inputPdfPath)) {
            // Load the PDF for editing
            EditableDocument editable = editor.edit();

            // Create a paragraph with Unicode text
            Paragraph paragraph = new Paragraph();
            TextRun textRun = new TextRun("Привет, 世界! – Added via Conholdate.Total");
            // Configure font properties
            textRun.getFont().setName("Arial Unicode MS");
            textRun.getFont().setSize(12);
            textRun.getFont().setBold(true);
            paragraph.getElements().add(textRun);

            // Insert the paragraph at the end of the first page (or create a new page if none exist)
            if (!editable.getPages().isEmpty()) {
                Page firstPage = editable.getPages().get(0);
                firstPage.getElements().add(paragraph);
            } else {
                Page newPage = new Page();
                newPage.getElements().add(paragraph);
                editable.getPages().add(newPage);
            }

            // Save the modified PDF
            PdfSaveOptions saveOptions = new PdfSaveOptions();
            saveOptions.setFilePath(outputPdfPath);
            editor.save(editable, saveOptions);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `output.pdf`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Conclusion

In this tutorial we showed how to add text to PDF in Java using the robust features of [Conholdate.Total for Java](https://products.conholdate.com/total/java/). By following the step‑by‑step walkthrough, you can reliably insert Unicode paragraphs, control font styling, and save the modified document. The SDK handles PDF page coordinates and text rendering internally, so you can focus on business logic. Remember to acquire a proper license for production use; you can obtain a temporary license from the [temporary license page](https://purchase.conholdate.com/temporary-license/) or explore pricing options on the [pricing page](https://purchase.conholdate.com/pricing/total/family/). With these tools in hand, enhancing PDFs with custom text becomes a straightforward part of your Java application.

## FAQs

- **How do I add text to PDF in Java without overwriting existing content?**  
  Use the `Page.getElements().add(paragraph)` method as shown in the example; it appends the new paragraph to the page's element collection, preserving existing content.

- **Is it possible to add a custom watermark text to PDF in Java?**  
  Yes. The same approach works for watermarks create a `Paragraph` with the desired watermark text, configure a semi‑transparent font color, and insert it on each page.

- **What should I do if the inserted text does not appear correctly for certain languages?**  
  Ensure the font you set supports the required Unicode range (e.g., "Arial Unicode MS"). The SDK respects the font settings, and the [documentation](https://docs.conholdate.com/java/) provides guidance on handling Unicode.

- **Can I batch process multiple PDFs to add the same text?**  
  Absolutely. Wrap the code inside a loop that iterates over a list of file paths, reusing the same `DocumentEditor` logic for each document.

## Read More
- [Add Shapes to PDF in Java](https://blog.conholdate.com/total/add-shapes-to-pdf-in-java/)
- [Add Barcode to PDF in Java](https://blog.conholdate.com/total/add-barcode-to-pdf-in-java/)
- [Add or Delete Pages in PDF using Java](https://blog.conholdate.com/total/add-or-delete-pages-in-pdf-using-java/)