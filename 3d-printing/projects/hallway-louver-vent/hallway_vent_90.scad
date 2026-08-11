// ============================================================
// Hallway 90-degree DIVERTER vent - cabinet sits over the register.
// Problem: floor register is fully under a cabinet (air gaps only at the
// four corners, ~20 cm); straight-up flow is blocked. This cover seals the
// top and BENDS the flow 90 deg about the LONG axis: air exits horizontally
// through a low scoop hood along the room-facing long edge, thrown along
// the floor toward the open room (away from the closet side).
//
// MEASUREMENTS (taken on site):
//   floor-plane opening 320 x 180, dropdown (duct) 300 x 160 at a measured
//   18-20 mm below floor top (worst case 18 used). Old grill 355 x 204 flange / 275 x 125 louver area.
//
// TWO-PIECE (print-physics driven): a one-piece raised hood cannot print
// support-free top-face-down (plate would float 15 mm above the bed -
// playbook rule: re-check every feature in PRINT orientation).
//   PAN  - flush drop-in: 10 mm lip, 4.5 plate, skirt into the 320x180
//          opening, 300 x 40 slot at the room edge, 45-deg corner deflector
//          turning the plenum flow up into the slot.
//          Print TOP FACE DOWN, flat, zero supports (house pattern).
//   HOOD - low scoop over the slot, 20 mm total above floor (user cap),
//          open room-facing side with deep vertical straightening fins,
//          gaps <= 5 mm (child-safety house rule).
//          Print ROOF FACE DOWN, zero supports; both show faces get PEI
//          texture. Walls drop into a locating groove in the pan; CA glue.
// AIR DIRECTION: exits toward +Y. Install with +Y facing the open room.
// Material: PETG (heater supply). 0.2 mm, 4 walls.
// Design orientation: pan plate top z=0, pan extends -z, hood extends +z.
// ============================================================

/* [What to render] */
RENDER_PART = "assembly";   // ["pan", "hood", "assembly", "plinth"]

/* [Opening - CONFIRM BY MEASURE] */
floor_open_L = 320;   // x, long axis, opening in the floor plane
floor_open_W = 180;   // y
ledge_depth  = 18.0;  // floor top down to the 300x160 ledge -
                      // MEASURED 18-20 mm (correction from an early "~1 inch" estimate);
                      // sized to the WORST CASE 18 (playbook rule)
duct_L = 300; duct_W = 160;
end_clear  = 0.75;    // skirt clearance per end
side_clear = 1.0;     // skirt clearance per side

/* [Pan body] */
lip_w   = 10.0;       // floor-resting lip all around
plate_T = 4.5;
skirt_depth = 15.0;   // below floor plane; must clear the 18 mm ledge
skirt_wall  = 2.4;
edge_ch = 2.0; corner_r = 2.0;

/* [Slot + deflector] */
slot_L  = 300;        // x extent of the slot (centered)
slot_y0 = 40;         // slot near edge (closet side of slot)
slot_y1 = 80;         // slot far edge (room side)
n_slot_ribs = 3;      // full-thickness ribs bracing the slot span
slot_rib_t  = 2.4;

/* [Hood] */
scoop_cap  = 20.0;    // max height above FLOOR plane (user limit)
hood_wall  = 2.4;
roof_T     = 2.5;
hood_y0    = 34;      // back wall outer face (closet side)
hood_y1    = 96;      // open outlet face (room side)
hood_margin_x = 4;    // hood extends past slot ends
groove_depth = 1.2; groove_clear = 0.2;
fin_t = 1.6;
fin_gap = 5.0;        // CHILD SAFETY <= 5
fin_y0 = 60;          // fins run fin_y0 .. hood_y1 (deep = straight throw)
fin_z_clear = 0.3;    // fin bottom vs plate top
hood_edge_ch = 2.0;

