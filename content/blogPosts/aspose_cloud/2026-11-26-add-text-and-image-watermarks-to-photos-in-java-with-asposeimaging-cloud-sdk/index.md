---
title: "Add Text and Image Watermarks to Photos in Java with Aspose.Imaging Cloud SDK"
seoTitle: "Add Text and Image Watermarks to Photos in Java with Aspose.Imaging Cloud SDK"
description: "Add text and image watermarks to photos with Aspose.Imaging Cloud SDK for Java. Follow step-by-step code, setup tips, and cURL commands to protect your images."
date: Thu, 26 Nov 2026 05:01:47 +0000
lastmod: Thu, 26 Nov 2026 05:01:47 +0000
draft: false
url: /imaging/add-text-and-image-watermarks-to-photos-in-java-with-asposeimaging-cloud-sdk/
author: "Muhammad Mustafa"
summary: "Learn to add text and image watermarks to photos with Aspose.Imaging Cloud SDK for Java. The guide covers prerequisites, Maven installation, a detailed code walkthrough, a full example, and equivalent cURL REST calls, so you can protect images quickly."
tags: ['java watermarking', 'image watermark', 'cloud image processing']
categories: ["Aspose.Imaging Cloud Product Family"]
showtoc: true
cover:
   image: images/add-text-and-image-watermarks-to-photos-in-java-with-asposeimaging-cloud-sdk.jpg
   alt: "Add Text and Image Watermarks to Photos in Java with Aspose.Imaging Cloud SDK"
   caption: "Add Text and Image Watermarks to Photos in Java with Aspose.Imaging Cloud SDK"
steps:
  - "Step 1: Install the Maven dependency and obtain cloud credentials"
  - "Step 2: Initialize the ImagingApi client"
  - "Step 3: Apply a text watermark to the source image"
  - "Step 4: Apply an image watermark to the same source image"
  - "Step 5: Save the resulting files locally"
faqs:
  - q: "How can I add text and image Watermarks to photos in Java with Aspose.Imaging cloud sdk?"
    a: "Use the ImagingApi class from [Aspose.Imaging Cloud SDK for Java](https://products.aspose.cloud/imaging/java/). The SDK lets you call putImageWatermarkText and putImageWatermarkImage methods to embed watermarks programmatically."
  - q: "Do I need an Aspose Cloud account to use the watermark features?"
    a: "Yes, you must have a valid Aspose Cloud account. Create a clientId and clientSecret in the Aspose Cloud console and use them when constructing the ImagingApi instance."
  - q: "Can I control the transparency and rotation of the watermark?"
    a: "Both putImageWatermarkText and putImageWatermarkImage accept parameters for transparency and rotationAngle, allowing you to fine‑tune the appearance of the watermark."
  - q: "Is there a way to test the code without a full project setup?"
    a: "You can run the provided example in a simple Java class after adding the Maven dependency and setting your credentials. For quick testing, refer to the [official documentation](https://docs.aspose.cloud/imaging/)."
---

