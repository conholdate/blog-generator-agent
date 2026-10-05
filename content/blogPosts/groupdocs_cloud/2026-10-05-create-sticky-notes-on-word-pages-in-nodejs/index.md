---
title: "Create Sticky Notes on Word Pages in Node.JS"
seoTitle: "Create Sticky Notes on Word Pages in Node.JS"
description: "Learn how to create Sticky Notes on Word pages in Node.JS using GroupDocs.Annotation Cloud SDK. Step-by-step guide, code example, and REST cURL commands."
date: Mon, 05 Oct 2026 16:29:28 +0000
lastmod: Mon, 05 Oct 2026 16:29:28 +0000
draft: false
url: /annotation/create-sticky-notes-on-word-pages-in-nodejs/
author: "Muhammad Mustafa"
summary: "This tutorial shows Node.JS developers how to create Sticky Notes on Word pages in Node.JS with GroupDocs.Annotation Cloud SDK. Follow prerequisites, a step-by-step walkthrough, sample, cURL REST calls, and configuration tips to add annotations to DOCX files."
tags: ['nodejs word annotations', 'sticky notes', 'document automation']
categories: ["GroupDocs.Annotation Cloud Product Family"]
showtoc: true
cover:
   image: images/create-sticky-notes-on-word-pages-in-nodejs.jpg
   alt: "Create Sticky Notes on Word Pages in Node.JS"
   caption: "Create Sticky Notes on Word Pages in Node.JS"
steps:
  - "Step 1: Install the SDK and configure credentials"
  - "Step 2: Define source and destination files"
  - "Step 3: Set up sticky note geometry"
  - "Step 4: Build the annotation object"
  - "Step 5: Execute the annotation request"
faqs:
  - q: "How can I create Sticky Notes on Word pages in Node.JS using GroupDocs.Annotation Cloud SDK?"
    a: "Use the SDK's AnnotateApi as shown in this guide. The [GroupDocs.Annotation Cloud SDK for Node.JS](https://products.groupdocs.cloud/annotation/nodejs/) provides methods to add sticky notes to DOCX files programmatically."
  - q: "What file formats can I annotate with the SDK?"
    a: "The SDK supports DOCX, PDF, PPTX, XLSX and many other formats. See the [official documentation](https://docs.groupdocs.cloud/annotation/) for the full list."
  - q: "How do I authenticate when using the REST API for sticky notes?"
    a: "Obtain an access token via the /auth/token endpoint using your clientId and clientSecret. Detailed steps are in the [API reference](https://reference.groupdocs.cloud/annotation/)."
  - q: "Can I customize the sticky note color or size?"
    a: "Yes, you can set the color property (e.g., \"FFFF00\" for yellow) and define the rectangle dimensions. Adjust these values in the AnnotationInfo object before sending the request."
---

