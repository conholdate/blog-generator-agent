---
title: Extract PowerPoint Animation Frames with Aspose.Slides for Python
seoTitle: Extract PowerPoint Animation Frames with Aspose.Slides for Python
description: Learn how to extract each animation frame from a PowerPoint presentation
  using Aspose.Slides for Python via .NET, with step‑by‑step code and event handling.
date: Fri, 02 Oct 2026 05:58:54 +0000
draft: true
url: /slides/extract-ppt-frames-python/
author: Muzammil Khan
summary: This tutorial shows how to capture every frame of a slide animation as an
  image using Aspose.Slides for Python. You will see the full code walk‑through, event
  handling details, and how to save the frames as PNG files.
tags: ['python', 'aspose-slides', 'powerpoint', 'animation-frames', 'presentationanimationsgenerator', 'presentationplayer', 'slide-animation', 'image-export']
categories: ["Aspose.Slides Product Family"]
showtoc: true
cover:
  image: images/extract-ppt-frames-python.jpg
  alt: Extract PowerPoint Animation Frames with Aspose.Slides for Python
  caption: Extract PowerPoint Animation Frames with Aspose.Slides for Python
  hidden: false
steps:
- Install Aspose.Slides for Python via pip.
- Load a presentation and add an animated shape.
- Subscribe to the frame_tick event and save each frame as PNG.
- Run PresentationAnimationsGenerator with PresentationPlayer to capture the animation.
faqs:
- q: Can I capture animation frames from any slide in a presentation?
  a: Yes, you can iterate over the Slides collection and run the generator for each
    slide you want to capture.
- q: What image format does the sample use for saved frames?
  a: The example saves each frame as a PNG file, but any format supported by Aspose.Slides
    (e.g., JPG, BMP) can be used.
- q: Do I need a commercial license to use PresentationAnimationsGenerator?
  a: A temporary free license works for development and testing; a full license is
    required for production deployments.
- q: How do I control the frame rate of the captured animation?
  a: The frame rate is set by the FPS variable when creating the PresentationPlayer;
    change the value to suit your needs.
- q: Is the event‑handling model the same as in .NET?
  a: Yes, Aspose.Slides for Python via .NET exposes .NET‑style events such as frame_tick
    and new_animation, allowing familiar event handling in Python.
---

Extracting individual animation frames from a PowerPoint file lets you repurpose motion graphics as static images, generate thumbnails, or create frame‑by‑frame video. This guide demonstrates how to do that with **Aspose.Slides for Python via .NET**, using the new `PresentationAnimationsGenerator` and `PresentationPlayer` classes.

## Key Takeaways
- `PresentationAnimationsGenerator` renders slide animations frame by frame.
- `PresentationPlayer` drives the playback and exposes a `frame_tick` event for custom processing.
- You can save each frame as an image (PNG in the example) with standard Aspose.Slides methods.
- The API follows .NET‑style event handling, which works naturally in Python.
- No additional third‑party libraries are required beyond Aspose.Slides.

## Why This Feature Matters
Developers often need to break down complex slide animations into discrete images for web previews, e‑learning content, or automated testing. Prior to this API, extracting frames required manual timing calculations or external video tools. The built‑in generator simplifies the workflow, provides precise frame control, and integrates directly with Aspose.Slides’ export capabilities.

## Getting Started with Aspose.Slides
First, add the Aspose.Slides package to your Python environment:

```bash
pip install aspose-slides
```

