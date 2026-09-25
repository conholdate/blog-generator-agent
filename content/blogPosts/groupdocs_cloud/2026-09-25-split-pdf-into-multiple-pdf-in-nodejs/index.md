---
title: "Split PDF into Multiple PDF in Node.JS"
seoTitle: "Split PDF into Multiple PDF in Node.JS"
description: "Learn to split PDFs in Node.js using GroupDocs.Merger Cloud SDK. Get step-by-step code, cURL examples, and configuration tips for PDF splitting."
date: Fri, 25 Sep 2026 09:41:12 +0000
lastmod: Fri, 25 Sep 2026 09:41:12 +0000
draft: false
url: /merger/split-pdf-into-multiple-pdf-in-nodejs/
author: "Muhammad Mustafa"
summary: "Learn to split PDF into multiple PDF in Node.JS with GroupDocs.Merger Cloud SDK. The guide covers uploading a PDF, setting page ranges, running the split, downloading each part, and cleaning up storage. Full code, cURL examples, and option details are provided."
tags: ['nodejs pdf', 'pdf splitting', 'pdf processing']
categories: ["GroupDocs.Merger Cloud Product Family"]
showtoc: true
cover:
   image: images/split-pdf-into-multiple-pdf-in-nodejs.jpg
   alt: "Split PDF into Multiple PDF in Node.JS"
   caption: "Split PDF into Multiple PDF in Node.JS"
steps:
  - "Step 1: Install the GroupDocs.Merger Cloud SDK for Node.JS."
  - "Step 2: Configure your App SID and App Key."
  - "Step 3: Upload the source PDF to cloud storage."
  - "Step 4: Define page ranges and execute the split operation."
  - "Step 5: Download each split part and clean up."
faqs:
  - q: "Can I split PDF into multiple PDF in Node.JS using different page ranges?"
    a: "Yes. The SplitOptions.pages property lets you specify any range, such as ['1-2', '3-5'], to create separate PDF files. See the [GroupDocs.Merger Cloud SDK for Node.JS](https://products.groupdocs.cloud/merger/nodejs/) documentation for more details."
  - q: "Is it possible to split a PDF without uploading it first?"
    a: "The SDK works with files stored in GroupDocs cloud storage, so you need to upload the source PDF before splitting. After the operation you can delete the source file if it is no longer needed."
  - q: "How many parts can I generate from a single PDF?"
    a: "You can create as many parts as you define in the pages array. Each entry generates a separate PDF file, allowing you to split large documents into manageable sections."
  - q: "Do I need a special license to use the split feature in production?"
    a: "A valid commercial license is required for production use. You can obtain pricing details on the product page and get a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/)."
---

