---
title: High-Performance DICOM Element Access with Memory<T> in .NET
seoTitle: High-Performance DICOM Element Access with Memory<T> in .NET
description: Discover how to use Aspose.Medical for .NET to read and modify DICOM
  element data with System.Memory<T>, enabling indexed access, Span iteration and
  fast copying to arrays for high‑performance processing.
date: Wed, 23 Sep 2026 05:15:17 +0000
draft: true
url: /medical/high-performance-dicom-memory/
author: Muzammil Khan
summary: In this tutorial you will learn how to open a DICOM file with Aspose.Medical,
  retrieve an element as a Memory‑backed collection, modify values using indexers,
  iterate the Span efficiently, and copy the data to an array for further processing.
tags: ['high-performance dicom element access with memoryt', 'adding updating and removing data from dicom files', 'fast dicom tag reading with memoryt in dotnet', 'high-performance dicom element extraction using memoryt in dotnet']
categories: ["Aspose.Medical Product Family"]
showtoc: true
cover:
  image: images/high-performance-dicom-memory.jpg
  alt: High-Performance DICOM Element Access with Memory<T> in .NET
  caption: High-Performance DICOM Element Access with Memory<T> in .NET
  hidden: false
steps:
- Install Aspose.Medical via NuGet.
- Open the DICOM file with DicomFile.Open.
- Retrieve the desired element using Dataset.Get<T>.
- Access and modify element values through the indexer or Span.
- Copy the element data to a separate array when needed.
faqs:
- q: What is System.Memory<T> and why does it improve DICOM processing?
  a: System.Memory<T> provides a lightweight, array‑like view of data that avoids
    copying; it lets you work directly on the underlying buffer, which significantly
    reduces allocation and improves throughput for large DICOM datasets.
- q: How do I read a DICOM tag using Aspose.Medical for .NET?
  a: Use DicomFile.Open to load the file, then call dicomFile.Dataset.Get<T>(Tag.<TagName>)
    to obtain a typed element such as DecimalString, which exposes its data via a
    Memory<T> property.
- q: Can I change an element’s value without creating a new object?
  a: Yes. The element’s indexer (e.g., spacing[0] = "0.5") writes directly into the
    underlying Memory<T>, updating the value in place without allocating a new collection.
- q: What is the best way to iterate all values of a multi‑valued DICOM element?
  a: Iterate the Span returned by Element.Data.Span – it provides fast, zero‑allocation
    enumeration of the values.
- q: When should I use CopyDataToArray instead of the Span?
  a: CopyDataToArray creates an independent array copy, which is useful when you need
    to pass the data to an API that expects a regular array or when you want to preserve
    the original values while modifying the copy.
---

Aspose.Medical now exposes DICOM element data as **System.Memory<T>**, letting .NET developers read, update, and copy values with minimal overhead. This guide shows how to unlock high‑performance access to DICOM tags using the new indexers, Span iteration, and the `CopyDataToArray` helper.

## Key Takeaways
- Memory<T> lets you work with DICOM element buffers without copying, boosting speed and reducing memory pressure.
- Indexers provide direct read/write access to individual values inside a multi‑valued element.
- The Span returned by `Element.Data.Span` enables fast, allocation‑free enumeration.
- `CopyDataToArray` gives you a safe, independent snapshot when you need a plain array.
- All of this is available out‑of‑the‑box with Aspose.Medical for .NET.

## Why This Feature Matters
High‑throughput medical imaging pipelines often need to inspect or adjust hundreds of DICOM tags per file. Traditional APIs return string arrays that incur allocations and copying, slowing down processing. By exposing the data as `Memory<T>`, Aspose.Medical allows you to manipulate tag values directly in memory, which is essential for large‑scale or real‑time scenarios.

## Getting Started with Aspose.Medical
First, add the library to your project via NuGet:
```
Install-Package Aspose.Medical
```
The product page is https://products.aspose.com/medical/net/ and the full documentation lives at https://docs.aspose.com/medical/net/. Once installed, you can start working with DICOM files.

