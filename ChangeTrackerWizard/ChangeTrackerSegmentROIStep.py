from __main__ import qt, ctk

from ChangeTrackerStep import *
from Helper import *

class ChangeTrackerSegmentROIStep( ChangeTrackerStep ) :

  def __init__( self, stepid ):
    self.initialize( stepid )
    self.setName( '3. Segment the analyzed structure' )
    self.setDescription( 'Segment the structure in the selected ROI.' )

    self.__parent = super( ChangeTrackerSegmentROIStep, self )
    
    self.__vrDisplayNode = None
    self.__threshold = [ -1, -1 ]
       
    # initialize VR stuff
    self.__vrLogic = slicer.modules.volumerendering.logic()
    self.__vrOpacityMap = None

  def createUserInterface( self ):
    '''
    '''
#    self.buttonBoxHints = self.ButtonBoxHidden

    self.__layout = self.__parent.createUserInterface()

    threshLabel = qt.QLabel('Choose threshold:')
    self.__threshSlider = ctk.ctkSliderWidget()
    self.__threshSlider.decimals = 0
    self.__threshSlider.singleStep = 1

    roiLabel = qt.QLabel( 'Select segmentation:' )
    self.__roiLabelSelector = slicer.qMRMLNodeComboBox()
    self.__roiLabelSelector.nodeTypes = ( 'vtkMRMLScalarVolumeNode', '' )
    self.__roiLabelSelector.addAttribute('vtkMRMLScalarVolumeNode','LabelMap','1')
    self.__roiLabelSelector.toolTip = "Choose the ROI segmentation"

    self.__layout.addRow(threshLabel, self.__threshSlider)
    self.__layout.addRow( roiLabel, self.__roiLabelSelector )

    self.__threshSlider.connect('valueChanged(double)', self.onThresholdChanged)

  def onThresholdChanged(self, newValue): 
    print 'New threshold value: ', newValue
    
    self.__threshold[0] = newValue

    self.__vrOpacityMap.RemoveAllPoints()
    self.__vrOpacityMap.AddPoint(0,0)
    self.__vrOpacityMap.AddPoint(0,0)
    self.__vrOpacityMap.AddPoint(self.__threshold[0]-1,0)
    self.__vrOpacityMap.AddPoint(self.__threshold[0],1)
    self.__vrOpacityMap.AddPoint(self.__threshold[1],1)
    self.__vrOpacityMap.AddPoint(self.__threshold[1]+1,0)




  def validate( self, desiredBranchId ):
    '''
    '''
    self.__parent.validate( desiredBranchId )
    # check here that ROI is not empty and is within the baseline volume
    self.__parent.validationSucceeded(desiredBranchId)

  def onEntry(self, comingFrom, transitionType):
    '''
    Resample the baseline volume using ROI

    TODO: if coming from the next step, do not resample!
    '''
    pNode = self.parameterNode()
    baselineVolumeID = pNode.GetParameter('baselineVolumeID')
    baselineVolume = slicer.mrmlScene.GetNodeByID(baselineVolumeID)

    outputVolume = slicer.modules.volumes.logic().CloneVolume(slicer.mrmlScene, baselineVolume, 'baselineROI')
    cropVolumeNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLCropVolumeParametersNode')
    cropVolumeNode.SetScene(slicer.mrmlScene)
    cropVolumeNode.SetName('ChangeTracker_CropVolume_node')
    slicer.mrmlScene.AddNode(cropVolumeNode)

    cropVolumeNode.SetAndObserveInputVolumeNodeID(pNode.GetParameter('baselineVolumeID'))
    cropVolumeNode.SetAndObserveROINodeID(pNode.GetParameter('roiID'))
    # cropVolumeNode.SetAndObserveOutputVolumeNodeID(outputVolume.GetID())

    cropVolumeLogic = slicer.modules.cropvolume.logic()
    cropVolumeLogic.Apply(cropVolumeNode)

    # TODO: cropvolume error checking
    pNode.SetParameter('croppedBaselineVolumeID',cropVolumeNode.GetOutputVolumeNodeID())

    Helper.SetBgFgVolumes(pNode.GetParameter('croppedBaselineVolumeID'),'')
    super(ChangeTrackerSegmentROIStep, self).onEntry(comingFrom, transitionType)

    # initilize threshold selector based on the ROI contents
    roiVolume = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('croppedBaselineVolumeID'))
    roiImage = roiVolume.GetImageData()
    roiImageRange = roiImage.GetScalarRange()
    self.__threshold[0] = roiImageRange[0]
    self.__threshold[1] = roiImageRange[1]
    self.__threshSlider.minimum =  self.__threshold[0]
    self.__threshSlider.maximum = self.__threshold[1]
    # TODO: initialize volume selectors, fit ROI to slice viewers, create
    # label volume, initialize the threshold, initialize volume rendering ?

    if self.__vrDisplayNode == None:
      self.__vrDisplayNode = self.__vrLogic.CreateVolumeRenderingDisplayNode()
      viewNode = slicer.util.getNode('ViewNode')
      self.__vrDisplayNode.AddViewNodeID(viewNode.GetID())
      print 'SegmentROI step: create VR node ',self.__vrDisplayNode.GetID()

    self.__vrDisplayNode.SetAndObserveVolumeNodeID(roiVolume.GetID())
    self.__vrLogic.UpdateDisplayNodeFromVolumeNode(self.__vrDisplayNode, roiVolume)
    self.__vrOpacityMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetScalarOpacity()
    vrColorMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetRGBTransferFunction()
    
    # setup color transfer function once
    vrColorMap.RemoveAllPoints()
    vrColorMap.AddRGBPoint(0, 0, 0, 0) 
    vrColorMap.AddRGBPoint(roiImageRange[0]-1, 0, 0, 0) 
    vrColorMap.AddRGBPoint(roiImageRange[0], 0.8, 0.8, 0) 
    vrColorMap.AddRGBPoint(roiImageRange[1], 0.8, 0.8, 0) 
    vrColorMap.AddRGBPoint(roiImageRange[1]+1, 0, 0, 0) 

    self.__vrDisplayNode.VisibilityOn()

    self.__vrOpacityMap.RemoveAllPoints()
    self.__vrOpacityMap.AddPoint(0,0)
    self.__vrOpacityMap.AddPoint(0,0)
    self.__vrOpacityMap.AddPoint(self.__threshold[0]-1,0)
    self.__vrOpacityMap.AddPoint(self.__threshold[0],1)
    self.__vrOpacityMap.AddPoint(self.__threshold[1],1)
    self.__vrOpacityMap.AddPoint(self.__threshold[1]+1,0)

    
