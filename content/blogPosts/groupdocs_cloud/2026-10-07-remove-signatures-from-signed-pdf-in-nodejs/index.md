---
title: "Remove Signatures from Signed PDF in Node.JS"
seoTitle: "Remove Signatures from Signed PDF in Node.JS"
description: "Learn how to remove signatures from a signed PDF document using GroupDocs.Signature Cloud SDK for Node.JS. Step-by-step guide with code and cURL."
date: Wed, 07 Oct 2026 14:49:25 +0000
lastmod: Wed, 07 Oct 2026 14:49:25 +0000
draft: false
url: /signature/remove-signatures-from-signed-pdf-in-nodejs/
author: "Muhammad Mustafa"
summary: "Learn how to remove signatures from a signed PDF document with GroupDocs.Signature Cloud SDK for Node.JS. This guide provides step-by-step instructions, a full code example, cURL commands, and tips to automate PDF signature removal in your Node.js projects."
tags: ['pdf signature removal', 'nodejs pdf manipulation', 'digital signature processing']
categories: ["GroupDocs.Signature Cloud Product Family"]
showtoc: true
cover:
   image: images/remove-signatures-from-signed-pdf-in-nodejs.jpg
   alt: "Remove Signatures from Signed PDF in Node.JS"
   caption: "Remove Signatures from Signed PDF in Node.JS"
steps:
  - "Step 1: Initialize configuration with your GroupDocs credentials."
  - "Step 2: Create API client and Signature API instance."
  - "Step 3: Define source PDF file information."
  - "Step 4: Prepare delete request with output path."
  - "Step 5: Execute request and handle the result."
faqs:
  - q: "How does remove Signatures from Signed PDF document work with GroupDocs.Signature Cloud SDK for Node.JS?"
    a: "The library authenticates using your client ID and secret, then calls the DeleteSignatures endpoint to strip all signatures from the specified PDF. See the [GroupDocs.Signature Cloud SDK for Node.JS](https://products.groupdocs.cloud/signature/nodejs/) documentation for details."
  - q: "Can I delete signatures from a PDF stored in GroupDocs cloud storage?"
    a: "Yes. Provide the storage path in the FileInfo object and the SDK will access the file directly. Refer to the [official documentation](https://docs.groupdocs.cloud/signature/) for storage handling."
  - q: "What if I need to keep a copy of the original signed PDF?"
    a: "Specify a different outputPath in DeleteSignaturesRequest so the original file remains untouched while the new file contains no signatures."
  - q: "Do I need a special license to use this functionality in production?"
    a: "A valid license is required for production use. You can obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/)."
---

