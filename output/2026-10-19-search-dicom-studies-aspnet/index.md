---
title: Search DICOM Studies with Aspose.Medical in .NET
seoTitle: Search DICOM Studies with Aspose.Medical in .NET
description: Search DICOM studies in .NET with Aspose.Medical's DICOMweb client (QIDO‑RS).
  This guide shows SDK setup, query creation, and reading study results efficiently.
date: Mon, 19 Oct 2026 10:36:49 +0000
draft: true
url: /medical/search-dicom-studies-aspnet/
author: Muzammil Khan
summary: This article demonstrates how to use Aspose.Medical's DICOMweb client to
  search for DICOM studies by patient name in a .NET application. You’ll see how to
  configure the client, build a QIDO‑RS query, and process the returned datasets.
tags: ['search dicom studies', 'dicomweb client', 'aspose medical', 'qido-rs', 'csharp', 'dicom query', 'medical imaging']
categories: ["Aspose.Medical Product Family"]
showtoc: true
cover:
  image: images/search-dicom-studies-aspnet.jpg
  alt: Search DICOM Studies with Aspose.Medical in .NET
  caption: Search DICOM Studies with Aspose.Medical in .NET
  hidden: false
steps:
- Install Aspose.Medical for .NET via NuGet.
- Create an HttpClient and configure DicomWebClientOptions with your DICOMweb base
  URI.
- Build DicomWebSearchOptions with a PatientName query parameter.
- Call Studies.SearchAsync, iterate the result stream, and read study metadata.
faqs:
- q: How do I install Aspose.Medical for .NET?
  a: Run `Install-Package Aspose.Medical` in the Package Manager Console or add the
    package via your IDE’s NuGet interface.
- q: Which NuGet package provides the DICOMweb client?
  a: The `Aspose.Medical` package contains the `Aspose.Medical.Dicom.Web` namespace
    that includes `DicomWebClient` and related types.
- q: How can I search studies by patient name?
  a: Create a `DicomWebSearchOptions` object with a `DicomWebQueryParameter` for the
    `PatientName` tag and pass it to `client.Studies.SearchAsync`.
- q: Can I limit the number of returned studies?
  a: Yes, set the `Limit` property on `DicomWebSearchOptions` to the maximum number
    of studies you want the server to return.
- q: What does the FuzzyMatching option do?
  a: When `FuzzyMatching` is true, the server performs a case‑insensitive, wildcard‑aware
    match, allowing patterns like "Doe*" to find all surnames starting with Doe.
- q: How do I extract patient name and study UID from the results?
  a: Each `Dataset` returned by the search stream exposes `GetValue<T>`; use `Tag.PatientName`
    and `Tag.StudyInstanceUID` to retrieve those values.
---

Search DICOM studies in .NET using Aspose.Medical's DICOMweb client (QIDO‑RS). This tutorial walks through installing the SDK, configuring a client, building a patient‑name query, and reading the returned study information.

## Key Takeaways
- The DICOMweb client lets you issue QIDO‑RS queries directly from .NET code.
- `DicomWebSearchOptions` defines matching parameters, fuzzy matching, and result limits.
- `DicomWebClientStream<Dataset>` provides an async enumerable for efficient result processing.
- Extracting tags such as `PatientName` and `StudyInstanceUID` is done via `Dataset.GetValue<T>`.
- No additional third‑party libraries are required beyond Aspose.Medical.

## Why This Feature Matters
Developers building radiology or health‑IT applications often need to locate studies without downloading whole images. QIDO‑RS offers a lightweight, REST‑ful way to query a PACS server for study metadata. Using Aspose.Medical’s DICOMweb client removes the need to craft raw HTTP requests and parse DICOM tags manually, speeding development and reducing bugs.

## Getting Started with Aspose.Medical
Before you can query a DICOMweb service, add the Aspose.Medical package to your .NET project:

```powershell
Install-Package Aspose.Medical
```

