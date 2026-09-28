---
title: "Create EML in Node.JS"
seoTitle: "Create EML in Node.JS"
description: "Learn how to create EML in Node.js with Aspose.3D Cloud SDK. This guide covers installation, a code example, cURL commands, and tips for email export."
date: Mon, 28 Sep 2026 20:57:01 +0000
lastmod: Mon, 28 Sep 2026 20:57:01 +0000
draft: false
url: /3d/create-eml-in-nodejs/
author: "Muhammad Mustafa"
summary: "Learn to create EML in Node.js with Aspose.3D Cloud SDK. This guide shows how to install the library, set API credentials, build an EmailDto with an attachment, and generate an EML file. It also provides cURL equivalents and best practices for email export."
tags: ['nodejs email', 'eml generation', 'email export']
categories: ["Aspose.3D Cloud Product Family"]
showtoc: true
cover:
   image: images/create-eml-in-nodejs.jpg
   alt: "Create EML in Node.JS"
   caption: "Create EML in Node.JS"
steps:
  - "Step 1: Install the Aspose.3D Cloud SDK for Node.js and configure your API credentials."
  - "Step 2: Initialize the EmailApi client with the configuration object."
  - "Step 3: Build an EmailDto object, set sender, recipient, subject, body, and add an attachment."
  - "Step 4: Call the create method with the 'Eml' format to generate the email file."
  - "Step 5: Write the returned buffer to a .eml file on disk."
faqs:
  - q: "How do I create EML in Node.js using Aspose.3D Cloud SDK?"
    a: "Use the EmailApi class to build an EmailDto, then call create with the 'Eml' format. See the full example in this guide."
  - q: "Can I generate an EML file without writing code?"
    a: "Yes, you can achieve the same result with REST calls. The cURL section demonstrates how to export email to EML in Node.js via the API."
  - q: "What options can I customize when creating an EML file?"
    a: "You can set isBodyHtml, add multiple attachments, and define custom headers. Refer to the Configuration / Options section for details."
  - q: "Is a license required for production use?"
    a: "A valid Aspose.3D Cloud SDK license is required. You can obtain a temporary license at the [temporary license page](https://purchase.aspose.com/temporary-license/)."
---

