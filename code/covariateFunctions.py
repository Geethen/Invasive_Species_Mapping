import ee

class prepareCovariates:
    def __init__(self, covariates, proj = 'EPSG:4326', nAngles = None):
        self.covariates = covariates
        self.proj = proj
        self.nAngles = nAngles
 
    def _addRotatedCoords(self, ang):
        """
        //adds bands with coordinates rotated to account for spatial autocorrelation
        // Reference: Møller, A. B., Beucher, A. M., Pouladi, N., & Greve, M. H. (2020).  
        Oblique geographic coordinates as covariates for digital soil mapping. Soil, 6(2), 269-289.
        """
        ang = ee.Number(ang).multiply(3.141592653589793)
        ang = ee.Image(ang)
        xy = ee.Image.pixelCoordinates(ee.Projection(self.proj))
        z = xy.select('y').pow(2).add(xy.select('x').pow(2)).sqrt().multiply(
         ang.subtract(xy.select('y').divide(xy.select('x')).atan()).cos())
        return z
    
    def addRotatedCoords(self):
        # Spatial autocorr using rotated coordinates
        steps = ee.List.sequence(0, 1, count = self.nAngles).slice(0,-1)
        steps = steps.map(lambda ang: self._addRotatedCoords(ang))
        steps = ee.ImageCollection(steps).toBands().regexpRename('^(.{0})', 'band')
        return self.covariates.addBands(steps)
                            
    def addTopoBands(self):
        """
        Adds SRTM elevation, CHILI, Topographic diversity, slope and aspect
        """
        # Load the SRTM elevation image.
        elevation = ee.Image("USGS/SRTMGL1_003").rename('elevation').regexpRename('^(.{0})', 'band')
        # Load the CHILI images- proxies for microclimate
        chili = ee.Image("CSP/ERGo/1_0/Global/SRTM_CHILI").rename('chili').regexpRename('^(.{0})', 'band')
        tpi =  ee.Image("CSP/ERGo/1_0/Global/SRTM_mTPI").rename('tpi').regexpRename('^(.{0})', 'band')
        # Apply an algorithm to compute slope and aspect.
        slope = ee.Terrain.slope(elevation).rename('slope').regexpRename('^(.{0})', 'band')
        aspect = ee.Terrain.aspect(elevation).rename('aspect').regexpRename('^(.{0})', 'band')
                            
        return self.covariates.addBands([elevation, chili, tpi, slope, aspect])
    
    def addCovariates(self, rotatedCoords = True, topoBands = True):
        """
        This function adds all covariates to the image
        """
        if rotatedCoords:
            self.covariates = self.addRotatedCoords()
        if topoBands:
            self.covariates = self.addTopoBands()
        return self.covariates
