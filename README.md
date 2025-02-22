# Flightplan

**A python script for generating a military-style low level navigation
plan and map info.**

Flying flight simulator planned low level routes in VR is demanding. In a real fast jet, you'll have an
annotated map in your hand with arrival times and departure bearings
for each waypoint. You can glance at it without flying the jet into the
ground. How can we replicate this in VR in a flight simulator?

One solution is to use the freeware application [Little
Navmap](https://albar965.github.io/littlenavmap.html). Waypoint `ident`
metadata can be configured to display relevant waypoint info on the
map. But formatting the information in _Little Navmap_ is quite tedious.

Separately, in [this YouTube
video](https://www.youtube.com/watch?v=L68ACL5_N24), cgiaviator
explains a method for planning a medium to low level military style
navigation sortie for the [Just Flight Hawk
T1](https://www.justflight.com/product/hawk-t1a-advanced-trainer-microsoft-flight-simulator).
Again, quite tedious.

This python script takes as input a route planned in [Little
Navmap](https://albar965.github.io/littlenavmap.html). It generates
sortie planning information and waypoint labels to display the
information, and creates a new _Little Navmap_ file with it. This can
then be loaded into the cockpit via the
[toolbar](https://github.com/bymaximus/msfs2020-toolbar-little-nav-map)
and flown.

Planning info displayed on the map includes:

- transit altitude
- top of climb arrival time
- top of descent arrival time
- low level entry point arrival time
- cumulative waypoint arrival time
- waypoint departure bearing
- miscellaneous info (e.g. VOR/ILS frequencies)

_Original_
![original](/docs/images/original.png)

_Processed. Each waypoint shows the cumulative time from the low level
entry point and the exit bearing from that waypoint._
![processed](/docs/images/processed.png)

## Installation

Python packaging is a fiasco. Here's how it's supposed to work. You
have my sympathies.

1. **Download the package to your machine.** It's under "Releases".

2. **Make sure you have `pip` installed.**  Most Python installations
   include `pip` by default. You can check by running    `pip --version`
   in your terminal. If it's not installed, follow the instructions on
   [https://pip.pypa.io/en/stable/installation/](https://pip.pypa.io/en/stable/installation/).

3. **Create a virtual environment (recommended).**  This helps to
   isolate the project's dependencies.

```    
> python3 -m venv .venv    
> source .venv/bin/activate  # On Linux/macOS    
> .venv\Scripts\activate     # On Windows    
```

4. **Install the package using `pip`.** In the `/dist` folder:

```
> pip install flightplan-0.1.0-py3-none-any.whl    
```

## Usage

Getting help:

```aiignore 
> flightplan
```

Running the app:

```
> flightplan [path_to_little_navmap_plan] --verbose

Converting /Users/richardlyon/Dev/python-flightplan/tests/data/VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln
...
File written to /Users/richardlyon/Dev/python-flightplan/tests/data/VFR Newcastle (EGNT) to Inverness (EGPE) [processed].lnmpln

Name           | Ident           | Alt   | Comment
-------------------------------------------------------
Newcastle      : 0:00/342        : 00266 : START
TOC            : 3:20/FL200/TOC  : 20000 : TOC
Saint Abbs     : 9:10/350/112.5  : 20000 : TP1
TOD            : 13:58/FL200/TOD : 20000 : TOD
Montrose       : 17:18/253/LLEP  : 00500 : LLEP
Forfar         : 2:11/338        : 00500 : WP1
Crathie        : 5:56/251        : 00500 : WP2
Braemar        : 7:16/225        : 00500 : WP3
Tummel         : 10:44/264       : 00500 : WP4
Rannoch        : 12:43/342       : 00500 : WP5
Loch Ericht    : 13:17/032       : 00500 : WP6
Dalwhinnie     : 15:10/310       : 00500 : WP7
Fort Augustus  : 17:49/033       : 00500 : WP8
None           : 20:42/049/ILS108.5/RW05 : 00500 : WP9
```

Load the version with the `[processed]` in the filename into _Little
Navmap_ and enjoy.

## Configuring the app

The app is set up with the following parameters from cgiaviator's
tutorial:

- climb 300kts / M0.65
- transit at M0.65 at a FL twice the range to the low level entry point
- descend M0.8 / 360kts
- fly low level route at 420 kts

You can alter these in the configuration file as follows (run `> flightplan config` to locate the file):

```aiignore
climb_rate_ft_min = 6000
descent_rate_ft_min = 6000
transit_groundspeed_kts = 360
route_airspeed_kts = 420
route_alt_ft = 500
```

## Creating a base plan

Here's how I set up a route before running the convertor. You'll find
it in the `/examples` folder as `VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln`:

![](/docs/images/lnmap-flight-plan.png)

You don't need to name the waypoints but, if you do, the names will
appear during processing making it easier. Anything in the `Remarks`
field is added to the displayed info. I use it for VOR/ILS frequencies,
runways etc. Keep it short, though, as _Little Navmap_ will truncate it
at larger scales, which is quite annoying at 420 kts/500'.

During conversion, you'll be asked for low level entry and exit points.
Conversion supports multi-segment transits. In this example, I enter
low level at Montrose, so the entry waypoint number is 3. I exit at
ILN234013 - waypoint 12.

A future update will add fuel calculations.

## Tips

In Little Navmap, play around with the `Map Flight Plan` formatting
options to increase the visibility of the waypoint info.

## Changelog

0.1.0 Initial Release


