# .103 — save within the workspace

Move the existing single save control from the navigation rail into the analysis workspace header controls, the editor room toolbar, or homepage actions according to the active view. Keep the same button, status, listeners and Ctrl+S/save path. Compact horizontal layout with bounded status text. Moving the same DOM node avoids duplicate handlers/IDs and preserves ongoing save feedback.

Navigation regression checks all three placements, absence from the rail and retained-frame navigation behavior. No persistence logic changed; .102 save tests apply. Windows GUI not run.
