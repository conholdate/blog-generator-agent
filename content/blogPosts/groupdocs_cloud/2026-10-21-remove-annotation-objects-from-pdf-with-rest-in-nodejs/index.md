---
title: "Remove Annotation Objects from PDF with REST in Node.JS"
seoTitle: "Remove Annotation Objects from PDF with REST in Node.JS"
description: "Learn how to remove Annotation objects from PDF with REST in Node.JS using GroupDocs.Annotation Cloud SDK. Step-by-step guide with code, cURL and practices."
date: Wed, 21 Oct 2026 13:18:44 +0000
lastmod: Wed, 21 Oct 2026 13:18:44 +0000
draft: false
url: /annotation/remove-annotation-objects-from-pdf-with-rest-in-nodejs/
author: "Muhammad Mustafa"
summary: "Learn how to remove Annotation objects from PDF with REST in Node.JS using GroupDocs.Annotation Cloud SDK. The guide covers uploading a PDF, deleting its annotations via the API, and downloading the cleaned file, plus code snippets, cURL calls and config tips."
tags: ['pdf annotation removal', 'nodejs rest api', 'pdf manipulation']
categories: ["GroupDocs.Annotation Cloud Product Family"]
showtoc: true
cover:
   image: images/remove-annotation-objects-from-pdf-with-rest-in-nodejs.jpg
   alt: "Remove Annotation Objects from PDF with REST in Node.JS"
   caption: "Remove Annotation Objects from PDF with REST in Node.JS"
steps:
  - "Step 1: [Clear actionable instruction]"
  - "Step 2: [Clear actionable instruction]"
  - "Step 3: [Clear actionable instruction]"
  - "Step 4: [Clear actionable instruction]"
  - "Step 5: [Optional]"
faqs:
  - q: "How do I authenticate with GroupDocs.Annotation Cloud API?"
    a: "Obtain a client ID and secret from your GroupDocs account, then request an access token via the OAuth endpoint. See the [official documentation](https://docs.groupdocs.cloud/annotation/) for details."
  - q: "Can I delete specific annotations instead of all?"
    a: "Yes, provide the IDs of the annotations you want to remove in the DeleteAnnotationsRequest. The SDK returns the list of annotation IDs after a GetAnnotations call."
  - q: "How can I remove Annotation objects from PDF with REST in Node.JS?"
    a: "Use the GroupDocs.Annotation Cloud SDK for Node.js to call the DeleteAnnotations endpoint after retrieving annotation IDs. The full workflow is demonstrated in the code example and cURL section of this guide."
  - q: "What licensing is required for production use?"
    a: "A paid license is needed for production. You can acquire a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) while evaluating."
---

