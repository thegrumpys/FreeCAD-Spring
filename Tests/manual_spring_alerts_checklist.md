# Spring Alerts Manual Verification

1. Open FreeCAD and activate the Spring Workbench.
2. Confirm no persistent "Spring Alerts" dock opens automatically.
3. Create two or more spring objects.
4. Double-click a spring in the tree and confirm a non-modal "Spring Alerts" dock opens.
5. Confirm a valid spring shows the spring name and zero counts or "No alerts" rows.
6. Confirm global FreeCAD commands such as "New Document" remain enabled while the dock is visible.
7. Select another spring and confirm the dock tracks the selected spring.
8. Change the selected spring to produce a warning or error and confirm the dock contents update.
9. Change the selected spring to produce a fatal geometry error, such as `OutsideDiameterAtFree <= 2 * WireDiameter`, and confirm the dock shows the error while geometry generation remains governed by the existing recompute behavior.
10. Confirm no modal validation popup appears.
11. Confirm existing geometry generation behavior and automated tests are unchanged.
