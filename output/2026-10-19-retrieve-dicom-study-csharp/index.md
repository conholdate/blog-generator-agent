---
title: Retrieve DICOM Study with Aspose.Medical in C#
seoTitle: Retrieve DICOM Study with Aspose.Medical in C#
description: Learn how to retrieve a complete DICOM study as Part‑10 files using Aspose.Medical's
  WADO‑RS client in C#. Step‑by‑step code and explanation included.
date: Mon, 19 Oct 2026 10:40:33 +0000
draft: true
url: /medical/retrieve-dicom-study-csharp/
author: Muzammil Khan
summary: This article shows how to download every instance of a DICOM study via WADO‑RS
  using Aspose.Medical for .NET. You’ll see the required NuGet package, client setup,
  and a full async example.
tags: ['csharp', 'aspose medical', 'dicom wado-rs', 'dicom study retrieval', 'dicom part10', 'aspose medical dicom', 'dicomwebclient']
categories: ["Aspose.Medical Product Family"]
showtoc: true
cover:
  image: images/retrieve-dicom-study-csharp.jpg
  alt: Retrieve DICOM Study with Aspose.Medical in C#
  caption: Retrieve DICOM Study with Aspose.Medical in C#
  hidden: false
steps:
- Install Aspose.Medical via NuGet.
- Create an HttpClient and configure DicomWebClientOptions.
- Instantiate DicomWebClient with the HttpClient and options.
- Call RetrieveStudyAsync with the study UID.
- Iterate the DicomWebClientStream to process each DICOM file.
faqs:
- q: What NuGet package is required to work with DICOM files in .NET?
  a: Install the Aspose.Medical package using the command `Install-Package Aspose.Medical`.
- q: Which class performs the WADO‑RS calls?
  a: '`Aspose.Medical.Dicom.Web.DicomWebClient` handles all WADO‑RS operations, including
    study retrieval.'
- q: How do I specify the DICOMweb service endpoint?
  a: Set the `BaseUri` property of `DicomWebClientOptions` to the URL of your DICOMweb
    server.
- q: What does `RetrieveStudyAsync` return?
  a: It returns a `DicomWebClientStream<DicomFile>` that streams each instance of
    the requested study as a DICOM Part‑10 file.
- q: Can I process the retrieved files one by one?
  a: Yes, you can enumerate the stream with `await foreach` and handle each `DicomFile`
    individually.
- q: Do I need to manage the HttpClient lifecycle myself?
  a: Pass your own `HttpClient` to the `DicomWebClient` constructor and dispose it
    when the client is no longer needed.
---

Retrieving a complete DICOM study via WADO‑RS is a common requirement for radiology PACS integrations. Using Aspose.Medical for .NET, you can download every instance of a study as standard DICOM Part‑10 files with just a few lines of C# code.

## Key Takeaways
- Aspose.Medical provides a high‑level `DicomWebClient` that abstracts the WADO‑RS protocol.
- The client returns a stream of `DicomFile` objects, allowing you to process studies instance‑by‑instance.
- All required configuration is done through `DicomWebClientOptions`, avoiding manual HTTP handling.
- The async API integrates cleanly with modern C# `await foreach` loops.
- No additional third‑party DICOM libraries are needed; the full workflow lives inside Aspose.Medical.

## Why Retrieve Complete DICOM Studies?
Clinicians and researchers often need every image slice of a study for analysis, reporting, or archiving. Downloading each instance individually is error‑prone and inefficient. A single WADO‑RS call that returns the whole study guarantees consistency, reduces network chatter, and simplifies downstream processing.

## Getting Started with Aspose.Medical
First, add the Aspose.Medical library to your project via NuGet:

```powershell
Install-Package Aspose.Medical
```

The library is documented at the official product page <https://products.aspose.com/medical/net/> and the API reference <https://reference.aspose.com/medical/net/>. Once the package is installed, you can start using the DICOM‑web client.