## Accessing DICOM Element Data with Memory<T>
**The following example demonstrates how to open a DICOM file, retrieve the PixelSpacing element as a `DecimalString`, and use the new Memory<T> features to read, modify, and copy its values.**
```csharp
using Aspose.Medical.Dicom;
using Aspose.Medical.Dicom.Elements;
using Aspose.Medical.Dicom.Tags;

// 1. Open the DICOM file
DicomFile dicomFile = DicomFile.Open("sample.dcm");

// 2. Get the PixelSpacing element as a DecimalString
DecimalString spacing = dicomFile.Dataset.Get<DecimalString>(Tag.PixelSpacing);

// 3. Indexed access – read the first value and replace it
string firstValue = spacing[0];
spacing[0] = "0.5"; // updates the underlying memory directly

// 4. Iterate the Span for fast, allocation‑free enumeration
foreach (string value in spacing.Data.Span)
{
    // Process each value (e.g., log or convert)
}

// 5. Create an independent copy when needed
string[] copy = spacing.CopyDataToArray();
```
- **Step 1** loads the DICOM container.
- **Step 2** fetches the `PixelSpacing` tag; the generic `Get<T>` call returns a typed element that contains a `Memory<string>` named `Data`.
- **Step 3** shows how the indexer (`spacing[0]`) reads the first string value and how assigning a new string writes directly into the underlying buffer.
- **Step 4** accesses `spacing.Data.Span`, an `ReadOnlySpan<string>` that can be enumerated without allocating a new collection, ideal for tight loops.
- **Step 5** calls `CopyDataToArray()` to produce a regular `string[]` if an external API requires a classic array.

## Modifying and Copying Element Data Efficiently
**This snippet expands on the previous example by demonstrating bulk updates and how to safely extract a copy for later use.**
```csharp
// Replace all spacing values with a uniform distance
for (int i = 0; i < spacing.Data.Length; i++)
{
    spacing[i] = "0.5"; // writes in‑place for each index
}

// Obtain a snapshot after modifications
string[] snapshot = spacing.CopyDataToArray();
```
- The `for` loop uses the element’s `Length` property to iterate efficiently, updating each entry via the indexer.
- After the bulk change, `CopyDataToArray` captures the current state, allowing you to pass the data to other components without affecting the live memory view.

## Conclusion
Aspose.Medical’s Memory<T> exposure transforms DICOM element handling from a copy‑heavy approach to a high‑performance, low‑allocation workflow. By leveraging indexers, Span enumeration, and the `CopyDataToArray` method, you can read, modify, and export tag values efficiently—crucial for demanding medical imaging applications.

## FAQs
1. **What is System.Memory<T> and why does it improve DICOM processing?**
   System.Memory<T> provides a lightweight, array‑like view of data that avoids copying; it lets you work directly on the underlying buffer, which significantly reduces allocation and improves throughput for large DICOM datasets.

2. **How do I read a DICOM tag using Aspose.Medical for .NET?**
   Use `DicomFile.Open` to load the file, then call `dicomFile.Dataset.Get<T>(Tag.<TagName>)` to obtain a typed element such as `DecimalString`, which exposes its data via a `Memory<T>` property.

3. **Can I change an element’s value without creating a new object?**
   Yes. The element’s indexer (e.g., `spacing[0] = "0.5"`) writes directly into the underlying `Memory<T>`, updating the value in place without allocating a new collection.

4. **What is the best way to iterate all values of a multi‑valued DICOM element?**
   Iterate the `Span` returned by `Element.Data.Span` – it provides fast, zero‑allocation enumeration of the values.

5. **When should I use `CopyDataToArray` instead of the Span?**
   `CopyDataToArray` creates an independent array copy, which is useful when you need to pass the data to an API that expects a regular array or when you want to preserve the original values while modifying the copy.

## Get a Free License and Explore More
Start experimenting with Aspose.Medical without cost by obtaining a temporary license at https://purchase.aspose.com/temporary-license/.

- Documentation: https://docs.aspose.com/medical/net/
- API Reference: https://reference.aspose.com/medical/net/
- Free Online Apps: https://products.aspose.app/medical/family
