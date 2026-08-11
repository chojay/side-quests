// Air Vent Cover with Dovetail Locking Frame
// Decorative cover for a standard 10 x 4 in wall duct
// Frame assembles from 4 pieces with interlocking dovetail joints

/* [Vent Opening Dimensions] */
vent_width = 200;        // Width of vent opening (mm)
vent_height = 100;       // Height of vent opening (mm)

/* [Frame Dimensions] */
frame_width = 25;        // Width of frame border (mm)
frame_thickness = 8;     // Thickness/depth of frame (mm)

/* [Dovetail Joint Parameters] */
dovetail_length = 15;    // Length of dovetail projection (mm)
dovetail_angle = 10;     // Angle of dovetail (degrees)
dovetail_clearance = 0.3; // Clearance for fit (mm)

/* [Grill Parameters] */
slat_count = 8;          // Number of horizontal slats
slat_thickness = 3;      // Thickness of each slat (mm)
slat_angle = 30;         // Angle of slats (degrees, 0 = horizontal)

/* [Display Options] */
show_assembled = true;   // Show assembled view
show_exploded = false;   // Show exploded view
explode_distance = 40;   // Distance for exploded view (mm)
show_individual = false; // Show individual pieces laid flat

// Calculated dimensions
outer_width = vent_width + 2 * frame_width;
outer_height = vent_height + 2 * frame_width;

// Main rendering
if (show_assembled) {
    color("SaddleBrown") assembled_frame();
    color("Sienna") grill();
}

if (show_exploded) {
    translate([outer_width + 50, 0, 0])
        exploded_frame();
}

if (show_individual) {
    translate([0, -outer_height - 50, 0])
        individual_pieces();
}

// ============================================
// DOVETAIL JOINT MODULES
// ============================================

// Single dovetail (male) profile - the pin
module dovetail_pin(length, width, thickness, angle, clearance=0) {
    // Tapered dovetail shape
    bottom_width = width - 2 * clearance;
    top_width = bottom_width + 2 * length * tan(angle);

    linear_extrude(height = thickness - clearance)
        polygon([
            [0, 0],
            [length, (width - top_width) / 2 + clearance],
            [length, (width + top_width) / 2 - clearance],
            [0, width]
        ]);
}

// Single dovetail (female) socket - the slot
module dovetail_socket(length, width, thickness, angle, clearance=0) {
    // Socket is slightly larger for clearance
    bottom_width = width;
    top_width = width + 2 * length * tan(angle);
    extra = clearance;

    translate([-0.1, -extra, -extra])
    linear_extrude(height = thickness + 2*extra)
        polygon([
            [0, 0],
            [length + extra, (width - top_width) / 2 - extra],
            [length + extra, (width + top_width) / 2 + extra],
            [0, width + 2*extra]
        ]);
}

// ============================================
// FRAME PIECE MODULES
// ============================================

// Top frame piece with dovetail pins on both ends
module top_frame_piece() {
    pin_width = frame_width * 0.7;

    difference() {
        union() {
            // Main bar (shorter to account for joints)
            cube([outer_width - 2*dovetail_length, frame_width, frame_thickness]);

            // Left dovetail pin
            translate([-dovetail_length, (frame_width - pin_width)/2, 0])
                dovetail_pin(dovetail_length, pin_width, frame_thickness, dovetail_angle);

            // Right dovetail pin
            translate([outer_width - 2*dovetail_length, frame_width - (frame_width - pin_width)/2, 0])
                rotate([0, 0, 180])
                    dovetail_pin(dovetail_length, pin_width, frame_thickness, dovetail_angle);
        }
    }
}

// Bottom frame piece (identical to top)
module bottom_frame_piece() {
    top_frame_piece();
}

// Left frame piece with dovetail sockets on both ends
module left_frame_piece() {
    pin_width = frame_width * 0.7;

    difference() {
        // Main bar
        cube([frame_width, vent_height + 2*dovetail_length, frame_thickness]);

        // Bottom dovetail socket
        translate([frame_width/2 - pin_width/2, -0.1, 0])
            rotate([0, 0, -90])
                translate([-pin_width, 0, 0])
                    dovetail_socket(dovetail_length, pin_width, frame_thickness,
                                   dovetail_angle, dovetail_clearance);

        // Top dovetail socket
        translate([frame_width/2 + pin_width/2, vent_height + 2*dovetail_length + 0.1, 0])
            rotate([0, 0, 90])
                translate([-pin_width, 0, 0])
                    dovetail_socket(dovetail_length, pin_width, frame_thickness,
                                   dovetail_angle, dovetail_clearance);
    }
}

