---
title: Count Messages in TGZ Files with TgzReader.GetItemsCount
seoTitle: Count Messages in TGZ Files with TgzReader.GetItemsCount – Aspose.Email
  for .NET
description: Learn how to count messages, contacts and other items inside a TGZ archive
  using Aspose.Email for .NET and the TgzReader.GetItemsCount method.
date: Wed, 30 Sep 2026 11:15:11 +0000
draft: true
url: /email/count-messages-tgz-getitemscount/
author: Muzammil Khan
summary: This tutorial shows .NET developers how to use Aspose.Email's TgzReader to
  retrieve the number of messages, contacts or other items stored in a TGZ archive.
  It covers installation, API basics, step‑by‑step code, error handling and best practices.
tags: ['count messages in tgz files with tgzreadergetitemscount', 'read tgz archive item count in dotnet', 'get contacts count from tgz archive in dotnet', 'how to count emails in a tgz file using dotnet']
categories: ["Aspose.Email Product Family"]
showtoc: true
cover:
  image: images/count-messages-tgz-getitemscount.jpg
  alt: Count Messages in TGZ Files with TgzReader.GetItemsCount
  caption: Count Messages in TGZ Files with TgzReader.GetItemsCount
  hidden: false
steps:
- Install Aspose.Email for .NET via NuGet.
- Create a TgzReader instance for the TGZ file.
- Call GetItemsCount(ItemType.Message) to obtain the message count.
- Call GetItemsCount(ItemType.Contact) to obtain the contact count.
- Use the retrieved counts in your application logic.
faqs:
- q: What file format does TgzReader support?
  a: TgzReader works with TGZ (tar‑gzip) archives that contain Aspose.Email items
    such as messages, contacts, calendar items or tasks.
- q: Do I need to extract the archive before counting items?
  a: No. GetItemsCount reads the archive metadata directly, so you can obtain counts
    without extracting any files.
- q: Can I count other item types besides messages and contacts?
  a: Yes. The ItemType enum includes Calendar, Task, and other supported entities,
    and you can pass any of them to GetItemsCount.
- q: What happens if the TGZ file is corrupted?
  a: TgzReader throws an Aspose.Email.Storage.Zimbra.ZimbraException. Catch the exception
    to handle corrupted archives gracefully.
- q: Is the TgzReader class thread‑safe?
  a: TgzReader is not thread‑safe; create a separate instance per thread or synchronize
    access if you share one.
- q: Do I need to dispose of TgzReader manually?
  a: Yes. Use a using statement or call Dispose to release file handles once you are
    finished.
---

Developers often need to process large TGZ archives that contain dozens or hundreds of email messages and contacts. When the only goal is to know how many items are present, extracting the archive is wasteful. **Count messages in TGZ files with TgzReader.GetItemsCount** lets you retrieve those numbers instantly, allowing you to make decisions about further processing, UI display, or resource allocation.

## Key Takeaways
- `TgzReader.GetItemsCount` returns the exact count of a specified `ItemType` without extracting the archive.
- The method works for messages, contacts, calendars, tasks and any future item types supported by Aspose.Email.
- Proper disposal of `TgzReader` prevents file‑handle leaks and ensures thread‑safety.
- Handling `ZimbraException` enables graceful recovery from corrupt TGZ files.
- The API integrates seamlessly with standard .NET `using` patterns and NuGet package management.

## Why This Feature Matters
Knowing the number of messages or contacts inside a TGZ file before you start a time‑consuming operation helps you allocate memory, display progress bars, or decide whether to abort early. In large enterprise migrations, a quick count can validate that an export completed correctly. The ability to retrieve counts directly from the archive also reduces I/O overhead, which is crucial for cloud‑based services where every read operation incurs cost.

## Getting Started with Aspose.Email
Aspose.Email for .NET provides a rich set of classes for working with email formats, archives and messaging stores. Install the library from NuGet:

```powershell
Install-Package Aspose.Email
```

