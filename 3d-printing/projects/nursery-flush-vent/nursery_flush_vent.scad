// ============================================================
// Nursery Flush Drop-In Floor Vent - 350 x 147 mm opening
// Fittes-inspired minimal flush register, child-safe (5 mm slots)
// Two styles from one body: "fittes" (lengthwise slots) and
// "kumiko" (45° diamond lattice, Japandi).
// Drop-in: skirt registers inside the duct opening; flanges on the
// two LONG edges carry all load (ends are flush inside the opening
// so the part fits the H2D 350 mm bed in ONE piece).
// Print: PETG, TOP FACE DOWN on textured PEI, 0.2 mm layers, 4 walls.
// Units: mm.  Design orientation: top surface at z=0, part extends -z.
// ============================================================

/* [What to render] */
RENDER_PART = "fittes";  // ["fittes", "kumiko", "luxe", "luxe1", "liftkey"]
// luxe  = 3 nested channels (better airflow, matches nested-frame look)
// luxe1 = SINGLE channel + one floating panel (purest frameless look;
//         only ~45 cm2 / ~9% of duct free area - most restrictive)
// "full" = one-piece (ends flush, fits 350 bed with 0.75mm margin).
// "A"/"B" = two-part halves split at mid-length, dovetail-joined; the
// two-part body gets the FULL perimeter flange back (374 x 171 total).
PART = "full";           // ["full", "A", "B"]

/* [Opening (measured)] */
opening_L = 350.0;   // opening length (along wall direction)
opening_W = 147.0;   // opening width
end_clear = 0.75;    // clearance per END (plate & skirt ends sit inside opening)
side_clear = 1.0;    // skirt clearance per SIDE

/* [Body] */
flange_w  = 12.0;    // visible border resting on floor, LONG edges only
plate_T   = 4.5;     // top plate thickness (furniture-proof w/ ribs)
skirt_depth = 16.0;  // drop-down below plate underside
skirt_wall  = 2.4;   // skirt wall thickness
edge_ch   = 2.0;     // 45° chamfer, top outer perimeter (45° = safe top-face-down)
corner_r  = 1.5;     // XY corner radius of plate

/* [Fittes slots] */
slot_w  = 5.0;       // CHILD SAFETY: keep <= 5 (toddler finger ~8-10)
slat_w  = 8.0;
n_slots = 10;
slot_ch = 0.7;       // 45° chamfer on slot top edges (soft touch)
end_margin = 12.0;   // solid plate beyond slot field, each end

/* [Kumiko lattice] */
bar_w   = 3.4;       // lattice bar width
gap_w   = 5.0;       // CHILD SAFETY: perpendicular gap between bars <= 5
// field matches fittes field for visual parity

/* [Luxe frameless (parallel-openings principle, ONE PIECE): 3 nested 5mm channels] */
// Panel + 2 rings are fused to the cross-ribs below - no separate tray.
luxe_end_border  = 12;   // frame face beyond opening, ends
luxe_side_border = 18;   // frame face beyond opening, sides (12 flange + 6 over opening)
luxe_gap    = 5;         // channel width - CHILD SAFETY, same 5mm standard
luxe_ring_w = 12;        // nested ring face width
luxe_ch_depth = 16;      // channel downstand wall below top surface
// Hidden understructure: NO material under any channel between the top
// surface and luxe_rib_top - the channels read as continuous dark lines.
// Islands are carried by spine walls under their own solid faces, which
// guide loads down to deep cross-ribs.
luxe_rib_top = 14.5;     // deep cross-rib top, below top surface
luxe_spine_w = 2.4;      // hidden spine wall thickness
luxe_spine_bot = 15;     // spine walls reach this depth (overlap ribs 0.5)

/* [Ribs & magnets] */
rib_t = 2.4;         // cross-rib thickness
rib_d = 9.0;         // cross-rib depth below plate underside
n_ribs = 7;
mag_d = 8.4;         // magnet pocket dia (8x3 disc + glue)
mag_boss_d = 13.0;
mag_x = 60;          // pocket positions +/- x, y = 0