Adding quick comments directly onto Word documents is a common requirement for collaborative review workflows. [GroupDocs.Annotation Cloud SDK for Node.JS](https://products.groupdocs.cloud/annotation/nodejs/) lets you programmatically add rich annotations without leaving your server environment. In this guide we will show you how to create Sticky Notes on Word pages in Node.JS, covering setup, a detailed walkthrough, a complete code example, and equivalent cURL calls.

## Setting Up GroupDocs.Annotation Cloud SDK for Node.JS

Before you start, make sure you have:

- Node.js 14+ and npm installed
- A GroupDocs cloud account with **clientId** and **clientSecret**
- Access to the source [DOCX](https://docs.fileformat.com/word-processing/docx/) file you want to annotate

Install the SDK via npm:

```bash
npm install groupdocs-annotation-cloud
```

Download the latest package from the official release page if you prefer a manual install: [GroupDocs.Annotation Cloud SDK for Node.JS Download](https://releases.groupdocs.cloud/annotation/nodejs/).

Create a configuration object with your credentials (excerpt from the full example):

```javascript
const { Configuration } = require("@groupdocs.annotation-cloud");

const config = new Configuration({
    clientId: "YOUR_CLIENT_ID",
    clientSecret: "YOUR_CLIENT_SECRET"
});
```

With the SDK installed and credentials ready, we can move on to the implementation.

## Create Sticky Notes on Word Pages in Node.JS: Step-by-Step Walkthrough

In this walkthrough we will create Sticky Notes on Word pages in Node.JS using the SDK's annotation classes.

### Step 1: Initialize the Annotation API
First, import the required classes and create an instance of **AnnotateApi**.

```javascript
const { AnnotateApi, models } = require("@groupdocs.annotation-cloud");
const annotateApi = new AnnotateApi(config);
```

### Step 2: Define Source and Destination Files
Specify the input DOCX and the path for the annotated output.

```javascript
const inputFilePath = "sample.docx";
const outputFilePath = "sample_annotated.docx";

const fileInfo = new models.FileInfo();
fileInfo.filePath = inputFilePath;
```

### Step 3: Set Up the Sticky Note Position
Create a **Rectangle** that determines where the sticky note will appear on page 1.

```javascript
const rect = new models.Rectangle();
rect.x = 100;      // distance from left edge (points)
rect.y = 100;      // distance from top edge (points)
rect.width = 200;  // width of the sticky note
rect.height = 100; // height of the sticky note
```

### Step 4: Build the Sticky Note Annotation Object
Configure the annotation type, page number, rectangle, text, and background color.

```javascript
const stickyNote = new models.AnnotationInfo();
stickyNote.annotationType = "StickyNote";
stickyNote.pageNumber = 1;
stickyNote.rect = rect;
stickyNote.text = "This is a sticky note added via GroupDocs.Annotation Cloud SDK.";
stickyNote.color = "FFFF00"; // Yellow background
```

### Step 5: Execute the Annotation Request
Assemble the request options and call the **annotate** method.

```javascript
const annotateOptions = new models.AnnotateOptions();
annotateOptions.fileInfo = fileInfo;
annotateOptions.annotations = [stickyNote];
annotateOptions.outputPath = outputFilePath;

(async () => {
    try {
        const request = new models.AnnotateRequest(annotateOptions);
        const response = await annotateApi.annotate(request);
        console.log("Sticky note created successfully. Output saved to:", response.path);
    } catch (err) {
        console.error("Failed to create sticky note:", err);
    }
})();
```

## Full Working Example for Create Sticky Notes on Word Pages in Node.JS

The following example demonstrates the complete implementation for creating Sticky Notes on Word pages in Node.JS using GroupDocs.Annotation Cloud SDK.

```javascript
const { AnnotateApi, Configuration, models } = require("@groupdocs.annotation-cloud");

// -----------------------------------------------------------------------------
// Configuration – replace with your actual GroupDocs credentials
// -----------------------------------------------------------------------------
const config = new Configuration({
    clientId: "YOUR_CLIENT_ID",
    clientSecret: "YOUR_CLIENT_SECRET"
});

const annotateApi = new AnnotateApi(config);

// -----------------------------------------------------------------------------
// Define input and output files
// -----------------------------------------------------------------------------
const inputFilePath = "sample.docx";
const outputFilePath = "sample_annotated.docx";

// -----------------------------------------------------------------------------
// Build FileInfo object for the source document
// -----------------------------------------------------------------------------
const fileInfo = new models.FileInfo();
fileInfo.filePath = inputFilePath;

// -----------------------------------------------------------------------------
// Define rectangle (position & size) for the sticky note on page 1
// -----------------------------------------------------------------------------
const rect = new models.Rectangle();
rect.x = 100;      // distance from left edge (points)
rect.y = 100;      // distance from top edge (points)
rect.width = 200;  // width of the sticky note
rect.height = 100; // height of the sticky note

// -----------------------------------------------------------------------------
// Create the sticky‑note annotation
// -----------------------------------------------------------------------------
const stickyNote = new models.AnnotationInfo();
stickyNote.annotationType = "StickyNote";
stickyNote.pageNumber = 1;
stickyNote.rect = rect;
stickyNote.text = "This is a sticky note added via GroupDocs.Annotation Cloud SDK.";
stickyNote.color = "FFFF00"; // Yellow background

// -----------------------------------------------------------------------------
// Assemble the annotate request options
// -----------------------------------------------------------------------------
const annotateOptions = new models.AnnotateOptions();
annotateOptions.fileInfo = fileInfo;
annotateOptions.annotations = [stickyNote];
annotateOptions.outputPath = outputFilePath;

// -----------------------------------------------------------------------------
// Execute the request
// -----------------------------------------------------------------------------
(async () => {
    try {
        const request = new models.AnnotateRequest(annotateOptions);
        const response = await annotateApi.annotate(request);
        console.log("Sticky note created successfully. Output saved to:", response.path);
    } catch (err) {
        console.error("Failed to create sticky note:", err);
    }
})();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/annotation/) or reach out to the [support team](https://forum.groupdocs.cloud/c/annotation/10) for assistance.

## Adding Sticky Note Annotations with cURL and the REST API

The REST API offers the same capability without writing code. Below are the required cURL calls.

First, obtain an access token:

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0.0/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
```

Upload the source DOCX file (replace **YOUR_ACCESS_TOKEN** with the token from the previous step):

```bash
curl -X PUT "https://api.groupdocs.cloud/v2.0.0/storage/file/sample.docx" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/octet-stream" \
     --data-binary @sample.docx
```

Create the sticky note annotation:

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0.0/annotation/annotate" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "fileInfo": { "filePath": "sample.docx" },
           "annotations": [
               {
                   "annotationType": "StickyNote",
                   "pageNumber": 1,
                   "rect": { "x": 100, "y": 100, "width": 200, "height": 100 },
                   "text": "This is a sticky note added via GroupDocs.Annotation Cloud SDK.",
                   "color": "FFFF00"
               }
           ],
           "outputPath": "sample_annotated.docx"
         }'
```

Download the annotated document:

```bash
curl -X GET "https://api.groupdocs.cloud/v2.0.0/storage/file/sample_annotated.docx?download=true" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o sample_annotated.docx
```

For more details on request payloads, see the [API reference](https://reference.groupdocs.cloud/annotation/).

## Configuring Annotation Options for Sticky Notes

The SDK exposes several properties that let you fine‑tune the sticky note appearance and behavior:

- **annotationType** - must be set to `"StickyNote"` (required).
- **pageNumber** - the page where the note will appear.
- **rect** - defines position (`x`, `y`) and size (`width`, `height`). Adjust these values to control placement.
- **text** - the note content.
- **color** - background color in HEX (e.g., `"FFFF00"` for yellow).

You can also set optional fields such as **author**, **fontFamily**, or **opacity** via the **AnnotationInfo** model. Refer to the [API reference](https://reference.groupdocs.cloud/annotation/) for the complete list of configurable properties.

## Conclusion

By following the steps above you now know how to create Sticky Notes on Word pages in Node.JS using GroupDocs.Annotation Cloud SDK. Whether you prefer a native Node.js implementation or a REST‑based cURL workflow, the SDK provides a consistent and reliable way to annotate DOCX files programmatically. Remember to apply a valid license for production use; you can obtain a temporary license from the [license page](https://purchase.groupdocs.cloud/temporary-license/) or review pricing options on the product page. Happy annotating!

## FAQs

- **How can I create Sticky Notes on Word pages in Node.JS using GroupDocs.Annotation Cloud SDK?**  
  Use the **AnnotateApi** as demonstrated in the code example. The SDK handles file access, annotation creation, and output generation automatically.

- **What file formats are supported for annotation with the SDK?**  
  The SDK works with DOCX, [PDF](https://docs.fileformat.com/pdf), [PPTX](https://docs.fileformat.com/presentation/pptx/), [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/), and many other popular formats. See the full list in the [official documentation](https://docs.groupdocs.cloud/annotation/).

- **How do I authenticate when using the REST API for sticky notes?**  
  Obtain an access token via the `/auth/token` endpoint using your client credentials, then include the token in the `Authorization: Bearer` header for all subsequent calls. Detailed steps are in the [API reference](https://reference.groupdocs.cloud/annotation/).

- **Can I customize the sticky note color or size?**  
  Yes. Set the `color` property to a HEX value and adjust the `rect` dimensions (`width`, `height`) to control the note's size and placement.

## Read More
- [Strikethrough Text in a PDF with Node.js and REST API](https://blog.groupdocs.cloud/annotation/strikethrough-text-in-a-pdf-using-nodejs/)
- [Add Annotations in Word Documents using REST API in Node.js](https://blog.groupdocs.cloud/annotation/add-annotations-in-word-documents-using-a-rest-api-in-node-js/)
- [Annotate Word Files using Python](https://blog.groupdocs.cloud/annotation/annotate-docx-files-using-python/)