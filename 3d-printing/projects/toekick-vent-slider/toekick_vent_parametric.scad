// Bathroom toe-kick vent grille — ¾ solid, right ¼ angled louvers (deflect air right)
// Original parametric design. Units: mm. Matches standard 2¼" × 12" toe-kick faceplate.
// Print: PETG, 0.2mm layers, 4 walls — print flat, front face down for smoothest finish.

/* [Plate] */
W = 340;            // plate width
H = 85;             // plate height
T = 3;              // plate thickness
corner_r = 6;       // corner radius

/* [Screw holes] */
hole_inset_x = 9.3; // hole center from each end
hole_y = 45;        // hole center from bottom
hole_d = 4.2;       // clearance for #6 / M3.5 screw
csk_d = 8.5;        // countersink dia (90°)

/* [Louvered window — centered quarter] */
win_w = 85;         // window width (quarter of plate)
win_margin_y = 14;  // top/bottom margin (matches original grille inset)

/* [Fins] */
fin_t = 1.6;        // fin thickness
fin_pitch = 5.0;    // horizontal spacing (no see-through at 45° in 3mm)
fin_angle = 45;     // deflect exiting air to the right
fin_back = 0;       // 0 = louvers contained within plate thickness

win_x0 = (W - win_w) / 2;
win_x1 = (W + win_w) / 2;
win_y0 = win_margin_y;
win_y1 = H - win_margin_y;
fin_len = (T + fin_back) / cos(fin_angle) + 4;

module plate2d() {
    offset(r = corner_r)
        translate([corner_r, corner_r])
            square([W - 2*corner_r, H - 2*corner_r]);
}

difference() {
    union() {
        // plate with window cut
        difference() {
            linear_extrude(T) plate2d();
            translate([win_x0, win_y0, -1])
                cube([win_x1 - win_x0, win_y1 - win_y0, T + 2]);
        }
        // angled fins, trimmed to window
        intersection() {
            translate([win_x0, win_y0 - 4, -fin_back])
                cube([win_x1 - win_x0, win_y1 - win_y0 + 8, T + fin_back]);
            for (x = [win_x0 - fin_len : fin_pitch : win_x1 + fin_len])
                translate([x, win_y0 - 4, (T - fin_back)/2])
                    rotate([0, fin_angle, 0])
                        translate([-fin_t/2, 0, -fin_len/2])
                            cube([fin_t, win_y1 - win_y0 + 8, fin_len]);
        }
    }
    // countersunk screw holes (front face = z = T)
    for (hx = [hole_inset_x, W - hole_inset_x]) {
        translate([hx, hole_y, -fin_back - 1])
            cylinder(d = hole_d, h = T + fin_back + 2, $fn = 64);
        csk_depth = (csk_d - hole_d) / 2;
        translate([hx, hole_y, T - csk_depth])
            cylinder(d1 = hole_d, d2 = csk_d + 1, h = csk_depth + 0.5, $fn = 64);
    }
}