// ---------------- derived ----------------
TWO_PART = (PART != "full");
end_flange = flange_w;   // TWO_PART end-lip width; override separately from
                         // flange_w to get asymmetric lips (e.g. ends 10, sides 12)
full_end_lip = 0;        // ONE-PIECE end lips - exceeds the bed when > 0.75:
                         // only for 45-degree TILTED printing (stair-stepped
                         // show face + supports; two-part is the quality path)
// one-piece: plate ends flush inside opening (unless full_end_lip)
plate_L = TWO_PART ? opening_L + 2*end_flange
                   : opening_L - 2*end_clear + 2*(full_end_lip > 0 ? full_end_lip + end_clear : 0);
plate_W = opening_W + 2*flange_w;           // 171
skirt_L = opening_L - 2*end_clear;          // 348.5 - always inside the opening
skirt_W = opening_W - 2*side_clear;         // 145
field_L = skirt_L - 2*end_margin;           // 324.5 (pattern stays over the duct)
field_W = n_slots*slot_w + (n_slots-1)*slat_w;  // 122
pitch   = slot_w + slat_w;
total_H = plate_T + skirt_depth;            // 20.5
rib_span = skirt_W - skirt_wall;            // fuses into walls
kpitch  = bar_w + gap_w;                    // perpendicular pitch of 45° bars
$fn = 48;

echo(str("plate ", plate_L, " x ", plate_W, " x ", total_H,
         "  | free area fittes ~", n_slots*slot_w*field_L/100, " cm2"));
// full_end_lip parts are exempt from the flat-bed check - they print tilted 45
assert((TWO_PART ? plate_L/2 + 10 : (full_end_lip > 0 ? 0 : plate_L)) <= 350
       && plate_W <= 320, "exceeds H2D bed");
assert(slot_w <= 5.01 && gap_w <= 5.01, "child-safety: opening > 5 mm");

// ---------------- helpers ----------------
// 45° chamfer prism along X at (y, z)
module ch_x(y, z, c, l) {
    translate([0, y, z]) rotate([45, 0, 0])
        cube([l, c*sqrt(2), c*sqrt(2)], center=true);
}
// 45° chamfer prism along Y at (x, z)
module ch_y(x, z, c, l) {
    translate([x, 0, z]) rotate([0, 0, 90]) rotate([45, 0, 0])
        cube([l, c*sqrt(2), c*sqrt(2)], center=true);
}

module plate_outline_2d() {
    offset(r=corner_r) offset(delta=-corner_r)
        square([plate_L, plate_W], center=true);
}

// ---------------- body parts ----------------
module base_plate() {
    translate([0, 0, -plate_T]) linear_extrude(plate_T) plate_outline_2d();
}

module skirt(d = skirt_depth) {
    translate([0, 0, -(plate_T + d)]) linear_extrude(d)
        difference() {
            square([skirt_L, skirt_W], center=true);
            square([skirt_L - 2*skirt_wall, skirt_W - 2*skirt_wall], center=true);
        }
}

module ribs() {
    for (i = [1 : n_ribs])
        if (!(TWO_PART && i == (n_ribs+1)/2))   // center rib replaced by seam ribs
            translate([-field_L/2 + i*field_L/(n_ribs+1), 0, -plate_T - rib_d/2])
                cube([rib_t, rib_span, rib_d], center=true);
    if (TWO_PART)   // doubled rib straddling the seam, one per half
        for (sx = [-1, 1])
            translate([sx*1.7, 0, -plate_T - rib_d/2])
                cube([rib_t, rib_span, rib_d], center=true);
}

module magnet_bosses() {
    for (sx = [-1, 1])
        translate([sx*mag_x, 0, 0]) {
            translate([0, 0, -plate_T - 2]) cylinder(d=mag_boss_d, h=plate_T + 2 - 1);
        }
}
module magnet_pockets() {
    for (sx = [-1, 1])
        translate([sx*mag_x, 0, -plate_T - 2]) cylinder(d=mag_d, h=plate_T + 2 - 1.2);
}