## Step‑by‑Step: Retrieve a Study via WADO‑RS
1. **Create an `HttpClient` and configure the DICOMweb endpoint.**
2. **Build `DicomWebClientOptions` with the service base URI.**
3. **Instantiate `DicomWebClient` using the `HttpClient` and options.**
4. **Call `RetrieveStudyAsync` with the study UID to obtain a stream of files.**
5. **Iterate the stream and handle each `DicomFile` as needed.**

The following example demonstrates the entire flow. It shows how to pull a study identified by its UID, enumerate the returned files, and write each instance UID to the console.

The example shows how to retrieve a complete DICOM study using Aspose.Medical's WADO‑RS client in C#.

```csharp
using System.Net.Http;
using Aspose.Medical.Dicom;
using Aspose.Medical.Dicom.Web;

HttpClient httpClient = new HttpClient();
DicomWebClientOptions options = new DicomWebClientOptions
{
    BaseUri = new System.Uri("https://dicom.example.com/dicomweb")
};
DicomWebClient client = new DicomWebClient(httpClient, options);

string studyUid = "1.2.840.113619.2.55.3.604688119";

// Retrieve the study as DICOM Part 10 files
await using DicomWebClientStream<DicomFile> files = await client.Studies.RetrieveStudyAsync(studyUid);

await foreach (DicomFile file in files)
{
    string sopInstanceUid = file.Dataset.GetValue<string>(
        Aspose.Medical.Dicom.Tags.Tag.SOPInstanceUID, 0);
    System.Console.WriteLine($"Retrieved instance: {sopInstanceUid}");
}
```

**Explanation of the code**
- `HttpClient` provides the underlying HTTP transport. Aspose.Medical does not create its own client, so you have full control over timeouts and headers.
- `DicomWebClientOptions` holds the base URI of the DICOMweb service. The client appends the required WADO‑RS paths automatically.
- `DicomWebClient` ties the transport and options together, exposing the `Studies` property which groups study‑level operations.
- `RetrieveStudyAsync` initiates a WADO‑RS request for the supplied `studyUid`. The method returns a `DicomWebClientStream<DicomFile>`, an async enumerable that yields each instance as a fully parsed `DicomFile`.
- Inside the `await foreach` loop, `file.Dataset.GetValue<string>(Tag.SOPInstanceUID, 0)` extracts the SOP Instance UID from the DICOM metadata, demonstrating how to access any tag you need.

Because the stream is async, the SDK downloads each file on demand, which is memory‑efficient for large studies containing hundreds of slices.

## Conclusion
Using Aspose.Medical's `DicomWebClient` you can retrieve an entire DICOM study with a single asynchronous call. The client abstracts WADO‑RS details, returns a convenient stream of `DicomFile` objects, and lets you work with each instance directly in C#. This approach simplifies PACS integration, improves performance, and reduces custom networking code.

## FAQs
1. **What NuGet package is required to work with DICOM files in .NET?**
   Install the Aspose.Medical package using the command `Install-Package Aspose.Medical`.
2. **Which class performs the WADO‑RS calls?**
   `Aspose.Medical.Dicom.Web.DicomWebClient` handles all WADO‑RS operations, including study retrieval.
3. **How do I specify the DICOMweb service endpoint?**
   Set the `BaseUri` property of `DicomWebClientOptions` to the URL of your DICOMweb server.
4. **What does `RetrieveStudyAsync` return?**
   It returns a `DicomWebClientStream<DicomFile>` that streams each instance of the requested study as a DICOM Part‑10 file.
5. **Can I process the retrieved files one by one?**
   Yes, you can enumerate the stream with `await foreach` and handle each `DicomFile` individually.
6. **Do I need to manage the HttpClient lifecycle myself?**
   Pass your own `HttpClient` to the `DicomWebClient` constructor and dispose it when the client is no longer needed.

## Get a Free License and Explore More
Start experimenting with Aspose.Medical today by requesting a temporary license: <https://purchase.aspose.com/temporary-license/>.

- Documentation: <https://docs.aspose.com/medical/net/>
- API Reference: <https://reference.aspose.com/medical/net/>
- Free online apps: <https://products.aspose.app/medical/family>

## Read More

- [Create DICOM File in C# with Aspose.Medical for .NET](https://blog.aspose.com/medical/create-dicom-file-in-csharp/)

