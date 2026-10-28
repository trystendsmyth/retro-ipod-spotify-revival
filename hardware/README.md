# USB-C bracket

A printed bracket that holds the USB-C breakout (Adafruit
[#6050](https://www.adafruit.com/product/6050)) in the iPod's old dock-connector opening.
Plugging and unplugging push and pull on the receptacle; the bracket takes those forces
instead of the solder joints. It uses the existing opening: nothing on the case is cut or
drilled.

| File | |
|---|---|
| [`usb-c-bracket.scad`](usb-c-bracket.scad) | OpenSCAD source, with every size as a parameter |
| [`usb-c-bracket.stl`](usb-c-bracket.stl) | the bracket with the default sizes (GitHub shows it in 3D) |
| [`normalize_stl.py`](normalize_stl.py) | sorts the STL's facets so a re-render gives the same file |

## How it works

* **Bezel:** fills the opening from the outside face, with a window for the receptacle.
* **Flange:** sits against the inside of the case wall around the opening. Pulling a
  cable out pushes it against the wall.
* **Base:** lies flat on the inside of the case and is glued to it. Pushing a cable in
  loads this glue joint sideways (in shear), where epoxy is strongest.
* **Bosses:** two M2 screws through the breakout's mounting holes hold the board, so the
  receptacle's face sits 0.64 mm behind the outside face with the default sizes.

## Measure your case first

No dimensions of the 4th-gen dock opening are published, and the defaults are estimates,
not measurements `[MEASURE]`. With calipers, on your case:

| Parameter | Default | What to measure |
|---|---|---|
| `slot_w` | 21.0 mm | width of the opening |
| `slot_h` | 4.0 mm | height of the opening (through the case's thickness) |
| `slot_r` | 1.0 mm | corner radius of the opening |
| `wall_t` | 1.2 mm | wall thickness at the opening |
| `floor_to_slot_center` | 4.0 mm | from the middle of the opening to the inside surface the base will be glued to |

Then render with your numbers:

```bash
openscad -o usb-c-bracket.stl -D slot_w=20.8 -D slot_h=3.6 -D wall_t=1.3 hardware/usb-c-bracket.scad
```

OpenSCAD refuses sizes that can't work (for example an opening too narrow for the
bezel's sides) and prints how far the receptacle sits behind the outside face: the wall
thickness less the receptacle's 0.56 mm overhang. Over 0.8 mm (a wall over about 1.4 mm),
cables with thick plug bodies may not click in all the way; try yours `[MEASURE]`.

The breakout's sizes come from Adafruit's
[board file](https://github.com/adafruit/Adafruit-Sunken-USB-Type-C-Breakout-PCB):
20.32 x 13.97 mm, 2.5 mm mounting holes 15.75 mm apart and 3.56 mm in from the
receptacle edge, receptacle 0.56 mm past the board edge.

## Print

| Setting | Value |
|---|---|
| Material | PETG (PLA works, but softens in a warm pocket or car) |
| Layer height | 0.12 mm (the bezel is under 2 mm thick) |
| Walls | 3 or more; infill 100 % |
| Orientation | base flat on the bed, bosses up |
| Supports | none (the bezel overhangs the flange by 1.2 mm) |

Print a test piece and check the bezel slides into the opening before gluing anything.

## Fit

1. Screw the breakout to the bosses with two M2 x 4 mm self-tapping screws, receptacle
   facing the bezel. Its edge rests against the back of the bezel.
2. Solder the two charging wires (chapter 7) before gluing; they leave from the board's
   header pads at the back.
3. Push the bezel into the opening from inside until the flange meets the wall. Plug in a
   cable and check it clicks in.
4. Glue the base to the case with two-part epoxy (5-minute is fine). Keep epoxy out of the
   receptacle and off the bezel's outside face. Let it cure before plugging in again.

## Licence

Original design for this repository, Apache-2.0 like the rest of it. Not a remix.