// ---------------- patterns ----------------
module fittes_slots() {
    for (i = [0 : n_slots-1]) {
        yc = -field_W/2 + slot_w/2 + i*pitch;
        translate([0, yc, -plate_T/2 - 1])
            cube([field_L, slot_w, plate_T + 4], center=true);
    }
}
module fittes_slot_chamfers() {
    for (i = [0 : n_slots-1]) {
        yc = -field_W/2 + slot_w/2 + i*pitch;
        ch_x(yc - slot_w/2, 0, slot_ch, field_L);
        ch_x(yc + slot_w/2, 0, slot_ch, field_L);
    }
}

// kumiko_depth = plate_T -> original flat lattice over ribs.
// kumiko_depth > plate_T (e.g. 12) -> DEEP lattice: every bar is a beam,
// the +-45 crossing grid is self-triangulating, and the ribs are dropped
// (clearer airflow path). Pair with thinner bar_w for maximum open area.
kumiko_depth = plate_T;
module kumiko_bars() {
    nb = ceil(sqrt(field_L*field_L + field_W*field_W) / 2 / kpitch) + 1;
    for (a = [45, -45]) rotate([0, 0, a])
        for (k = [-nb : nb])
            translate([0, k*kpitch, -kumiko_depth/2])
                cube([600, bar_w, kumiko_depth], center=true);
}
module kumiko_lattice() {
    intersection() {
        translate([0, 0, -kumiko_depth/2])
            cube([field_L, field_W, kumiko_depth], center=true);
        kumiko_bars();
    }
}

// ---------------- assemblies ----------------
module common_chamfers(th = total_H) {
    ch_x(-plate_W/2, 0, edge_ch, plate_L + 4);
    ch_x( plate_W/2, 0, edge_ch, plate_L + 4);
    ch_y(-plate_L/2, 0, edge_ch, plate_W + 4);
    ch_y( plate_L/2, 0, edge_ch, plate_W + 4);
    // skirt bottom insertion chamfers
    ch_x(-skirt_W/2, -th, 1.2, skirt_L + 4);
    ch_x( skirt_W/2, -th, 1.2, skirt_L + 4);
    ch_y(-skirt_L/2, -th, 1.2, skirt_W + 4);
    ch_y( skirt_L/2, -th, 1.2, skirt_W + 4);
}

module vent_fittes() {
    difference() {
        union() {
            difference() {
                base_plate();
                fittes_slots();
                fittes_slot_chamfers();
            }
            skirt();
            ribs();
            magnet_bosses();
        }
        common_chamfers();
        magnet_pockets();
    }
}

module vent_kumiko() {
    difference() {
        union() {
            difference() {
                base_plate();
                translate([0, 0, -plate_T/2 - 1])
                    cube([field_L, field_W, plate_T + 4], center=true);
            }
            kumiko_lattice();
            skirt();
            if (kumiko_depth <= plate_T + 0.01) ribs();  // deep lattice IS the structure
            // deep-lattice version skips magnets: any diamond is a hook point
            // for removal, and a boss would show through the finer lattice
            if (kumiko_depth <= plate_T + 0.01) magnet_bosses();
        }
        common_chamfers();
        if (kumiko_depth <= plate_T + 0.01) magnet_pockets();
    }
}

// Lift key: flat 3 mm tool. Blade drops through a slot next to a
// cross-rib; 7 mm foot slides under the rib; lift. (Fittes style;
// for kumiko use the magnet pockets or a suction cup.)
// foot=7: hooks under fittes cross-ribs. foot=4.2 (luxe key): hooks under
// the floating panel's own edge - clears the 4.8mm gap to the spine loop.
module lift_key_final(foot = 7) {
    linear_extrude(3) union() {
        difference() {
            translate([0, 38]) offset(r=4) offset(delta=-4) square([40, 28], center=true);
            translate([0, 38]) offset(r=3) offset(delta=-3) square([26, 12], center=true);
        }
        translate([-6, 0]) square([12, 28]);          // stem 12 wide, 28 tall
        translate([-6, 0]) square([12 + foot, 5]);    // foot past stem
    }
}