// ---------------- derived ----------------
plate_L = floor_open_L + 2*lip_w;            // 340
plate_W = floor_open_W + 2*lip_w;            // 200
skirt_L = floor_open_L - 2*end_clear;        // 318.5
skirt_W = floor_open_W - 2*side_clear;       // 178
skirt_in_L = skirt_L - 2*skirt_wall;
skirt_in_W = skirt_W - 2*skirt_wall;
hood_h  = scoop_cap - plate_T;               // 15.5 above plate top
hood_L  = slot_L + 2*(hood_wall + hood_margin_x);   // 312.8 (a stale "308" here once named an export file; see README)
hood_D  = hood_y1 - hood_y0;                 // 62
fin_pitch = fin_gap + fin_t;                 // 6.6
fin_H   = hood_h - roof_T;                   // 13 (roof underside to plate)
n_fins  = floor((hood_L - 2*hood_wall - fin_gap) / fin_pitch);
fins_span = n_fins*fin_pitch + fin_t;
defl_d  = skirt_in_W/2 - slot_y1;            // corner-fillet wedge depth
$fn = 48;

assert(plate_L <= 350 && plate_W <= 320, "pan exceeds bed");
assert(hood_L <= 350 && hood_D <= 320, "hood exceeds bed");
assert(fin_gap <= 5.01, "child-safety: fin gap > 5");
assert(skirt_depth <= ledge_depth - 2, "skirt hits the ledge");
assert(slot_L/2 <= skirt_in_L/2 - 2 && slot_y1 <= skirt_in_W/2 - 2,
       "slot exceeds skirt interior");
assert(hood_y0 + hood_wall + groove_clear < slot_y0,
       "back-wall groove intersects slot");
assert(hood_L/2 - hood_wall - groove_clear > slot_L/2 + 1,
       "end-wall groove too close to slot end");
assert(hood_L/2 <= plate_L/2 - 2 && hood_y1 <= plate_W/2 - 2,
       "hood exceeds plate");
assert(plate_T + hood_h <= scoop_cap + 0.01, "scoop over user height cap");
echo(str("outlet free area ~",
     round((hood_L - 2*hood_wall - ((n_fins+1)*fin_t)) * fin_H / 100),
     " cm2  (slot ", round((slot_L*(slot_y1-slot_y0)
       - n_slot_ribs*slot_rib_t*(slot_y1-slot_y0))/100),
     " cm2, duct ", round(duct_L*duct_W/100), " cm2)"));
echo(str("n_fins ", n_fins, "  hood total above floor ", plate_T + hood_h));

// ---------------- helpers ----------------
module ch_x(y, z, c, l) { translate([0, y, z]) rotate([45, 0, 0])
    cube([l, c*sqrt(2), c*sqrt(2)], center=true); }
module ch_y(x, z, c, l) { translate([x, 0, z]) rotate([0, 0, 90]) rotate([45, 0, 0])
    cube([l, c*sqrt(2), c*sqrt(2)], center=true); }
module rrect(l, w, r) { offset(r=r) offset(delta=-r) square([l, w], center=true); }

// ============================================================ PAN
module pan_plate() {
    difference() {
        translate([0, 0, -plate_T]) linear_extrude(plate_T)
            rrect(plate_L, plate_W, corner_r);
        // slot (ribs re-added after)
        translate([-slot_L/2, slot_y0, -plate_T - 1])
            cube([slot_L, slot_y1 - slot_y0, plate_T + 2]);
    }
    // full-thickness ribs bracing the slot span (hidden under the hood)
    for (i = [1 : n_slot_ribs])
        translate([-slot_L/2 + i*slot_L/(n_slot_ribs+1) - slot_rib_t/2,
                   slot_y0, -plate_T])
            cube([slot_rib_t, slot_y1 - slot_y0, plate_T]);
}
module pan_skirt() {
    translate([0, 0, -plate_T - skirt_depth]) linear_extrude(skirt_depth)
        difference() { square([skirt_L, skirt_W], center=true);
                       square([skirt_in_L, skirt_in_W], center=true); }
}
// 45-deg wedge filling the dead-end between slot far edge and skirt wall:
// +y plenum flow hits it and turns up into the slot.
module deflector() {
    translate([-slot_L/2, 0, 0]) rotate([90, 0, 90]) linear_extrude(slot_L)
        polygon([[slot_y1, -plate_T], [skirt_in_W/2, -plate_T],
                 [skirt_in_W/2, -plate_T - defl_d]]);
}
// locating groove for hood back + end walls (front face is open)
module hood_groove() {
    gw = hood_wall + 2*groove_clear;
    translate([0, 0, -groove_depth]) linear_extrude(groove_depth + 1) {
        // back wall groove
        translate([-hood_L/2 - groove_clear, hood_y0 - groove_clear])
            square([hood_L + 2*groove_clear, gw]);
        // end wall grooves: wall sx=+1 spans x [hood_L/2-hood_wall, hood_L/2]
        for (sx = [-1, 1])
            translate([sx>0 ? hood_L/2 - hood_wall - groove_clear
                            : -hood_L/2 - groove_clear,
                       hood_y0 - groove_clear])
                square([gw, hood_D + 2*groove_clear]);
    }
}
module pan_chamfers() {
    ch_x(-plate_W/2, 0, edge_ch, plate_L + 4); ch_x(plate_W/2, 0, edge_ch, plate_L + 4);
    ch_y(-plate_L/2, 0, edge_ch, plate_W + 4); ch_y(plate_L/2, 0, edge_ch, plate_W + 4);
    // skirt lead-in
    ch_x(-skirt_W/2, -plate_T - skirt_depth, 1.2, skirt_L + 4);
    ch_x( skirt_W/2, -plate_T - skirt_depth, 1.2, skirt_L + 4);
    ch_y(-skirt_L/2, -plate_T - skirt_depth, 1.2, skirt_W + 4);
    ch_y( skirt_L/2, -plate_T - skirt_depth, 1.2, skirt_W + 4);
}
module pan() {
    difference() {
        union() { pan_plate(); pan_skirt(); deflector(); }
        pan_chamfers();
        hood_groove();
    }
}

