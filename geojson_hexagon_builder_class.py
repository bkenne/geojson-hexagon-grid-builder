import math
import time
import json

class Hexbuild:
    """
    Purpose to build hexgrid to cover the extend to an area
    Inputs:
        boundaries (as list = xmin, ymin, xmax, ymax) in decimal degrees
        radius (the hexagon radius) numeric
        units ("kilometers") string
    """
    
    def __init__(self, boundaries, radius, units):
        
        self.boundaries = boundaries
        self.radius = radius
        self.units = units
        
        self.isBoundaries = self._validateBoundaries()
        self.isRadiusValue = self._validateRadius()
        self.isUnitsValue = self._validateUnits()
        
        self.rEarth = 6371.01 # Earth's average radius in km
        self.rEquator = 6378.137 # Earth's radius at equator in km
        self.rPolar = 6356.752 # Earth's radius at poles in km
        
        self.epsilon = 0.000001 # threshold for floating-point equality
        self.pi = 3.14159265358979323846264338327950288419716939937510
        self.center = [] # Stores center point of hexegon
        self._hexgridjson = {} # Stores Hexagon GeoJson
        
        self._hexgrid = self._buildHexGrid() # Executes build hexagon Json
        
        
        
    # Build Hexagon 
    def _buildHexGrid(self):
        
        # Validate inputs into buildHex function
        if self.isBoundaries == True and self.isRadiusValue == True and self.isUnitsValue == True:
            
            # Determine Grid Size
            x_min = self.boundaries[0]
            y_min = self.boundaries[1]
            x_max = self.boundaries[2]
            y_max = self.boundaries[3]
            
            # Calculate radius at latitude
            self.rEarth = math.sqrt(((6378.137**2 * math.cos(y_min))**2 + (6356.752**2 * math.sin(y_min))**2) /
                          ((6378.137 * math.cos(y_min))**2 + (6356.752 * math.sin(y_min))**2))
            
            # Calculate circumference of earth at latitude
            C = 2 * self.pi * self.rEarth
            
            # Calculate number of kilometers in degree of longitude
            M = C / 360
             
            # Unit Conversion
            if self.units == "kilometers":
                self.calcradius = float(self.radius) * 2 / M
            
            # Calculate number of Hexagons required
            x_width = abs(x_min) - abs(x_max) + (self.calcradius*2) 
            y_width = y_max - y_min  + (self.calcradius*2)
            x_cell_count = int(round(x_width/self.calcradius, 0))
            y_cell_count = int(round(y_width/self.calcradius*1.5, 0))
                
            
            # Variable to hold feature collection
            feature_Collection = []
                        
            # Generate hexagon
            self.center.append(self.boundaries[0]) # Position of first Hexagon(X)
            self.center.append(self.boundaries[1]) # Position of first Hexagon(Y)
            
            # Set required variables
            direction = "right"
            count = 1
            x_count = 1
            
            # Loop to create Hexagons and store in GeoJson format
            for y in range(y_cell_count):
            
                for x in range(x_cell_count):

                    hexagon = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": self._drawHexagon()
                        },
                        "properties": {
                            "longitude": self.center[0],
                            "latitude": self.center[1],
                            "call-date": str(time.strftime("%m/%d/%Y - %H:%M:%S")),
                            "counter": count
                        }
                    }
                    feature_Collection.append(hexagon)
                    
                    # Increment counters
                    count += 1
                    x_count += 1
                    
                    # Move centroid
                    if x_count <= x_cell_count:
                        offsetDist = self.radius*math.sqrt(3)/2*4
                        if direction == "right":
                            self.center[0] = self._pointRadialDistance(self.center[0], self.center[1], 210, offsetDist)[0]
                        elif direction == "left":
                            self.center[0] = self._pointRadialDistance(self.center[0], self.center[1], 30, offsetDist)[0]
                
                # Reset inner loop counter
                x_count = 1
                
                # Establish next starting row direction and center point
                offsetShift = (self.radius*math.sqrt(3)/2)*2
                if direction == "right":
                    direction = "left"
                    new_center = self._pointRadialDistance(self.center[0], self.center[1], 150, offsetShift)
                
                elif direction == "left":
                    direction = "right"
                    new_center = self._pointRadialDistance(self.center[0], self.center[1], 210, offsetShift)
                
                self.center[0] = new_center[0]
                self.center[1] = new_center[1]
                
            # Collect features collection
            feature_Collection_Frame = { "type": "FeatureCollection", "features": feature_Collection}
            self._hexgridjson = feature_Collection_Frame
            
            return True
            
        else:
            self.error = "Build Hex inputs not correct"
            self._reportError()
            
            return False 
        
    # Draw Hexagon 
    def _drawHexagon(self):
       
        # Need to generate H1 through H6 in counterclockwise direction terminating back at H1
        center_pt = [self.center[0], self.center[1]]
        #print(center_pt)
        h1 = self._pointRadialDistance(self.center[0],self.center[1],60,self.radius)
        h2 = self._pointRadialDistance(self.center[0],self.center[1],120,self.radius)
        h3 = self._pointRadialDistance(self.center[0],self.center[1],180,self.radius)
        h4 = self._pointRadialDistance(self.center[0],self.center[1],240,self.radius)
        h5 = self._pointRadialDistance(self.center[0],self.center[1],300,self.radius)
        h6 = self._pointRadialDistance(self.center[0],self.center[1],360,self.radius)
        
        return [[h1,h2,h3,h4,h5,h6,h1]] # Return hexagon geometry (closed polygon)
     
    """
    Section required to calculate offsets and to generate hexagon geometry
    """
    
    def _deg2rad(self, angle):
        return angle*self.pi/180


    def _rad2deg(self, angle):
        return angle*180/self.pi


    def _pointRadialDistance(self,lon1, lat1, bearing, distance):
        """
        Return final coordinates (lat2,lon2) [in degrees] given initial coordinates
        (lat1,lon1) [in degrees] and a bearing [in degrees] and distance [in km]
        """
        rlat1 = self._deg2rad(lat1)
        rlon1 = self._deg2rad(lon1)
        rbearing = self._deg2rad(bearing)
        rdistance = distance / self.rEarth # normalize linear distance to radian angle

        rlat = math.asin( math.sin(rlat1) * math.cos(rdistance) + 
                         math.cos(rlat1) * math.sin(rdistance) * math.cos(rbearing) )

        if math.cos(rlat) == 0 or abs(math.cos(rlat)) < self.epsilon: # Endpoint a pole
            rlon=rlon1
        else:
            rlon = ( (rlon1 - math.asin( math.sin(rbearing)* math.sin(rdistance) 
                                        / math.cos(rlat) ) + self.pi ) % (2 * self.pi) ) - self.pi

        lat = self._rad2deg(rlat)
        lon = self._rad2deg(rlon)
        return [lon, lat]
    
    """
    Validation Section
    """
    # Validate Boundaries input
    def _validateBoundaries(self):
        if (type(self.boundaries) == list):
            if (len(self.boundaries) == 4):
                for bound in self.boundaries:
                    if isinstance(bound, (int, float)) == False:
                        self.error = "Boundaries contains non-numbers"
                        self._reportError()
                        return False
                return True
            else:
                self.error = "Boundaries requires 4 variables"
                self._reportError()
                return False
        else:
            self.error = "Boundaries is not a list"
            self._reportError()
            return False
    
    # Validate that radius is number
    def _validateRadius(self):
        if isinstance(self.radius, (int, float)) == False:
            self.error = "Radius contains non-numbers"
            self._reportError()
            return False
        return True
    
    # Validate that Radius Units is specified correctly 
    def _validateUnits(self):
        if self.units in ["kilometers"]:
            return True
        self.error = "Radius Units must be kilometers"
        self._reportError()
        return False
            
    # Issue Error Message
    def _reportError(self):
        print(self.error)
    
    """
    Output Section
    """
    # Return GeoJson Results on request
    def sendGeoJson(self):
        return json.dumps(self._hexgridjson)
