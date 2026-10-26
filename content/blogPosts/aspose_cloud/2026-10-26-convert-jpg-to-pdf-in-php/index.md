---
title: "Convert JPG to PDF in PHP"
seoTitle: "Convert JPG to PDF in PHP"
description: "Learn how to convert JPG to PDF in PHP using Aspose.Words Cloud SDK. This guide covers setup, code walkthrough, cURL API and configuration tips."
date: Mon, 26 Oct 2026 14:02:32 +0000
lastmod: Mon, 26 Oct 2026 14:02:32 +0000
draft: false
url: /words/convert-jpg-to-pdf-in-php/
author: "Muhammad Mustafa"
summary: "Discover how PHP developers can convert JPG images to PDF using Aspose.Words Cloud SDK for PHP. The guide walks through prerequisites, Composer installation, a step-by-step code walkthrough, a full example, cURL REST calls, and key conversion settings like DPI and image quality."
tags: ['php image to pdf', 'jpeg to pdf conversion', 'pdf performance optimization']
categories: ["Aspose.Words Cloud Product Family"]
showtoc: true
cover:
   image: images/convert-jpg-to-pdf-in-php.jpg
   alt: "Convert JPG to PDF in PHP"
   caption: "Convert JPG to PDF in PHP"
steps:
  - "Step 1: Install the SDK via Composer"
  - "Step 2: Configure your Aspose Cloud credentials"
  - "Step 3: Load the JPG image"
  - "Step 4: Set conversion options"
  - "Step 5: Execute conversion and save PDF"
faqs:
  - q: "How do I convert JPG to PDF in PHP using Aspose?"
    a: "Use the Aspose.Words Cloud SDK for PHP. After configuring your client ID and secret, create a ConvertDocumentRequest with the JPG stream and target format \"pdf\". The SDK returns binary PDF data you can write to a file."
  - q: "Can I adjust image quality during JPG to PDF conversion?"
    a: "Yes. The ConvertOptions object lets you set ImageQuality (0‑100) and DPI values. See the [API reference](https://reference.aspose.cloud/words/) for full details."
  - q: "Is it possible to batch convert many JPG files to PDF?"
    a: "You can loop over a collection of JPG paths, reuse the same WordsApi instance, and invoke convertDocument for each file. This approach works well for batch processing."
  - q: "Do I need a license to use the SDK in production?"
    a: "A temporary license is available at the [temporary license page](https://purchase.aspose.com/temporary-license/). For production you should purchase a full license from the Aspose store."
---