remove Signatures from Signed [PDF](https://docs.fileformat.com/pdf) document is a common requirement when you need a clean copy for further processing or archiving. [GroupDocs.Signature Cloud SDK for Node.js](https://products.groupdocs.cloud/signature/nodejs/) provides a robust library that lets you manipulate PDF signatures programmatically. In this tutorial you will learn how to delete all signatures from a PDF using Node.js, see a complete code example, and explore equivalent cURL commands for the REST API.

## Remove Signatures from Signed PDF Document in Node.JS in 5 Steps

The following steps show how to **remove Signatures from Signed PDF document** using the GroupDocs.Signature Cloud SDK for Node.js.

1. **Initialize configuration with credentials**: Create a `Configuration` object that holds your client ID and secret.  
```javascript
const config = new Configuration({
    clientId: process.env.GROUPDOCS_CLIENT_ID,
    clientSecret: process.env.GROUPDOCS_CLIENT_SECRET
});
```

2. **Create API client and Signature API instance**: Use the configuration to build an `ApiClient` and then a `SignatureApi`.  
```javascript
const apiClient = new ApiClient(config);
const signatureApi = new SignatureApi(apiClient);
```

3. **Define source PDF file information**: Set the `filePath` of the PDF that resides in GroupDocs storage.  
```javascript
const fileInfo = new FileInfo();
fileInfo.filePath = "input.pdf";
```

4. **Prepare delete request with output path**: Create a `DeleteSignaturesRequest`, assign the `fileInfo`, and specify where the result should be saved.  
```javascript
const deleteRequest = new DeleteSignaturesRequest();
deleteRequest.fileInfo = fileInfo;
deleteRequest.outputPath = "output.pdf";
```

5. **Execute request and handle the result**: Call `deleteSignatures` and process the response.  
```javascript
try {
    const result = await signatureApi.deleteSignatures(deleteRequest);
    console.log("All signatures removed successfully.");
    console.log("Result file stored at:", result.path);
} catch (err) {
    console.error("Failed to remove signatures:", err);
}
```

For more details on each class, refer to the [API Reference](https://reference.groupdocs.cloud/signature/).

## Strip All Signatures from PDF - Complete Code Example

The following example demonstrates the full workflow for removing signatures from a signed PDF document.

```javascript
const { Configuration, ApiClient, SignatureApi, DeleteSignaturesRequest, FileInfo } = require("@groupdocs/signature-cloud");

async function removeSignaturesFromPdf() {
    // Initialize configuration with your GroupDocs credentials
    const config = new Configuration({
        clientId: process.env.GROUPDOCS_CLIENT_ID,
        clientSecret: process.env.GROUPDOCS_CLIENT_SECRET
    });

    // Create API client and Signature API instance
    const apiClient = new ApiClient(config);
    const signatureApi = new SignatureApi(apiClient);

    // Define source PDF file (must be already uploaded to GroupDocs storage)
    const fileInfo = new FileInfo();
    fileInfo.filePath = "input.pdf"; // path in GroupDocs storage

    // Prepare request to delete all signatures and store result as a new file
    const deleteRequest = new DeleteSignaturesRequest();
    deleteRequest.fileInfo = fileInfo;
    deleteRequest.outputPath = "output.pdf"; // resulting file path in storage

    try {
        const result = await signatureApi.deleteSignatures(deleteRequest);
        console.log("All signatures removed successfully.");
        console.log("Result file stored at:", result.path);
    } catch (err) {
        console.error("Failed to remove signatures:", err);
    }
}

removeSignaturesFromPdf();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/signature/) or reach out to the [support team](https://forum.groupdocs.cloud/c/signature/13) for assistance.

## Remove PDF Signatures via REST API Using cURL

Below are the cURL commands that perform the same operation through the GroupDocs REST API.

1. **Authenticate and obtain an access token**  
```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/connect/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```

2. **Upload the source PDF to GroupDocs storage**  
```bash
curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/pdf" \
     --data-binary @input.pdf
```

3. **Execute the delete signatures operation**  
```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/signature/delete" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "fileInfo": { "filePath": "input.pdf" },
           "outputPath": "output.pdf"
         }'
```

4. **Download the resulting PDF**  
```bash
curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/output.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o output.pdf
```

For the full API contract, see the [API Reference](https://reference.groupdocs.cloud/signature/).

## Getting the Environment Ready

Install the library via npm and ensure your Node.js version meets the minimum requirements.

```bash
npm install groupdocs-signature-cloud
```

You can also download the latest package from the [download page](https://releases.groupdocs.cloud/signature/nodejs/). Make sure you have a valid GroupDocs account and have generated client credentials.

## What Makes GroupDocs.Signature Cloud SDK for Node.js Ideal for PDF Signature Removal

- **Delete all signature types** - Supports text, image, barcode, QR code, and digital signatures.  
- **Cloud storage integration** - Works directly with files stored in GroupDocs cloud, eliminating the need for local file handling.  
- **High performance** - Optimized for large PDF documents and batch processing.  
- **Comprehensive API** - Full REST endpoints are mirrored in the Node.js library, giving you flexibility to choose code or cURL.  
- **Secure processing** - All operations occur over HTTPS and respect your account permissions.  

For deeper insight, refer to the [official documentation](https://docs.groupdocs.cloud/signature/).

## Fine-Tuning Signature Deletion Options

While the basic request removes every signature, you can adjust options such as:

- **outputPath** - Choose a different folder or filename for the unsigned PDF.  
- **fileInfo.password** - If the source PDF is password‑protected, set the password here.  

Example of setting the output path (already shown in the code snippet above):

```javascript
deleteRequest.outputPath = "output.pdf";
```

Additional parameters are listed in the API reference.

## Best Practices for Removing Signatures from PDFs

- **Validate file existence** before sending the request to avoid unnecessary API calls.  
- **Use environment variables** for client credentials to keep them out of source control.  
- **Store the unsigned result in a separate folder** to preserve the original signed document.  
- **Handle errors gracefully** by catching exceptions and logging the error details.  
- **Test with different signature types** to ensure the delete operation works across all scenarios.

## Conclusion

Removing signatures from a signed PDF document becomes straightforward with the [GroupDocs.Signature Cloud SDK for Node.js](https://products.groupdocs.cloud/signature/nodejs/). The library handles authentication, storage access, and the delete operation in just a few lines of code, while the REST API offers the same capability via cURL. Remember to acquire a proper license for production use; pricing details are available on the product page and you can obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). With these tools, you can automate PDF signature removal in any Node.js workflow.

## FAQs

- **How does remove Signatures from Signed PDF document work with GroupDocs.Signature Cloud SDK for Node.js?**  
  The library authenticates using your client ID and secret, then calls the DeleteSignatures endpoint to strip all signatures from the specified PDF. See the [GroupDocs.Signature Cloud SDK for Node.js](https://products.groupdocs.cloud/signature/nodejs/) documentation for details.

- **Can I delete signatures from a PDF stored in GroupDocs cloud storage?**  
  Yes. Provide the storage path in the `FileInfo` object and the SDK will access the file directly. Refer to the [official documentation](https://docs.groupdocs.cloud/signature/) for storage handling.

- **What if I need to keep a copy of the original signed PDF?**  
  Specify a different `outputPath` in `DeleteSignaturesRequest` so the original file remains untouched while the new file contains no signatures.

- **Do I need a special license to use this functionality in production?**  
  A valid license is required for production use. You can obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/).

## Read More
- [How to Digitally Sign a Word Document Online](https://blog.groupdocs.cloud/signature/digitally-sign-a-word-document-online/)
- [Remove Signatures from Signed PDF Document using Python](https://blog.groupdocs.cloud/signature/remove-signatures-from-signed-pdf-document-using-python/)
- [Edit Signatures in Signed PDF Documents using Python](https://blog.groupdocs.cloud/signature/edit-signatures-in-signed-pdf-documents-using-python/)