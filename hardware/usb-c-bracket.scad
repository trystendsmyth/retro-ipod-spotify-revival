// USB-C bracket for the iPod 4th gen (A1059) dock-connector opening.
// Holds an Adafruit #6050 sunken USB-C breakout so its receptacle sits in the opening,
// and takes plug forces off the solder joints.
//
// Render: openscad -o hardware/usb-c-bracket.stl hardware/usb-c-bracket.scad
// Change values with -D, e.g. -D slot_w=20.6 -D wall_t=1.4
//
// Coordinates: x across the opening, y into the iPod (y = 0 is the outside face of the
// case), z through the case thickness (z = 0 is the middle of the opening).
//
// Parts, front to back:
//   bezel   fills the opening from the outside face, with a window for the receptacle;
//   flange  sits against the inside of the case wall around the opening (pull-out stop);
//   base    lies on the inside of the case and is glued to it (takes the push-in force);
//   bosses  two posts for M2 screws through the breakout's mounting holes.
//
// Original design for retro-ipod-spotify-revival (Apache-2.0), not a remix.

/* [iPod case: measure these with calipers] */
// Width of the dock-connector opening [MEASURE]
slot_w = 21.0;
// Height of the opening, through the case thickness [MEASURE]
slot_h = 4.0;
// Corner radius of the opening [MEASURE]
slot_r = 1.0;
// Wall thickness around the opening [MEASURE]
wall_t = 1.2;
// From the middle of the opening to the inside surface the base is glued to [MEASURE]
floor_to_slot_center = 4.0;
// Gap on each side of the bezel, so it slides in
fit = 0.15;

/* [Adafruit #6050 sunken USB-C breakout, from Adafruit's board file] */
pcb_w = 20.32;
pcb_d = 13.97;
pcb_t = 1.6;
// Receptacle shell, and how far it sticks out past the board edge
usbc_w = 8.94;
usbc_h = 3.26;
usbc_overhang = 0.56;
// Mounting holes (2.5 mm, plated): spacing, and distance in from the receptacle edge
hole_dx = 15.748;
hole_from_edge = 3.556;
// Height of the board's middle above the middle of the opening (sunken: about 0) [MEASURE]
pcb_z = 0;

/* [Bracket] */
flange_t = 1.2;
flange_margin = 1.5;
base_t = 1.2;
boss_d = 4.5;
// Pilot hole for M2 self-tapping screws
pilot_d = 1.6;
// Clearance around the receptacle shell in the bezel window
window_clear = 0.25;

$fn = 48;

pcb_edge_y = wall_t;                       // board edge rests on the back of the bezel
face_recess = pcb_edge_y - usbc_overhang;  // receptacle face behind the outside face
floor_z = -floor_to_slot_center;
base_top = floor_z + base_t;
pcb_bottom = pcb_z - pcb_t / 2;
boss_h = pcb_bottom - base_top;
hole_y = pcb_edge_y + hole_from_edge;
base_depth = hole_y + boss_d / 2 + 1.0 - (wall_t + flange_t);
flange_w = slot_w + 2 * flange_margin;
flange_top = slot_h / 2 + flange_margin;

assert(boss_h >= 1.2, str("bosses only ", boss_h, " mm tall: raise floor_to_slot_center or lower pcb_z"));
// A USB-C plug's shell is 8.25 x 2.4 mm. If the window is taller than the opening, the
// bezel is just its two sides, which is fine.
assert(slot_w - 2 * fit >= usbc_w + 2 * window_clear + 2.0, "opening too narrow: no room for the bezel's sides");
assert(slot_h - 2 * fit >= 2.6, "opening too low for a USB-C plug");
echo(str("receptacle face sits ", face_recess, " mm behind the outside face"));
if (face_recess > 0.8) echo("WARNING: more than 0.8 mm recess; thick plug overmolds may not click in");

module rounded_rect(w, h, r) {
    offset(r = r) square([w - 2 * r, h - 2 * r], center = true);
}

// A 2D shape in x-z, extruded along y from y0 to y1
module slab_xz(y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
}

module window() {
    slab_xz(-1, pcb_edge_y + 0.01)
        translate([0, pcb_z]) rounded_rect(usbc_w + 2 * window_clear, usbc_h + 2 * window_clear, 1.2);
}

module bracket() {
    difference() {
        union() {
            // bezel in the opening
            slab_xz(0, wall_t) rounded_rect(slot_w - 2 * fit, slot_h - 2 * fit, max(0.01, slot_r - fit));
            // flange behind the wall, down to the floor
            slab_xz(wall_t, wall_t + flange_t)
                translate([-flange_w / 2, floor_z]) square([flange_w, flange_top - floor_z]);
            // base on the floor
            translate([-flange_w / 2, wall_t + flange_t, floor_z]) cube([flange_w, base_depth, base_t]);
            // screw bosses
            for (sx = [-1, 1])
                translate([sx * hole_dx / 2, hole_y, base_top - 0.01]) cylinder(d = boss_d, h = boss_h + 0.01);
        }
        window();
        // slot in the flange for the board to pass through
        slab_xz(pcb_edge_y - 0.01, wall_t + flange_t + 0.01)
            translate([0, pcb_z]) square([pcb_w + 0.4, pcb_t + 0.3], center = true);
        // the receptacle's lower half and the board's underside need room above the base
        slab_xz(pcb_edge_y - 0.01, wall_t + flange_t + 0.01)
            translate([0, pcb_z]) rounded_rect(usbc_w + 2 * window_clear, usbc_h + 2 * window_clear, 1.2);
        // pilot holes
        for (sx = [-1, 1])
            translate([sx * hole_dx / 2, hole_y, floor_z - 1]) cylinder(d = pilot_d, h = 20);
    }
}

bracket();