Adding watermarks to images is a common requirement when you need to protect visual assets or brand content. [Aspose.Imaging Cloud SDK for Java](https://products.aspose.cloud/imaging/java/) provides a powerful library that simplifies watermark operations on the server side. In this guide you will learn how to add text and image Watermarks to photos in Java with Aspose.Imaging cloud sdk, covering setup, code walkthrough, a complete example, and equivalent REST calls.

## Setting Up Aspose.Imaging Cloud SDK for Java

Before you start, make sure you have the following:

- Java 8 or higher installed.
- Maven or Gradle for dependency management.
- An Aspose Cloud account with **clientId** and **clientSecret**.

Add the SDK to your Maven project:

```xml
<dependency>
    <groupId>com.aspose</groupId>
    <artifactId>aspose-imaging-cloud</artifactId>
    <version>25.4</version>
</dependency>
```

You can also download the library directly from the [release page](https://releases.aspose.cloud/imaging/java/). After adding the dependency, obtain your cloud credentials from the Aspose Cloud console and keep them handy for the next steps.

## Adding Text and Image Watermarks to Photos in Java with Aspose.Imaging Cloud SDK

The following steps demonstrate how to **add text and image Watermarks to photos in Java with Aspose.Imaging cloud sdk** using the ImagingApi class. Each step extracts a small portion of the full program for clarity.

### Step 1: Initialize the Imaging API Client
Create an instance of `ImagingApi` with your client credentials.

```java
String clientId = "clientId";
String clientSecret = "clientSecret";
ImagingApi api = new ImagingApi(clientId, clientSecret);
```

The `ImagingApi` class is documented in the [API reference](https://reference.aspose.cloud/imaging/).

### Step 2: Add a Text Watermark
Specify the watermark text, font, color, and other options, then call `putImageWatermarkText`.

```java
String inputImage = "input.jpg";
String outputTextWatermarked = "output_text_watermark.jpg";
String watermarkText = "Sample Watermark";
String fontFamily = "Arial";
Integer fontSize = 24;
String fontStyle = "Bold";
String textColor = "FF0000";
Double transparency = 0.5;
Double rotationAngle = 0.0;
Boolean background = false;
Boolean border = false;

byte[] textResult = api.putImageWatermarkText(
        inputImage,
        null,
        null,
        null,
        outputTextWatermarked,
        watermarkText,
        fontFamily,
        fontSize,
        fontStyle,
        textColor,
        transparency,
        rotationAngle,
        background,
        border
);
Files.write(Paths.get(outputTextWatermarked), textResult);
```

### Step 3: Add an Image Watermark
Provide the watermark image and configure its transparency and scaling.

```java
String watermarkImage = "logo.png";
String outputImageWatermarked = "output_image_watermark.jpg";
Double imgTransparency = 0.3;
Double imgRotationAngle = 0.0;
Boolean scale = true;
Boolean imgBackground = false;
Boolean imgBorder = false;

byte[] imageResult = api.putImageWatermarkImage(
        inputImage,
        null,
        null,
        null,
        outputImageWatermarked,
        watermarkImage,
        imgTransparency,
        imgRotationAngle,
        scale,
        imgBackground,
        imgBorder
);
Files.write(Paths.get(outputImageWatermarked), imageResult);
```

### Step 4: Verify the Output
After the two calls, you will have `output_text_watermark.jpg` and `output_image_watermark.jpg` saved locally. These files contain the applied watermarks and can be used directly in your application.

## Complete Code Example: Watermarking Photos with Aspose.Imaging Cloud SDK

The following code demonstrates the complete workflow from initialization to saving both watermarked images.

```java
import com.aspose.imaging.cloud.sdk.api.ImagingApi;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class AddWatermarkExample {
    public static void main(String[] args) {
        String clientId = "clientId";
        String clientSecret = "clientSecret";
        ImagingApi api = new ImagingApi(clientId, clientSecret);
        try {
            // Add text watermark
            String inputImage = "input.jpg";
            String outputTextWatermarked = "output_text_watermark.jpg";
            String watermarkText = "Sample Watermark";
            String fontFamily = "Arial";
            Integer fontSize = 24;
            String fontStyle = "Bold";
            String textColor = "FF0000";
            Double transparency = 0.5;
            Double rotationAngle = 0.0;
            Boolean background = false;
            Boolean border = false;

            byte[] textResult = api.putImageWatermarkText(
                    inputImage,
                    null,
                    null,
                    null,
                    outputTextWatermarked,
                    watermarkText,
                    fontFamily,
                    fontSize,
                    fontStyle,
                    textColor,
                    transparency,
                    rotationAngle,
                    background,
                    border
            );
            Files.write(Paths.get(outputTextWatermarked), textResult);

            // Add image watermark
            String watermarkImage = "logo.png";
            String outputImageWatermarked = "output_image_watermark.jpg";
            Double imgTransparency = 0.3;
            Double imgRotationAngle = 0.0;
            Boolean scale = true;
            Boolean imgBackground = false;
            Boolean imgBorder = false;

            byte[] imageResult = api.putImageWatermarkImage(
                    inputImage,
                    null,
                    null,
                    null,
                    outputImageWatermarked,
                    watermarkImage,
                    imgTransparency,
                    imgRotationAngle,
                    scale,
                    imgBackground,
                    imgBorder
            );
            Files.write(Paths.get(outputImageWatermarked), imageResult);
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            // No explicit resource cleanup required for ImagingApi
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.aspose.cloud/imaging/) or reach out to the [support team](https://forum.aspose.cloud/c/imaging/10) for assistance.

## Watermark Operations via REST API Using cURL

If you prefer a pure REST approach, the same operations can be performed with cURL commands.

### 1. Authenticate and Get an Access Token
```bash
curl -X POST "https://api.aspose.cloud/connect/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```
The response contains an `access_token` you will use in subsequent calls.

### 2. Upload the Source Image
```bash
curl -X PUT "https://api.aspose.cloud/v3.0/imaging/input.jpg" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: image/jpeg" \
     --data-binary "@input.jpg"
```

### 3. Apply a Text Watermark
```bash
curl -X POST "https://api.aspose.cloud/v3.0/imaging/input.jpg/watermark/text" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "Sample Watermark",
           "fontFamily": "Arial",
           "fontSize": 24,
           "fontStyle": "Bold",
           "color": "FF0000",
           "transparency": 0.5,
           "rotationAngle": 0,
           "background": false,
           "border": false,
           "outputPath": "output_text_watermark.jpg"
         }'
```

### 4. Apply an Image Watermark
```bash
curl -X POST "https://api.aspose.cloud/v3.0/imaging/input.jpg/watermark/image" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "imagePath": "logo.png",
           "transparency": 0.3,
           "rotationAngle": 0,
           "scale": true,
           "background": false,
           "border": false,
           "outputPath": "output_image_watermark.jpg"
         }'
```

### 5. Download the Watermarked Files
```bash
curl -X GET "https://api.aspose.cloud/v3.0/imaging/output_text_watermark.jpg" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o "output_text_watermark.jpg"

curl -X GET "https://api.aspose.cloud/v3.0/imaging/output_image_watermark.jpg" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o "output_image_watermark.jpg"
```

For more details on request bodies and additional parameters, see the [official API documentation](https://docs.aspose.cloud/imaging/).

## Key Takeaways

In this article we showed how to **add text and image Watermarks to photos in Java with Aspose.Imaging cloud sdk** using both the Java library and direct REST calls. The SDK handles authentication, file upload, and watermark rendering with just a few method calls, while the cURL examples give you flexibility for scripting or integration with other platforms. Remember to secure your client credentials and obtain a proper license for production use; you can acquire a temporary license from the [temporary license page](https://purchase.aspose.com/temporary-license/). With the code and API patterns in hand, you can now protect your images across any Java‑based backend.

## FAQs

- **How can I add text and image Watermarks to photos in Java with Aspose.Imaging cloud sdk?**  
  Use the `putImageWatermarkText` and `putImageWatermarkImage` methods of the `ImagingApi` class provided by [Aspose.Imaging Cloud SDK for Java](https://products.aspose.cloud/imaging/java/). The methods accept parameters for text, font, color, transparency, rotation, and more.

- **Do I need to upload the source image before applying a watermark via the API?**  
  Yes. The image must be stored in Aspose Cloud storage first. You can upload it with a simple PUT request as shown in the cURL section.

- **Can I change the watermark opacity and rotation?**  
  Both the text and image watermark methods include `transparency` and `rotationAngle` parameters, giving you full control over the visual appearance.

- **Where can I find more examples and detailed parameter descriptions?**  
  The [official documentation](https://docs.aspose.cloud/imaging/) provides extensive guides, and the [API reference](https://reference.aspose.cloud/imaging/) lists all available methods and their signatures.

## Further Reading
- [DCM to JPG in Java. DICOM Images Converter. DICOMViewer](https://blog.aspose.cloud/imaging/convert-dcm-to-jpg-in-java/)
- [Batch Resize Images in Java with Aspose.Imaging Cloud SDK - High‑Performance Bulk Processing](https://blog.aspose.cloud/imaging/batch-resize-images-in-java-with-asposeimaging-cloud-sdk-highperformance-bulk-processing/)
- [Convert PSD to PDF with .NET REST API - Photoshop to PDF](https://blog.aspose.cloud/imaging/convert-psd-to-pdf-in-csharp/)