Creating an [EML](https://docs.fileformat.com/email/eml/) file programmatically is essential when you need to archive emails, integrate with legacy systems, or automate notifications. [Aspose.3D Cloud SDK for Node.js](https://products.aspose.cloud/3d/nodejs/) provides a straightforward library that handles the heavy lifting, letting you focus on business logic. In this tutorial you will learn how to create EML in Node.js, see a complete working example, explore equivalent cURL commands, and discover best practices for reliable email export.

## How to Create EML in Node.js - Step by Step

1. **Install the SDK and configure API keys**: Use npm to add the package and create a `Configuration` object with your client credentials.  
   ```javascript
   const { Configuration } = require('@asposecloud/email');

   const config = new Configuration({
       clientId: 'YOUR_CLIENT_ID',
       clientSecret: 'YOUR_CLIENT_SECRET'
   });
   ```
   

2. **Initialize the EmailApi client**: Pass the configuration to the `EmailApi` constructor.  
   ```javascript
   const { EmailApi } = require('@asposecloud/email');
   const emailApi = new EmailApi(config);
   ```
   
   For more details, see the [EmailApi reference](https://reference.aspose.cloud/3d/).

3. **Create an EmailDto with sender, recipient, subject, body, and attachment**: The DTO holds all email components.  
   ```javascript
   const { EmailDto, MailAddress } = require('@asposecloud/email');

   const email = new EmailDto({
       from: new MailAddress({ address: 'sender@example.com', displayName: 'Sender Name' }),
       to: [new MailAddress({ address: 'recipient@example.com', displayName: 'Recipient Name' })],
       subject: 'Test Email generated via Aspose.Email Cloud SDK',
       body: 'Hello,\n\nThis is a test email created with Aspose.Email Cloud SDK for Node.js.\n\nBest regards,\nNode.js',
       isBodyHtml: false,
       attachments: [{
           name: 'sample.txt',
           content: Buffer.from('Sample attachment content').toString('base64')
       }]
   });
   ```
   

4. **Generate the EML file**: Call `create` with the format `'Eml'`. The method returns a binary buffer.  
   ```javascript
   const emlBuffer = await emailApi.create(email, 'Eml');
   ```
   

5. **Write the buffer to disk**: Use Node's `fs` module to save the file.  
   ```javascript
   const fs = require('fs');
   const path = require('path');

   const outputFile = path.resolve(__dirname, 'output.eml');
   fs.writeFileSync(outputFile, emlBuffer);
   console.log(`EML file successfully created at: ${outputFile}`);
   ```
   

## Complete Code Example: Create EML File with Node.js

The following code demonstrates the entire workflow from configuration to file creation.

```javascript
const fs = require('fs');
const path = require('path');
const {
    EmailApi,
    EmailDto,
    MailAddress,
    Configuration
} = require('@asposecloud/email');

// -----------------------------------------------------
// 1. Install the SDK and configure API keys
// -----------------------------------------------------
const clientId = 'YOUR_CLIENT_ID';
const clientSecret = 'YOUR_CLIENT_SECRET';

const config = new Configuration({
    clientId: clientId,
    clientSecret: clientSecret,
    // baseUrl is optional; default is https://api.aspose.cloud
});

const emailApi = new EmailApi(config);

// -----------------------------------------------------
// 2. Initialize Email object and set properties
// -----------------------------------------------------
const email = new EmailDto({
    from: new MailAddress({
        address: 'sender@example.com',
        displayName: 'Sender Name'
    }),
    to: [
        new MailAddress({
            address: 'recipient@example.com',
            displayName: 'Recipient Name'
        })
    ],
    subject: 'Test Email generated via Aspose.Email Cloud SDK',
    body: 'Hello,\n\nThis is a test email created with Aspose.Email Cloud SDK for Node.js.\n\nBest regards,\nNode.js',
    isBodyHtml: false,
    // Optional: add a simple text attachment
    attachments: [
        {
            name: 'sample.txt',
            // Content must be Base64‑encoded
            content: Buffer.from('Sample attachment content').toString('base64')
        }
    ]
});

// -----------------------------------------------------
// 3. Generate EML file with Node.js
// -----------------------------------------------------
(async () => {
    try {
        // 'Eml' tells the service to return the message in .eml format
        const emlBuffer = await emailApi.create(email, 'Eml');

        // Write the binary buffer to a file
        const outputFile = path.resolve(__dirname, 'output.eml');
        fs.writeFileSync(outputFile, emlBuffer);
        console.log(`EML file successfully created at: ${outputFile}`);
    } catch (error) {
        console.error('Failed to create EML:', error);
    }
})();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.aspose.cloud/3d/) or reach out to the [support team](https://forum.aspose.cloud/c/3d/29) for assistance.

## Generate EML via REST API with cURL

Below are the cURL commands that perform the same operation through the REST API.

1. **Obtain an access token**  
   ```bash
   curl -X POST "https://api.aspose.cloud/connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
   ```

2. **Create the email [JSON](https://docs.fileformat.com/web/json/) payload** (save as `email.json`)  
   ```json
   {
     "from": { "address": "sender@example.com", "displayName": "Sender Name" },
     "to": [{ "address": "recipient@example.com", "displayName": "Recipient Name" }],
     "subject": "Test Email generated via Aspose.Email Cloud SDK",
     "body": "Hello,\n\nThis is a test email created with Aspose.Email Cloud SDK for Node.js.\n\nBest regards,\nNode.js",
     "isBodyHtml": false,
     "attachments": [
       {
         "name": "sample.txt",
         "content": "U2FtcGxlIGF0dGFjaG1lbnQgY29udGVudA=="
       }
     ]
   }
   ```

3. **Request EML generation**  
   ```bash
   curl -X POST "https://api.aspose.cloud/email/create?format=Eml" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d @email.json --output output.eml
   ```

These commands let you generate an EML file without writing any Node.js code. For more details, see the [official API documentation](https://reference.aspose.cloud/3d/).

## Prerequisites and Setup for Aspose.3D Cloud SDK

To start using the SDK, you need Node.js (v12 or later) and an Aspose Cloud account.

```bash
npm install aspose3dcloud
```

You can also download the package directly from the [release page](https://releases.aspose.cloud/3d/nodejs/). After installation, create a free Aspose Cloud account, obtain your `clientId` and `clientSecret`, and keep them secure.

## Fine-Tuning Email Generation Options

The SDK exposes several properties you can adjust:

- **isBodyHtml** - Set to `true` if your email body contains [HTML](https://docs.fileformat.com/web/html/) markup.  
- **attachments** - Add multiple objects to the `attachments` array; each must include a `name` and Base64‑encoded `content`.  
- **customHeaders** - Although not shown in the sample, you can add a `customHeaders` map to include additional MIME headers.

Refer to the [EmailDto class reference](https://reference.aspose.cloud/3d/) for a full list of configurable fields.

## Best Practices for EML Generation

- **Validate email addresses** before sending them to the API to avoid runtime errors.  
- **Base64‑encode attachment content** to ensure binary data is transmitted correctly.  
- **Reuse the Configuration object** across multiple API calls to reduce overhead.  
- **Handle errors gracefully** by wrapping the `create` call in a `try/catch` block and logging the response.  
- **Store generated EML files securely**, especially if they contain sensitive information.

## Conclusion

Creating EML in Node.js becomes a simple, repeatable process with the [Aspose.3D Cloud SDK for Node.js](https://products.aspose.cloud/3d/nodejs/). By following the steps, code example, and best practices outlined above, you can reliably export emails to the EML format for archiving, compliance, or downstream processing. Remember to secure your API credentials and obtain a proper license for production use; you can explore pricing options or request a temporary license at the [temporary license page](https://purchase.aspose.com/temporary-license/). Happy coding!

## FAQs

**How do I create EML in Node.js using Aspose.3D Cloud SDK?**  
Use the EmailApi class to build an EmailDto, then call `create` with the `'Eml'` format. The complete example in this article shows the exact code.

**Can I generate an EML file without writing code?**  
Yes. The cURL section demonstrates how to call the REST API directly, which achieves the same result as the Node.js library.

**What options can I customize when creating an EML file?**  
You can toggle `isBodyHtml`, add multiple attachments, and define custom MIME headers. See the Configuration / Options section for details.

**Is a license required for production use?**  
A valid license is required for production deployments. Obtain a temporary license from the [temporary license page](https://purchase.aspose.com/temporary-license/) or purchase a full license through the Aspose store.

## Read More
- [Convert GLB to FBX in Node.js - Easy and Simple Conversion](https://blog.aspose.cloud/3d/glb-to-fbx-in-node.js/)
- [Import XML Data to PDF in C#](https://blog.aspose.cloud/3d/import-xml-data-to-pdf-in-csharp/)
- [3D to PDF Conversion in C#: a Complete Tutorial](https://blog.aspose.cloud/3d/3d-to-pdf-conversion-in-csharp-a-complete-tutorial/)