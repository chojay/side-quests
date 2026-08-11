// ============================================================
// Kitchen LUXE flush vent - 3 nested channels, maximum-flow luxe.
// Follows the nursery LUXE principles (nursery_flush_vent.scad):
//   - child-safe: every opening is a 5.0 mm channel, 0.7 mm chamfered
//   - "no visible line": NOTHING under any channel from the surface
//     down to the deep grid at 20 mm -> sightline cuts off at
//     atan(5/20) = 14 deg; channels read as continuous dark lines
//   - islands carried by hidden SPINE WALLS under their own solid
//     faces, guided down to a bidirectional DEEP GRID (sturdy underfoot
//     - this is a kitchen floor, it WILL be stepped on)
//   - maximum flow in the luxe language: THREE nested channels
//     (~100 cm2) instead of the single-channel bath look (~40 cm2)
//
// MEASUREMENTS (site, 2026-07):
//   floor opening 300 x 133; duct (dropdown) 285 x 133 at 25 mm below
//   the floor -> ledge at the two ENDS only (7.5 mm each), sides sheer.
//   One long edge near a wall: lip max 17 mm -> UNIFORM 17 mm lip,
//   plate 334 x 167 - full perimeter lip AND fits the bed flat
//   (the 350-opening nursery original couldn't have both).
//
// ONE PIECE. Print TOP FACE DOWN on textured PEI, 0.2 mm, 4 walls,
// zero supports (grid layer bridges <= ~20 mm between anchors - routine).
// PETG (heater supply). Design orientation: top surface z=0, part -z.
// ============================================================

/* [What to render] */
RENDER_PART = "vent";   // ["vent"]

/* [Opening - CONFIRM BY MEASURE] */
opening_L = 300;      // floor opening, long axis
opening_W = 133;      // floor opening, width (wall along one long edge)
duct_L = 285;         // dropdown opening below
ledge_depth = 25;     // floor top to the end ledges
end_clear  = 0.75;
side_clear = 1.0;

/* [Body] */
lip_w   = 17.0;       // MAX per the wall clearance; uniform all around
plate_T = 4.5;
skirt_depth = 22.0;   // below plate underside; end ledges at 25 -> clears 3
skirt_wall  = 2.4;
edge_ch = 2.0; corner_r = 2.0; slot_ch = 0.7;

/* [Luxe channels] */
luxe_gap    = 5.0;    // CHILD SAFETY <= 5
luxe_ring_w = 12.0;   // nested ring face width (nursery luxe value)
grid_top    = 20.0;   // deep grid top below TOP surface; sightline atan(5/20)
spine_w     = 2.4;
rib_t       = 2.4;
n_ribs      = 7;
mag_d = 8.4; mag_boss_d = 13.0; mag_x = 60;

// ---------------- derived ----------------
plate_L = opening_L + 2*lip_w;               // 334
plate_W = opening_W + 2*lip_w;               // 167
skirt_L = opening_L - 2*end_clear;           // 298.5
skirt_W = opening_W - 2*side_clear;          // 131
skirt_in_L = skirt_L - 2*skirt_wall;         // 293.7
skirt_in_W = skirt_W - 2*skirt_wall;         // 126.2
total_H = plate_T + skirt_depth;             // 26.5
luxe_FL = skirt_in_L - 2.7;                  // 291 - outer channel outline
luxe_FW = skirt_in_W - 2.2;                  // 124
r1_oL = luxe_FL - 2*luxe_gap;  r1_oW = luxe_FW - 2*luxe_gap;   // 281 x 114
r1_iL = r1_oL - 2*luxe_ring_w; r1_iW = r1_oW - 2*luxe_ring_w;  // 257 x 90
r2_oL = r1_iL - 2*luxe_gap;    r2_oW = r1_iW - 2*luxe_gap;     // 247 x 80
r2_iL = r2_oL - 2*luxe_ring_w; r2_iW = r2_oW - 2*luxe_ring_w;  // 223 x 56
panel_L = r2_iL - 2*luxe_gap;  panel_W = r2_iW - 2*luxe_gap;   // 213 x 46
spine_bot = grid_top + 0.5;                  // spines overlap the grid 0.5
extra_rib_x = [(r1_oL + r1_iL)/4, (r2_oL + r2_iL)/4];  // under ring end bands
spine_y = [-15, 0, 15];                      // panel longitudinal spines
ring_spine_y = [(r1_oW + r1_iW)/4, (r2_oW + r2_iW)/4]; // 51, 34 (stringer rows)
field_L = luxe_FL;                            // main rib placement span
rib_span = skirt_W - skirt_wall;
$fn = 48;