// ============================================================ HOOD
// Modeled in ASSEMBLED position: walls z = -groove_depth .. hood_h,
// roof top at z = hood_h. Open face at y = hood_y1 (+y, room side).
module hood_body() {
    // back wall
    translate([-hood_L/2, hood_y0, -groove_depth])
        cube([hood_L, hood_wall, groove_depth + hood_h]);
    // end walls
    for (sx = [-1, 1])
        translate([sx*hood_L/2 - (sx>0 ? hood_wall : 0), hood_y0, -groove_depth])
            cube([hood_wall, hood_D, groove_depth + hood_h]);
    // roof
    translate([-hood_L/2, hood_y0, hood_h - roof_T])
        cube([hood_L, hood_D, roof_T]);
    // fins: vertical straighteners, fused to roof, deep along y
    fin_x0 = -fins_span/2;
    for (k = [0 : n_fins])
        translate([fin_x0 + k*fin_pitch, fin_y0, fin_z_clear])
            cube([fin_t, hood_y1 - fin_y0, hood_h - fin_z_clear]);
}
module hood_chamfers() {
    // roof top perimeter, 45 deg (prints flaring from bed, roof-down)
    ch_x(hood_y0, hood_h, hood_edge_ch, hood_L + 4);
    ch_x(hood_y1, hood_h, hood_edge_ch, hood_L + 4);
    ch_y(-hood_L/2, hood_h, hood_edge_ch, hood_D + 4);
    ch_y( hood_L/2, hood_h, hood_edge_ch, hood_D + 4);
}
module hood() {
    difference() {
        hood_body();
        hood_chamfers();
    }
}

// ============================================================ PLINTH
// TRUE ONE-PIECE alternative: the entire cover is a 20 mm low box -
// flat roof at the scoop cap height, perimeter walls resting on the
// floor, fins built into the room-facing long edge, skirt hanging into
// the opening. ONE print, no glue. Requires ~20 mm clearance under the
// cabinet across the WHOLE footprint (not just the scoop strip).
// Prints TOP FACE DOWN: the whole roof is layer 1 on the PEI; walls,
// skirt, ribs, fins all grow straight up. Zero supports.
// Airflow bonus vs two-piece: full-width 17.5 mm channel -> ~40 cm2.
// Coordinates: roof top z=0, part extends -z; floor plane z=-scoop_cap.
/* [Plinth] */
p_roof_T   = 2.5;
p_wall_t   = 2.4;
p_fin_field= 300;    // fin field length; outlet corners stay solid
p_fin_d    = 30;     // fin depth along y
p_floor_clear = 0.5; // fin bottoms vs floor
p_rib_d    = 12;     // internal roof ribs, depth below roof underside
p_n_ribs   = 7;
p_stub_len = 8;      // room-side skirt registration stubs at the ends;
                     // MUST stay outside the fin field or they block channels

