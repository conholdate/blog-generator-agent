---
title: "Merge PDF in Node.JS"
seoTitle: "Merge PDF in Node.JS"
description: "Learn how to merge PDF files in Node.JS using GroupDocs.Merger Cloud SDK. Step-by-step guide, code example, cURL commands, and performance tips for developers."
date: Mon, 19 Oct 2026 15:04:19 +0000
lastmod: Mon, 19 Oct 2026 15:04:19 +0000
draft: false
url: /merger/merge-pdf-in-nodejs/
author: "Muhammad Mustafa"
summary: "Learn how Node.JS developers can merge PDF files using GroupDocs.Merger Cloud SDK. The guide covers setup, a detailed walkthrough, a full code sample, cURL REST calls, merge options, and performance tips for large or encrypted PDFs."
tags: ['nodejs pdf merge', 'pdf manipulation', 'encrypted pdf']
categories: ["GroupDocs.Merger Cloud Product Family"]
showtoc: true
cover:
   image: images/merge-pdf-in-nodejs.jpg
   alt: "Merge PDF in Node.JS"
   caption: "Merge PDF in Node.JS"
steps:
  - "Step 1: Install the SDK and import required classes"
  - "Step 2: Configure your GroupDocs credentials"
  - "Step 3: Define the PDF files to merge"
  - "Step 4: Set merge options such as output path"
  - "Step 5: Execute the merge operation and handle the result"
faqs:
  - q: "How do I merge PDF files in Node.JS using GroupDocs?"
    a: "Use the [GroupDocs.Merger Cloud SDK for Node.js](https://products.groupdocs.cloud/merger/nodejs/) to create a MergeApi instance, configure MergeOptions with your source PDFs, and call mergeDocuments. The full code example in this guide demonstrates the process."
  - q: "Can I merge encrypted PDF files in Node.JS?"
    a: "Yes, the SDK supports merging encrypted PDFs. Provide the correct passwords in the FileInfo objects before calling mergeDocuments. See the [official documentation](https://docs.groupdocs.cloud/merger/) for details."
  - q: "What are the licensing options for GroupDocs.Merger?"
    a: "GroupDocs offers flexible pricing plans. For testing, you can request a [temporary license](https://purchase.groupdocs.cloud/temporary-license/) to evaluate the library before purchasing a full subscription."
  - q: "Where can I find more examples and support?"
    a: "Additional samples are available on the [GitHub repository](https://github.com/groupdocs-merger-cloud/groupdocs-merger-cloud-node). For help, visit the [support forum](https://forum.groupdocs.cloud/c/merger/18)."
---