assert(plate_L <= 350 && plate_W <= 320, "exceeds bed");
assert(luxe_gap <= 5.01, "child-safety: channel > 5 mm");
assert(panel_W > 40, "luxe panel too narrow - shrink ring_w or gap");
assert(skirt_depth <= ledge_depth - 2, "skirt hits the end ledges");
assert(luxe_FL <= skirt_in_L - 1, "luxe opening exceeds skirt interior (L)");
// W went unchecked once on an earlier bath variant - its side channels would
// have vented into the under-lip floor gap instead of the duct. Never again:
assert(luxe_FW <= skirt_in_W - 1, "luxe opening exceeds skirt interior (W)");
assert(grid_top + 0.5 < total_H - 3, "grid needs >= 3mm of height");
echo(str("plate ", plate_L, " x ", plate_W, " x ", total_H,
     "  channels ~", round((2*((luxe_FL+r1_oL)/2 + (luxe_FW+r1_oW)/2)
                          + 2*((r1_iL+r2_oL)/2 + (r1_iW+r2_oW)/2)
                          + 2*((r2_iL+panel_L)/2 + (r2_iW+panel_W)/2)) * luxe_gap / 100),
     " cm2, duct ", round(duct_L*opening_W/100), " cm2, sightline ",
     round(atan(luxe_gap/grid_top)), " deg"));

// ---------------- helpers (vent-family conventions) ----------------
module ch_x(y, z, c, l) { translate([0, y, z]) rotate([45, 0, 0])
    cube([l, c*sqrt(2), c*sqrt(2)], center=true); }
module ch_y(x, z, c, l) { translate([x, 0, z]) rotate([0, 0, 90]) rotate([45, 0, 0])
    cube([l, c*sqrt(2), c*sqrt(2)], center=true); }
module rrect(l, w, r) { offset(r=r) offset(delta=-r) square([l, w], center=true); }
module opening_edge_chamfers(l, w, c) {
    ch_x(-w/2, 0, c, l - 3); ch_x(w/2, 0, c, l - 3);
    ch_y(-l/2, 0, c, w - 3); ch_y(l/2, 0, c, w - 3);
}