p_H       = scoop_cap;                 // 20 above floor
p_floor_z = -p_H;
p_skirt_bot = p_floor_z - skirt_depth;
p_fin_H   = p_H - p_roof_T;            // 17.5 outlet height
p_n_fins  = floor((p_fin_field - fin_gap) / fin_pitch);
p_fins_span = p_n_fins*fin_pitch + fin_t;

assert(p_fin_field/2 + 2 < plate_L/2 - p_wall_t, "fin field hits end walls");
echo(str("plinth outlet ~",
     round((p_fin_field - (p_n_fins+1)*fin_t) * p_fin_H / 100),
     " cm2, one piece, ", p_H, " mm above floor"));

module p_roof() {
    translate([0, 0, -p_roof_T]) linear_extrude(p_roof_T)
        rrect(plate_L, plate_W, corner_r);
}
module p_walls() {   // closet long wall + both end walls + room-face corners
    difference() {
        translate([0, 0, p_floor_z]) linear_extrude(p_H - p_roof_T + 0.1)
            difference() {
                rrect(plate_L, plate_W, corner_r);
                rrect(plate_L - 2*p_wall_t, plate_W - 2*p_wall_t, 1);
            }
        // open the room face over the fin field only
        translate([-p_fin_field/2, plate_W/2 - p_wall_t - 1, p_floor_z - 1])
            cube([p_fin_field, p_wall_t + 3, p_H + 2]);
    }
}
module p_skirt() {   // 3 sides full (ends + closet); room side = end stubs
    // hangs from roof underside through the floor opening: also structure
    difference() {
        translate([0, 0, p_skirt_bot])
            linear_extrude(-p_roof_T - p_skirt_bot + 0.1)
            difference() { square([skirt_L, skirt_W], center=true);
                           square([skirt_in_L, skirt_in_W], center=true); }
        // remove room-side wall between the stubs
        translate([-(skirt_L/2 - skirt_wall - p_stub_len),
                   skirt_W/2 - skirt_wall - 1, p_skirt_bot - 1])
            cube([skirt_L - 2*skirt_wall - 2*p_stub_len, skirt_wall + 2,
                  -p_roof_T - p_skirt_bot + 2]);
    }
}
module p_fins() {
    fx0 = -p_fins_span/2;
    for (k = [0 : p_n_fins])
        translate([fx0 + k*fin_pitch, plate_W/2 - p_fin_d,
                   p_floor_z + p_floor_clear])
            cube([fin_t, p_fin_d - 0.5, p_H - p_roof_T - p_floor_clear + 0.1]);
}
module p_ribs() {    // stiffen the roof; parallel to flow (+y), stop before fins
    for (i = [1 : p_n_ribs])
        translate([-skirt_in_L/2 + i*skirt_in_L/(p_n_ribs+1) - slot_rib_t/2,
                   -(plate_W/2 - p_wall_t), -p_roof_T - p_rib_d])
            cube([slot_rib_t, plate_W - 2*p_wall_t - p_fin_d - 5, p_rib_d]);
}
module p_chamfers() {
    ch_x(-plate_W/2, 0, edge_ch, plate_L + 4); ch_x(plate_W/2, 0, edge_ch, plate_L + 4);
    ch_y(-plate_L/2, 0, edge_ch, plate_W + 4); ch_y(plate_L/2, 0, edge_ch, plate_W + 4);
    // skirt lead-in
    ch_x(-skirt_W/2, p_skirt_bot, 1.2, skirt_L + 4);
    ch_x( skirt_W/2, p_skirt_bot, 1.2, skirt_L + 4);
    ch_y(-skirt_L/2, p_skirt_bot, 1.2, skirt_W + 4);
    ch_y( skirt_L/2, p_skirt_bot, 1.2, skirt_W + 4);
}
module plinth() {
    difference() {
        union() { p_roof(); p_walls(); p_skirt(); p_fins(); p_ribs(); }
        p_chamfers();
    }
}

// ============================================================ render
if (RENDER_PART == "pan") pan();
if (RENDER_PART == "hood") hood();
if (RENDER_PART == "assembly") { pan(); hood(); }
if (RENDER_PART == "plinth") plinth();