// ------- LUXE frameless: parallel-openings principle, ONE PIECE -------
// derived: frame border | ch1 | ring1 | ch2 | ring2 | ch3 | panel
// pattern length anchored to the SKIRT (i.e. the opening), not the plate - 
// so one-piece and two-part variants share the exact same visible pattern
// regardless of how far the end lips extend.
luxe_FL = skirt_L - 2*luxe_end_border;               // 324.5 in every mode
luxe_FW = plate_W - 2*luxe_side_border;              // (135)
r1_oL = luxe_FL - 2*luxe_gap;  r1_oW = luxe_FW - 2*luxe_gap;      // 314.5 x 125
r1_iL = r1_oL - 2*luxe_ring_w; r1_iW = r1_oW - 2*luxe_ring_w;     // 290.5 x 101
r2_oL = r1_iL - 2*luxe_gap;    r2_oW = r1_iW - 2*luxe_gap;        // 280.5 x 91
r2_iL = r2_oL - 2*luxe_ring_w; r2_iW = r2_oW - 2*luxe_ring_w;     // 256.5 x 67
panel_L = r2_iL - 2*luxe_gap;  panel_W = r2_iW - 2*luxe_gap;      // 246.5 x 57

// only enforce when actually rendering the 3-channel style - small vents
// (e.g. the 10x4 bath) are valid for luxe1 but too narrow for 3 channels
assert(RENDER_PART != "luxe" || panel_W > 40,
       "luxe panel too narrow - shrink ring_w or gap");
assert(luxe_gap <= 5.01, "child-safety: channel > 5 mm");
assert(luxe_FL <= skirt_L - 2*skirt_wall - 1, "luxe opening exceeds skirt interior (L)");
// WIDTH was unchecked and bit us on the RMG bath variant: a lip wider than
// luxe_side_border pushes the side channels off the skirt - they'd vent
// into the under-lip floor gap instead of the duct.
assert(luxe_FW <= skirt_W - 2*skirt_wall - 1, "luxe opening exceeds skirt interior (W)");
// extra ribs centered under each ring's end bands (derived, mode-aware)
luxe_extra_rib_x = [(r1_oL + r1_iL)/4, (r2_oL + r2_iL)/4];

module rrect(l, w, r) { offset(r=r) offset(delta=-r) square([l, w], center=true); }

// NOTE: prisms trimmed 3 short so they never overrun a rounded corner and
// scar the adjacent top face (leaves ~1.5mm unchamfered at each corner arc).
module opening_edge_chamfers(l, w, c) {
    ch_x(-w/2, 0, c, l - 3); ch_x(w/2, 0, c, l - 3);
    ch_y(-l/2, 0, c, w - 3); ch_y(l/2, 0, c, w - 3);
}

// deep cross-ribs: tops 14.5 below the surface - out of sight down the
// 5mm channels (line of sight cut off beyond ~atan(5/14.5) = 19 deg)
module luxe_deep_ribs(extras, zt = -luxe_rib_top, zb = -total_H) {
    for (i = [1 : n_ribs])
        if (!(TWO_PART && i == (n_ribs+1)/2))
            translate([-field_L/2 + i*field_L/(n_ribs+1), 0, (zt+zb)/2])
                cube([rib_t, rib_span, zt - zb], center=true);
    if (TWO_PART)
        for (sx = [-1, 1])
            translate([sx*1.7, 0, (zt+zb)/2])
                cube([rib_t, rib_span, zt - zb], center=true);
    for (sx = [-1, 1], xx = extras)             // under island end spines
        translate([sx*xx, 0, (zt+zb)/2])
            cube([rib_t, rib_span, zt - zb], center=true);
}

