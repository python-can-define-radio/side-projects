
# GRC Spectrum Analyzer

ℹ️ This material coincides with material from SDR slideshow D (slides 1-27).  However, the slides are not necessary for building and operating this program.

Prerequisite: basic knowledge of [guizero](https://github.com/python-can-define-radio/python-course/blob/main/classroom_activities/Ch02_Advanced/03_guizero.md), specifically creating an `App` with `Text` and `Slider` widgets.

### Introduction

Most of us have listened to an FM Radio at least once in our lives. We may even know that the music on these radio stations is transmitted using electromagnetic waves. However, it can be difficult to imagine what these invisible waves look like. A Spectrum Analyzer is one way to **_see_** those frequencies. 

### Dependencies

The paragradio module is required for the next exercise, you will need to `pip install paragradio`.
Marimo is also required `pip install marimo`.

### Execution

We'll start by looking at a simulated spectrum analyzer. This allows us to familiarize ourselves with the Python code that launches GNU Radio.

Open a new Marimo notebook. (For an intro to marimo, reference the lesson in the github python course [TODO: link to marimo lesson]).

Copy the following:

```python3
## 1
## Try this.
#### In the first cell:
import marimo as mo
from paragradio.v2024_12 import PGR_simspecan

#### In the second cell:
pgr = PGR_simspecan()
pgr.start()
```

If it runs, you should see this:

[[TODO: Image of simspecan]]

[[ Discuss the three GUI Sinks. ]]

Let's explore what methods we have available.

```python3
## 2
## Keep the same Marimo cells shown above.
## In a new cell, add this:
pgr.set_center_freq(93.7e6)
```

What did it do? Look closely at the simspecan and then change the frequency and try again.

#### Adding UI elements

To improve the user experience, we can add a slider to control the frequency. This could be done using any graphics toolkit (Guizero, PyQt, PyGame, etc). In this lesson, we'll use Marimo.

```python3
## 3
## Try this.
cfslider = mo.ui.slider(start=92.5, stop=94.5, step=0.01, label="Frequency (Hz)", show_value=True)
cfslider
```

This will create a slider, but the slider doesn't do anything yet. (Try sliding it to confirm.)

To make it actually work, insert this:

```python3
## 4
pgr.set_center_freq(slider.value)
```

With this 

Now, let's start using hardware. First, let's run the code without plugging in the hardware, so we can see the error message:

```python3
## 2
## Try this. You should get an error.
from paragradio.v2024_12 import PGR_specan
default_freq = 98e6
default_gain = 16
pgr = PGR_specan(default_freq, default_gain)
pgr.start()
```

You should see `Failed to launch ... not enough devices [[ TODO: actual err msg]]`. As we expected, having no devices plugged in causes this error.

### Intro to the HackRF One

Open your HackRF One box [[ TODO: assembly discussion, careful antenna, etc. Also discuss the HackRF docs, including block diagram, sample rate limitations (tell them this is the instantaneous bandwidth that it can see), gain limitations, transmit power limitations, pointing out that we chose 2.437 GHz because the HackRF One is stronger in this band ]]

Run the code again with the HackRF plugged in, and you should see something like this:

[[ TODO: Image of Spec A ]]

The spectrum will vary depending on what activity (if any) is present on those frequencies in your area.

### Checkpoint Activity

The instructor will ensure that everyone has working hardware by doing the following activity:

1. The instructor will transmit a pure sine wave on 2.437 GHz that toggles on and off every few seconds.
2. Students will adjust the Python code to tune to 2.4369 GHz.
3. Students will look at the waterfall sink or the frequency sink to see the spike of activity appearing and disappearing.

Notice that you (the student) tuned to a frequency that was slightly offset from the transmitted frequency. This is because the Hack RF (and most SDR devices that aren't terribly expensive) have a "DC Spike" on the center frequency of the received spectrum. We tune off-center so that this spike doesn't obscure or distort the frequency of interest.
