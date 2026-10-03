"""
Protheon 3D Virtual Hand Visualization
"""

import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

class VirtualHandWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = gl.GLViewWidget()
        self.view.opts['distance'] = 250
        self.view.opts['elevation'] = 30
        self.view.opts['azimuth'] = -45
        self.layout.addWidget(self.view)
        
        # Grid
        grid = gl.GLGridItem()
        grid.scale(20, 20, 1)
        self.view.addItem(grid)
        
        # Origin
        axis = gl.GLAxisItem()
        axis.setSize(x=50, y=50, z=50)
        self.view.addItem(axis)
        
        # Build Palm
        palm_mesh = gl.MeshData.cylinder(rows=1, cols=4, radius=[30, 30], length=40)
        self.palm = gl.GLMeshItem(meshdata=palm_mesh, color=(0.3, 0.3, 0.4, 0.8), smooth=False)
        self.palm.translate(0, 0, 0)
        self.view.addItem(self.palm)
        
        # Define fingers (Base coords relative to palm)
        self.fingers = {
            'thumb': {'pos': (-30, 10, 5), 'color': (1.0, 0.4, 0.4, 0.9), 'nodes': []},
            'index': {'pos': (-20, 40, 0), 'color': (0.3, 0.8, 0.4, 0.9), 'nodes': []},
            'middle': {'pos': (0, 40, 0), 'color': (0.3, 0.6, 1.0, 0.9), 'nodes': []},
            'ring': {'pos': (20, 40, 0), 'color': (1.0, 0.8, 0.2, 0.9), 'nodes': []},
            'pinky': {'pos': (40, 35, 0), 'color': (0.8, 0.5, 1.0, 0.9), 'nodes': []},
        }
        
        # Construct nodes for each finger (base, middle, distal)
        for f, data in self.fingers.items():
            for i in range(3):
                # Simple cylinders for finger segments
                mesh = gl.MeshData.cylinder(rows=1, cols=8, radius=[6, 5], length=20)
                seg = gl.GLMeshItem(meshdata=mesh, color=data['color'], smooth=True)
                self.view.addItem(seg)
                data['nodes'].append(seg)
                
        self.update_hand({'thumb': 0, 'index': 0, 'middle': 0, 'ring': 0, 'pinky': 0})

    def update_hand(self, percentages):
        """
        Update the 3D hand posture based on 0-100% bend values.
        """
        for f_name, data in self.fingers.items():
            pct = percentages.get(f_name, 0.0)
            
            # Map percentage (0-100) to joint angle (0 to 90 degrees)
            angle_deg = (pct / 100.0) * 85.0
            angle_rad = np.radians(angle_deg)
            
            bx, by, bz = data['pos']
            
            # Procedural inverse kinematics / forward kinematics (basic)
            # Assuming joints lie on the Y axis, bending down towards -Z
            for i, seg in enumerate(data['nodes']):
                seg.resetTransform()
                
                # Apply local rotation to this segment (compounded by parent)
                total_angle = angle_deg * (i + 1) * 0.5
                
                # Length of previous segments (approx 20 each)
                length = 20
                
                # Calculate cumulative position
                if i == 0:
                    px, py, pz = bx, by, bz
                elif i == 1:
                    prev_rad = np.radians(angle_deg * 0.5)
                    px = bx
                    py = by + length * np.cos(prev_rad)
                    pz = bz - length * np.sin(prev_rad)
                else:
                    prev_rad_1 = np.radians(angle_deg * 0.5)
                    prev_rad_2 = np.radians(angle_deg * 1.0)
                    px = bx
                    py = by + length * np.cos(prev_rad_1) + length * np.cos(prev_rad_2)
                    pz = bz - length * np.sin(prev_rad_1) - length * np.sin(prev_rad_2)
                
                # Apply transforms
                seg.rotate(-total_angle, 1, 0, 0)
                seg.translate(px, py, pz)