Converting [JPG](https://docs.fileformat.com/image/jpg/) images to [PDF](https://docs.fileformat.com/pdf) documents programmatically is a frequent requirement for PHP developers building reporting or archival features. [Aspose.Words Cloud SDK for PHP](https://products.aspose.cloud/words/php/) enables you to convert JPG to PDF in PHP with just a few lines of code. In this guide you will see a step‑by‑step walkthrough, a complete working example, and cURL commands for the REST API. You will also learn how to fine‑tune DPI and image quality for optimal results.

## Setting Up Aspose.Words Cloud SDK for PHP

Before you start, make sure you have:

- PHP 7.4 or higher
- Composer installed
- An Aspose Cloud account with **Client Id** and **Client Secret**
- Network access to `https://api.aspose.cloud`

Install the SDK via Composer:

```bash
composer require aspose-cloud/aspose-words-cloud
```

Download the latest package from the official release page: [Aspose.Words Cloud SDK for PHP Download](https://releases.aspose.cloud/words/php/).

Now configure the SDK with your credentials:

```php
require __DIR__ . '/vendor/autoload.php';

use Aspose\Words\Configuration;

$config = new Configuration();
$config->setClientId('YOUR_CLIENT_ID');
$config->setClientSecret('YOUR_CLIENT_SECRET');
$config->setHost('https://api.aspose.cloud');
```

With the configuration ready, you can create a `WordsApi` instance and start converting.

## JPG to PDF Conversion in PHP: Step-by-Step Walkthrough

### Step 1: Load the Source Document

Open the JPG file as a stream so large images are handled efficiently.

```php
$inputJpgPath  = __DIR__ . '/sample.jpg';   // source JPG
$jpgStream = fopen($inputJpgPath, 'rb');
```

### Step 2: Configure Conversion Options

Set the desired DPI and image quality. These settings directly affect the output PDF size and clarity, which is important when you convert JPG to PDF in PHP.

```php
use Aspose\Words\Model\ConvertOptions;

$convertOptions = new ConvertOptions();
$convertOptions->setDpiX(300);   // horizontal DPI
$convertOptions->setDpiY(300);   // vertical DPI
$convertOptions->setImageQuality(80); // 0‑100
```

### Step 3: Create the Convert Request

Prepare the request object with the input stream, target format, and options.

```php
use Aspose\Words\Model\Requests\ConvertDocumentRequest;

$request = new ConvertDocumentRequest(
    $jpgStream,          // Input file stream
    'pdf',               // Target format
    null,                // outPath – null to receive binary response
    null,                // storage – default
    null,                // folder – default
    $convertOptions      // conversion options
);
```

### Step 4: Execute Conversion and Save PDF

Call the API, receive binary PDF data, and write it to a file.

```php
use Aspose\Words\WordsApi;

$wordsApi = new WordsApi($config);

try {
    $pdfBinary = $wordsApi->convertDocument($request);
    $outputPdfPath = __DIR__ . '/result.pdf';
    $pdfHandle = fopen($outputPdfPath, 'wb');
    fwrite($pdfHandle, $pdfBinary);
    fclose($pdfHandle);
    echo "Conversion successful: {$outputPdfPath}\n";
} catch (Exception $e) {
    echo 'Error during conversion: ', $e->getMessage(), "\n";
}
```

## Full Working Example for Converting JPG to PDF in PHP

The example below demonstrates the complete implementation from start to finish.

```php
<?php
require __DIR__ . '/vendor/autoload.php';

use Aspose\Words\Configuration;
use Aspose\Words\WordsApi;
use Aspose\Words\Model\ConvertOptions;
use Aspose\Words\Model\Requests\ConvertDocumentRequest;

$clientId = 'YOUR_CLIENT_ID';
$clientSecret = 'YOUR_CLIENT_SECRET';

$config = new Configuration();
$config->setClientId($clientId);
$config->setClientSecret($clientSecret);
$config->setHost('https://api.aspose.cloud');

$wordsApi = new WordsApi($config);

$inputJpgPath  = __DIR__ . '/sample.jpg';   // source JPG
$outputPdfPath = __DIR__ . '/result.pdf';   // destination PDF

// Open JPG as a stream to avoid loading whole file into memory for large images
$jpgStream = fopen($inputJpgPath, 'rb');

$convertOptions = new ConvertOptions();
$convertOptions->setDpiX(300);   // horizontal DPI
$convertOptions->setDpiY(300);   // vertical DPI
$convertOptions->setImageQuality(80); // optional, 0‑100

$request = new ConvertDocumentRequest(
    $jpgStream,          // Input file stream
    'pdf',               // Target format
    null,                // outPath – null to receive binary response
    null,                // storage – default
    null,                // folder – default
    $convertOptions      // conversion options
);

try {
    // API returns binary PDF data
    $pdfBinary = $wordsApi->convertDocument($request);
    // Write binary data to file efficiently
    $pdfHandle = fopen($outputPdfPath, 'wb');
    fwrite($pdfHandle, $pdfBinary);
    fclose($pdfHandle);
    echo "Conversion successful: {$outputPdfPath}\n";
} catch (Exception $e) {
    echo 'Error during conversion: ', $e->getMessage(), "\n";
}

// Cleanup
if (is_resource($jpgStream)) {
    fclose($jpgStream);
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.aspose.cloud/words/) or reach out to the [support team](https://forum.aspose.cloud/c/words/17) for assistance.

## Using cURL to Convert JPG Images to PDF Documents

If you prefer a direct REST call, the same conversion can be performed with cURL.

1. **Obtain an access token**

   ```bash
   curl -X POST "https://api.aspose.cloud/connect/token" \
        -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
   ```

2. **Upload the source JPG to storage**

   ```bash
   curl -X PUT "https://api.aspose.cloud/v4.0/words/storage/file/sample.jpg" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        --data-binary "@sample.jpg"
   ```

3. **Execute the conversion**

   ```bash
   curl -X GET "https://api.aspose.cloud/v4.0/words/sample.jpg?format=pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o result.pdf
   ```

4. **Download the resulting PDF (if not using `-o` above)**

   ```bash
   curl -X GET "https://api.aspose.cloud/v4.0/words/result.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o result.pdf
   ```

These commands illustrate the same workflow without writing any PHP code. For more details, see the [official API documentation](https://reference.aspose.cloud/words/).

## Fine-Tuning Conversion Settings for Optimal PDF Output

The SDK offers several options to control the appearance and size of the generated PDF.

- **DPI (Dots Per Inch)** - Higher DPI (e.g., 300) yields sharper output suitable for printing. Set with `setDpiX` and `setDpiY`.
- **ImageQuality** - Controls [JPEG](https://docs.fileformat.com/image/jpeg/) compression level (0‑100). Lower values reduce file size at the cost of visual fidelity.
- **Additional options** - The `ConvertOptions` class also supports `setPageSize`, `setPageOrientation`, and `setColorMode`. Refer to the [API reference](https://reference.aspose.cloud/words/) for the full list.

Example of setting DPI and quality (already shown in the walkthrough):

```php
$convertOptions = new ConvertOptions();
$convertOptions->setDpiX(300);
$convertOptions->setDpiY(300);
$convertOptions->setImageQuality(80);
```

## Key Takeaways

Using the **Aspose.Words Cloud SDK for PHP**, you can easily convert JPG to PDF in PHP without dealing with low‑level image processing. The SDK handles streaming, DPI, and image quality, allowing you to focus on business logic. Remember to secure your **Client Id** and **Client Secret**, and consider the temporary license for evaluation before purchasing a full license. Pricing details are available on the product page, and a temporary license can be obtained from the [temporary license page](https://purchase.aspose.com/temporary-license/). With the code and cURL examples provided, you're ready to integrate JPG to PDF conversion into any web or desktop PHP application.

## Questions You Might Have

- **What is the simplest way to convert JPG to PDF in PHP?**  
  The one‑liner shown in the complete example uses `ConvertDocumentRequest` with the target format set to `"pdf"`. This single call performs the entire conversion.

- **Can I convert multiple JPG files in a single request?**  
  The API processes one source file per request. To handle batches, loop over your file list and invoke the conversion for each image.

- **How do I control the output PDF size?**  
  Adjust `DpiX`, `DpiY`, and `ImageQuality` in `ConvertOptions`. Lower DPI and quality reduce file size, while higher values improve visual fidelity.

- **Is there a limit on the size of the JPG image I can convert?**  
  The SDK streams the input, so memory usage stays low. However, extremely large files may be subject to service limits; consult the [official documentation](https://docs.aspose.cloud/words/) for the exact thresholds.

## Further Reading
- [Convert PDF to TXT in Java](https://blog.aspose.cloud/words/convert-pdf-to-txt-in-java/)
- [Convert Word (DOC, DOCX) to JPG using Java](https://blog.aspose.cloud/words/convert-word-to-jpg-in-java/)
- [Convert PDF to HTML in Ruby. PDF to HTML online. pdftohtml](https://blog.aspose.cloud/words/convert-pdf-to-html-using-file-format-conversion-ruby-library/)