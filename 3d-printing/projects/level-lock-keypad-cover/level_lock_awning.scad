// Level Lock Awning Cover - OpenSCAD Version
// Compare with build123d to diagnose geometry issues

// === PARAMETERS ===
OUTER_WIDTH = 88.9;
OUTER_HEIGHT = 122.0;
BACK_PLATE_THICKNESS = 3.0;

// Lock opening
SIDE_CLEARANCE = 10.0;
TOP_CLEARANCE = 10.0;
LOCK_DIAMETER = OUTER_WIDTH - 2 * SIDE_CLEARANCE;  // ~68.9mm
LOCK_RADIUS = LOCK_DIAMETER / 2;

// Awning
AWNING_DEPTH = 50.8;
AWNING_THICKNESS = 5.0;
AWNING_ANGLE = 15.0;

// Sidewalls - tiny corner tabs
SIDEWALL_THICKNESS = 5.0;
SIDEWALL_HEIGHT = 15.0;

// Calculate circle position
circle_center_y = -(OUTER_HEIGHT / 2 - TOP_CLEARANCE - LOCK_RADIUS);

echo("=== Level Lock Awning - OpenSCAD ===");
echo(str("Back plate: ", OUTER_WIDTH, "W x ", OUTER_HEIGHT, "H x ", BACK_PLATE_THICKNESS, "D mm"));
echo(str("Lock opening diameter: ", LOCK_DIAMETER, "mm"));
echo(str("Circle center Y: ", circle_center_y));

$fn = 100;  // Smooth circles

module level_lock_awning() {
    difference() {
        union() {
            // 1. BACK PLATE with rounded corners
            translate([0, 0, BACK_PLATE_THICKNESS/2])
                linear_extrude(height=BACK_PLATE_THICKNESS, center=true)
                    offset(r=2.0)  // 2mm rounded corners
                        offset(r=-2.0)
                            square([OUTER_WIDTH, OUTER_HEIGHT], center=true);

            // 2. ANGLED AWNING TOP
            awning_y_pos = (OUTER_HEIGHT - AWNING_THICKNESS) / 2;
            height_diff = (AWNING_DEPTH - BACK_PLATE_THICKNESS) * tan(AWNING_ANGLE);

            // Create awning as a prism
            translate([0, awning_y_pos, BACK_PLATE_THICKNESS]) {
                polyhedron(
                    points = [
                        // Bottom face (at back plate level)
                        [-OUTER_WIDTH/2, -AWNING_THICKNESS/2, 0],
                        [OUTER_WIDTH/2, -AWNING_THICKNESS/2, 0],
                        [OUTER_WIDTH/2, AWNING_THICKNESS/2, 0],
                        [-OUTER_WIDTH/2, AWNING_THICKNESS/2, 0],
                        // Top face (angled forward)
                        [-OUTER_WIDTH/2, -AWNING_THICKNESS/2 + height_diff, AWNING_DEPTH - BACK_PLATE_THICKNESS],
                        [OUTER_WIDTH/2, -AWNING_THICKNESS/2 + height_diff, AWNING_DEPTH - BACK_PLATE_THICKNESS],
                        [OUTER_WIDTH/2, AWNING_THICKNESS/2 + height_diff, AWNING_DEPTH - BACK_PLATE_THICKNESS],
                        [-OUTER_WIDTH/2, AWNING_THICKNESS/2 + height_diff, AWNING_DEPTH - BACK_PLATE_THICKNESS]
                    ],
                    faces = [
                        [0,1,2,3],  // bottom
                        [4,5,6,7],  // top
                        [0,1,5,4],  // front
                        [2,3,7,6],  // back
                        [0,3,7,4],  // left
                        [1,2,6,5]   // right
                    ]
                );
            }

            // 3. LEFT CORNER TAB
            translate([-(OUTER_WIDTH - SIDEWALL_THICKNESS) / 2,
                      (OUTER_HEIGHT / 2) - (SIDEWALL_HEIGHT / 2),
                      BACK_PLATE_THICKNESS])
                cube([SIDEWALL_THICKNESS, SIDEWALL_HEIGHT, AWNING_DEPTH - BACK_PLATE_THICKNESS]);

            // 4. RIGHT CORNER TAB
            translate([(OUTER_WIDTH - SIDEWALL_THICKNESS) / 2,
                      (OUTER_HEIGHT / 2) - (SIDEWALL_HEIGHT / 2),
                      BACK_PLATE_THICKNESS])
                cube([SIDEWALL_THICKNESS, SIDEWALL_HEIGHT, AWNING_DEPTH - BACK_PLATE_THICKNESS]);
        }

        // 5. CUT CIRCLE for Level Lock Pro (through entire back plate)
        translate([0, circle_center_y, -0.5])
            cylinder(h=BACK_PLATE_THICKNESS + 1, r=LOCK_RADIUS, center=false);
    }
}

// Generate the part
level_lock_awning();