Reference the product page for additional details: [Aspose.Medical for .NET](https://products.aspose.com/medical/net/).

## How to Search DICOM Studies Using the DICOMweb Client
Below is a complete, self‑contained example that searches for studies whose patient name starts with "Doe". The code demonstrates client creation, query configuration, asynchronous search execution, and result extraction.

**The following example shows how to search DICOM studies by patient name using C# and Aspose.Medical.**

```csharp
using System.Net.Http;
using Aspose.Medical.Dicom;
using Aspose.Medical.Dicom.Web;

// 1. Create an HttpClient that will be reused for the lifetime of the application
HttpClient httpClient = new HttpClient();

// 2. Configure the DICOMweb client with the base URI of your PACS server
DicomWebClientOptions options = new DicomWebClientOptions
{
    BaseUri = new System.Uri("https://dicom.example.com/dicomweb")
};

// 3. Instantiate the DICOMweb client
DicomWebClient client = new DicomWebClient(httpClient, options);

// 4. Build search options – we look for patient names that start with "Doe"
DicomWebSearchOptions searchOptions = new DicomWebSearchOptions
{
    MatchingParameters =
    [
        new DicomWebQueryParameter("PatientName", "Doe*")
    ],
    FuzzyMatching = true,   // enable wildcard matching
    Limit = 10               // return at most 10 studies
};

// 5. Execute the QIDO‑RS search asynchronously
await using DicomWebClientStream<Dataset> results = await client.Studies.SearchAsync(searchOptions);

// 6. Iterate over the returned datasets and read desired tags
await foreach (Dataset study in results)
{
    string patientName = study.GetValue<string>(Aspose.Medical.Dicom.Tags.Tag.PatientName, 0);
    string studyUid = study.GetValue<string>(Aspose.Medical.Dicom.Tags.Tag.StudyInstanceUID, 0);
    System.Console.WriteLine($"Patient: {patientName}, Study UID: {studyUid}");
}
```

**Explanation of the code**
1. **HttpClient** – Reusing a single `HttpClient` instance follows best practices for connection management.
2. **DicomWebClientOptions** – The `BaseUri` points to the DICOMweb endpoint exposed by your PACS server.
3. **DicomWebClient** – This class abstracts the QIDO‑RS, WADO‑RS, and STOW‑RS services.
4. **DicomWebSearchOptions** – `MatchingParameters` holds one or more `DicomWebQueryParameter` objects; each maps a DICOM tag name to a search value. Setting `FuzzyMatching` to `true` enables wildcard behaviour, and `Limit` caps the result set.
5. **SearchAsync** – Returns a `DicomWebClientStream<Dataset>` which implements `IAsyncEnumerable<Dataset>`. This allows efficient streaming of potentially large result sets without loading everything into memory.
6. **Dataset.GetValue<T>** – Retrieves the first value (index 0) for a given tag. Here we extract the human‑readable patient name and the unique study identifier.

The example can be extended to iterate over all matching parameters, handle pagination, or fetch additional tags such as `StudyDate` or `Modality`.

## Conclusion
By leveraging Aspose.Medical's DICOMweb client, .NET developers can perform QIDO‑RS queries with just a few lines of code. The approach handles HTTP communication, query construction, and DICOM tag extraction, letting you focus on application logic such as displaying study lists or integrating with downstream image retrieval workflows.

## FAQs
1. **How do I install Aspose.Medical for .NET?**
   Run `Install-Package Aspose.Medical` in the Package Manager Console or add the package via your IDE’s NuGet UI.
2. **Which NuGet package provides the DICOMweb client?**
   The `Aspose.Medical` package contains the `Aspose.Medical.Dicom.Web` namespace with `DicomWebClient` and related types.
3. **How can I search studies by patient name?**
   Create a `DicomWebSearchOptions` object with a `DicomWebQueryParameter` for the `PatientName` tag and pass it to `client.Studies.SearchAsync`.
4. **Can I limit the number of returned studies?**
   Yes – set the `Limit` property on `DicomWebSearchOptions` to the maximum number of results you want.
5. **What does the FuzzyMatching option do?**
   When enabled, the server performs a case‑insensitive, wildcard‑aware match, allowing patterns like `Doe*`.
6. **How do I extract patient name and study UID from the results?**
   Use `Dataset.GetValue<string>(Tag.PatientName, 0)` and `Dataset.GetValue<string>(Tag.StudyInstanceUID, 0)` on each `Dataset` returned by the stream.

## Get a Free License and Explore More
Try Aspose.Medical risk‑free by requesting a temporary license:

[Get a Free License](https://purchase.aspose.com/temporary-license/)

Additional resources:
- [Documentation](https://docs.aspose.com/medical/net/)
- [API Reference](https://reference.aspose.com/medical/net/)
- [Free Online Apps](https://products.aspose.app/medical/family)

## Read More

- [Create DICOM File in C# with Aspose.Medical for .NET](https://blog.aspose.com/medical/create-dicom-file-in-csharp/)