Removing unwanted notes, highlights, or ink marks from PDFs is a frequent requirement when preparing clean documents for distribution. [GroupDocs.Annotation Cloud SDK for Node.js](https://products.groupdocs.cloud/annotation/nodejs/) provides a powerful REST‑based library that lets you manage [PDF](https://docs.fileformat.com/pdf) annotations programmatically. This guide shows you how to remove Annotation objects from PDF with REST in Node.JS, step by step. You will see a complete code example, equivalent cURL commands, configuration tips, and best‑practice recommendations to integrate annotation removal into your services.

## Full Working Example to Remove Annotation Objects from PDF with REST in Node.JS

This example demonstrates how to upload a PDF, delete all its annotations, and download the cleaned file using the GroupDocs.Annotation SDK.

```javascript
const fs = require('fs');
const path = require('path');
const GroupDocsAnnotationCloud = require("@groupdocs/annotation-cloud");

// ==== Authentication =========================================================
const clientId = "YOUR_CLIENT_ID";
const clientSecret = "YOUR_CLIENT_SECRET";

const config = new GroupDocsAnnotationCloud.Configuration(clientId, clientSecret);
const annotationsApi = new GroupDocsAnnotationCloud.AnnotationsApi(config);
const storageApi = new GroupDocsAnnotationCloud.StorageApi(config);

// ==== Local & Remote file definitions =======================================
const localInputPath = path.resolve(__dirname, "input.pdf");
const localOutputPath = path.resolve(__dirname, "output.pdf");
const remoteFilePath = "input.pdf";

// ==== Main workflow ==========================================================
(async () => {
    // 1. Upload PDF to GroupDocs Cloud storage
    const fileBytes = fs.readFileSync(localInputPath);
    const uploadRequest = new GroupDocsAnnotationCloud.UploadFileRequest({
        path: remoteFilePath,
        file: fileBytes
    });
    await storageApi.uploadFile(uploadRequest);

    // 2. Build FileInfo object for the uploaded PDF
    const fileInfo = new GroupDocsAnnotationCloud.FileInfo({
        filePath: remoteFilePath
    });

    // 3. Retrieve all existing annotations
    const getAnnotationsRequest = new GroupDocsAnnotationCloud.GetAnnotationsRequest({
        fileInfo: fileInfo
    });
    const annotationsResult = await annotationsApi.getAnnotations(getAnnotationsRequest);
    const annotationIds = (annotationsResult.annotations || []).map(a => a.id);

    // 4. Delete all annotations (if any)
    if (annotationIds.length > 0) {
        const deleteRequest = new GroupDocsAnnotationCloud.DeleteAnnotationsRequest({
            fileInfo: fileInfo,
            annotationIds: annotationIds
        });
        await annotationsApi.deleteAnnotations(deleteRequest);
    }

    // 5. Download the cleaned PDF back to local storage
    const downloadRequest = new GroupDocsAnnotationCloud.DownloadFileRequest({
        path: remoteFilePath
    });
    const fileStream = await storageApi.downloadFile(downloadRequest);
    fs.writeFileSync(localOutputPath, fileStream);
    console.log(`All annotations removed. Clean file saved to ${localOutputPath}`);
})();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/annotation/) or reach out to the [support team](https://forum.groupdocs.cloud/c/annotation/10) for assistance.

## Delete PDF Annotations via REST API Using cURL

Below are the cURL commands that perform the same annotation removal workflow through the GroupDocs.Annotation Cloud REST endpoints.

```bash
# 1. Obtain an access token
curl -X POST "https://api.groupdocs.cloud/v2.0/auth/token" \
     -H "Content-Type: application/json" \
     -d "{\"client_id\":\"YOUR_CLIENT_ID\",\"client_secret\":\"YOUR_CLIENT_SECRET\"}"
```

```bash
# 2. Upload the source PDF
curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/pdf" \
     --data-binary "@input.pdf"
```

```bash
# 3. Retrieve annotation IDs
curl -X GET "https://api.groupdocs.cloud/v2.0/annotation/annotations?filePath=input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

```bash
# 4. Delete all retrieved annotations
curl -X DELETE "https://api.groupdocs.cloud/v2.0/annotation/annotations?filePath=input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d "{\"annotationIds\":[\"id1\",\"id2\"]}"
```

```bash
# 5. Download the cleaned PDF
curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o output.pdf
```

For a complete list of endpoints and parameters, see the [official API documentation](https://reference.groupdocs.cloud/annotation/).

## How Remove Annotation Objects from PDF with REST in Node.JS Works

1. **Authentication Setup** - The `Configuration` class is instantiated with your `clientId` and `clientSecret`, creating an authenticated context for all subsequent API calls.  
   ```javascript
   const config = new GroupDocsAnnotationCloud.Configuration(clientId, clientSecret);
   ```
2. **File Upload** - `UploadFileRequest` sends the local PDF bytes to GroupDocs Cloud storage. The `storageApi.uploadFile` method handles the transfer.  
   ```javascript
   const uploadRequest = new GroupDocsAnnotationCloud.UploadFileRequest({
       path: remoteFilePath,
       file: fileBytes
   });
   await storageApi.uploadFile(uploadRequest);
   ```
3. **Retrieve Annotations** - `GetAnnotationsRequest` builds a request object with a `FileInfo` reference. The `annotationsApi.getAnnotations` call returns a collection of annotation objects, from which IDs are extracted.  
   ```javascript
   const getAnnotationsRequest = new GroupDocsAnnotationCloud.GetAnnotationsRequest({
       fileInfo: fileInfo
   });
   const annotationsResult = await annotationsApi.getAnnotations(getAnnotationsRequest);
   ```
4. **Delete Annotations** - If any IDs exist, `DeleteAnnotationsRequest` is populated and passed to `annotationsApi.deleteAnnotations`, which permanently removes the annotations from the stored PDF.  
   ```javascript
   const deleteRequest = new GroupDocsAnnotationCloud.DeleteAnnotationsRequest({
       fileInfo: fileInfo,
       annotationIds: annotationIds
   });
   await annotationsApi.deleteAnnotations(deleteRequest);
   ```
5. **Download Clean PDF** - Finally, `DownloadFileRequest` fetches the updated file, and `fs.writeFileSync` writes it to the local filesystem.  
   ```javascript
   const downloadRequest = new GroupDocsAnnotationCloud.DownloadFileRequest({
       path: remoteFilePath
   });
   const fileStream = await storageApi.downloadFile(downloadRequest);
   fs.writeFileSync(localOutputPath, fileStream);
   ```

For detailed class and method definitions, refer to the [API reference](https://reference.groupdocs.cloud/annotation/).

## Installing and Configuring GroupDocs.Annotation Cloud SDK for Node.js

The SDK is distributed as an npm package. Install it with the command below and then require it in your project.

```bash
npm install groupdocs-annotation-cloud
```

You can also download the latest package directly from the [GitHub releases page](https://github.com/groupdocs-annotation-cloud/groupdocs-annotation-cloud-node) or the official [download URL](https://releases.groupdocs.cloud/annotation/nodejs/).

After installation, import the library and create a configuration object as shown in the code example:

```javascript
const GroupDocsAnnotationCloud = require("@groupdocs/annotation-cloud");
const config = new GroupDocsAnnotationCloud.Configuration("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
```

Make sure your runtime environment meets the Node.js version requirements and that you have a valid GroupDocs account to obtain the client credentials.

## Annotation Removal Options and Settings

The SDK exposes several parameters you can tune:

- **clientId / clientSecret** - Credentials for OAuth authentication. Set them in the `Configuration` constructor.  
- **fileInfo.filePath** - The path of the PDF in GroupDocs Cloud storage. Adjust this if you store files in a different folder.  
- **annotationIds** - An array of IDs returned by `GetAnnotations`. Supplying a subset allows selective deletion.  

Additional settings such as request timeouts and proxy configuration are available in the SDK documentation; see the [official documentation](https://docs.groupdocs.cloud/annotation/) for the full list.

## Best Practices for Removing PDF Annotations via REST

- **Validate Annotation IDs** - Always check that the IDs you intend to delete exist; attempting to delete non‑existent IDs can cause a 404 error.  
- **Use HTTPS** - All API calls must be made over HTTPS to protect your credentials and document data.  
- **Handle Large Files with Chunked Uploads** - For PDFs larger than 100 MB, prefer the multipart upload endpoint to avoid timeouts.  
- **Log API Responses** - Store request IDs and responses for audit trails and easier troubleshooting.  
- **Reuse Access Tokens** - Cache the OAuth token until it expires to reduce authentication overhead.

## Common Questions

- **How do I authenticate with GroupDocs.Annotation Cloud API?**  
  Obtain a client ID and secret from your GroupDocs account, then request an access token via the OAuth endpoint. See the [official documentation](https://docs.groupdocs.cloud/annotation/) for details.

- **Can I delete specific annotations instead of all?**  
  Yes, provide the IDs of the annotations you want to remove in the DeleteAnnotationsRequest. The SDK returns the list of annotation IDs after a GetAnnotations call.

- **How can I remove Annotation objects from PDF with REST in Node.JS?**  
  Use the GroupDocs.Annotation Cloud SDK for Node.js to call the DeleteAnnotations endpoint after retrieving annotation IDs. The full workflow is demonstrated in the code example and cURL section of this guide.

- **What licensing is required for production use?**  
  A paid license is needed for production. You can acquire a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) while evaluating.

## Further Reading
- [Extract or Remove Annotations from PDF using REST API in Node.js](https://blog.groupdocs.cloud/annotation/extract-or-remove-annotations-from-pdf-using-rest-api-in-node-js/)
- [Strikethrough Text in a PDF with Node.js and REST API](https://blog.groupdocs.cloud/annotation/strikethrough-text-in-a-pdf-using-nodejs/)
- [Remove Annotations from PDF using REST API in Python](https://blog.groupdocs.cloud/annotation/remove-annotations-from-pdf-using-rest-api-in-python/)