// Right frame piece (identical to left)
module right_frame_piece() {
    left_frame_piece();
}

// ============================================
// ASSEMBLY MODULES
// ============================================

module assembled_frame() {
    // Top piece
    translate([dovetail_length, vent_height + frame_width, 0])
        top_frame_piece();

    // Bottom piece
    translate([dovetail_length, 0, 0])
        bottom_frame_piece();

    // Left piece
    translate([0, frame_width - dovetail_length, 0])
        left_frame_piece();

    // Right piece
    translate([outer_width - frame_width, frame_width - dovetail_length, 0])
        right_frame_piece();
}

module exploded_frame() {
    // Top piece - moved up
    translate([dovetail_length, vent_height + frame_width + explode_distance, 0])
        color("SaddleBrown") top_frame_piece();

    // Bottom piece - moved down
    translate([dovetail_length, -explode_distance, 0])
        color("Peru") bottom_frame_piece();

    // Left piece - moved left
    translate([-explode_distance, frame_width - dovetail_length, 0])
        color("Sienna") left_frame_piece();

    // Right piece - moved right
    translate([outer_width - frame_width + explode_distance, frame_width - dovetail_length, 0])
        color("Chocolate") right_frame_piece();
}

module individual_pieces() {
    // Layout pieces flat for printing
    spacing = 20;

    // Top piece
    color("SaddleBrown") top_frame_piece();

    // Bottom piece
    translate([0, -frame_width - spacing, 0])
        color("Peru") bottom_frame_piece();

    // Left piece (rotated for compact layout)
    translate([outer_width - 2*dovetail_length + spacing, 0, 0])
        rotate([0, 0, -90])
            color("Sienna") left_frame_piece();

    // Right piece
    translate([outer_width - 2*dovetail_length + spacing + vent_height + 2*dovetail_length + spacing, 0, 0])
        rotate([0, 0, -90])
            color("Chocolate") right_frame_piece();
}

// ============================================
// GRILL MODULE
// ============================================

module grill() {
    slat_spacing = vent_height / (slat_count + 1);
    slat_width = slat_spacing * 0.6;

    translate([frame_width, frame_width, 0]) {
        for (i = [1:slat_count]) {
            translate([0, i * slat_spacing - slat_width/2, frame_thickness/2])
                rotate([slat_angle, 0, 0])
                    cube([vent_width, slat_width, frame_thickness * 1.5]);
        }
    }
}

// ============================================
// ALTERNATIVE: SLIDING DOVETAIL DESIGN
// ============================================
// This version uses a sliding dovetail where vertical
// pieces slide into horizontal pieces from above

module sliding_dovetail_rail(length) {
    // Rail that accepts a sliding dovetail
    rail_depth = frame_thickness * 0.6;
    rail_width_bottom = frame_width * 0.4;
    rail_width_top = rail_width_bottom + 2 * rail_depth * tan(dovetail_angle);

    translate([0, 0, frame_thickness])
    rotate([180, 0, 0])
    linear_extrude(height = rail_depth)
        polygon([
            [0, (frame_width - rail_width_bottom)/2],
            [0, (frame_width + rail_width_bottom)/2],
            [length, (frame_width + rail_width_top)/2],
            [length, (frame_width - rail_width_top)/2]
        ]);
}

module sliding_dovetail_tongue(length) {
    // Tongue that slides into the rail
    tongue_depth = frame_thickness * 0.6 - dovetail_clearance;
    tongue_width_bottom = frame_width * 0.4 - dovetail_clearance;
    tongue_width_top = tongue_width_bottom + 2 * tongue_depth * tan(dovetail_angle) - dovetail_clearance;

    linear_extrude(height = tongue_depth)
        polygon([
            [0, (frame_width - tongue_width_bottom)/2],
            [0, (frame_width + tongue_width_bottom)/2],
            [length, (frame_width + tongue_width_top)/2],
            [length, (frame_width - tongue_width_top)/2]
        ]);
}

// ============================================
// INFORMATION TEXT
// ============================================
echo("=== Air Vent Cover Dimensions ===");
echo(str("Vent Opening: ", vent_width, " x ", vent_height, " mm"));
echo(str("Outer Frame: ", outer_width, " x ", outer_height, " mm"));
echo(str("Frame Border Width: ", frame_width, " mm"));
echo(str("Frame Thickness: ", frame_thickness, " mm"));
echo(str("Dovetail Length: ", dovetail_length, " mm"));
echo(str("Dovetail Angle: ", dovetail_angle, " degrees"));