// spine wall loop under a ring band's centerline (hidden under solid face)
module luxe_spine_loop(cl_l, cl_w, bot = luxe_spine_bot) {
    translate([0, 0, -bot])
        linear_extrude(bot - plate_T + 0.1)
            difference() {
                rrect(cl_l + luxe_spine_w, cl_w + luxe_spine_w, 1);
                rrect(cl_l - luxe_spine_w, cl_w - luxe_spine_w, 1);
            }
}
module luxe_spines() {
    luxe_spine_loop((r1_oL + r1_iL)/2, (r1_oW + r1_iW)/2);  // ring1: ends land on extra ribs
    luxe_spine_loop((r2_oL + r2_iL)/2, (r2_oW + r2_iW)/2);  // ring2: same
    for (yy = [-21, 0, 21])                                  // panel: 3 longitudinal spines
        translate([0, yy, -(plate_T + luxe_spine_bot)/2])
            cube([panel_L - 6, luxe_spine_w, luxe_spine_bot - plate_T], center=true);
}

// panel + rings, fused to ribs below (islands held by 11 rib crossings)
module luxe_islands() {
    translate([0, 0, -plate_T]) linear_extrude(plate_T) {
        difference() { rrect(r1_oL, r1_oW, 2); rrect(r1_iL, r1_iW, 2); }  // ring1
        difference() { rrect(r2_oL, r2_oW, 2); rrect(r2_iL, r2_iW, 2); }  // ring2
        rrect(panel_L, panel_W, 2);                                        // panel
    }
}

module vent_luxe() {
    difference() {
        union() {
            difference() {
                base_plate();
                translate([0, 0, -plate_T/2])
                    linear_extrude(plate_T + 4, center=true) rrect(luxe_FL, luxe_FW, 2);
            }
            luxe_islands();
            // channel downstand wall (finished look into the outer channel)
            translate([0, 0, -luxe_ch_depth]) linear_extrude(luxe_ch_depth - plate_T + 0.1)
                difference() {
                    rrect(luxe_FL + 2*2.4, luxe_FW + 2*2.4, 2);
                    rrect(luxe_FL, luxe_FW, 2);
                }
            skirt();
            luxe_spines();
            luxe_deep_ribs(luxe_extra_rib_x);
            magnet_bosses();
        }
        common_chamfers();
        // 0.7mm 45deg chamfers on every channel top edge (6 edge loops)
        opening_edge_chamfers(luxe_FL, luxe_FW, slot_ch);
        opening_edge_chamfers(r1_oL + 0.01, r1_oW + 0.01, slot_ch);
        opening_edge_chamfers(r1_iL, r1_iW, slot_ch);
        opening_edge_chamfers(r2_oL + 0.01, r2_oW + 0.01, slot_ch);
        opening_edge_chamfers(r2_iL, r2_iW, slot_ch);
        opening_edge_chamfers(panel_L + 0.01, panel_W + 0.01, slot_ch);
        magnet_pockets();
    }
}

// ---------------- render ----------------
// ------- LUXE-1: single channel + one floating panel (purest frameless) -------
// v3: supports lowered to a bottom GRID whose top is 24 below the surface - 
// sightline into the 5mm channel cuts off at atan(5/24) = 11.8 deg, i.e.
// only visible standing directly overhead. Being fully out of the visible
// path, structure is ADDED: 13 cross members + 5 longitudinal stringers
// (aligned under every spine wall), forming a stiff bidirectional grid.
l1_panel_L = luxe_FL - 2*luxe_gap;          // 314.5 one-piece
l1_panel_W = luxe_FW - 2*luxe_gap;          // 125
l1_loop_L  = l1_panel_L - 12;               // spine loop centerline (inset 6)
l1_loop_W  = l1_panel_W - 12;
l1_extra_rib_x = l1_loop_L/2;               // grid member aligned under loop end walls
l1_skirt_depth = 24;                        // deeper skirt houses the low grid
l1_total = plate_T + l1_skirt_depth;        // 28.5
l1_grid_top = 24;                           // grid top below top surface
l1_spine_bot = l1_grid_top + 0.5;           // spines overlap grid 0.5
l1_spine_y = [-28, 0, 28];                  // longitudinal spines under panel
// added cross members at midpoints between the 7 main rib positions
l1_mid_x = [field_L/16, 3*field_L/16, 5*field_L/16];   // 20.3, 60.8, 101.4