The product page provides an overview of supported formats and licensing options: [Aspose.Slides for Python via .NET](https://products.aspose.com/slides/python-net/).

## How to Extract Animation Frames from a PowerPoint Presentation
The following example demonstrates the complete workflow:

**What the code does:** it loads a presentation, adds a rectangle shape with a fade effect, subscribes to the `frame_tick` event to save each rendered frame as a PNG file, and then runs the animation generator.

```python
import aspose.slides as slides
from aspose.slides.animation import EffectType, EffectSubtype, EffectTriggerType
from aspose.slides.export import PresentationAnimationsGenerator, PresentationPlayer

FPS = 30

# Load an Empty Presentation (Or Replace with Your Own File)
with slides.Presentation() as presentation:
    slide = presentation.slides[0]
    # Add a rectangle shape that will be animated
    shape = slide.shapes.add_auto_shape(slides.ShapeType.RECTANGLE, 50, 50, 200, 100)
    # Apply a simple fade effect after the previous animation (or start)
    slide.timeline.main_sequence.add_effect(
        shape, EffectType.FADE, EffectSubtype.NONE, EffectTriggerType.AFTER_PREVIOUS)

    # Event handler that receives each frame and saves it as a PNG
    def on_frame_tick(sender, args):
        with args.get_frame() as frame:
            frame.save(f"frame_{sender.frame_index:04d}.png")

    # Create generator and player, wire the event, and start playback
    with PresentationAnimationsGenerator(presentation) as generator:
        with PresentationPlayer(generator, FPS) as player:
            player.frame_tick += on_frame_tick
            generator.run(presentation.slides)
```

**Explanation of key steps**
1. **Create a presentation** – `slides.Presentation()` constructs an in‑memory slide deck.
2. **Add an animated shape** – `add_auto_shape` creates a rectangle; `add_effect` attaches a fade animation.
3. **Define the frame handler** – The `on_frame_tick` function receives the `sender` (player) and `args` (frame data). `args.get_frame()` returns an image object that can be saved directly.
4. **Instantiate the generator and player** – `PresentationAnimationsGenerator` prepares the animation timeline, while `PresentationPlayer` drives playback at the specified FPS.
5. **Wire the event** – `player.frame_tick += on_frame_tick` registers the callback so it runs for every rendered frame.
6. **Run the animation** – `generator.run(presentation.slides)` starts processing; each frame is captured by the handler and written to disk.

You can also pass a lambda directly to `run` if you prefer an inline handler:

```python
with PresentationAnimationsGenerator(presentation) as generator:
    generator.run(presentation.slides, FPS, lambda sender, args: print("Frame", sender.frame_index))
```

The `new_animation` event lets you inspect animation metadata such as total duration:

```python
def on_new_animation(animation_player):
    print("Animation duration:", animation_player.duration)

generator.new_animation += on_new_animation
```

## Conclusion
By leveraging `PresentationAnimationsGenerator` and `PresentationPlayer`, you can programmatically render each frame of a PowerPoint animation and export it as an image. This approach removes the need for external video tools, gives you precise control over frame rate, and fits naturally into existing Python workflows that already use Aspose.Slides.

## FAQs
1. **Can I capture animation frames from any slide in a presentation?**
   Yes, you can iterate over the Slides collection and run the generator for each slide you want to capture.
2. **What image format does the sample use for saved frames?**
   The example saves each frame as a PNG file, but any format supported by Aspose.Slides (e.g., JPG, BMP) can be used.
3. **Do I need a commercial license to use PresentationAnimationsGenerator?**
   A temporary free license works for development and testing; a full license is required for production deployments.
4. **How do I control the frame rate of the captured animation?**
   The frame rate is set by the FPS variable when creating the PresentationPlayer; change the value to suit your needs.
5. **Is the event‑handling model the same as in .NET?**
   Yes, Aspose.Slides for Python via .NET exposes .NET‑style events such as frame_tick and new_animation, allowing familiar event handling in Python.

## Get a Free License and Explore More
Start experimenting with Aspose.Slides today by obtaining a temporary license: [Free License](https://purchase.aspose.com/temporary-license/).

- [Documentation](https://docs.aspose.com/slides/python-net/)
- [API Reference](https://reference.aspose.com/slides/python-net/)
- [Free Online Apps](https://products.aspose.app/slides/family)