// ---------------- body ----------------
module base_plate() {
    translate([0, 0, -plate_T]) linear_extrude(plate_T)
        rrect(plate_L, plate_W, corner_r);
}
module skirt() {
    translate([0, 0, -total_H]) linear_extrude(skirt_depth)
        difference() { square([skirt_L, skirt_W], center=true);
                       square([skirt_in_L, skirt_in_W], center=true); }
}
module luxe_islands() {   // ring1 + ring2 + panel, all in the top plate plane
    translate([0, 0, -plate_T]) linear_extrude(plate_T) {
        difference() { rrect(r1_oL, r1_oW, 2); rrect(r1_iL, r1_iW, 2); }
        difference() { rrect(r2_oL, r2_oW, 2); rrect(r2_iL, r2_iW, 2); }
        rrect(panel_L, panel_W, 2);
    }
}
module downstand() {      // finished wall around the outer channel, to the grid
    translate([0, 0, -spine_bot]) linear_extrude(spine_bot - plate_T + 0.1)
        difference() { rrect(luxe_FL + 2*2.4, luxe_FW + 2*2.4, 2);
                       rrect(luxe_FL, luxe_FW, 2); }
}
module spine_loop(cl_l, cl_w) {   // hidden wall under a ring band centerline
    translate([0, 0, -spine_bot]) linear_extrude(spine_bot - plate_T + 0.1)
        difference() { rrect(cl_l + spine_w, cl_w + spine_w, 1);
                       rrect(cl_l - spine_w, cl_w - spine_w, 1); }
}
module spines() {
    spine_loop((r1_oL + r1_iL)/2, (r1_oW + r1_iW)/2);  // under ring1 band
    spine_loop((r2_oL + r2_iL)/2, (r2_oW + r2_iW)/2);  // under ring2 band
    for (yy = spine_y)                                  // under the panel
        translate([0, yy, -(plate_T + spine_bot)/2])
            cube([panel_L - 6, spine_w, spine_bot - plate_T], center=true);
}
// deep bidirectional grid: cross members full width + stringers under
// every spine plane. All between grid_top and the part bottom.
module deep_grid() {
    zc = -(grid_top + total_H)/2;  gh = total_H - grid_top;
    for (i = [1 : n_ribs])                              // main cross members
        translate([-field_L/2 + i*field_L/(n_ribs+1), 0, zc])
            cube([rib_t, rib_span, gh], center=true);
    for (sx = [-1, 1], xx = extra_rib_x)                // under ring end spines
        translate([sx*xx, 0, zc]) cube([rib_t, rib_span, gh], center=true);
    for (sy = [-1, 1], yy = ring_spine_y)               // ring-row stringers, full length
        translate([0, sy*yy, zc])
            cube([skirt_L - skirt_wall, rib_t, gh], center=true);
    for (yy = spine_y)                                  // panel-row stringers: end ON the
        translate([0, yy, zc])                          // panel spines (no long bridges)
            cube([panel_L - 6, rib_t, gh], center=true);
}
module magnet_bosses() { for (sx = [-1, 1]) translate([sx*mag_x, 0, -plate_T - 2])
    cylinder(d=mag_boss_d, h=plate_T + 2 - 1); }
module magnet_pockets() { for (sx = [-1, 1]) translate([sx*mag_x, 0, -plate_T - 2])
    cylinder(d=mag_d, h=plate_T + 2 - 1.2); }
module common_chamfers() {
    ch_x(-plate_W/2, 0, edge_ch, plate_L + 4); ch_x(plate_W/2, 0, edge_ch, plate_L + 4);
    ch_y(-plate_L/2, 0, edge_ch, plate_W + 4); ch_y(plate_L/2, 0, edge_ch, plate_W + 4);
    ch_x(-skirt_W/2, -total_H, 1.2, skirt_L + 4); ch_x(skirt_W/2, -total_H, 1.2, skirt_L + 4);
    ch_y(-skirt_L/2, -total_H, 1.2, skirt_W + 4); ch_y(skirt_L/2, -total_H, 1.2, skirt_W + 4);
}

module vent_kitchen_luxe() {
    difference() {
        union() {
            difference() {
                base_plate();
                translate([0, 0, -plate_T/2])
                    linear_extrude(plate_T + 4, center=true) rrect(luxe_FL, luxe_FW, 2);
            }
            luxe_islands();
            downstand();
            skirt();
            spines();
            deep_grid();
            magnet_bosses();
        }
        common_chamfers();
        // 0.7mm chamfers on all six channel edge loops
        opening_edge_chamfers(luxe_FL, luxe_FW, slot_ch);
        opening_edge_chamfers(r1_oL + 0.01, r1_oW + 0.01, slot_ch);
        opening_edge_chamfers(r1_iL, r1_iW, slot_ch);
        opening_edge_chamfers(r2_oL + 0.01, r2_oW + 0.01, slot_ch);
        opening_edge_chamfers(r2_iL, r2_iW, slot_ch);
        opening_edge_chamfers(panel_L + 0.01, panel_W + 0.01, slot_ch);
        magnet_pockets();
    }
}
if (RENDER_PART == "vent") vent_kitchen_luxe();
