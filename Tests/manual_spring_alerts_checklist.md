# Spring Alerts Manual Verification

1. Open FreeCAD and activate the Spring Workbench.
2. Confirm no persistent "Spring Alerts" dock opens automatically.
3. Create two or more spring objects.
4. Double-click a spring in the tree and confirm FreeCAD enters spring edit mode with a "Spring Alerts" task panel.
5. Confirm a valid spring shows the spring name and zero counts or "No alerts" rows.
6. Change the edited spring to produce a warning or error and confirm the task panel contents update.
7. Change the edited spring to produce a fatal geometry error, such as `OutsideDiameterAtFree <= 2 * WireDiameter`, and confirm the task panel shows the error while geometry generation remains governed by the existing recompute behavior.
8. Close the task panel and confirm FreeCAD exits spring edit mode.
9. Double-click another spring and confirm the task panel changes to that spring's alerts.
10. Confirm no modal validation popup appears.
11. Confirm existing geometry generation behavior and automated tests are unchanged.