Splitting large [PDF](https://docs.fileformat.com/pdf) documents into smaller, more manageable pieces is a frequent requirement for developers building document‑centric applications. [GroupDocs.Merger Cloud SDK for Node.JS](https://products.groupdocs.cloud/merger/nodejs/) makes it easy to split PDF into multiple PDF in Node.JS, handling the heavy lifting in the cloud while you focus on business logic. In this guide you will see a complete working example, learn how to call the same operation with cURL, and discover configuration options that let you fine‑tune the split process.

## Split PDF Into Multiple PDF in Node.JS - Complete Code Example
This example demonstrates how to split a PDF into multiple PDF files using GroupDocs.Merger Cloud SDK for Node.JS.

```javascript
const fs = require('fs');
const path = require('path');
const GroupDocsMergerCloud = require('@groupdocs/merger-cloud');

// ---------- Set up API credentials ----------
const client = new GroupDocsMergerCloud.ApiClient();
client.appSid = 'YOUR_APP_SID';
client.appKey = 'YOUR_APP_KEY';

// ---------- Initialize API instances ----------
const mergerApi = new GroupDocsMergerCloud.MergerApi(client);
const storageApi = new GroupDocsMergerCloud.StorageApi(client);

// ---------- Helper to upload a local file to cloud storage ----------
async function uploadFile(localPath, cloudPath) {
    const fileData = fs.readFileSync(localPath);
    const uploadRequest = new GroupDocsMergerCloud.UploadFileRequest({
        path: cloudPath,
        file: fileData
    });
    await storageApi.uploadFile(uploadRequest);
}

// ---------- Helper to download a cloud file to local storage ----------
async function downloadFile(cloudPath, localPath) {
    const downloadRequest = new GroupDocsMergerCloud.DownloadFileRequest({ path: cloudPath });
    const response = await storageApi.downloadFile(downloadRequest);
    fs.writeFileSync(localPath, response);
}

// ---------- Main execution ----------
(async () => {
    try {
        // 1. Upload source PDF to cloud storage
        const localInputPdf = path.resolve(__dirname, 'input.pdf');          // local source PDF
        const cloudInputPdf = 'input/input.pdf';                            // cloud path
        await uploadFile(localInputPdf, cloudInputPdf);
        console.log('Uploaded PDF to cloud storage.');

        // 2. Configure split options (example: split into two parts: pages 1‑2 and 3‑5)
        const splitOptions = new GroupDocsMergerCloud.SplitOptions({
            pages: ['1-2', '3-5']                                            // page ranges to split
        });

        // 3. Build split request
        const splitRequest = new GroupDocsMergerCloud.SplitDocumentRequest({
            fileInfo: new GroupDocsMergerCloud.FileInfo({ filePath: cloudInputPdf }),
            options: splitOptions
        });

        // 4. Execute split operation
        const splitResult = await mergerApi.splitDocument(splitRequest);
        console.log(`Split operation completed. ${splitResult.length} parts generated.`);

        // 5. Download each split part and save locally
        for (let i = 0; i < splitResult.length; i++) {
            const partInfo = splitResult[i];
            const localOutputPath = path.resolve(__dirname, `output_part_${i + 1}.pdf`);
            await downloadFile(partInfo.path, localOutputPath);
            console.log(`Saved split part ${i + 1} to ${localOutputPath}`);
        }

        // 6. (Optional) Clean up cloud storage – delete uploaded source file
        const deleteRequest = new GroupDocsMergerCloud.DeleteFileRequest({ path: cloudInputPdf });
        await storageApi.deleteFile(deleteRequest);
        console.log('Cleaned up source file from cloud storage.');
    } catch (error) {
        console.error('Error during PDF split process:', error);
    }
})();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/merger/) or reach out to the [support team](https://forum.groupdocs.cloud/c/merger/18) for assistance.

## Split PDF Using REST API with cURL
If you prefer a pure REST approach, the same split operation can be performed with cURL commands. The steps below show how to obtain an access token, upload the source PDF, run the split, and download each part.

```bash
# 1. Get an access token (replace YOUR_CLIENT_ID and YOUR_CLIENT_SECRET)
curl -X POST "https://api.groupdocs.cloud/v2.0/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```

```bash
# 2. Upload the source PDF (replace YOUR_ACCESS_TOKEN and adjust paths)
curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/pdf" \
     --data-binary @./input.pdf
```

```bash
# 3. Execute the split operation (pages 1-2 and 3-5)
curl -X POST "https://api.groupdocs.cloud/v2.0/merger/split" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "fileInfo": { "filePath": "input.pdf" },
           "options": { "pages": ["1-2","3-5"] }
         }'
```

```bash
# 4. Download each generated part (example for part 1)
curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/output_part_1.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o ./output_part_1.pdf
```

For a complete list of endpoints and parameters, see the [official API documentation](https://reference.groupdocs.cloud/merger/).

## How Split PDF Into Multiple PDF in Node.JS Works
Understanding the flow helps you adapt the code to more complex scenarios.

1. **Initialize the API client** - `new GroupDocsMergerCloud.ApiClient()` creates a client that holds your App SID and App Key.  
   ```javascript
   const client = new GroupDocsMergerCloud.ApiClient();
   client.appSid = 'YOUR_APP_SID';
   client.appKey = 'YOUR_APP_KEY';
   ```
   

2. **Upload the source file** - The helper `uploadFile` reads the local PDF and sends it to cloud storage using `storageApi.uploadFile`.  
   ```javascript
   await uploadFile(localInputPdf, cloudInputPdf);
   ```
   

3. **Configure split options** - `new GroupDocsMergerCloud.SplitOptions({ pages: ['1-2', '3-5'] })` tells the service which page ranges to extract.  
   ```javascript
   const splitOptions = new GroupDocsMergerCloud.SplitOptions({
       pages: ['1-2', '3-5']
   });
   ```
   

4. **Send the split request** - `mergerApi.splitDocument(splitRequest)` posts the request and returns an array with information about each generated part.  
   ```javascript
   const splitResult = await mergerApi.splitDocument(splitRequest);
   ```
   

5. **Download the results** - The loop iterates over `splitResult`, calling `downloadFile` for each part and saving it locally.  
   ```javascript
   for (let i = 0; i < splitResult.length; i++) {
       const partInfo = splitResult[i];
       await downloadFile(partInfo.path, localOutputPath);
   }
   ```
   

For deeper details on each class and method, refer to the [API reference](https://reference.groupdocs.cloud/merger/).

## Prerequisites and Setup
Before you start, ensure you have the following:

- Node.js 14 or later installed.
- A GroupDocs Cloud account with valid App SID and App Key.
- Access to the internet for API calls.

Install the SDK via npm and download the latest package:

```bash
npm install groupdocs-merger-cloud
```

You can also fetch the binaries directly from the [download page](https://releases.groupdocs.cloud/merger/nodejs/).

## Fine-Tuning Split Options
The `SplitOptions` object offers several properties you can adjust:

- **pages** - An array of page ranges (e.g., `['1-2','3-5']`). This is the core setting used in the example.
- **outputPath** - Optional folder where the split files will be stored in cloud storage.
- **preserveMetadata** - When set to `true`, original document metadata is copied to each part. See the [API reference](https://reference.groupdocs.cloud/merger/) for more options.

Adjusting these values lets you control the size, naming, and metadata of each resulting PDF.

## Conclusion
Splitting PDF into multiple PDF in Node.JS becomes straightforward with the [GroupDocs.Merger Cloud SDK for Node.JS](https://products.groupdocs.cloud/merger/nodejs/). The SDK handles file upload, page‑range selection, and result retrieval, letting you focus on integrating the output into your workflow. Remember to secure your App SID and App Key, and consider using a commercial license for production deployments. Pricing details are available on the product page, and you can obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). With the code, cURL examples, and configuration tips in this guide, you're ready to implement robust PDF splitting in your Node.JS applications.

## FAQs
- **How do I split PDF into multiple PDF in Node.JS using custom page ranges?**  
  Use the `pages` property of `SplitOptions` to define any range you need, such as `['1-3','4-6']`. The SDK will generate a separate PDF for each range.

- **Can I split a PDF without storing it permanently in cloud storage?**  
  Yes. After uploading the source file and completing the split, you can delete the original file with `storageApi.deleteFile` as shown in the example.

- **Is there a limit on the number of parts I can create from a single PDF?**  
  The limit is defined by the number of entries you provide in the `pages` array. Each entry creates one output file.

- **Do I need a paid license to use the split feature in production?**  
  A commercial license is required for production use. Visit the product page for pricing and obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) for evaluation.

## Read More
- [Split PowerPoint PPT or PPTX into Multiple Files in Node.js](https://blog.groupdocs.cloud/merger/split-powerpoint-ppt-or-pptx-into-multiple-files-in-node.js/)
- [Split PDF File into Multiple PDF Files using Python](https://blog.groupdocs.cloud/merger/split-pdf-file-into-multiple-pdf-files-using-python/)
- [Java Document Splitting API - Split PDF into Multiple Files in Java](https://blog.groupdocs.cloud/merger/java-document-splitting-split-pdf-into-multiple-files-in-java/)