The package includes the `Aspose.Email.Storage.Zimbra` namespace where `TgzReader` and `ItemType` live. For deeper documentation, visit the [Aspose.Email product page](https://products.aspose.com/email/net/), the [official docs](https://docs.aspose.com/email/net/), or the [API reference](https://reference.aspose.com/email/net/).

## How to Count Items in a TGZ Archive
Below is a complete, step‑by‑step example that demonstrates how to count email messages and contacts stored in a TGZ archive.

### 1. Prepare the Project
Create a new .NET console application or add the code to an existing project. Ensure the `Aspose.Email` NuGet package is referenced.

### 2. Import Required Namespaces
Add the following `using` directives at the top of your C# file:

```csharp
using Aspose.Email.Storage.Zimbra;
```

### 3. Open the TGZ Archive with `TgzReader`
Instantiate `TgzReader` by supplying the path to your TGZ file. The class implements `IDisposable`, so wrap it in a `using` block to guarantee proper cleanup.

```csharp
var fileName = "xhy.tgz";
using (var reader = new TgzReader(fileName))
{
    // Step 4 and 5 are performed inside this block.
}
```

### 4. Retrieve the Message Count
Call `GetItemsCount` with `ItemType.Message`. The method returns an `int` representing the total number of email messages inside the archive.

```csharp
int numberOfMessages = reader.GetItemsCount(ItemType.Message);
```

### 5. Retrieve the Contact Count
Similarly, request the contact count by passing `ItemType.Contact`.

```csharp
int numberOfContacts = reader.GetItemsCount(ItemType.Contact);
```

### 6. Use the Counts
At this point you have two integer values. You can log them, display them in a UI, or drive conditional logic.

```csharp
Console.WriteLine($"Messages: {numberOfMessages}");
Console.WriteLine($"Contacts: {numberOfContacts}");
```

### 7. Full Example
The following example shows the complete workflow from start to finish.

The following example shows how to count messages and contacts in a TGZ archive using C#.

```csharp
using System;
using Aspose.Email.Storage.Zimbra;

class Program
{
    static void Main()
    {
        var fileName = "xhy.tgz";
        using (var reader = new TgzReader(fileName))
        {
            int numberOfMessages = reader.GetItemsCount(ItemType.Message);
            int numberOfContacts = reader.GetItemsCount(ItemType.Contact);

            Console.WriteLine($"Messages: {numberOfMessages}");
            Console.WriteLine($"Contacts: {numberOfContacts}");
        }
    }
}
```

**Explanation of the code:**
- `var fileName = "xhy.tgz";` defines the path to the TGZ archive you want to analyze.
- The `using` statement creates a `TgzReader` instance and ensures `Dispose` runs automatically, releasing the file handle.
- `reader.GetItemsCount(ItemType.Message)` asks the reader to scan the archive's internal index and return how many `Message` items it contains.
- `reader.GetItemsCount(ItemType.Contact)` does the same for `Contact` items.
- `Console.WriteLine` prints the results to the console; in a real application you might store the numbers in a database or feed them to a progress indicator.

### Handling Exceptions
If the TGZ file is missing, corrupted, or contains unsupported data, `TgzReader` throws an `Aspose.Email.Storage.Zimbra.ZimbraException`. Wrap the call in a try‑catch block to handle such scenarios gracefully:

```csharp
try
{
    using (var reader = new TgzReader(fileName))
    {
        int messages = reader.GetItemsCount(ItemType.Message);
        int contacts = reader.GetItemsCount(ItemType.Contact);
        // Use counts here.
    }
}
catch (ZimbraException ex)
{
    Console.Error.WriteLine($"Failed to read TGZ archive: {ex.Message}");
    // Additional recovery logic such as fallback or user notification.
}
```

### Counting Other Item Types
`ItemType` is an enum that includes additional values like `Calendar`, `Task`, and `Document`. Counting them follows the same pattern:

```csharp
int calendarCount = reader.GetItemsCount(ItemType.Calendar);
int taskCount = reader.GetItemsCount(ItemType.Task);
```

### Performance Considerations
`GetItemsCount` reads the archive's central directory only once per call, so the overhead is minimal. However, calling it repeatedly for the same archive may cause redundant scans. Cache the results if you need multiple counts in a tight loop.

### Thread Safety
`TgzReader` instances are not thread‑safe. If you need to count items from several archives concurrently, create a separate `TgzReader` per thread or synchronize access with a lock.

## Conclusion
Using `TgzReader.GetItemsCount` you can quickly determine how many messages, contacts or other email items reside in a TGZ archive without extracting its contents. The approach saves I/O, simplifies validation steps in migration pipelines, and integrates cleanly with standard .NET patterns. By handling exceptions and disposing the reader correctly, you ensure robust and leak‑free code.

## FAQs
1. **What file format does TgzReader support?**
   TgzReader works with TGZ (tar‑gzip) archives that contain Aspose.Email items such as messages, contacts, calendar items or tasks.

2. **Do I need to extract the archive before counting items?**
   No. GetItemsCount reads the archive metadata directly, so you can obtain counts without extracting any files.

3. **Can I count other item types besides messages and contacts?**
   Yes. The ItemType enum includes Calendar, Task, and other supported entities, and you can pass any of them to GetItemsCount.

4. **What happens if the TGZ file is corrupted?**
   TgzReader throws an Aspose.Email.Storage.Zimbra.ZimbraException. Catch the exception to handle corrupted archives gracefully.

5. **Is the TgzReader class thread‑safe?**
   TgzReader is not thread‑safe; create a separate instance per thread or synchronize access if you share one.

6. **Do I need to dispose of TgzReader manually?**
   Yes. Use a using statement or call Dispose to release file handles once you are finished.

## Get a Free License and Explore More
Start experimenting with Aspose.Email for .NET today by obtaining a temporary license. Visit the [Aspose temporary license page](https://purchase.aspose.com/temporary-license/) to request a free 30‑day license.

- Explore the full documentation: https://docs.aspose.com/email/net/
- Browse the API reference for additional classes: https://reference.aspose.com/email/net/
- Try the online demo apps for quick testing: https://products.aspose.app/email/family