module luxe1_spines() {
    luxe_spine_loop(l1_loop_L, l1_loop_W, l1_spine_bot);
    for (yy = l1_spine_y)
        translate([0, yy, -(plate_T + l1_spine_bot)/2])
            cube([l1_loop_L, luxe_spine_w, l1_spine_bot - plate_T], center=true);
}
// longitudinal stringers directly under every spine plane, tying the grid
module luxe1_grid_stringers() {
    zc = -(l1_grid_top + l1_total)/2;
    for (yy = concat(l1_spine_y, [-l1_loop_W/2, l1_loop_W/2]))
        translate([0, yy, zc])
            cube([skirt_L - skirt_wall, rib_t, l1_total - l1_grid_top], center=true);
}

module vent_luxe1() {
    difference() {
        union() {
            difference() {
                base_plate();
                translate([0, 0, -plate_T/2])
                    linear_extrude(plate_T + 4, center=true) rrect(luxe_FL, luxe_FW, 2);
            }
            translate([0, 0, -plate_T]) linear_extrude(plate_T)
                rrect(l1_panel_L, l1_panel_W, 2);          // the one floating panel
            // channel downstand wall, reaching the grid
            translate([0, 0, -l1_spine_bot]) linear_extrude(l1_spine_bot - plate_T + 0.1)
                difference() {
                    rrect(luxe_FL + 2*2.4, luxe_FW + 2*2.4, 2);
                    rrect(luxe_FL, luxe_FW, 2);
                }
            skirt(l1_skirt_depth);
            luxe1_spines();
            luxe_deep_ribs(concat([l1_extra_rib_x], l1_mid_x),
                           -l1_grid_top, -l1_total);       // 13 cross members, deep
            luxe1_grid_stringers();
            magnet_bosses();
        }
        common_chamfers(l1_total);
        opening_edge_chamfers(luxe_FL, luxe_FW, slot_ch);
        opening_edge_chamfers(l1_panel_L + 0.01, l1_panel_W + 0.01, slot_ch);
        magnet_pockets();
    }
}

// ------------- two-part split v2: FOUR-LEVEL interlock at the seam -------------
// All levels engage with one vertical drop and stay invisible from above:
//  L0 plate:  45deg SCARF - step loads cross the seam in direct bearing
//  L0 border: full-thickness dovetails - in-plane pull-apart lock
//  L1 skirt:  vertical dovetail KEYS in both skirt side walls - deep
//             pull-apart + shear lock, 7 to bottom mm below the surface
//  L2 ribs:   interdigitated FINGER COMBS on the doubled seam ribs - 
//             shear + torsion coupling at the deepest structural level
seam_gap = 0.1;                       // butt-face clearance across the seam
dt_neck = 8; dt_head = 12; dt_depth = 7; dt_clear = 0.2;
dt_y = [-77, 77];                     // solid flange/border zone in ALL styles
scarf_land = 1.0;                     // vertical land top+bottom; 45deg ramp between
// style-aware depths (luxe1 is deeper than the others)
function jt_zbot() = (RENDER_PART == "luxe1") ? -(plate_T + l1_skirt_depth) : -total_H;
function jt_fz()   = (RENDER_PART == "luxe1") ? [-24.0, -(plate_T + l1_skirt_depth)]
                   : (RENDER_PART == "luxe")  ? [-15.5, -total_H]
                   : [-5.0, -(plate_T + rib_d)];   // below the scarf ledges
comb_yA = [-48, 14];  comb_yB = [-14, 48];   // clear of all spines/stringers
comb_w = 12; comb_clear = 0.2;