Combining multiple [PDF](https://docs.fileformat.com/pdf) documents into a single file is a frequent requirement when building document workflows or generating reports. [GroupDocs.Merger Cloud SDK for Node.js](https://products.groupdocs.cloud/merger/nodejs/) makes it easy to merge PDF in Node.JS without dealing with low‑level PDF structures. This guide walks you through setup, a step‑by‑step implementation, a full code example, equivalent cURL calls, and performance tips for large or encrypted PDFs.

## Before You Start: Prerequisites and Installation

Before you begin, ensure you have the following:

- Node.js 14 or later installed on your development machine.
- An active GroupDocs Cloud account with client ID and client secret.
- Access to the PDF files you want to combine, stored in GroupDocs Cloud storage.

Install the SDK via npm and download the latest package:

```bash
npm install groupdocs-merger-cloud
```

You can also retrieve the SDK from the official release page: [Download SDK](https://releases.groupdocs.cloud/merger/nodejs/). After installation, you are ready to start coding.

## Step-by-Step Guide to Merge PDF in Node.JS

### Step 1: Install SDK and Import Required Classes

First, import the classes you will need for merging PDFs.

```javascript
const { MergeApi, MergeOptions, FileInfo, Configuration } = require("@groupdocs/merger-cloud");
```

This import gives you access to the core API, configuration objects, and file descriptors.

### Step 2: Configure Your GroupDocs Credentials

Create a configuration object with your client credentials.

```javascript
const config = new Configuration({
    clientId: "YOUR_CLIENT_ID",
    clientSecret: "YOUR_CLIENT_SECRET"
});
```

Providing the correct credentials lets the library authenticate your requests.

### Step 3: Define the PDF Files to Merge

List the PDF documents you want to combine. This step prepares you to merge PDF in Node.JS efficiently.

```javascript
const filesToMerge = [
    new FileInfo({ filePath: "input1.pdf" }),
    new FileInfo({ filePath: "input2.pdf" })
];
```

Each `FileInfo` points to a file stored in your GroupDocs Cloud storage.

### Step 4: Set Merge Options

Configure the output location and attach the file list to the merge request.

```javascript
const mergeOptions = new MergeOptions();
mergeOptions.fileInfos = filesToMerge;
mergeOptions.outputPath = "merged_output.pdf";
```

These settings control how you merge PDF in Node.JS and where the result will be saved.

### Step 5: Execute the Merge Operation

Create the API instance, call the merge method, and handle the response.

```javascript
const mergeApi = new MergeApi(config);

try {
    const result = await mergeApi.mergeDocuments(mergeOptions);
    console.log("Merge completed. Output file stored at:", result.path);
} catch (error) {
    console.error("Error during PDF merge:", error);
}
```

The async call returns the path of the merged document if the operation succeeds.

## Full Implementation Example for Merging PDFs in Node.JS

The following code demonstrates the complete workflow from configuration to result handling.

```javascript
const { MergeApi, MergeOptions, FileInfo, Configuration } = require("@groupdocs/merger-cloud");

// Configure the SDK (replace with your actual credentials)
const config = new Configuration({
    clientId: "YOUR_CLIENT_ID",
    clientSecret: "YOUR_CLIENT_SECRET"
});

async function mergePdfFiles() {
    // Initialize the Merge API
    const mergeApi = new MergeApi(config);

    // Define the PDF files to be merged (must exist in GroupDocs Cloud storage)
    const filesToMerge = [
        new FileInfo({ filePath: "input1.pdf" }),
        new FileInfo({ filePath: "input2.pdf" })
    ];

    // Set merge options
    const mergeOptions = new MergeOptions();
    mergeOptions.fileInfos = filesToMerge;
    mergeOptions.outputPath = "merged_output.pdf";

    try {
        // Perform the merge operation
        const result = await mergeApi.mergeDocuments(mergeOptions);
        console.log("Merge completed. Output file stored at:", result.path);
    } catch (error) {
        console.error("Error during PDF merge:", error);
    }
}

// Execute the merge
mergePdfFiles();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/merger/) or reach out to the [support team](https://forum.groupdocs.cloud/c/merger/18) for assistance.

## Merging PDFs via REST API Using cURL

If you prefer a pure REST approach, the same operation can be performed with cURL commands.

First, obtain an access token:

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/oauth2/token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET","grant_type":"client_credentials"}'
```

Upload the source PDFs to your storage (replace `YOUR_ACCESS_TOKEN` with the token from the previous step):

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/storage/file/upload?path=input1.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "file=@/local/path/input1.pdf"
```

Repeat the upload for `input2.pdf`. Then request the merge operation:

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/merger/merge" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "fileInfos": [
               {"filePath":"input1.pdf"},
               {"filePath":"input2.pdf"}
           ],
           "outputPath":"merged_output.pdf"
         }'
```

Finally, download the merged file:

```bash
curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/download?path=merged_output.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o merged_output.pdf
```

For a complete list of endpoints and parameters, see the [API reference](https://reference.groupdocs.cloud/merger/).

## Configuring Merge Options

The SDK exposes several options that let you fine‑tune the merge process:

- **outputPath** - Destination path for the merged PDF. Adjust this to control where the result is stored.
- **fileInfos** - An array of `FileInfo` objects that define the source PDFs and their order.

You can also set additional properties such as `pages` to merge specific page ranges, or `password` for encrypted PDFs. Refer to the [official documentation](https://docs.groupdocs.cloud/merger/) for the full list of configurable fields.

## Performance Considerations for Merging PDFs

When merging large or many PDF files, keep these tips in mind:

- **Use async/await** to avoid blocking the event loop, especially for big documents.
- **Batch uploads**: upload source PDFs in parallel before invoking the merge to reduce overall latency.
- **Streamed processing**: for extremely large PDFs, consider storing intermediate results in cloud storage and merging them in smaller chunks.
- **Encrypted PDFs**: provide passwords in the `FileInfo` objects; processing encrypted files adds overhead, so merge them after decryption when possible.

Applying these practices helps you merge PDF in Node.JS efficiently while minimizing memory consumption.

## Questions You Might Have

- **How do I merge PDF files in Node.JS using GroupDocs?**  
  Use the [GroupDocs.Merger Cloud SDK for Node.js](https://products.groupdocs.cloud/merger/nodejs/) to create a `MergeApi` instance, configure `MergeOptions` with your source PDFs, and call `mergeDocuments`. The full code example in this guide demonstrates the process.

- **Can I merge encrypted PDF files in Node.JS?**  
  Yes, the SDK supports merging encrypted PDFs. Provide the correct passwords in the `FileInfo` objects before calling `mergeDocuments`. See the [official documentation](https://docs.groupdocs.cloud/merger/) for details.

- **What are the licensing options for GroupDocs.Merger?**  
  GroupDocs offers flexible pricing plans. For testing, you can request a [temporary license](https://purchase.groupdocs.cloud/temporary-license/) to evaluate the library before purchasing a full subscription.

- **Where can I find more examples and support?**  
  Additional samples are available on the [GitHub repository](https://github.com/groupdocs-merger-cloud/groupdocs-merger-cloud-node). For help, visit the [support forum](https://forum.groupdocs.cloud/c/merger/18).

## Further Reading
- [Split PDF into Multiple PDF in Node.JS](https://blog.groupdocs.cloud/merger/split-pdf-into-multiple-pdf-in-nodejs/)
- [Lock PDF Documents with Passwords using REST API in Node.js](https://blog.groupdocs.cloud/merger/lock-pdf-with-password-using-rest-api-in-nodejs/)
- [How to Merge PDF Files in C# using REST API](https://blog.groupdocs.cloud/merger/how-to-merge-pdf-files-in-csharp-using-rest-api/)