// full-thickness dovetail: prints flat on the bed (no mid-air shelf),
// visible on the border as a joinery detail
module dt_tabs() {
    for (yy = dt_y) translate([0, yy, -plate_T]) linear_extrude(plate_T)
        polygon([[3, -dt_neck/2], [3, dt_neck/2], [0, dt_neck/2],
                 [-dt_depth, dt_head/2], [-dt_depth, -dt_head/2], [0, -dt_neck/2]]);
}
module dt_sockets() {
    for (yy = dt_y) translate([0, yy, -plate_T - 1]) linear_extrude(plate_T + 2)
        offset(delta=dt_clear)
            polygon([[0.05, -dt_neck/2], [0.05, dt_neck/2],
                     [-dt_depth, dt_head/2], [-dt_depth, -dt_head/2]]);
}
// L0: scarf keep-region (ported from vent-14x20; distinct ledge depths so the
// receding side steps back deeper than the mating lip - zero-clearance gotcha)
module scarf_keep(side) {
    g = seam_gap/2;
    run = plate_T - 2*scarf_land;               // 2.5 -> 45deg, lip 1.25/side
    ledge = (side > 0) ? 0.4 : 0.2;
    zr0 = -scarf_land; zr1 = -(plate_T - scarf_land);
    top_e = -run/2 + side*g;  bot_e = run/2 + side*g;  below = side*g;
    far = side*400;
    rotate([90, 0, 0]) linear_extrude(900, center=true)
        polygon([[top_e, 1], [top_e, zr0], [bot_e, zr1], [bot_e, -plate_T - ledge],
                 [below, -plate_T - ledge], [below, -45], [far, -45], [far, 1]]);
}
// L1: vertical dovetail keys in the skirt side walls. Outer face stays flush
// (must clear the floor opening); the head flares INWARD only.
module skirt_key_2d(sy, o = 0) {
    yo = sy*skirt_W/2; yi = sy*(skirt_W/2 - skirt_wall);
    offset(delta=o) polygon([[1.6, yo], [-5, yo], [-5, yi - sy*3],
                             [0, yi], [1.6, yi]]);
}
module skirt_dt_tabs() {
    for (sy = [-1, 1])
        translate([0, 0, jt_zbot()]) linear_extrude(-7 - jt_zbot())
            skirt_key_2d(sy);
}
module skirt_dt_sockets() {
    for (sy = [-1, 1])
        translate([0, 0, jt_zbot() - 1]) linear_extrude(-6.8 - jt_zbot() + 1)
            skirt_key_2d(sy, dt_clear);
}
// L2: finger combs - fingers reach across and seat in sockets cut from the
// mating half's seam rib (0.2 clearance/side)
module comb_fingers(ys) {
    z = jt_fz();
    for (yy = ys) translate([0, yy, (z[0]+z[1])/2])
        cube([5.8, comb_w, z[0]-z[1]], center=true);
}
module comb_sockets(ys) {
    z = jt_fz();
    for (yy = ys) translate([0, yy, (z[0]+z[1])/2 - 0.5])
        cube([7.2, comb_w + 2*comb_clear, z[0]-z[1] + 1.4], center=true);
}
module styled() {
    if (RENDER_PART == "fittes") vent_fittes();
    if (RENDER_PART == "kumiko") vent_kumiko();
    if (RENDER_PART == "luxe")   vent_luxe();
    if (RENDER_PART == "luxe1")  vent_luxe1();
}

if (RENDER_PART == "liftkey") lift_key_final();
else if (RENDER_PART == "liftkey_luxe") lift_key_final(4.2);
else if (PART == "full") styled();
else if (PART == "A") difference() {
    union() { intersection() { styled(); scarf_keep(1); }
              dt_tabs(); skirt_dt_tabs(); comb_fingers(comb_yA); }
    comb_sockets(comb_yB);          // receive B's fingers
}
else if (PART == "B") difference() {
    union() { intersection() { styled(); scarf_keep(-1); }
              comb_fingers(comb_yB); }
    dt_sockets(); skirt_dt_sockets(); comb_sockets(comb_yA);
}
